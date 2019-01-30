Storage Pools
=============

LXD supports creating and managing storage pools and storage volumes. General
keys are top-level. Driver specific keys are namespaced by driver name. Volume
keys apply to any volume created in the pool unless the value is overridden on
a per-volume basis.

Storage Pool objects
--------------------

:py:class:`~pylxd.models.storage_pool.StoragePool` objects represent the json
object that is returned from `GET /1.0/storage-pools/<name>` and then the
associated methods that are then available at the same endpoint.

There are also :py:class:`~pylxd.models.storage_pool.StorageResource` and
:py:class:`~pylxd.models.storage_pool.StorageVolume` objects that represent the
storage resources endpoint for a pool at `GET
/1.0/storage-pools/<pool>/resources` and a storage volume on a pool at `GET
/1.0/storage-pools/<pool>/volumes/<type>/<name>`.  Note that these should be
accessed from the storage pool object.  For example:

.. code:: python

    client = pylxd.Client()
    storage_pool = client.storage_pools.get('poolname')
    storage_volume = storage_pool.volumes.get('custom', 'volumename')


.. note:: For more details of the LXD documentation concerning storage pools
        please see `LXD Storage Pools REST API`_ Documentation and `LXD Storage Pools`_
        Documentation.  This provides information on the parameters and attributes in
        the following methods.

.. note:: Please see the pylxd API documentation for more information on
        storage pool methods and parameters.  The following is a summary.

Storage Pool Manager methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Storage-pools can be queried through the following client manager methods:

  - `all()` - Return a list of storage pools.
  - `get()` - Get a specific storage-pool, by its name.
  - `exists()` - Return a boolean for whether a storage-pool exists by name.
  - `create()` - Create a storage-pool.  **Note the config in the create class
    method is the WHOLE json object described as `input` in the API docs.**
    e.g. the 'config' key in the API docs would actually be `config.config` as
    passed to this method.


Storage-pool Object attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For more information about the specifics of these attributes, please see
the `LXD Storage Pools REST API`_ documentation.

  - `name` - the name of the storage pool
  - `driver` - the driver (or type of storage pool). e.g. 'zfs' or 'btrfs', etc.
  - `used_by` - which containers (by API endpoint `/1.0/containers/<name>`) are
    using this storage-pool.
  - `config` - a dictionary with some information about the storage-pool.  e.g.
    size, source (path), volume.size, etc.
  - `managed` -- Boolean that indicates whether LXD manages the pool or not.


Storage-pool Object methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following methods are available on a Storage Pool object:

  - `save` - save a modified storage pool.  This saves the `config` attribute
    in it's entirety.
  - `delete` - delete the storage pool.
  - `put` - Change the LXD storage object with a passed parameter.  The object
    is then synced back to the storage pool object.
  - `patch` - A more fine grained patch of the object.  Note that the object is
    then synced back after a successful patch.

.. note:: `raw_put` and `raw_patch` are availble (but not documented) to allow
        putting and patching without syncing the object back.


Storage Resources
-----------------

Storage Resources are accessed from the storage pool object:

.. code:: python

    resources = storage_pool.resources.get()

Resources are read-only and there are no further methods available on them.

Storage Volumes
---------------

Storage Volumes are stored in storage pools.  On the `pylxd` API they are
accessed from a storage pool object:

.. code:: Python

    storage_pool = client.storage_pools.get('pool1')
    volumes = storage_pool.volumes.all()
    named_volume = storage_pool.volumes.get('custom', 'vol1')

Methods available on `<storage_pool_object>.volumes`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following methods are accessed from the `volumes` attribute on the storage
pool object.

  - `all` - get all the volumes on the pool.
  - `get` - a get a single, type + name volume on the pool.
  - `create` - create a volume on the storage pool.

.. note:: Note that storage volumes have a tuple of `type` and `name` to uniquely
        identify them.  At present LXD recognises three types (but this may change),
        and these are `container`, `image` and `custom`.  LXD uses `container` and
        `image` for containers and images respectively.  Thus, for user applications,
        `custom` seems like the type of choice.  Please see the `LXD Storage Pools`_
        documentation for further details.

Methods available on the storage volume object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once in possession of a storage volume object from the `pylxd` API, the
following methods are available:

  - `rename` - Rename a volume.  This can also be used to migrate a volume from
    one pool to the other, as well as migrating to a different LXD instance.
  - `put` - Put an object to the LXD server using the storage volume details
    and then re-sync the object.
  - `patch` - Patch the object on the LXD server, and then re-sync the object
    back.
  - `save` - after modifying the object in place, use a PUT to push those
    changes to the LXD server.
  - `delete` - delete a storage volume object.  Note that the object is,
    therefore, stale after this action.

.. note:: `raw_put` and `raw_patch` are availble (but not documented) to allow
        putting and patching without syncing the object back.

.. links

.. _LXD Storage Pools: https://lxd.readthedocs.io/en/latest/storage/
.. _LXD REST API: https://github.com/lxc/lxd/blob/master/doc/rest-api.md
.. _LXD Storage Pools REST API: https://github.com/lxc/lxd/blob/master/doc/rest-api.md#10storage-pools
