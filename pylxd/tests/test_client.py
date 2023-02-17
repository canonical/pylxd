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
import json
import os
from unittest import TestCase, mock
from urllib import parse

import pytest
import requests
import requests_unixsocket

from pylxd import client, exceptions


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

    def test_create_LXD_DIR(self):
        """When LXD_DIR is set, use it in the client."""
        os.environ["LXD_DIR"] = "/lxd"
        expected = "http+unix://%2Flxd%2Funix.socket/1.0"

        an_client = client.Client()

        self.assertEqual(expected, an_client.api._api_endpoint)

    def test_create_endpoint(self):
        """Explicitly set the client endpoint."""
        endpoint = "http://lxd"
        expected = "http://lxd/1.0"

        an_client = client.Client(endpoint=endpoint)

        self.assertEqual(expected, an_client.api._api_endpoint)

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
        response = mock.MagicMock(status_code=404)
        self.get.return_value = response

        self.assertRaises(exceptions.ClientConnectionFailed, client.Client)

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
            {"metadata": {"auth": "untrusted"}},
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

    def test_events_unix_socket(self):
        """A unix socket compatible websocket client is returned."""
        websocket_client = mock.Mock(resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        os.environ["LXD_DIR"] = "/lxd"
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

    def test_events_https(self):
        """An https compatible websocket client is returned."""
        websocket_client = mock.Mock(resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        an_client = client.Client("https://lxd.local", cert=client.DEFAULT_CERTS)

        an_client.events(websocket_client=WebsocketClient)
        ssl_options = {
            "certfile": client.DEFAULT_CERTS.cert,
            "keyfile": client.DEFAULT_CERTS.key,
        }
        WebsocketClient.assert_called_once_with(
            "wss://lxd.local", ssl_options=ssl_options
        )

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

    def test_getitem(self):
        """API Nodes can use dict notation for nesting."""
        node = client._APINode("http://test.com", mock.sentinel.session)
        new_node = node["test"]
        self.assertEqual("http://test.com/test", new_node._api_endpoint)

    def test_getitem_leave_underscores_alone(self):
        """Bug 295 erronously changed underscores to '-' -- let's make sure
        it doens't happend again
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
        """session should be shared across path traversl"""
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
        self.assertIsInstance(session, requests_unixsocket.Session)

    def test_session_http(self):
        """HTTP nodes return the default requests session."""
        session = client.get_session_for_url("http://test.com")
        self.assertIsInstance(session, requests.Session)
        self.assertNotIsInstance(session, requests_unixsocket.Session)

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
