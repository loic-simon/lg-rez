import unittest
from unittest import mock

from lgrez.blocs import gsheets
from test import mock_env



class TestModif(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.gsheets.Modif class."""

    def test___init__(self):
        """Unit tests for Modif.__init__ method."""
        # def __init__(self, row, column, val)
        __init__ = gsheets.Modif.__init__
        # unique case
        slf = mock.Mock(gsheets.Modif)
        row, column, val = mock.Mock(), mock.Mock(), mock.Mock()
        __init__(slf, row, column, val)
        self.assertEqual(slf.row, row)
        self.assertEqual(slf.column, column)
        self.assertEqual(slf.val, val)

    def test___repr__(self):
        """Unit tests for Modif.__repr__ method."""
        # def __repr__(self)
        __repr__ = gsheets.Modif.__repr__
        # unique case
        slf = mock.Mock(gsheets.Modif, row=12, column=2, val="hohoho")
        res = __repr__(slf)
        self.assertEqual(res, f"<gsheets.Modif: (12, 2) = 'hohoho'>")

    def test___eq__(self):
        """Unit tests for Modif.__eq__ method."""
        # def __eq__(self, other)
        __eq__ = gsheets.Modif.__eq__
        slf = mock.Mock(gsheets.Modif, row=12, column=2, val="hohoho")
        # not same type
        oth0 = "oh"
        self.assertIs(__eq__(slf, oth0), NotImplemented)
        # not equal
        oth1 = mock.Mock(gsheets.Modif, row=11, column=2, val="hohoho")
        oth2 = mock.Mock(gsheets.Modif, row=12, column=1, val="hohoho")
        oth3 = mock.Mock(gsheets.Modif, row=12, column=2, val="hahaha")
        self.assertFalse(__eq__(slf, oth1))
        self.assertFalse(__eq__(slf, oth2))
        self.assertFalse(__eq__(slf, oth3))
        # equal
        oth4 = mock.Mock(gsheets.Modif, row=12, column=2, val="hohoho")
        self.assertTrue(__eq__(slf, oth4))
        self.assertTrue(__eq__(slf, slf))

    def test___hash__(self):
        """Unit tests for Modif.__hash__ method."""
        # def __hash__(self)
        __hash__ = gsheets.Modif.__hash__
        slf = mock.Mock(gsheets.Modif, row=12, column=2, val="hohoho")
        # not same type
        oth0 = "oh"
        self.assertNotEqual(__hash__(slf), hash(oth0))
        # not equal
        oth1 = mock.Mock(gsheets.Modif, row=11, column=2, val="hohoho")
        oth2 = mock.Mock(gsheets.Modif, row=12, column=1, val="hohoho")
        oth3 = mock.Mock(gsheets.Modif, row=12, column=2, val="hahaha")
        self.assertNotEqual(__hash__(slf), __hash__(oth1))
        self.assertNotEqual(__hash__(slf), __hash__(oth2))
        self.assertNotEqual(__hash__(slf), __hash__(oth3))
        # equal
        oth4 = mock.Mock(gsheets.Modif, row=12, column=2, val="hohoho")
        self.assertEqual(__hash__(slf), __hash__(oth4))
        self.assertEqual(__hash__(slf), __hash__(slf))


class TestGsheetsFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.gsheets functions."""

    @mock_env.patch_env(LGREZ_GCP_CREDENTIALS='{"st": 2, "ls": [], "dc": {}}')
    @mock.patch("gspread.authorize")
    @mock.patch("oauth2client.service_account.ServiceAccountCredentials")
    def test_connect(self, sac_patch, auth_patch):
        """Unit tests for gsheets.connect function."""
        # def connect(key)
        connect = gsheets.connect
        # unique case
        key = mock.Mock()
        wb = connect(key)
        sac_patch.from_json_keyfile_dict.assert_called_once_with(
            {"st": 2, "ls": [], "dc": {}},
            ['https://spreadsheets.google.com/feeds']
        )
        auth_patch.assert_called_once_with(
            sac_patch.from_json_keyfile_dict.return_value)
        client = auth_patch.return_value
        client.open_by_key.assert_called_once_with(key)
        self.assertEqual(wb, client.open_by_key.return_value)
