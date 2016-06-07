import json


def containers_POST(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': 'operation-abc'})


def container_DELETE(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': 'operation-abc'})


def images_POST(request, context):
    context.status_code = 202
    return json.dumps({
        'type': 'async',
        'operation': 'operation-abc'})


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
                         'environment': {}}}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0$',
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
        'url': r'^http://pylxd.test/1.0/containers$',
    },
    {
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                'name': 'an-container',
                'ephemeral': True,
            }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },
    {
        'text': json.dumps({
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
            }}),
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
        'text': json.dumps({
            'type': 'sync',  # This should be async
            'operation': 'operation-abc'}),
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },
    {
        'text': json.dumps({
            'type': 'sync',  # This should be async
            'operation': 'operation-abc'}),
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
            'type': 'sync',  # This should be async
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
            'type': 'sync',  # This should be async
            'operation': 'operation-abc'}),
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
            'type': 'sync',  # This should be async
            'operation': 'operation-abc'}),
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
        'text': json.dumps({
            'type': 'sync',
            'metadata': {
                'aliases': [
                    {
                        'name': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # NOQA
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
        'text': json.dumps({'type': 'sync'}),  # should be async
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$',  # NOQA
    },
    {
        'text': '',
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855/export$',  # NOQA
    },
    {
        'text': image_DELETE,
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$',  # NOQA
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
        'url': r'^http://pylxd.test/1.0/profiles/(an-profile|an-new-profile)$',
    },
    {
        'text': json.dumps({'type': 'sync'}),
        'method': 'PUT',
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
            'metadata': {'id': 'operation-abc'},
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
]
