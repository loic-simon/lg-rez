import unittest
from unittest import mock

import discord

from lgrez import config
from lgrez.blocs import one_command
from test import mock_discord



class Test_Bypasser(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.one_command._Bypasser class."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    def test___init__(self):
        """Unit tests for _Bypasser.__init__ method."""
        # def __init__(self, ctx)
        __init__ = one_command._Bypasser.__init__
        # unique case
        slf = mock.Mock(one_command._Bypasser)
        ctx = mock.Mock()
        __init__(slf, ctx)
        self.assertEqual(slf.ctx, ctx)

    def test___enter__(self):
        """Unit tests for _Bypasser.__enter__ method."""
        # def __enter__(self)
        __enter__ = one_command._Bypasser.__enter__
        # unique case
        slf = mock.Mock(one_command._Bypasser, ctx=mock.Mock())
        res = __enter__(slf)
        config.bot.in_command.remove.assert_called_once_with(
            slf.ctx.channel.id)
        self.assertEqual(res, slf)

    def test___exit__(self):
        """Unit tests for _Bypasser.__exit__ method."""
        # def __exit__(self, exc_type, exc, tb)
        __exit__ = one_command._Bypasser.__exit__
        # unique case
        slf = mock.Mock(one_command._Bypasser, ctx=mock.Mock())
        res = __exit__(slf, mock.Mock(), mock.Mock(), mock.Mock())
        config.bot.in_command.append.assert_called_once_with(
            slf.ctx.channel.id)


class TestOneCommandFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.one_command functions."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    @mock.patch("lgrez.blocs.one_command._Bypasser")
    def test_bypass(self, bp_class):
        """Unit tests for one_command.bypass function."""
        # def bypass(ctx)
        bypass = one_command.bypass
        # unique case
        slf = mock.Mock()
        ret = bypass(slf)
        bp_class.assert_called_once_with(slf)
        self.assertEqual(ret, bp_class.return_value)


    @mock.patch("asyncio.sleep")
    async def test_not_in_command(self, zzz_patch):
        """Unit tests for one_command.not_in_command function."""
        # async def not_in_command(ctx)
        not_in_command = one_command.not_in_command
        one_command.exempted = ["ah", "oh"]
        config.bot.in_command = [14, 15]

        # exempted
        ctx = mock.Mock(command="ah")
        res = await not_in_command(ctx)
        ctx.send.assert_not_called()
        zzz_patch.assert_not_called()
        self.assertEqual(res, True)

        # channel free
        ctx = mock.Mock(command="eh")
        ctx.channel.id = 13             # not in command
        res = await not_in_command(ctx)
        ctx.send.assert_not_called()
        zzz_patch.assert_not_called()
        self.assertEqual(res, True)

        # no freeing
        ctx = mock.Mock(command="eh", send=mock.AsyncMock())
        ctx.channel.id = 14             # in command
        with self.assertRaises(one_command.AlreadyInCommand):
            await not_in_command(ctx)
        ctx.send.assert_called_once_with(config.stop_keywords[0],
                                         delete_after=0)
        zzz_patch.assert_called_once_with(1)
        self.assertIn(14, config.bot.in_command)
        zzz_patch.reset_mock()

        # freeing!
        ctx = mock.Mock(command="eh", send=mock.AsyncMock())
        ctx.channel.id = 14             # in command
        zzz_patch.side_effect = lambda v: config.bot.in_command.remove(14)
        res = await not_in_command(ctx)
        ctx.send.assert_called_once_with(config.stop_keywords[0],
                                         delete_after=0)
        zzz_patch.assert_called_once_with(1)
        self.assertNotIn(14, config.bot.in_command)
        self.assertEqual(res, True)


    async def test_add_to_in_command(self):
        """Unit tests for one_command.add_to_in_command function."""
        # async def add_to_in_command(ctx)
        add_to_in_command = one_command.add_to_in_command
        one_command.exempted = ["ah", "oh"]
        config.bot.in_command = [14, 15]

        # exempted
        ctx = mock.Mock(command="ah")
        ctx.channel.id = 13             # not in command
        await add_to_in_command(ctx)
        self.assertNotIn(13, config.bot.in_command)     # nothing changed

        # webhook
        ctx = mock.Mock(command="eh")
        ctx.channel.id = 13             # not in command
        await add_to_in_command(ctx)
        self.assertNotIn(13, config.bot.in_command)     # nothing changed

        # other
        ctx = mock.Mock(command="eh")
        ctx.channel.id = 13             # not in command
        ctx.message.webhook_id = None
        await add_to_in_command(ctx)
        self.assertIn(13, config.bot.in_command)        # appended


    @mock.patch("asyncio.sleep")
    async def test_remove_from_in_command(self, zzz_patch):
        """Unit tests for one_command.remove_from_in_command function."""
        # async def remove_from_in_command(ctx)
        remove_from_in_command = one_command.remove_from_in_command
        one_command.exempted = ["ah", "oh"]
        config.bot.in_command = [14, 15]

        # in command but exempted
        ctx = mock.Mock(command="ah")
        ctx.channel.id = 14             # not in command
        await remove_from_in_command(ctx)
        zzz_patch.assert_called_once_with(0.1)
        self.assertIn(14, config.bot.in_command)        # nothing changed
        zzz_patch.reset_mock()

        # not in command
        ctx = mock.Mock(command="eh")
        ctx.channel.id = 13             # not in command
        await remove_from_in_command(ctx)
        zzz_patch.assert_called_once_with(0.1)
        self.assertNotIn(13, config.bot.in_command)     # nothing changed
        zzz_patch.reset_mock()

        # other
        ctx = mock.Mock(command="eh")
        ctx.channel.id = 14             # not in command
        await remove_from_in_command(ctx)
        zzz_patch.assert_called_once_with(0.1)
        self.assertNotIn(14, config.bot.in_command)     # removed


    async def test_do_not_limit(self):
        """Unit tests for one_command.do_not_limit function."""
        # def do_not_limit(command)
        do_not_limit = one_command.do_not_limit
        one_command.exempted = ["ah", "oh"]

        # bad type
        command = mock.Mock()
        with self.assertRaises(TypeError):
            do_not_limit(command)

        # okay
        command = mock.Mock(discord.ext.commands.Command)
        res = do_not_limit(command)
        self.assertIn(command, one_command.exempted)    # apenned
        self.assertEqual(res, command)
