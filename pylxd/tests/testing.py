import json
import re
import unittest

import requests_mock

from pylxd.client import Client
from pylxd.tests import mock_lxd


class PyLXDTestCase(unittest.TestCase):
    """A test case for handling mocking of LXD services."""

    def setUp(self):
        self.requests_mock = requests_mock.Mocker()
        self.add_rules(mock_lxd.RULES)
        self.requests_mock.start()

        self.client = Client(endpoint="http://pylxd.test")

    def tearDown(self):
        self.requests_mock.stop()

    def add_rule(self, rule):
        """Add a rule to the mock LXD service."""
        self.requests_mock.register_uri(
            rule["method"],
            re.compile(rule["url"]),
            text=rule.get("text"),
            status_code=rule.get("status_code", 200),
            json=rule.get("json"),
            headers=rule.get("headers", {}),
        )

    def add_rules(self, rules):
        for rule in rules:
            self.add_rule(rule)


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
