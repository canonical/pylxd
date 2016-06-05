=====
Usage
=====

.. currentmodule:: pylxd

Client
======

Once you have :doc:`installed <installation>`, you're ready to
instantiate an API client to start interacting with the LXD daemon on
localhost:

.. code-block:: python

    >>> from pylxd import Client
    >>> client = Client()

If your LXD instance is listening on HTTPS, you can pass a two part tuple
of (cert, key) as the `cert` argument.

.. code-block:: python

    >>> from pylxd import Client
    >>> client = Client(
    ...     endpoint='http://10.0.0.1:8443',
    ...     cert=('/path/to/client.crt', '/path/to/client.key'))

Note: in the case where the certificate is self signed (LXD default),
you may need to pass `verify=False`.

Client Managers
---------------

:class:`~client.Client` exposes an object manager protocol for
:class:`~container.Container`, :class:`~image.Image`, and
:class:`~profile.Profile`. These managers are `containers`, `images`,
and `profiles` attributes on the Client itself, and contain three
special methods.

- `create` creates new object. The arguments required differ based
  on the object that is being created.
- `get` will get a single object by its key. Each object is keyed by its
  own property.
- `all` returns a list of all the objects. The caveat here is that
  the object is "incomplete", i.e. it doesn't have all its properties
  populated yet. Each object will require a call to `fetch` before
  it can be modified/saved.


Containers
==========

If you'd only like to fetch a single container by its name...

.. code-block:: python

    >>> client.containers.get('my-container')
    <container.Container at 0x7f95d8af72b0>


If you're looking to operate on all containers of a LXD instance, you can
get a list of all LXD containers with `all`.

.. code-block:: python

    >>> client.containers.all()
    [<container.Container at 0x7f95d8af72b0>,]


See the above caveat about `all`. For example:
The caveat with `all` is that you won't have fully fetched objects. You'll
have an impartial object, so you must call `fetch` on the Container before
operating on it.

    >>> container = client.containers.all()[0]
    >>> container.architecture
    AttributeError: ...
    >>> container.fetch()
    >>> container.architecture
    'x86_64'


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

    >>> container.start()
    >>> container.freeze()
    >>> container.delete()


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


Images
======

:class:`~image.Image` operations follow the same protocol from the client`s
`images` manager (i.e. `get`, `all`, and `create`). Images are keyed on
a sha-1 fingerprint of the image itself. To get an image...

.. code-block:: python

    >>> image = client.images.get(
    ...     'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
    >>> image
    <image.Image at 0x7f95d8af72b0>


Once you have an image, you can operate on it as before:

.. code-block:: python

    >>> image.public
    False
    >>> image.public = True
    >>> image.update()


To create a new Image, you'll open an image file, and pass that to `create`.
If the image is to be public, `public=True`. As this is an asynchonous operation,
you may also want to `wait=True`.

.. code-block:: python

    >>> image_data = open('an_image.tar.gz').read()
    >>> image = client.images.create(image_data, public=True, wait=True)
    >>> image.fingerprint
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'


Profiles
========

:class:`~profile.Profile` operations follow the same manager-style as
Containers and Images. Profiles are keyed on a unique name.

.. code-block:: python

    >>> profile = client.profiles.get('my-profile')
    >>> profile
    <profile.Profile at 0x7f95d8af72b0>


The profile can then be modified and saved.

    >>> profile.config = profile.config.update({'security.nesting': 'true'})
    >>> profile.update()


To create a new profile, use `create` with a name, and optional `config`
and `devices` config dictionaries.

    >>> profile = client.profiles.create(
    ...     'an-profile', config={'security.nesting': 'true'},
    ...     devices={'root': {'path': '/', 'size': '10GB', 'type': 'disk'}})


Events
======

LXD provides an `/events` endpoint that is upgraded to a streaming websocket
for getting LXD events in real-time. The :class:`~pylxd.Client`'s `events`
method will return a websocket client that can interact with the
web socket messages.

.. code-block:: python

    >>> ws_client = client.events()
    >>> ws_client.connect()
    >>> ws_client.run()

A default client class is provided, which will block indefinitely, and
collect all json messages in a `messages` attribute. An optional 
`websocket_client` parameter can be provided when more functionality is
needed. The `ws4py` library is used to establish the connection; please
see the `ws4py` documentation for more information.
