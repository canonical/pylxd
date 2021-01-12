.. py:currentmodule:: pylxd.models

Projects
========

LXD supports projects as a way to split your LXD server. Each :class:`Project` holds its own set of instances and may also have its own images and profiles.


Manager methods
---------------

Projects can be queried through the following client manager
methods:

  - :func:`~Project.all` - Retrieve all projects
  - :func:`~Project.exists` - See if a project with a name exists.  Returns `boolean`.
  - :func:`~Project.get` - Get a specific project, by its name.
  - :func:`~Project.create` - Create a new project. The `name` of the project is required. `description` is an optional string with a description of the project.  The `config` dictionary is also optional, the scope of which is documented in the LXD project documentation.


Project attributes
------------------

  - :attr:`Project.name` - (str) name of the project
  - :attr:`Project.description` - (str) The description of the project
  - :attr:`Project.config` - (dict) config options for the project
  - :attr:`Project.used_by` - (list) images, instances, networks, and profiles using this project


Project methods
---------------

  - :func:`Project.rename` - Rename the project.
  - :func:`Project.save` - save a project.  This uses the PUT HTTP method and not the PATCH.
  - :func:`Project.delete` - deletes a project.


Examples
--------

:class:`~Project` operations follow the same manager-style as Containers and Images. Projects are keyed on a unique name.

.. code-block:: python

    >>> project = client.projects.get('my-project')
    >>> project
    <project.Project at 0x7f599e129a60>


The project can then be modified and saved.

    >>> project.config['limits.instances'] = '4'
    >>> project.description = "The four horsemen of the apococalypse"
    >>> project.save()


To create a new project, use `create` with a name, optional `description` string
and `config` dictionary.
p
    >>> project = client.projects.create(
    ...     'a-project', description="New project", config={'limits.instances': '10'})
