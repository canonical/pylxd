from pylxd import operation
from pylxd.tests import testing


class TestOperation(testing.PyLXDTestCase):
    """Tests for pylxd.operation.Operation."""

    def test_get(self):
        """Return an operation."""
        name = 'operation-abc'

        an_operation = operation.Operation.get(self.client, name)

        self.assertEqual(name, an_operation.id)

    def test_get_full_path(self):
        """Return an operation even if the full path is specified."""
        name = '/1.0/operations/operation-abc'

        an_operation = operation.Operation.get(self.client, name)

        self.assertEqual('operation-abc', an_operation.id)
