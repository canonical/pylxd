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
import warnings
from base64 import b64decode

from pylxd import exceptions, models
from pylxd.tests import testing

LINKS_URL = "http://pylxd.test/1.0/cluster/links"
LINK_URL = f"{LINKS_URL}/an-link"


class TestClusterLink(testing.PyLXDTestCase):
    """Tests for pylxd.models.ClusterLink."""

    def assert_no_request_to(self, url_prefix):
        self.assertFalse(
            [
                r
                for r in self.requests_mock.request_history
                if r.url.startswith(url_prefix)
            ]
        )

    def test_get(self):
        """A cluster link is fetched by name."""
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.cluster.links.get("an-link")
        testing.add_api_extension_helper(self, ["cluster_links"])

        link = self.client.cluster.links.get("an-link")

        self.assertEqual("an-link", link.name)
        self.assertEqual("public", link.type)
        self.assertEqual({"volatile.addresses": "127.0.0.1:8443"}, link.config)
        self.assertEqual([], link.used_by)

    def test_all(self):
        """All cluster links are listed as sparse objects."""
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.cluster.links.all()
        testing.add_api_extension_helper(self, ["cluster_links"])

        links = self.client.cluster.links.all()

        self.assertEqual(["an-link"], [link.name for link in links])
        # Only the listing was fetched; the type is synced on first access.
        self.assertFalse(
            [r for r in self.requests_mock.request_history if r.url == LINK_URL]
        )
        self.assertEqual("public", links[0].type)

    def test_all_unquotes_names(self):
        """LXD escapes names in the listing URLs; objects get the real name."""
        testing.add_api_extension_helper(self, ["cluster_links"])
        self.add_rule(
            {
                "text": json.dumps(
                    {
                        "type": "sync",
                        "metadata": ["/1.0/cluster/links/east%20coast"],
                    }
                ),
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/cluster/links$",
            }
        )

        links = self.client.cluster.links.all()

        self.assertEqual(["east coast"], [link.name for link in links])

    def test_get_quotes_name(self):
        """A "#" in a name must not become a URL fragment."""
        testing.add_api_extension_helper(self, ["cluster_links"])

        link = self.client.cluster.links.get("east#prod")

        self.assertEqual("east#prod", link.name)
        self.last_matching_request("GET", f"{LINKS_URL}/east%23prod")

    def test_instance_api_quotes_name(self):
        """Instance requests reach the escaped path, not a different link."""
        testing.add_api_extension_helper(self, ["cluster_links"])
        self.add_rule(
            {
                "text": json.dumps({"type": "sync"}),
                "method": "DELETE",
                "url": r"^http://pylxd.test/1.0/cluster/links/east%20coast$",
            }
        )
        link = models.ClusterLink(self.client, name="east coast")

        link.state()
        link.delete()

        self.last_matching_request("GET", f"{LINKS_URL}/east%20coast/state")
        self.last_matching_request("DELETE", f"{LINKS_URL}/east%20coast")
        self.assert_no_request_to(f"{LINKS_URL}/east/")

    def test_all_empty(self):
        """LXD answers null, not [], when there are no links."""
        testing.add_api_extension_helper(self, ["cluster_links"])
        self.add_rule(
            {
                "text": json.dumps({"type": "sync", "metadata": None}),
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/cluster/links$",
            }
        )

        self.assertEqual([], self.client.cluster.links.all())

    def test_links_via_cluster_object(self):
        """The links manager on a fetched Cluster binds only the client."""
        testing.add_api_extension_helper(self, ["clustering", "cluster_links"])
        cluster = self.client.cluster.get()

        self.assertEqual("an-link", cluster.links.get("an-link").name)
        self.assertTrue(cluster.links.exists("an-link"))
        self.assertEqual(["an-link"], [link.name for link in cluster.links.all()])

    def test_exists(self):
        """exists is True for an existing link."""
        testing.add_api_extension_helper(self, ["cluster_links"])

        self.assertTrue(self.client.cluster.links.exists("an-link"))

    def test_exists_not_found(self):
        """exists is False when LXD answers 404."""
        testing.add_api_extension_helper(self, ["cluster_links"])
        self.add_rule(
            {
                "text": json.dumps(
                    {"type": "error", "error": "not found", "error_code": 404}
                ),
                "status_code": 404,
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/cluster/links/missing$",
            }
        )

        self.assertFalse(self.client.cluster.links.exists("missing"))

    def test_create_bidirectional(self):
        """An active bidirectional link is created from a trust token."""
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.cluster.links.create("an-link", trust_token="tok")
        testing.add_api_extension_helper(self, ["cluster_links"])

        link = self.client.cluster.links.create(
            "an-link", trust_token="tok", auth_groups=["admins"]
        )

        self.assertIsInstance(link, models.ClusterLink)
        self.assertEqual("an-link", link.name)
        body = self.last_matching_request("POST", LINKS_URL).json()
        self.assertEqual(
            {
                "name": "an-link",
                "type": "bidirectional",
                "description": "",
                "config": {},
                "trust_token": "tok",
                "auth_groups": ["admins"],
            },
            body,
        )

    def test_create_requires_trust_token(self):
        """Without a token LXD would create a pending link, so refuse early."""
        testing.add_api_extension_helper(
            self, ["cluster_links", "cluster_links_unidirectional"]
        )

        with self.assertRaises(ValueError):
            self.client.cluster.links.create("an-link")
        with self.assertRaises(ValueError):
            self.client.cluster.links.create("an-link", trust_token="")
        with self.assertRaises(ValueError):
            self.client.cluster.links.create("an-link", type="unidirectional")
        self.assert_no_request_to(LINKS_URL)

    def test_create_unidirectional_requires_extension(self):
        """Unidirectional links need cluster_links_unidirectional."""
        testing.add_api_extension_helper(self, ["cluster_links"])

        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.cluster.links.create(
                "an-link", trust_token="tok", type="unidirectional"
            )

    def test_create_unidirectional(self):
        """A unidirectional link is created from a remote identity token."""
        testing.add_api_extension_helper(
            self, ["cluster_links", "cluster_links_unidirectional"]
        )

        link = self.client.cluster.links.create(
            "an-link", trust_token="tok", type="unidirectional", description="d"
        )

        self.assertEqual("an-link", link.name)
        body = self.last_matching_request("POST", LINKS_URL).json()
        self.assertEqual("unidirectional", body["type"])
        self.assertEqual("tok", body["trust_token"])
        self.assertEqual("d", body["description"])
        self.assertNotIn("fingerprint", body)

    def test_create_token(self):
        """A pending bidirectional link yields a base64 trust token."""
        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.cluster.links.create_token("an-link")
        testing.add_api_extension_helper(self, ["cluster_links"])

        token = self.client.cluster.links.create_token(
            "an-link", auth_groups=["admins"]
        )

        body = self.last_matching_request("POST", LINKS_URL).json()
        self.assertNotIn("trust_token", body)
        self.assertEqual("bidirectional", body["type"])
        self.assertEqual(["admins"], body["auth_groups"])
        decoded = json.loads(b64decode(token))
        self.assertEqual("an-link", decoded["client_name"])
        self.assertEqual("abcd1234", decoded["fingerprint"])
        self.assertEqual(["127.0.0.1:8443"], decoded["addresses"])
        self.assertEqual("s3cret", decoded["secret"])

    def test_create_pending_public_requires_extension(self):
        """Public links need cluster_links_public."""
        testing.add_api_extension_helper(self, ["cluster_links"])

        with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
            self.client.cluster.links.create_pending_public("an-link", "127.0.0.1:8443")

    def test_create_pending_public(self):
        """A pending public link yields the remote fingerprint."""
        testing.add_api_extension_helper(
            self, ["cluster_links", "cluster_links_public"]
        )

        fingerprint = self.client.cluster.links.create_pending_public(
            "an-link", "127.0.0.1:8443", description="d", config={"user.a": "b"}
        )

        self.assertEqual("abcd1234", fingerprint)
        body = self.last_matching_request("POST", LINKS_URL).json()
        self.assertEqual(
            {
                "name": "an-link",
                "type": "public",
                "description": "d",
                "config": {"user.a": "b"},
                "remote_address": "127.0.0.1:8443",
            },
            body,
        )

    def test_create_public_confirm(self):
        """A pending public link is confirmed with the fingerprint."""
        testing.add_api_extension_helper(
            self, ["cluster_links", "cluster_links_public"]
        )

        link = self.client.cluster.links.create(
            "an-link", type="public", fingerprint="abcd1234"
        )

        self.assertEqual("public", link.type)
        body = self.last_matching_request("POST", LINKS_URL).json()
        self.assertEqual("public", body["type"])
        self.assertEqual("abcd1234", body["fingerprint"])
        self.assertNotIn("remote_address", body)
        self.assertNotIn("trust_token", body)

    def test_create_public_requires_fingerprint(self):
        """Confirming a public link needs the fingerprint from the pending step."""
        testing.add_api_extension_helper(
            self, ["cluster_links", "cluster_links_public"]
        )

        with self.assertRaises(ValueError):
            self.client.cluster.links.create("an-link", type="public")
        self.assert_no_request_to(LINKS_URL)

    def test_create_public_rejects_description_and_config(self):
        """LXD drops both when confirming; they belong to the pending step."""
        testing.add_api_extension_helper(
            self, ["cluster_links", "cluster_links_public"]
        )

        with self.assertRaises(ValueError):
            self.client.cluster.links.create(
                "an-link", type="public", fingerprint="abcd1234", description="d"
            )
        with self.assertRaises(ValueError):
            self.client.cluster.links.create(
                "an-link",
                type="public",
                fingerprint="abcd1234",
                config={"user.a": "b"},
            )
        self.assert_no_request_to(LINKS_URL)

    def test_instance_methods_require_extension(self):
        """A directly built link is gated like the class methods."""
        link = models.ClusterLink(
            self.client, name="an-link", description="", type="public", config={}
        )

        for call in (
            link.state,
            lambda: link.rename("new-link"),
            lambda: link.patch({"description": "d"}),
            link.save,
            link.delete,
        ):
            with self.assertRaises(exceptions.LXDAPIExtensionNotAvailable):
                call()
        self.assert_no_request_to(LINK_URL)

    def test_state(self):
        """The link state lists the remote members."""
        testing.add_api_extension_helper(self, ["cluster_links"])
        link = self.client.cluster.links.get("an-link")

        state = link.state()

        self.assertEqual("Active", state["cluster_link_members"][0]["status"])
        self.last_matching_request("GET", f"{LINK_URL}/state")

    def test_rename(self):
        """A link is renamed."""
        testing.add_api_extension_helper(self, ["cluster_links"])
        link = self.client.cluster.links.get("an-link")

        link.rename("new-link")

        body = self.last_matching_request("POST", LINK_URL).json()
        self.assertEqual({"name": "new-link"}, body)
        self.assertEqual("new-link", link.name)

    def test_save(self):
        """save sends only the writable fields."""
        testing.add_api_extension_helper(self, ["cluster_links"])
        link = self.client.cluster.links.get("an-link")

        link.description = "updated"
        link.save()

        body = self.last_matching_request("PUT", LINK_URL).json()
        self.assertEqual(
            {
                "description": "updated",
                "config": {"volatile.addresses": "127.0.0.1:8443"},
            },
            body,
        )

    def test_patch(self):
        """patch sends the given fields and re-syncs."""
        testing.add_api_extension_helper(self, ["cluster_links"])
        link = self.client.cluster.links.get("an-link")

        link.patch({"description": "patched"})

        body = self.last_matching_request("PATCH", LINK_URL).json()
        self.assertEqual({"description": "patched"}, body)

    def test_delete(self):
        """A link is deleted."""
        testing.add_api_extension_helper(self, ["cluster_links"])
        link = self.client.cluster.links.get("an-link")

        link.delete()

        self.last_matching_request("DELETE", LINK_URL)
        self.assertIsNone(link.client)

    def test_used_by_optional(self):
        """A server without cluster_links_used_by omits used_by silently."""
        testing.add_api_extension_helper(self, ["cluster_links"])

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            link = models.ClusterLink(
                self.client,
                name="an-link",
                description="",
                type="public",
                config={},
            )
            link.save()

        self.assertEqual([], caught)
        body = self.last_matching_request("PUT", LINK_URL).json()
        self.assertEqual({"description": "", "config": {}}, body)

    def test_eq(self):
        """Links compare by name."""
        link = models.ClusterLink(self.client, name="an-link")

        self.assertEqual(link, models.ClusterLink(self.client, name="an-link"))
        self.assertNotEqual(link, models.ClusterLink(self.client, name="other"))
        self.assertNotEqual(link, "an-link")
