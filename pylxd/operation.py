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
from pylxd import exceptions


class Operation(object):
    """A LXD operation."""

    __slots__ = [
        '_client',
        'class', 'created_at', 'err', 'id', 'may_cancel', 'metadata',
        'resources', 'status', 'status_code', 'updated_at']

    @classmethod
    def wait_for_operation(cls, client, operation_id):
        """Get an operation and wait for it to complete."""
        operation = cls.get(client, operation_id)
        operation.wait()
        return cls.get(client, operation.id)

    @classmethod
    def get(cls, client, operation_id):
        """Get an operation."""
        if operation_id.startswith('/'):
            operation_id = operation_id.split('/')[-1]
        response = client.api.operations[operation_id].get()
        return cls(_client=client, **response.json()['metadata'])

    def __init__(self, **kwargs):
        super(Operation, self).__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def wait(self):
        """Wait for the operation to complete and return."""
        response = self._client.api.operations[self.id].wait.get()

        try:
            if response.json()['metadata']['status'] == 'Failure':
                raise exceptions.LXDAPIException(response)
        except KeyError:
            # Support for legacy LXD
            pass
