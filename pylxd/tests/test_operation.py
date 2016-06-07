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

from pylxd import operation
from pylxd.tests import testing


class TestOperation(testing.PyLXDTestCase):
    """Tests for pylxd.operation.Operation."""

    def test_get(self):
        """Return an operation."""
        name = 'operation-abc'

        an_operation = operation.Operation.get(self.client, name)

        self.assertEqual(name, an_operation.id)

    def test_get_full_path(self):
        """Return an operation even if the full path is specified."""
        name = '/1.0/operations/operation-abc'

        an_operation = operation.Operation.get(self.client, name)

        self.assertEqual('operation-abc', an_operation.id)
