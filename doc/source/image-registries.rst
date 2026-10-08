Image Registries
================

LXD image registries are named image sources kept on the server. Instead of
telling LXD a server URL, protocol and certificate every time an image is
copied or an instance is created, the source is a registry name. Registries
need the `image_registries` API extension.

Image Registry objects
----------------------

:py:class:`~pylxd.models.image_registry.ImageRegistry` objects represent the
json object that is returned from `GET /1.0/image-registries/<name>` and the
methods that are available at the same endpoint. For example:

.. code:: python

    client = pylxd.Client()
    registry = client.image_registries.get('ubuntu')
    images = registry.images()

.. note:: For more details of the LXD documentation concerning image
        registries please see the `LXD Image Registries`_ documentation and
        the `LXD Image Registries REST API`_ documentation. Please see the
        pylxd API documentation for more information on image registry
        methods and parameters. The following is a summary.

Built-in registries
^^^^^^^^^^^^^^^^^^^

Every server has five built-in registries: `images`, `ubuntu`,
`ubuntu-daily`, `ubuntu-minimal` and `ubuntu-minimal-daily`. They are public,
use the `simplestreams` protocol and cannot be changed, renamed or deleted:
LXD answers `400` and pylxd raises
:py:class:`~pylxd.exceptions.LXDAPIException`. The names `builtin`, `allow`
and `block` are reserved and cannot be used for a registry.

Protocols
^^^^^^^^^

LXD infers the protocol from the registry config, so `create()` takes no
protocol argument:

  - `simplestreams` - `config` has `url`, the HTTPS address of a simplestreams
    server.
  - `lxd` - `config` has `cluster`, the name of a cluster link to the other
    LXD cluster, and `source_project`, the project on that cluster to take
    images from. See :doc:`clustering` for how to create a cluster link. LXD
    refuses to delete a link while a registry uses it.

`user.*` keys are free-form and stored as given.

Image Registry Manager methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Image registries can be queried through the following client manager
methods:

  - `all()` - Return a list of image registries. Only the name is populated
    until another attribute is read.
  - `get(name)` - Get a specific image registry by name.
  - `exists(name)` - Return a boolean for whether an image registry exists.
  - `create(name, config, description='', wait=True)` - Create an image
    registry.

Image Registry Object attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For more information about the specifics of these attributes, please see
the `LXD Image Registries REST API`_ documentation.

  - `name` - the name of the registry
  - `description` - a description of the registry
  - `protocol` - `simplestreams` or `lxd`, inferred by LXD from `config`
  - `public` - whether images can be fetched without authentication
  - `builtin` - whether the registry ships with LXD
  - `config` - `url`, or `cluster` and `source_project`, plus `user.*` keys

Only `description` and `config` can be changed.

Image Registry Object methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following methods are available on an image registry object:

  - `images()` - list the images the registry provides, as dictionaries in
    the form LXD returns them. They describe images on the upstream source,
    not images on this server.
  - `rename(new_name)` - rename the registry.
  - `save()` - save a modified registry. This sends `description` and
    `config` in their entirety.
  - `put(dict)`, `patch(dict)` - update the registry and sync the object
    back.
  - `delete()` - delete the registry. LXD refuses while local images still
    reference it.

Every change to a registry is an asynchronous operation on the server. The
methods above wait for it by default; pass `wait=False` to return as soon as
LXD has accepted the request.

Examples
^^^^^^^^

.. code:: python

    # A simplestreams registry
    mirror = client.image_registries.create(
        'mirror', {'url': 'https://images.example.com'})

    # An lxd registry over an existing cluster link
    remote = client.image_registries.create(
        'other-cluster',
        {'cluster': 'other-cluster', 'source_project': 'default'})

    for image in remote.images():
        print(image['fingerprint'], [a['name'] for a in image['aliases']])

    mirror.description = 'Local mirror'
    mirror.save()
    mirror.delete()

Project restrictions
^^^^^^^^^^^^^^^^^^^^

The `restricted.registries` project configuration key controls which
registries a project may use: `builtin` (the default), `allow`, `block`, or
a comma-separated list of registry names.

.. links

.. _LXD Image Registries: https://canonical.com/lxd/docs/latest/reference/image_registries/
.. _LXD Image Registries REST API: https://canonical.com/lxd/docs/latest/api/
