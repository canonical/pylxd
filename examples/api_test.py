#!/usr/bin/python

# Copyright (c) 2015 Canonical Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid

# Let's pick a random name, avoiding clashes
CONTAINER_NAME = str(uuid.uuid1())

from pylxd import api

lxd = api.API()
try:
    lxd.container_defined(CONTAINER_NAME)
except Exception as e:
    print("Container doesnt exist: %s" % e)

config = {'name': CONTAINER_NAME,
          'source': {'type': 'none'}}
lxd.container_init(config)
if lxd.container_defined(CONTAINER_NAME):
    print("Container is running")
else:
    print("Whoops!")
containers = lxd.container_list()
for x in containers:
    lxd.container_destroy(x)
