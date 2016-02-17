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

from ddt import ddt
import json
import mock

from pylxd.deprecated import connection

from pylxd.deprecated.tests import annotated_data
from pylxd.deprecated.tests import fake_api
from pylxd.deprecated.tests import LXDAPITestBase


@ddt
class LXDAPICertificateTest(LXDAPITestBase):

    def test_list_certificates(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_certificate_list())
            self.assertEqual(
                ['ABCDEF01'],
                self.lxd.certificate_list())
            ms.assert_called_with('GET',
                                  '/1.0/certificates')

    def test_certificate_show(self):
        with mock.patch.object(connection.LXDConnection, 'get_object') as ms:
            ms.return_value = ('200', fake_api.fake_certificate())
            self.assertEqual(
                ms.return_value, self.lxd.certificate_show('ABCDEF01'))
            ms.assert_called_with('GET',
                                  '/1.0/certificates/ABCDEF01')

    @annotated_data(
        ('delete', 'DELETE', '/ABCDEF01'),
        ('create', 'POST', '', (json.dumps('ABCDEF01'),)),
    )
    def test_certificate_operations(self, method, http, path, call_args=()):
        with mock.patch.object(connection.LXDConnection, 'get_status') as ms:
            ms.return_value = True
            self.assertTrue(
                getattr(self.lxd, 'certificate_' + method)('ABCDEF01'))
            ms.assert_called_with(http,
                                  '/1.0/certificates' + path,
                                  *call_args)
