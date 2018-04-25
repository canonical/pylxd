Networks
========

`Network` objects show the current networks available to lxd.


Manager methods
---------------

Networks can be queried through the following client manager
methods:

  - `all()` - Retrieve all networks.
  - `exists()` - See if a profile with a name exists.  Returns `boolean`.
  - `get()` - Get a specific network, by its name.
  - `create(name, description, type_, config)` - Create a new network.
    The name of the network is required. `description`, `type_` and `config`
    are optional and the scope of their contents is documented in the LXD
    documentation.


Network attributes
------------------

  - `name` - The name of the network.
  - `description` - The description of the network.
  - `type` - The type of the network.
  - `used_by` - A list of containers using this network.
  - `config` - The configuration associated with the network.
  - `managed` - `boolean`; whether LXD manages the network.


Profile methods
---------------

  - `rename` - Rename the network.
  - `save` - Save the network. This uses the PUT HTTP method and not the PATCH.
  - `delete` - Deletes the network.

Examples
--------

:class:`~network.Network` operations follow the same manager-style as other
classes. Network are keyed on a unique name.

.. code-block:: python

    >>> network = client.networks.get('lxdbr0')
    >>> network
    <pylxd.models.network.Network object at 0x7f66ae4a2840>


The network can then be modified and saved.

    >>> network.config['ipv4.address'] = '10.253.10.1/24'
    >>> network.save()


To create a new network, use `create` with a name, and optional arguments:
`description` and `type_` and `config`.

    >>> network = client.networks.create(
    ...     'lxdbr1', description='My new network', type_='bridge', config={})
