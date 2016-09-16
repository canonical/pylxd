import unittest

import mock_services

from pylxd.client import Client
from pylxd.tests import mock_lxd


def requires_ws4py(f):
    """Marks a test as requiring ws4py.

    As ws4py is an optional dependency, some tests should
    be skipped, as they won't run properly if ws4py is not
    installed.
    """
    try:
        import ws4py  # NOQA
        return f
    except ImportError:
        return unittest.skip('ws4py is not installed')(f)


class PyLXDTestCase(unittest.TestCase):
    """A test case for handling mocking of LXD services."""

    def setUp(self):
        mock_services.update_http_rules(mock_lxd.RULES)
        mock_services.start_http_mock()

        self.client = Client(endpoint='http://pylxd.test')

    def tearDown(self):
        mock_services.stop_http_mock()

    def add_rule(self, rule):
        """Add a rule to the mock LXD service."""
        mock_services.update_http_rules([rule])
