
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
from . import container
from . import certificate
from . import hosts
from . import image
from . import network
from . import profiles

class Client(object):
    def __init__(self, base_url, host):
        self.unix_socket = '/var/lib/lxd/unix.socket'
        self.base_url = base_url
        self.host = host

        if base_url == 'https':
            self.connection = connection.HTTPSConnection(host, port="8443")
        else:
            self.connection = connection.UnixHTTPConnection(self.unix_socket)

        self.hosts = hosts.LXDHost(self.connection)
        self.certificate = certificate.LXDCertificate(self.connection)
        self.image = image.LXDImage(self.connection)
        self.network = network.LXDNetwork(self.connection)
        self.container = container.LXDContainer(self.connection)
        self.profile = profiles.LXDProfile(self.connection)

    # host
    def host_ping(self):
        return self.hosts.host_ping()

    def host_info(self):
        return self.hosts.host_info()

    # images
    def image_list(self):
        pass

    def image_list_by_key(self):
        pass

    def image_upload(self):
        pass

    def image_info(self):
        pass

    def image_delete(self):
        pass

    def image_export(self):
        pass

    # alias
    def alias_list(self):
        pass

    def alias_create(self):
        pass

    def alias_update(self):
        pass

    def alias_delete(self):
        pass

    # containers:
    def container_init(self):
        pass

    def container_start(self):
        pass

    def container_stop(self):
        pass

    def container_destroy(self):
        pass

    def container_suspend(self):
        pass

    def container_reboot(self):
        pass

    def container_info(self):
        pass

    def container_resume(self):
        pass

    def get_container_log(self):
        pass

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

    # certificates
    def certificate_list(self):
        pass

    def certificate_show(self):
        pass

    # profiles
    def profile_init(self):
        pass

    def profile_show(self):
        pass

    def profile_update(self):
        pass

    def profile_delete(self):
        pass

    # lxd operations
    def list_operations(self):
        pass

    def get_container_operation(self):
        pass

    # networks
    def network_list(self):
        pass

    def network_show(self):
        pass
