#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import copy
import json
import os
import traceback
from collections import OrderedDict
from multiprocessing import Pool

import click

import vaultwardentools
from vaultwardentools import (
    EXPORT_DIR,
    VAULTIER_SECRET,
    Client,
    L,
    NoAttachmentsError,
    SecretNotFound,
    as_bool,
    sanitize,
)
from vaultwardentools.vaultier import AS_SINGLE_ORG

vaultwardentools.setup_logging()
JSON = os.environ.get("VAULTIER_JSON", "data/export/vaultier.json")
BW_ORGA_NAME = os.environ.get("BW_ORGA_NAME", "bitwarden")
DONE = {"contructed": OrderedDict(), "errors": OrderedDict()}


class NameNotFound(RuntimeError):
    """."""


def get_name(cipherd):
    s = cipherd["secret"]
    n = s.get("name", "")
    sdata = s.get("data", {})
    if not n:
        username = sdata.get("username", "")
        if username:
            n += f"@{username}"
        url = sdata.get("url", "")
        if url:
            n = username and "{username}@{url}" or url
        if not n and ("note" in sdata):
            n = "note"
    if not n:
        raise NameNotFound(cipherd)
    return n


def get_note(cipherd):
    note = ""
    for item in "vault", "card", "secret":
        dsc = cipherd[item].get("description", "")
        if dsc:
            note += f"## {item}\n{dsc}\n\n"
    sdata = cipherd["secret"].get("data", {})
    dn = sdata.get("note", "")
    if dn:
        note += f"## note\n\n{dn}\n\n"
    return note


def assemble(cipherd):
    bw = cipherd["bw"]
    patch = cipherd["patch"]
    secret = cipherd["secret"]
    if "link" in cipherd["actions"]:
        patch["collections"] = cipherd["collections"]
    s = secret.get("data", {})
    patch.update({"vaultiersecretid": secret["id"]})
    if bw:
        patch.update(copy.deepcopy(bw.json))
    cipherd["action"] = bw and "edit" or "create"
    patch["name"] = get_name(cipherd)
    patch["collection"] = cipherd["collections"]
    patch["object"] = "item"
    patch["orga"] = cipherd["orga"]
    patch["notes"] = get_note(cipherd)
    login = patch.setdefault("login", {})
    if secret["type"] in [VAULTIER_SECRET.secret, VAULTIER_SECRET.file]:
        login.update(
            {"username": s.get("username", None), "password": s.get("password", None)}
        )
        uris = login.get("uris", None) or []
        if s.get("url"):
            item = {"uri": s["url"], "match": None, "response": None}
            if not uris:
                uris = [item]
            else:
                if item not in uris:
                    uris = [item]
            if uris:
                login["uris"] = uris
    return cipherd


def record(client, cipherd):
    try:
        secret = cipherd["secret"]
        cipherd = assemble(cipherd)
        bw = cipherd["bw"]
        for action in cipherd["actions"]:
            if action in ["create", "edit"]:
                bw = getattr(client, action)(**cipherd["patch"])
                break
        # attachments
        if "attach" in cipherd["actions"]:
            filename = secret["blob_meta"]["filename"]
            filepath = f'{EXPORT_DIR}/{secret["id"]}/{filename}'
            client.attach(bw, filepath)
        return bw
    except Exception as exc:
        trace = traceback.format_exc()
        sid = cipherd["secret"]["id"]
        L.error(f"Error while creating {sid}\n{trace}")
        DONE["errors"][sid] = exc


@click.command()
@click.argument("jsonf", default=JSON)
@click.option("--server", default=vaultwardentools.SERVER)
@click.option("--email", default=vaultwardentools.EMAIL)
@click.option("--password", default=vaultwardentools.PASSWORD)
@click.option("--assingleorg", " /-S", default=AS_SINGLE_ORG, is_flag=True)
def main(jsonf, server, email, password, assingleorg):
    L.info("start")
    client = Client(vaultier=True)
    client.sync()
    ciphers_to_import = OrderedDict()
    vaultier_secrets = {}
    for jsonff in jsonf.split(":"):
        with open(jsonff) as fic:
            data = json.load(fic)
        orga = {}
        if assingleorg:
            organ = data["name"]
            orga = client.get_organization(organ)
        for iv, vdata in enumerate(data["vaults"]):
            v = vdata["name"]
            if not vdata["cards"]:
                L.info(f"Skipping {v} as it has no cards")
                continue
            if not assingleorg:
                orga = client.get_organization(v)
            collections = client.get_collections(orga)
            for cdata in vdata["cards"]:
                cn = sanitize(cdata["name"])
                vc = cn
                if assingleorg:
                    vc = f"{v} {cn}"
                collection = client.get_collection(vc, collections=collections)
                cid = collection.id
                for ix, secret in enumerate(cdata["secrets"]):
                    sid = f"{secret['id']}"
                    vaultier_secrets[sid] = secret
                    sd = secret.get("data", {})
                    idata = {
                        "vault": vdata,
                        "card": cdata,
                        "sid": sid,
                        "actions": [],
                        "secret": secret,
                        "collection": collection,
                        "collections": [],
                        "orga": orga,
                        "patch": {},
                        "bw": None,
                    }
                    sname = get_name(idata)
                    idata["name"] = sname
                    try:
                        sec = client.get_cipher(
                            sid,
                            vc,
                            collections=collections,
                            orga=orga,
                            vaultier=True,
                            sync=False,
                        )
                        if sec.vaultiersecretid != sid:
                            raise SecretNotFound()
                        idata["bw"] = sec
                        edit = False
                        #
                        # vaultier otypes: 200: secret, 300, files, 100: Note
                        #
                        if secret["type"] in [
                            VAULTIER_SECRET.file,
                            VAULTIER_SECRET.secret,
                        ]:
                            login = getattr(sec, "login", {}) or {}
                            if any(
                                (
                                    (login.get("username", "") or "")
                                    != (sd.get("username") or ""),
                                    (login.get("password", "") or "")
                                    != (sd.get("password") or ""),
                                )
                            ):
                                edit = True
                            uris = login.get("uris", {}) or {}
                            urls = [a.get("uri", "") for a in uris if a.get("uri", "")]
                            if sd.get("url") and (sd["url"] not in urls):
                                edit = True
                        if secret["type"] in [a for a in VAULTIER_SECRET]:
                            if any(
                                (
                                    (sec.name or "") != (sname or ""),
                                    (sec.notes or "") != (get_note(idata) or ""),
                                )
                            ):
                                edit = True
                        if edit:
                            idata["actions"].append("edit")
                            L.info(f"Will patch already existing {sec.name} in {vc}")
                        if secret["type"] == VAULTIER_SECRET.file:
                            fn = secret["blob_meta"]["filename"]
                            try:
                                filenames = [
                                    a["fileName"] for a in client.get_attachments(sec)
                                ]
                            except NoAttachmentsError:
                                filenames = []
                            if fn not in filenames:
                                idata["actions"].append("attach")
                            else:
                                L.info(
                                    f"Already attached {fn} to  {sec.name}/{sec.id} in {vc}"
                                )
                        if cid not in sec.collectionIds:
                            idata["actions"].append("link")
                            idata["collections"] = [cid] + (sec.collectionIds or [])
                            L.info(f"Will link {sec.name} in {vc}")
                        if not idata["actions"]:
                            L.info(f"Already created {sec.name}/{sec.id} in {vc}")
                    except SecretNotFound:
                        try:
                            ciphers_to_import[sid]
                        except KeyError:
                            idata["actions"].append("create")
                            if secret["type"] == VAULTIER_SECRET.file:
                                idata["actions"].append("attach")
                            idata["collections"] = [cid]
                            idata["actions"].append("link")
                            L.info(f'Will create {secret["name"]} in {vc}')
                    if idata["actions"]:
                        ciphers_to_import[sid] = idata

    constructed = OrderedDict()
    # either create or edit passwords
    parallel = as_bool(os.environ.get("BW_PARALLEL_IMPORT", "1"))
    # parallel = False
    processes = int(os.environ.get("BW_PARALLEL_IMPORT_PROCESSES", "10"))
    if parallel:
        with Pool(processes=processes) as pool:
            res = pool.starmap_async(
                record, [(client, cipherd) for n, cipherd in ciphers_to_import.items()]
            )
            res.wait()
            for ret in res.get():
                if not ret:
                    continue
                constructed[ret.id] = ret
    else:
        for n, cipherd in ciphers_to_import.items():
            ret = record(client, cipherd)
            if not ret:
                continue
            constructed[ret.id] = ret

    return constructed


if __name__ == "__main__":
    main()
# vim:set et sts=4 ts=4 tw=0:
