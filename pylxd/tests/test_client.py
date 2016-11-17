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
import os.path
import unittest

import mock
import requests
import requests_unixsocket

from pylxd import client, exceptions
from pylxd.tests.testing import requires_ws4py


class TestClient(unittest.TestCase):
    """Tests for pylxd.client.Client."""

    def setUp(self):
        self.get_patcher = mock.patch('pylxd.client._APINode.get')
        self.get = self.get_patcher.start()

        self.post_patcher = mock.patch('pylxd.client._APINode.post')
        self.post = self.post_patcher.start()

        response = mock.MagicMock(status_code=200)
        response.json.return_value = {'metadata': {
            'auth': 'trusted',
            'environment': {'storage': 'zfs'},
        }}
        self.get.return_value = response

        post_response = mock.MagicMock(status_code=200)
        self.post.return_value = post_response

    def tearDown(self):
        self.get_patcher.stop()
        self.post_patcher.stop()

    def test_create(self):
        """Client creation sets default API endpoint."""
        expected = 'http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket/1.0'

        an_client = client.Client()

        self.assertEqual(expected, an_client.api._api_endpoint)

    def test_create_LXD_DIR(self):
        """When LXD_DIR is set, use it in the client."""
        os.environ['LXD_DIR'] = '/lxd'
        expected = 'http+unix://%2Flxd%2Funix.socket/1.0'

        an_client = client.Client()

        self.assertEqual(expected, an_client.api._api_endpoint)

    def test_create_endpoint(self):
        """Explicitly set the client endpoint."""
        endpoint = 'http://lxd'
        expected = 'http://lxd/1.0'

        an_client = client.Client(endpoint=endpoint)

        self.assertEqual(expected, an_client.api._api_endpoint)

    def test_create_endpoint_unixsocket(self):
        """Test with unix socket endpoint."""
        endpoint = '/tmp/unix.socket'
        expected = 'http+unix://%2Ftmp%2Funix.socket/1.0'

        real_isfile = os.path.isfile
        os.path.isfile = lambda x: True
        an_client = client.Client(endpoint)
        os.path.isfile = real_isfile

        self.assertEqual(expected, an_client.api._api_endpoint)

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
        response.json.return_value = {'metadata': {'auth': 'untrusted'}}
        self.get.return_value = response

        an_client = client.Client()

        self.assertFalse(an_client.trusted)

    def test_connection_trusted(self):
        """Client.trusted is True when certs are untrusted."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {'metadata': {'auth': 'trusted'}}
        self.get.return_value = response

        an_client = client.Client()

        self.assertTrue(an_client.trusted)

    def test_authenticate(self):
        """A client is authenticated."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {'metadata': {'auth': 'untrusted'}}
        self.get.return_value = response

        certs = (
            os.path.join(os.path.dirname(__file__), 'lxd.crt'),
            os.path.join(os.path.dirname(__file__), 'lxd.key'))
        an_client = client.Client('https://lxd', cert=certs)

        get_count = []

        def _get(*args, **kwargs):
            if len(get_count) == 0:
                get_count.append(None)
                return {'metadata': {
                    'type': 'client',
                    'fingerprint': 'eaf55b72fc23aa516d709271df9b0116064bf8cfa009cf34c67c33ad32c2320c',  # NOQA
                }}
            else:
                return {'metadata': {'auth': 'trusted'}}
        response = mock.MagicMock(status_code=200)
        response.json.side_effect = _get
        self.get.return_value = response

        an_client.authenticate('test-password')

        self.assertTrue(an_client.trusted)

    def test_authenticate_already_authenticated(self):
        """If the client is already authenticated, nothing happens."""
        an_client = client.Client()

        an_client.authenticate('test-password')

        self.assertTrue(an_client.trusted)

    def test_host_info(self):
        """Perform a host query."""
        an_client = client.Client()
        self.assertEqual('zfs', an_client.host_info['environment']['storage'])

    @requires_ws4py
    def test_events(self):
        """The default websocket client is returned."""
        an_client = client.Client()

        ws_client = an_client.events()

        self.assertEqual('/1.0/events', ws_client.resource)

    def test_events_no_ws4py(self):
        """No ws4py will result in a ValueError."""
        from pylxd import client
        old_installed = client._ws4py_installed
        client._ws4py_installed = False

        def cleanup():
            client._ws4py_installed = old_installed
        self.addCleanup(cleanup)

        an_client = client.Client()

        self.assertRaises(ValueError, an_client.events)
        client._ws4py_installed

    @requires_ws4py
    def test_events_unix_socket(self):
        """A unix socket compatible websocket client is returned."""
        websocket_client = mock.Mock(resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        an_client = client.Client()

        an_client.events(websocket_client=WebsocketClient)

        WebsocketClient.assert_called_once_with('ws+unix:///lxd/unix.socket')

    @requires_ws4py
    def test_events_htt(self):
        """An http compatible websocket client is returned."""
        websocket_client = mock.Mock(resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        an_client = client.Client('http://lxd.local')

        an_client.events(websocket_client=WebsocketClient)

        WebsocketClient.assert_called_once_with('ws://lxd.local')

    @requires_ws4py
    def test_events_https(self):
        """An https compatible websocket client is returned."""
        websocket_client = mock.Mock(resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        an_client = client.Client('https://lxd.local')

        an_client.events(websocket_client=WebsocketClient)

        WebsocketClient.assert_called_once_with('wss://lxd.local')


class TestAPINode(unittest.TestCase):
    """Tests for pylxd.client._APINode."""

    def test_getattr(self):
        """API Nodes can use object notation for nesting."""
        node = client._APINode('http://test.com')

        new_node = node.test

        self.assertEqual(
            'http://test.com/test', new_node._api_endpoint)

    def test_getitem(self):
        """API Nodes can use dict notation for nesting."""
        node = client._APINode('http://test.com')

        new_node = node['test']

        self.assertEqual(
            'http://test.com/test', new_node._api_endpoint)

    def test_session_http(self):
        """HTTP nodes return the default requests session."""
        node = client._APINode('http://test.com')

        self.assertIsInstance(node.session, requests.Session)

    def test_session_unix_socket(self):
        """HTTP nodes return a requests_unixsocket session."""
        node = client._APINode('http+unix://test.com')

        self.assertIsInstance(node.session, requests_unixsocket.Session)

    @mock.patch('pylxd.client.requests.Session')
    def test_get(self, Session):
        """Perform a session get."""
        response = mock.Mock(**{
            'status_code': 200,
            'json.return_value': {'type': 'sync'},
        })
        session = mock.Mock(**{'get.return_value': response})
        Session.return_value = session

        node = client._APINode('http://test.com')

        node.get()

        session.get.assert_called_once_with('http://test.com')

    @mock.patch('pylxd.client.requests.Session')
    def test_post(self, Session):
        """Perform a session post."""
        response = mock.Mock(**{
            'status_code': 200,
            'json.return_value': {'type': 'sync'},
        })
        session = mock.Mock(**{'post.return_value': response})
        Session.return_value = session

        node = client._APINode('http://test.com')

        node.post()

        session.post.assert_called_once_with('http://test.com')

    @mock.patch('pylxd.client.requests.Session')
    def test_post_200_not_sync(self, Session):
        """A status code of 200 with async request raises an exception."""
        response = mock.Mock(**{
            'status_code': 200,
            'json.return_value': {'type': 'async'},
        })
        session = mock.Mock(**{'post.return_value': response})
        Session.return_value = session

        node = client._APINode('http://test.com')

        self.assertRaises(
            exceptions.LXDAPIException,
            node.post)

    @mock.patch('pylxd.client.requests.Session')
    def test_post_missing_type_200(self, Session):
        """A missing response type raises an exception."""
        response = mock.Mock(**{
            'status_code': 200,
            'json.return_value': {},
        })
        session = mock.Mock(**{'post.return_value': response})
        Session.return_value = session

        node = client._APINode('http://test.com')

        self.assertRaises(
            exceptions.LXDAPIException,
            node.post)

    @mock.patch('pylxd.client.requests.Session')
    def test_put(self, Session):
        """Perform a session put."""
        response = mock.Mock(**{
            'status_code': 200,
            'json.return_value': {'type': 'sync'},
        })
        session = mock.Mock(**{'put.return_value': response})
        Session.return_value = session

        node = client._APINode('http://test.com')

        node.put()

        session.put.assert_called_once_with('http://test.com')

    @mock.patch('pylxd.client.requests.Session')
    def test_delete(self, Session):
        """Perform a session delete."""
        response = mock.Mock(**{
            'status_code': 200,
            'json.return_value': {'type': 'sync'},
        })
        session = mock.Mock(**{'delete.return_value': response})
        Session.return_value = session

        node = client._APINode('http://test.com')

        node.delete()

        session.delete.assert_called_once_with('http://test.com')


class TestWebsocketClient(unittest.TestCase):
    """Tests for pylxd.client.WebsocketClient."""

    @requires_ws4py
    def test_handshake_ok(self):
        """A `message` attribute of an empty list is created."""
        ws_client = client._WebsocketClient('ws://an/fake/path')

        ws_client.handshake_ok()

        self.assertEqual([], ws_client.messages)

    @requires_ws4py
    def test_received_message(self):
        """A json dict is added to the messages attribute."""
        message = mock.Mock(data=json.dumps({'test': 'data'}).encode('utf-8'))
        ws_client = client._WebsocketClient('ws://an/fake/path')
        ws_client.handshake_ok()

        ws_client.received_message(message)

        self.assertEqual({'test': 'data'}, ws_client.messages[0])
