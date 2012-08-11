#   Copyright 2012 OpenStack LLC.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import datetime
import webob

from cinder import exception
from cinder import flags
from cinder import test
#from cinder import utils
from cinder.api.openstack.volume.contrib import create_volume_ext
#from cinder.openstack.common import jsonutils
from cinder.openstack.common.rpc import common as rpc_common
from cinder.tests.api.openstack import fakes
from cinder.tests.image import fake as fake_image
from cinder.volume import api as volume_api


FLAGS = flags.FLAGS


def stub_volume_get(self, context, volume_id):
    vol = fakes.stub_volume(volume_id)
    if volume_id == 5:
        vol['status'] = 'in-use'
    else:
        vol['status'] = 'available'
    return vol


class CreateVolumeExtensionTest(test.TestCase):
    def setUp(self):
        super(CreateVolumeExtensionTest, self).setUp()
        fake_image.stub_out_image_service(self.stubs)
        self.controller = create_volume_ext.CreateVolumeExtensionController()

        self.stubs.Set(volume_api.API, 'get', stub_volume_get)
        self.stubs.Set(volume_api.API, '_create',
                       fakes.stub_volume_create_from_image)
        self.vol = {
               "display_name": "test_vol",
               "display_description": "test_description",
               "size": 1,
               "imageRef": "c905cedb-7281-47e4-8a62-f26bc5fc4c77"
              }
        self.body = {"volume": self.vol}

    def test_create_volume_extension(self):
        req = fakes.HTTPRequest.blank(
                                '/v1/tenant1/os-create-volume-from-image')
        res_dict = self.controller.create(req, self.body)
        expected = {'volume': {
                        'status': 'creating',
                        'display_name': self.vol['display_name'],
                        'availability_zone': 'cinder',
                        'created_at': datetime.datetime(1, 1, 1, 1, 1, 1),
                        'display_description': self.vol['display_description'],
                        'image_id': self.vol['imageRef'],
                        'volume_type': 'vol_type_name',
                        'metadata': {},
                        'id': '1',
                        'size': self.vol['size']
                         }
                   }

        self.assertDictMatch(res_dict, expected)

    def test_create_volume_extension_imagenotfound(self):
        def stub_create_volume_from_image_raise(self, *args, **kwargs):
            raise exception.ImageNotFound

        self.stubs.Set(volume_api.API,
                       "create_volume_from_image",
                       stub_create_volume_from_image_raise)
        req = fakes.HTTPRequest.blank(
                                '/v1/tenant1/os-create-volume-from-image')
        self.assertRaises(webob.exc.HTTPNotFound,
                          self.controller.create,
                          req,
                          self.body)

    def test_create_volume_extension_imagenotauthorized(self):
        def stub_create_volume_from_image_raise(self, *args, **kwargs):
            raise exception.ImageNotAuthorized
        self.stubs.Set(volume_api.API,
                       "create_volume_from_image",
                       stub_create_volume_from_image_raise)
        req = fakes.HTTPRequest.blank(
                                '/v1/tenant1/os-create-volume-from-image')
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.create,
                          req,
                          self.body)

    def test_create_volume_extension_invalid(self):
        def stub_create_volume_from_image_raise(self, *args, **kwargs):
            raise exception.InvalidVolume
        self.stubs.Set(volume_api.API,
                       "create_volume_from_image",
                       stub_create_volume_from_image_raise)
        req = fakes.HTTPRequest.blank(
                                '/v1/tenant1/os-create-volume-from-image')
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.create,
                          req,
                          self.body)

    def test_create_volume_extension_remoteerror(self):
        def stub_create_volume_from_image_raise(self, *args, **kwargs):
            raise rpc_common.RemoteError
        self.stubs.Set(volume_api.API,
                       "create_volume_from_image",
                       stub_create_volume_from_image_raise)

        req = fakes.HTTPRequest.blank(
                                '/v1/tenant1/os-create-volume-from-image')
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.create,
                          req,
                          self.body)

    def test_create_volume_extension_image_ref_unspecified(self):
        req = fakes.HTTPRequest.blank(
                                '/v1/tenant1/os-create-volume-from-image')
        body = self.body
        del(body['volume']['imageRef'])
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.create,
                          req,
                          body)

    def test_create_volume_extension_vol_size_unspecified(self):
        req = fakes.HTTPRequest.blank(
                                '/v1/tenant1/os-create-volume-from-image')
        body = self.body
        del(body['volume']['size'])
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.create,
                          req,
                          body)

    def test_create_volume_ext_image_size_greater_than_vol_size(self):
        req = fakes.HTTPRequest.blank(
                                '/v1/tenant1/os-create-volume-from-image')
        vol = {
               "display_name": "test_vol",
               "display_description": "test_description",
               "size": 1,
               "imageRef": "a2459075-d96c-40d5-893e-577ff92e721c"
              }
        body = {"volume": vol}
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.create,
                          req,
                          body)
