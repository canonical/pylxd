Networks
========

`Network` objects show the current networks available to lxd. They are
read-only via the REST API.


Manager methods
---------------

Networks can be queried through the following client manager
methods:

  - `all()` - Retrieve all networks
  - `get()` - Get a specific network, by its name.


Network attributes
----------------

  - `name` - The name of the network
  - `type` - The type of the network
  - `used_by` - A list of containers using this network
