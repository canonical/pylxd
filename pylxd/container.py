
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

from . import connection

class LXDContainer(object):
    def __init__(self):
        self.connection = connection.LXDConnection()

    # containers:
    def container_list(self):
        (state, data) = self.connection.get_object('GET', '/1.0/containers')
        return [container.split('/1.0/images/')[-1] for container in data['metadata']]

    def container_init(self, container):
        return self.connection.get_object('POST', '/1.0/containers',
                                          json.dumps(container))

    def container_state(self, container):
        (state, data) = self.connection.get_object('GET', '/1.0/containers/%s/state'
                                                   % container)
        return data.get('status')


    def container_start(self, container, timeout):
        action = {'action': 'start', 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_stop(self, container, timeout):
        action = {'action': 'stop', 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_suspend(self, container, timeout):
        action = {'action': 'freeze', 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_resume(self, container, timeout):
        action = {'action': 'unfreeze', 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_reboot(self, container, timeout):
        action = {'action': 'restart', 'timeout': timeout}
        return self.connection.get_object('PUT', '/1.0/containers/%s/state'
                                          % container,
                                          json.dumps(action))

    def container_destroy(self, container):
        return self.connection.get_object('DELETE', '/1.0/containers/%s'
                                          % container)

    def get_container_log(self, container):
        (status, data) = self.connection.get_object('GET', '/1.0/containers/%s?log=true'
                                                            % container)
        print data

    def get_container_console(self):
        pass

    def get_container_syslog(self):
        pass

    # container state
    def get_container_state(self):
        pass

    def update_container_state(self):
        pass

    # file operations
    def get_container_file(self):
        pass

    def put_container_file(self):
        pass

    # snapshots
    def container_snapshot_list(self):
        pass

    def container_snapshot_create(self):
        pass

    def container_snapshot_info(self):
        pass

    def container_snaphsot_delete(self):
        pass

    def container_run_command(self):
        pass
