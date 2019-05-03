===============
Getting started
===============

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

Querying LXD
------------

LXD exposes a number of objects via its REST API that are used to orchestrate
containers. Those objects are all accessed via manager attributes on the client
itself. This includes `certificates`, `containers`, `images`, `networks`,
`operations`, and `profiles`. Each manager has methods for querying the
LXD instance. For example, to get all containers in a LXD instance

.. code-block:: python

    >>> client.containers.all()
    [<container.Container at 0x7f95d8af72b0>,]


For specific manager methods, please see the documentation for each object.


pylxd Objects
-------------

Each LXD object has an analagous pylxd object. Returning to the previous
`client.containers.all` example, a `Container` object is manipulated as
such:

.. code-block:: python

    >>> container = client.containers.all()[0]
    >>> container.name
    'lxd-container'

Each pylxd object has a lifecycle which includes support for
transactional changes. This lifecycle includes the following
methods and attributes:

  - `sync()` - Synchronize the object with the server. This method is
    called implicitly when accessing attributes that have not yet been
    populated, but may also be called explicitly. Why would attributes
    not yet be populated? When retrieving objects via `all`, LXD's
    API does not return a full representation.
  - `dirty` - After setting attributes on the object, the object is
    considered "dirty".
  - `rollback()` - Discard all local changes to the object, opting
    for a representation taken from the server.
  - `save()` - Save the object, writing changes to the server.


Returning again to the `Container` example

.. code-block:: python

    >>> container.config
    { 'security.privileged': True }
    >>> container.config.update({'security.nesting': True})
    >>> container.dirty
    True
    >>> container.rollback()
    >>> container.dirty
    False
    >>> container.config
    { 'security.privileged': True }
    >>> container.config = {'security.privileged': False}
    >>> container.save(wait=True)  # The object is now saved back to LXD


A note about asynchronous operations
------------------------------------

Some changes to LXD will return immediately, but actually occur in the
background after the http response returns. All operations that happen
this way will also take an optional `wait` parameter that, when `True`,
will not return until the operation is completed.

UserWarning: Attempted to set unknown attribute "x" on instance of "y"
----------------------------------------------------------------------

The LXD server changes frequently, particularly if it is snap installed.  In
this case it is possible that the LXD server may send back objects with
attributes that this version of pylxd is not aware of, and in that situation,
the pylxd library issues the warning above.

The default behaviour is that *one* warning is issued for each unknown
attribute on *each* object class that it unknown.  Further warnings are then
surpressed.  The environment variable ``PYLXD_WARNINGS`` can be set to control
the warnings further:

  - if set to ``none`` then *all* warnings are surpressed all the time.
  - if set to ``always`` then warnings are always issued for each instance returned from the server.
