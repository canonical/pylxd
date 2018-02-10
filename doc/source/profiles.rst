Profiles
========

`Profile` describe configuration options for containers in a re-usable way.


Manager methods
---------------

Profiles can be queried through the following client manager
methods:

  - `all()` - Retrieve all profiles
  - `exists()` - See if a profile with a name exists.  Returns `boolean`.
  - `get()` - Get a specific profile, by its name.
  - `create(name, config, devices)` - Create a new profile. The name of the
    profile is required. `config` and `devices` dictionaries are optional,
    and the scope of their contents is documented in the LXD documentation.


Profile attributes
------------------

  - `config` - config options for containers
  - `description` - The description of the profile
  - `devices` - device options for containers
  - `name` - The name of the profile
  - `used_by` - A list of containers using this profile


Profile methods
---------------

  - `rename` - Rename the profile.
  - `save` - save a profile.  This uses the PUT HTTP method and not the PATCH.
  - `delete` - deletes a profile.


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
