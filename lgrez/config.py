"""config - variables globales"""

import discord


class NotReadyError(RuntimeError):
    """Raised when an attribute is accessed before it is ready. Inherits from :exc:`RuntimeError`."""
    pass


class _RCDict(dict):
    def __init__(self, *args, _is_ready=None, _class=None, **kwargs):
        super().__init__(*args, **kwargs)
        if _is_ready is None:
            _is_ready = lambda item: item is not None
        self._is_ready = _is_ready
        if _class:
            self._errormsg = f"'{_class.__qualname__}' has no attribute"
        else:
            self._errormsg = f"No attribute"

    def __getitem__(self, name):
        try:
            val = super().__getitem__(name)
        except KeyError:
            raise AttributeError(f"{self._errormsg} '{name}'") from None

        ready = self._is_ready(val)
        if not ready:
            raise NotReadyError(f"'{name}' is not ready yet!")
        return val


class _RCMeta(type):
    def __new__(metacls, name, bases, dict, check=None, check_type=None):
        # register directly private/magic names only
        _ps_dict = {name: dict[name] for name in dict if name.startswith('_')}
        return super().__new__(metacls, name, bases, _ps_dict)

    def __init__(cls, name, bases, dict, check=None, check_type=None):
        _ps_dict = {name: dict[name] for name in dict if name.startswith('_')}
        super().__init__(name, bases, _ps_dict)
        if check_type:
            if check:
                check = lambda item: isinstance(item, check_type) and check(item)
            else:
                check = lambda item: isinstance(item, check_type)
        cls._dict = _RCDict(_is_ready=check, _class=cls, **dict)

    def __getattr__(cls, name):
        if name.startswith('_'):
            # private/magic name: do not search in ._dict (infinite recursion)
            raise AttributeError(f"'{cls.__qualname__}' has no attribute '{name}'")
        return cls._dict[name]

    def __setattr__(cls, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            cls._dict[name] = value

    def __delattr__(cls, name):
        try:
            super().__delattr__(name)
        except AttributeError:
            del cls._dict[name]


class ReadyCheck(metaclass=_RCMeta):
    """Proxy class to prevent accessing not initialised objects.

    When accessing a class attribute, this class:
        - returns its value (classic behavior) if it is evaluated
          *ready* (see below);
        - raises a :exc:`NotReadyError` exception otherwise.

    Subclass this class to implment readiness check on class attributes
    and define "readiness" as needed. By default, attributes are
    considered *not ready* only if their value is ``None``::

        class NotNone(ReadyCheck):
            a = None            # NotNone.a will raise a NotReadyError
            b = <any object>    # NotNone.b will be the given object

    Use ``check_type`` class-definition argument to define readiness based
    on attributes types (using :func:`isinstance()`)::

        class MustBeList(ReadyCheck, check_type=list):
            a = "TDB"           # MustBeList.a will raise a NotReadyError
            b = [1, 2, 3]       # MustBeList.b will be the given list

    Use ``check`` class-definition argument to define custom readiness
    check (``value -> bool`` function)::

        class MustBePositive(ReadyCheck, check=lambda val: val > 0):
            a = 0               # MustBePositive.a will raise a NotReadyError
            b = 37              # MustBePositive.b will be 37

    If both arguments are provided, attribute type will be checked first
    and custom check will be called only for suitable attributes.

    Attributes can be added, modified and deleted the normal way.
    Readiness is evaluated at access time, so changing an attribute's
    value will change its readiness with no aditionnal work required.

    Note:
        Attributes whose name start with ``'_'`` (private and magic attributes)
        are not affected and will be returned even if not ready.

    Warning:
        Class derivating from this class are not meant to be instantiated.
        Due to the checking proxy on class attributes, instances will not
        see attributes defined at class level, and attributes defined in
        ``__init__`` or after construction will **not** be ready-checked.

        This class defines no attributes or methods, but relies on a custom
        metaclass: you will not be able to create mixin classes from this
        one and a custom-metaclass one.
    """
    pass


class _ModuleGlobals(ReadyCheck):
    """Module attributes with not-None ReadyCheck, returned by __getattr__

    (documented directly in api.rst)
    """
    guild = None
    bot = None
    engine = None
    session = None

def __getattr__(attr):
    try:
        return getattr(_ModuleGlobals, attr)
    except AttributeError:
        raise AttributeError(f"module '{__name__}' has no attribute '{attr}'") from None
