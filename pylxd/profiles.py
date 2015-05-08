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

class LXDProfile(object):
    def __init__(self, connection):
        self.connection = connection

    def _make_request(self, *args, **kwargs):
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()
        data = json.loads(response.read())
        return (response.status, data)
