#!/usr/bin/python

from pylxd import client

c = client.Client(base_url='none',
                  host=None)
if c.host_ping():
    print "Host is available"
else:
    print "Host is not available"

return c.host_info()