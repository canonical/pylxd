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


class ContainerUnDefined(Exception):
    pass


class UntrustedHost(Exception):
    pass


class ContainerProfileCreateFail(Exception):
    pass


class ContainerProfileDeleteFail(Exception):
    pass


class ImageInvalidSize(Exception):
    pass


class APIError(Exception):

    def __init__(self, error, status_code):
        msg = 'Error %s - %s.' % (status_code, error)
        Exception.__init__(self, msg)
        self.status_code = status_code
        self.error = error
