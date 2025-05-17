#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os

import click

import vaultwardentools
from vaultwardentools import Client, L
from vaultwardentools import client as bwclient

vaultwardentools.setup_logging()
PASSWORDS = os.environ.get("BW_PASSWORDS_JSON", "data/passwords.json")


@click.command()
@click.option("--login")
def main(
    login,
):
    assert login
    L.info("start")
    client = Client()
    client.sync()
    try:
        user = client.get_user(email=login)
        client.disable_user(user=user)
    except bwclient.UserNotFoundError:
        pass


if __name__ == "__main__":
    main()
#
