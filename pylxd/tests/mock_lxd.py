import json


def containers_POST(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': 'operation-abc'})


def container_POST(request, context):
    context.status_code = 202
    if not request.json().get('migration', False):
        return {
            'type': 'async',
            'operation': 'operation-abc'}
    else:
        return {
            'type': 'async',
            'operation': 'operation-abc',
            'metadata': {
                'metadata': {
                    '0': 'abc',
                    '1': 'def',
                    'control': 'ghi',
                }
            }
        }


def container_DELETE(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': 'operation-abc'})


def images_POST(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': 'images-create-operation'})


def image_DELETE(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': 'operation-abc'})


def profiles_POST(request, context):
    context.status_code = 200
    return json.dumps({
        'type': 'sync',
        'metadata': {}})


def profile_DELETE(request, context):
    context.status_code = 200
    return json.dumps({
        'type': 'sync',
        'operation': 'operation-abc'})


def snapshot_DELETE(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': 'operation-abc'})


def profile_GET(request, context):
    name = request.path.split('/')[-1]
    return json.dumps({
        'type': 'sync',
        'metadata': {
            'name': name,
            'description': 'An description',
            'config': {},
            'devices': {},
        },
    })


RULES = [
    # General service endpoints
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {'auth': 'trusted',
                         'environment': {
                             'certificate': 'an-pem-cert',
                             }}}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {'auth': 'trusted',
                         'environment': {}}}),
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
                'status_code': 103
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
        'status_code': 202,
        'json': {
            'type': 'async',
            'operation': 'operation-abc'},
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
            'operation': 'operation-abc'}),
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
            'operation': 'operation-abc'},
        'status_code': 202,
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/an-container/exec$',  # NOQA
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
            'operation': 'operation-abc'}),
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
            'operation': 'operation-abc'}),
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
        'method': 'POST',
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
        'text': json.dumps({'type': 'async', 'operation': 'operation-abc'}),
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
            ]},
        'method': 'GET',
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
