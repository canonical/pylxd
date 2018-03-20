#!/usr/bin/env python3

import datetime
import pylxd
import requests
import time

from requests.packages.urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def log(s):
    now = datetime.datetime.utcnow()
    print("{} - {}".format(now, s))


def create_and_update(client):
    log("Creating...")
    base = client.containers.create({
        'name': 'ubuntu-1604',
        'source': {
            'type': 'image',
            'protocol': 'simplestreams',
            'server': 'https://images.linuxcontainers.org',
            'alias': 'ubuntu/xenial/amd64'
        }
    }, wait=True)
    log("starting...")
    base.start(wait=True)
    while len(base.state().network['eth0']['addresses']) < 2:
        time.sleep(1)
    commands = [
        ['apt-get', 'update'],
        ['apt-get', 'install', 'openssh-server', 'sudo', 'man', '-y']
    ]
    for command in commands:
        log("command: {}".format(command))
        result = base.execute(command)
        log("result: {}".format(result.exit_code))
        log("stdout: {}".format(result.stdout))
        log("stderr: {}".format(result.stderr))


if __name__ == '__main__':
    client = pylxd.Client()
    log("Authenticating...")
    client.authenticate('password')

    create_and_update(client)
