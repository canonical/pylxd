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

import uuid

from pylxd import api

def upload_image(image):
    alias = '{}/{}/{}/{}'.format(image['os'], image['release'],
                             image['arch'], image['variant'])
    lxd = api.API()
    imgs = api.API(host='images.linuxcontainers.org')
    d = imgs.alias_show(alias)

    meta =  d[1]['metadata']
    tgt = meta['target']

    i = imgs.image_export(tgt)
    c = lxd.image_upload(data=i)
    image_name = str(uuid.uuid4())
    image = {'name': image_name, 'target': tgt}
    lxd.alias_create(image)

    return image_name

def delete_image(image):
    lxd = api.API()
    lxd.image_delete(image)