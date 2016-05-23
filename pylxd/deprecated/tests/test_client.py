# Copyright (c) 2016 Canonical Ltd
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
"""Tests for pylxd.client."""
import unittest

import mock

from pylxd import client


class Test_APINode(unittest.TestCase):
    """Tests for pylxd.client._APINode."""
    ROOT = 'http://lxd/api'

    def test_getattr(self):
        """`__getattr__` returns a nested node."""
        lxd = client._APINode(self.ROOT)

        self.assertEqual('{}/fake'.format(self.ROOT), lxd.fake._api_endpoint)

    def test_getattr_nested(self):
        """Nested objects return a more detailed path."""
        lxd = client._APINode(self.ROOT)  # NOQA

        self.assertEqual(
            '{}/fake/path'.format(self.ROOT),
            lxd.fake.path._api_endpoint)

    def test_getitem(self):
        """`__getitem__` enables dynamic url parts."""
        lxd = client._APINode(self.ROOT)  # NOQA

        self.assertEqual(
            '{}/fake/path'.format(self.ROOT),
            lxd.fake['path']._api_endpoint)

    def test_getitem_integer(self):
        """`__getitem__` with an integer allows dynamic integer url parts."""
        lxd = client._APINode(self.ROOT)  # NOQA

        self.assertEqual(
            '{}/fake/0'.format(self.ROOT),
            lxd.fake[0]._api_endpoint)

    @mock.patch('pylxd.client.requests.request')
    def test_get(self, _request):
        """`get` will make a request to the smart url."""
        lxd = client._APINode(self.ROOT)

        lxd.fake.get()

        _request.assert_called_once_with(
            'GET',
            '{}/{}'.format(self.ROOT, 'fake')
        )

    @mock.patch('pylxd.client.requests.request')
    def test_post(self, _request):
        """`post` will POST to the smart url."""
        lxd = client._APINode(self.ROOT)

        lxd.fake.post()

        _request.assert_called_once_with(
            'POST',
            '{}/{}'.format(self.ROOT, 'fake')
        )

    @mock.patch('pylxd.client.requests.request')
    def test_put(self, _request):
        """`put` will PUT to the smart url."""
        lxd = client._APINode(self.ROOT)

        lxd.fake.put()

        _request.assert_called_once_with(
            'PUT',
            '{}/{}'.format(self.ROOT, 'fake')
        )

    @mock.patch('pylxd.client.requests.request')
    def test_delete(self, _request):
        """`delete` will DELETE to the smart url."""
        lxd = client._APINode(self.ROOT)

        lxd.fake.delete()

        _request.assert_called_once_with(
            'DELETE',
            '{}/{}'.format(self.ROOT, 'fake')
        )
