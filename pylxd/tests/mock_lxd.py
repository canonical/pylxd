import json


def containers_POST(request, context):
    context.status_code = 202
    return json.dumps({'operation': 'operation-abc'})


def container_GET(request, context):
    if request.path.endswith('an-container'):
        response_text = json.dumps({'metadata': {
            'name': 'an-container',
            'ephemeral': True,
        }})
        context.status_code = 200
        return response_text
    else:
        context.status_code = 404


def container_DELETE(request, context):
    context.status_code = 202
    return json.dumps({'operation': 'operation-abc'})


def profile_GET(request, context):
    name = request.path.split('/')[-1]
    if name in ('an-profile', 'an-new-profile'):
        return json.dumps({
            'metadata': {
                'name': name,
            },
        })
    else:
        context.status_code = 404


RULES = [
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
        'text': container_GET,
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/containers/(?P<container_name>.*)$',
    },
    {
        'text': json.dumps({'operation': 'operation-abc'}),
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/containers/(?P<container_name>.*)$',
    },
    {
        'text': json.dumps({'operation': 'operation-abc'}),
        'method': 'PUT',
        'url': r'^http://pylxd.test/1.0/containers/(?P<container_name>.*)$',
    },
    {
        'text': container_DELETE,
        'method': 'DELETE',
        'url': r'^http://pylxd.test/1.0/containers/(?P<container_name>.*)$',
    },

    # Images
    {
        'text': json.dumps({'metadata': [
            'http://pylxd.test/1.0/images/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$',  # NOQA
        ]}),
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/images$',
    },
    {
        'text': json.dumps({'metadata': {}}),
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/images$',
    },
    {
        'text': json.dumps({
            'metadata': {
                'fingerprint': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # NOQA
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
        'method': 'POST',
        'url': r'^http://pylxd.test/1.0/profiles$',
    },
    {
        'text': profile_GET,
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/profiles/(?P<container_name>.*)$',
    },

    # Operations
    {
        'text': '{"metadata": {"id": "operation-abc"}}',
        'method': 'GET',
        'url': r'^http://pylxd.test/1.0/operations/(?P<operation_id>.*)$',
    },
]
