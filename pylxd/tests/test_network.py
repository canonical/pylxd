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

import unittest

from pylxd import api

import pylxd.tests.utils as utils

class LXDTestNetwork(unittest.TestCase):
    def setUp(self):
        self.api = api.API()

        self.config = {'name': 'test-container',
                       'source': {'type': 'none'}}
        self.container = 'test-container'

    def test_show_network_info(self):
        network = self.api.network_show('lxcbr0')

        self.assertIn('network_name', network)
        self.assertIn('network_type', network)
        self.assertIn('network_members', network)

    def test_show_network_member(self):
        utils.create_lxd_container(self.container, self.config)