import json
import os
import unittest

import mock
import requests
import requests_unixsocket

from pylxd import client, exceptions


class TestClient(unittest.TestCase):
    """Tests for pylxd.client.Client."""

    def setUp(self):
        self.patcher = mock.patch('pylxd.client._APINode.get')
        self.get = self.patcher.start()

        response = mock.MagicMock(status_code=200)
        response.json.return_value = {'metadata': {
            'auth': 'trusted',
            'environment': {'storage': 'zfs'},
        }}
        self.get.return_value = response

    def tearDown(self):
        self.patcher.stop()

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

    def test_authentication_failed(self):
        """If the authentication fails, an exception is raised."""
        response = mock.MagicMock(status_code=200)
        response.json.return_value = {'metadata': {'auth': 'untrusted'}}
        self.get.return_value = response

        self.assertRaises(exceptions.ClientAuthenticationFailed, client.Client)

    def test_host_info(self):
        """Perform a host query """
        an_client = client.Client()
        self.assertEqual('zfs', an_client.host_info['environment']['storage'])

    def test_events(self):
        """The default websocket client is returned."""
        an_client = client.Client()

        ws_client = an_client.events()

        self.assertEqual('/1.0/events', ws_client.resource)

    def test_events_unix_socket(self):
        """A unix socket compatible websocket client is returned."""
        websocket_client = mock.Mock(resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        an_client = client.Client()

        an_client.events(websocket_client=WebsocketClient)

        WebsocketClient.assert_called_once_with('ws+unix:///lxd/unix.socket')

    def test_events_htt(self):
        """An http compatible websocket client is returned."""
        websocket_client = mock.Mock(resource=None)
        WebsocketClient = mock.Mock()
        WebsocketClient.return_value = websocket_client
        an_client = client.Client('http://lxd.local')

        an_client.events(websocket_client=WebsocketClient)

        WebsocketClient.assert_called_once_with('ws://lxd.local')

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
    def test_post_202_sync(self, Session):
        """A status code of 202 with sync request raises an exception."""
        response = mock.Mock(**{
            'status_code': 202,
            'json.return_value': {'type': 'sync'},
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
    def test_post_missing_type_202(self, Session):
        """A missing response type raises an exception."""
        response = mock.Mock(**{
            'status_code': 202,
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

    def test_handshake_ok(self):
        """A `message` attribute of an empty list is created."""
        ws_client = client._WebsocketClient('ws://an/fake/path')

        ws_client.handshake_ok()

        self.assertEqual([], ws_client.messages)

    def test_received_message(self):
        """A json dict is added to the messages attribute."""
        message = mock.Mock(data=json.dumps({'test': 'data'}).encode('utf-8'))
        ws_client = client._WebsocketClient('ws://an/fake/path')
        ws_client.handshake_ok()

        ws_client.received_message(message)

        self.assertEqual({'test': 'data'}, ws_client.messages[0])
