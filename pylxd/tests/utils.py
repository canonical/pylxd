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

from pylxd import api
from pylxd import exceptions as lxd_exceptions


def upload_image(image):
    alias = '{}/{}/{}/{}'.format(image['os'],
                                 image['release'],
                                 image['arch'],
                                 image['variant'])
    lxd = api.API()
    imgs = api.API(host='images.linuxcontainers.org')
    d = imgs.alias_show(alias)

    meta = d[1]['metadata']
    tgt = meta['target']

    try:
        lxd.alias_update(meta)
    except lxd_exceptions.APIError as ex:
        if ex.status_code == 404:
            lxd.alias_create(meta)

    return tgt


def delete_image(image):
    lxd = api.API()
    lxd.image_delete(image)
