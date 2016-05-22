=====
Usage
=====

.. currentmodule:: pylxd

Once you have :doc:`installed <installation>`, you're ready to
instanciate an API client to start interacting with the LXD daemon on
localhost:

.. code-block:: python

    >>> from pylxd.client import Client
    >>> client = Client()

This :class:`~client.Client` object exposes managers for:

- :class:`~container.Container`,
- :class:`~profile.Profile`,
- :class:`~operation.Operation`,
- :class:`~image.Image`,

Also, it exposes the HTTP API with the `api <api.html#Client.api>`_ attribute,
allowing lower-level operations.

Containers
==========

Example creating a :class:`~container.Container` with
:class:`client.containers <client.Client.Containers>`'s ``create(config,
wait=False)``
attribute, the partial of :meth:`Container.create
<container.Container.create>`:

.. code-block:: python

    >>> container = client.container.create(dict(name='testcont'))
    [<container.Container at 0x7f95d8af72b0>,]

Example getting a list of :class:`~container.Container` with
:meth:`Client.containers.all() <client.Client.Containers.all>`:

.. code-block:: python

    >>> client.container.all()
    [<container.Container at 0x7f95d8af72b0>,]

Examples
========

See more examples in the ``examples/`` directory of the repository.
