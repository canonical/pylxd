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
  - `create(data, public=False, wait=False)` - Create a new image. The first
    argument is the binary data of the image itself. If the image is public,
    set `public` to `True`.


Image attributes
----------------

For more information about the specifics of these attributes, please see
the LXD documentation.

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


Image methods
-------------

  - `export` - Export the image. Returns binary data that is the
    image itself.


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
    >>> image.update()


To create a new Image, you'll open an image file, and pass that to `create`.
If the image is to be public, `public=True`. As this is an asynchonous operation,
you may also want to `wait=True`.

.. code-block:: python

    >>> image_data = open('an_image.tar.gz').read()
    >>> image = client.images.create(image_data, public=True, wait=True)
    >>> image.fingerprint
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
