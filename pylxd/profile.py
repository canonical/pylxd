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
import six
from pylxd import mixin


class Profile(mixin.Marshallable):
    """A LXD profile."""

    __slots__ = [
        '_client',
        'config', 'devices', 'name'
        ]

    @classmethod
    def get(cls, client, name):
        """Get a profile."""
        response = client.api.profiles[name].get()

        if response.status_code == 404:
            raise NameError('No profile with name "{}"'.format(name))
        return cls(_client=client, **response.json()['metadata'])

    @classmethod
    def all(cls, client):
        """Get all profiles."""
        response = client.api.profiles.get()

        profiles = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            profiles.append(cls(_client=client, name=name))
        return profiles

    @classmethod
    def create(cls, client, name, config, devices={}):
        """Create a profile."""
        client.api.profiles.post(json={
            'name': name,
            'config': config,
            'devices': devices
            })

        return cls.get(client, name)

    def __init__(self, **kwargs):
        super(Profile, self).__init__()
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

    def update(self):
        """Update the profile in LXD based on local changes."""
        marshalled = self.marshall()
        # The name property cannot be updated.
        del marshalled['name']

        self._client.api.profiles[self.name].put(json=marshalled)

    def rename(self, new):
        """Rename the profile."""
        raise NotImplementedError(
            'LXD does not currently support renaming profiles')
        self._client.api.profiles[self.name].post(json={'name': new})
        self.name = new

    def delete(self):
        """Delete a profile."""
        self._client.api.profiles[self.name].delete()
