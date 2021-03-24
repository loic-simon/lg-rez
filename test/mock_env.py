import asyncio
import functools
import os


class _PatchEnv():
    def __init__(self, **kwargs):
        self.vars = kwargs

    def __enter__(self):
        self.olds = {var: os.getenv(var) for var in self.vars}
        for var, value in self.vars.items():
            if value is None:
                del os.environ[var]
            else:
                os.environ[var] = value
        return self

    def __exit__(self, etype, eval, tb):
        for var, value in self.olds.items():
            if value is None:
                del os.environ[var]
            else:
                os.environ[var] = value

    def __call__(self, func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def newfunc(*args, **kwargs):
                self.__enter__()
                try:
                    await func(*args, **kwargs)
                finally:
                    self.__exit__(None, None, None)
        else:
            @functools.wraps(func)
            def newfunc(*args, **kwargs):
                self.__enter__()
                try:
                    func(*args, **kwargs)
                finally:
                    self.__exit__(None, None, None)

        return newfunc


def patch_env(**kwargs):
    """Patch environment variables.

    Args:
        kwargs: NAME, value pair(s) of environment variables to patch,
            restored (or deleted) after. Set a variable to ``None`` to
            temporary delete it.

    Can be used as a function decorator or context manager, as for
    `unittest.mock.patch`.
    """
    return _PatchEnv(**kwargs)
