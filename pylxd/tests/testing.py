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

    def _last_matching_request(self, method, url):
        """Return the last request matching *method* and *url*, or fail the test.

        Parameters:
            method (str): The expected HTTP method (for example, ``"GET"``).
            url (str): The expected full request URL to match.
        """
        matching = [
            r
            for r in self.requests_mock.request_history
            if r.method == method and r.url == url
        ]
        self.assertTrue(matching, f"No {method} request to {url} found")
        return matching[-1]


def add_api_extension_helper(obj, extensions):
    """Add a mocked API extensions response and refresh cached host metadata.

    Parameters:
        obj: Test helper object that provides ``add_rule`` and ``client``.
        extensions: Iterable of API extension names to expose in ``metadata``.

    Side effects:
        - Registers a new mock ``GET /1.0`` rule on ``obj``.
        - Updates ``obj.client.host_info`` from ``obj.client.api.get()``.
    """
    obj.add_rule(
        {
            "text": json.dumps(
                {
                    "type": "sync",
                    "metadata": {
                        "auth": "trusted",
                        "environment": {
                            "certificate": "a-pem-cert",
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
