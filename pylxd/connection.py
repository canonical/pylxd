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
import os
import socket
import ssl

from pylxd import exceptions
from pylxd import utils
from six.moves import http_client


class UnixHTTPConnection(http_client.HTTPConnection):

    def __init__(self, path, host='localhost', port=None, strict=None,
                 timeout=None):
        http_client.HTTPConnection.__init__(self, host, port=port,
                                            strict=strict,
                                            timeout=timeout)

        self.path = path

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock


class HTTPSConnection(http_client.HTTPConnection):
    default_port = 8443

    def __init__(self, *args, **kwargs):
        http_client.HTTPConnection.__init__(self, *args, **kwargs)

    def connect(self):
        sock = socket.create_connection((self.host, self.port),
                                        self.timeout, self.source_address)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        (cert_file, key_file) = self._get_ssl_certs()
        self.sock = ssl.wrap_socket(sock, certfile=cert_file,
                                    keyfile=key_file,
                                    ssl_version=ssl.PROTOCOL_TLSv1_2)

    @staticmethod
    def _get_ssl_certs():
        return (os.path.join(os.environ['HOME'], '.config/lxc/client.crt'),
                os.path.join(os.environ['HOME'], '.config/lxc/client.key'))


class LXDConnection(object):

    def __init__(self, host=None, port=8443):
        if host:
            self.host = host
            self.port = port
            self.unix_socket = None
        else:
            if 'LXD_DIR' in os.environ:
                self.unix_socket = os.path.join(os.environ['LXD_DIR'],
                                                'unix.socket')
            else:
                self.unix_socket = '/var/lib/lxd/unix.socket'
            self.host, self.port = None, None
        self.connection = None

    def get_connection(self):
        if self.host:
            return HTTPSConnection(self.host, self.port)
        return UnixHTTPConnection(self.unix_socket)

    def get_object(self, *args, **kwargs):
        self.connection = self.get_connection()
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()
        state = response.status
        data = json.loads(response.read())
        if not data:
            msg = "Null Data"
            raise exceptions.PyLXDException(msg)
        elif state == 200 or (state == 202 and data.get('status_code') == 100):
            return state, data
        else:
            utils.get_lxd_error(state, data)

    def get_status(self, *args, **kwargs):
        status = False
        self.connection = self.get_connection()
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()
        state = response.status
        data = json.loads(response.read())
        if not data:
            msg = "Null Data"
            raise exceptions.PyLXDException(msg)
        elif data.get('error'):
            utils.get_lxd_error(state, data)
        elif state == 200 or (state == 202 and data.get('status_code') == 100):
            status = True
        return status

    def get_raw(self, *args, **kwargs):
        self.connection = self.get_connection()
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()
        body = response.read()
        if not body:
            msg = "Null Body"
            raise exceptions.PyLXDException(msg)
        elif response.status == 200:
            return body
        else:
            msg = "Failed to get raw response"
            raise exceptions.PyLXDException(msg)

    def get_ws(self, *args, **kwargs):
        self.connection = self.get_connection()
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()
        return response.status
