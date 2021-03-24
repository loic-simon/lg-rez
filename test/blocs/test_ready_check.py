import unittest
from unittest import mock

from lgrez.blocs import ready_check



class Test_RCDict(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.ready_check._RCDict class."""

    def test___init__(self):
        """Unit tests for _RCDict.__init__ method."""
        # def __init__(self, _is_ready=None, _class=None, **kwargs)
        __init__ = ready_check._RCDict.__init__

        # simplest
        slf = ready_check._RCDict.__new__(ready_check._RCDict)
        __init__(slf)
        self.assertEqual(slf._errormsg, "No attribute")
        self.assertTrue(slf._is_ready(False))
        self.assertTrue(slf._is_ready(2))
        self.assertTrue(slf._is_ready("a"))
        self.assertFalse(slf._is_ready(None))

        # simple
        slf = ready_check._RCDict.__new__(ready_check._RCDict)
        dic = {str(i): mock.Mock() for i in range(5)}
        __init__(slf, **dic)
        for i in range(5):
            self.assertEqual(slf[str(i)], dic[str(i)])
        self.assertEqual(slf._errormsg, "No attribute")
        self.assertTrue(slf._is_ready(False))
        self.assertTrue(slf._is_ready(2))
        self.assertTrue(slf._is_ready("a"))
        self.assertFalse(slf._is_ready(None))

        # custom _is_ready
        slf = ready_check._RCDict.__new__(ready_check._RCDict)
        dic = {str(i): mock.Mock() for i in range(5)}
        _is_ready = mock.Mock()
        __init__(slf, **dic, _is_ready=_is_ready)
        for i in range(5):
            self.assertEqual(slf[str(i)], dic[str(i)])
        self.assertEqual(slf._errormsg, "No attribute")
        self.assertEqual(slf._is_ready, _is_ready)

        # custom _is_ready and _class
        slf = ready_check._RCDict.__new__(ready_check._RCDict)
        dic = {str(i): mock.Mock() for i in range(5)}
        _is_ready = mock.Mock()
        _class = mock.Mock(__qualname__="zbrrr")
        __init__(slf, **dic, _is_ready=_is_ready, _class=_class)
        for i in range(5):
            self.assertEqual(slf[str(i)], dic[str(i)])
        self.assertIn("zbrrr", slf._errormsg)
        self.assertEqual(slf._is_ready, _is_ready)


    def test__get_raw(self):
        """Unit tests for _RCDict._get_raw method."""
        # def _get_raw(self, name)
        _get_raw = ready_check._RCDict._get_raw
        slf = ready_check._RCDict(a=1, b=2)
        # existing
        val = _get_raw(slf, "a")
        self.assertEqual(val, 1)
        # non-existing
        with self.assertRaises(AttributeError):
            _get_raw(slf, "c")


    def test___getitem__(self):
        """Unit tests for _RCDict.__getitem__ method."""
        # def __getitem__(self, name)
        __getitem__ = ready_check._RCDict.__getitem__
        slf = mock.Mock(ready_check._RCDict, _get_raw=mock.Mock(),
                        _is_ready=mock.Mock())
        # inexistant
        slf._get_raw.side_effect = AttributeError
        with self.assertRaises(AttributeError):
            __getitem__(slf, "c")           # c -> "ccc" < 4
        # ready
        slf._get_raw.side_effect = lambda name: name*3
        slf._is_ready.side_effect = lambda name: len(name) > 4
        val = __getitem__(slf, "ro")
        self.assertEqual(val, "rororo")     # "rororo" > 4
        # not ready
        with self.assertRaises(ready_check.NotReadyError):
            __getitem__(slf, "c")           # c -> "ccc" < 4



class Test_RCMeta(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.ready_check._RCMeta class."""

    def test___new__(self):
        """Unit tests for _RCMeta.__new__ method."""
        # def __new__(metacls, name, bases, dict, check=None, check_type=None)
        __new__ = ready_check._RCMeta.__new__

        # simple
        result = __new__(ready_check._RCMeta, "ah", (), {})
        self.assertTrue(isinstance(result, ready_check._RCMeta))
        self.assertEqual(result.__name__, "ah")

        # complex
        result = __new__(ready_check._RCMeta, "ah", (int,), {"_a": 1, "b": 2},
                         check="fsodfpsd", check_type=dict)
        self.assertTrue(isinstance(result, ready_check._RCMeta))
        self.assertEqual(result.__name__, "ah")
        self.assertEqual(result.__bases__, (int,))
        self.assertIn(("_a", 1), result.__dict__.items())
        self.assertNotIn(("b", 2), result.__dict__.items())   # b public!


    @mock.patch("lgrez.blocs.ready_check._RCDict")
    def test___init__(self, rdc_patch):
        """Unit tests for _RCMeta.__init__ method."""
        # def __init__(cls, name, bases, dict, check=None, check_type=None)
        __new__ = ready_check._RCMeta.__new__
        __init__ = ready_check._RCMeta.__init__

        # simple
        cls = __new__(ready_check._RCMeta, "ah", (), {})
        __init__(cls, "ah", (), {})
        rdc_patch.assert_called_once_with(_is_ready=None, _class=cls)
        rdc_patch.reset_mock()

        # with dict and check
        check = mock.Mock()
        cls = __new__(ready_check._RCMeta, "ah", (int,), {"_a": 1, "b": 2},
                      check=check)
        __init__(cls, "ah", (int,), {"_a": 1, "b": 2}, check=check)
        self.assertIn(("_a", 1), cls.__dict__.items())
        self.assertNotIn(("b", 2), cls.__dict__.items())
        rdc_patch.assert_called_once_with(_is_ready=check, _class=cls, b=2)
                                          # called with public only
        self.assertEqual(cls._rc_dict, rdc_patch.return_value)
        rdc_patch.reset_mock()

        # with dict and check_type
        class Oui:
            pass
        cls = __new__(ready_check._RCMeta, "ah", (int,), {"_a": 1, "b": 2},
                      check_type=Oui)
        __init__(cls, "ah", (int,), {"_a": 1, "b": 2}, check_type=Oui)
        self.assertIn(("_a", 1), cls.__dict__.items())
        self.assertNotIn(("b", 2), cls.__dict__.items())
        rdc_patch.assert_called_once_with(_is_ready=mock.ANY, _class=cls, b=2)
                                          # called with public only
        self.assertEqual(cls._rc_dict, rdc_patch.return_value)
        _is_ready = rdc_patch.call_args.kwargs["_is_ready"]
        self.assertFalse(_is_ready(1))
        self.assertFalse(_is_ready("a"))
        self.assertFalse(_is_ready(None))
        self.assertTrue(_is_ready(Oui()))
        rdc_patch.reset_mock()

        # with dict, check and check_type
        class Oui(str):
            pass
        cls = __new__(ready_check._RCMeta, "ah", (int,), {"_a": 1, "b": 2},
                      check=lambda oui: len(oui) > 3, check_type=Oui)
        __init__(cls, "ah", (int,), {"_a": 1, "b": 2},
                 check=lambda oui: len(oui) > 3, check_type=Oui)
        self.assertIn(("_a", 1), cls.__dict__.items())
        self.assertNotIn(("b", 2), cls.__dict__.items())
        rdc_patch.assert_called_once_with(_is_ready=mock.ANY, _class=cls, b=2)
                                          # called with public only
        self.assertEqual(cls._rc_dict, rdc_patch.return_value)
        _is_ready = rdc_patch.call_args.kwargs["_is_ready"]
        self.assertFalse(_is_ready(1))
        self.assertFalse(_is_ready("a"))
        self.assertFalse(_is_ready("aaaaaaaa"))
        self.assertFalse(_is_ready(None))
        self.assertFalse(_is_ready(Oui()))
        self.assertFalse(_is_ready(Oui("aa")))
        self.assertTrue(_is_ready(Oui("aaaa")))
        rdc_patch.reset_mock()


    def test___getattr__(self):
        """Unit tests for _RCMeta.__getattr__ method."""
        # def __getattr__(cls, name)
        __getattr__ = ready_check._RCMeta.__getattr__
        cls = mock.Mock(_rc_dict={"a": 1, "b": 2})
        # private
        with self.assertRaises(AttributeError):
            __getattr__(cls, "_c")
        # not found
        with self.assertRaises(KeyError):
            __getattr__(cls, "d")
        # found
        result = __getattr__(cls, "a")
        self.assertEqual(result, 1)

    def test___setattr__(self):
        """Unit tests for _RCMeta.__setattr__ method."""
        # def __setattr__(cls, name, value)
        __setattr__ = ready_check._RCMeta.__setattr__
        cls = mock.Mock(_rc_dict={"a": 1, "b": 2})
        # private -> setattr
        with self.assertRaises(TypeError):
            # try to setattr, cant 'cause of mocking
            __setattr__(cls, "_c", "oh")
        # public -> _rc_dict
        result = __setattr__(cls, "a", "eh")
        self.assertNotEqual(cls.a, "eh")
        self.assertEqual(cls._rc_dict["a"], "eh")

    def test___delattr__(self):
        """Unit tests for _RCMeta.__delattr__ method."""
        # def __delattr__(cls, name)
        __delattr__ = ready_check._RCMeta.__delattr__
        cls = mock.Mock(_rc_dict={"a": 1, "b": 2})
        # private -> delattr
        with self.assertRaises(TypeError):
            # try to delattr, cant 'cause of mocking
            __delattr__(cls, "_c")
        # public -> _rc_dict
        __delattr__(cls, "a")
        self.assertNotIn("a", cls._rc_dict)

    def test___iter__(self):
        """Unit tests for _RCMeta.__iter__ method."""
        # def __iter__(cls)
        __iter__ = ready_check._RCMeta.__iter__
        cls = mock.Mock(_rc_dict={"a": 1, "b": 2})
        result = __iter__(cls)
        self.assertEqual(list(result), list(iter(cls._rc_dict)))

    def test_get_raw(self):
        """Unit tests for _RCMeta.get_raw method."""
        # def get_raw(cls, attr)
        get_raw = ready_check._RCMeta.get_raw
        cls = mock.Mock(_rc_dict=mock.Mock(_get_raw=mock.Mock()))
        attr = mock.Mock()
        result = get_raw(cls, attr)
        cls._rc_dict._get_raw.assert_called_once_with(attr)
        self.assertEqual(result, cls._rc_dict._get_raw.return_value)
