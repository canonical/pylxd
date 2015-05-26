#!/usr/bin/python
#
# api_test.py: Test/demo of the python3-lxc API
#
# (C) Copyright Canonical Ltd. 2015
#
# Authors:
# Chuck Short <zulcss@ubuntu.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

import uuid
import sys
import subprocess
import time

# Let's pick a random name, avoiding clashes
CONTAINER_NAME = str(uuid.uuid1())

from pylxd import api

lxd = api.API()
try:
    lxd.container_defined(CONTAINER_NAME)
except Exception as e:
    print "Container doesnt exist: %s" % e

config = {'name': CONTAINER_NAME,
          'source': {'type': 'none'}}
lxd.container_init(config)
if lxd.container_defined(CONTAINER_NAME):
    print "Container is running"
else:
    print "Whoops!"
containers = lxd.container_list()
for x in containers:
    lxd.container_destroy(x)
