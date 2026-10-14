# Copyright (c) 2016 Canonical Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from pylxd.models import _model as model


class ImageRegistry(model.Model):
    """An LXD image registry.

    This corresponds to the LXD endpoint at /1.0/image-registries. Every
    mutation is an asynchronous operation on the server, so the methods below
    wait for it by default; pass ``wait=False`` to return as soon as LXD has
    accepted the request.

    api_extension: 'image_registries'
    """

    name = model.Attribute(readonly=True)
    description = model.Attribute()
    protocol = model.Attribute(readonly=True)
    public = model.Attribute(readonly=True)
    builtin = model.Attribute(readonly=True)
    config = model.Attribute()

    def __eq__(self, other):
        if not isinstance(other, ImageRegistry):
            return NotImplemented
        return self.name == other.name

    __hash__ = None  # type: ignore  # unhashable, consistent with defining __eq__

    @classmethod
    def get(cls, client, name):
        """Get an image registry by name.

        Implements GET /1.0/image-registries/<name>.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :param name: name of the image registry
        :type name: str
        :returns: the image registry
        :rtype: :class:`ImageRegistry`
        :raises: :class:`pylxd.exceptions.LXDAPIExtensionNotAvailable` if the
            server lacks the ``image_registries`` extension
        :raises: :class:`pylxd.exceptions.NotFound` if the registry does not
            exist
        """
        client.assert_has_api_extension("image_registries")
        response = client.api.image_registries[name].get()
        return cls(client, **response.json()["metadata"])

    @classmethod
    def all(cls, client):
        """Get all image registries.

        Implements GET /1.0/image-registries. The returned objects are sparse
        and fetch the rest of their attributes on first access.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :returns: the image registries
        :rtype: list[:class:`ImageRegistry`]
        :raises: :class:`pylxd.exceptions.LXDAPIExtensionNotAvailable` if the
            server lacks the ``image_registries`` extension
        """
        client.assert_has_api_extension("image_registries")
        response = client.api.image_registries.get()
        # A nil slice in LXD: null, not [], when the caller can see no registry.
        urls = response.json()["metadata"] or []
        return [cls(client, name=url.split("/")[-1]) for url in urls]

    @classmethod
    def exists(cls, client, name):
        """Determine whether an image registry exists.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :param name: name of the image registry
        :type name: str
        :returns: ``True`` if the registry exists
        :rtype: bool
        """
        try:
            cls.get(client, name)
            return True
        except cls.NotFound:
            return False

    @classmethod
    def create(cls, client, name, config, description="", wait=True):
        """Create an image registry.

        Implements POST /1.0/image-registries. LXD infers the protocol from
        ``config``: ``{"url": ...}`` makes a ``simplestreams`` registry and
        ``{"cluster": ..., "source_project": ...}`` makes an ``lxd`` registry
        over that cluster link.

        :param client: client instance
        :type client: :class:`~pylxd.client.Client`
        :param name: name of the image registry
        :type name: str
        :param config: registry configuration
        :type config: dict
        :param description: description of the registry
        :type description: str
        :param wait: whether to wait for the operation to complete. If
            ``False``, the returned object contains only its name.
        :type wait: bool
        :returns: the new image registry
        :rtype: :class:`ImageRegistry`
        :raises: :class:`pylxd.exceptions.LXDAPIExtensionNotAvailable` if the
            server lacks the ``image_registries`` extension
        :raises: :class:`pylxd.exceptions.LXDAPIException` if LXD rejects
            the request, for example for a reserved name
        """
        client.assert_has_api_extension("image_registries")
        response = client.api.image_registries.post(
            json={"name": name, "description": description, "config": config}
        )
        cls._handle_async_response_for_client(client, response, wait)
        if wait:
            return cls.get(client, name)
        return cls(client, name=name)

    @property
    def api(self):
        self.client.assert_has_api_extension("image_registries")
        return self.client.api.image_registries[self.name]

    def images(self):
        """Get the images the registry provides.

        Implements GET /1.0/image-registries/<name>/images. The images live on
        the upstream source, not on this server, so they are returned as
        plain dictionaries in the form LXD returns them.

        :returns: the images available from the registry
        :rtype: list[dict]
        """
        return self.api.images.get().json()["metadata"] or []

    def rename(self, new_name, wait=True):
        """Rename the image registry.

        Implements POST /1.0/image-registries/<name>.

        :param new_name: the new name
        :type new_name: str
        :param wait: whether to wait for the operation to complete
        :type wait: bool
        :raises: :class:`pylxd.exceptions.LXDAPIException` if LXD rejects
            the request, for example for a built-in registry
        """
        response = self.api.post(json={"name": new_name})
        self._handle_async_response(response, wait)
        self.name = new_name

    def save(self, wait=True):
        """Save the image registry using PUT.

        Implements PUT /1.0/image-registries/<name>. The fields sent are
        ``description`` and ``config``, replaced in their entirety.

        :param wait: whether to wait for the operation to complete
        :type wait: bool
        :raises: :class:`pylxd.exceptions.LXDAPIException` if LXD rejects
            the request, for example for a built-in registry
        """
        super().save(wait=wait)

    def delete(self, wait=True):
        """Delete the image registry.

        Implements DELETE /1.0/image-registries/<name>. LXD refuses while
        local images still reference the registry.

        :param wait: whether to wait for the operation to complete
        :type wait: bool
        :raises: :class:`pylxd.exceptions.LXDAPIException` if LXD rejects
            the request, for example for a built-in registry
        """
        super().delete(wait=wait)

    def put(self, put_object, wait=True):
        """Put the image registry and re-sync it.

        Implements PUT /1.0/image-registries/<name>. The object is synced
        back once the operation has finished; with ``wait=False`` it is left
        as it was, so call :meth:`sync` to refresh it later.

        :param put_object: the ``description`` and ``config`` to send
        :type put_object: dict
        :param wait: whether to wait for the operation to complete
        :type wait: bool
        :raises: :class:`pylxd.exceptions.LXDAPIException` if LXD rejects
            the request
        """
        self.raw_put(put_object, wait)
        if wait:
            self.sync(rollback=True)

    def patch(self, patch_object, wait=True):
        """Patch the image registry and re-sync it.

        Implements PATCH /1.0/image-registries/<name>. The object is synced
        back once the operation has finished; with ``wait=False`` it is left
        as it was, so call :meth:`sync` to refresh it later.

        :param patch_object: the fields to change
        :type patch_object: dict
        :param wait: whether to wait for the operation to complete
        :type wait: bool
        :raises: :class:`pylxd.exceptions.LXDAPIException` if LXD rejects
            the request
        """
        self.raw_patch(patch_object, wait)
        if wait:
            self.sync(rollback=True)
