.. py:currentmodule:: pylxd.models

Network ACLs
========

:class:`NetworkACL` objects show the current network ACLs available to LXD. Creation
and / or modification of network ACLs is possible only if 'network_acl' LXD API
extension is present.


Manager methods
---------------

Network ACLs can be queried through the following client manager
methods:


  - :func:`~NetworkACL.all` - Retrieve all networks.
  - :func:`~NetworkACL.exists` - See if a network ACL with a name exists.
    Returns `bool`.
  - :func:`~NetworkACL.get` - Get a specific network ACL, by its name.
  - :func:`~NetworkACL.create` - Create a new network ACL.
    The name of the network ACL is required. `description`, `egress`, `ingress` and `config`
    are optional and the scope of their contents is documented in the LXD
    documentation.


Network ACL attributes
------------------

  - :attr:`~NetworkACL.name` - The name of the network ACL.
  - :attr:`~NetworkACL.description` - The description of the network ACL.
  - :attr:`~NetworkACL.egress` - The egress of the network ACL.
  - :attr:`~NetworkACL.ingress` - The ingress of the network ACL.
  - :attr:`~NetworkACL.used_by` - A list of containers using this network ACL.
  - :attr:`~NetworkACL.config` - The configuration associated with the network ACL.


Network ACL methods
---------------

  - :func:`~NetworkACL.rename` - Rename the network ACL.
  - :func:`~NetworkACL.save` - Save the network ACL. This uses the PUT HTTP method and
    not the PATCH.
  - :func:`~NetworkACL.delete` - Deletes the network ACL.

.. py:currentmodule:: pylxd.models

Examples
--------

:class:`NetworkACL` operations follow the same manager-style as other
classes. Network ACLs are keyed on a unique name.

.. code-block:: python

    >>> client.network_acls.exists('allow-external-ingress')
    True

    >>> acl = client.network_acls.get('allow-external-ingress')
    >>> acl
    NetworkACL(config={}, description="Allowing external source for ingress", egress=[], ingress=[{"action": "allow", "description": "Allow external sources", "source": "@external", "state": "enabled"}], name="allow-external-ingress")

    >>> print(acl)
    {
      "name": "allow-external-ingress",
      "description": "Allowing external source for ingress",
      "egress": [],
      "ingress": [
        {
          "action": "allow",
          "source": "@external",
          "description": "Allow external sources",
          "state": "enabled"
        }
      ],
      "config": {},
      "used_by": []
    }

The network ACL can then be modified and saved.

    >>> acl.ingress.append({"action":"allow","state":"enabled"})
    >>> acl.save()

Or deleted

    >>> acl.delete()

To create a new network ACL, use :func:`~NetworkACL.create` with a name, and optional
arguments: `description` and `egress` and `ingress` and `config`.

    >>> acl = client.network_acls.create(name="allow-external-ingress", description="Allowing external source for ingress", ingress=[{"action":"allow","description":"Allow external sources","source":"@external","state":"enabled"}])

