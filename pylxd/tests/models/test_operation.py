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

from pylxd import exceptions, models
from pylxd.tests import testing


class TestOperation(testing.PyLXDTestCase):
    """Tests for pylxd.models.Operation."""

    def test_get(self):
        """Return an operation."""
        name = 'operation-abc'

        an_operation = models.Operation.get(self.client, name)

        self.assertEqual(name, an_operation.id)

    def test_get_full_path(self):
        """Return an operation even if the full path is specified."""
        name = '/1.0/operations/operation-abc'

        an_operation = models.Operation.get(self.client, name)

        self.assertEqual('operation-abc', an_operation.id)

    def test_wait_with_error(self):
        """If the operation errors, wait raises an exception."""
        def error(request, context):
            context.status_code = 200
            return {
                'type': 'sync',
                'metadata': {
                    'status': 'Failure',
                    'err': 'Keep your foot off the blasted samoflange.',
                }}
        self.add_rule({
            'json': error,
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/operations/operation-abc/wait$',  # NOQA
        })

        name = '/1.0/operations/operation-abc'

        an_operation = models.Operation.get(self.client, name)

        self.assertRaises(exceptions.LXDAPIException, an_operation.wait)
