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

import httplib
import json
import os
import socket
import ssl

from . import utils


class UnixHTTPConnection(httplib.HTTPConnection):

    def __init__(self, path, host='localhost', port=None, strict=None,
                 timeout=None):
        httplib.HTTPConnection.__init__(self, host, port=port,
                                        strict=strict,
                                        timeout=timeout)

        self.path = path

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock


class HTTPSConnection(httplib.HTTPConnection):
    default_port = 8443

    def __init__(self, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, *args, **kwargs)

    def connect(self):
        sock = socket.create_connection((self.host, self.port),
                                        self.timeout, self.source_address)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        (cert_file, key_file) = self._get_ssl_certs()
        self.sock = ssl.wrap_socket(sock, certfile=cert_file,
                                    keyfile=key_file)

    @staticmethod
    def _get_ssl_certs():
        return (os.path.join(os.environ['HOME'], '.config/lxc/client.crt'),
                os.path.join(os.environ['HOME'], '.config/lxc/client.key'))


class LXDConnection(object):

    def __init__(self):
        self.unix_socket = '/var/lib/lxd/unix.socket'
        self.connection = None

    def get_connection(self):
        return UnixHTTPConnection(self.unix_socket)

    def get_object(self, *args, **kwargs):
        self.connection = self.get_connection()
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()
        (state, data) = json.loads(response.read())
        if not data:
            msg = "Null Data"
            raise Exception(msg)
        elif state == 200 or \
                (state == 202 and data.get('status_code') == 100):
            return state, data
        else:
            utils.get_lxd_error(state, data)

    def get_status(self, *args, **kwargs):
        status = False
        self.connection = self.get_connection()
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()
        (state, data) = json.loads(response.read())
        if not data:
            msg = "Null Data"
            raise Exception(msg)
        elif state == 200 or \
                (state == 202 and data.get('status_code') == 100):
            status = True
        else:
            utils.get_lxd_error(state, data)
        return status

    def get_raw(self, *args, **kwargs):
        self.connection = self.get_connection()
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()
        body = response.read()
        if not body:
            msg = "Null Body"
            raise Exception(msg)
        elif response.status == 200:
            return body
        else:
            msg = "Failed to get raw response"
            raise Exception(msg)
