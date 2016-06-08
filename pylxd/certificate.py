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
import binascii

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding
import six


class Certificate(object):
    """A LXD certificate."""

    __slots__ = [
        '_client',
        'certificate', 'fingerprint', 'type',
    ]

    @classmethod
    def get(cls, client, fingerprint):
        """Get a certificate by fingerprint."""
        response = client.api.certificates[fingerprint].get()

        return cls(_client=client, **response.json()['metadata'])

    @classmethod
    def all(cls, client):
        """Get all certificates."""
        response = client.api.certificates.get()

        certs = []
        for cert in response.json()['metadata']:
            fingerprint = cert.split('/')[-1]
            certs.append(cls(_client=client, fingerprint=fingerprint))
        return certs

    @classmethod
    def create(cls, client, password, cert_data):
        """Create a new certificate."""
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        data = {
            'type': 'client',
            'certificate': cert.public_bytes(Encoding.PEM).decode('utf-8'),
            'password': password,
        }
        client.api.certificates.post(json=data)

        # XXX: rockstar (08 Jun 2016) - Please see the open lxd bug here:
        # https://github.com/lxc/lxd/issues/2092
        fingerprint = binascii.hexlify(
            cert.fingerprint(hashes.SHA256())).decode('utf-8')
        return cls.get(client, fingerprint)

    def __init__(self, **kwargs):
        super(Certificate, self).__init__()
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

    def delete(self):
        """Delete the certificate."""
        self._client.api.certificates[self.fingerprint].delete()

    def fetch(self):
        """Fetch an updated representation of the certificate."""
        response = self._client.api.certificates[self.fingerprint].get()

        for key, value in six.iteritems(response.json()['metadata']):
            setattr(self, key, value)
