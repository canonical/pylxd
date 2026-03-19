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

import os
import warnings
from urllib import parse

from pylxd import exceptions

# Global used to record which warnings have been issues already for unknown
# attributes.
_seen_attribute_warnings = set()


class Operation:
    """An LXD operation.

    If the LXD server sends attributes that this version of pylxd is unaware of
    then a warning is printed.  By default the warning is issued ONCE and then
    supressed for every subsequent attempted setting.  The warnings can be
    completely suppressed by setting the environment variable PYLXD_WARNINGS to
    'none', or always displayed by setting the PYLXD_WARNINGS variable to
    'always'.
    """

    __slots__ = [
        "_client",
        "class",
        "created_at",
        "description",
        "err",
        "id",
        "location",
        "may_cancel",
        "metadata",
        "resources",
        "status",
        "status_code",
        "updated_at",
    ]

    @classmethod
    def wait_for_operation(cls, client, operation_id):
        """Get an operation and wait for it to complete."""
        operation = cls.get(client, operation_id)
        operation.wait()
        return cls.get(client, operation.id)

    @classmethod
    def extract_operation_id(cls, s):
        return os.path.split(parse.urlparse(s).path)[-1]

    @classmethod
    def get(cls, client, operation_id):
        """Get an operation."""
        operation_id = cls.extract_operation_id(operation_id)
        response = client.api.operations[operation_id].get()
        return cls(_client=client, **response.json()["metadata"])

    def _set_attributes(self, attributes):
        """Set attributes on self, warning about unknown ones per PYLXD_WARNINGS."""
        for key, value in attributes.items():
            try:
                setattr(self, key, value)
            except AttributeError:
                env = os.environ.get("PYLXD_WARNINGS", "").lower()
                if env != "always" and key in _seen_attribute_warnings:
                    continue
                _seen_attribute_warnings.add(key)
                if env == "none":
                    continue
                warnings.warn(
                    f'Attempted to set unknown attribute "{key}" '
                    f'on instance of "{self.__class__.__name__}"'
                )

    def __init__(self, **kwargs):
        super().__init__()
        self._set_attributes(kwargs)

    def wait(self):
        """Wait for the operation to complete.

        Returns True if the /wait response included an operation object that
        was applied to self, or False if the response contained no metadata.
        Raises LXDAPIException on operation failure.
        """
        response = self._client.api.operations[self.id].wait.get()

        try:
            body = response.json()
            metadata = body["metadata"]

            # If metadata is absent/null but a top-level error is present
            # (e.g. {"type": "async", "error": "...", "metadata": null}),
            # treat it as a failure.
            if not metadata and body.get("error"):
                raise exceptions.LXDAPIException(response)

            if metadata:
                # Failure can be indicated by status string or status_code.
                if metadata.get("status") == "Failure" or (
                    metadata.get("status_code") is not None
                    and not (200 <= metadata["status_code"] < 300)
                ):
                    raise exceptions.LXDAPIException(response)

                # Update self with the final state so callers don't need
                # a second GET (which could race with LXD cleaning up the operation).
                self._set_attributes(metadata)
                return True
        except KeyError:
            # /wait response does not contain an operation object
            pass

        return False
