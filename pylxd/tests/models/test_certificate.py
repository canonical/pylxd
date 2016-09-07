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
import os

from pylxd import models
from pylxd.tests import testing


class TestCertificate(testing.PyLXDTestCase):
    """Tests for pylxd.models.Certificate."""

    def test_get(self):
        """A certificate is retrieved."""
        cert = self.client.certificates.get('an-certificate')

        self.assertEqual('certificate-content', cert.certificate)

    def test_all(self):
        """A certificates are returned."""
        certs = self.client.certificates.all()

        self.assertIn('an-certificate', [c.fingerprint for c in certs])

    def test_create(self):
        """A certificate is created."""
        cert_data = open(os.path.join(
            os.path.dirname(__file__), '..', 'lxd.crt')).read().encode('utf-8')
        an_certificate = self.client.certificates.create(
            'test-password', cert_data)

        self.assertEqual(
            'eaf55b72fc23aa516d709271df9b0116064bf8cfa009cf34c67c33ad32c2320c',
            an_certificate.fingerprint)

    def test_fetch(self):
        """A partial object is fully fetched."""
        an_certificate = models.Certificate(
            self.client, fingerprint='an-certificate')

        an_certificate.sync()

        self.assertEqual('certificate-content', an_certificate.certificate)

    def test_delete(self):
        """A certificate is deleted."""
        # XXX: rockstar (08 Jun 2016) - This just executes a code path. An
        # assertion should be added.
        an_certificate = models.Certificate(
            self.client, fingerprint='an-certificate')

        an_certificate.delete()
