
import asyncio
import functools
from contextlib import ExitStack
from unittest import mock

import discord
from discord.ext import commands
import sqlalchemy

from lgrez import LGBot, config


def _decorate_with_cm(func_or_class, context_manager):
    """Returns the func_or_class wrapped into context_manager."""
    if asyncio.iscoroutinefunction(func_or_class):
        @functools.wraps(func_or_class)
        async def newfunc(*args, **kwargs):
            context_manager.__enter__()
            try:
                await func_or_class(*args, **kwargs)
            finally:
                context_manager.__exit__(None, None, None)
    else:
        @functools.wraps(func_or_class)
        def newfunc(*args, **kwargs):
            context_manager.__enter__()
            try:
                func_or_class(*args, **kwargs)
            finally:
                context_manager.__exit__(None, None, None)

    return newfunc


backup = {
    rc_class.__name__: {attr: rc_class.get_raw(attr) for attr in rc_class}
    for rc_class in [config.Role, config.Channel, config.Emoji]
}

def _prepare_attributes(rc_class, discord_type):
    """Rend prêts les attributs d'une classe ReadyCheck"""
    for attr in rc_class:
        raw = rc_class.get_raw(attr)
        name = raw if isinstance(raw, str) else raw.name
        ready = mock.MagicMock(discord_type, name=name)
        ready.configure_mock(name=name)
        setattr(rc_class, attr, ready)
        backup[rc_class.__name__][attr] = name

def _unprepare_attributes(rc_class):
    """Rend non-prêts les attributs d'une classe ReadyCheck"""
    for attr in rc_class:
        setattr(rc_class, attr, backup[rc_class.__name__][attr])


def mock_config():
    config.bot = mock.MagicMock(LGBot(), command_prefix="!")
    config.session = mock.Mock(sqlalchemy.orm.session.Session)
    config.engine = mock.Mock(sqlalchemy.engine.Engine)
    config.guild = mock.NonCallableMagicMock(discord.Guild)
    config.loop = mock.NonCallableMock()
    _prepare_attributes(config.Role, discord.Role)
    _prepare_attributes(config.Channel, discord.TextChannel)
    _prepare_attributes(config.Emoji, discord.Emoji)

def unmock_config():
    del config.bot, config.session, config.engine, config.guild, config.loop
    _unprepare_attributes(config.Role)
    _unprepare_attributes(config.Channel)
    _unprepare_attributes(config.Emoji)



class TypingMock(mock.AsyncMock):
    def __init__(self, *args, **kwargs):
        super().__init__(discord.context_managers.Typing, *args, **kwargs)

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type=None, exc_val=None, exc_tb=None):
        pass


def get_ctx(_command=None, *args, _caller_id=None, **kwargs):
    ctx = mock.NonCallableMagicMock(commands.Context)
    ctx.configure_mock(
        message=mock.NonCallableMagicMock(discord.Message),
        bot=config.bot,
        args=args,
        kwargs=kwargs,
        prefix=config.bot.command_prefix,
        command=_command,
        cog=_command.cog if _command else None,
        guild=config.guild,
        invoked_with=ctx,
        channel=mock.NonCallableMagicMock(discord.TextChannel),
        author=mock.NonCallableMagicMock(discord.Member),
        send=mock.AsyncMock(discord.TextChannel.send),
        typing=mock.MagicMock(discord.TextChannel.typing),
    )
    ctx.typing.return_value = TypingMock()
    ctx.message.configure_mock(
        guild=ctx.guild,
        channel=ctx.channel,
        author=ctx.author,
        webhook_id=None,
    )
    ctx.channel.configure_mock(
        guild=ctx.guild,
        send=ctx.send,
        typing=ctx.typing,
    )
    ctx.author.configure_mock(
        guild=ctx.guild,
        id=_caller_id or -1,
    )
    ctx.new_message = functools.partial(message, ctx)
    ctx.invoke = functools.partial(call, _command, ctx)
    ctx.assert_sent = functools.partial(assert_sent, ctx)
    ctx.assert_not_sent = functools.partial(assert_not_sent, ctx)
    return ctx


async def call(_command, ctx=None, *args, _caller_id=None, cog=None, **kwargs):
    if ctx is None:
        ctx = get_ctx(_command, *args, _caller_id, **kwargs)
    else:
        ctx.args = (*ctx.args, *args)
        ctx.kwargs.update(kwargs)
        if _caller_id is not None:
            ctx.author.configure_mock(id=_caller_id)
    if cog is None:
        cog = _command.cog
    await _command.callback(cog, ctx, *ctx.args, **ctx.kwargs)
    return ctx


def message(ctx, content=None, **kwargs):
    msg = mock.NonCallableMock(discord.Message)
    msg.configure_mock(
        content=content,
        guild=ctx.guild,
        channel=ctx.channel,
        author=ctx.author,
        **kwargs,
    )
    return msg

def chan(name, **kwargs):
    msg = mock.NonCallableMock(discord.TextChannel)
    msg.configure_mock(
        name=name,
        guild=config.guild,
        send=mock.AsyncMock(discord.TextChannel.send),
        typing=mock.MagicMock(discord.TextChannel.typing),
        **kwargs,
    )
    return msg


def assert_sent(chan, *msgs):
    """Raises an AssertionError if chan.send has not been called:

    - len(msgs) times
    - with msgs[<i>] in <i>th message call (string of list of strings, in
        which case each string it contains must be present in the call)
    """
    msgs = list(msgs)
    calls = [call.args[0] for call in chan.send.call_args_list]

    if len(calls) != len(msgs):
        ncalls, nmsgs = len(calls), len(msgs)
        msgs.extend(["[end]"]*(ncalls - nmsgs))
        calls.extend(["[end]"]*(nmsgs - ncalls))

        table = ("     Expected                 | Recieved               \n"
                 "    --------------------------|------------------------\n")
        for msg, call in zip(msgs, calls):
            if msg != "[end]":
                msg = f"*{msg if isinstance(msg, str) else '*'.join(msg)}*"
            called = call.replace("\n", "\\n")
            table += f"     {msg.ljust(24)} | {called} \n"

        raise AssertionError(f"chan.send called {ncalls} times - "
                             f"expecting {nmsgs} calls. Details:\n{table}")

    for msg, call in zip(msgs, calls):
        if isinstance(msg, str):
            msg = [msg]
        for smsg in msg:
            assert str(smsg) in call, (f"chan.send: excepted message '{smsg}' "
                                       f"not found in '{call}'")


def assert_not_sent(chan, *msgs):
    """Raises an AssertionError if chan.send has been called:

    - not len(msgs) times
    - with msgs[<i>] in <i>th message call (string of list of strings, in
        which case each string it contains must NOT be present in the call)
    """
    msgs = list(msgs)
    calls = [call.args[0] for call in chan.send.call_args_list]

    if len(calls) != len(msgs):
        ncalls, nmsgs = len(calls), len(msgs)
        msgs.extend(["[end]"]*(ncalls - nmsgs))
        calls.extend(["[end]"]*(nmsgs - ncalls))

        table = ("     Expected                 | Recieved               \n"
                 "    --------------------------|------------------------\n")
        for msg, call in zip(msgs, calls):
            if msg != "[end]":
                msg = f"*{msg if isinstance(msg, str) else '*'.join(msg)}*"
            called = call.replace("\n", "\\n")
            table += f"     NOT {msg.ljust(20)} | {called} \n"

        raise AssertionError(f"chan.send called {ncalls} times - "
                             f"expecting {nmsgs} calls. Details:\n{table}")

    for msg, call in zip(msgs, calls):
        if isinstance(msg, str):
            msg = [msg]
        for smsg in msg:
            assert str(smsg) not in call, (f"ctx.send: unexcepted message "
                                           f"'{smsg}' found in '{call}'")


def get_member(joueur):
    member = mock.NonCallableMagicMock(discord.Member)
    member.configure_mock(
        guild=config.guild,
        id=joueur.discord_id,
        display_name=joueur.nom,
    )
    return member

def get_chan(joueur):
    chan = mock.NonCallableMagicMock(discord.TextChannel)
    chan.configure_mock(
        guild=config.guild,
        id=joueur.chan_id_,
        name=(config.private_chan_prefix
              + joueur.nom.lower().replace(" ", "-")),
        send=mock.AsyncMock(discord.TextChannel.send),
    )
    return chan


class _MembersAndChansMocker:
    def __init__(self, *joueurs):
        self.ids = {jr.discord_id: get_member(jr) for jr in joueurs}
        self.chans = {jr.chan_id_: get_chan(jr) for jr in joueurs}
        self.members_patch = mock.patch("lgrez.config.guild.get_member",
                                        side_effect=self.ids.get)
        self.chans_patch = mock.patch("lgrez.config.guild.get_channel",
                                      side_effect=self.chans.get)

    def __enter__(self):
        self.members_patch.__enter__()
        self.chans_patch.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.members_patch.__exit__(exc_type, exc_val, exc_tb)
        self.chans_patch.__exit__(exc_type, exc_val, exc_tb)

    def __call__(self, func_or_class):
        """Use as a decorator"""
        return _decorate_with_cm(func_or_class, self)


def mock_members_and_chans(*joueurs):
    """Mock corrspondant members and private chans for joueurs.

    Can be used as a context manager or a class/function/async function
    decorator, as for `mock.patch`.
    """
    return _MembersAndChansMocker(*joueurs)


class _Interact:
    funcs = [
        ("lgrez.config.bot", "wait_for"),
        ("lgrez.blocs.tools", "wait_for_message"),
        ("lgrez.blocs.tools", "wait_for_message_here"),
        ("lgrez.blocs.tools", "wait_for_react_clic"),
        # ("lgrez.blocs.tools", "boucle_message"),
        # ("lgrez.blocs.tools", "boucle_query_joueur"),
        ("lgrez.blocs.tools", "yes_no"),
        ("lgrez.blocs.tools", "choice"),
    ]

    def __init__(self, *args):
        self.expected = list(args)
        self.side_effects = iter(args)
        # Itérateur de tuples (func, call) attendus
        self._patchs = {}   # objets _patchs
        self.patchs = {}    # mocks créés à l'enter
        for (mod, func) in self.funcs:
            # Patch de chaque fonction d'interaction
            self._patchs[func] = mock.patch(
                f"{mod}.{func}", new_callable=mock.AsyncMock,
                side_effect=functools.partial(self._side_effect, func),
            )

    def _format_calls(self, msg):
        if len(self.expected) < len(self.calls):
            self.expected.append(("[end]", ""))
        else:
            self.calls.append(("[end]", mock.call()))

        table = ("     Expected                 | Recieved               \n"
                 "    --------------------------|------------------------\n")
        for (efunc, result), (hfunc, call) in zip(self.expected, self.calls):
            expected = f"{efunc}"
            called = f"{hfunc}"   # "{tuple(call.args)}"
            table += f"     {expected.ljust(24)} | {called} \n"
        return f"{msg}\n{table}"

    def _side_effect(self, func, *args, **kwargs):
        self.calls.append((func, mock.call(*args, **kwargs)))
        expected_func, result = next(self.side_effects, (..., ...))
        assert result != ..., self._format_calls(
            "Too many user interactions"
        )
        assert expected_func == func, self._format_calls(
            "Unexpected user interaction"
        )
        if callable(result):        # Function used as side_effect
            return result(*args, **kwargs)
        else:
            return result           # Result value given directly

    def __enter__(self):
        self.stack = ExitStack()
        self.calls = []
        for func in self._patchs:
            mk = self.stack.enter_context(self._patchs[func])
            self.patchs[func] = mk
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stack.close()
        if exc_type is None:        # no exception
            assert next(self.side_effects, ...) == ..., self._format_calls(
                "Missing user interaction"
            )


    def __call__(self, func_or_class):
        """Use as a decorator"""
        return _decorate_with_cm(func_or_class, self)


def interact(*args):
    return _Interact(*args)
