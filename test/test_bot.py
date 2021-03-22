import datetime
import functools
import unittest
from unittest import mock

import discord
from discord.ext import commands
import freezegun
import sqlalchemy

from lgrez import bot, config, bdd, blocs, __version__
from lgrez.blocs import ready_check
from test import mock_discord, mock_bdd, mock_env



class TestBotOnReady(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bot on_ready function."""

    def setUp(self):
        # partial set up (LGBot.run effects only)
        config.bot = mock.MagicMock(bot.LGBot(), command_prefix="!")
        config.session = mock.Mock(sqlalchemy.orm.session.Session)
        config.engine = mock.Mock(sqlalchemy.engine.Engine)

    def tearDown(self):
        mock_discord.unmock_config()

    @mock_bdd.patch_db()
    @mock.patch("builtins.print")
    @mock.patch("lgrez.blocs.tools.channel")
    @mock.patch("lgrez.blocs.tools.role")
    @mock.patch("lgrez.blocs.tools.emoji")
    async def test__on_ready(self, emo_patch, role_patch, ch_patch, ppatch):
        """Unit tests for bot._on_ready function."""
        # async def _on_ready(bot)
        _on_ready = bot._on_ready

        # guild not found
        config.bot.get_guild.return_value = None
        with self.assertRaises(RuntimeError) as cm:
            await _on_ready(config.bot)
        self.assertEqual(config.loop, config.bot.loop)
        config.bot.i_am_alive.assert_not_called()
        config.bot.get_guild.assert_called_once_with(config.bot.GUILD_ID)
        self.assertIn(str(config.bot.GUILD_ID), cm.exception.args[0])
        ppatch.assert_not_called()
        config.bot.get_guild.reset_mock(return_value=True)
        config.bot.reset_mock()

        # guild found, everything ok
        config.output_liveness = False
        ch_patch.side_effect=functools.partial(mock.Mock, discord.TextChannel)
        role_patch.side_effect=functools.partial(mock.Mock, discord.Role)
        emo_patch.side_effect=functools.partial(mock.Mock, discord.Emoji)
        await _on_ready(config.bot)
        guild = config.bot.get_guild.return_value
        self.assertEqual(config.loop, config.bot.loop)
        config.bot.i_am_alive.assert_not_called()
        config.bot.get_guild.assert_called_once_with(config.bot.GUILD_ID)
        self.assertEqual(config.guild, guild)
        printed = "\n".join(call.args[0] for call in ppatch.call_args_list)
        self.assertIn("Connected", printed)
        self.assertIn(str(guild.name), printed)
        self.assertIn("Initialization", printed)
        self.assertIn("Initialization", printed)
        self.assertIn("Initialization complete", printed)
        self.assertIn("Listening for events", printed)
        mock_discord.assert_sent(config.Channel.logs, "Just rebooted")
        mock_discord.assert_not_sent(config.Channel.logs,
                                     ["tâches planifiées", "ERREURS"])
        ppatch.reset_mock()
        try:
            for name in config.Channel:
                getattr(config.Channel, name)
            for name in config.Role:
                getattr(config.Role, name)
            for name in config.Emoji:
                getattr(config.Emoji, name)
            config.private_chan_category_name
        except ready_check.NotReadyError as e:
            raise AssertionError from e
        config.bot.change_presence.assert_called_once()
        config.bot.reset_mock()

        mock_discord._unprepare_attributes(config.Role)
        mock_discord._unprepare_attributes(config.Channel)
        mock_discord._unprepare_attributes(config.Emoji)

        # guild found, some missing Discord elements (not #logs / @MJ)
        def _channel(name):
            if name in ["rôles", "débats", config.private_chan_category_name]:
                raise ValueError
            else:
                return mock.NonCallableMock(discord.TextChannel)
        def _role(name):
            if name in ["Joueur en vie", "Maire"]:
                raise ValueError
            else:
                return mock.NonCallableMock(discord.Role)
        def _emoji(name):
            if name == "ro":
                raise ValueError
            else:
                return mock.NonCallableMock(discord.Emoji)
        ch_patch.side_effect = _channel
        role_patch.side_effect = _role
        emo_patch.side_effect = _emoji
        await _on_ready(config.bot)
        guild = config.bot.get_guild.return_value
        self.assertEqual(config.loop, config.bot.loop)
        config.bot.i_am_alive.assert_not_called()
        config.bot.get_guild.assert_called_once_with(config.bot.GUILD_ID)
        self.assertEqual(config.guild, guild)
        printed = "\n".join(call.args[0] for call in ppatch.call_args_list)
        self.assertIn("Connected", printed)
        self.assertIn(str(guild.name), printed)
        self.assertIn("Initialization", printed)
        self.assertIn("Initialization complete", printed)
        self.assertIn("Listening for events", printed)
        mock_discord.assert_sent(
            config.Channel.logs,
            ["ERREURS", "6 errors", 'config.Channel.roles = "rôles"',
             'config.Channel.debats = "débats"', str(config.Role.mj.mention),
             'catégorie config.private_chan_category_name = '
             f'"{config.private_chan_category_name}"',
             'config.Role.joueur_en_vie = "Joueur en vie"',
             'config.Role.maire = "Maire"', 'config.Emoji.ro = "ro"'],
            "Just rebooted")
        mock_discord.assert_not_sent(config.Channel.logs, "tâches planifiées",
                                     "tâches planifiées")
        ppatch.reset_mock()
        try:
            for attr in config.Channel:
                if attr not in ["roles", "debats"]:
                    getattr(config.Channel, attr)
            for attr in config.Role:
                if attr not in ["joueur_en_vie", "maire"]:
                    getattr(config.Role, attr)
            for attr in config.Emoji:
                if attr != "ro":
                    getattr(config.Emoji, attr)
            config.private_chan_category_name
        except ready_check.NotReadyError as e:
            raise AssertionError from e
        config.bot.change_presence.assert_called_once()
        config.bot.reset_mock()

        mock_discord._unprepare_attributes(config.Role)
        mock_discord._unprepare_attributes(config.Channel)
        mock_discord._unprepare_attributes(config.Emoji)

        # guild found, missing @MJ
        def _channel(name):
            return mock.NonCallableMock(discord.TextChannel)
        def _role(name):
            if name == "MJ":
                raise ValueError
            else:
                return mock.NonCallableMock(discord.Role)
        def _emoji(name):
            return mock.NonCallableMock(discord.Emoji)
        ch_patch.side_effect = _channel
        role_patch.side_effect = _role
        emo_patch.side_effect = _emoji
        await _on_ready(config.bot)
        guild = config.bot.get_guild.return_value
        self.assertEqual(config.loop, config.bot.loop)
        config.bot.i_am_alive.assert_not_called()
        config.bot.get_guild.assert_called_once_with(config.bot.GUILD_ID)
        self.assertEqual(config.guild, guild)
        printed = "\n".join(call.args[0] for call in ppatch.call_args_list)
        self.assertIn("Connected", printed)
        self.assertIn(str(guild.name), printed)
        self.assertIn("Initialization", printed)
        self.assertIn("Initialization complete", printed)
        self.assertIn("Listening for events", printed)
        mock_discord.assert_sent(
            config.Channel.logs,
            ["ERREURS", "1 error", 'config.Role.mj = "MJ"',
             "@everyone"],
            "Just rebooted")
        mock_discord.assert_not_sent(config.Channel.logs, "tâches planifiées",
                                     "tâches planifiées")
        ppatch.reset_mock()
        try:
            for attr in config.Channel:
                getattr(config.Channel, attr)
            for attr in config.Role:
                if attr != "mj":
                    getattr(config.Role, attr)
            for attr in config.Emoji:
                getattr(config.Emoji, attr)
            config.private_chan_category_name
        except ready_check.NotReadyError as e:
            raise AssertionError from e
        config.bot.change_presence.assert_called_once()
        config.bot.reset_mock()

        mock_discord._unprepare_attributes(config.Role)
        mock_discord._unprepare_attributes(config.Channel)
        mock_discord._unprepare_attributes(config.Emoji)

        # guild found, missing @MJ / #logs
        def _channel(name):
            if name == "logs":
                raise ValueError
            else:
                return mock.NonCallableMock(discord.TextChannel)
        def _role(name):
            return mock.NonCallableMock(discord.Role)
        def _emoji(name):
            return mock.NonCallableMock(discord.Emoji)
        ch_patch.side_effect = _channel
        role_patch.side_effect = _role
        emo_patch.side_effect = _emoji
        defchan = mock.NonCallableMock(discord.TextChannel)
        config.guild.text_channels.__getitem__.return_value = defchan
        await _on_ready(config.bot)
        guild = config.bot.get_guild.return_value
        self.assertEqual(config.loop, config.bot.loop)
        config.bot.i_am_alive.assert_not_called()
        config.bot.get_guild.assert_called_once_with(config.bot.GUILD_ID)
        self.assertEqual(config.guild, guild)
        printed = "\n".join(call.args[0] for call in ppatch.call_args_list)
        self.assertIn("Connected", printed)
        self.assertIn(str(guild.name), printed)
        self.assertIn("Initialization", printed)
        self.assertIn("Initialization complete", printed)
        self.assertIn("Listening for events", printed)
        mock_discord.assert_sent(
            defchan,
            ["ERREURS", "1 error", 'config.Channel.logs = "logs"',
             "Routing logs", str(config.Role.mj.mention)],
            "Just rebooted")
        ppatch.reset_mock()
        try:
            for attr in config.Channel:
                if attr != "logs":
                    getattr(config.Channel, attr)
            for attr in config.Role:
                getattr(config.Role, attr)
            for attr in config.Emoji:
                getattr(config.Emoji, attr)
            config.private_chan_category_name
        except ready_check.NotReadyError as e:
            raise AssertionError from e
        config.bot.change_presence.assert_called_once()
        config.bot.reset_mock()

        mock_discord._unprepare_attributes(config.Role)
        mock_discord._unprepare_attributes(config.Channel)
        mock_discord._unprepare_attributes(config.Emoji)

        # guild found, missing @MJ / #logs
        def _channel(name):
            return mock.NonCallableMock(discord.TextChannel)
        def _role(name):
            return mock.NonCallableMock(discord.Role)
        def _emoji(name):
            return mock.NonCallableMock(discord.Emoji)
        taches = [
            bdd.Tache(timestamp=datetime.datetime.now(), commande="cmdz"),
            bdd.Tache(timestamp=datetime.datetime.now(), commande="cmd2"),
            bdd.Tache(timestamp=datetime.datetime.now(), commande="cmd3"),
        ]
        bdd.Tache.add(*taches)
        ch_patch.side_effect = _channel
        role_patch.side_effect = _role
        emo_patch.side_effect = _emoji
        await _on_ready(config.bot)
        guild = config.bot.get_guild.return_value
        self.assertEqual(config.loop, config.bot.loop)
        config.bot.i_am_alive.assert_not_called()
        config.bot.get_guild.assert_called_once_with(config.bot.GUILD_ID)
        self.assertEqual(config.guild, guild)
        printed = "\n".join(call.args[0] for call in ppatch.call_args_list)
        self.assertIn("Connected", printed)
        self.assertIn(str(guild.name), printed)
        self.assertIn("Initialization", printed)
        self.assertIn("Initialization complete", printed)
        self.assertIn("Listening for events", printed)
        mock_discord.assert_sent(config.Channel.logs, "Just rebooted",
                                 "3 tâches planifiées")
        ppatch.reset_mock()
        try:
            for attr in config.Channel:
                if attr != "logs":
                    getattr(config.Channel, attr)
            for attr in config.Role:
                getattr(config.Role, attr)
            for attr in config.Emoji:
                getattr(config.Emoji, attr)
            config.private_chan_category_name
        except ready_check.NotReadyError as e:
            raise AssertionError from e
        config.bot.change_presence.assert_called_once()
        config.loop.call_later.assert_has_calls(
            [mock.call(mock.ANY, tache.execute) for tache in taches]
        )


class TestBotEventsFunction(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bot events functions."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()


    @mock.patch("lgrez.features.inscription.main")
    async def test__on_member_join(self, inscr_patch):
        """Unit tests for bot._on_member_join function."""
        # async def _on_member_join(bot, member)
        _on_member_join = bot._on_member_join

        # bad guild
        member = mock.MagicMock(discord.Member, guild=3)
        await _on_member_join(config.bot, member)
        inscr_patch.assert_not_called()

        # good guild
        member = mock.MagicMock(discord.Member, guild=config.guild)
        await _on_member_join(config.bot, member)
        inscr_patch.assert_called_once_with(member)


    @mock.patch("lgrez.blocs.tools.mention_MJ")
    async def test__on_member_remove(self, mmj_patch):
        """Unit tests for bot._on_member_remove function."""
        # async def _on_member_remove(bot, member)
        _on_member_remove = bot._on_member_remove

        # bad guild
        member = mock.MagicMock(discord.Member, guild=3)
        await _on_member_remove(config.bot, member)
        config.Channel.logs.send.assert_not_called()
        mmj_patch.assert_not_called()

        # good guild
        member = mock.MagicMock(discord.Member, guild=config.guild)
        await _on_member_remove(config.bot, member)
        mock_discord.assert_sent(config.Channel.logs,
                                 [mmj_patch.return_value, "ALERTE",
                                  member.display_name])


    @mock.patch("lgrez.features.IA.process_IA")
    async def test__on_message(self, ia_patch):
        """Unit tests for bot._on_message function."""
        # async def _on_message(bot, message)
        _on_message = bot._on_message
        config.bot.get_context = mock.AsyncMock()
        config.bot.invoke = mock.AsyncMock()
        config.bot.in_command = [12]
        config.bot.in_stfu = [13]

        # author = bot
        message = mock.NonCallableMock(discord.Message, author=config.bot.user)
        await _on_message(config.bot, message)
        self.assertEqual(len(message.mock_calls), 0)
        ia_patch.assert_not_called()

        # pas de serveur (MP)
        message = mock.NonCallableMock(discord.Message, guild=None)
        message.channel = mock_discord.chan("some-private-chan")
        await _on_message(config.bot, message)
        message.channel.send.assert_called_once()
        self.assertEqual(len(message.mock_calls), 1)
        ia_patch.assert_not_called()

        # mauvais serveur
        message = mock.NonCallableMock(discord.Message, guild=3)
        await _on_message(config.bot, message)
        self.assertEqual(len(message.mock_calls), 0)
        ia_patch.assert_not_called()

        # pas de rôle affecté
        message = mock.NonCallableMock(discord.Message, guild=config.guild,
                                       webhook_id=None)
        message.author.top_role = config.Role.everyone
        await _on_message(config.bot, message)
        self.assertEqual(len(message.mock_calls), 0)
        ia_patch.assert_not_called()

        # basic
        message = mock.NonCallableMock(
            discord.Message, guild=config.guild, content="bzzt",
            channel=mock_discord.chan("conv-bot-A", id=11)
        )
        await _on_message(config.bot, message)
        config.bot.get_context.assert_called_with(message)
        config.bot.invoke.assert_called_with(
            config.bot.get_context.return_value)
        ia_patch.assert_called_with(message)
        ia_patch.reset_mock()

        # command
        message = mock.NonCallableMock(discord.Message, guild=config.guild,
                                       content="!bzzt")
        await _on_message(config.bot, message)
        config.bot.get_context.assert_called_with(message)
        config.bot.invoke.assert_called_with(
            config.bot.get_context.return_value)
        ia_patch.assert_not_called()

        # command + blanc
        message = mock.NonCallableMock(discord.Message, guild=config.guild,
                                       content="! bzzt")
        await _on_message(config.bot, message)
        config.bot.get_context.assert_called_with(message)
        config.bot.invoke.assert_called_with(
            config.bot.get_context.return_value)
        self.assertEqual(message.content, "!bzzt")
        ia_patch.assert_not_called()

        # autre préfixe
        config.bot.command_prefix = "<OP>"
        message = mock.NonCallableMock(discord.Message, guild=config.guild,
                                       content="<OP>bzzt")
        await _on_message(config.bot, message)
        config.bot.get_context.assert_called_with(message)
        config.bot.invoke.assert_called_with(
            config.bot.get_context.return_value)
        ia_patch.assert_not_called()
        config.bot.command_prefix = "!"

        # not in private chan
        message = mock.NonCallableMock(
            discord.Message, guild=config.guild, content="bzzt",
            channel=mock_discord.chan("gzzt", id=11)
        )
        await _on_message(config.bot, message)
        config.bot.get_context.assert_called_with(message)
        config.bot.invoke.assert_called_with(
            config.bot.get_context.return_value)
        ia_patch.assert_not_called()

        # in private chan - other prefix
        config.private_chan_prefix = "<OP>"
        message = mock.NonCallableMock(
            discord.Message, guild=config.guild, content="bzzt",
            channel=mock_discord.chan("<OP>gzzt", id=11)
        )
        await _on_message(config.bot, message)
        config.bot.get_context.assert_called_with(message)
        config.bot.invoke.assert_called_with(
            config.bot.get_context.return_value)
        ia_patch.assert_called_with(message)
        ia_patch.reset_mock()
        config.private_chan_prefix = "conv-bot-"

        # in command
        message = mock.NonCallableMock(
            discord.Message, guild=config.guild, content="bzzt",
            channel=mock_discord.chan("conv-bot-gzzt", id=12)
        )
        await _on_message(config.bot, message)
        config.bot.get_context.assert_called_with(message)
        config.bot.invoke.assert_called_with(
            config.bot.get_context.return_value)
        ia_patch.assert_not_called()

        # in stfu
        message = mock.NonCallableMock(
            discord.Message, guild=config.guild, content="bzzt",
            channel=mock_discord.chan("conv-bot-gzzt", id=13)
        )
        await _on_message(config.bot, message)
        config.bot.get_context.assert_called_with(message)
        config.bot.invoke.assert_called_with(
            config.bot.get_context.return_value)
        ia_patch.assert_not_called()

        # good
        message = mock.NonCallableMock(
            discord.Message, guild=config.guild, content="bzzt",
            channel=mock_discord.chan("conv-bot-gzzt", id=11)
        )
        await _on_message(config.bot, message)
        config.bot.get_context.assert_called_with(message)
        config.bot.invoke.assert_called_with(
            config.bot.get_context.return_value)
        ia_patch.assert_called_with(message)


    @mock.patch("lgrez.blocs.tools.create_context")
    async def test__on_raw_reaction_add(self, cc_patch):
        """Unit tests for bot._on_raw_reaction_add function."""
        # async def _on_raw_reaction_add(bot, payload)
        _on_raw_reaction_add = bot._on_raw_reaction_add

        # author = bot
        payload = mock.NonCallableMock(discord.RawReactionActionEvent,
                                       member=config.bot.user)
        await _on_raw_reaction_add(config.bot, payload)
        config.bot.invoke.assert_not_called()
        cc_patch.assert_not_called()

        # mauvais serveur
        payload = mock.NonCallableMock(discord.RawReactionActionEvent,
                                       guild_id=10)
        await _on_raw_reaction_add(config.bot, payload)
        config.bot.invoke.assert_not_called()
        cc_patch.assert_not_called()

        # chan non privé
        payload = mock.NonCallableMock(discord.RawReactionActionEvent,
                                       guild_id=config.guild.id)
        config.guild.get_channel.return_value = mock_discord.chan("bzzt")
        await _on_raw_reaction_add(config.bot, payload)
        config.guild.get_channel.assert_called_with(payload.channel_id)
        config.bot.invoke.assert_not_called()
        cc_patch.assert_not_called()

        # pas joueur en vie
        payload = mock.NonCallableMock(
            discord.RawReactionActionEvent, guild_id=config.guild.id,
            member=mock.Mock(discord.Member, roles=[config.Role.joueur_mort])
        )
        config.guild.get_channel.return_value = mock_discord.chan(
            "conv-bot-A")
        await _on_raw_reaction_add(config.bot, payload)
        config.guild.get_channel.assert_called_with(payload.channel_id)
        config.bot.invoke.assert_not_called()
        cc_patch.assert_not_called()

        # bûcher
        payload = mock.NonCallableMock(
            discord.RawReactionActionEvent, guild_id=config.guild.id,
            emoji=config.Emoji.bucher,
            member=mock.Mock(discord.Member, roles=[config.Role.joueur_en_vie])
        )
        chan = mock_discord.chan("conv-bot-A")
        config.guild.get_channel.return_value = chan
        await _on_raw_reaction_add(config.bot, payload)
        config.guild.get_channel.assert_called_with(payload.channel_id)
        config.bot.invoke.assert_called_once()
        cc_patch.assert_called_once_with(payload.member, "!vote")
        sent = cc_patch.return_value.send.call_args.args[0]
        self.assertIn(str(config.Emoji.bucher), sent)
        self.assertIn("Vote pour le condamné", sent)
        config.bot.invoke.reset_mock()
        cc_patch.reset_mock()

        # maire
        payload = mock.NonCallableMock(
            discord.RawReactionActionEvent, guild_id=config.guild.id,
            emoji=config.Emoji.maire,
            member=mock.Mock(discord.Member, roles=[config.Role.joueur_en_vie])
        )
        chan = mock_discord.chan("conv-bot-A")
        config.guild.get_channel.return_value = chan
        await _on_raw_reaction_add(config.bot, payload)
        config.guild.get_channel.assert_called_with(payload.channel_id)
        config.bot.invoke.assert_called_once()
        cc_patch.assert_called_once_with(payload.member, "!votemaire")
        sent = cc_patch.return_value.send.call_args.args[0]
        self.assertIn(str(config.Emoji.maire), sent)
        self.assertIn("Vote pour le nouveau maire", sent)
        config.bot.invoke.reset_mock()
        cc_patch.reset_mock()

        # loups
        payload = mock.NonCallableMock(
            discord.RawReactionActionEvent, guild_id=config.guild.id,
            emoji=config.Emoji.lune,
            member=mock.Mock(discord.Member, roles=[config.Role.joueur_en_vie])
        )
        chan = mock_discord.chan("conv-bot-A")
        config.guild.get_channel.return_value = chan
        await _on_raw_reaction_add(config.bot, payload)
        config.guild.get_channel.assert_called_with(payload.channel_id)
        config.bot.invoke.assert_called_once()
        cc_patch.assert_called_once_with(payload.member, "!voteloups")
        sent = cc_patch.return_value.send.call_args.args[0]
        self.assertIn(str(config.Emoji.lune), sent)
        self.assertIn("Vote pour la victime", sent)
        config.bot.invoke.reset_mock()
        cc_patch.reset_mock()

        # action
        payload = mock.NonCallableMock(
            discord.RawReactionActionEvent, guild_id=config.guild.id,
            emoji=config.Emoji.action,
            member=mock.Mock(discord.Member, roles=[config.Role.joueur_en_vie])
        )
        chan = mock_discord.chan("conv-bot-A")
        config.guild.get_channel.return_value = chan
        await _on_raw_reaction_add(config.bot, payload)
        config.guild.get_channel.assert_called_with(payload.channel_id)
        config.bot.invoke.assert_called_once()
        cc_patch.assert_called_once_with(payload.member, "!action")
        sent = cc_patch.return_value.send.call_args.args[0]
        self.assertIn(str(config.Emoji.action), sent)
        self.assertIn("Action", sent)
        config.bot.invoke.reset_mock()
        cc_patch.reset_mock()

        # other emoji
        payload = mock.NonCallableMock(
            discord.RawReactionActionEvent, guild_id=config.guild.id,
            emoji=config.Emoji.ha,
            member=mock.Mock(discord.Member, roles=[config.Role.joueur_en_vie])
        )
        chan = mock_discord.chan("conv-bot-A")
        config.guild.get_channel.return_value = chan
        await _on_raw_reaction_add(config.bot, payload)
        config.guild.get_channel.assert_called_with(payload.channel_id)
        config.bot.invoke.assert_not_called()
        cc_patch.assert_not_called()


    async def test__on_command_error(self):
        """Unit tests for bot._on_command_error function."""
        # async def _on_command_error(bot, ctx, exc)
        _on_command_error = bot._on_command_error

        # mauvais serveur
        ctx = mock.NonCallableMock(commands.Context, guild=10)
        await _on_command_error(config.bot, ctx, None)
        ctx.send.assert_not_called()

        # STOP
        ctx = mock_discord.get_ctx()
        exc = commands.CommandInvokeError(blocs.tools.CommandExit())
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent("Mission aborted")

        # STOP custom message
        ctx = mock_discord.get_ctx()
        exc = commands.CommandInvokeError(blocs.tools.CommandExit("cust0m"))
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent("cust0m")

        # BDD error - MJ
        ctx = mock_discord.get_ctx()
        ctx.author.top_role = mock.MagicMock(discord.Role,
                                             __ge__=lambda s, o: True) # >= MJ
        exc = commands.CommandInvokeError(bdd.SQLAlchemyError("bzzt"))
        try: raise exc.original      # creating traceback
        except bdd.SQLAlchemyError: pass
        await _on_command_error(config.bot, ctx, exc)
        mock_discord.assert_sent(config.Channel.logs, "Rollback session")
        config.Channel.logs.send.reset_mock()
        config.session.rollback.assert_called_once()
        config.session.rollback.reset_mock()
        ctx.assert_sent(["Un problème est survenu", "Traceback",
                         "SQLAlchemyError", "bzzt"])

        # BDD error - not MJ
        ctx = mock_discord.get_ctx()
        ctx.author.top_role = mock.MagicMock(discord.Role,
                                             __ge__=lambda s, o: False) # < MJ
        exc = commands.CommandInvokeError(bdd.DriverOperationalError("bzoozt"))
        try: raise exc.original      # creating traceback
        except bdd.DriverOperationalError: pass
        await _on_command_error(config.bot, ctx, exc)
        mock_discord.assert_sent(config.Channel.logs, "Rollback session")
        config.Channel.logs.send.reset_mock()
        config.session.rollback.assert_called_once()
        config.session.rollback.reset_mock()
        ctx.assert_sent(["Un problème est survenu",
                         bdd.DriverOperationalError.__name__, "bzoozt"])
        ctx.assert_not_sent("Traceback")

        # BDD error - session not ready : on vérifie juste que pas d'erreur
        ctx = mock_discord.get_ctx()
        _session = config.session
        del config.session
        ctx.author.top_role = mock.MagicMock(discord.Role,
                                             __ge__=lambda s, o: True) # >= MJ
        exc = commands.CommandInvokeError(bdd.SQLAlchemyError("bzzt"))
        await _on_command_error(config.bot, ctx, exc)
        mock_discord.assert_sent(config.Channel.logs)   # nothing
        config.Channel.logs.send.reset_mock()
        ctx.assert_sent(["Un problème est survenu", "SQLAlchemyError", "bzzt"])
        config.session = _session

        # CommandNotFound
        ctx = mock_discord.get_ctx()
        await _on_command_error(config.bot, ctx, commands.CommandNotFound())
        ctx.assert_sent("je ne connais pas cette commande")

        # DisabledCommand
        ctx = mock_discord.get_ctx()
        await _on_command_error(config.bot, ctx, commands.DisabledCommand())
        ctx.assert_sent("Cette commande est désactivée")

        # ConversionError
        command = mock.Mock()
        ctx = mock_discord.get_ctx(command)
        exc = commands.ConversionError("bkrkr", "kak")
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent(["ce n'est pas comme ça qu'on utilise cette commande",
                         "ConversionError", "bkrkr", "kak"])
        config.bot.get_context.assert_called_with(ctx.message)
        self.assertEqual(ctx.message.content, f"!help {command.name}")
        config.bot.get_context.return_value.reinvoke.assert_called()

        # UserInputError
        command = mock.Mock()
        ctx = mock_discord.get_ctx(command)
        exc = commands.UserInputError("bakaka")
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent(["ce n'est pas comme ça qu'on utilise cette commande",
                         "UserInputError", "bakaka"])
        config.bot.get_context.assert_called_with(ctx.message)
        self.assertEqual(ctx.message.content, f"!help {command.name}")
        config.bot.get_context.return_value.reinvoke.assert_called()

        # UserInputError derivate
        command = mock.Mock()
        ctx = mock_discord.get_ctx(command)
        exc = commands.BadArgument("bakaka")
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent(["ce n'est pas comme ça qu'on utilise cette commande",
                         "BadArgument", "bakaka"])
        config.bot.get_context.assert_called_with(ctx.message)
        self.assertEqual(ctx.message.content, f"!help {command.name}")
        config.bot.get_context.return_value.reinvoke.assert_called()

        # CheckAnyFailure
        ctx = mock_discord.get_ctx()
        exc = commands.CheckAnyFailure(mock.ANY, mock.ANY)
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent("cette commande est réservée aux MJs")

        # MissingAnyRole
        ctx = mock_discord.get_ctx()
        exc = commands.MissingAnyRole([mock.ANY])
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent("Cette commande est réservée aux joueurs")

        # MissingRole
        ctx = mock_discord.get_ctx()
        exc = commands.MissingRole(mock.ANY)
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent("cette commande est réservée aux joueurs en vie")

        # one_command.AlreadyInCommand, not addIA/modifIA
        command = mock.Mock()
        command.configure_mock(name="blabla")
        ctx = mock_discord.get_ctx(command)
        exc = blocs.one_command.AlreadyInCommand()
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent("Impossible d'utiliser une commande pendant")

        # one_command.AlreadyInCommand, addIA
        command = mock.Mock()
        command.configure_mock(name="addIA")
        ctx = mock_discord.get_ctx(command)
        exc = blocs.one_command.AlreadyInCommand()
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent()

        # one_command.AlreadyInCommand, modifIA
        command = mock.Mock()
        command.configure_mock(name="modifIA")
        ctx = mock_discord.get_ctx(command)
        exc = blocs.one_command.AlreadyInCommand()
        await _on_command_error(config.bot, ctx, exc)
        ctx.assert_sent()

        # CheckFailure (autre check erreur)
        ctx = mock_discord.get_ctx()
        exc = commands.CheckFailure("jojo")
        with mock.patch("lgrez.blocs.tools.mention_MJ") as mmj_patch:
            await _on_command_error(config.bot, ctx, exc)
        mmj_patch.assert_called_once_with(ctx)
        ctx.assert_sent(["cette commande ne puisse pas être exécutée",
                         "CheckFailure", "jojo"])

        # other exception
        ctx = mock_discord.get_ctx()
        exc = AttributeError("oh")
        with mock.patch("lgrez.blocs.tools.mention_MJ") as mmj_patch:
            await _on_command_error(config.bot, ctx, exc)
        mmj_patch.assert_called_once_with(ctx)
        ctx.assert_sent(["Une erreur inattendue est survenue",
                         "AttributeError", "oh"])

        # other exception
        ctx = mock_discord.get_ctx()
        class SomeException(Exception):
            pass
        exc = SomeException("p!wet")
        with mock.patch("lgrez.blocs.tools.mention_MJ") as mmj_patch:
            await _on_command_error(config.bot, ctx, exc)
        mmj_patch.assert_called_once_with(ctx)
        ctx.assert_sent(["Une erreur inattendue est survenue",
                         "SomeException", "p!wet"])


    async def test__on_error(self):
        """Unit tests for bot._on_error function."""
        # async def _on_error(bot, event, *args, **kwargs)
        _on_error = bot._on_error

        # SQLAlchemyError
        exc = bdd.SQLAlchemyError("bzzt")
        with self.assertRaises(bdd.SQLAlchemyError):    # re-raised
            try:
                raise exc
            except bdd.SQLAlchemyError:
                # called within a running except block
                await _on_error(config.bot, "event")
        mock_discord.assert_sent(
            config.Channel.logs, "Rollback session",
            [f"{config.Role.mj.mention} ALED : Exception Python",
             "Traceback", "SQLAlchemyError", "bzzt"])
        config.Channel.logs.send.reset_mock()
        config.session.rollback.assert_called_once()
        config.session.rollback.reset_mock()

        # DriverOperationalError
        exc = bdd.DriverOperationalError("koook")
        with self.assertRaises(bdd.DriverOperationalError):    # re-raised
            try:
                raise exc
            except bdd.DriverOperationalError:
                # called within a running except block
                await _on_error(config.bot, "event")
        mock_discord.assert_sent(
            config.Channel.logs, "Rollback session",
            [f"{config.Role.mj.mention} ALED : Exception Python",
             "Traceback", bdd.DriverOperationalError.__name__, "koook"])
        config.Channel.logs.send.reset_mock()
        config.session.rollback.assert_called_once()
        config.session.rollback.reset_mock()

        # BDD error - session not ready : on vérifie juste que pas d'erreur
        exc = bdd.SQLAlchemyError("bzzt")
        _session = config.session
        del config.session
        with self.assertRaises(bdd.SQLAlchemyError):    # re-raised
            try:
                raise exc
            except bdd.SQLAlchemyError:
                # called within a running except block
                await _on_error(config.bot, "event")
        mock_discord.assert_sent(
            config.Channel.logs,
            [f"{config.Role.mj.mention} ALED : Exception Python",
             "Traceback", "SQLAlchemyError", "bzzt"])
        config.Channel.logs.send.reset_mock()
        config.session = _session

        # other exception
        class SomeException(Exception):
            pass
        with self.assertRaises(SomeException):    # re-raised
            try:
                raise SomeException("!a!", "@b@", "^c^")
            except SomeException:
                # called within a running except block
                await _on_error(config.bot, "event")
        mock_discord.assert_sent(
            config.Channel.logs,
            [f"{config.Role.mj.mention} ALED : Exception Python",
             "Traceback", "SomeException", "!a!", "@b@", "^c^"])
        config.Channel.logs.send.reset_mock()



class TestLGBot(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.LGBot class methods."""

    # def setUp(self):
    #     mock_discord.mock_config()
    #
    # def tearDown(self):
    #     mock_discord.unmock_config()


    @mock.patch("lgrez.features.informations.Informations")
    @mock.patch("lgrez.features.voter_agir.VoterAgir")
    @mock.patch("lgrez.features.actions_publiques.ActionsPubliques")
    @mock.patch("lgrez.features.open_close.OpenClose")
    @mock.patch("lgrez.features.sync.Sync")
    @mock.patch("lgrez.features.taches.GestionTaches")
    @mock.patch("lgrez.features.communication.Communication")
    @mock.patch("lgrez.features.IA.GestionIA")
    @mock.patch("lgrez.features.annexe.Annexe")
    @mock.patch("lgrez.features.special.Special")
    async def test___init__(self, *cog_patches):
        """Unit tests for bot.__init__ function."""
        # def __init__(self, command_prefix="!", case_insensitive=True,
        #              description=None, intents=None, member_cache_flags=None,
        #              **kwargs)
        __init__ = bot.LGBot.__init__

        # all default
        created = mock.MagicMock(bot.LGBot)
        with mock.patch("discord.ext.commands.Bot.__init__") as bot_patch:
            __init__(created)
        bot_patch.assert_called_once_with(
            command_prefix="!", description=bot.default_descr,
            case_insensitive=True, intents=discord.Intents.all(),
            member_cache_flags=discord.MemberCacheFlags.all()
        )

        self.assertIsNone(created.GUILD_ID)
        self.assertEqual(created.in_stfu, [])
        self.assertEqual(created.in_fals, [])
        self.assertEqual(created.tasks, {})
        self.assertEqual(created.in_command, [])
        created.add_check.assert_called_once_with(
            blocs.one_command.not_in_command)
        created.before_invoke.assert_called_once_with(
            blocs.one_command.add_to_in_command)
        created.after_invoke.assert_called_once_with(
            blocs.one_command.remove_from_in_command)
        created.remove_command.assert_called_once_with("help")
        for patch in cog_patches:
            patch.assert_called_once_with(created)
        self.assertEqual(
            {call.args[0] for call in created.add_cog.call_args_list},
            {patch.return_value for patch in cog_patches},
        )

        # all custom
        created = mock.MagicMock(bot.LGBot)
        with mock.patch("discord.ext.commands.Bot.__init__") as bot_patch:
            __init__(created, command_prefix="<gez>", case_insensitive=False,
                     description="@descr@", intents=35, member_cache_flags=12,
                     aaa=15, blblbl="oh")
        bot_patch.assert_called_once_with(
            command_prefix="<gez>", description="@descr@",
            case_insensitive=False, intents=35, member_cache_flags=12,
            aaa=15, blblbl="oh"
        )


    @mock.patch("lgrez.bot._on_ready")
    async def test_on_ready(self, ptch):
        """Unit tests for bot.on_ready function."""
        # async def on_ready(self), on_ready(self)
        bt = mock.Mock()
        await bot.LGBot.on_ready(bt)
        ptch.assert_called_once_with(bt)

    @mock.patch("lgrez.bot._on_member_join")
    async def test_on_member_join(self, ptch):
        """Unit tests for bot.on_member_join function."""
        # async def on_member_join(bt, member)
        bt, member = mock.Mock(), mock.Mock()
        await bot.LGBot.on_member_join(bt, member)
        ptch.assert_called_once_with(bt, member)

    @mock.patch("lgrez.bot._on_member_remove")
    async def test_on_member_remove(self, ptch):
        """Unit tests for bot.on_member_remove function."""
        # async def on_member_remove(bt, member)
        bt, member = mock.Mock(), mock.Mock()
        await bot.LGBot.on_member_remove(bt, member)
        ptch.assert_called_once_with(bt, member)

    @mock.patch("lgrez.bot._on_message")
    async def test_on_message(self, ptch):
        """Unit tests for bot.on_message function."""
        # async def on_message(bt, message)
        bt, message = mock.Mock(), mock.Mock()
        await bot.LGBot.on_message(bt, message)
        ptch.assert_called_once_with(bt, message)

    @mock.patch("lgrez.bot._on_raw_reaction_add")
    async def test_on_raw_reaction_add(self, ptch):
        """Unit tests for bot.on_raw_reaction_add function."""
        # async def on_raw_reaction_add(bt, payload)
        bt, payload = mock.Mock(), mock.Mock()
        await bot.LGBot.on_raw_reaction_add(bt, payload)
        ptch.assert_called_once_with(bt, payload)

    @mock.patch("lgrez.bot._on_command_error")
    async def test_on_command_error(self, ptch):
        """Unit tests for bot.on_command_error function."""
        # async def on_command_error(bt, ctx, exc)
        bt, ctx, exc = mock.Mock(), mock.Mock(), mock.Mock()
        await bot.LGBot.on_command_error(bt, ctx, exc)
        ptch.assert_called_once_with(bt, ctx, exc)

    @mock.patch("lgrez.bot._on_error")
    async def test_on_error(self, ptch):
        """Unit tests for bot.on_error function."""
        # async def on_error(bt, event, *args, **kwargs)
        bt, event = mock.Mock(), mock.Mock()
        args = [mock.Mock(), mock.Mock(), mock.Mock()]
        kwargs = {"a": mock.Mock(), "bzzt": mock.Mock()}
        await bot.LGBot.on_error(bt, event, *args, **kwargs)
        ptch.assert_called_once_with(bt, event, *args, **kwargs)


    async def test_i_am_alive(self):
        """Unit tests for bot.i_am_alive function."""
        # def i_am_alive(self, filename="alive.log")
        i_am_alive = bot.LGBot.i_am_alive
        bt = mock.Mock()

        # default filename
        with freezegun.freeze_time(datetime.datetime.utcfromtimestamp(75824)):
            with mock.patch("builtins.open", mock.mock_open()) as open_mock:
                i_am_alive(bt)
        open_mock.assert_called_once_with("alive.log", "w")
        open_mock.return_value.write.assert_called_once_with("75824.0")
        bt.loop.call_later.assert_called_once_with(60, bt.i_am_alive,
                                                   "alive.log")
        open_mock.reset_mock()
        bt.reset_mock()

        # custom filename
        with freezegun.freeze_time(datetime.datetime.utcfromtimestamp(75824)):
            with mock.patch("builtins.open", mock.mock_open()) as open_mock:
                i_am_alive(bt, "krkrkr")
        open_mock.assert_called_once_with("krkrkr", "w")
        open_mock.return_value.write.assert_called_once_with("75824.0")
        bt.loop.call_later.assert_called_once_with(60, bt.i_am_alive, "krkrkr")


    @mock_env.patch_env(LGREZ_DISCORD_TOKEN="t@ken",
                        LGREZ_SERVER_ID="12345")
    @mock.patch("lgrez.bdd.connect")
    @mock.patch("builtins.print")
    async def test_run(self, ppatch, connect_patch):
        """Unit tests for bot.run function."""
        # def run(self, **kwargs)
        run = bot.LGBot.run
        bt = mock.Mock(bot.LGBot)
        kwargs = {"a": mock.Mock(), "bzzt": mock.Mock()}

        # default filename
        with mock.patch("discord.ext.commands.Bot.run") as run_patch:
            run(bt, **kwargs)
        self.assertEqual(ppatch.call_count, 5)
        vers, codb, codbok, codi, deco = ppatch.call_args_list
        self.assertIn(__version__, vers.args[0])
        self.assertEqual(bt.GUILD_ID, 12345)
        self.assertIn("Connecting", codb.args[0])
        connect_patch.assert_called_once()
        self.assertIn("Connected", codbok.args[0])
        self.assertEqual(config.bot, bt)
        del config.bot
        self.assertIn("Connecting", codi.args[0])
        run_patch.assert_called_once_with("t@ken", **kwargs)
        self.assertIn("Disconnected", deco.args[0])
