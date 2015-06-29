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

import mock
import unittest

import pylxd

class LXDUnitTestHost(unittest.TestCase):
    def setUp(self):
        super(LXDUnitTestHost, self).setUp()

        self.lxd = pylxd.api.API()
        self.fake_host_mock = {
		            "type": "sync",
		            "status": "Success",
		            "status_code": 200,
		            "metadata": {
			            "api_compat": 1,
			            "auth": "trusted",
			            "config": {},
			            "environment": {
				            "backing_fs": "ext4",
				            "driver": "lxc",
				            "kernel_version": "3.19.0-21-generic",
				            "lxc_version": "1.1.2",
				            "lxd_version": "0.12"
			    }
		    }
	    }

    @mock.patch.object(pylxd.api, 'host_ping'
    def test_host_ping(self, mock_api):
        mock_api.resturn_value = True
        self.assertTrue(self.lxd.host_ping()))

    @mock.patch.object(plxd.api.API, 'host_info')
    def test_host_info(self, mock_api):
        mock_api.return_value = self.fake_host_mock
