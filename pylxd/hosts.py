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

import json

from . import utils

class LXDHost(object):
    def __init__(self, connection):
        self.connection = connection

    def _make_request(self, *args, **kwargs):
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()
        data = json.loads(response.read())
        return response.status, data

    def host_ping(self):
        try:
            host_up = False
            (state, data) = self._make_request('GET', '/1.0')
            if state == 200 or (state == 202 and data.get('status_code') == 100):
                host_up = True
            else:
                utils.get_container_error(state, data)
            return host_up
        except Exception:
            msg = ('LXD service is unavailable.')
            raise Exception(msg)

    def host_info(self):
        (state, data) = self._make_request('GET', '/1.0')
        if state == 200 or (state == 202 and data.get('status_code') == 100):
            metadata = data.get('metadata')

            return {
                'lxd_api_compat_level': self.get_lxd_api_compat(metadata)
            }

    def get_lxd_api_compat(self, metadata):
        return metadata['api_compat']