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


class Waitable(object):

    def get_operation(self, operation_id):
        if operation_id.startswith('/'):
            operation_id = operation_id.split('/')[-1]
        return self._client.operations.get(operation_id)

    def wait_for_operation(self, operation_id):
        operation = self.get_operation(operation_id)
        operation.wait()
        return operation


class Marshallable(object):

    def marshall(self):
        marshalled = {}
        for name in self.__slots__:
            if name.startswith('_'):
                continue
            marshalled[name] = getattr(self, name)
        return marshalled
