import unittest
from unittest import mock

from lgrez.blocs import env



class TestEnv(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.env module."""

    @mock.patch("os.getenv")
    def test_load(self, ge_patch):
        """Unit tests for env.load function."""
        # def load(VAR_NAME)
        load = env.load
        # existing
        ge_patch.return_value = "12345"
        VAR_NAME = "OUI"
        result = load(VAR_NAME)
        ge_patch.assert_called_once_with("OUI")
        ge_patch.reset_mock()
        self.assertEqual(result, "12345")
        # non existing
        ge_patch.return_value = None
        VAR_NAME = "NON"
        with self.assertRaises(RuntimeError):
            load(VAR_NAME)
        ge_patch.assert_called_once_with("NON")
