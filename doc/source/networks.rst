.. py:currentmodule:: pylxd.models

Networks
========

:class:`Network` objects show the current networks available to LXD. Creation
and / or modification of networks is possible only if 'network' LXD API
extension is present.


Manager methods
---------------

Networks can be queried through the following client manager
methods:


  - :func:`~Network.all` - Retrieve all networks.
  - :func:`~Network.exists` - See if a profile with a name exists.
    Returns `bool`.
  - :func:`~Network.get` - Get a specific network, by its name.
  - :func:`~Network.create` - Create a new network.
    The name of the network is required. `description`, `type` and `config`
    are optional and the scope of their contents is documented in the LXD
    documentation.


Network attributes
------------------

  - :attr:`~Network.name` - The name of the network.
  - :attr:`~Network.description` - The description of the network.
  - :attr:`~Network.type` - The type of the network.
  - :attr:`~Network.used_by` - A list of containers using this network.
  - :attr:`~Network.config` - The configuration associated with the network.
  - :attr:`~Network.managed` - `boolean`; whether LXD manages the network.


Profile methods
---------------

  - :func:`~Network.rename` - Rename the network.
  - :func:`~Network.save` - Save the network. This uses the PUT HTTP method and
    not the PATCH.
  - :func:`~Network.delete` - Deletes the network.

.. py:currentmodule:: pylxd.models

Examples
--------

:class:`Network` operations follow the same manager-style as other
classes. Networks are keyed on a unique name.

.. code-block:: python

    >>> network = client.networks.get('lxdbr0')

    >>> network
    Network(config={"ipv4.address": "10.74.126.1/24", "ipv4.nat": "true", "ipv6.address": "none"}, description="", name="lxdbr0", type="bridge")

    >>> print(network)
    {
      "name": "lxdbr0",
      "description": "",
      "type": "bridge",
      "config": {
        "ipv4.address": "10.74.126.1/24",
        "ipv4.nat": "true",
        "ipv6.address": "none"
      },
      "managed": true,
      "used_by": []
    }



The network can then be modified and saved.

    >>> network.config['ipv4.address'] = '10.253.10.1/24'
    >>> network.save()


To create a new network, use :func:`~Network.create` with a name, and optional
arguments: `description` and `type` and `config`.

    >>> network = client.networks.create(
    ...     'lxdbr1', description='My new network', type='bridge', config={})


    >>> network = client.networks.create(
    ...     'lxdbr1', description='My new network', type='bridge', config={})


    >>> network = client.networks.create(
    ...     'lxdbr1', description='My new network', type='bridge', config={})
