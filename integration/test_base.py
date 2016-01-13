import unittest

from pylxd.api import LXD

CERT = '''MIICATCCAWoCCQDejRDAWZlG0DANBgkqhkiG9w0BAQsFADBFMQswCQYDVQQGEwJV
UzETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50ZXJuZXQgV2lkZ2l0
cyBQdHkgTHRkMB4XDTE2MDExMzE0MTAyNFoXDTI2MDExMDE0MTAyNFowRTELMAkG
A1UEBhMCVVMxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNVBAoMGEludGVybmV0
IFdpZGdpdHMgUHR5IEx0ZDCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAv4bk
u8i1q/5vl8VbSALC4Q2MHcyVgQ7I8RGnTZArbD5fGAhhvBXki2w2fo8eoaOV7hh0
bAo+t7rn4RE39OQbdeyAdG62qkRug58eeUb0Qz2Zcg9CQ5vcbApElykHmMt2yXW3
gxtPu0mqUQnUt2zs7/8okwtfc2SMZKpwrUrxDU8CAwEAATANBgkqhkiG9w0BAQsF
AAOBgQA2c14J5FbxMFxTJuEjiIY1s4eJCW1XDC0SO2WRY3iz0fwKautLoOnZJOQk
OZNzJlCVpZjpHeL847mz2ybtoFpUO45bWGg75W5gh4D2gmnG+FlCg2l3Tno1bMoS
tTQu8yyFguWnWnCokzEovlKMR1YajPvndmzf7zRujcL2vKL5uA==
'''


class TestBaseAssumptions(unittest.TestCase):
    """lxd makes some common base assumptions about the rest api."""

    def setUp(self):
        self.lxd = LXD('http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket')

    def test_root(self):
        """GET to / is allowed for everyone (lists the API endpoints)."""
        expected = {
            'type': 'sync',
            'status': 'Success',
            'status_code': 200,
            'metadata': ['/1.0']
        }

        result = self.lxd.get()

        self.assertEqual(200, result.status_code)
        self.assertEqual(expected, result.json())

    def test_1_0(self):
        """GET to /1.0 is allowed for everyone (but result varies)."""
        expected = {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "metadata": {
                "api_compat": 1,
                "auth": "trusted",
                "config": {
                    "images.remote_cache_expiry": "10"
                },
                "environment": {
                    "addresses": [],
                    "architectures": [2, 1],
                    "driver": "lxc",
                    "driver_version": "1.1.5",
                    "kernel": "Linux",
                    "kernel_architecture": "x86_64",
                    "kernel_version": "4.2.0-19-generic",
                    "server": "lxd",
                    "server_pid": 7453,
                    "server_version": "0.20",
                    "storage": "dir",
                    "storage_version": ""
                }
            }
        }

        result = self.lxd['1.0'].get()

        self.assertEqual(200, result.status_code)
        self.assertEqual(expected, result.json())

    def test_1_0_images(self):
        """GET to /1.0/images/* is allowed for everyone.

        ...but only returns public images for unauthenticated users.
        """
        expected = {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "metadata": []
        }

        result = self.lxd['1.0'].images.get()
        json = result.json()
        # metadata should exist, but its content varies.
        json['metadata'] = []

        self.assertEqual(200, result.status_code)
        self.assertEqual(expected, json)

    def test_1_0_certificates_POST(self):
        """POST to /1.0/certificates is allowed for everyone with a client certificate."""
        expected = {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "metadata": {}
        }

        data = {
            'type': 'client',
            'certificate': CERT,
        }
        result = self.lxd['1.0'].certificates.post(json=data)

        self.assertEqual(200, result.status_code)
        self.assertEqual(expected, result.json())
