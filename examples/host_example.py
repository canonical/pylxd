#!/usr/bin/python

from pylxd import api

client = api.API()
print client.get_lxd_backing_fs()
