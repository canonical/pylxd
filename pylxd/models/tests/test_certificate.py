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
from unittest import mock

from pylxd import models
from pylxd.tests import testing


class TestCertificate(testing.PyLXDTestCase):
    """Tests for pylxd.models.Certificate."""

    def test_get(self):
        """A certificate is retrieved."""
        cert = self.client.certificates.get("an-certificate")

        self.assertEqual("certificate-content", cert.certificate)

    def test_all(self):
        """A certificates are returned."""
        certs = self.client.certificates.all()

        self.assertIn("an-certificate", [c.fingerprint for c in certs])

    def test_create(self):
        """A certificate is created."""
        with open(
            os.path.join(os.path.dirname(__file__), "../../tests", "lxd.crt"),
            encoding="utf-8",
        ) as f:
            cert_data = f.read().encode("utf-8")
        an_certificate = self.client.certificates.create("test-password", cert_data)

        self.assertEqual(
            "eaf55b72fc23aa516d709271df9b0116064bf8cfa009cf34c67c33ad32c2320c",
            an_certificate.fingerprint,
        )

    def test_create_token(self):
        """A token is returned."""
        self.add_rule(
            {
                "text": json.dumps(
                    {
                        "type": "sync",
                        "status": "Operation created",
                        "status_code": 100,
                        "operation": "/1.0/operations/a1d77f1b-7dfb-44e0-a3a3-1dd18bd5c15a",
                        "error_code": 0,
                        "error": "",
                        "metadata": {
                            "id": "a1d77f1b-7dfb-44e0-a3a3-1dd18bd5c15a",
                            "class": "token",
                            "description": "Executing operation",
                            "created_at": "2022-06-01T19:22:21.778204449Z",
                            "updated_at": "2022-06-01T19:22:21.778204449Z",
                            "status": "Running",
                            "status_code": 103,
                            "resources": None,
                            "metadata": {
                                "addresses": [
                                    "127.0.0.1:8443",
                                    "[::1]:8443",
                                ],
                                "fingerprint": "eddaa6023f9064f94dd6fadb36c01d9af9de935efff76f4ebada5a2fda4753be",
                                "request": {
                                    "name": "foo",
                                    "type": "client",
                                    "restricted": True,
                                    "projects": ["default"],
                                    "certificate": "",
                                    "password": "",
                                    "token": True,
                                },
                                "secret": "6efac2f5de066103dc9798414e916996a8ffe3b9818608d4fe3ba175fae618ad",
                            },
                            "may_cancel": True,
                            "err": "",
                            "location": "foo",
                        },
                    },
                ),
                "method": "POST",
                "url": r"^http://pylxd.test/1.0/certificates$",
                "headers": {
                    "location": "/1.0/operations/a1d77f1b-7dfb-44e0-a3a3-1dd18bd5c15a",
                },
            },
        )

        a_token = self.client.certificates.create_token(
            name="foo", projects=["default"], restricted=True
        )

        self.assertEqual(
            "eyJjbGllbnRfbmFtZSI6ImZvbyIsImZpbmdlcnByaW50IjoiZWRkYWE2MDIzZjkwNjRmOTRkZDZmYWRiMzZjMDFkOWFmOWRlOTM1ZWZmZjc2ZjRlYmFkYTVhMmZkYTQ3NTNiZSIsImFkZHJlc3NlcyI6WyIxMjcuMC4wLjE6ODQ0MyIsIls6OjFdOjg0NDMiXSwic2VjcmV0IjoiNmVmYWMyZjVkZTA2NjEwM2RjOTc5ODQxNGU5MTY5OTZhOGZmZTNiOTgxODYwOGQ0ZmUzYmExNzVmYWU2MThhZCJ9",
            a_token,
        )

    def test_fetch(self):
        """A partial object is fully fetched."""
        an_certificate = models.Certificate(self.client, fingerprint="an-certificate")

        an_certificate.sync()

        self.assertEqual("certificate-content", an_certificate.certificate)

    def test_delete(self):
        """A certificate is deleted."""
        # XXX: rockstar (08 Jun 2016) - This just executes a code path. An
        # assertion should be added.
        an_certificate = models.Certificate(self.client, fingerprint="an-certificate")

        an_certificate.delete()

    def _cert_data(self):
        with open(
            os.path.join(os.path.dirname(__file__), "../../tests", "lxd.crt")
        ) as f:
            return f.read().encode("utf-8")

    def _mock_post_response(
        self,
        fingerprint="eaf55b72fc23aa516d709271df9b0116064bf8cfa009cf34c67c33ad32c2320c",
    ):
        resp = mock.MagicMock()
        resp.status_code = 201
        resp.headers = {"Location": f"/1.0/certificates/{fingerprint}"}
        return resp

    def test_create_omits_projects_when_none(self):
        """create() does not include 'projects' in the POST payload when projects=None."""
        with mock.patch.object(
            self.client.api.session, "post", return_value=self._mock_post_response()
        ) as mock_post:
            self.client.certificates.create("test-password", self._cert_data())

        posted_json = mock_post.call_args.kwargs["json"]
        self.assertNotIn("projects", posted_json)

    def test_create_includes_projects_when_provided(self):
        """create() includes 'projects' in the POST payload when projects is given."""
        with mock.patch.object(
            self.client.api.session, "post", return_value=self._mock_post_response()
        ) as mock_post:
            self.client.certificates.create(
                "test-password", self._cert_data(), projects=["default"]
            )

        posted_json = mock_post.call_args.kwargs["json"]
        self.assertIn("projects", posted_json)
        self.assertEqual(["default"], posted_json["projects"])

    def test_create_token_omits_projects_when_none(self):
        """create_token() does not include 'projects' in the POST payload when projects=None."""
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {
            "metadata": {
                "metadata": {
                    "addresses": ["192.0.2.1:8443"],
                    "fingerprint": "abc123",
                    "secret": "some-secret",
                },
            },
        }
        with mock.patch.object(
            self.client.api.session, "post", return_value=mock_resp
        ) as mock_post:
            self.client.certificates.create_token(name="foo")

        posted_json = mock_post.call_args.kwargs["json"]
        self.assertNotIn("projects", posted_json)

    def test_create_token_includes_projects_when_provided(self):
        """create_token() includes 'projects' in the POST payload when projects is given."""
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {
            "metadata": {
                "metadata": {
                    "addresses": ["192.0.2.1:8443"],
                    "fingerprint": "abc123",
                    "secret": "some-secret",
                },
            },
        }
        with mock.patch.object(
            self.client.api.session, "post", return_value=mock_resp
        ) as mock_post:
            self.client.certificates.create_token(name="foo", projects=["default"])

        posted_json = mock_post.call_args.kwargs["json"]
        self.assertIn("projects", posted_json)
        self.assertEqual(["default"], posted_json["projects"])

    def test_create_with_trust_token(self):
        """create() uses trust_token instead of password when secret is provided."""
        with (
            mock.patch.object(self.client, "has_api_extension", return_value=True),
            mock.patch.object(
                self.client.api.session, "post", return_value=self._mock_post_response()
            ) as mock_post,
        ):
            self.client.certificates.create(
                "test-password", self._cert_data(), secret="my-token"
            )

        posted_json = mock_post.call_args.kwargs["json"]
        self.assertIn("trust_token", posted_json)
        self.assertEqual("my-token", posted_json["trust_token"])
        self.assertNotIn("password", posted_json)
