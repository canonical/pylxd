# Copyright (c) 2015 Canonical Ltd
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
# XXX: rockstar (15 Feb 2016) - This module should be renamed to 'profile'.
import json

from pylxd import base
from pylxd import mixin


class LXDProfile(base.LXDBase):

    def profile_list(self):
        '''List profiles on the LXD daemon as an array.'''
        (state, data) = self.connection.get_object('GET', '/1.0/profiles')
        return [profiles.split('/1.0/profiles/')[-1]
                for profiles in data['metadata']]

    def profile_create(self, profile):
        '''Create an LXD Profile'''
        return self.connection.get_status('POST', '/1.0/profiles',
                                          json.dumps(profile))

    def profile_show(self, profile):
        '''Display the LXD profile'''
        return self.connection.get_object('GET', '/1.0/profiles/%s'
                                          % profile)

    def profile_defined(self, profile):
        '''Check for an LXD profile'''
        return self.connection.get_status('GET', '/1.0/profiles/%s'
                                          % profile)

    def profile_update(self, profile, config):
        '''Update the LXD profile (not implemented)'''
        return self.connection.get_status('PUT', '/1.0/profiles/%s'
                                          % profile,
                                          json.dumps(config))

    def profile_rename(self, profile, config):
        '''Rename the LXD profile'''
        return self.connection.get_status('POST', '/1.0/profiles/%s'
                                          % profile,
                                          json.dumps(config))

    def profile_delete(self, profile):
        '''Delete the LXD profile'''
        return self.connection.get_status('DELETE', '/1.0/profiles/%s'
                                          % profile)


class Profile(mixin.Marshallable):

    __slots__ = [
        '_client',
        'config', 'devices', 'name'
        ]

    @classmethod
    def get(cls, client, name):
        response = client.api.profiles[name].get()

        if response.status_code == 404:
            raise NameError('No profile with name "{}"'.format(name))
        return cls(_client=client, **response.json()['metadata'])

    @classmethod
    def all(cls, client):
        response = client.api.profiles.get()

        profiles = []
        for url in response.json()['metadata']:
            name = url.split('/')[-1]
            profiles.append(cls(_client=client, name=name))
        return profiles

    @classmethod
    def create(cls, client, name, config):
        client.api.profiles.post(json={
            'name': name,
            'config': config
            })

        return cls.get(client, name)

    def __init__(self, **kwargs):
        super(Profile, self).__init__()
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def update(self):
        marshalled = self.marshall()
        # The name property cannot be updated.
        del marshalled['name']

        self._client.api.profiles[self.name].put(json=marshalled)

    def rename(self, new):
        raise NotImplementedError('LXD does not currently support renaming profiles')
        self._client.api.profiles[self.name].post(json={'name': new})
        self.name = new

    def delete(self):
        self._client.api.profiles[self.name].delete()
