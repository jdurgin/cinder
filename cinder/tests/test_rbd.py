# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Josh Durgin
# All Rights Reserved.
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

from cinder import exception
from cinder.openstack.common import log as logging
from cinder import test
from cinder.volume.driver import RBDDriver

LOG = logging.getLogger(__name__)


class RBDTestCase(test.TestCase):

    def setUp(self):
        super(RBDTestCase, self).setUp()

        def fake_execute(*args):
            pass
        self.driver = RBDDriver(execute=fake_execute)

    def test_good_locations(self):
        locations = [
            'rbd://fsid/pool/image/snap',
            'rbd://%2F/%2F/%2F/%2F',
            ]
        map(self.driver._parse_location, locations)

    def test_bad_locations(self):
        locations = [
            'rbd://image',
            'http://path/to/somewhere/else',
            'rbd://image/extra',
            'rbd://image/',
            'rbd://fsid/pool/image/',
            'rbd://fsid/pool/image/snap/',
            'rbd://///',
            ]
        for loc in locations:
            self.assertRaises(exception.ImageUnacceptable,
                              self.driver._parse_location,
                              loc)
            self.assertFalse(self.driver.is_cloneable(loc))

    def test_cloneable(self):
        self.stubs.Set(self.driver, '_get_fsid', lambda: 'abc')
        location = 'rbd://abc/pool/image/snap'
        self.assertTrue(self.driver.is_cloneable(location))

    def test_uncloneable_different_fsid(self):
        self.stubs.Set(self.driver, '_get_fsid', lambda: 'abc')
        location = 'rbd://def/pool/image/snap'
        self.assertFalse(self.driver.is_cloneable(location))

    def test_uncloneable_unreadable(self):
        def fake_exc(*args):
            raise exception.ProcessExecutionError()
        self.stubs.Set(self.driver, '_get_fsid', lambda: 'abc')
        self.stubs.Set(self.driver, '_execute', fake_exc)
        location = 'rbd://abc/pool/image/snap'
        self.assertFalse(self.driver.is_cloneable(location))
