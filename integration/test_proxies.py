import os
import unittest

from pylxd.client import Client


class ProxyTestCase(unittest.TestCase):

    @unittest.skipIf('HTTP_PROXY' not in os.environ,
                     'requires an HTTP_PROXY environment variable')
    def test_create_with_proxy_env_var(self):
        client = Client()
        self.assertEqual(200, client.api.get().status_code)
