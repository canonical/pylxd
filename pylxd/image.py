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
import hashlib

import six

from pylxd import exceptions, mixin
from pylxd.operation import Operation


class Image(mixin.Marshallable):
    """A LXD Image."""

    __slots__ = [
        '_client',
        'aliases', 'architecture', 'created_at', 'expires_at', 'filename',
        'fingerprint', 'properties', 'public', 'size', 'uploaded_at'
    ]

    @classmethod
    def get(cls, client, fingerprint):
        """Get an image."""
        try:
            response = client.api.images[fingerprint].get()
        except exceptions.LXDAPIException as e:
            if e.response.status_code == 404:
                raise exceptions.NotFound()
            raise

        image = cls(_client=client, **response.json()['metadata'])
        return image

    @classmethod
    def all(cls, client):
        """Get all images."""
        response = client.api.images.get()

        images = []
        for url in response.json()['metadata']:
            fingerprint = url.split('/')[-1]
            images.append(cls(_client=client, fingerprint=fingerprint))
        return images

    @classmethod
    def create(cls, client, image_data, public=False, wait=False):
        """Create an image."""
        fingerprint = hashlib.sha256(image_data).hexdigest()

        headers = {}
        if public:
            headers['X-LXD-Public'] = '1'
        try:
            response = client.api.images.post(
                data=image_data, headers=headers)
        except exceptions.LXDAPIException as e:
            raise exceptions.CreateFailed(e.response.json())

        if wait:
            Operation.wait_for_operation(client, response.json()['operation'])
        return cls(_client=client, fingerprint=fingerprint)

    def __init__(self, **kwargs):
        super(Image, self).__init__()
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

    def update(self):
        """Update LXD based on changes to this image."""
        try:
            marshalled = self.marshall()
        except AttributeError:
            raise exceptions.ObjectIncomplete()
        self._client.api.images[self.fingerprint].put(
            json=marshalled)

    def delete(self, wait=False):
        """Delete the image."""
        response = self._client.api.images[self.fingerprint].delete()

        if wait:
            Operation.wait_for_operation(
                self._client, response.json()['operation'])

    def fetch(self):
        """Fetch the object from LXD, populating attributes."""
        try:
            response = self._client.api.images[self.fingerprint].get()
        except exceptions.LXDAPIException as e:
            if e.response.status_code == 404:
                raise exceptions.NotFound()
            raise

        for key, val in six.iteritems(response.json()['metadata']):
            setattr(self, key, val)

    def export(self):
        """Export the image."""
        try:
            response = self._client.api.images[self.fingerprint].export.get()
        except exceptions.LXDAPIException as e:
            if e.response.status_code == 404:
                raise exceptions.NotFound()
            raise

        return response.content
