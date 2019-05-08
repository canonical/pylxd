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

import json
import mock

from pylxd import exceptions, models
from pylxd.tests import testing


class TestOperation(testing.PyLXDTestCase):
    """Tests for pylxd.models.Operation."""

    @mock.patch.dict('os.environ', {'PYLXD_WARNINGS': ''})
    @mock.patch('warnings.warn')
    def test_init_warnings_once(self, mock_warn):
        with mock.patch('pylxd.models.operation._seen_attribute_warnings',
                        new=set()):
            models.Operation(unknown='some_value')
            mock_warn.assert_called_once_with(mock.ANY)
            models.Operation(unknown='some_value_as_well')
            mock_warn.assert_called_once_with(mock.ANY)
            models.Operation(unknown2="some_2nd_value")
            self.assertEqual(len(mock_warn.call_args_list), 2)

    @mock.patch.dict('os.environ', {'PYLXD_WARNINGS': 'none'})
    @mock.patch('warnings.warn')
    def test_init_warnings_none(self, mock_warn):
        with mock.patch('pylxd.models.operation._seen_attribute_warnings',
                        new=set()):
            models.Operation(unknown='some_value')
            mock_warn.assert_not_called()

    @mock.patch.dict('os.environ', {'PYLXD_WARNINGS': 'always'})
    @mock.patch('warnings.warn')
    def test_init_warnings_always(self, mock_warn):
        with mock.patch('pylxd.models.operation._seen_attribute_warnings',
                        new=set()):
            models.Operation(unknown='some_value')
            mock_warn.assert_called_once_with(mock.ANY)
            models.Operation(unknown='some_value_as_well')
            self.assertEqual(len(mock_warn.call_args_list), 2)

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

    def test_get_full_path_and_project(self):
        """Return an operation even if the full path is specified."""
        name = '/1.0/operations/operation-abc?project=default'

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

    def test_unknown_attribute(self):
        self.add_rule({
            'text': json.dumps({
                'type': 'sync',
                'metadata': {'id': 'operation-unknown',
                             'metadata': {'return': 0},
                             'unknown': False},
                }),
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/operations/operation-unknown$',
        })
        url = '/1.0/operations/operation-unknown'
        models.Operation.get(self.client, url)
