Containers
==========

`Container` objects are the core of LXD. Containers can be created,
updated, and deleted. Most of the methods for operating on the
container itself are asynchronous, but many of the methods for getting
information about the container are synchronous.


Manager methods
---------------

Containers can be queried through the following client manager
methods:

  - `all()` - Retrieve all containers.
  - `get()` - Get a specific container, by its name.
  - `create(wait=False)` - Create a new container. This method requires
    a first argument that is the container name, followed by a config.
    The config itself is beyond the scope of this documentation. Please
    refer to the LXD documentation for more information. This method
    will also return immediately, unless `wait` is `True`.


Container attributes
--------------------

For more information about the specifics of these attributes, please see
the LXD documentation.

  - `architecture` - The container architecture.
  - `config` - The container config
  - `created_at` - The time the container was created
  - `devices` - The devices for the container
  - `ephemeral` - Whether the container is ephemeral
  - `expanded_config` - An expanded version of the config
  - `expanded_devices` - An expanded version of devices
  - `name` - The name of the container. This attribute serves as the
    primary identifier of a container.
  - `profiles` - A list of profiles applied to the container
  - `status` - A string representing the status of the container
  - `status_code` - A LXD status code of the container
  - `stateful` - Whether the container is stateful


Container methods
-----------------

  - `rename` - Rename a container. Because `name` is the key, it cannot be
    renamed by simply changing the name of the container as an attribute
    and calling `save`. The new name is the first argument and, as the method
    is asynchronous, you may pass `wait=True` as well.
  - `save` - Update container's configuration
  - `state` - Get the expanded state of the container.
  - `start` - Start the container
  - `stop` - Stop the container
  - `restart` - Restart the container
  - `freeze` - Suspend the container
  - `unfreeze` - Resume the container
  - `execute` - Execute a command on the container. The first argument is
    a list, in the form of `subprocess.Popen` with each item of the command
    as a separate item in the list. Returns a two part tuple of
    `(stdout, stderr)`. This method will block while the command is executed.
  - `migrate` - Migrate the container. The first argument is a client
    connection to the destination server. This call is asynchronous, so
    `wait=True` is optional. The container on the new client is returned.



Examples
--------

If you'd only like to fetch a single container by its name...

.. code-block:: python

    >>> client.containers.get('my-container')
    <container.Container at 0x7f95d8af72b0>


If you're looking to operate on all containers of a LXD instance, you can
get a list of all LXD containers with `all`.

.. code-block:: python

    >>> client.containers.all()
    [<container.Container at 0x7f95d8af72b0>,]


In order to create a new :class:`~container.Container`, a container
config dictionary is needed, containing a name and the source. A create
operation is asynchronous, so the operation will take some time. If you'd
like to wait for the container to be created before the command returns,
you'll pass `wait=True` as well.

.. code-block:: python

    >>> config = {'name': 'my-container', 'source': {'type': 'none'}}
    >>> container = client.containers.create(config, wait=False)
    >>> container
    <container.Container at 0x7f95d8af72b0>


If you were to use an actual image source, you would be able to operate
on the container, starting, stopping, snapshotting, and deleting the
container.

.. code-block:: python

    >>> config = {'name': 'my-container', 'source': {'type': 'image', 'image': 'ubuntu/trusty'}}
    >>> container = client.containers.create(config, wait=True)
    >>> container.start()
    >>> container.freeze()
    >>> container.delete()


To modify container's configuration method `save` should be called after
:class:`~container.Container` attributes changes.

    >>> container = client.containers.get('my-container')
    >>> container.ephemeral = False
    >>> container.devices = { 'root': { 'path': '/', 'type': 'disk', 'size': '7GB'} }
    >>> container.save


Container Snapshots
-------------------

Each container carries its own manager for managing :class:`~container.Snapshot`
functionality. It has `get`, `all`, and `create` functionality.

Snapshots are keyed by their name (and only their name, in pylxd; LXD
keys them by <container-name>/<snapshot-name>, but the manager allows
us to use our own namespacing).

.. code-block:: python
    >>> snapshot = container.snapshots.get('an-snapshot')
    >>> snapshot.created_at
    '1983-06-16T2:38:00'
    >>> snapshot.rename('backup-snapshot', wait=True)
    >>> snapshot.delete(wait=True)


To create a new snapshot, use `create` with a `name` argument. If you want
to capture the contents of RAM in the snapshot, you can use `stateful=True`.
**Note: Your LXD requires a relatively recent version of CRIU for this.**

.. code-block:: python
    >>> snapshot = container.snapshots.create(
    ...     'my-backup', stateful=True, wait=True)
    >>> snapshot.name
    'my-backup'


Container files
---------------

Containers also have a `files` manager for getting and putting files on the
container.

.. code-block:: python
    >>> filedata = open('my-script').read()
    >>> container.files.put('/tmp/my-script', filedata)
    >>> newfiledata = container.files.get('/tmp/my-script2')
    >>> open('my-script2', 'wb').write(newfiledata)
