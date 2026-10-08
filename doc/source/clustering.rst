Clustering
==========

LXD supports clustering. There is only one cluster object.

Cluster object
--------------

The :py:class:`~pylxd.models.cluster.Cluster` object represents the json
object that is returned from `GET /1.0/cluster`.

.. note:: Please see the pylxd API documentation for more information on
        cluster methods and parameters.  The following is a summary.

Cluster methods
^^^^^^^^^^^^^^^

A cluster can be queried through the following client manager methods:


  - `get()` - Returns the cluster.
  - `enable(server_name)` - Enable clustering.


Cluster Object attributes
^^^^^^^^^^^^^^^^^^^^^^^^^

For more information about the specifics of these attributes, please see
the `LXD Cluster REST API`_ documentation.

  - `server_name` - the name of the server in the cluster
  - `enabled` - if the node is enabled
  - `member_config` - configuration information for new cluster members.


Cluster Members objects
-----------------------

The :py:class:`~pylxd.models.cluster.ClusterMember` object represents the
json object that is returned from `GET /1.0/cluster/members/<name>`.  For
example:

.. code:: python

    client = pylxd.Client()
    member = client.cluster.members.get('node-5')


Methods available on `<clustermember_object>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A cluster member can be queried through the following manager methods:

  - `all` - get all the members of the cluster.
  - `get` - a get a single named member of the cluster.


Cluster Member Object attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For more information about the specifics of these attributes, please see
the `LXD Cluster REST API`_ documentation.

  - `server_name` - the name of the server in the cluster
  - `url` - the url the lxd endpoint
  - `database` - if the distributed database is replicated on this node
  - `status` - if the member is off or online
  - `message` - a general message


Cluster links
-------------

The :py:class:`~pylxd.models.cluster.ClusterLink` object represents the json
object that is returned from `GET /1.0/cluster/links/<name>`. Cluster links
connect two LXD clusters; `lxd`-protocol image registries use them to reach
the other cluster. They need the `cluster_links` API extension. For example:

.. code:: python

    client = pylxd.Client()
    link = client.cluster.links.get('other-cluster')
    link.state()['cluster_link_members']

Cluster link methods
^^^^^^^^^^^^^^^^^^^^

Cluster links can be queried through the following client manager methods:

  - `all()` - get all the cluster links.
  - `get(name)` - get a single named cluster link.
  - `exists(name)` - whether a named cluster link exists.
  - `create(name, trust_token=None, type='bidirectional', auth_groups=None,
    description='', config=None, fingerprint=None)` - create an active link.
    Bidirectional and unidirectional links need `trust_token`; public links
    need `fingerprint`.
  - `create_token(name, auth_groups=None, description='')` - create a pending
    bidirectional link and return the trust token for the other cluster.
  - `create_pending_public(name, remote_address, description='', config=None)`
    - create a pending public link and return the remote certificate
    fingerprint.

And on a `<clusterlink_object>`:

  - `state()` - the remote members and their status.
  - `rename(new_name)` - rename the link.
  - `save()`, `patch(dict)`, `put(dict)` - update `description` and `config`.
  - `delete()` - delete the link. LXD refuses while an image registry uses it.

Every cluster link operation is synchronous on the server.

Creating a link
^^^^^^^^^^^^^^^

A **bidirectional** link is created in two steps, one on each cluster. The
first cluster issues a token, the second cluster activates the link with it,
and the first link becomes active when the second connects back:

.. code:: python

    # On cluster A
    token = client_a.cluster.links.create_token('cluster-b')

    # On cluster B
    link = client_b.cluster.links.create('cluster-a', trust_token=token)

A **unidirectional** link (`cluster_links_unidirectional` extension) uses a
token issued on the remote with `lxc auth identity create cluster-link/<name>`:

.. code:: python

    link = client.cluster.links.create(
        'cluster-a', trust_token=token, type='unidirectional')

A **public** link (`cluster_links_public` extension) connects to a remote
that serves public images without authentication. pylxd returns the remote
certificate fingerprint and does not confirm the link itself; verify the
fingerprint out of band, then confirm. LXD records `description` and `config`
when the pending link is created, so pass them to `create_pending_public()`;
`create()` rejects them for public links:

.. code:: python

    fingerprint = client.cluster.links.create_pending_public(
        'images-mirror', 'images.example.com:8443')
    # ... check that fingerprint matches the remote certificate ...
    link = client.cluster.links.create(
        'images-mirror', type='public', fingerprint=fingerprint)

Cluster link object attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For more information about the specifics of these attributes, please see
the `LXD Cluster REST API`_ documentation.

  - `name` - the name of the link
  - `description` - a description of the link
  - `type` - `bidirectional`, `unidirectional` or `public`
  - `config` - `volatile.*` keys managed by LXD and `user.*` keys
  - `used_by` - resources using the link; only with the
    `cluster_links_used_by` extension

.. links

.. _LXD Clustering: https://canonical.com/lxd/docs/latest/clustering/
.. _LXD Cluster REST API: https://canonical.com/lxd/docs/latest/api/#/cluster
