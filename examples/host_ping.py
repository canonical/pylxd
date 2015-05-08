#!/usr/bin/python

from pylxd import client

c = client.Client(base_url='none',
                  host=None)
c.host_ping()
