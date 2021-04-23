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

import inspect
import socket
from http import client as http_client
from io import BytesIO
from unittest import TestCase, mock

from ddt import ddt

from pylxd.deprecated import connection, exceptions
from pylxd.deprecated.tests import annotated_data


@ddt
class LXDInitConnectionTest(TestCase):
    @mock.patch("socket.socket")
    @mock.patch.object(http_client.HTTPConnection, "__init__")
    def test_http_connection(self, mc, ms):
        conn = connection.UnixHTTPConnection("/", "host", 1234)
        mc.assert_called_once_with(conn, "host", port=1234, timeout=None)
        conn.connect()
        ms.assert_called_once_with(socket.AF_UNIX, socket.SOCK_STREAM)
        ms.return_value.connect.assert_called_once_with("/")

    @mock.patch("os.environ", {"HOME": "/home/foo"})
    @mock.patch("ssl.wrap_socket")
    @mock.patch("socket.create_connection")
    def test_https_connection(self, ms, ml):
        conn = connection.HTTPSConnection("host", 1234)
        with mock.patch.object(conn, "_tunnel") as mc:
            conn.connect()
            self.assertFalse(mc.called)
            ms.assert_called_once_with(
                ("host", 1234), socket._GLOBAL_DEFAULT_TIMEOUT, None
            )
            ml.assert_called_once_with(
                ms.return_value,
                certfile="/home/foo/.config/lxc/client.crt",
                keyfile="/home/foo/.config/lxc/client.key",
                ssl_version=connection.DEFAULT_TLS_VERSION,
            )

    @mock.patch("os.environ", {"HOME": "/home/foo"})
    @mock.patch("ssl.wrap_socket")
    @mock.patch("socket.create_connection")
    def test_https_proxy_connection(self, ms, ml):
        conn = connection.HTTPSConnection("host", 1234)
        conn._tunnel_host = "host"
        with mock.patch.object(conn, "_tunnel") as mc:
            conn.connect()
            self.assertTrue(mc.called)
            ms.assert_called_once_with(
                ("host", 1234), socket._GLOBAL_DEFAULT_TIMEOUT, None
            )
            ml.assert_called_once_with(
                ms.return_value,
                certfile="/home/foo/.config/lxc/client.crt",
                keyfile="/home/foo/.config/lxc/client.key",
                ssl_version=connection.DEFAULT_TLS_VERSION,
            )

    @mock.patch("pylxd.deprecated.connection.HTTPSConnection")
    @mock.patch("pylxd.deprecated.connection.UnixHTTPConnection")
    @annotated_data(
        ("unix", (None,), {}, "/var/lib/lxd/unix.socket"),
        ("unix_path", (None,), {"LXD_DIR": "/fake/"}, "/fake/unix.socket"),
        ("https", ("host",), {}, ""),
        ("https_port", ("host", 1234), {}, ""),
    )
    def test_get_connection(self, mode, args, env, path, mc, ms):
        with mock.patch("os.environ", env):
            conn = connection.LXDConnection(*args).get_connection()
            if mode.startswith("unix"):
                self.assertEqual(mc.return_value, conn)
                mc.assert_called_once_with(path)
            elif mode.startswith("https"):
                self.assertEqual(ms.return_value, conn)
                ms.assert_called_once_with(args[0], len(args) == 2 and args[1] or 8443)


class FakeResponse:
    def __init__(self, status, data):
        self.status = status
        self.read = BytesIO(bytes(data, "utf-8")).read


@ddt
@mock.patch("pylxd.deprecated.connection.LXDConnection.get_connection")
class LXDConnectionTest(TestCase):
    def setUp(self):
        super().setUp()
        self.conn = connection.LXDConnection()

    @annotated_data(
        ("null", (200, "{}"), exceptions.PyLXDException),
        ("200", (200, '{"foo": "bar"}'), (200, {"foo": "bar"})),
        ("202", (202, '{"status_code": 100}'), (202, {"status_code": 100})),
        ("500", (500, '{"foo": "bar"}'), exceptions.APIError),
    )
    def test_get_object(self, tag, effect, result, mg):
        mg.return_value.getresponse.return_value = FakeResponse(*effect)
        if inspect.isclass(result):
            self.assertRaises(result, self.conn.get_object)
        else:
            self.assertEqual(result, self.conn.get_object())

    @annotated_data(
        ("null", (200, "{}"), exceptions.PyLXDException),
        ("200", (200, '{"foo": "bar"}'), True),
        ("202", (202, '{"status_code": 100}'), True),
        ("200", (200, '{"error": "bar"}'), exceptions.APIError),
        ("500", (500, '{"foo": "bar"}'), False),
    )
    def test_get_status(self, tag, effect, result, mg):
        mg.return_value.getresponse.return_value = FakeResponse(*effect)
        if inspect.isclass(result):
            self.assertRaises(result, self.conn.get_status)
        else:
            self.assertEqual(result, self.conn.get_status())

    @annotated_data(
        ("null", (200, ""), exceptions.PyLXDException),
        ("200", (200, '{"foo": "bar"}'), b'{"foo": "bar"}'),
        ("500", (500, '{"foo": "bar"}'), exceptions.PyLXDException),
    )
    def test_get_raw(self, tag, effect, result, mg):
        mg.return_value.getresponse.return_value = FakeResponse(*effect)
        if inspect.isclass(result):
            self.assertRaises(result, self.conn.get_raw)
        else:
            self.assertEqual(result, self.conn.get_raw())

    @mock.patch("pylxd.deprecated.connection.WebSocketClient")
    @annotated_data(
        ("fake_host", "wss://fake_host:8443"),
        (None, "ws+unix:///var/lib/lxd/unix.socket"),
    )
    def test_get_ws(self, host, result, mock_ws, _):
        conn = connection.LXDConnection(host)

        conn.get_ws("/fake/path")

        mock_ws.assert_has_calls([mock.call(result), mock.call().connect()])
