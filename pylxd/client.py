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

import requests
import requests_unixsocket
from six.moves.urllib import parse
from ws4py.client import WebSocketBaseClient

from pylxd import exceptions, managers

requests_unixsocket.monkeypatch()


class _APINode(object):
    """An api node object."""

    def __init__(self, api_endpoint, cert=None, verify=True):
        self._api_endpoint = api_endpoint

        if self._api_endpoint.startswith('http+unix://'):
            self.session = requests_unixsocket.Session()
        else:
            self.session = requests.Session()
            self.session.cert = cert
            self.session.verify = verify

    def __getattr__(self, name):
        return self.__class__(
            '{}/{}'.format(self._api_endpoint, name),
            cert=self.session.cert, verify=self.session.verify)

    def __getitem__(self, item):
        return self.__class__(
            '{}/{}'.format(self._api_endpoint, item),
            cert=self.session.cert, verify=self.session.verify)

    def _assert_response(self, response, allowed_status_codes=(200,)):
        """Assert properties of the response.

        LXD's API clearly defines specific responses. If the API
        response is something unexpected (i.e. an error), then
        we need to raise an exception and have the call points
        handle the errors or just let the issue be raised to the
        user.
        """
        if response.status_code not in allowed_status_codes:
            raise exceptions.LXDAPIException(response)

        try:
            data = response.json()
        except ValueError:
            # Not a JSON response
            return

        if response.status_code == 200:
            # Synchronous request
            try:
                if data['type'] != 'sync':
                    raise exceptions.LXDAPIException(response)
            except KeyError:
                # Missing 'type' in response
                raise exceptions.LXDAPIException(response)

        if response.status_code == 202:
            try:
                if data['type'] != 'async':
                    raise exceptions.LXDAPIException(response)
            except KeyError:
                # Missing 'type' in response
                raise exceptions.LXDAPIException(response)

    def get(self, *args, **kwargs):
        """Perform an HTTP GET."""
        response = self.session.get(self._api_endpoint, *args, **kwargs)
        self._assert_response(response)
        return response

    def post(self, *args, **kwargs):
        """Perform an HTTP POST."""
        response = self.session.post(self._api_endpoint, *args, **kwargs)
        self._assert_response(response, allowed_status_codes=(200, 202))
        return response

    def put(self, *args, **kwargs):
        """Perform an HTTP PUT."""
        response = self.session.put(self._api_endpoint, *args, **kwargs)
        self._assert_response(response, allowed_status_codes=(200, 202))
        return response

    def delete(self, *args, **kwargs):
        """Perform an HTTP delete."""
        response = self.session.delete(self._api_endpoint, *args, **kwargs)
        self._assert_response(response, allowed_status_codes=(200, 202))
        return response


class _WebsocketClient(WebSocketBaseClient):
    """A basic websocket client for the LXD API.

    This client is intentionally barebones, and serves
    as a simple default. It simply connects and saves
    all json messages to a messages attribute, which can
    then be read are parsed.
    """
    def handshake_ok(self):
        self.messages = []

    def received_message(self, message):
        json_message = json.loads(message.data.decode('utf-8'))
        self.messages.append(json_message)


class Client(object):
    """
    Client class for LXD REST API.

    This client wraps all the functionality required to interact with
    LXD, and is meant to be the sole entry point.

    .. attribute:: containers

        Instance of :class:`Client.Containers
        <pylxd.client.Client.Containers>`:

    .. attribute:: images

        Instance of :class:`Client.Images <pylxd.client.Client.Images>`.

    .. attribute:: operations

        Instance of :class:`Client.Operations
        <pylxd.client.Client.Operations>`.

    .. attribute:: profiles

        Instance of :class:`Client.Profiles <pylxd.client.Client.Profiles>`.

    .. attribute:: api

        This attribute provides tree traversal syntax to LXD's REST API for
        lower-level interaction.

        Use the name of the url part as attribute or item of an api object to
        create another api object appended with the new url part name, ie:

            >>> api = Client().api
            # /
            >>> response = api.get()
            # Check status code and response
            >>> print response.status_code, response.json()
            # /containers/test/
            >>> print api.containers['test'].get().json()
    """

    def __init__(self, endpoint=None, version='1.0', cert=None, verify=True):
        if endpoint is not None:
            self.api = _APINode(endpoint, cert=cert, verify=verify)
        else:
            if 'LXD_DIR' in os.environ:
                path = os.path.join(
                    os.environ.get('LXD_DIR'), 'unix.socket')
            else:
                path = '/var/lib/lxd/unix.socket'
            self.api = _APINode('http+unix://{}'.format(
                parse.quote(path, safe='')))
        self.api = self.api[version]

        # Verify the connection is valid.
        try:
            response = self.api.get()
            if response.status_code != 200:
                raise exceptions.ClientConnectionFailed()
            auth = response.json()['metadata']['auth']
            if auth != "trusted":
                raise exceptions.ClientAuthenticationFailed()

            self.host_info = response.json()['metadata']
        except (requests.exceptions.ConnectionError,
                requests.exceptions.InvalidURL):
            raise exceptions.ClientConnectionFailed()

        self.containers = managers.ContainerManager(self)
        self.images = managers.ImageManager(self)
        self.operations = managers.OperationManager(self)
        self.profiles = managers.ProfileManager(self)

    @property
    def websocket_url(self):
        parsed = parse.urlparse(self.api._api_endpoint)
        if parsed.scheme in ('http', 'https'):
            host = parsed.netloc
            if parsed.scheme == 'http':
                scheme = 'ws'
            else:
                scheme = 'wss'
        else:
            scheme = 'ws+unix'
            host = parse.unquote(parsed.netloc)
        url = parse.urlunparse((scheme, host, '', '', '', ''))
        return url

    def events(self, websocket_client=None):
        """Get a websocket client for getting events.

        /events is a websocket url, and so must be handled differently than
        most other LXD API endpoints. This method returns
        a client that can be interacted with like any
        regular python socket.

        An optional `websocket_client` parameter can be
        specified for implementation-specific handling
        of events as they occur.
        """
        if websocket_client is None:
            websocket_client = _WebsocketClient

        client = websocket_client(self.websocket_url)
        parsed = parse.urlparse(self.api.events._api_endpoint)
        client.resource = parsed.path

        return client
