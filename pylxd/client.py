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

import requests
import requests_unixsocket
from six.moves.urllib import parse
try:
    from ws4py.client import WebSocketBaseClient
    _ws4py_installed = True
except ImportError:  # pragma: no cover
    WebSocketBaseClient = object
    _ws4py_installed = False

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

    def _assert_response(
            self, response, allowed_status_codes=(200,), stream=False):
        """Assert properties of the response.

        LXD's API clearly defines specific responses. If the API
        response is something unexpected (i.e. an error), then
        we need to raise an exception and have the call points
        handle the errors or just let the issue be raised to the
        user.
        """
        if response.status_code not in allowed_status_codes:
            if response.status_code == 404:
                raise exceptions.NotFound(response)
            raise exceptions.LXDAPIException(response)

        # In the case of streaming, we can't validate the json the way we
        # would with normal HTTP responses, so just ignore that entirely.
        if stream:
            return

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

    @property
    def scheme(self):
        return parse.urlparse(self.api._api_endpoint).scheme

    @property
    def netloc(self):
        return parse.urlparse(self.api._api_endpoint).netloc

    def get(self, *args, **kwargs):
        """Perform an HTTP GET."""
        response = self.session.get(
            self._api_endpoint, *args, **kwargs)
        self._assert_response(response, stream=kwargs.get('stream', False))
        return response

    def post(self, *args, **kwargs):
        """Perform an HTTP POST."""
        response = self.session.post(self._api_endpoint, *args, **kwargs)
        # Prior to LXD 2.0.3, successful synchronous requests returned 200,
        # rather than 201.
        self._assert_response(response, allowed_status_codes=(200, 201, 202))
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
    """Client class for LXD REST API.

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

    DEFAULT_CERTS = (
        os.path.expanduser('~/.config/lxc/client.crt'),
        os.path.expanduser('~/.config/lxc/client.key'))

    def __init__(self, endpoint=None, version='1.0', cert=None, verify=True):
        self.cert = cert
        if endpoint is not None:
            if endpoint.startswith('/') and os.path.isfile(endpoint):
                self.api = _APINode('http+unix://{}'.format(
                    parse.quote(endpoint, safe='')))
            else:
                # Extra trailing slashes cause LXD to 301
                endpoint = endpoint.rstrip('/')
                if cert is None and (
                        os.path.exists(self.DEFAULT_CERTS[0]) and
                        os.path.exists(self.DEFAULT_CERTS[1])):
                    cert = self.DEFAULT_CERTS
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
            self.host_info = response.json()['metadata']

        except (requests.exceptions.ConnectionError,
                requests.exceptions.InvalidURL):
            raise exceptions.ClientConnectionFailed()

        self.certificates = managers.CertificateManager(self)
        self.containers = managers.ContainerManager(self)
        self.images = managers.ImageManager(self)
        self.networks = managers.NetworkManager(self)
        self.operations = managers.OperationManager(self)
        self.profiles = managers.ProfileManager(self)

    @property
    def trusted(self):
        return self.host_info['auth'] == 'trusted'

    def authenticate(self, password):
        if self.trusted:
            return
        cert = open(self.api.session.cert[0]).read().encode('utf-8')
        self.certificates.create(password, cert)

        # Refresh the host info
        response = self.api.get()
        self.host_info = response.json()['metadata']

    @property
    def websocket_url(self):
        if self.api.scheme in ('http', 'https'):
            host = self.api.netloc
            if self.api.scheme == 'http':
                scheme = 'ws'
            else:
                scheme = 'wss'
        else:
            scheme = 'ws+unix'
            host = parse.unquote(self.api.netloc)
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
        if not _ws4py_installed:
            raise ValueError(
                'This feature requires the optional ws4py library.')
        if websocket_client is None:
            websocket_client = _WebsocketClient

        client = websocket_client(self.websocket_url)
        parsed = parse.urlparse(self.api.events._api_endpoint)
        client.resource = parsed.path

        return client
