=====
Usage
=====

.. currentmodule:: pylxd

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

This :class:`~client.Client` object exposes managers for:

- :class:`~container.Container`,
- :class:`~profile.Profile`,
- :class:`~operation.Operation`,
- :class:`~image.Image`,


Containers
==========

In order to create a new container, a container config dictionary is needed,
containing a name and the source. A create operation is asynchronous, so
the operation will take some time. If you'd like to wait for the container
to be created before the command returns, you'll pass `wait=True` as well.

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


If you're looking to operate on all containers of a LXD instance, you can
get a list of all LXD containers with `all`.

.. code-block:: python

    >>> client.containers.all()
    [<container.Container at 0x7f95d8af72b0>,]


...or if you'd only like to fetch a single container by its name...

.. code-block:: python

    >>> client.containers.get('my-container')
    <container.Container at 0x7f95d8af72b0>
