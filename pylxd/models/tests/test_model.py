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

from unittest import mock

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


class ChildItem(Item):
    """A fake model child class."""


class TestAttributeDict:
    def test_from_dict(self):
        a = model.AttributeDict({"foo": "bar", "baz": "bza"})
        assert a.foo == "bar"
        assert a.baz == "bza"

    def test_iterable(self):
        d = {"foo": "bar", "baz": "bza"}
        a = model.AttributeDict(d)
        assert dict(a) == d


class TestModel(testing.PyLXDTestCase):
    """Tests for pylxd.model.Model."""

    def setUp(self):
        super().setUp()

        self.add_rule(
            {
                "json": {
                    "type": "sync",
                    "metadata": {
                        "name": "an-item",
                        "age": 1000,
                        "data": {"key": "val"},
                    },
                },
                "method": "GET",
                "url": r"^http://pylxd.test/1.0/items/an-item",
            }
        )
        self.add_rule(
            {
                "json": {"type": "sync", "metadata": {}},
                "method": "put",
                "url": r"^http://pylxd.test/1.0/items/an-item",
            }
        )
        self.add_rule(
            {
                "json": {"type": "sync", "metadata": {}},
                "method": "patch",
                "url": r"^http://pylxd.test/1.0/items/an-item",
            }
        )
        self.add_rule(
            {
                "json": {"type": "sync", "metadata": {}},
                "method": "DELETE",
                "url": r"^http://pylxd.test/1.0/items/an-item",
            }
        )

    def test_init(self):
        """Initial attributes are set."""
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        self.assertEqual(self.client, item.client)
        self.assertEqual("an-item", item.name)

    @mock.patch.dict("os.environ", {"PYLXD_WARNINGS": ""})
    @mock.patch("warnings.warn")
    def test_init_warnings_once(self, mock_warn):
        with mock.patch("pylxd.models._model._seen_attribute_warnings", new=set()):
            Item(self.client, unknown="some_value")
            mock_warn.assert_called_once_with(mock.ANY)
            Item(self.client, unknown="some_value_as_well")
            mock_warn.assert_called_once_with(mock.ANY)
            Item(self.client, unknown2="some_2nd_value")
            self.assertEqual(len(mock_warn.call_args_list), 2)

    @mock.patch.dict("os.environ", {"PYLXD_WARNINGS": "none"})
    @mock.patch("warnings.warn")
    def test_init_warnings_none(self, mock_warn):
        with mock.patch("pylxd.models._model._seen_attribute_warnings", new=set()):
            Item(self.client, unknown="some_value")
            mock_warn.assert_not_called()

    @mock.patch.dict("os.environ", {"PYLXD_WARNINGS": "always"})
    @mock.patch("warnings.warn")
    def test_init_warnings_always(self, mock_warn):
        with mock.patch("pylxd.models._model._seen_attribute_warnings", new=set()):
            Item(self.client, unknown="some_value")
            mock_warn.assert_called_once_with(mock.ANY)
            Item(self.client, unknown="some_value_as_well")
            self.assertEqual(len(mock_warn.call_args_list), 2)

    @mock.patch.dict("os.environ", {"PYLXD_WARNINGS": "none"})
    def test_init_unknown_attribute(self):
        """Unknown attributes aren't set."""
        item = Item(self.client, name="an-item", nonexistent="SRSLY")

        try:
            item.nonexistent
            self.fail("item.nonexistent did not raise AttributeError")
        except AttributeError:
            pass

    def test_init_sets_attributes_on_child_class(self):
        """Ensure that .__attributes__ is set on a child class."""
        item = Item(self.client)
        child_item = ChildItem(self.client)
        self.assertEqual(len(item.__attributes__), len(child_item.__attributes__))

    def test_unknown_attribute(self):
        """Setting unknown attributes raise an exception."""

        def set_unknown_attribute():
            item = Item(self.client, name="an-item")
            item.nonexistent = "SRSLY"

        self.assertRaises(AttributeError, set_unknown_attribute)

    def test_get_unknown_attribute(self):
        """Setting unknown attributes raise an exception."""

        def get_unknown_attribute():
            item = Item(self.client, name="an-item")
            return item.nonexistent

        self.assertRaises(AttributeError, get_unknown_attribute)

    def test_unset_attribute_sync(self):
        """Reading unavailable attributes calls sync."""
        item = Item(self.client, name="an-item")

        self.assertEqual(1000, item.age)

    def test_iter(self):
        """Test models can be iterated over."""
        item = Item(self.client, name="an-item")

        self.assertDictEqual(
            {"name": "an-item", "age": 1000, "data": {"key": "val"}}, dict(item)
        )

    def test_sync(self):
        """A sync will update attributes from the server."""
        item = Item(self.client, name="an-item")

        item.sync()

        self.assertEqual(1000, item.age)

    def test_sync_dirty(self):
        """Sync will not overwrite local attribute changes."""
        item = Item(self.client, name="an-item")

        item.age = 250
        item.sync()

        self.assertEqual(250, item.age)

    def test_rollback(self):
        """Rollback resets the object from the server."""
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        item.age = 50
        item.rollback()

        self.assertEqual(1000, item.age)
        self.assertFalse(item.dirty)

    def test_int_attribute_validator(self):
        """Age is set properly to be an int."""
        item = Item(self.client)

        item.age = "100"

        self.assertEqual(100, item.age)

    def test_int_attribute_invalid(self):
        """TypeError is raised when data can't be converted to type."""

        def set_string():
            item = Item(self.client)
            item.age = "abc"

        self.assertRaises(ValueError, set_string)

    def test_dirty(self):
        """Changes mark the object as dirty."""
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        item.age = 100

        self.assertTrue(item.dirty)

    def test_not_dirty(self):
        """Changes mark the object as dirty."""
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        self.assertFalse(item.dirty)

    def test_marshall(self):
        """The object is marshalled into a dict."""
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        result = item.marshall()

        self.assertEqual({"age": 15, "data": {"key": "val"}}, result)

    def test_delete(self):
        """The object is deleted, and client is unset."""
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        item.delete()

        self.assertIsNone(item.client)

    def test_save(self):
        """Attributes are written to the server; object is marked clean."""
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        item.age = 69
        item.save()

        self.assertFalse(item.dirty)

    def test_put(self):
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        item.put({"age": 69})

        # should sync back to 1000
        self.assertEqual(item.age, 1000)

    def test_raw_put(self):
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        item.age = 55
        item.raw_put({"age": 69})

        # should sync NOT back to 1000
        self.assertEqual(item.age, 55)

    def test_put_raw_async(self):
        self.add_rule(
            {
                "json": {
                    "type": "async",
                    "metadata": {},
                    "operation": "/1.0/items/123456789",
                },
                "status_code": 202,
                "method": "put",
                "url": r"^http://pylxd.test/1.0/items/an-item$",
            }
        )
        self.add_rule(
            {
                "json": {
                    "status": "Running",
                    "status_code": 103,
                    "type": "sync",
                    "metadata": {
                        "id": "123456789",
                        "secret": "some-long-string-of-digits",
                    },
                },
                "method": "get",
                "url": r"^http://pylxd.test/1.0/operations/123456789$",
            }
        )
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                },
                "method": "get",
                "url": r"^http://pylxd.test/1.0/operations/123456789/wait$",
            }
        )
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})
        item.put({"age": 69}, wait=True)

    def test_patch(self):
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})

        item.patch({"age": 69})
        # should sync back to 1000
        self.assertEqual(item.age, 1000)

    def test_patch_raw_async(self):
        self.add_rule(
            {
                "json": {
                    "type": "async",
                    "metadata": {},
                    "operation": "/1.0/items/123456789",
                },
                "status_code": 202,
                "method": "patch",
                "url": r"^http://pylxd.test/1.0/items/an-item$",
            }
        )
        self.add_rule(
            {
                "json": {
                    "status": "Running",
                    "status_code": 103,
                    "type": "sync",
                    "metadata": {
                        "id": "123456789",
                        "secret": "some-long-string-of-digits",
                    },
                },
                "method": "get",
                "url": r"^http://pylxd.test/1.0/operations/123456789$",
            }
        )
        self.add_rule(
            {
                "json": {
                    "type": "sync",
                },
                "method": "get",
                "url": r"^http://pylxd.test/1.0/operations/123456789/wait$",
            }
        )
        item = Item(self.client, name="an-item", age=15, data={"key": "val"})
        item.patch({"age": 69}, wait=True)
