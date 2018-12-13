Clustering
==========

LXD supports clustering. There is only one cluster object.

Cluster object
--------------

The :py:class:`~pylxd.models.cluster.Cluster` object represents the json
object that is returned from `GET /1.0/cluster`.

There is also a :py:class:`~pylxd.models.cluster.ClusterMember` and object that represents a
cluster member at `GET
/1.0/cluster/members`.  Note that it should be
accessed from the cluster object.  For example:

.. code:: python

    client = pylxd.Client()
    cluster = client.cluster.get()
    member = cluster.members.get('node-5')


.. note:: Please see the pylxd API documentation for more information on
        storage pool methods and parameters.  The following is a summary.

Cluster methods
^^^^^^^^^^^^^^^

A cluster can be queried through the following client manager methods:


  - `get()` - Returns the cluster.


Cluster Object attributes
^^^^^^^^^^^^^^^^^^^^^^^^^

For more information about the specifics of these attributes, please see
the `LXD Cluster REST API`_ documentation.

  - `server_name` - the name of the server in the cluster
  - `enabled` - if the node is enabled
  - `member_config` - configuration information for new cluster members.


Cluster Members
---------------

Cluster Members are stored in a cluster.  On the `pylxd` API they are
accessed from a cluster object:

.. code:: Python

    cluster = client.cluster.get()
    members = cluster.members.all()
    named_member = cluster.members.get('membername')


Methods available on `<cluster_object>.members`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following methods are accessed from the `members` attribute on the cluster object.

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

.. links

.. _LXD Storage Pools: https://lxd.readthedocs.io/en/latest/storage/
.. _LXD REST API: https://github.com/lxc/lxd/blob/master/doc/rest-api.md
.. _LXD Cluster REST API: https://github.com/lxc/lxd/blob/master/doc/rest-api.md#10cluster
