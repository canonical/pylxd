Images
======

`Image` objects are the base for which containers are built. Many of
the methods of images are asynchronous, as they required reading and
writing large files.


Manager methods
---------------

Images can be queried through the following client manager
methods:

  - `all()` - Retrieve all images.
  - `get()` - Get a specific image, by its fingerprint.
  - `get_by_alias()` - Ger a specific image using its alias.

And create through the following methods, there's also a copy method on an
image:

  - `create(data, public=False)` - Create a new image. The first
    argument is the binary data of the image itself. If the image is public,
    set `public` to `True`.
  - `create_from_registry(registry, image, public=False, auto_update=False, copy_aliases=False, image_type=None)` -
    Copy an image from an image registry, named by alias or fingerprint.
    Needs the `image_registries` API extension; see :doc:`image-registries`.
  - `create_from_simplestreams(server, alias, public=False, auto_update=False)` -
    Create an image from simplestreams. On servers with the `image_registries`
    extension this source is deprecated: LXD maps it to an existing registry
    with the same URL and otherwise creates one only for
    `cloud-images.ubuntu.com`, `images.lxd.canonical.com` and
    `cdimage.ubuntu.com`; any other URL is rejected. A `DeprecationWarning`
    is raised there. Use `create_from_registry` instead.
  - `create_from_url(url, public=False, auto_update=False)` -
    Create an image from a url. Deprecated: servers with the `image_registries`
    extension reject client-specified URLs, so this method cannot work there
    and always raises a `DeprecationWarning`. Use `create_from_registry`.

Image attributes
----------------

For more information about the specifics of these attributes, please see
the `LXD documentation`_.

  - `aliases` - A list of aliases for this image
  - `auto_update` - Whether the image should auto-update
  - `architecture` - The target architecture for the image
  - `cached` - Whether the image is cached
  - `created_at` - The date and time the image was created
  - `expires_at` - The date and time the image expires
  - `filename` - The name of the image file
  - `fingerprint` - The image fingerprint, a sha2 hash of the image data
    itself. This unique key identifies the image.
  - `last_used_at` - The last time the image was used
  - `properties` - The configuration of image itself
  - `public` - Whether the image is public or not
  - `size` - The size of the image
  - `uploaded_at` - The date and time the image was uploaded
  - `update_source` - A dict describing where the image was downloaded from
    and is updated from: `server`, `protocol`, `certificate`, `alias` and,
    on servers with the `image_registries` extension, `image_registry`

.. _LXD documentation: https://canonical.com/lxd/docs/latest/api/#/images/image_get

Image methods
-------------

  - `export` - Export the image. Returns a file object with the contents
    of the image. *Note: Prior to pylxd 2.1.1, this method returned a
    bytestring with data; as it was not unbuffered, the API was severely
    limited.*
  - `add_alias` - Add an alias to the image.
  - `delete_alias` - Remove an alias.
  - `copy(new_client, public=None, auto_update=None, wait=False, image_registry=None, copy_aliases=False)` -
    Copy the image to another LXD client. By default the request names this
    server's URL and certificate, which servers with the `image_registries`
    extension deprecate and only accept when a matching registry already
    exists. Pass `image_registry`, the name of a registry on the destination
    that points at this server, instead. `copy_aliases` also copies the
    aliases and needs the extension on the destination.
  - `delete` - Deletes the image.

Examples
--------

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
    >>> image.save()


To create a new Image, you'll open an image file, and pass that to `create`.
If the image is to be public, `public=True`. As this is an asynchonous operation,
you may also want to `wait=True`.

.. code-block:: python

    >>> image_data = open('an_image.tar.gz', 'rb').read()
    >>> image = client.images.create(image_data, public=True, wait=True)
    >>> image.fingerprint
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'


To copy an image from an image registry, give the registry name and an alias
or a fingerprint. LXD downloads the image as an operation and the call waits
for it.

.. code-block:: python

    >>> image = client.images.create_from_registry('ubuntu', '24.04')
    >>> image.fingerprint
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'


Finally, delete an image. As this is an asynchonous operation,
you may also want to `wait=True`.

.. code-block:: python

    >>> image = client.images.get(
    ...     'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
    >>> image.delete(wait=True)
