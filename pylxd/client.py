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
import functools
import os

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

import requests
import requests_unixsocket

from pylxd import exceptions
from pylxd.container import Container
from pylxd.image import Image
from pylxd.operation import Operation
from pylxd.profile import Profile

requests_unixsocket.monkeypatch()


class _APINode(object):
    """An api node object.
    """

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

    def get(self, *args, **kwargs):
        """Perform an HTTP GET."""
        return self.session.get(self._api_endpoint, *args, **kwargs)

    def post(self, *args, **kwargs):
        """Perform an HTTP POST."""
        return self.session.post(self._api_endpoint, *args, **kwargs)

    def put(self, *args, **kwargs):
        """Perform an HTTP PUT."""
        return self.session.put(self._api_endpoint, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """Perform an HTTP delete."""
        return self.session.delete(self._api_endpoint, *args, **kwargs)


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

    class Containers(object):
        """
        Manager for :class:`~pylxd.container.Container` of a :class:`Client`.

        .. attribute:: all

            Partial of :meth:`Container.all <pylxd.container.Container.all>`,
            calling it without argument returns the same as calling that method
            with just the client argument.

        .. attribute:: get

            Partial of of :meth:`Container.get
            <pylxd.container.Container.get>`.

        .. attribute:: create

            Partial of of :meth:`Container.create
            <pylxd.container.Container.create>`.
        """
        def __init__(self, client):
            self.get = functools.partial(Container.get, client)
            self.all = functools.partial(Container.all, client)
            self.create = functools.partial(Container.create, client)

    class Images(object):
        """
        Manager for :py:class:`~pylxd.image.Image` of a :class:`Client`.

        .. attribute:: all

            Partial of :meth:`Image.all <pylxd.image.Image.all>`,

        .. attribute:: get

            Partial of of :meth:`Image.get <pylxd.image.Image.get>`.

        .. attribute:: create

            Partial of of :meth:`Image.create <pylxd.image.Image.create>`.
        """
        def __init__(self, client):
            self.get = functools.partial(Image.get, client)
            self.all = functools.partial(Image.all, client)
            self.create = functools.partial(Image.create, client)

    class Operations(object):
        """
        Manager for :class:`~pylxd.operation.Operation` of a :class:`Client`.

        .. attribute:: get

            Partial of of :meth:`Operation.get
            <pylxd.operation.Operation.get>`.
        """
        def __init__(self, client):
            self.get = functools.partial(Operation.get, client)

    class Profiles(object):
        """
        Manager for :py:class:`~pylxd.profile.Profile` of a :class:`Client`.

        .. attribute:: all

            Partial of :meth:`Profile.all <pylxd.profile.Profile.all>`,

        .. attribute:: get

            Partial of of :meth:`Profile.get <pylxd.profile.Profile.get>`.

        .. attribute:: create

            Partial of of :meth:`Profile.create
            <pylxd.profile.Profile.create>`.
        """
        def __init__(self, client):
            self.get = functools.partial(Profile.get, client)
            self.all = functools.partial(Profile.all, client)
            self.create = functools.partial(Profile.create, client)

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
                quote(path, safe='')))
        self.api = self.api[version]

        # Verify the connection is valid.
        try:
            response = self.api.get()
            if response.status_code != 200:
                raise exceptions.ClientConnectionFailed()
            auth = response.json()['metadata']['auth']
            if auth != "trusted":
                raise exceptions.ClientAuthenticationFailed()
        except (requests.exceptions.ConnectionError,
                requests.exceptions.InvalidURL):
            raise exceptions.ClientConnectionFailed()

        self.containers = self.Containers(self)
        self.images = self.Images(self)
        self.operations = self.Operations(self)
        self.profiles = self.Profiles(self)
