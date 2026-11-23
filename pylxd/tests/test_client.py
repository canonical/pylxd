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
import base64
import contextlib
import datetime
import hashlib
import ipaddress
import json
import os
import re
import socket
import ssl
import threading
from types import MappingProxyType
from unittest import TestCase, mock
from urllib import parse

import pytest
import requests
import requests.adapters
import requests.certs
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from ws4py.client import WebSocketBaseClient

from pylxd import client, exceptions

CERT = os.path.join(os.path.dirname(__file__), "lxd.crt")
KEY = os.path.join(os.path.dirname(__file__), "lxd.key")


class TestClient(TestCase):
    """Tests for pylxd.client.Client."""

    def setUp(self):
        self.get_patcher = mock.patch("pylxd.client._APINode.get")
        self.get = self.get_patcher.start()

        self.post_patcher = mock.patch("pylxd.client._APINode.post")
        self.post = self.post_patcher.start()

        response = mock.MagicMock(status_code=200)
        response.json.return_value = {
            "metadata": {
                "auth": "trusted",
                "environment": {"storage": "zfs"},
            }
        }
        self.get.return_value = response

        post_response = mock.MagicMock(status_code=200)
        self.post.return_value = post_response

    def tearDown(self):
        self.get_patcher.stop()
        self.post_patcher.stop()

    @mock.patch("os.path.exists")
    def test_create(self, _path_exists):
        """Client creation sets default API endpoint."""
        _path_exists.return_value = False
        expected = "http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket/1.0"

        an_client = client.Client()

        self.assertEqual(expected, an_client.api._api_endpoint)

    @mock.patch("os.path.exists")
    @mock.patch("os.environ")
    def test_create_with_snap_lxd(self, _environ, _path_exists):
        """Client creation sets default API endpoint."""
        _path_exists.return_value = True
        expected = "http+unix://%2Fvar%2Fsnap%2Flxd%2F" "common%2Flxd%2Funix.socket/1.0"

        an_client = client.Client()
        self.assertEqual(expected, an_client.api._api_endpoint)

    @mock.patch.dict(os.environ, {"LXD_DIR": "/lxd"})
    def test_create_LXD_DIR(self):
        """When LXD_DIR is set, use it in the client."""
        expected = "http+unix://%2Flxd%2Funix.socket/1.0"

        an_client = client.Client()

        self.assertEqual(expected, an_client.api._api_endpoint)

    def test_create_endpoint(self):
        """Explicitly set the client endpoint."""
        endpoint = "http://lxd"
        expected = "http://lxd/1.0"

        an_client = client.Client(endpoint=endpoint)

        self.assertEqual(expected, an_client.api._api_endpoint)

    def test_create_endpoint_verify_false_ignores_saved_cert(self):
        """An explicit verify=False is not replaced by a saved server cert."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            servercerts = os.path.join(tmpdir, "servercerts")
            os.makedirs(servercerts)
            cert_path = os.path.join(servercerts, "lxd.local.crt")
            with open(cert_path, "w") as fd:
                fd.write("dummy")

            with mock.patch.object(client, "CERTS_PATH", tmpdir):
                a_client = client.Client("https://lxd.local:8443", verify=False)

        self.assertIs(a_client.api.session.verify, False)
        self.assertNotIsInstance(
            a_client.api.session.get_adapter("https://lxd.local:8443/1.0"),
            client.LXDSSLAdapter,
        )

    def test_create_endpoint_verify_true_uses_saved_cert(self):
        """verify=True discovers and uses an existing saved server cert."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            servercerts = os.path.join(tmpdir, "servercerts")
            os.makedirs(servercerts)
            cert_path = os.path.join(servercerts, "lxd.local.crt")
            with open(cert_path, "w") as fd:
                fd.write("dummy")

            with mock.patch.object(client, "CERTS_PATH", tmpdir):
                a_client = client.Client("https://lxd.local:8443", verify=True)

        self.assertEqual(a_client.api.session.verify, cert_path)
        self.assertIsInstance(
            a_client.api.session.get_adapter("https://lxd.local:8443/1.0"),
            client.LXDSSLAdapter,
        )

    def test_create_endpoint_with_project(self):
        """Explicitly set the client endpoint."""
        response = mock.MagicMock(status_code=200)
        response.json.side_effect = [
            {
                "metadata": {
                    "auth": "untrusted",
                    "api_extensions": ["projects"],
                }
            },
        ]
        self.get.return_value = response

        endpoint = "/tmp/unix.socket"
        expected = "http+unix://%2Ftmp%2Funix.socket/1.0"

        with mock.patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            a_client = client.Client(endpoint=endpoint, project="prj")

        self.assertEqual(a_client.api._api_endpoint, expected)
        self.assertEqual(a_client.api._project, "prj")

    def test_create_endpoint_unixsocket(self):
        """Test with unix socket endpoint."""
        endpoint = "/tmp/unix.socket"
        expected = "http+unix://%2Ftmp%2Funix.socket/1.0"

        with mock.patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            a_client = client.Client(endpoint)

        self.assertEqual(expected, a_client.api._api_endpoint)

    def test_connection_404(self):
        """If the endpoint 404s, an exception is raised."""
        import requests_mock

        self.get_patcher.stop()
        with requests_mock.Mocker() as m:
            m.get("http://lxd/1.0", status_code=404, json={"error": "not found"})
            with self.assertRaises(exceptions.ClientConnectionFailed) as ctx:
                client.Client("http://lxd")
        self.assertEqual("not found", str(ctx.exception))

    def test_connection_api_error(self):
        """If the endpoint returns an API error, ClientConnectionFailed is raised."""
        import requests_mock

        self.get_patcher.stop()
        with requests_mock.Mocker() as m:
            m.get(
                "http://lxd/1.0",
                status_code=500,
                json={"error": "internal server error"},
            )
            with self.assertRaises(exceptions.ClientConnectionFailed) as ctx:
                client.Client("http://lxd")
        self.assertEqual("internal server error", str(ctx.exception))

    def test_connection_failed(self):
        """If the connection fails, an exception is raised."""

        def raise_exception():
            raise requests.exceptions.ConnectionError()

        self.get.side_effect = raise_exception
        self.get.return_value = None

        self.assertRaises(exceptions.ClientConnectionFailed, client.Client)

    def test_connection_untrusted(self):
        """Client.trusted is False when certs are untrusted."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {"metadata": {"auth": "untrusted"}}
        self.get.return_value = response

        an_client = client.Client()

        self.assertFalse(an_client.trusted)

    def test_connection_trusted(self):
        """Client.trusted is True when certs are untrusted."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {"metadata": {"auth": "trusted"}}
        self.get.return_value = response

        an_client = client.Client()

        self.assertTrue(an_client.trusted)

    def test_server_clustered_false_no_info(self):
        """Client.server_clustered is False if the info is not available in metadata."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {"metadata": {"environment": {}}}
        self.get.return_value = response
        a_client = client.Client()
        self.assertFalse(a_client.server_clustered)

    def test_server_clustered_false(self):
        """Client.server_clustered is False if not clustered."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {
            "metadata": {"environment": {"server_clustered": False}}
        }
        self.get.return_value = response
        a_client = client.Client()
        self.assertFalse(a_client.server_clustered)

    def test_server_clustered_true(self):
        """Client.server_clustered is True if clustered."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {
            "metadata": {"environment": {"server_clustered": True}}
        }
        self.get.return_value = response
        a_client = client.Client()
        self.assertTrue(a_client.server_clustered)

    def test_authenticate(self):
        """A client is authenticated."""
        response = mock.MagicMock(status_code=200)
        response.json.side_effect = [
            {
                "metadata": {
                    "auth": "untrusted",
                    "api_extensions": ["explicit_trust_token"],
                }
            },
            {
                "metadata": {
                    "type": "client",
                    "fingerprint": "eaf55b72fc23aa516d709271df9b0116064bf8cfa009cf34c67c33ad32c2320c",
                }
            },
            {"metadata": {"auth": "trusted"}},
        ]
        self.get.return_value = response

        certs = (
            os.path.join(os.path.dirname(__file__), "lxd.crt"),
            os.path.join(os.path.dirname(__file__), "lxd.key"),
        )
        an_client = client.Client("https://lxd", cert=certs)

        an_client.authenticate("test-password")

        self.assertTrue(an_client.trusted)

    def test_authenticate_with_project(self):
        """A client is authenticated with a project."""
        response = mock.MagicMock(status_code=200)
        response.json.side_effect = [
            {
                "metadata": {
                    "auth": "untrusted",
                    "api_extensions": ["projects"],
                }
            },
            {
                "metadata": {
                    "type": "client",
                    "fingerprint": "eaf55b72fc23aa516d709271df9b0116064bf8cfa009cf34c67c33ad32c2320c",
                }
            },
            {
                "metadata": {
                    "auth": "trusted",
                    "environment": {"project": "test-proj"},
                }
            },
        ]
        self.get.return_value = response

        certs = (
            os.path.join(os.path.dirname(__file__), "lxd.crt"),
            os.path.join(os.path.dirname(__file__), "lxd.key"),
        )
        an_client = client.Client("https://lxd", cert=certs, project="test-proj")

        an_client.authenticate("test-password")

        self.assertTrue(an_client.trusted)
        self.assertEqual(an_client.host_info["environment"]["project"], "test-proj")

    def test_authenticate_project_not_supported(self):
        """A client raises an error if projects are not supported."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {
            "metadata": {
                "auth": "untrusted",
                "api_extensions": [],
            }
        }
        self.get.return_value = response

        with pytest.raises(exceptions.ClientConnectionFailed):
            client.Client("https://lxd", project="test-proj")

    def test_authenticate_project_not_supported_but_default(self):
        """
        A client doesn't raise an error if projects are not supported and the
        default one is requested.
        """
        response = mock.MagicMock(status_code=200)
        response.json.side_effect = [
            {
                "metadata": {
                    "auth": "untrusted",
                    "api_extensions": [],
                }
            },
            {
                "metadata": {
                    "type": "client",
                    "fingerprint": "eaf55b72fc23aa516d709271df9b0116064bf8cfa009cf34c67c33ad32c2320c",
                }
            },
            {
                "metadata": {
                    "auth": "trusted",
                    "environment": {},
                }
            },
        ]
        self.get.return_value = response

        certs = (
            os.path.join(os.path.dirname(__file__), "lxd.crt"),
            os.path.join(os.path.dirname(__file__), "lxd.key"),
        )
        an_client = client.Client("https://lxd", cert=certs, project="default")

        an_client.authenticate("test-password")

        self.assertTrue(an_client.trusted)

    def test_authenticate_already_authenticated(self):
        """If the client is already authenticated, nothing happens."""
        an_client = client.Client()

        an_client.authenticate("test-password")

        self.assertTrue(an_client.trusted)

    def test_host_info(self):
        """Perform a host query."""
        an_client = client.Client()
        self.assertEqual("zfs", an_client.host_info["environment"]["storage"])

    def test_events(self):
        """The default websocket client is returned."""
        an_client = client.Client()

        ws_client = an_client.events()

        self.assertEqual("/1.0/events", ws_client.resource)

    @mock.patch.dict(os.environ, {"LXD_DIR": "/lxd"})
    def test_events_unix_socket(self):
        """A unix socket compatible websocket client is returned."""
        websocket_client = mock.Mock(resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        an_client = client.Client()

        an_client.events(websocket_client=WebsocketClient)

        WebsocketClient.assert_called_once_with(
            "ws+unix:///lxd/unix.socket", ssl_options=None
        )

    def test_events_http(self):
        """An http compatible websocket client is returned."""
        websocket_client = mock.Mock(resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        an_client = client.Client("http://lxd.local")

        an_client.events(websocket_client=WebsocketClient)

        WebsocketClient.assert_called_once_with("ws://lxd.local", ssl_options=None)

    @mock.patch.dict(os.environ, {"REQUESTS_CA_BUNDLE": "", "CURL_CA_BUNDLE": ""})
    def test_events_https(self):
        """An https compatible websocket client is returned."""
        websocket_client = mock.Mock(spec=client._LXDWebSocketBaseClient, resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        an_client = client.Client("https://lxd.local", cert=client.DEFAULT_CERTS)

        an_client.events(websocket_client=WebsocketClient)
        ssl_options = {
            "certfile": client.DEFAULT_CERTS.cert,
            "keyfile": client.DEFAULT_CERTS.key,
            "cert_reqs": ssl.CERT_REQUIRED,
            "ca_certs": requests.certs.where(),
        }
        WebsocketClient.assert_called_once_with(
            "wss://lxd.local", ssl_options=ssl_options
        )

    def test_events_protects_a_callers_websocket_class(self):
        """A caller's ws4py class gets pylxd's TLS verification mixed in."""

        class Mine(WebSocketBaseClient):
            pass

        an_client = client.Client("https://127.0.0.1:8443", verify=CERT)
        ws_client = an_client.events(websocket_client=Mine)
        ws_client.sock.close()

        self.assertIsInstance(ws_client, Mine)
        self.assertIsInstance(ws_client, client._LXDWebSocketBaseClient)

    def test_events_refuses_a_client_it_cannot_protect(self):
        """A factory hides the class, so verification cannot be mixed in."""
        an_client = client.Client("https://127.0.0.1:8443", verify=CERT)

        with self.assertRaises(exceptions.ClientConnectionFailed):
            an_client.events(websocket_client=lambda url, **kwargs: mock.Mock())

    def test_events_takes_any_client_when_nothing_is_verified(self):
        an_client = client.Client("https://127.0.0.1:8443", verify=False)
        ws_client = mock.Mock(resource=None)

        returned = an_client.events(websocket_client=lambda url, **kwargs: ws_client)

        self.assertIs(returned, ws_client)

    def test_events_type_filter(self):
        """The websocket client can filter events by type."""

        an_client = client.Client()

        # from the itertools recipes documentation
        def powerset(types):
            from itertools import chain, combinations

            pwset = [combinations(types, r) for r in range(len(types) + 1)]
            return chain.from_iterable(pwset)

        event_path = "/1.0/events"

        for types in powerset(client.EventType):
            ws_client = an_client.events(event_types=set(types))

            actual_resource = parse.urlparse(ws_client.resource)
            expect_resource = parse.urlparse(event_path)

            if types and client.EventType.All not in types:
                type_csl = ",".join([t.value for t in types])
                query = parse.parse_qs(expect_resource.query)
                query.update({"type": type_csl})
                qs = parse.urlencode(query)
                expect_resource = expect_resource._replace(query=qs)

            self.assertEqual(expect_resource.path, actual_resource.path)

            if types and client.EventType.All not in types:
                qdict = parse.parse_qs(expect_resource.query)
                expect_types = set(qdict["type"][0].split(","))
                qdict = parse.parse_qs(actual_resource.query)
                actual_types = set(qdict["type"][0].split(","))

                self.assertEqual(expect_types, actual_types)
            else:
                self.assertEqual(expect_resource.query, actual_resource.query)

    def test_events_with_project(self):
        """The websocket resource includes the configured project query parameter."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {
            "metadata": {
                "auth": "trusted",
                "api_extensions": ["projects"],
            }
        }
        self.get.return_value = response

        a_client = client.Client(project="prj")

        ws_client = a_client.events()
        self.assertEqual("/1.0/events?project=prj", ws_client.resource)

        ws_client_all = a_client.events(event_types={client.EventType.All})
        self.assertEqual("/1.0/events?project=prj", ws_client_all.resource)

    def test_events_with_project_and_type_filter(self):
        """The websocket resource includes both project and event type filters."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {
            "metadata": {
                "auth": "trusted",
                "api_extensions": ["projects"],
            }
        }
        self.get.return_value = response

        a_client = client.Client(project="prj")
        ws_client = a_client.events(
            event_types={client.EventType.Lifecycle, client.EventType.Operation}
        )

        parsed = parse.urlparse(ws_client.resource)
        self.assertEqual("/1.0/events", parsed.path)
        qdict = parse.parse_qs(parsed.query)
        self.assertEqual(["prj"], qdict["project"])
        self.assertEqual({"lifecycle", "operation"}, set(qdict["type"][0].split(",")))

    def test_resources(self):
        a_client = client.Client()
        a_client.host_info["api_extensions"] = ["resources"]
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {
            "metadata": {
                "cpu": {},
            }
        }
        self.get.return_value = response
        self.assertIn("cpu", a_client.resources)

    def test_resources_raises_conn_failed_exception(self):
        a_client = client.Client()
        a_client.host_info["api_extensions"] = ["resources"]
        response = mock.MagicMock(status_code=400)
        self.get.return_value = response
        with self.assertRaises(exceptions.ClientConnectionFailed):
            a_client.resources

    def test_resources_raises_api_extension_not_avail_exception(self):
        a_client = client.Client()
        a_client.host_info["api_extensions"] = []
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            a_client.resources

    def test_resources_uses_cache(self):
        a_client = client.Client()
        a_client._resource_cache = {"cpu": {}}
        # Client.__init__ calls get, reset the mock before trying
        # resources to confirm it wasn't called.
        self.get.called = False
        self.assertIn("cpu", a_client.resources)
        self.assertFalse(self.get.called)

    def test_has_api_extension(self):
        a_client = client.Client()
        a_client.host_info = {"api_extensions": ["one", "two"]}
        self.assertFalse(a_client.has_api_extension("three"))
        self.assertTrue(a_client.has_api_extension("one"))
        self.assertTrue(a_client.has_api_extension("two"))

    def test_assert_has_api_extension(self):
        a_client = client.Client()
        a_client.host_info = {"api_extensions": ["one", "two"]}
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable) as c:
            self.assertFalse(a_client.assert_has_api_extension("three"))
        self.assertIn("three", str(c.exception))
        a_client.assert_has_api_extension("one")
        a_client.assert_has_api_extension("two")


class TestAPINode(TestCase):
    """Tests for pylxd.client._APINode."""

    def test_getattr(self):
        """API Nodes can use object notation for nesting."""
        node = client._APINode("http://test.com", mock.sentinel.session)
        new_node = node.test
        self.assertEqual("http://test.com/test", new_node._api_endpoint)

    def test_getattr_storage_pools(self):
        """API node with storage_pool should be storage-pool"""
        node = client._APINode("http://test.com", mock.sentinel.session)
        new_node = node.test.storage_pools
        self.assertEqual("http://test.com/test/storage-pools", new_node._api_endpoint)
        # other _ should stay as they were.
        new_node = node.test.some_thing
        self.assertEqual("http://test.com/test/some_thing", new_node._api_endpoint)

    def test_getattr_image_registries(self):
        """API node with image_registries should be image-registries"""
        node = client._APINode("http://test.com", mock.sentinel.session)
        new_node = node.test.image_registries
        self.assertEqual(
            "http://test.com/test/image-registries", new_node._api_endpoint
        )

    def test_getitem(self):
        """API Nodes can use dict notation for nesting."""
        node = client._APINode("http://test.com", mock.sentinel.session)
        new_node = node["test"]
        self.assertEqual("http://test.com/test", new_node._api_endpoint)

    def test_getitem_leave_underscores_alone(self):
        """Bug 295 erroneously changed underscores to '-' -- let's make sure
        it doesn't happen again
        """
        node = client._APINode("http://test.com", mock.sentinel.session)
        new_node = node.thing["my_snapshot"]
        self.assertEqual("http://test.com/thing/my_snapshot", new_node._api_endpoint)

    def test_session(self):
        """Session is exposed on the _APINode."""
        session = requests.Session()
        node = client._APINode("http://test.com", session)
        self.assertIs(node.session, session)

    def test_session_passed_to_child(self):
        """session should be shared across path traversal"""
        parent_node = client._APINode("http+unix://test.com", mock.sentinel.session)
        child_node = parent_node.instances
        self.assertIs(parent_node.session, child_node.session)

    @mock.patch("pylxd.client.requests.Session")
    def test_get(self, Session):
        """Perform a session get."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"type": "sync"},
            }
        )
        session = mock.Mock(**{"get.return_value": response})
        Session.return_value = session

        node = client._APINode("http://test.com", session)
        node.get()
        session.get.assert_called_once_with("http://test.com", timeout=None)

    @mock.patch("pylxd.client.requests.Session")
    def test_post(self, Session):
        """Perform a session post."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"type": "sync"},
            }
        )
        session = mock.Mock(**{"post.return_value": response})
        Session.return_value = session
        node = client._APINode("http://test.com", session)
        node.post()
        session.post.assert_called_once_with("http://test.com", timeout=None)

    @mock.patch("pylxd.client.requests.Session")
    def test_post_raw_data(self, Session):
        """A raw request body is sent as application/octet-stream."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"type": "sync"},
            }
        )
        session = mock.Mock(**{"post.return_value": response})
        Session.return_value = session
        node = client._APINode("http://test.com", session)
        node.post(data=b"raw")
        session.post.assert_called_once_with(
            "http://test.com",
            data=b"raw",
            headers={"Content-Type": "application/octet-stream"},
            timeout=None,
        )

    @mock.patch("pylxd.client.requests.Session")
    def test_post_200_not_sync(self, Session):
        """A status code of 200 with async request raises an exception."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"type": "async"},
            }
        )
        session = mock.Mock(**{"post.return_value": response})
        Session.return_value = session
        node = client._APINode("http://test.com", session)
        self.assertRaises(exceptions.LXDAPIException, node.post)

    @mock.patch("pylxd.client.requests.Session")
    def test_post_missing_type_200(self, Session):
        """A missing response type raises an exception."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {},
            }
        )
        session = mock.Mock(**{"post.return_value": response})
        Session.return_value = session
        node = client._APINode("http://test.com", session)
        self.assertRaises(exceptions.LXDAPIException, node.post)

    @mock.patch("pylxd.client.requests.Session")
    def test_put(self, Session):
        """Perform a session put."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"type": "sync"},
            }
        )
        session = mock.Mock(**{"put.return_value": response})
        Session.return_value = session
        node = client._APINode("http://test.com", session)
        node.put()
        session.put.assert_called_once_with("http://test.com", timeout=None)

    @mock.patch("pylxd.client.requests.Session")
    def test_put_raw_data(self, Session):
        """A raw request body is sent as application/octet-stream."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"type": "sync"},
            }
        )
        session = mock.Mock(**{"put.return_value": response})
        Session.return_value = session
        node = client._APINode("http://test.com", session)
        node.put(data=b"raw")
        session.put.assert_called_once_with(
            "http://test.com",
            data=b"raw",
            headers={"Content-Type": "application/octet-stream"},
            timeout=None,
        )

    @mock.patch("pylxd.client.requests.Session")
    def test_patch(self, Session):
        """Perform a session patch."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"type": "sync"},
            }
        )
        session = mock.Mock(**{"patch.return_value": response})
        Session.return_value = session
        node = client._APINode("http://test.com", session)
        node.patch()
        session.patch.assert_called_once_with("http://test.com", timeout=None)

    @mock.patch("pylxd.client.requests.Session")
    def test_patch_raw_data(self, Session):
        """A raw request body is sent as application/octet-stream."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"type": "sync"},
            }
        )
        session = mock.Mock(**{"patch.return_value": response})
        Session.return_value = session
        node = client._APINode("http://test.com", session)
        node.patch(data=b"raw")
        session.patch.assert_called_once_with(
            "http://test.com",
            data=b"raw",
            headers={"Content-Type": "application/octet-stream"},
            timeout=None,
        )

    @mock.patch("pylxd.client.requests.Session")
    def test_delete(self, Session):
        """Perform a session delete."""
        response = mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": {"type": "sync"},
            }
        )
        session = mock.Mock(**{"delete.return_value": response})
        Session.return_value = session
        node = client._APINode("http://test.com", session)
        node.delete()
        session.delete.assert_called_once_with("http://test.com", timeout=None)


class TestWebsocketClient(TestCase):
    """Tests for pylxd.client.WebsocketClient."""

    def test_handshake_ok(self):
        """A `message` attribute of an empty list is created."""
        ws_client = client._WebsocketClient("ws://an/fake/path")
        ws_client.handshake_ok()
        self.assertEqual([], ws_client.messages)

    def test_received_message(self):
        """A json dict is added to the messages attribute."""
        message = mock.Mock(data=json.dumps({"test": "data"}).encode("utf-8"))
        ws_client = client._WebsocketClient("ws://an/fake/path")
        ws_client.handshake_ok()
        ws_client.received_message(message)
        self.assertEqual({"test": "data"}, ws_client.messages[0])


class TestGetSessionForUrl(TestCase):
    """Tests for pylxd.client.get_session_for_url."""

    def test_session_unix_socket(self):
        """http+unix URL return a requests_unixsocket session."""
        session = client.get_session_for_url("http+unix://test.com")
        self.assertIsInstance(
            session.get_adapter("http+unix://"), requests.adapters.HTTPAdapter
        )

    def test_session_http(self):
        """HTTP nodes return the default requests session."""
        session = client.get_session_for_url("http://test.com")
        self.assertIsInstance(session, requests.Session)
        self.assertRaises(
            requests.exceptions.InvalidSchema, session.get_adapter, "http+unix://"
        )

    def test_session_cert(self):
        """If certs are given, they're set on the Session."""
        certs = (
            os.path.join(os.path.dirname(__file__), "lxd.crt"),
            os.path.join(os.path.dirname(__file__), "lxd.key"),
        )
        session = client.get_session_for_url("http://test.com", cert=certs)
        self.assertEqual(session.cert, certs)

    def test_session_verify(self):
        """If verify is given, it's set on the Session."""
        session = client.get_session_for_url("http://test.com", verify=True)
        self.assertIs(session.verify, True)

    def _merged_settings(self, session, url="https://lxd.test:8443/1.0"):
        """Return the settings requests resolves for a request on session."""
        return session.merge_environment_settings(url, {}, None, None, None)

    @mock.patch.dict(os.environ, {"REQUESTS_CA_BUNDLE": "/env/ca-bundle.crt"})
    def test_session_verify_false_beats_requests_ca_bundle(self):
        """verify=False is not overridden by REQUESTS_CA_BUNDLE."""
        session = client.get_session_for_url("https://lxd.test:8443", verify=False)
        self.assertIs(self._merged_settings(session)["verify"], False)

    @mock.patch.dict(os.environ, {"CURL_CA_BUNDLE": "/env/ca-bundle.crt"})
    def test_session_verify_path_beats_curl_ca_bundle(self):
        """A verify path is not overridden by CURL_CA_BUNDLE."""
        session = client.get_session_for_url(
            "https://lxd.test:8443", verify="/path/server.crt"
        )
        self.assertEqual(self._merged_settings(session)["verify"], "/path/server.crt")

    @mock.patch.dict(os.environ, {"REQUESTS_CA_BUNDLE": "/env/ca-bundle.crt"})
    def test_session_verify_true_uses_requests_ca_bundle(self):
        """verify=True still picks up the CA bundle from the environment."""
        session = client.get_session_for_url("https://lxd.test:8443", verify=True)
        self.assertEqual(self._merged_settings(session)["verify"], "/env/ca-bundle.crt")

    @mock.patch.dict(os.environ, {"REQUESTS_CA_BUNDLE": "/env/ca-bundle.crt"})
    def test_session_request_verify_beats_session_verify(self):
        """A verify passed for a single request still takes precedence."""
        session = client.get_session_for_url("https://lxd.test:8443", verify=False)
        settings = session.merge_environment_settings(
            "https://lxd.test:8443/1.0", {}, None, "/path/other.crt", None
        )
        self.assertEqual(settings["verify"], "/path/other.crt")

    @mock.patch.dict(
        os.environ,
        {
            "REQUESTS_CA_BUNDLE": "/env/ca-bundle.crt",
            "HTTPS_PROXY": "http://proxy.test:3128",
        },
    )
    def test_session_verify_false_keeps_env_proxies(self):
        """An explicit verify does not stop proxies coming from the environment."""
        session = client.get_session_for_url("https://lxd.test:8443", verify=False)
        settings = self._merged_settings(session)
        self.assertIs(settings["verify"], False)
        self.assertEqual(settings["proxies"]["https"], "http://proxy.test:3128")

    @mock.patch.dict(os.environ, {"REQUESTS_CA_BUNDLE": "/env/ca-bundle.crt"})
    def test_session_verify_false_sent_to_adapter(self):
        """The adapter is asked not to verify when verify=False."""
        session = client.get_session_for_url("https://lxd.test:8443", verify=False)
        response = requests.Response()
        response.status_code = 200
        adapter = mock.Mock(**{"send.return_value": response})
        session.mount("https://", adapter)
        session.get("https://lxd.test:8443/1.0")
        self.assertIs(adapter.send.call_args.kwargs["verify"], False)

    def _cert_fingerprint(self, cert_path):
        """Return the SHA-256 hex digest of a PEM certificate file."""
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes

        with open(cert_path, "rb") as fd:
            cert = x509.load_pem_x509_certificate(fd.read())
        return cert.fingerprint(hashes.SHA256()).hex()

    def _run_path_session_request(self, verify_override=None, conn=None):
        """Send a mocked request through a path-verified session's LXDSSLAdapter."""
        import io

        import urllib3

        cert_path = os.path.join(os.path.dirname(__file__), "lxd.crt")
        session = client.get_session_for_url("https://lxd.test:8443", verify=cert_path)
        adapter = session.get_adapter("https://lxd.test:8443/1.0")
        self.assertIsInstance(adapter, client.LXDSSLAdapter)

        if conn is None:
            conn = urllib3.HTTPSConnectionPool("lxd.test", 8443)
        conn.urlopen = mock.Mock(
            return_value=urllib3.HTTPResponse(
                body=io.BytesIO(b""), status=200, preload_content=False
            )
        )

        kwargs = {}
        if verify_override is not None:
            kwargs["verify"] = verify_override

        with mock.patch.object(
            adapter, "get_connection_with_tls_context", return_value=conn
        ):
            session.get("https://lxd.test:8443/1.0", **kwargs)
        return conn, cert_path

    def test_session_verify_path_pins_fingerprint(self):
        """A session initialized with a cert path pins its SHA-256 fingerprint."""
        conn, cert_path = self._run_path_session_request()
        self.assertEqual(conn.assert_fingerprint, self._cert_fingerprint(cert_path))
        self.assertEqual(conn.cert_reqs, "CERT_NONE")

    def test_session_verify_path_override_pathlike(self):
        """A request-level os.PathLike override pins that certificate's fingerprint."""
        import pathlib

        cert_path = os.path.join(os.path.dirname(__file__), "lxd.crt")
        conn, _ = self._run_path_session_request(
            verify_override=pathlib.Path(cert_path)
        )
        self.assertEqual(conn.assert_fingerprint, self._cert_fingerprint(cert_path))
        self.assertEqual(conn.cert_reqs, "CERT_NONE")

    def test_session_verify_path_override_true(self):
        """A request-level verify=True delegates to standard TLS verification."""
        import urllib3

        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE")
        }
        conn = urllib3.HTTPSConnectionPool("lxd.test", 8443)
        conn.assert_fingerprint = "stale-fingerprint"
        with mock.patch.dict(os.environ, env, clear=True):
            self._run_path_session_request(verify_override=True, conn=conn)
        self.assertIsNone(conn.assert_fingerprint)
        self.assertEqual(conn.cert_reqs, "CERT_REQUIRED")
        self.assertIsNotNone(conn.ca_certs)

    def test_session_verify_path_override_false(self):
        """A request-level verify=False disables verification without opening a fd."""
        import urllib3

        conn = urllib3.HTTPSConnectionPool("lxd.test", 8443)
        conn.assert_fingerprint = "stale-fingerprint"
        self._run_path_session_request(verify_override=False, conn=conn)
        self.assertIsNone(conn.assert_fingerprint)
        self.assertEqual(conn.cert_reqs, "CERT_NONE")
        self.assertIsNone(conn.ca_certs)


class TestWsExcludeOrigin:
    """Tests for pylxd.client._ws_exclude_origin."""

    @pytest.mark.parametrize(
        "input_kwargs,expected",
        [
            ({}, ["origin"]),
            ({"exclude_headers": ["upgrade"]}, ["upgrade", "origin"]),
            (
                {"exclude_headers": ["Origin"]},
                ["Origin"],
            ),  # already present, case-insensitive
            ({"exclude_headers": None}, ["origin"]),
        ],
    )
    def test_ws_exclude_origin(self, input_kwargs, expected):
        client._ws_exclude_origin(input_kwargs)
        assert input_kwargs["exclude_headers"] == expected


class TestSetDefaultContentType:
    """Tests for pylxd.client._set_default_content_type."""

    @pytest.mark.parametrize(
        "input_kwargs,expected",
        [
            ({}, {}),
            ({"data": None}, {"data": None}),
            ({"json": {"a": 1}}, {"json": {"a": 1}}),
            (
                {"data": b"raw"},
                {
                    "data": b"raw",
                    "headers": {"Content-Type": "application/octet-stream"},
                },
            ),
            (
                {"data": "raw", "headers": None},
                {
                    "data": "raw",
                    "headers": {"Content-Type": "application/octet-stream"},
                },
            ),
            (
                {"data": b"raw", "headers": {"X-LXD-mode": "0644"}},
                {
                    "data": b"raw",
                    "headers": {
                        "X-LXD-mode": "0644",
                        "Content-Type": "application/octet-stream",
                    },
                },
            ),
            (
                {"data": b"raw", "headers": {"content-type": "text/plain"}},
                {"data": b"raw", "headers": {"content-type": "text/plain"}},
            ),
            ({"data": {"a": "1"}}, {"data": {"a": "1"}}),
            (
                {"data": MappingProxyType({"a": "1"})},
                {"data": MappingProxyType({"a": "1"})},
            ),
            (
                {"data": b"raw", "files": {"f": b"x"}},
                {"data": b"raw", "files": {"f": b"x"}},
            ),
            (
                {"data": b"raw", "files": {}},
                {
                    "data": b"raw",
                    "files": {},
                    "headers": {"Content-Type": "application/octet-stream"},
                },
            ),
        ],
    )
    def test_set_default_content_type(self, input_kwargs, expected):
        client._set_default_content_type(input_kwargs)
        assert input_kwargs == expected

    def test_files_with_form_data_stay_multipart(self):
        """requests builds the multipart Content-Type when files are sent."""
        kwargs = {"data": MappingProxyType({"a": "1"}), "files": {"f": b"x"}}
        client._set_default_content_type(kwargs)
        assert "headers" not in kwargs
        request = requests.Request("POST", "http://lxd.test", **kwargs).prepare()
        assert request.headers["Content-Type"].startswith("multipart/form-data")

    def test_does_not_mutate_caller_headers(self):
        headers = {"X-LXD-mode": "0644"}
        kwargs = {"data": b"raw", "headers": headers}
        client._set_default_content_type(kwargs)
        assert headers == {"X-LXD-mode": "0644"}


class TestWsSslOptions:
    """Tests for pylxd.client._ws_ssl_options."""

    URL = "https://lxd.local:8443"
    CA_VERIFIED = {"cert_reqs": ssl.CERT_REQUIRED}

    @pytest.fixture(autouse=True)
    def no_ca_bundle_in_environment(self, monkeypatch):
        monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
        monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)

    def options(self, verify):
        session = client.get_session_for_url(self.URL, verify=verify)
        return client._ws_ssl_options(session, self.URL, None)

    def test_client_certificate_is_passed_through(self):
        session = client.get_session_for_url(self.URL, verify=False)
        options = client._ws_ssl_options(
            session, self.URL, ("client.crt", "client.key")
        )
        assert options == {"certfile": "client.crt", "keyfile": "client.key"}

    def test_verify_path_pins_the_server_certificate(self):
        """The pin is checked by pylxd: no cert_reqs is set."""
        assert self.options(CERT) == {"ca_certs": CERT}

    def test_verify_true_uses_the_ca_bundle_requests_uses(self):
        expected = {**self.CA_VERIFIED, "ca_certs": requests.certs.where()}
        assert self.options(True) == expected

    def test_ca_bundle_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/etc/ca.pem")
        expected = {**self.CA_VERIFIED, "ca_certs": "/etc/ca.pem"}
        assert self.options(True) == expected

    def test_ca_bundle_on_a_caller_supplied_session_is_not_a_pin(self):
        """Without LXDSSLAdapter, requests reads a path as a CA bundle."""
        session = requests.Session()
        session.verify = "/etc/ca.pem"
        expected = {**self.CA_VERIFIED, "ca_certs": "/etc/ca.pem"}
        assert client._ws_ssl_options(session, self.URL, None) == expected

    @pytest.mark.parametrize("verify", [False, None])
    def test_falsy_verify_opts_out(self, verify):
        """requests skips verification for None as well as for False."""
        assert self.options(verify) == {}


class TestLXDWebSocketBaseClient:
    """Tests for pylxd.client._LXDWebSocketBaseClient."""

    PINNED = {"ca_certs": CERT}
    with open(CERT) as fd:
        PEER = ssl.PEM_cert_to_DER_cert(fd.read())

    @staticmethod
    def connected(ssl_options, peer_cert, scheme="wss"):
        """Return a client that looks as if its TLS handshake just finished."""
        ws = client._LXDWebSocketBaseClient(
            f"{scheme}://127.0.0.1:8443", ssl_options=ssl_options
        )
        ws.sock.close()
        ws.sock = mock.Mock()
        ws.sock.getpeercert.return_value = peer_cert
        ws._is_secure = scheme == "wss"
        return ws

    def test_pinned_certificate_is_accepted(self):
        ws = self.connected(self.PINNED, self.PEER)
        ws._write(b"handshake")
        ws._write(b"frame")
        assert ws.sock.sendall.call_count == 2
        ws.sock.getpeercert.assert_called_once_with(binary_form=True)

    @pytest.mark.parametrize("peer_cert", [b"another certificate", None])
    def test_other_certificate_is_refused_before_anything_is_sent(self, peer_cert):
        ws = self.connected(self.PINNED, peer_cert)
        sock = ws.sock
        with pytest.raises(exceptions.ClientConnectionFailed):
            ws._write(b"GET /1.0/operations/x/websocket?secret=hunter2")
        sock.sendall.assert_not_called()
        sock.close.assert_called_once_with()
        assert ws.sock is None

    @pytest.mark.parametrize(
        "ssl_options",
        [
            {},  # verification declined
            {"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": CERT},  # done in TLS handshake
        ],
    )
    def test_no_fingerprint_check_without_a_pin(self, ssl_options):
        ws = self.connected(ssl_options, b"another certificate")
        ws._write(b"handshake")
        ws.sock.getpeercert.assert_not_called()
        ws.sock.sendall.assert_called_once_with(b"handshake")

    def test_plain_ws_has_no_peer_certificate_to_check(self):
        ws = self.connected(self.PINNED, None, scheme="ws")
        ws._write(b"handshake")
        ws.sock.getpeercert.assert_not_called()
        ws.sock.sendall.assert_called_once_with(b"handshake")

    def test_origin_header_is_excluded_from_handshake(self):
        ws = self.connected(None, None)
        assert ws.exclude_headers == ["origin"]
        assert all(h.lower() != "origin" for h, _ in ws.handshake_headers)

    def test_connect_wss_verifies_with_ca_bundle_and_skips_ws4py_tls(self):
        ws = self.connected(
            {
                "certfile": "client.crt",
                "keyfile": "client.key",
                "cert_reqs": ssl.CERT_REQUIRED,
                "ca_certs": "/etc/ca.pem",
            },
            None,
        )
        raw_sock = ws.sock
        seen_schemes = []
        with (
            mock.patch("pylxd.client.ssl.create_default_context") as create_ctx,
            mock.patch.object(
                WebSocketBaseClient,
                "connect",
                autospec=True,
                side_effect=lambda self_ws: seen_schemes.append(self_ws.scheme),
            ),
        ):
            ws.connect()

        create_ctx.assert_called_once_with(cafile="/etc/ca.pem")
        ctx = create_ctx.return_value
        ctx.load_cert_chain.assert_called_once_with("client.crt", "client.key")
        ctx.wrap_socket.assert_called_once_with(raw_sock, server_hostname="127.0.0.1")
        assert seen_schemes == ["ws"]
        assert ws.scheme == "wss"
        assert ws._is_secure is True

    def test_connect_wss_without_cert_reqs_uses_unverified_context(self):
        ws = self.connected(self.PINNED, self.PEER)
        with (
            mock.patch("pylxd.client.ssl.SSLContext") as MockCtx,
            mock.patch.object(WebSocketBaseClient, "connect"),
        ):
            ws.connect()

        MockCtx.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
        ctx = MockCtx.return_value
        assert ctx.check_hostname is False
        assert ctx.verify_mode == ssl.CERT_NONE
        ctx.load_cert_chain.assert_not_called()
        assert ws.scheme == "wss"

    def test_connect_plain_ws_delegates_to_super(self):
        ws = self.connected(None, None, scheme="ws")
        with mock.patch.object(WebSocketBaseClient, "connect") as super_connect:
            ws.connect()
        super_connect.assert_called_once_with()

    def test_connect_wss_accepts_a_ca_directory(self, tmp_path):
        ws = self.connected(
            {"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": str(tmp_path)}, None
        )
        with (
            mock.patch("pylxd.client.ssl.create_default_context") as create_ctx,
            mock.patch.object(WebSocketBaseClient, "connect"),
        ):
            ws.connect()

        create_ctx.assert_called_once_with(capath=str(tmp_path))

    def test_connect_wss_closes_the_socket_when_it_fails(self):
        ws = self.connected(self.PINNED, self.PEER)
        with (
            mock.patch("pylxd.client.ssl.SSLContext") as MockCtx,
            mock.patch.object(
                WebSocketBaseClient, "connect", side_effect=OSError("refused")
            ),
        ):
            with pytest.raises(OSError):
                ws.connect()

        MockCtx.return_value.wrap_socket.return_value.close.assert_called_once_with()
        assert ws.sock is None
        assert ws.scheme == "wss"


def self_signed(directory, name, san):
    """Write a self-signed certificate valid for `san`.

    :returns: The paths of the certificate and of its key.
    """
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName([san]), critical=False)
        .sign(key, hashes.SHA256())
    )
    certfile, keyfile = directory / f"{name}.crt", directory / f"{name}.key"
    certfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    keyfile.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return str(certfile), str(keyfile)


@contextlib.contextmanager
def tls_server(certfile, keyfile):
    """Serve one websocket handshake over TLS on the loopback.

    Yields the port and the list of what the client sent after the TLS
    handshake, which stays empty if the client refused the certificate.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile, keyfile)
    received = []

    def serve():
        try:
            conn, _ = listener.accept()
            with context.wrap_socket(conn, server_side=True) as tls:
                request = tls.recv(4096)
                received.append(request)
                key = re.search(rb"Sec-WebSocket-Key: (\S+)", request)
                if key:
                    accept = base64.b64encode(
                        hashlib.sha1(
                            key.group(1) + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
                        ).digest()
                    )
                    tls.sendall(
                        b"HTTP/1.1 101 Switching Protocols\r\n"
                        b"Upgrade: websocket\r\nConnection: Upgrade\r\n"
                        b"Sec-WebSocket-Accept: " + accept + b"\r\n\r\n"
                    )
        except OSError:
            pass  # The client refused the certificate or hung up.

    with socket.create_server(("127.0.0.1", 0)) as listener:
        listener.settimeout(5)
        thread = threading.Thread(target=serve)
        thread.start()
        try:
            yield listener.getsockname()[1], received
        finally:
            thread.join()


class TestWebsocketTLS:
    """The websocket clients against a real TLS server on the loopback."""

    LOOPBACK = x509.IPAddress(ipaddress.ip_address("127.0.0.1"))
    SECRET = b"secret=hunter2"

    @classmethod
    def connect(cls, ws):
        """Run the handshake that would hand the operation secret to the peer."""
        ws.resource = "/1.0/operations/x/websocket?" + cls.SECRET.decode()
        ws.sock.settimeout(5)
        try:
            ws.connect()
        finally:
            if ws.sock:
                ws.sock.close()

    @classmethod
    def connect_to(cls, port, ssl_options):
        cls.connect(
            client._LXDWebSocketBaseClient(
                f"wss://127.0.0.1:{port}", ssl_options=ssl_options
            )
        )

    def test_pinned_certificate_connects_whatever_the_hostname(self):
        """lxd.crt names no host, as a pinned LXD certificate need not."""
        with tls_server(CERT, KEY) as (port, received):
            self.connect_to(port, {"ca_certs": CERT})
        assert self.SECRET in received[0]

    def test_pinned_certificate_refuses_another_before_sending(self, tmp_path):
        impostor = self_signed(tmp_path, "impostor", self.LOOPBACK)
        with tls_server(*impostor) as (port, received):
            with pytest.raises(exceptions.ClientConnectionFailed):
                self.connect_to(port, {"ca_certs": CERT})
        assert not b"".join(received)

    def test_pinned_certificate_is_checked_on_a_callers_class(self, tmp_path):
        """Client.events() protects a plain ws4py client class."""
        impostor = self_signed(tmp_path, "impostor", self.LOOPBACK)
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {"metadata": {"auth": "trusted"}}
        with tls_server(*impostor) as (port, received):
            with mock.patch("pylxd.client._APINode.get", return_value=response):
                an_client = client.Client(f"https://127.0.0.1:{port}", verify=CERT)
            ws = an_client.events(websocket_client=WebSocketBaseClient)
            with pytest.raises(exceptions.ClientConnectionFailed):
                self.connect(ws)
        assert not b"".join(received)

    def test_ca_verified_certificate_connects(self, tmp_path):
        cert, key = self_signed(tmp_path, "server", self.LOOPBACK)
        with tls_server(cert, key) as (port, received):
            self.connect_to(port, {"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": cert})
        assert self.SECRET in received[0]

    def test_ca_verification_refuses_an_untrusted_certificate(self, tmp_path):
        trusted, _ = self_signed(tmp_path, "trusted", self.LOOPBACK)
        impostor = self_signed(tmp_path, "impostor", self.LOOPBACK)
        with tls_server(*impostor) as (port, received):
            with pytest.raises(ssl.SSLCertVerificationError):
                self.connect_to(
                    port, {"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": trusted}
                )
        assert not b"".join(received)

    def test_ca_verification_refuses_another_hostname(self, tmp_path):
        cert, key = self_signed(tmp_path, "elsewhere", x509.DNSName("lxd-host"))
        with tls_server(cert, key) as (port, received):
            with pytest.raises(ssl.SSLCertVerificationError):
                self.connect_to(
                    port, {"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": cert}
                )
        assert not b"".join(received)


class TestIsAToken(TestCase):
    """Tests for pylxd.client._is_a_token."""

    def _make_token(self):
        token = json.dumps(
            {
                "client_name": "test",
                "fingerprint": "abcd",
                "addresses": ["192.0.2.1:8443"],
                "secret": "I-am-a-secret",
                "expires_at": "0001-01-01T00:00:00Z",
                "type": "",
            }
        )
        return base64.b64encode(token.encode("utf-8"))

    def test_plain_password_is_not_a_token(self):
        """A plain password string is not a token."""
        self.assertFalse(client._is_a_token("password"))

    def test_b64_non_json_is_not_a_token(self):
        """Base64-encoded non-JSON data is not a token."""
        self.assertFalse(client._is_a_token(base64.b64encode(b"password")))

    def test_valid_token_bytes_is_a_token(self):
        """A valid base64-encoded token (bytes) is recognised as a token."""
        self.assertTrue(client._is_a_token(self._make_token()))

    def test_valid_token_str_is_a_token(self):
        """A valid base64-encoded token (str) is recognised as a token."""
        self.assertTrue(client._is_a_token(self._make_token().decode("utf-8")))

    def test_token_with_surrounding_whitespace_is_a_token(self):
        """A token with surrounding whitespace (copy-paste artefact) is still detected."""
        token_str = self._make_token().decode("utf-8")
        self.assertTrue(client._is_a_token(f"\n  {token_str}  \n"))

    def test_token_bytes_with_surrounding_whitespace_is_a_token(self):
        """A token bytes value with surrounding whitespace is still detected."""
        token_bytes = b"\n  " + self._make_token() + b"  \n"
        self.assertTrue(client._is_a_token(token_bytes))

    def test_invalid_base64_characters_returns_false(self):
        """Data containing non-base64 characters (caught by validate=True) returns False."""
        # These characters are never valid in strict base64 but b64decode without
        # validate=True would silently ignore them.
        self.assertFalse(client._is_a_token("not!valid@base64#"))

    def test_json_string_containing_secret_is_not_a_token(self):
        """A base64-encoded JSON string containing 'secret' is not a token."""
        payload = base64.b64encode(json.dumps("my-secret-value").encode("utf-8"))
        self.assertFalse(client._is_a_token(payload))

    def test_json_list_containing_secret_is_not_a_token(self):
        """A base64-encoded JSON list containing 'secret' is not a token."""
        payload = base64.b64encode(json.dumps(["secret"]).encode("utf-8"))
        self.assertFalse(client._is_a_token(payload))
