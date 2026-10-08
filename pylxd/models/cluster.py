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
from base64 import b64encode
from urllib.parse import quote, unquote

from pylxd import managers
from pylxd.exceptions import LXDAPIException
from pylxd.models import _model as model


class Cluster(model.Model):
    """An LXD Cluster."""

    server_name = model.Attribute(readonly=True)
    enabled = model.Attribute(readonly=True)
    member_config = model.Attribute(readonly=True)

    members = model.Manager()
    certificate = model.Manager()
    links = model.Manager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.members = managers.ClusterMemberManager(self.client, self)
        self.certificate = managers.ClusterCertificateManager(self.client, self)
        self.links = managers.ClusterLinkManager(self.client)

    def __eq__(self, other):
        if not isinstance(other, Cluster):
            return NotImplemented
        return self.server_name == other.server_name

    __hash__ = None  # type: ignore  # unhashable, consistent with defining __eq__

    @property
    def api(self):
        return self.client.api.cluster

    @classmethod
    def enable(cls, client, server_name):
        """Enable clustering on a single non-clustered LXD server."""
        client.assert_has_api_extension("clustering_join")
        response = client.api.cluster.put(
            json={"server_name": server_name, "enabled": True},
        )

        # Wait for operation to complete
        operation = client.operations.wait_for_operation(response.json()["operation"])

        if operation.status_code == 200:
            return
        raise LXDAPIException(response)

    @classmethod
    def get(cls, client, *args):
        """Get cluster details"""
        client.assert_has_api_extension("clustering")
        response = client.api.cluster.get()
        container = cls(client, **response.json()["metadata"])
        return container


class ClusterMember(model.Model):
    """A LXD cluster member."""

    architecture = model.Attribute(readonly=True)
    description = model.Attribute(readonly=True)
    failure_domain = model.Attribute(readonly=True)
    roles = model.Attribute(readonly=True)
    url = model.Attribute(readonly=True)
    database = model.Attribute(readonly=True)
    server_name = model.Attribute(readonly=True)
    status = model.Attribute(readonly=True)
    message = model.Attribute(readonly=True)
    config = model.Attribute(readonly=True, optional=True)
    groups = model.Attribute(readonly=True, optional=True)

    cluster = model.Parent()

    @classmethod
    def get(cls, client, server_name):
        """Get a cluster member by name."""
        response = client.api.cluster.members[server_name].get()

        return cls(client, **response.json()["metadata"])

    @classmethod
    def all(cls, client, *args):
        """Get all cluster members."""
        response = client.api.cluster.members.get()

        nodes = []
        for node in response.json()["metadata"]:
            server_name = node.split("/")[-1]
            nodes.append(cls(client, server_name=server_name))
        return nodes

    @property
    def api(self):
        return self.client.api.cluster.members[self.server_name]


class ClusterLink(model.Model):
    """An LXD cluster link.

    This corresponds to the LXD endpoint at /1.0/cluster/links. Every
    operation on a cluster link is synchronous on the server, so none of the
    methods take a ``wait`` parameter.

    api_extension: 'cluster_links'
    """

    name = model.Attribute(readonly=True)
    description = model.Attribute()
    type = model.Attribute(readonly=True)
    config = model.Attribute()
    used_by = model.Attribute(readonly=True, optional=True)

    def __eq__(self, other):
        if not isinstance(other, ClusterLink):
            return NotImplemented
        return self.name == other.name

    __hash__ = None  # type: ignore  # unhashable, consistent with defining __eq__

    @classmethod
    def get(cls, client, name):
        """Get a cluster link by name.

        Implements GET /1.0/cluster/links/<name>.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :param name: name of the cluster link
        :type name: str
        :returns: the cluster link
        :rtype: :class:`ClusterLink`
        :raises: :class:`pylxd.exceptions.LXDAPIExtensionNotAvailable` if the
            server lacks the ``cluster_links`` extension
        :raises: :class:`pylxd.exceptions.NotFound` if the link does not exist
        """
        client.assert_has_api_extension("cluster_links")
        # LXD allows link names with characters such as "#" and " " that
        # _APINode does not escape, so quote them wherever they form a path.
        response = client.api.cluster.links[quote(name, safe="")].get()
        return cls(client, **response.json()["metadata"])

    @classmethod
    def all(cls, client):
        """Get all cluster links.

        Implements GET /1.0/cluster/links. The returned objects are sparse
        and fetch the rest of their attributes on first access.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :returns: the cluster links
        :rtype: list[:class:`ClusterLink`]
        :raises: :class:`pylxd.exceptions.LXDAPIExtensionNotAvailable` if the
            server lacks the ``cluster_links`` extension
        """
        client.assert_has_api_extension("cluster_links")
        response = client.api.cluster.links.get()
        # LXD returns null rather than an empty list when there are no links,
        # and escapes the names in the URLs it does return.
        urls = response.json()["metadata"] or []
        return [cls(client, name=unquote(url.split("/")[-1])) for url in urls]

    @classmethod
    def exists(cls, client, name):
        """Determine whether a cluster link exists.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :param name: name of the cluster link
        :type name: str
        :returns: ``True`` if the link exists
        :rtype: bool
        """
        try:
            cls.get(client, name)
            return True
        except cls.NotFound:
            return False

    @staticmethod
    def _assert_type_supported(client, link_type):
        client.assert_has_api_extension("cluster_links")
        if link_type == "unidirectional":
            client.assert_has_api_extension("cluster_links_unidirectional")
        elif link_type == "public":
            client.assert_has_api_extension("cluster_links_public")

    @classmethod
    def create(
        cls,
        client,
        name,
        trust_token=None,
        type="bidirectional",
        auth_groups=None,
        description="",
        config=None,
        fingerprint=None,
    ):
        """Create an active cluster link.

        Implements POST /1.0/cluster/links followed by a GET of the new link.
        The body depends on the link type:

        - ``bidirectional``: pass the ``trust_token`` issued by
          :meth:`create_token` on the other cluster.
        - ``unidirectional``: pass the ``trust_token`` issued on the remote
          with ``lxc auth identity create cluster-link/<name>``.
        - ``public``: pass the ``fingerprint`` returned by
          :meth:`create_pending_public` to confirm the remote certificate.
          LXD stores ``description`` and ``config`` for a public link when
          the pending link is created, so pass them to
          :meth:`create_pending_public` instead.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :param name: name of the cluster link
        :type name: str
        :param trust_token: trust token from the other cluster
        :type trust_token: str
        :param type: ``bidirectional``, ``unidirectional`` or ``public``
        :type type: str
        :param auth_groups: authorization groups to grant the remote
        :type auth_groups: list[str]
        :param description: description of the link
        :type description: str
        :param config: ``user.*`` configuration keys
        :type config: dict
        :param fingerprint: remote certificate fingerprint, public links only
        :type fingerprint: str
        :returns: the new cluster link
        :rtype: :class:`ClusterLink`
        :raises: :class:`pylxd.exceptions.LXDAPIExtensionNotAvailable` if the
            server lacks the ``cluster_links`` extension, or the extension
            for the requested type
        :raises: ValueError if ``trust_token`` is missing for a bidirectional
            or unidirectional link, or if ``fingerprint`` is missing or
            ``description`` or ``config`` is given for a public link
        :raises: :class:`pylxd.exceptions.LXDAPIException` if LXD rejects
            the request
        """
        cls._assert_type_supported(client, type)
        # Without these, LXD silently takes another path: a name with no token
        # creates a pending link, and a public confirmation drops description
        # and config.
        if type == "public":
            if not fingerprint:
                raise ValueError(
                    "fingerprint is required to confirm a public link; "
                    "call create_pending_public() first"
                )
            if description or config:
                raise ValueError(
                    "description and config are ignored when confirming a "
                    "public link; pass them to create_pending_public()"
                )
        elif not trust_token:
            raise ValueError(
                f"trust_token is required for an active {type} link; "
                "use create_token() to create a pending bidirectional link"
            )
        body = {
            "name": name,
            "type": type,
            "description": description,
            "config": config or {},
        }
        if trust_token is not None:
            body["trust_token"] = trust_token
        if auth_groups is not None:
            body["auth_groups"] = auth_groups
        if fingerprint is not None:
            body["fingerprint"] = fingerprint
        client.api.cluster.links.post(json=body)
        return cls.get(client, name)

    @classmethod
    def create_token(cls, client, name, auth_groups=None, description=""):
        """Create a pending bidirectional link and return its trust token.

        Implements POST /1.0/cluster/links without a trust token. The token
        is returned base64-encoded, the form ``lxc cluster link create``
        prints, ready to pass to :meth:`create` on the other cluster.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :param name: name of the cluster link
        :type name: str
        :param auth_groups: authorization groups to grant the remote
        :type auth_groups: list[str]
        :param description: description of the link
        :type description: str
        :returns: the trust token for the other cluster
        :rtype: str
        :raises: :class:`pylxd.exceptions.LXDAPIExtensionNotAvailable` if the
            server lacks the ``cluster_links`` extension
        """
        client.assert_has_api_extension("cluster_links")
        body = {
            "name": name,
            "type": "bidirectional",
            "description": description,
            "config": {},
        }
        if auth_groups is not None:
            body["auth_groups"] = auth_groups
        metadata = client.api.cluster.links.post(json=body).json()["metadata"]
        token = json.dumps(metadata, separators=(",", ":"))
        return b64encode(token.encode()).decode()

    @classmethod
    def create_pending_public(
        cls, client, name, remote_address, description="", config=None
    ):
        """Create a pending public link and return the remote fingerprint.

        Implements POST /1.0/cluster/links with ``remote_address``. The link
        stays inert until the returned SHA-256 fingerprint of the remote
        certificate is verified and passed to :meth:`create` with
        ``type="public"``. This is the only step at which LXD records the
        ``description`` and ``config`` of a public link.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :param name: name of the cluster link
        :type name: str
        :param remote_address: address of the remote cluster, ``host:port``
        :type remote_address: str
        :param description: description of the link
        :type description: str
        :param config: ``user.*`` configuration keys
        :type config: dict
        :returns: fingerprint of the remote certificate
        :rtype: str
        :raises: :class:`pylxd.exceptions.LXDAPIExtensionNotAvailable` if the
            server lacks the ``cluster_links_public`` extension
        """
        cls._assert_type_supported(client, "public")
        body = {
            "name": name,
            "type": "public",
            "description": description,
            "config": config or {},
            "remote_address": remote_address,
        }
        response = client.api.cluster.links.post(json=body)
        return response.json()["metadata"]["fingerprint"]

    @property
    def api(self):
        self.client.assert_has_api_extension("cluster_links")
        return self.client.api.cluster.links[quote(self.name, safe="")]

    def state(self):
        """Get the state of the link's remote members.

        Implements GET /1.0/cluster/links/<name>/state.

        :returns: the state as returned by LXD, with a
            ``cluster_link_members`` list of ``server_name``, ``address``
            and ``status``
        :rtype: dict
        """
        return self.api.state.get().json()["metadata"]

    def rename(self, new_name):
        """Rename the cluster link.

        Implements POST /1.0/cluster/links/<name>.

        :param new_name: the new name
        :type new_name: str
        :raises: :class:`pylxd.exceptions.LXDAPIException` if LXD rejects
            the request
        """
        self.api.post(json={"name": new_name})
        self.name = new_name


class ClusterCertificate(model.Model):
    """A LXD cluster certificate"""

    cluster_certificate = model.Attribute()
    cluster_certificate_key = model.Attribute()

    cluster = model.Parent()

    @classmethod
    def put(cls, client, cert, key):
        client.assert_has_api_extension("clustering_update_cert")

        response = client.api.cluster.certificate.put(
            json={"cluster_certificate": cert, "cluster_certificate_key": key}
        )

        if response.status_code == 200:
            return
        raise LXDAPIException(response)

    @property
    def api(self):
        return self.client.api.cluster.certificate
