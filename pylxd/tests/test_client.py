import os
import unittest

import mock
import requests
import requests_unixsocket

from pylxd import client


class TestClient(unittest.TestCase):
    """Tests for pylxd.client.Client."""

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

        self.assertEqual(requests, node.session)

    def test_session_unix_socket(self):
        """HTTP nodes return a requests_unixsocket session."""
        node = client._APINode('http+unix://test.com')

        self.assertIsInstance(node.session, requests_unixsocket.Session)

    @mock.patch('pylxd.client.requests.get')
    def test_get(self, get):
        """Perform a session get."""
        node = client._APINode('http://test.com')

        node.get()

        get.assert_called_once_with('http://test.com')

    @mock.patch('pylxd.client.requests.post')
    def test_post(self, post):
        """Perform a session post."""
        node = client._APINode('http://test.com')

        node.post()

        post.assert_called_once_with('http://test.com')

    @mock.patch('pylxd.client.requests.put')
    def test_put(self, put):
        """Perform a session put."""
        node = client._APINode('http://test.com')

        node.put()

        put.assert_called_once_with('http://test.com')

    @mock.patch('pylxd.client.requests.delete')
    def test_delete(self, delete):
        """Perform a session delete."""
        node = client._APINode('http://test.com')

        node.delete()

        delete.assert_called_once_with('http://test.com')
