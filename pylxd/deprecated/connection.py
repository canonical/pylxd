# Copyright (c) 2015 Canonical Ltd
# Copyright (c) 2015 Mirantis inc.
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

import copy
import json
import os
import queue
import socket
import ssl
import threading
from http import client as http_client
from typing import Any, NamedTuple

from ws4py.client import WebSocketBaseClient

from pylxd.deprecated import exceptions, utils

DEFAULT_TLS_VERSION = ssl.PROTOCOL_TLSv1_2


class UnixHTTPConnection(http_client.HTTPConnection):
    def __init__(self, path, host="localhost", port=None, strict=None, timeout=None):
        http_client.HTTPConnection.__init__(self, host, port=port, timeout=timeout)

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
        sock = socket.create_connection(
            (self.host, self.port), self.timeout, self.source_address
        )
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        (cert_file, key_file) = self._get_ssl_certs()
        self.sock = ssl.wrap_socket(
            sock, certfile=cert_file, keyfile=key_file, ssl_version=DEFAULT_TLS_VERSION
        )

    @staticmethod
    def _get_ssl_certs():
        return (
            os.path.join(os.environ["HOME"], ".config/lxc/client.crt"),
            os.path.join(os.environ["HOME"], ".config/lxc/client.key"),
        )


class _LXDResponse(NamedTuple):

    status: int
    body: bytes
    json: Any


class WebSocketClient(WebSocketBaseClient):
    def __init__(
        self, url, protocols=None, extensions=None, ssl_options=None, headers=None
    ):
        """WebSocket client that executes into a eventlet green thread."""
        WebSocketBaseClient.__init__(
            self,
            url,
            protocols,
            extensions,
            ssl_options=ssl_options,
            headers=headers,
        )
        self._th = threading.Thread(target=self.run, name="WebSocketClient")
        self._th.daemon = True

        self.messages = queue.Queue()

    def handshake_ok(self):
        """Starts the client's thread."""
        self._th.start()

    def received_message(self, message):
        """Override the base class to store the incoming message."""
        self.messages.put(copy.deepcopy(message))

    def closed(self, code, reason=None):
        # When the connection is closed, put a StopIteration
        # on the message queue to signal there's nothing left
        # to wait for
        self.messages.put(StopIteration)

    def receive(self):
        # If the websocket was terminated and there are no messages
        # left in the queue, return None immediately otherwise the client
        # will block forever
        if self.terminated and self.messages.empty():
            return None
        message = self.messages.get()
        if message is StopIteration:
            return None
        return message


class LXDConnection:
    def __init__(self, host=None, port=8443):
        if host:
            self.host = host
            self.port = port
            self.unix_socket = None
        else:
            if "LXD_DIR" in os.environ:
                self.unix_socket = os.path.join(os.environ["LXD_DIR"], "unix.socket")
            else:
                self.unix_socket = "/var/lib/lxd/unix.socket"
            self.host, self.port = None, None
        self.connection = None

    def _request(self, *args, **kwargs):
        if self.connection is None:
            self.connection = self.get_connection()
        self.connection.request(*args, **kwargs)
        response = self.connection.getresponse()

        status = response.status
        raw_body = response.read()
        try:
            body = json.loads(raw_body.decode())
        except ValueError:
            body = None

        return _LXDResponse(status, raw_body, body)

    def get_connection(self):
        if self.host:
            return HTTPSConnection(self.host, self.port)
        return UnixHTTPConnection(self.unix_socket)

    def get_object(self, *args, **kwargs):
        response = self._request(*args, **kwargs)

        if not response.json:
            raise exceptions.PyLXDException("Null Data")
        elif response.status == 200 or (
            response.status == 202 and response.json.get("status_code") == 100
        ):
            return response.status, response.json
        else:
            utils.get_lxd_error(response.status, response.json)

    def get_status(self, *args, **kwargs):
        response = self._request(*args, **kwargs)

        if not response.json:
            raise exceptions.PyLXDException("Null Data")
        elif response.json.get("error"):
            utils.get_lxd_error(response.status, response.json)
        elif response.status == 200 or (
            response.status == 202 and response.json.get("status_code") == 100
        ):
            return True
        return False

    def get_raw(self, *args, **kwargs):
        response = self._request(*args, **kwargs)

        if not response.body:
            raise exceptions.PyLXDException("Null Body")
        elif response.status == 200:
            return response.body
        else:
            raise exceptions.PyLXDException("Failed to get raw response")

    def get_ws(self, path):
        if self.unix_socket:
            connection_string = "ws+unix://%s" % self.unix_socket
        else:
            connection_string = "wss://%(host)s:%(port)s" % {
                "host": self.host,
                "port": self.port,
            }

        ws = WebSocketClient(connection_string)
        ws.resource = path
        ws.connect()

        return ws
