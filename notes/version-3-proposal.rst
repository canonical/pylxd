..
  Copyright 2018 Canonical Limited

  This work is licensed under a Creative Commons Attribution 3.0
  Unported License.
  http://creativecommons.org/licenses/by/3.0/legalcode

..
  This template should be in ReSTructured text. Please do not delete
  any of the sections in this template.  If you have nothing to say
  for a whole section, just write: "None". For help with syntax, see
  http://sphinx-doc.org/rest.html To test out your formatting, see
  http://www.tele3.cz/jbar/rest/rest.html

===========================================
pyLxd 3.0 Proposal - backwards incompatible
===========================================

pylxd 2.x has an odd interface and tends not to be very flexible to
changes/variations in the parent LXD API.  The 'oddness' in the interface is
that the *api* and *client* are on every instance, and the raw API methods tend
to have to be used inconsistently.

Problem Description
===================

A detailed description of the problem.

The pylxd client API has the following issues/inconsistencies, which should be
addressed to give a more natural Pythonic interface to lxd, which is the
purpose of the library.

1. The attribute/manager/__slots__ system, whilst very clever, is inflexible
   and simply discards new attributes that are added to (point) releases of the
   LXD package.

2. The attribute system only tries to do a single level of JSON loading, and
   doesn't load the whole tree of metadata returned in an API call.  Thus you
   get the (slightly) perverse situation of some attributes container contain
   JSON encoded strings, rather than a dictionary/list object.  See `#214
   <https://github.com/lxc/pylxd/issues/214>`_ for example.

3. Each ``object`` returned has hard-coded methods for ``.api``, ``.client``
   and ``.save`` which allows/encourages fairly strange code structures.  e.g.
   if you have a *container* object, you can (oddly) do
   ``container.client.profiles.all()``.  This also means that an object can
   never have an attribute called *client*, *api* or *save*.

4. The object system is only partially done.  e.g. The *container* object has
   *profiles* as simple list attribute; it really ought to be profile objects.
   So code such as ``container.profiles['general']`` should return the general
   profile (or a ``KeyError``), and ``container.profiles`` ought to be a
   dictionary like object.

5. There is a surprising result that if you ask for the same container twice,
   they are two different objects.  This means that you can change them
   independently in different ways, and then ``.save()`` then they would
   overwrite it each in interesting ways (last write wins).  It would be better
   to serve up the same object each time it is fetched.  This can be acheived
   with reference counting and weak-refs.

6. nova-lxd will need a some changes to the API usage to match this work.  This
   is not a particularly difficult task.

Proposed Change
===============

Here is where you cover the change you propose to make in detail. How do you
propose to solve this problem?

If this is one part of a larger effort make it clear where this piece ends. In
other words, what's the scope of this effort?

The proposal is to release a pylxd 3.0 that is backwards *incompatible* with
the 2.0 series.  This will have a modified external API that is more Pythonic
and also fixes some of the unexpected quirks of the existing external API.
These are in detail:

**1. Resolve inflexible __slots__ arrangement**

The issue with the ``__slots__`` is that it fixes what attributes are loaded
from the ``metadata`` key returned during a ``GET`` call.  i.e. new attributes,
which do appear from time to time, *and are frequently backported with a
feature flag to the stable releases*, aren't accessible via the pylxd library.
This is, frankly, annoying.

A solution to this problem is to store the whole ``metadata`` JSON object
(after it has been parsed) on an internal var (say ``_metadata``) and
dynamically accept attribute access via key lookups.  This would make any new
attributes read-only which is, at least, more useful than not existing.  Then
the different lxd object classes would just need lists for what keys are
writable and which ones relate to other objects (the so called *manager*
methods).

**2. Single level of JSON loading**

This one is very easy to fix.  Instead of just assigning each top-level key to
a local attribute, just JSON parse the entire ``metadata`` section and store
it.  This will parse (and thus, JSON validate) the attributes.  They can then
be lazily accessed via ``__getattribute__()`` if they exist in the
``_metadata``.

**3. .client, .api properties on every lxd object**

The end result will be that every attribute on an lxd object will have a direct
mapping to the (new) ``_metadata`` private attribute on the object.  i.e. the
``class Model`` will have a private ``_metadata`` member that is the
``metadata`` returned by API calls to lxd.

The ``.save()``, ``.dirty()``, ``.sync()``, ``.rollback()``, ``.delete()`` and
``.marshal()`` methods will be removed completely, and new functions will be
added to the top level pylxd module to access their functionality.  Therefore,
saving an lxd object will then take the form:

.. code-block:: python

   import pylxd

   ...
   pylxd.save(some_object)

The concept is that the objects themselves become just data entities, but will
a little bit of behaviour around read-only attributes, and 'manager' attributes
for 'chained' objects (e.g. profiles on a container).

This ``client`` and ``api`` properties will be renamed to ``_client`` and
``_api`` to make them 'private' and thus, for internal library use; i.e.
signalling that the user of the library is not supposed to use these methods on
the objects.  If possible, they may be removed entirely, although it's not
clear how dependent objects could be automatically fetched without having at
least the ``_client`` available on each object.

Note, that currently, the ``.api`` property is set for each object to resolve
the API path and instead having an ``_url`` property which returns the API
endpoint url fragment for that container.  Then the ``save(...)``,
``sync(...)`` can use that as a data string, rather than as a convoluted client
accessing property which is hard to follow when reading the code.

**4.  The object system is only partially done**

e.g. Container objects have profiles, but they just return strings.  i.e. to
access a profile, currently:

.. code-block:: python

   import pylxd

   c = pylxd.Client()
   container = c.containers.get('test')
   profile = c.profiles.get(container.profiles[0])

This would be much more natural if it could be accessed as:

.. code-block:: python

   import pylxd

   c = pylxd.Client()
   profile = c.containers['test'].profiles[0]

and the ``profile`` object would be a pylxd ``Model()`` object, where the
``used_by`` attribute would be a dictionary like object which had 'test' as a
key, and the test container as a value. e.g.

.. code-block:: python

   container_manager = c.profiles['default'].used_by
   <... Manager for containers ...>

i.e. the ``used_by`` property would return a manager to access containers.
This might represents 0 to *n* containers as a profile can be used by more than
one container.

**5. Make the manager classes 'smarter' and self documenting**

The Manager classes for various 'lists' of lxd objects could be made smarter,
and thus more intuitive to use.  At the moment, they have ``.get()`` and
``.all()`` methods (as well as the other class methods) of the managed object
class.  (e.g. Container has a class method of ``create``).

However, the code would be eaiser to understand if the Manager classes had the
class methods for the various objects, without having to dynamically set them,
and the object classes were 'dumber'.  In the process, it is possible to make
the classes easier to use.

So if the manager class supports the ``__getitem__()`` method then we can use
dictionary-like indexing to provide a natural interface to accessing
containers.  The two specific behaviours the manager classes should have are
dictionary getitem behaviour and iterator behaviour.  This means that they can
be used like dictionaries and also as iterators (and thus 'listable').

So examples:

.. code-block:: python

   c = pylxd.Client()
   list(c.containers)
   [<container... 1>, <container... 2>, etc.]

   c.containers['test']  # access the test container.
   c.containers[3]       # access the fourth container (0 indexed)
   c.containers.create(...)  # create a container
   c.containers.delete(str or container) # delete a container
   pylxd.delete(container)
   pylxd.save(container)

**6. Raw API access**

The pythonic interface is very useful, but sometimes, just accessing the raw
methods and returning the response is useful.  pylxd provides this via the
``.api`` property, but it is missing the ``patch()`` method.  Also, with the
other changes, the ``api`` property on each lxd object will (probably)
disappear, and thus a little work may be necessary to be able to keep doing
something like:

.. code-block:: python

   c = pylxd.Client()
   response = c.api.containers['test'].get()

It may be better to provide a separate *raw* api interface that can be used to
generate the URL that will then be used.  e.g.

.. code-block:: python

   c = pylxd.Client()
   url = c.url.containers['test'].files['/abc/def']
   file = c.raw.get(url)

It's not clear what the best approach to this is yet.

**7. Caching of objects**

This is the principal that if the system hands out the same url object twice,
it ought to be the same object.  This (optional) part of the proposal is to
weakref count the objects by URL and give out the same object if the weakref is
still valid (by url).  Note that this is not the same as being *thread safe*
which the library isn't at present (due to the way that multiple objects of the
same resource are handed out).  This would allow the API to be used in a way
that minimises the API calls, yet allows it to be used effectively.

**Self Documenting code**

At present there are separate ReST files for each of the ManagerModel classes
*because* they can't be documentd on the *actual* classes (the methods are
runtime imported from the managed class).  With the changes suggested in this
proposal, the Manager classes can be properly documented in ``docstrings``
which would help to ensure that documentation stays up to date with code
changes.

Thus, the key to 'self-documenting' is that the documentation on how to the
methods on the Manager class can actually *be* in the manager class, along with
type information, etc., and this can be used to generate the API documentation.
This would make for more maintainable documentation for the library.

Alternatives
------------

None

Implementation
==============

Assignee(s)
-----------

Who is leading the writing of the code? Or is this a blueprint where you're
throwing it out there to see who picks it up?

If more than one person is working on the implementation, please designate the
primary author and contact.

Primary assignee:
  <launchpad-id or None>

Can optionally list additional ids if they intend on doing substantial
implementation work on this blueprint.

TBC

Gerrit Topic
------------

NA - The code is managed in GitHub.  A separate 3.0 development branch will be
created and code/documentation merged using the GitHub Pull Request system.

Work Items
----------

Work items or tasks -- break the feature up into the things that need to be
done to implement it. Those parts might end up being done by different people,
but we're mostly trying to understand the timeline for implementation.

TBC

Repositories
------------

No new repositories are needed.

Documentation
-------------

The existing documentation will need to be changed.  This documentation is
already generated as a sphinx job with the python module.  It is proposed as
part of the work to migrate the separately maintained written documentation
pages about the containers, profiles, (etc.) and move them to the ManagerModel
doctstring documentation.  This would enhance the documentation and also ensure
that it stays up to date with changes in the library.  At present, because the
documentation is separate from the code, it often ages and doesn't correspond
to the actual API.

Security
--------

No change to security is envisaged.

Testing
-------

The existing test infrastructure is sufficient to adequately test the changes.
The unit tests will need to be changed to accommodate the API changes.

Dependencies
============

- nova-lxd will be impacted by the API change, but the changes will just be how
  the pylxd API is called, rather than semantic changes to how the API is used.
