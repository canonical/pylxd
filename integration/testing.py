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
import unittest
import uuid

from pylxd import exceptions
from pylxd.client import Client
from integration.busybox import create_busybox_image


class IntegrationTestCase(unittest.TestCase):
    """A base test case for pylxd integration tests."""

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.client = Client()
        self.lxd = self.client.api

    def generate_object_name(self):
        """Generate a random object name."""
        # Underscores are not allowed in container names.
        test = self.id().split('.')[-1].replace('_', '')
        rando = str(uuid.uuid1()).split('-')[-1]
        return '{}-{}'.format(test, rando)

    def create_container(self):
        """Create a container in lxd."""
        fingerprint, alias = self.create_image()

        name = self.generate_object_name()
        machine = {
            'name': name,
            'architecture': '2',
            'profiles': ['default'],
            'ephemeral': False,
            'config': {'limits.cpu': '2'},
            'source': {'type': 'image',
                       'alias': alias},
        }
        result = self.lxd['containers'].post(json=machine)
        operation_uuid = result.json()['operation'].split('/')[-1]
        result = self.lxd.operations[operation_uuid].wait.get()

        self.addCleanup(self.delete_container, name)
        return name

    def delete_container(self, name, enforce=False):
        """Delete a container in lxd."""
        # enforce is a hack. There's a race somewhere in the delete.
        # To ensure we don't get an infinite loop, let's count.
        count = 0
        try:
            result = self.lxd['containers'][name].delete()
        except exceptions.LXDAPIException as e:
            if e.response.status_code in (400, 404):
                return
            raise
        while enforce and result.status_code == 404 and count < 10:
            try:
                result = self.lxd['containers'][name].delete()
            except exceptions.LXDAPIException as e:
                if e.response.status_code in (400, 404):
                    return
                raise
            count += 1
        try:
            operation_uuid = result.json()['operation'].split('/')[-1]
            result = self.lxd.operations[operation_uuid].wait.get()
        except KeyError:
            pass  # 404 cases are okay.

    def create_image(self):
        """Create an image in lxd."""
        path, fingerprint = create_busybox_image()
        with open(path, 'rb') as f:
            headers = {
                'X-LXD-Public': '1',
                }
            response = self.lxd.images.post(data=f.read(), headers=headers)
        operation_uuid = response.json()['operation'].split('/')[-1]
        self.lxd.operations[operation_uuid].wait.get()

        alias = self.generate_object_name()
        response = self.lxd.images.aliases.post(json={
            'description': '',
            'target': fingerprint,
            'name': alias
            })

        self.addCleanup(self.delete_image, fingerprint)
        return fingerprint, alias

    def delete_image(self, fingerprint):
        """Delete an image in lxd."""
        try:
            self.lxd.images[fingerprint].delete()
        except exceptions.LXDAPIException as e:
            if e.response.status_code == 404:
                return
            raise

    def create_profile(self):
        """Create a profile."""
        name = self.generate_object_name()
        config = {'limits.memory': '1GB'}
        self.lxd.profiles.post(json={
            'name': name,
            'config': config
            })
        return name

    def delete_profile(self, name):
        """Delete a profile."""
        try:
            self.lxd.profiles[name].delete()
        except exceptions.LXDAPIException as e:
            if e.response.status_code == 404:
                return
            raise

    def assertCommon(self, response):
        """Assert common LXD responses.

        LXD responses are relatively standard. This function makes assertions
        to all those standards.
        """
        self.assertEqual(response.status_code, response.json()['status_code'])
        self.assertEqual(
            ['metadata', 'operation', 'status', 'status_code', 'type'],
            sorted(response.json().keys()))
