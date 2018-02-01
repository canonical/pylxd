Storage Pools
=============

LXD supports creating and managing storage pools and storage volumes. General
keys are top-level. Driver specific keys are namespaced by driver name. Volume
keys apply to any volume created in the pool unless the value is overridden on
a per-volume basis.

`Storage Pool` objects represent the json object that is returned from
`GET /1.0/storage-pools/<name>` and then the associated methods that are then
available at the same endpoint.

Manager methods
---------------

Storage-pools can be queried through the following client manager methods:

  - `all()` - Return a list of storage pools.
  - `get()` - Get a specific storage-pool, by its name.
  - `exists()` - Return a boolean for whether a storage-pool exists by name.
  - `create()` - Create a storage-pool.  **Note the config in the create class
    method is the WHOLE json object described as `input` in the API docs.**
    e.g. the 'config' key in the API docs would actually be `config.config` as
    passed to this method.


Storage-pool attributes
-----------------------

For more information about the specifics of these attributes, please see
the `LXD documentation`_.

  - `name` - the name of the storage pool
  - `driver` - the driver (or type of storage pool). e.g. 'zfs' or 'btrfs', etc.
  - `used_by` - which containers (by API endpoint `/1.0/containers/<name>`) are
    using this storage-pool.
  - `config` - a string (json encoded) with some information about the
    storage-pool.  e.g. size, source (path), volume.size, etc.

.. _LXD documentation: https://github.com/lxc/lxd/blob/master/doc/rest-api.md#10storage-pools

Storage-pool methods
--------------------

The are no storage pool methods defined yet.
