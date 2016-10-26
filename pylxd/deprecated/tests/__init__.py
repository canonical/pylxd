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

from ddt import data
from ddt import unpack
import unittest

from pylxd.deprecated import api


class LXDAPITestBase(unittest.TestCase):

    def setUp(self):
        super(LXDAPITestBase, self).setUp()
        self.lxd = api.API()


def annotated_data(*args):
    class List(list):
        pass

    new_args = []

    for arg in args:
        new_arg = List(arg)
        new_arg.__name__ = arg[0]
        new_args.append(new_arg)

    return lambda func: data(*new_args)(unpack(func))
