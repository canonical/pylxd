=====
Usage
=====

.. currentmodule:: pylxd

Once you have :doc:`installed <installation>`, you're ready to
instanciate an API client to start interacting with the LXD daemon on
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

Example creating a :class:`~container.Container` with
:class:`client.containers <client.Client.Containers>`'s ``create(config,
wait=False)``
attribute, the partial of :meth:`Container.create
<container.Container.create>`:

.. code-block:: python

    >>> container = client.containers.create(dict(name='testcont'))
    [<container.Container at 0x7f95d8af72b0>,]

Example getting a list of :class:`~container.Container` with
:meth:`Client.containers.all() <client.Client.Containers.all>`:

.. code-block:: python

    >>> client.containers.all()
    [<container.Container at 0x7f95d8af72b0>,]

Examples
========

See more examples in the ``examples/`` directory of the repository.
