# Copyright (c) 2016 Canonical Ltd
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
from pylxd.models import _model as model
from pylxd.tests import testing


class Item(model.Model):
    """A fake model."""
    name = model.Attribute(readonly=True)
    age = model.Attribute(int)
    data = model.Attribute()

    @property
    def api(self):
        return self.client.api.items[self.name]


class TestModel(testing.PyLXDTestCase):
    """Tests for pylxd.model.Model."""

    def setUp(self):
        super(TestModel, self).setUp()

        self.add_rule({
            'json': {
                'type': 'sync',
                'metadata': {
                    'name': 'an-item',
                    'age': 1000,
                    'data': {'key': 'val'},
                }
            },
            'method': 'GET',
            'url': r'^http://pylxd.test/1.0/items/an-item',
        })
        self.add_rule({
            'json': {
                'type': 'sync',
                'metadata': {}
            },
            'method': 'PUT',
            'url': r'^http://pylxd.test/1.0/items/an-item',
        })
        self.add_rule({
            'json': {
                'type': 'sync',
                'metadata': {}
            },
            'method': 'DELETE',
            'url': r'^http://pylxd.test/1.0/items/an-item',
        })

    def test_init(self):
        """Initial attributes are set."""
        item = Item(self.client, name='an-item', age=15, data={'key': 'val'})

        self.assertEqual(self.client, item.client)
        self.assertEqual('an-item', item.name)

    def test_init_unknown_attribute(self):
        """Unknown attributes aren't set."""
        item = Item(self.client, name='an-item', nonexistent='SRSLY')

        try:
            item.nonexistent
            self.fail('item.nonexistent did not raise AttributeError')
        except AttributeError:
            pass

    def test_unknown_attribute(self):
        """Setting unknown attributes raise an exception."""
        def set_unknown_attribute():
            item = Item(self.client, name='an-item')
            item.nonexistent = 'SRSLY'
        self.assertRaises(AttributeError, set_unknown_attribute)

    def test_get_unknown_attribute(self):
        """Setting unknown attributes raise an exception."""
        def get_unknown_attribute():
            item = Item(self.client, name='an-item')
            return item.nonexistent
        self.assertRaises(AttributeError, get_unknown_attribute)

    def test_unset_attribute_sync(self):
        """Reading unavailable attributes calls sync."""
        item = Item(self.client, name='an-item')

        self.assertEqual(1000, item.age)

    def test_sync(self):
        """A sync will update attributes from the server."""
        item = Item(self.client, name='an-item')

        item.sync()

        self.assertEqual(1000, item.age)

    def test_sync_dirty(self):
        """Sync will not overwrite local attribute changes."""
        item = Item(self.client, name='an-item')

        item.age = 250
        item.sync()

        self.assertEqual(250, item.age)

    def test_rollback(self):
        """Rollback resets the object from the server."""
        item = Item(self.client, name='an-item', age=15, data={'key': 'val'})

        item.age = 50
        item.rollback()

        self.assertEqual(1000, item.age)
        self.assertFalse(item.dirty)

    def test_int_attribute_validator(self):
        """Age is set properly to be an int."""
        item = Item(self.client)

        item.age = '100'

        self.assertEqual(100, item.age)

    def test_int_attribute_invalid(self):
        """TypeError is raised when data can't be converted to type."""
        def set_string():
            item = Item(self.client)
            item.age = 'abc'

        self.assertRaises(ValueError, set_string)

    def test_dirty(self):
        """Changes mark the object as dirty."""
        item = Item(self.client, name='an-item', age=15, data={'key': 'val'})

        item.age = 100

        self.assertTrue(item.dirty)

    def test_not_dirty(self):
        """Changes mark the object as dirty."""
        item = Item(self.client, name='an-item', age=15, data={'key': 'val'})

        self.assertFalse(item.dirty)

    def test_marshall(self):
        """The object is marshalled into a dict."""
        item = Item(self.client, name='an-item', age=15, data={'key': 'val'})

        result = item.marshall()

        self.assertEqual({'age': 15, 'data': {'key': 'val'}}, result)

    def test_delete(self):
        """The object is deleted, and client is unset."""
        item = Item(self.client, name='an-item', age=15, data={'key': 'val'})

        item.delete()

        self.assertIsNone(item.client)

    def test_save(self):
        """Attributes are written to the server; object is marked clean."""
        item = Item(self.client, name='an-item', age=15, data={'key': 'val'})

        item.age = 69
        item.save()

        self.assertFalse(item.dirty)
