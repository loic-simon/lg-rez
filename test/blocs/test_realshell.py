import asyncio
import unittest
from unittest import mock

import discord

from lgrez import config
from lgrez.blocs import realshell
from test import mock_discord


class TestRealShell(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.realshell.RealShell class."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    @mock.patch("asyncode.AsyncInteractiveConsole.__init__")
    def test___init__(self, aic_patch):
        """Unit tests for RealShell.__init__ method."""
        # def __init__(self, channel, locals={}, filename="!shell")
        __init__ = realshell.RealShell.__init__
        # simple
        slf = mock.Mock(realshell.RealShell)
        channel = mock.Mock()
        __init__(slf, channel)
        self.assertEqual(slf.bot, config.bot)
        self.assertEqual(slf.channel, channel)
        aic_patch.assert_called_once_with({"_shell": slf}, "!shell")
        aic_patch.reset_mock()
        # complex
        slf = mock.Mock(realshell.RealShell)
        channel, filename = mock.Mock(), mock.Mock()
        __init__(slf, channel, locals={"a": 1, "b": "oh"}, filename=filename)
        self.assertEqual(slf.bot, config.bot)
        self.assertEqual(slf.channel, channel)
        aic_patch.assert_called_once_with({"a": 1, "b": "oh", "_shell": slf},
                                          filename)


    @mock.patch("asyncode.AsyncInteractiveConsole.interact")
    @mock.patch("lgrez.blocs.realshell._py_bloc")
    async def test_interact(self, bloc_patch, aic_patch):
        """Unit tests for RealShell.interact method."""
        # async def interact(self, banner=None, exitmsg="Byebye!")
        interact = realshell.RealShell.interact
        bloc_patch.side_effect = lambda data: f"<!<{data}>!>"

        # simple
        channel = mock_discord.chan("tezt")
        slf = mock.Mock(realshell.RealShell, channel=channel)
        await interact(slf)
        mock_discord.assert_sent(channel, "Launching Python shell")
        aic_patch.assert_called_once_with(mock.ANY, "Byebye!")
        banner = aic_patch.call_args.args[0]
        self.assertIn("Discord implementation", banner)
        slf.message.clear_reactions.assert_called_once()
        aic_patch.reset_mock()

        # complex
        channel = mock_discord.chan("tezt")
        slf = mock.Mock(realshell.RealShell, channel=channel)
        await interact(slf, banner="LULZ", exitmsg="allo?")
        mock_discord.assert_sent(channel, "Launching Python shell")
        aic_patch.assert_called_once_with("LULZ", "allo?")
        slf.message.clear_reactions.assert_called_once()
        aic_patch.reset_mock()

        # simple, exited
        aic_patch.side_effect = SystemExit
        channel = mock_discord.chan("tezt")
        slf = mock.Mock(realshell.RealShell, channel=channel)
        with self.assertRaises(realshell.RealShellExit):
            await interact(slf)
        mock_discord.assert_sent(channel, "Launching Python shell")
        aic_patch.assert_called_once_with(mock.ANY, "Byebye!")
        slf.write.assert_called_once_with(f"\nByebye!", refresh=True,
                                          show_caret=False)
        slf.message.clear_reactions.assert_called_once()
        aic_patch.reset_mock()

        # complex, exited
        channel = mock_discord.chan("tezt")
        slf = mock.Mock(realshell.RealShell, channel=channel)
        aic_patch.side_effect = SystemExit
        with self.assertRaises(realshell.RealShellExit):
            await interact(slf, banner="LULZ", exitmsg="allo?")
        mock_discord.assert_sent(channel, "Launching Python shell")
        aic_patch.assert_called_once_with("LULZ", "allo?")
        slf.write.assert_called_once_with(f"\nallo?", refresh=True,
                                          show_caret=False)
        slf.message.clear_reactions.assert_called_once()


    async def test_control(self):
        """Unit tests for RealShell.control method."""
        # async def control(self, self, command, times=1)
        control = realshell.RealShell.control

        # bad command
        slf = mock.Mock(realshell.RealShell)
        with self.assertRaises(ValueError):
            await control(slf, "uiz")

        samples = {
            # (COMMAND, indent, times): (indent, result, write call)
            (realshell.RSCommand.HOME,  0, None): (0,  None, None),
            (realshell.RSCommand.HOME,  3, None): (0,  None, ""),
            (realshell.RSCommand.UNTAB, 0, None): (0,  None, None),
            (realshell.RSCommand.UNTAB, 0, 3):    (0,  None, None),
            (realshell.RSCommand.UNTAB, 5, None): (4,  None, ""),
            (realshell.RSCommand.UNTAB, 5, 3):    (2,  None, ""),
            (realshell.RSCommand.UNTAB, 5, 7):    (0,  None, ""),
            (realshell.RSCommand.TAB,   0, None): (1,  None, ""),
            (realshell.RSCommand.TAB,   0, 3):    (3,  None, ""),
            (realshell.RSCommand.TAB,   5, None): (6,  None, ""),
            (realshell.RSCommand.TAB,   5, 3):    (8,  None, ""),
            (realshell.RSCommand.TAB,   5, 7):    (12, None, ""),
            (realshell.RSCommand.ENTER, 0, None): (0,  "", None),
            (realshell.RSCommand.ENTER, 0, 3):    (0,  "", None),
            (realshell.RSCommand.ENTER, 5, None): (5,  "", None),
            (realshell.RSCommand.ENTER, 5, 3):    (5,  "", None),
            (realshell.RSCommand.ENTER, 5, 7):    (5,  "", None),
        }

        for (COMM, ind, times), (ind_res, res, wrc) in samples.items():
            slf = mock.Mock(realshell.RealShell, indent=ind)
            if times is None:
                ret = await control(slf, COMM)
            else:
                ret = await control(slf, COMM.value, times=times)
                # on teste avec .value de temps en temps aussi
            self.assertEqual(slf.indent, ind_res)
            self.assertEqual(ret, res)
            if wrc is None:
                slf.write.assert_not_called()
            else:
                slf.write.assert_called_once_with(wrc, refresh=True)

        samples = {
            # (COMMAND, indent, times):(indent
            (realshell.RSCommand.EOF,   0, None): 0,
            (realshell.RSCommand.EOF,   0, 3):    0,
            (realshell.RSCommand.EOF,   5, None): 5,
            (realshell.RSCommand.EOF,   5, 3):    5,
            (realshell.RSCommand.EOF,   5, 3):    5,
        }

        for (COMM, ind, times), ind_res in samples.items():
            slf = mock.Mock(realshell.RealShell, indent=ind)
            with self.assertRaises(realshell.RealShellExit):
                if times is None:
                     await control(slf, COMM)
                else:
                     await control(slf, COMM.value, times=times)
                # on teste avec .value de temps en temps aussi
            self.assertEqual(slf.indent, ind_res)
            slf.write.assert_not_called()


    async def test__check_reacts(self):
        """Unit tests for RealShell._check_reacts method."""
        # async def _check_reacts(self)
        _check_reacts = realshell.RealShell._check_reacts

        class AsyncIter():
            def __init__(self, _iter):
                self._iter = iter(_iter)

            async def __anext__(self):
                return next(self._iter)
        class ReactUsersRV(mock.Mock):
            def __iter__(self):
                return iter(self.users)
            def __aiter__(self):
                return AsyncIter(self.users)
        class ReactUsersMocker(mock.MagicMock):
            @property
            def return_value(self):
                return ReactUsersRV(users=self.users)

        # no reacts
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(),
                        message=mock.Mock(discord.Message))
        slf.message.reactions = []
        ret = await _check_reacts(slf)
        slf.message.add_reaction.assert_has_calls(
            [mock.call(command.value) for command in realshell.RSCommand])
        self.assertIs(False, ret)

        # reacts before, none clicked
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(),
                        message=mock.Mock(discord.Message))
        reacts = [mock.Mock(discord.Reaction,
                            **{"emoji.name": command.value}, count=1)
                  for command in realshell.RSCommand]
        slf.message.reactions = reacts
        ret = await _check_reacts(slf)
        slf.message.add_reaction.assert_not_called()
        for react in reacts:
            react.remove.assert_not_called()
        slf.control.assert_not_called()
        self.assertIs(False, ret)

        # reacts before, TAB clicked
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(),
                        message=mock.Mock(discord.Message))
        user = mock.Mock()
        reacts = [
            mock.Mock(discord.Reaction, **{"emoji.name": command.value},
                      count=2 if command == realshell.RSCommand.TAB else 1,
                      users=ReactUsersMocker(users=[slf.bot.user] + ([user]
                            if command == realshell.RSCommand.TAB else [])))
            for command in realshell.RSCommand
        ]
        slf.message.reactions = reacts
        ret = await _check_reacts(slf)
        slf.message.add_reaction.assert_not_called()
        for react in reacts:
            if react.emoji.name == realshell.RSCommand.TAB.value:
                react.remove.assert_called_once_with(user)
            else:
                react.remove.assert_not_called()
        slf.control.assert_called_once_with(realshell.RSCommand.TAB)
        slf.control.reset_mock()
        self.assertEqual(ret, (True, slf.control.return_value))

        # reacts before, more clicked -> one treated only
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(),
                        message=mock.Mock(discord.Message))
        reacts = [
            mock.Mock(discord.Reaction, **{"emoji.name": command.value},
                      count=2 if i > 2 else 1,
                      users=ReactUsersMocker(users=[slf.bot.user] +
                            ([user] if i > 2 else [])))
            for i, command in enumerate(realshell.RSCommand)
        ]
        slf.message.reactions = reacts
        ret = await _check_reacts(slf)
        slf.message.add_reaction.assert_not_called()
        for react in reacts:
            if react == reacts[3]:
                react.remove.assert_called_once()
            else:
                react.remove.assert_not_called()
        slf.control.assert_called_once_with(
            realshell.RSCommand(reacts[3].emoji.name))
        slf.control.reset_mock()
        self.assertEqual(ret, (True, slf.control.return_value))


    @mock.patch("lgrez.blocs.tools.wait_for_message", new_callable=mock.Mock)
    @mock.patch("asyncio.create_task")
    @mock.patch("asyncio.wait")
    async def test_get_order(self, aw_patch, act_patch, wfm_patch):
        """Unit tests for RealShell.get_order method."""
        # async def get_order(self)
        get_order = realshell.RealShell.get_order
        RSCommand = realshell.RSCommand

        # clic anticipé
        slf = mock.Mock(realshell.RealShell)
        ctrl_ret = mock.Mock()
        slf._check_reacts.return_value = (True, ctrl_ret)
        ret = await get_order(slf)
        slf._check_reacts.assert_called_once()
        self.assertEqual(ret, ctrl_ret)
        aw_patch.assert_not_called()
        act_patch.assert_not_called()
        wfm_patch.assert_not_called()

        # clic on TAB react
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(),
                        channel=mock.Mock(),
                        message=mock.Mock(discord.Message))
        slf._check_reacts.return_value = False       # pas de clic anticipé
        slf.message.reactions = []
        tasks = [mock.Mock(), mock.Mock()]      # react, message
        tasks[0].result.return_value.emoji.name = RSCommand.TAB.value
        act_patch.side_effect = tasks
        aw_patch.return_value = {tasks[0]}, {tasks[1]}

        ret = await get_order(slf)
        slf._check_reacts.assert_called_once()
        slf.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                 check=mock.ANY)
        wfm_patch.assert_called_once_with(trigger_on_commands=True,
                                          check=mock.ANY)
        react_check = slf.bot.wait_for.call_args.kwargs["check"]
        message_check = wfm_patch.call_args.kwargs["check"]
        self.assertEqual(act_patch.call_count, 2)
        act_patch.assert_has_calls([mock.call(slf.bot.wait_for.return_value),
                                    mock.call(wfm_patch.return_value)])
        aw_patch.assert_called_once_with(set(tasks),
                                         return_when=asyncio.FIRST_COMPLETED)
        tasks[1].cancel.assert_called_once()
        tasks[0].cancel.assert_not_called()
        p = tasks[0].result.return_value
        slf.message.remove_reaction.assert_called_once_with(p.emoji, p.member)
        slf.control.assert_called_once_with(RSCommand.TAB)
        self.assertEqual(ret, slf.control.return_value)
        aw_patch.reset_mock()
        act_patch.reset_mock()
        wfm_patch.reset_mock()

        # interlude: check checks
        slf.message.id = 15
        slf.bot.user.id = 33
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=31)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=33)))
        self.assertTrue(react_check(mock.Mock(message_id=15, user_id=31)))
        self.assertFalse(react_check(mock.Mock(message_id=15, user_id=33)))
        chan = slf.channel
        auth = slf.bot.user
        self.assertFalse(message_check(mock.Mock(channel="oh", author="meh")))
        self.assertFalse(message_check(mock.Mock(channel="oh", author=auth)))
        self.assertTrue(message_check(mock.Mock(channel=chan, author="meh")))
        self.assertFalse(message_check(mock.Mock(channel=chan, author=auth)))

        # message response
        samples = {
            # input -> (return value, control calls)
            "bzzt":     ("bzzt",    []),
            "<":        (None,      [mock.call(RSCommand.UNTAB, times=1)]),
            "<<<":      (None,      [mock.call(RSCommand.UNTAB, times=3)]),
            ">":        (None,      [mock.call(RSCommand.TAB, times=1)]),
            ">>>":      (None,      [mock.call(RSCommand.TAB, times=3)]),
            "<<>>":     (">>",      [mock.call(RSCommand.UNTAB, times=2)]),
            ">><<":     ("<<",      [mock.call(RSCommand.TAB, times=2)]),
            "<bzzt":    ("bzzt",    [mock.call(RSCommand.UNTAB, times=1)]),
            "<<<bzzt":  ("bzzt",    [mock.call(RSCommand.UNTAB, times=3)]),
            ">bzzt":    ("bzzt",    [mock.call(RSCommand.TAB, times=1)]),
            ">>>bzzt":  ("bzzt",    [mock.call(RSCommand.TAB, times=3)]),
            "<<>>bzzt": (">>bzzt",  [mock.call(RSCommand.UNTAB, times=2)]),
            "<=":       (...,       [mock.call(RSCommand.UNTAB, times=1),
                                     mock.call(RSCommand.ENTER)]),
            "<<<=":     (...,       [mock.call(RSCommand.UNTAB, times=3),
                                     mock.call(RSCommand.ENTER)]),
            ">=":       (...,       [mock.call(RSCommand.TAB, times=1),
                                     mock.call(RSCommand.ENTER)]),
            ">>>=":     (...,       [mock.call(RSCommand.TAB, times=3),
                                     mock.call(RSCommand.ENTER)]),
            "<<>>=":    (">>=",     [mock.call(RSCommand.UNTAB, times=2)]),
            "<a=b":     ("a=b",     [mock.call(RSCommand.UNTAB, times=1)]),
            ">>a=b":    ("a=b",     [mock.call(RSCommand.TAB, times=2)]),
            "a<=b":     ("a<=b",    []),
            "a>=b>":    ("a>=b>",   []),
            "a>=b><<":  ("a>=b><<", []),
            "<==":      ("==",      [mock.call(RSCommand.UNTAB, times=1)]),
            "==":       ("==",      []),
            "=":        (...,       [mock.call(RSCommand.ENTER)]),
        }

        for inpt, (expected, exp_calls) in samples.items():
            slf = mock.Mock(realshell.RealShell, bot=mock.Mock(),
                            channel=mock.Mock(),
                            message=mock.Mock(discord.Message))
            slf._check_reacts.return_value = False    # pas de clic anticipé
            slf.message.reactions = []
            tasks = [mock.Mock(), mock.Mock()]        # react, message
            tasks[1].result.return_value = mock.Mock(discord.Message,
                                                     content=inpt)
            act_patch.side_effect = tasks
            aw_patch.return_value = {tasks[1]}, {tasks[0]}

            ret = await get_order(slf)
            slf._check_reacts.assert_called_once()
            slf.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                     check=mock.ANY)
            wfm_patch.assert_called_once_with(trigger_on_commands=True,
                                              check=mock.ANY)
            react_check = slf.bot.wait_for.call_args.kwargs["check"]
            message_check = wfm_patch.call_args.kwargs["check"]
            self.assertEqual(act_patch.call_count, 2)
            act_patch.assert_has_calls(
                [mock.call(slf.bot.wait_for.return_value),
                 mock.call(wfm_patch.return_value)])
            aw_patch.assert_called_once_with(
                set(tasks), return_when=asyncio.FIRST_COMPLETED)
            tasks[0].cancel.assert_called_once()
            tasks[1].cancel.assert_not_called()
            mess = tasks[1].result.return_value
            mess.delete.assert_called_once()
            if expected is ...:
                expected = slf.control.return_value
            self.assertEqual(ret, expected, msg=inpt)
            self.assertEqual(slf.control.call_count, len(exp_calls), msg=inpt)
            slf.control.assert_has_calls(exp_calls)
            aw_patch.reset_mock()
            act_patch.reset_mock()
            wfm_patch.reset_mock()


    @mock.patch("lgrez.blocs.realshell._py_bloc")
    @mock.patch("lgrez.blocs.tools.smooth_split")
    async def test_write(self, tss_patch, aic_patch):
        """Unit tests for RealShell.write method."""
        # async def write(self, data, *, refresh=False, show_caret=True)
        write = realshell.RealShell.write
        aic_patch.side_effect = lambda data: f"<!<{data}>!>"

        # basic - non full -> nothing
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(), indent=2,
                        message=mock.Mock(discord.Message, content="<!<oh>!>"),
                        rsbuffer="kook", content="oh")
        await write(slf, "drzzz")
        self.assertEqual(slf.rsbuffer, "kookdrzzz")
        self.assertEqual(slf.indent, 2)
        self.assertEqual(slf.content, "oh")
        slf.message.edit.assert_not_called()
        slf.message.clear_reactions.assert_not_called()
        aic_patch.assert_not_called()
        tss_patch.assert_not_called()

        # refresh - non full
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(), indent=2,
                        message=mock.Mock(discord.Message, content="<!<oh>!>"),
                        rsbuffer="kook", content="oh")
        await write(slf, "drzzz", refresh=True)
        self.assertEqual(slf.rsbuffer, "")
        self.assertEqual(slf.indent, 2)
        self.assertEqual(slf.content, "ohkookdrzzz")
        slf.message.edit.assert_called_once_with(
            content="<!<ohkookdrzzz        ‸>!>")
        slf.message.clear_reactions.assert_not_called()
        tss_patch.assert_not_called()

        # refresh - no caret - non full
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(), indent=2,
                        message=mock.Mock(discord.Message, content="<!<oh>!>"),
                        rsbuffer="kook", content="oh")
        await write(slf, "drzzz", refresh=True, show_caret=False)
        self.assertEqual(slf.rsbuffer, "")
        self.assertEqual(slf.indent, 2)
        self.assertEqual(slf.content, "ohkookdrzzz")
        slf.message.edit.assert_called_once_with(content="<!<ohkookdrzzz>!>")
        slf.message.clear_reactions.assert_not_called()
        tss_patch.assert_not_called()

        # ends by sys.ps1 -> refresh auto - non full
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(), indent=2,
                        message=mock.Mock(discord.Message, content="<!<oh>!>"),
                        rsbuffer="kook", content="oh")
        await write(slf, "drzzz\n>>> ")
        self.assertEqual(slf.rsbuffer, "")
        self.assertEqual(slf.indent, 2)
        self.assertEqual(slf.content, "ohkookdrzzz\n>>> ")
        slf.message.edit.assert_called_once_with(
            content="<!<ohkookdrzzz\n>>>         ‸>!>")
        slf.message.clear_reactions.assert_not_called()
        tss_patch.assert_not_called()

        # ends by sys.ps2 -> refresh auto - non full
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(), indent=2,
                        message=mock.Mock(discord.Message, content="<!<oh>!>"),
                        rsbuffer="kook", content="oh")
        await write(slf, "drzzz\n... ")
        self.assertEqual(slf.rsbuffer, "")
        self.assertEqual(slf.indent, 2)
        self.assertEqual(slf.content, "ohkookdrzzz\n... ")
        slf.message.edit.assert_called_once_with(
            content="<!<ohkookdrzzz\n...         ‸>!>")
        slf.message.clear_reactions.assert_not_called()
        tss_patch.assert_not_called()

        # ends by :\nsys.ps2 -> refresh auto + autoindent - non full
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(), indent=2,
                        message=mock.Mock(discord.Message, content="<!<oh>!>"),
                        rsbuffer="kook", content="oh")
        await write(slf, "drzzz:\n... ")
        self.assertEqual(slf.rsbuffer, "")
        self.assertEqual(slf.indent, 3)
        self.assertEqual(slf.content, "ohkookdrzzz:\n... ")
        slf.message.edit.assert_called_once_with(
            content="<!<ohkookdrzzz:\n...             ‸>!>")
        slf.message.clear_reactions.assert_not_called()
        tss_patch.assert_not_called()

        # refresh - content(2) + buffer(4) + data(x) + insert(9) = 1991 => full
        # x = (1991 - 9 - 4 - 2) = 1976 + 4*494
        chan = mock_discord.chan(".")
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(), indent=2,
                        message=mock.Mock(discord.Message, content="<!<oh>!>"),
                        rsbuffer="kook", content="oh", channel=chan)
        orig_msg = slf.message
        tss_patch.return_value = ["bl1", "bl2", "bl3"]
        await write(slf, "drzZ"*494, refresh=True)
        orig_msg.clear_reactions.assert_called_once()
        self.assertEqual(slf.rsbuffer, "")
        self.assertEqual(slf.indent, 2)
        self.assertEqual(slf.content, "bl3")
        slf.message.edit.assert_not_called()
        tss_patch.assert_called_once_with("kook" + "drzZ" * 494, N=1990)
        self.assertEqual(chan.send.call_count, 3)
        chan.send.assert_has_calls([mock.call("<!<bl1>!>"),
                                    mock.call("<!<bl2>!>"),
                                    mock.call("<!<bl3        ‸>!>")])
        self.assertEqual(slf.message, chan.send.return_value)


    async def test_raw_input(self):
        """Unit tests for RealShell.raw_input method."""
        # async def raw_input(self, prompt="")
        raw_input = realshell.RealShell.raw_input

        # basic
        chan = mock_discord.chan(".")
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(), indent=2)
        slf.get_order.return_value = "oh"
        ret = await raw_input(slf)
        slf.get_order.assert_called_once()
        slf.write.assert_called_once_with("        oh\n", refresh=True,
                                          show_caret=False)
        self.assertEqual(ret, "        oh")

        # prompt + get_order loop
        chan = mock_discord.chan(".")
        slf = mock.Mock(realshell.RealShell, bot=mock.Mock(), indent=2)
        slf.get_order.side_effect = [None, None, ""]
        ret = await raw_input(slf, prompt="klkl")
        self.assertEqual(slf.get_order.call_count, 3)
        self.assertEqual(slf.write.call_count, 2)
        slf.write.assert_has_calls([
            mock.call("klkl", refresh=True),
            mock.call("        \n", refresh=True, show_caret=False),
        ])
        self.assertEqual(ret, "        ")



class TestRealShellFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.realshell functions."""

    @mock.patch("lgrez.blocs.tools.code_bloc")
    def test__py_bloc(self, cb_patch):
        """Unit tests for realshell._py_bloc function."""
        # def _py_bloc(data)
        _py_bloc = realshell._py_bloc
        # unique case
        data = mock.Mock()
        ret = _py_bloc(data)
        cb_patch.assert_called_once_with(data, "py")
        self.assertEqual(ret, cb_patch.return_value)
