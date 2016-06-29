Profiles
========

`Profile` describe configuration options for containers in a re-usable way.


Manager methods
---------------

Profiles can be queried through the following client manager
methods:

  - `all()` - Retrieve all networks
  - `get()` - Get a specific network, by its name.
  - `create(name, config, devices)` - Create a new profile. The name of the
    profile is required. `config` and `devices` dictionaries are optional,
    and the scope of their contents is documented in the LXD documentation.


Profile attributes
------------------

  - `name` - The name of the network
  - `type` - The type of the network
  - `used_by` - A list of containers using this network


Profile methods
---------------

  - `rename` - Rename the profile.


Examples
--------

:class:`~profile.Profile` operations follow the same manager-style as
Containers and Images. Profiles are keyed on a unique name.

.. code-block:: python

    >>> profile = client.profiles.get('my-profile')
    >>> profile
    <profile.Profile at 0x7f95d8af72b0>


The profile can then be modified and saved.

    >>> profile.config = profile.config.update({'security.nesting': 'true'})
    >>> profile.update()


To create a new profile, use `create` with a name, and optional `config`
and `devices` config dictionaries.

    >>> profile = client.profiles.create(
    ...     'an-profile', config={'security.nesting': 'true'},
    ...     devices={'root': {'path': '/', 'size': '10GB', 'type': 'disk'}})
