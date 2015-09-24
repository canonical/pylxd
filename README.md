# pylxd [![Build Status](https://travis-ci.org/lxc/pylxd.svg?branch=master)](https://travis-ci.org/lxc/pylxd)

A Python library for interacting with the LXD REST API.

## Getting started with pylxd

If you're running on Ubuntu Wily or greater:

    sudo apt-get install python-pylxd lxd

otherwise you can track LXD development on other Ubuntu releases:

    sudo add-apt-repository ppa:ubuntu-lxc/lxd-git-master && sudo apt-get update
    sudo apt-get install lxd

and install pylxd using pip:

    pip install pylxd

## First steps

Once you have pylxd installed, you're ready to start interacting with LXD:

```python
import uuid
from pylxd import api

# Let's pick a random name, avoiding clashes
CONTAINER_NAME = str(uuid.uuid1())

lxd = api.API()

try:
    lxd.container_defined(CONTAINER_NAME)
except Exception as e:
    print("Container does not exist: %s" % e)

config = {'name': CONTAINER_NAME,
          'source': {'type': 'none'}}
lxd.container_init(config)
if lxd.container_defined(CONTAINER_NAME):
    print("Container is running")
else:
    print("Whoops - please report a bug!")
containers = lxd.container_list()
for x in containers:
    lxd.container_destroy(x)
```

## Bug reports

Bug reports can be filed at https://github.com/lxc/pylxd/issues/new

## Support and discussions

We use the LXC mailing-lists for developer and user discussions, you can
find and subscribe to those at: https://lists.linuxcontainers.org

If you prefer live discussions, some of us also hang out in
[#lxcontainers](http://webchat.freenode.net/?channels=#lxcontainers) on irc.freenode.net.
