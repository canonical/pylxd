============
Contributing
============

pyLXD development is done on `Github`_. Pull Requests and Issues should be
filed there. We try and respond to PRs and Issues within a few days.

If you would like to contribute major features or have big ideas, it's best to
post at the `Linux Containers disucssion forum
<https://discuss.linuxcontainers.org/>`_ to discuss your ideas before
submitting PRs.  If you use ``[pylxd]`` in the title, it'll make it clearer.

Adding a Feature or Fixing a Bug
--------------------------------

The main steps are:

1. There needs to be a bug filed on the `Github`_ repository.  This is also for
   a feature, so it's clear what is being proposed prior to somebody starting
   work on it.
2. The pyLXD repository must be forked on Github to the developer's own
   account.
3. The developer should create a personal branch, with either:

   * feature/name-of-feature
   * bug/number/descriptive-name-of-bug

   This can be done with ``git checkout -b feature/name-of-feature`` from the
   master branch.
4. Work on that branch, push to the personal GitHub repository and then create
   a Pull Request.  It's a good idea to create the Pull Request early,
   particularly for features, so that it can be discussed and help sought (if
   needed).
5. When the Pull Request is ready it will then be merged.
6. At regular intervals the pyLXD module will be released to PyPi with the new
   features and bug fixes.

Requirements to merge a Pull Request (PR)
-----------------------------------------

In order for a Pull Request to be merged the following criteria needs to be
met:

1. All of the commits in the PR need to be `signed off using the '-s' option
   with git commit <https://git-scm.com/docs/git-commit>`_.  This is a
   requirement for all projects in the `Github Linux Containers projects space
   <https://github.com/lxc>`_.
2. Unit tests are required for the changes.  These are in the ``pylxd/tests``
   directory and follow the same directory structure as the module.
3. The unit test code coverage for the project shouldn't drop.  This means that
   any lines that aren't testable (for good reasons) need to be explicitly
   excluded from the coverage using ``# NOQA`` comments.
4. If the feature/bug fix requires integration test changes, then they should
   be added to the ``integration`` directory.
5. If the feature/bug fix changes the API then the documentation in the
   ``doc/source`` directory should also be updated.
6. If the contributor is new to the project, then they should add their
   name/details to the ``CONTRIBUTORS.rst`` file in the root of the repository
   as part of the PR.

Once these requirements are met, the change will be merged to the repository.
At this point, the contributor should then delete their private branch.

Code standards
--------------

pyLXD formats code with Black and isort. Verify the formatting with::

    tox -e lint

If it fails, you can reformat the code with::

    tox -e format

Testing
-------

Testing pyLXD is in 3 parts:

1. Conformance with Black and isort, using the ``tox -e lint`` command.
2. Unit tests using ``tox -e py`` or ``tox -e coverage``.
3. Integration tests using the ``tox -e integration-in-lxd``.

.. note:: all of the tests can be run by just using the ``tox`` command on it's
          own, with the exception of the integration tests.  These are not
          automatically run as they require a working LXD environment.

All of the commands use the `Tox`_ automation project to run tests in a
sandboxed environment.


Unit Testing
^^^^^^^^^^^^

pyLXD tries to follow best practices when it comes to testing. PRs are gated
by `GitHub Actions <https://github.com/lxc/pylxd/actions>`_ and
`CodeCov <https://codecov.io/gh/lxc/pylxd>`_. It's best to submit tests
with new changes, as your patch is unlikely to be accepted without them.

To run the tests, you should use `Tox`_::

    tox

Integration Testing
^^^^^^^^^^^^^^^^^^^

Integration testing requires a running LXD system.  They can be tested locally
in LXD container with nesting support; ``tox -e integration-in-lxd``.

.. _Github: https://github.com/lxc/pylxd
.. _Tox: https://documentation.ubuntu.com/lxd/en/latest/clustering/
.. _Multipass: https://github.com/canonical/multipass
