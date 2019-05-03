import json


def containers_POST(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': '/1.0/operations/operation-abc?project=default'})


def container_POST(request, context):
    context.status_code = 202
    if not request.json().get('migration', False):
        return {
            'type': 'async',
            'operation': '/1.0/operations/operation-abc?project=default'}
    else:
        return {
            'type': 'async',
            'operation': '/1.0/operations/operation-abc?project=default',
            'metadata': {
                'metadata': {
                    '0': 'abc',
                    '1': 'def',
                    'control': 'ghi',
                }
            }
        }


def container_PUT(request, context):
    context.status_code = 202
    return {
        'type': 'async',
        'operation': '/1.0/operations/operation-abc?project=default'
    }


def container_DELETE(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': '/1.0/operations/operation-abc?project=default'})


def images_POST(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': '/1.0/operations/images-create-operation?project=default'
    })


def image_DELETE(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': '/1.0/operations/operation-abc?project=default'})


def networks_GET(request, _):
    name = request.path.split('/')[-1]
    return json.dumps({
        'type': 'sync',
        'metadata': {
            'config': {
                'ipv4.address': '10.80.100.1/24',
                'ipv4.nat': 'true',
                'ipv6.address': 'none',
                'ipv6.nat': 'false',
            },
            'name': name,
            'description': 'Network description',
            'type': 'bridge',
            'managed': True,
            'used_by': [],
        },
    })


def networks_POST(_, context):
    context.status_code = 200
    return json.dumps({
        'type': 'sync',
        'metadata': {}})


def networks_DELETE(_, context):
    context.status_code = 202
    return json.dumps({
        'type': 'sync',
        'operation': '/1.0/operations/operation-abc?project=default'})


def profile_GET(request, context):
    name = request.path.split('/')[-1]
    return json.dumps({
        'type': 'sync',
        'metadata': {
            'name': name,
            'description': 'An description',
            'config': {},
            'devices': {},
            'used_by': [],
        },
    })


def profiles_POST(request, context):
    context.status_code = 200
    return json.dumps({
        'type': 'sync',
        'metadata': {}})


def profile_DELETE(request, context):
    context.status_code = 200
    return json.dumps({
        'type': 'sync',
        'operation': '/1.0/operations/operation-abc?project=default'})


def snapshot_DELETE(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': '/1.0/operations/operation-abc?project=default'})


RULES = [
    # General service endpoints
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {'auth': 'trusted',
                         'environment': {
                             'certificate': 'an-pem-cert',
                             },
                         'api_extensions': []
                         }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {'auth': 'trusted',
                         'environment': {},
                         'api_extensions': []
                         }}),
        'method': 'GET',
        'url': r'^http://pylxd2.test/1.0$',
    },



    # Certificates
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': [
                'http://pylxd.test/1.0/certificates/an-certificate',
            ]}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/certificates$',
    },
    {
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/certificates$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                'certificate': 'certificate-content',
                'fingerprint': 'eaf55b72fc23aa516d709271df9b0116064bf8cfa009cf34c67c33ad32c2320c',  # NOQA
                'type': 'client',
            }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/certificates/eaf55b72fc23aa516d709271df9b0116064bf8cfa009cf34c67c33ad32c2320c$',  # NOQA
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                'certificate': 'certificate-content',
                'fingerprint': 'an-certificate',
                'type': 'client',
            }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/certificates/an-certificate$',
    },
    {
        'json': {
            'type': 'sync',
            'metadata': {},
        },
        'status_code': 202,
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/certificates/an-certificate$',
    },


    # Cluster
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                "server_name": "an-member",
                "enabled": 'true',
                "member_config": [{
                    "entity": "storage-pool",
                    "name": "local",
                    "key": "source",
                    "value": "",
                    "description":
                        "\"source\" property for storage pool \"local\""
                },
                {
                    "entity": "storage-pool",
                    "name": "local",
                    "key": "volatile.initial_source",
                    "value": "",
                    "description":
                        "\"volatile.initial_source\" property for"
                        " storage pool \"local\""
                }]
            }
        }),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/cluster$',
    },


    # Cluster Members
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': [
                'http://pylxd.test/1.0/certificates/an-member',
                'http://pylxd.test/1.0/certificates/nd-member',
            ]}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/cluster/members$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                "server_name": "an-member",
                "url": "https://10.1.1.101:8443",
                "database": 'false',
                "status": "Online",
                "message": "fully operational",
            }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/cluster/members/an-member$',  # NOQA
    },


    # Containers
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': [
                'http://pylxd.test/1.0/containers/an-container',
            ]}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': [
                'http://pylxd2.test/1.0/containers/an-container',
            ]}),
        'method': 'GET',
        'url': r'^http://pylxd2.test/1.0/containers$',
    },
    {
        'text': containers_POST,
        'method': 'POST',
        'url': r'^http://pylxd2.test/1.0/containers$',
    },
    {
        'text': containers_POST,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers$',
    },
    {
        'text': containers_POST,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers\?target=an-remote',
    },
    {
        'json': {
            'type': 'sync',
            'metadata': {
                'name': 'an-container',

                'architecture': "x86_64",
                'config': {
                    'security.privileged': "true",
                },
                'created_at': "1983-06-16T00:00:00-00:00",
                'last_used_at': "1983-06-16T00:00:00-00:00",
                'description': "Some description",
                'devices': {
                    'root': {
                        'path': "/",
                        'type': "disk"
                    }
                },
                'ephemeral': True,
                'expanded_config': {
                    'security.privileged': "true",
                },
                'expanded_devices': {
                    'eth0': {
                        'name': "eth0",
                        'nictype': "bridged",
                        'parent': "lxdbr0",
                        'type': "nic"
                    },
                    'root': {
                        'path': "/",
                        'type': "disk"
                    }
                },
                'profiles': [
                    "default"
                ],
                'stateful': False,
                'status': "Running",
                'status_code': 103,
                'unsupportedbypylxd': "This attribute is not supported by "\
                    "pylxd. We want to test whether the mere presence of it "\
                    "makes it crash."
            }},
        'method': 'GET',
        'url': r'^http://pylxd2.test/1.0/containers/an-container$',
    },
    {
        'json': {
            'type': 'sync',
            'metadata': {
                'name': 'an-container',

                'architecture': "x86_64",
                'config': {
                    'security.privileged': "true",
                },
                'created_at': "1983-06-16T00:00:00-00:00",
                'last_used_at': "1983-06-16T00:00:00-00:00",
                'description': "Some description",
                'devices': {
                    'root': {
                        'path': "/",
                        'type': "disk"
                    }
                },
                'ephemeral': True,
                'expanded_config': {
                    'security.privileged': "true",
                },
                'expanded_devices': {
                    'eth0': {
                        'name': "eth0",
                        'nictype': "bridged",
                        'parent': "lxdbr0",
                        'type': "nic"
                    },
                    'root': {
                        'path': "/",
                        'type': "disk"
                    }
                },
                'profiles': [
                    "default"
                ],
                'stateful': False,
                'status': "Running",
                'status_code': 103,
                'unsupportedbypylxd': "This attribute is not supported by "\
                    "pylxd. We want to test whether the mere presence of it "\
                    "makes it crash."
            }},
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },
    {
        'json': {
            'type': 'sync',
            'metadata': {
                'status': 'Running',
                'status_code': 103,
                'disk': {
                    'root': {
                        'usage': 10,
                    }
                },
                'memory': {
                    'usage': 15,
                    'usage_peak': 20,
                    'swap_usage': 0,
                    'swap_usage_peak': 5,
                },
                'network': {
                    'l0': {
                        'addresses': [
                            {'family': 'inet',
                             'address': '127.0.0.1',
                             'netmask': '8',
                             'scope': 'local'}
                        ],
                    }
                },
                'pid': 69,
                'processes': 100,
            }},
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container/state$',  # NOQA
    },
    {
        'json': {
            'type': 'sync',
            'metadata': {
                'name': 'an-new-remote-container',

                'architecture': "x86_64",
                'config': {
                    'security.privileged': "true",
                },
                'created_at': "1983-06-16T00:00:00-00:00",
                'last_used_at': "1983-06-16T00:00:00-00:00",
                'description': "Some description",
                'location': "an-remote",
                'status': "Running",
                'status_code': 103,
                'unsupportedbypylxd': "This attribute is not supported by "\
                    "pylxd. We want to test whether the mere presence of it "\
                    "makes it crash."
            }},
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-new-remote-container$',
    },
    {
        'status_code': 202,
        'json': {
            'type': 'async',
            'operation': '/1.0/operations/operation-abc?project=default'},
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/containers/an-container/state$',  # NOQA
    },
    {
        'json': container_POST,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },
    {
        'text': json.dumps({
            'type': 'async',
            'operation': '/1.0/operations/operation-abc?project=default'}),
        'status_code': 202,
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },
    {
        'text': container_DELETE,
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },
    {
        'json': {
            'type': 'async',
            'metadata': {
                'metadata': {
                    'fds': {
                        '0': 'abc',
                        '1': 'def',
                        '2': 'ghi',
                        'control': 'jkl',
                    }
                },
            },
            'operation': '/1.0/operations/operation-abc?project=default'},
        'status_code': 202,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/an-container/exec$',  # NOQA
    },
    {
        'json': container_PUT,
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },

    # Container Snapshots
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': [
                '/1.0/containers/an_container/snapshots/an-snapshot',
            ]}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container/snapshots$',  # NOQA
    },
    {
        'text': json.dumps({
            'type': 'async',
            'operation': '/1.0/operations/operation-abc?project=default'}),
        'status_code': 202,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/an-container/snapshots$',  # NOQA
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                'name': 'an_container/an-snapshot',
                'stateful': False,
            }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container/snapshots/an-snapshot$',  # NOQA
    },
    {
        'text': json.dumps({
            'type': 'async',
            'operation': '/1.0/operations/operation-abc?project=default'}),
        'status_code': 202,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/an-container/snapshots/an-snapshot$',  # NOQA
    },
    {
        'text': snapshot_DELETE,
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/containers/an-container/snapshots/an-snapshot$',  # NOQA
    },


    # Container files
    {
        'text': 'This is a getted file',
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container/files\?path=%2Ftmp%2Fgetted$',  # NOQA
    },
    {
        'text': '{"some": "value"}',
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container/files\?path=%2Ftmp%2Fjson-get$',  # NOQA
    },
    {
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/an-container/files\?path=%2Ftmp%2Fputted$',  # NOQA
    },
    {
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/containers/an-container/files\?path=%2Ftmp%2Fputted$',  # NOQA
    },



    # Images
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': [
                'http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # NOQA
            ]}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/images$',
    },
    {
        'text': images_POST,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/images$',
    },
    {
        'text': images_POST,
        'method': 'POST',
        'url': r'^http://pylxd2.test/1.0/images$',
    },
    {
        'json': {
            'type': 'sync',
            'status': 'Success',
            'status_code': 200,
            'metadata': {
                'name': 'an-alias',
                'description': 'an-alias',
                'target': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # NOQA
            }
        },
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/images/aliases/an-alias$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                'aliases': [
                    {
                        'name': 'an-alias',  # NOQA
                        'fingerprint': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # NOQA
                    }
                ],
                'architecture': 'x86_64',
                'cached': False,
                'filename': 'a_image.tar.bz2',
                'fingerprint': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # NOQA
                'public': False,
                'properties': {},
                'size': 1,
                'auto_update': False,
                'created_at': '1983-06-16T02:42:00Z',
                'expires_at': '1983-06-16T02:42:00Z',
                'last_used_at': '1983-06-16T02:42:00Z',
                'uploaded_at': '1983-06-16T02:42:00Z',

            },
        }),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$',  # NOQA
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                'aliases': [
                    {
                        'name': 'an-alias',  # NOQA
                        'fingerprint': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # NOQA
                    }
                ],
                'architecture': 'x86_64',
                'cached': False,
                'filename': 'a_image.tar.bz2',
                'fingerprint': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # NOQA
                'public': False,
                'properties': {},
                'size': 1,
                'auto_update': False,
                'created_at': '1983-06-16T02:42:00Z',
                'expires_at': '1983-06-16T02:42:00Z',
                'last_used_at': '1983-06-16T02:42:00Z',
                'uploaded_at': '1983-06-16T02:42:00Z',

            },
        }),
        'method': 'GET',
        'url': r'^http://pylxd2.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$',  # NOQA
    },
    {
        'text': json.dumps({
            'type': 'async',
            'operation': '/1.0/operations/operation-abc?project=default'}),
        'status_code': 202,
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$',  # NOQA
    },
    {
        'text': '0' * 2048,
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/export$',  # NOQA
    },
    {
        'text': image_DELETE,
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$',  # NOQA
    },

    # Image Aliases
    {
        'json': {
            'type': 'sync',
            'status': 'Success',
            'status_code': 200,
            'metadata': {
                'name': 'an-alias',
                'description': 'an-alias',
                'target': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # NOQA
            }
        },
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/images/aliases/an-alias$',
    },
    {
        'json': {
            'type': 'sync',
            'status': 'Success',
            'metadata': None
        },
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/images/aliases$'
    },
    {
        'json': {
            'type': 'sync',
            'status': 'Success',
            'status_code': 200,
            'metadata': None
        },
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/images/aliases/an-alias$'
    },
    {
        'json': {
            'type': 'sync',
            'status': 'Success',
            'status_code': 200,
            'metadata': None
        },
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/images/aliases/b-alias$'
    },

    # Images secret
    {
        'json': {
            'type': 'sync',
            'status': 'Success',
            'status_code': 200,
            'metadata': {
                'metadata': {
                    'secret': 'abcdefg'
                }
            }
        },
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/secret$',  # NOQA
    },

    # Networks
    {
        'json': {
            'type': 'sync',
            'metadata': [
                'http://pylxd.test/1.0/networks/lo',
                'http://pylxd.test/1.0/networks/eth0',
            ]},
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/networks$',
    },
    {
        'text': networks_POST,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/networks$',
    },
    {
        'json': {
            'type': 'sync',
            'metadata': {
                'name': 'lo',
                'type': 'loopback',
                'used_by': [],
            }},
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/networks/lo$',
    },
    {
        'text': networks_GET,
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/networks/eth(0|1|2)$',
    },
    {
        'text': json.dumps({'type': 'sync'}),
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/networks/eth0$',
    },
    {
        'text': networks_DELETE,
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/networks/eth0$',
    },

    # Storage Pools
    {
        'json': {
            'type': 'sync',
            'metadata': [
                'http://pylxd.test/1.0/storage-pools/lxd',
            ]},
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/storage-pools$',
    },
    {
        'json': {
            'type': 'sync',
            'metadata': {
                'config': {
                    'size': '0',
                    'source': '/var/lib/lxd/disks/lxd.img'
                },
                'description': '',
                'name': 'lxd',
                'driver': 'zfs',
                'used_by': [],
            }},
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd$',
    },
    {
        'json': {'type': 'sync'},
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/storage-pools$',
    },
    {
        'json': {'type': 'sync'},
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd$',
    },
    {
        'json': {'type': 'sync'},
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd$',
    },
    {
        'json': {'type': 'sync'},
        'method': 'PATCH',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd$',
    },

    # Storage Resources
    {
        'json': {
            'type': 'sync',
            'metadata': {
                'space': {
                    'used': 207111192576,
                    'total': 306027577344
                },
                'inodes': {
                    "used": 3275333,
                    "total": 18989056
                }
            }},
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd/resources$',
    },

    # Storage Volumes
    {
        'json': {
            'type': 'sync',
            'metadata': [
                '/1.0/storage-pools/default/volumes/containers/c1',
                '/1.0/storage-pools/default/volumes/containers/c2',
                '/1.0/storage-pools/default/volumes/containers/c3',
                '/1.0/storage-pools/default/volumes/images/i1',
                '/1.0/storage-pools/default/volumes/images/i2',
                '/1.0/storage-pools/default/volumes/custom/cu1',
            ]},
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd/volumes$',
    },
    # create a sync storage volume
    {
        'json': {'type': 'sync'},
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd/volumes/custom$',
    },
    {
        'json': {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "error_code": 0,
            "error": "",
            "metadata": {
                "type": "custom",
                "used_by": [],
                "name": "cu1",
                "config": {
                    "block.filesystem": "ext4",
                    "block.mount_options": "discard",
                    "size": "10737418240"
                }
            }
        },
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd/volumes/custom/cu1$',
    },
    # create an async storage volume
    {
        'json': {'type': 'async',
                 'operation': '/1.0/operations/operation-abc?project=default'},
        'status_code': 202,
        'method': 'POST',
        'url': (r'^http://pylxd.test/1.0/storage-pools/'
                'async-lxd/volumes/custom$'),
    },
    {
        'json': {
            "type": "sync",
            "status": "Success",
            "status_code": 200,
            "error_code": 0,
            "error": "",
            "metadata": {
                "type": "custom",
                "used_by": [],
                "name": "cu1",
                "config": {
                    "block.filesystem": "ext4",
                    "block.mount_options": "discard",
                    "size": "10737418240"
                }
            }
        },
        'method': 'GET',
        'url': (r'^http://pylxd.test/1.0/storage-pools/'
                'async-lxd/volumes/custom/cu1$'),
    },
    # rename a storage volume, sync
    {
        'json': {
            "type": "sync",
            "metadata": {
                "control": "secret1",
                "fs": "secret2"
            },
        },
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd/volumes/custom/cu1$',
    },
    # rename a storage volume, async
    {
        'json': {
            "type": "async",
            "operation": "/1.0/operations/operation-abc?project=default",
            "metadata": {
                "control": "secret1",
                "fs": "secret2"
            },
        },
        'method': 'POST',
        'status_code': 202,
        'url': (r'^http://pylxd.test/1.0/storage-pools/'
                'async-lxd/volumes/custom/cu1$'),
    },
    {
        'json': {'type': 'sync'},
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd/volumes/custom/cu1$',
    },
    {
        'json': {'type': 'sync'},
        'method': 'PATCH',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd/volumes/custom/cu1$',
    },
    {
        'json': {'type': 'sync'},
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/storage-pools/lxd/volumes/custom/cu1$',
    },

    # Profiles
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': [
                'http://pylxd.test/1.0/profiles/an-profile',
            ]}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/profiles$',
    },
    {
        'text': profiles_POST,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/profiles$',
    },
    {
        'text': profile_GET,
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/profiles/(an-profile|an-new-profile|an-renamed-profile)$',  # NOQA
    },
    {
        'text': json.dumps({'type': 'sync'}),
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/profiles/(an-profile|an-new-profile)$',
    },
    {
        'text': json.dumps({'type': 'sync'}),
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/profiles/(an-profile|an-new-profile)$',
    },
    {
        'text': profile_DELETE,
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/profiles/(an-profile|an-new-profile)$',
    },


    # Operations
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {'id': 'operation-abc', 'metadata': {'return': 0}},
            }),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/operations/operation-abc$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            }),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/operations/operation-abc/wait$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {'id': 'operation-abc'},
            }),
        'method': 'GET',
        'url': r'^http://pylxd2.test/1.0/operations/operation-abc$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            }),
        'method': 'GET',
        'url': r'^http://pylxd2.test/1.0/operations/operation-abc/wait$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                'id': 'images-create-operation',
                'metadata': {
                    'fingerprint': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'  # NOQA
                }
            }
        }),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/operations/images-create-operation$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            }),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/operations/images-create-operation/wait$',  # NOQA
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {'id': 'operation-abc'},
            }),
        'method': 'GET',
        'url': r'^http://pylxd2.test/1.0/operations/images-create-operation$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            }),
        'method': 'GET',
        'url': r'^http://pylxd2.test/1.0/operations/images-create-operation/wait$',  # NOQA
    }
]
