Instances
==========

`Instance` objects are the core of LXD. They are the result of
supporting the management of virtual machines. Instances can be created,
updated, and deleted. Most of the methods for operating on the
instance itself are asynchronous, but many of the methods for getting
information about the instance are synchronous.

Instead of the `instances` model, separate `containers` and `virtual_machines`
exist which only return instances of the specific type.


Manager methods
---------------

Instances can be queried through the following client manager
methods:

  - `exists(name)` - Returns `boolean` indicating if the instance exists.
  - `all()` - Retrieve all instances.
  - `get()` - Get a specific instance, by its name.
  - `create(config, wait=False, target='lxd-cluster-member')` - Create a new instance. 
    - This method requires the instance config as the first parameter.
    - The config itself is beyond the scope of this documentation. Please refer to the LXD documentation for more information. 
    - This method will also return immediately, unless `wait` is `True`.
    - Optionally, the target node can be specified for LXD clusters.


Instance attributes
--------------------

For more information about the specifics of these attributes, please see
the LXD documentation.

  - `architecture` - The instance architecture.
  - `config` - The instance config
  - `created_at` - The time the instance was created
  - `devices` - The devices for the instance
  - `ephemeral` - Whether the instance is ephemeral
  - `expanded_config` - An expanded version of the config
  - `expanded_devices` - An expanded version of devices
  - `name` - (Read only) The name of the instance. This attribute serves as the
    primary identifier of an instance
  - `description` - A description given to the instance
  - `profiles` - A list of profiles applied to the instance
  - `status` - (Read only) A string representing the status of the instance
  - `last_used_at` - (Read only) when the instance was last used
  - `location` - (Read only) the host of the instance in a cluster
  - `type` - (Read only) whether a container (default) or virtual-machine
  - `status_code` - (Read only) A LXD status code of the instance
  - `stateful` - (Read only) Whether the instance is stateful


Instance methods
-----------------

  - `rename` - Rename an instance. Because `name` is the key, it cannot be
    renamed by simply changing the name of the instance as an attribute
    and calling `save`. The new name is the first argument and, as the method
    is asynchronous, you may pass `wait=True` as well.
  - `save` - Update instance's configuration
  - `state` - Get the expanded state of the instance.
  - `start` - Start the instance
  - `stop` - Stop the instance
  - `restart` - Restart the instance
  - `freeze` - Suspend the instance
  - `unfreeze` - Resume the instance
  - `execute` - Execute a command on the instance. The first argument is
    a list, in the form of `subprocess.Popen` with each item of the command
    as a separate item in the list. Returns a tuple of `(exit_code, stdout, stderr)`.
    This method will block while the command is executed.
  - `raw_interactive_execute` - Execute a command on the instance. It will return
    an url to an interactive websocket and the execution only starts after a client connected to the websocket.
  - `migrate` - Migrate the instance. The first argument is a client
    connection to the destination server. This call is asynchronous, so
    ``wait=True`` is optional. The instance on the new client is returned.  If
    ``live=True`` is passed to the function call, then the instance is live
    migrated (see the LXD documentation for further details).
  - `publish` - Publish the instance as an image.  Note the instance must be stopped
    in order to use this method.  If `wait=True` is passed, then the image is returned.
  - `restore_snapshot` - Restore a snapshot by name.


Examples
--------

If you'd only like to fetch a single instance by its name...

.. code-block:: python

    >>> client.instances.get('my-instance')
    <instance.Instance at 0x7f95d8af72b0>


If you're looking to operate on all instances of a LXD instance, you can
get a list of all LXD instances with `all`.

.. code-block:: python

    >>> client.instances.all()
    [<instance.Instance at 0x7f95d8af72b0>,]


In order to create a new :class:`~instance.Instance`, an instance
config dictionary is needed, containing a name and the source. A create
operation is asynchronous, so the operation will take some time. If you'd
like to wait for the instance to be created before the command returns,
you'll pass `wait=True` as well.

.. code-block:: python

    >>> config = {'name': 'my-instance', 'source': {'type': 'none'}, 'type': 'container'}
    >>> instance = client.instances.create(config, wait=False)
    >>> instance
    <instance.Instance at 0x7f95d8af72b0>


If you were to use an actual local image source, you would be able to
operate on the instance: starting, stopping, freezing, deleting, etc.
You could also customize the instance's config (limits and etc). Note
that depends on having a local image with the alias `focal`. See
the next example for using a remote image.

.. code-block:: python

    >>> config = {'name': 'my-instance', 'source': {'type': 'image', 'alias': 'focal'}, 'config': {'limits.cpu': '2'}}
    >>> instance = client.instances.create(config, wait=True)
    >>> instance.start()
    >>> instance.freeze()
    >>> instance.delete()


Config line with a remote image source (daily build of the latest Ubuntu LTS)
and a single profile named `profilename`.

.. code-block:: python

    >>> config = {'name': 'my-instance', 'source': {'type': 'image', "mode": "pull", "server":
        "https://cloud-images.ubuntu.com/daily", "protocol": "simplestreams", 'alias': 'lts/amd64'},
        'profiles': ['profilename'] }


To modify instance's configuration method `
` should be called after
:class:`~instance.Instance` attributes changes.

    >>> instance = client.instances.get('my-instance')
    >>> instance.ephemeral = False
    >>> instance.devices = { 'root': { 'path': '/', 'type': 'disk', 'size': '7GB'} }
    >>> instance.save()

To get state information such as a network address.

.. code-block:: python

    >>> addresses = instance.state().network['eth0']['addresses']
    >>> addresses[0]
    {'family': 'inet', 'address': '10.251.77.182', 'netmask': '24', 'scope': 'global'}


To migrate an instance between two servers, first you need to create a client certificate in order to connect to the remote server

    openssl req -newkey rsa:2048 -nodes -keyout lxd.key -out lxd.csr
    openssl x509 -signkey lxd.key -in lxd.csr -req -days 365 -out lxd.crt

Then you need to connect to both the destination server and the source server,
the source server has to be reachable by the destination server otherwise the migration will fail due to a websocket error

.. code-block:: python

    from pylxd import Client

    client_source=Client(endpoint='https://192.168.1.104:8443',cert=('lxd.crt','lxd.key'),verify=False)
    client_destination=Client(endpoint='https://192.168.1.106:8443',cert=('lxd.crt','lxd.key'),verify=False)
    cont = client_source.instances.get('testm')
    cont.migrate(client_destination,wait=True)

This will migrate the instance from source server to destination server

To migrate a live instance, user the ``live=True`` parameter:

.. code-block:: python

    cont.migrate(client__destination, live=True, wait=True)

If you want an interactive shell in the instance, you can attach to it via a websocket.

.. code-block:: python

    >>> res = instance.raw_interactive_execute(['/bin/bash'])
    >>> res
    {
        "name": "instance-name",
        "ws": "/1.0/operations/adbaab82-afd2-450c-a67e-274726e875b1/websocket?secret=ef3dbdc103ec5c90fc6359c8e087dcaf1bc3eb46c76117289f34a8f949e08d87",
        "control": "/1.0/operations/adbaab82-afd2-450c-a67e-274726e875b1/websocket?secret=dbbc67833009339d45140671773ac55b513e78b219f9f39609247a2d10458084"
    }

You can connect to this urls from e.g. https://xtermjs.org/ .

Instance Snapshots
-------------------

Each instance carries its own manager for managing :class:`~instance.Snapshot`
functionality. It has `get`, `all`, and `create` functionality.

Snapshots are keyed by their name (and only their name, in pylxd; LXD
keys them by <instance-name>/<snapshot-name>, but the manager allows
us to use our own namespacing).

A instance object (returned by `get` or `all`) has the following methods:

  - `rename` - rename a snapshot
  - `publish` - create an image from a snapshot.  However, this may fail if the
    image from the snapshot is bigger than the logical volume that is allocated
    by lxc.  See https://github.com/canonical/lxd/issues/2201 for more details.  The solution
    is to increase the `storage.lvm_volume_size` parameter in lxc.
  - `restore` - restore the instance to this snapshot.

.. code-block:: python

    >>> snapshot = instance.snapshots.get('an-snapshot')
    >>> snapshot.created_at
    '1983-06-16T2:38:00'
    >>> snapshot.rename('backup-snapshot', wait=True)
    >>> snapshot.delete(wait=True)


To create a new snapshot, use `create` with a `name` argument. If you want
to capture the contents of RAM in the snapshot, you can use `stateful=True`.

.. note:: Your LXD requires a relatively recent version of CRIU for this.

.. code-block:: python

    >>> snapshot = instance.snapshots.create(
    ...     'my-backup', stateful=True, wait=True)
    >>> snapshot.name
    'my-backup'


Instance files
---------------

Instances also have a `files` manager for getting and putting files on the
instance.  The following methods are available on the `files` manager:

  - `put` - push a file into the instance.
  - `mk_dir` - create an empty directory on the instance.
  - `recursive_put` - recursively push a directory to the instance.
  - `get` - get a file from the instance.
  - `recursive_get` - recursively pull a directory from the instance.
  - `delete_available` - If the `file_delete` extension is available on the lxc
    host, then this method returns `True` and the `delete` method is available.
  - `delete` - delete a file on the instance.

.. note:: All file operations use `uid` and `gid` of 0 in the instance.  i.e. root.

.. code-block:: python

    >>> filedata = open('my-script').read()
    >>> instance.files.put('/tmp/my-script', filedata)
    >>> newfiledata = instance.files.get('/tmp/my-script2')
    >>> open('my-script2', 'wb').write(newfiledata)
