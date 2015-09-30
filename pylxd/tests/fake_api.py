# Copyright (c) 2015 Canonical Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


def fake_standard_return():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": {}
    }


def fake_host():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": {
                "api_compat": 1,
                "auth": "trusted",
                "config": {},
                "environment": {
                    "backing_fs": "ext4",
                    "driver": "lxc",
                    "kernel_version": "3.19.0-22-generic",
                    "lxc_version": "1.1.2",
                    "lxd_version": "0.12"
                }
        }
    }


def fake_image_list_empty():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": []
    }


def fake_image_list():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": ['/1.0/images/trusty']
    }


def fake_image_info():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": {
            "aliases": [
                {
                    "target": "ubuntu",
                    "description": "ubuntu"
                }
            ],
            "architecture": 2,
            "fingerprint": "04aac4257341478b49c25d22cea8a6ce"
                           "0489dc6c42d835367945e7596368a37f",
            "filename": "",
            "properties": {},
            "public": 0,
            "size": 67043148,
            "created_at": 0,
            "expires_at": 0,
            "uploaded_at": 1435669853
        }
    }


def fake_alias():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": {
                "target": "ubuntu",
                "description": "ubuntu"
        }
    }


def fake_alias_list():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": [
            "/1.0/images/aliases/ubuntu"
        ]
    }


def fake_container_list():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": [
            "/1.0/containers/trusty-1"
        ]
    }


def fake_container_state(status):
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": {
            "status": status
        }
    }


def fake_container_log():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": {
            "log": "fake log"
        }
    }


def fake_container_migrate():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "operation": "/1.0/operations/1234",
        "metadata": {
            "control": "fake_control",
            "fs": "fake_fs",
            "criu": "fake_criu",
        }
    }


def fake_snapshots_list():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": [
            "/1.0/containers/trusty-1/snapshots/first"
        ]
    }


def fake_certificate_list():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": [
            "/1.0/certificates/ABCDEF01"
        ]
    }


def fake_certificate():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": {
            "type": "client",
            "certificate": "ABCDEF01"
        }
    }


def fake_profile_list():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": [
            "/1.0/profiles/fake-profile"
        ]
    }


def fake_profile():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": {
            "name": "fake-profile",
            "config": {
                "resources.memory": "2GB",
                "network.0.bridge": "lxcbr0"
            }
        }
    }


def fake_operation_list():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": [
            "/1.0/operations/1234"
        ]
    }


def fake_operation():
    return {
        "type": "async",
        "status": "OK",
        "status_code": 100,
        "operation": "/1.0/operation/1234",
        "metadata": {
            "created_at": "2015-06-09T19:07:24.379615253-06:00",
            "updated_at": "2015-06-09T19:07:23.379615253-06:00",
            "status": "Running",
            "status_code": 103,
            "resources": {
                "containers": ["/1.0/containers/1"]
            },
            "metadata": {},
            "may_cancel": True
        }
    }


def fake_network_list():
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": [
            "/1.0/networks/lxcbr0"
        ]
    }


def fake_network():
    return {
        "type": "async",
        "status": "OK",
        "status_code": 100,
        "operation": "/1.0/operation/1234",
        "metadata": {
            "name": "lxcbr0",
            "type": "bridge",
            "members": ["/1.0/containers/trusty-1"]
        }
    }
