import json


def containers_POST(request, context):
    context.status_code = 202
    return json.dumps({'operation': 'operation-abc'})


def container_DELETE(request, context):
    context.status_code = 202
    return json.dumps({'operation': 'operation-abc'})


def images_POST(request, context):
    context.status_code = 202
    return json.dumps({'metadata': {}})


def profiles_POST(request, context):
    context.status_code = 202
    return json.dumps({'metadata': {}})


def snapshot_DELETE(request, context):
    context.status_code = 202
    return json.dumps({'operation': 'operation-abc'})


def profile_GET(request, context):
    name = request.path.split('/')[-1]
    return json.dumps({
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
        'text': json.dumps({'metadata': {'auth': 'trusted',
                                         'environment': {}}}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0$',
    },


    # Containers
    {
        'text': json.dumps({'metadata': [
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
        'text': json.dumps({'metadata': {
            'name': 'an-container',
            'ephemeral': True,
        }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },
    {
        'text': json.dumps({'metadata': {
            'status': 'Running',
            'status_code': 103,
        }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container/state$',  # NOQA
    },
    {
        'text': json.dumps({'operation': 'operation-abc',
                            'metadata': {}}),
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },
    {
        'text': json.dumps({'operation': 'operation-abc'}),
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },
    {
        'text': container_DELETE,
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/containers/an-container$',
    },


    # Container Snapshots
    {
        'text': json.dumps({'metadata': [
            '/1.0/containers/an_container/snapshots/an-snapshot',
        ]}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container/snapshots$',  # NOQA
    },
    {
        'text': json.dumps({'operation': 'operation-abc'}),
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/an-container/snapshots$',  # NOQA
    },
    {
        'text': json.dumps({'metadata': {
            'name': 'an_container/an-snapshot',
            'stateful': False,
        }}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/an-container/snapshots/an-snapshot$',  # NOQA
    },
    {
        'text': json.dumps({'operation': 'operation-abc'}),
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
        'text': json.dumps({'metadata': [
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

    # Profiles
    {
        'text': json.dumps({'metadata': [
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

    # Operations
    {
        'text': '{"metadata": {"id": "operation-abc"}}',
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/operations/operation-abc$',
    },
    {
        'text': '{"metadata": {}',
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/operations/operation-abc/wait$',
    },
]
