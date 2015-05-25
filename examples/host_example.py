#!/usr/bin/python

from pylxd import client

c = client.Client()
print c.get_lxd_backing_fs()
