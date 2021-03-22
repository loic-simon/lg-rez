import unittest

from lgrez import config
from lgrez.blocs import ready_check


class TestConfigGetReady(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.config ready checks."""

    async def test_variables_notready(self):
        """Unit tests for config variables."""

        with self.assertRaises(ready_check.NotReadyError):
            config.guild
        with self.assertRaises(ready_check.NotReadyError):
            config.bot
        with self.assertRaises(ready_check.NotReadyError):
            config.loop
        with self.assertRaises(ready_check.NotReadyError):
            config.engine
        with self.assertRaises(ready_check.NotReadyError):
            config.session

        with self.assertRaises(ready_check.NotReadyError):
            config.Role.mj

        with self.assertRaises(ready_check.NotReadyError):
            config.Channel.logs

        with self.assertRaises(ready_check.NotReadyError):
            config.Emoji.bucher


    async def test___getattr__(self):
        """Unit tests for accessing config variables."""
        __getattr__ = config.__getattr__

        with self.assertRaises(ready_check.NotReadyError):
            __getattr__("guild")

        with self.assertRaises(AttributeError):
            __getattr__("bzzt")
