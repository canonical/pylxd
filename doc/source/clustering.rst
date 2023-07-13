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

.. links

.. _LXD Clustering: https://documentation.ubuntu.com/lxd/en/latest/clustering/
.. _LXD REST API: https://documentation.ubuntu.com/lxd/en/latest/api/
