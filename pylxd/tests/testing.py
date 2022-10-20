import json
import unittest

import mock_services

from pylxd.client import Client
from pylxd.tests import mock_lxd


class PyLXDTestCase(unittest.TestCase):
    """A test case for handling mocking of LXD services."""

    def setUp(self):
        mock_services.update_http_rules(mock_lxd.RULES)
        mock_services.start_http_mock()

        self.client = Client(endpoint="http://pylxd.test")

    def tearDown(self):
        mock_services.stop_http_mock()

    def add_rule(self, rule):
        """Add a rule to the mock LXD service."""
        mock_services.update_http_rules([rule])

    def add_rules(self, rules):
        mock_services.update_http_rules(rules)


def add_api_extension_helper(obj, extensions):
    obj.add_rule(
        {
            "text": json.dumps(
                {
                    "type": "sync",
                    "metadata": {
                        "auth": "trusted",
                        "environment": {
                            "certificate": "an-pem-cert",
                        },
                        "api_extensions": extensions,
                    },
                }
            ),
            "method": "GET",
            "url": r"^http://pylxd.test/1.0$",
        }
    )
    # Update hostinfo
    obj.client.host_info = obj.client.api.get().json()["metadata"]
