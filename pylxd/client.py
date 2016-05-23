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
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from pylxd.container import Container
from pylxd.image import Image
from pylxd.operation import Operation
from pylxd.profile import Profile

requests_unixsocket.monkeypatch()


class _APINode(object):
    """An api node object.

    This class allows us to dynamically create request urls by expressing them
    in python. For example:

        >>> node = _APINode('http://example.com/api')
        >>> node.users[1].comments.get()

    ...would make an HTTP GET request on
    http://example.com/api/users/1/comments
    """

    def __init__(self, api_endpoint, default_kwargs=None):
        self._api_endpoint = api_endpoint
        self._default_kwargs = default_kwargs or {}

    def create_child(self, child):
        return self.__class__(
            '{}/{}'.format(self._api_endpoint, child),
            self._default_kwargs,
        )

    def __getattr__(self, name):
        return self.create_child(name)

    def __getitem__(self, item):
        return self.create_child(item)

    @property
    def session(self):
        if self._api_endpoint.startswith('http+unix://'):
            return requests_unixsocket.Session()
        else:
            return requests

    def request(self, method, *args, **kwargs):
        kwargs.update(self._default_kwargs)

        response = self.session.request(
            method.upper(),
            self._api_endpoint,
            *args,
            **kwargs
        )

        if int(response.status_code) >= 500:
            # A bit rough for now, let's see how it looks like in bug reports
            # and refine over time.
            raise RuntimeError(
                self._api_endpoint,
                args,
                kwargs,
                response.status_code,
                response.json()
            )

        return response

    def get(self, *args, **kwargs):
        """Perform an HTTP GET."""
        return self.request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        """Perform an HTTP POST."""
        return self.request('POST', *args, **kwargs)

    def put(self, *args, **kwargs):
        """Perform an HTTP PUT."""
        return self.request('PUT', *args, **kwargs)

    def delete(self, *args, **kwargs):
        """Perform an HTTP delete."""
        return self.request('DELETE', *args, **kwargs)


class Client(object):
    """A LXD client.

    This client wraps all the functionality required to interact with
    LXD, and is meant to be the sole entry point.
    """

    class Containers(object):
        """A convenience wrapper for :py:class:`~pylxd.container.Container`."""
        def __init__(self, client):
            self.get = functools.partial(Container.get, client)
            self.all = functools.partial(Container.all, client)
            self.create = functools.partial(Container.create, client)

    class Images(object):
        """A convenience wrapper for :py:class:`~pylxd.image.Image`."""
        def __init__(self, client):
            self.get = functools.partial(Image.get, client)
            self.all = functools.partial(Image.all, client)
            self.create = functools.partial(Image.create, client)

    class Operations(object):
        """A convenience wrapper for :py:class:`~pylxd.operation.Operation`."""
        def __init__(self, client):
            self.get = functools.partial(Operation.get, client)

    class Profiles(object):
        """A convenience wrapper for :py:class:`~pylxd.profile.Profile`."""
        def __init__(self, client):
            self.get = functools.partial(Profile.get, client)
            self.all = functools.partial(Profile.all, client)
            self.create = functools.partial(Profile.create, client)

    def __init__(self, endpoint=None, version='1.0',
                 client_crt=None, client_key=None, insecure=False):
        if endpoint is not None:
            self.api = _APINode(endpoint)

            # This should be made constructor arguments at some point.
            if client_crt and client_key:
                self.api._default_kwargs['cert'] = (client_crt, client_key)

            if insecure:
                self.api._default_kwargs['verify'] = False

            # Since disabling the warning is global, we can't and should not
            # try to do this per-instance.
            if 'LXD_INSECURE' in os.environ:
                requests.packages.urllib3.disable_warnings(
                    InsecureRequestWarning)
        else:
            if 'LXD_DIR' in os.environ:
                path = os.path.join(
                    os.environ.get('LXD_DIR'), 'unix.socket')
            else:
                path = '/var/lib/lxd/unix.socket'
            self.api = _APINode('http+unix://{}'.format(
                quote(path, safe='')))

        self.api = self.api[version]

        self.containers = self.Containers(self)
        self.images = self.Images(self)
        self.operations = self.Operations(self)
        self.profiles = self.Profiles(self)
