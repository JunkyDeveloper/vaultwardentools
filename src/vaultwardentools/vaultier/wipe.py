#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import os
from collections import OrderedDict
from multiprocessing import Pool

import click

import vaultwardentools
from vaultwardentools import Client, L, as_bool, sanitize
from vaultwardentools.vaultier import AS_SINGLE_ORG

vaultwardentools.setup_logging()
JSON = os.environ.get("VAULTIER_JSON", "data/export/vaultier.json")


@click.command()
@click.argument("jsonf", default=JSON)
@click.option("--server", default=vaultwardentools.SERVER)
@click.option("--email", default=vaultwardentools.EMAIL)
@click.option("--password", default=vaultwardentools.PASSWORD)
@click.option("--assingleorg", " /-S", default=AS_SINGLE_ORG, is_flag=True)
def main(jsonf, server, email, password, assingleorg):
    L.info("start")
    client = Client(server, email, password)
    client.sync()
    orgas = client.get_organizations()
    orgas_to_delete = OrderedDict()
    for jsonff in jsonf.split(":"):
        with open(jsonff) as fic:
            data = json.load(fic)
        if assingleorg:
            orga = {"bw": None, "name": data["name"], "collections": OrderedDict()}
            v = orga["name"]
            v = sanitize(orga["name"])
            data["vaults"] = [orga]
        for vdata in data["vaults"]:
            v = sanitize(vdata["name"])
            try:
                orgas_to_delete[v.lower()]
            except KeyError:
                try:
                    ods = orgas["name"][v.lower()]
                except KeyError:
                    continue
                for ix, (_, o) in enumerate(ods.items()):
                    orgas_to_delete[f"{v}{ix}".lower()] = {
                        "bw": o,
                        "vault": vdata,
                        "name": v,
                        "collections": OrderedDict(),
                    }
                    L.info(f"Will delete orga {v}")

    # either create or edit passwords
    parallel = as_bool(os.environ.get("BW_PARALLEL_IMPORT", "1"))
    # parallel = False
    processes = int(os.environ.get("BW_PARALLEL_IMPORT_PROCESSES", "30"))

    items = []
    for org, odata in orgas_to_delete.items():
        if odata["bw"] is not None:
            items.append([client, odata])
    if parallel:
        with Pool(processes=processes) as pool:
            results = pool.starmap_async(record, items)
            results.wait()
    else:
        for item in items:
            record(*item)


def record(client, odata):
    odata["bw"].delete(client)


if __name__ == "__main__":
    main()
# vim:set et sts=4 ts=4 tw=120:
