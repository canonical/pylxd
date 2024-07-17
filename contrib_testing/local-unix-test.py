#!/usr/bin/env python3

import datetime
import os
import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import pylxd

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def log(s):
    now = datetime.datetime.now(datetime.UTC)
    print(f"{now} - {s}")


def create_and_update(client):
    log("Creating...")
    base = client.containers.create(
        {
            "name": "ubuntu-1604",
            "source": {
                "type": "image",
                "protocol": "simplestreams",
                "server": "https://images.linuxcontainers.org",
                "alias": "ubuntu/xenial/amd64",
            },
        },
        wait=True,
    )
    log("starting...")
    base.start(wait=True)
    while len(base.state().network["eth0"]["addresses"]) < 2:
        time.sleep(1)
    commands = [
        ["apt-get", "update"],
        ["apt-get", "install", "openssh-server", "sudo", "man", "-y"],
    ]
    for command in commands:
        log(f"command: {command}")
        result = base.execute(command)
        log(f"result: {result.exit_code}")
        log(f"stdout: {result.stdout}")
        log(f"stderr: {result.stderr}")


if __name__ == "__main__":
    client = pylxd.Client()
    log("Authenticating...")
    if client.has_api_extension("explicit_trust_token"):
        secret = os.getenv("LXD_TOKEN")
    else:
        secret = "password"

    client.authenticate(secret)

    create_and_update(client)
