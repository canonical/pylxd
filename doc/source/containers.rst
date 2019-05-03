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

  - `exists(name)` - Returns `boolean` indicating if the container exists.
  - `all()` - Retrieve all containers.
  - `get()` - Get a specific container, by its name.
  - `create(config, wait=False)` - Create a new container. This method
    requires the container config as the first parameter.
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
  - `name` - (Read only) The name of the container. This attribute serves as the
    primary identifier of a container
  - `description` - A description given to the container
  - `profiles` - A list of profiles applied to the container
  - `status` - (Read only) A string representing the status of the container
  - `last_used_at` - (Read only) when the container was last used
  - `status_code` - (Read only) A LXD status code of the container
  - `stateful` - (Read only) Whether the container is stateful


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
    as a separate item in the list. Returns a tuple of `(exit_code, stdout, stderr)`.
    This method will block while the command is executed.
  - `raw_interactive_execute` - Execute a command on the container. It will return
    an url to an interactive websocket and the execution only starts after a client connected to the websocket.
  - `migrate` - Migrate the container. The first argument is a client
    connection to the destination server. This call is asynchronous, so
    ``wait=True`` is optional. The container on the new client is returned.  If
    ``live=True`` is passed to the function call, then the container is live
    migrated (see the LXD documentation for further details).
  - `publish` - Publish the container as an image.  Note the container must be stopped
    in order to use this method.  If `wait=True` is passed, then the image is returned.
  - `restore_snapshot` - Restore a snapshot by name.


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

    >>> config = {'name': 'my-container', 'source': {'type': 'image', 'alias': 'ubuntu/trusty'}}
    >>> container = client.containers.create(config, wait=True)
    >>> container.start()
    >>> container.freeze()
    >>> container.delete()
   
   
Config line with a specific image source and a profile.

.. code-block:: python

    >>> config = {'name': 'my-container', 'source': {'type': 'image', "mode": "pull", "server":
        "https://cloud-images.ubuntu.com/daily", "protocol": "simplestreams", 'alias': 'bionic/amd64'},
	'profiles': ['profilename'] }


To modify container's configuration method `save` should be called after
:class:`~container.Container` attributes changes.

    >>> container = client.containers.get('my-container')
    >>> container.ephemeral = False
    >>> container.devices = { 'root': { 'path': '/', 'type': 'disk', 'size': '7GB'} }
    >>> container.save
    
To get state information such as a network address.

.. code-block:: python

    >>> addresses = container.state().network['eth0']['addresses']
    >>> addresses[0]
    {'family': 'inet', 'address': '10.251.77.182', 'netmask': '24', 'scope': 'global'}


To migrate a container between two servers, first you need to create a client certificate in order to connect to the remote server

    openssl req -newkey rsa:2048 -nodes -keyout lxd.key -out lxd.csr
    openssl x509 -signkey lxd.key -in lxd.csr -req -days 365 -out lxd.crt

Then you need to connect to both the destination server and the source server,
the source server has to be reachable by the destination server otherwise the migration will fail due to a websocket error

.. code-block:: python

    from pylxd import Client

    client_source=Client(endpoint='https://192.168.1.104:8443',cert=('lxd.crt','lxd.key'),verify=False)
    client_destination=Client(endpoint='https://192.168.1.106:8443',cert=('lxd.crt','lxd.key'),verify=False)
    cont = client_source.containers.get('testm')
    cont.migrate(client_destination,wait=True)

This will migrate the container from source server to destination server

To migrate a live container, user the ``live=True`` parameter:

..code-block:: python

    cont.migrate(client__destination, live=True, wait=True)

If you want an interactive shell in the container, you can attach to it via a websocket.

.. code-block:: python

    >>> res = container.raw_interactive_execute(['/bin/bash'])
    >>> res
    {
        "name": "container-name",
        "ws": "/1.0/operations/adbaab82-afd2-450c-a67e-274726e875b1/websocket?secret=ef3dbdc103ec5c90fc6359c8e087dcaf1bc3eb46c76117289f34a8f949e08d87",
        "control": "/1.0/operations/adbaab82-afd2-450c-a67e-274726e875b1/websocket?secret=dbbc67833009339d45140671773ac55b513e78b219f9f39609247a2d10458084"
    }

You can connect to this urls from e.g. https://xtermjs.org/ .

Container Snapshots
-------------------

Each container carries its own manager for managing :class:`~container.Snapshot`
functionality. It has `get`, `all`, and `create` functionality.

Snapshots are keyed by their name (and only their name, in pylxd; LXD
keys them by <container-name>/<snapshot-name>, but the manager allows
us to use our own namespacing).

A container object (returned by `get` or `all`) has the following methods:

  - `rename` - rename a snapshot
  - `publish` - create an image from a snapshot.  However, this may fail if the
    image from the snapshot is bigger than the logical volume that is allocated
    by lxc.  See https://github.com/lxc/lxd/issues/2201 for more details.  The solution
    is to increase the `storage.lvm_volume_size` parameter in lxc.
  - `restore` - restore the container to this snapshot.

.. code-block:: python

    >>> snapshot = container.snapshots.get('an-snapshot')
    >>> snapshot.created_at
    '1983-06-16T2:38:00'
    >>> snapshot.rename('backup-snapshot', wait=True)
    >>> snapshot.delete(wait=True)


To create a new snapshot, use `create` with a `name` argument. If you want
to capture the contents of RAM in the snapshot, you can use `stateful=True`.

.. note:: Your LXD requires a relatively recent version of CRIU for this.

.. code-block:: python

    >>> snapshot = container.snapshots.create(
    ...     'my-backup', stateful=True, wait=True)
    >>> snapshot.name
    'my-backup'


Container files
---------------

Containers also have a `files` manager for getting and putting files on the
container.  The following methods are available on the `files` manager:

  - `put` - push a file into the container.
  - `get` - get a file from the container.
  - `delete_available` - If the `file_delete` extension is available on the lxc
    host, then this method returns `True` and the `delete` method is available.
  - `delete` - delete a file on the container.

.. note:: All file operations use `uid` and `gid` of 0 in the container.  i.e. root.

.. code-block:: python

    >>> filedata = open('my-script').read()
    >>> container.files.put('/tmp/my-script', filedata)
    >>> newfiledata = container.files.get('/tmp/my-script2')
    >>> open('my-script2', 'wb').write(newfiledata)
