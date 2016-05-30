============
Contributing
============

pyLXD development is done `on Github <https://github.com/lxc/pylxd>`_. Pull
Requests and Issues should be filed there. We try and respond to PRs and
Issues within a few days.

If you would like to contribute large features or have big ideas, it's best
to post on to `the lxc-users list
<https://lists.linuxcontainers.org/listinfo/lxc-users>`_
to discuss your ideas before submitting PRs.

Code standards
--------------

pyLXD follows `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ as closely
as practical. To check your compliance, use the `pep8` tox target::

    tox -epep8

Testing
-------

pyLXD tries to follow best practices when it comes to testing. PRs are gated
by `Travis CI <https://travis-ci.org/lxc/pylxd>`_ and
`CodeCov <https://codecov.io/gh/lxc/pylxd>`_. It's best to submit tests
with new changes, as your patch is unlikely to be accepted without them.

To run the tests, you can use nose::

    nosetests pylxd

...or, alternatively, you can use `tox` (with the added bonus that it will
test python 2.7, python 3, and pypy, as well as run pep8). This is the way
that Travis will test, so it's recommended that you run this at least once
before submitting a Pull Request.
