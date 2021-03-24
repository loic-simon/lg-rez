import unittest
from unittest import mock

import discord

from lgrez import config, bdd, blocs, features, __version__
from lgrez.features import special
from test import mock_discord



class TestSpecialFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.special functions."""

    @mock.patch("lgrez.blocs.one_command.bypass")
    async def test__filter_runnables(self, bp_patch):
        """Unit tests for _filter_runnables function."""
        # async def _filter_runnables(commands, ctx)
        _filter_runnables = special._filter_runnables

        commands = [
            mock.Mock(can_run=mock.AsyncMock(return_value=True)),
            mock.Mock(can_run=mock.AsyncMock(return_value=False)),
            mock.Mock(can_run=mock.AsyncMock(side_effect=RuntimeError)),
        ]
        ctx = mock.Mock()
        res = await _filter_runnables(commands, ctx)
        bp_patch.assert_called_once_with(ctx)
        bp_patch.return_value.__enter__.assert_called_once()
        self.assertEqual(res, [commands[0]])



class TestSpecial(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.special commands."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = special.Special(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()


    async def test_panik(self):
        """Unit tests for !panik command."""
        # async def panik(self, ctx)
        panik = self.cog.panik

        ctx = mock_discord.get_ctx(panik)
        with mock.patch("sys.exit") as exit_patch:
            await ctx.invoke()
        exit_patch.assert_called_once()


    async def test_do(self):
        """Unit tests for !do command."""
        # async def do(self, ctx, *, code)
        do = self.cog.do

        samples = {
            "1": 1,
            "1 + 2": 3,
            "37*(5-2)": 37*(5-2),
            "config.debut_saison": config.debut_saison,
            "blocs.tools.montre()": blocs.tools.montre(),
            "tools.montre()": blocs.tools.montre(),
            "features.sync.transtype": features.sync.transtype,
            "bdd.Joueur": bdd.Joueur,
            "Joueur": bdd.Joueur,
        }

        # Vérification bases + accès à tous modules
        for sample, result in samples.items():
            ctx = mock_discord.get_ctx(do, code=sample)
            await ctx.invoke()
            ctx.assert_sent(str(result))

        # Vérification coroutines
        ctx = mock_discord.get_ctx(do, code="ctx.send('oh' + 'ah')")
        ctx.send.return_value = "bookz"
        await ctx.invoke()
        ctx.assert_sent("ohah", "bookz")

        # Vérification erreurs
        ctx = mock_discord.get_ctx(do, code="blbllb")
        with self.assertRaises(NameError):
            await ctx.invoke()
        ctx.assert_sent()


    @mock.patch("lgrez.blocs.realshell.RealShell")
    async def test_shell(self, rs_patch):
        """Unit tests for !shell command."""
        # async def shell(self, ctx)
        shell = self.cog.shell
        rs_patch().interact = mock.AsyncMock()
        rs_patch.reset_mock()

        # Okay
        ctx = mock_discord.get_ctx(shell)
        await ctx.invoke()
        rs_patch.assert_called_once_with(ctx.channel, mock.ANY)
        self.assertEqual(rs_patch.call_args.args[1]["ctx"], ctx)
        ctx.assert_sent()
        rs_patch.reset_mock()

        # Exit
        rs_patch().interact.side_effect = blocs.realshell.RealShellExit
        rs_patch.reset_mock()
        ctx = mock_discord.get_ctx(shell)
        with self.assertRaises(blocs.tools.CommandExit):
            await ctx.invoke()
        rs_patch.assert_called_once_with(ctx.channel, mock.ANY)
        self.assertEqual(rs_patch.call_args.args[1]["ctx"], ctx)
        ctx.assert_sent()


    @mock.patch("lgrez.blocs.tools.member")
    @mock.patch("lgrez.features.inscription.main")
    async def test_co(self, im_patch, mb_patch):
        """Unit tests for !co command."""
        # async def co(self, ctx, cible=None)
        co = self.cog.co

        # no cible
        ctx = mock_discord.get_ctx(co)
        await ctx.invoke()
        im_patch.assert_called_once_with(ctx.author)
        mb_patch.assert_not_called()
        im_patch.reset_mock()

        # cible = non-existing player
        mb_patch.side_effect = ValueError
        ctx = mock_discord.get_ctx(co, cible="booo")
        await ctx.invoke()
        ctx.assert_sent("introuvable")
        im_patch.assert_not_called()
        mb_patch.reset_mock(side_effect=True)

        # cible = existing player
        ctx = mock_discord.get_ctx(co, cible="noice")
        await ctx.invoke()
        mb_patch.assert_called_once_with("noice")
        im_patch.assert_called_once_with(mb_patch.return_value)


    @mock.patch("lgrez.blocs.tools.boucle_query_joueur")
    @mock.patch("lgrez.blocs.one_command.bypass")
    async def test_doas(self, ocb_patch, bqj_patch):
        """Unit tests for !doas command."""
        # async def doas(self, ctx, *, qui_quoi)
        doas = self.cog.doas

        # bad argument
        ctx = mock_discord.get_ctx(doas, qui_quoi="brbbrbr")
        with self.assertRaises(discord.ext.commands.UserInputError):
            await ctx.invoke()
        ctx = mock_discord.get_ctx(doas, qui_quoi="brbbr!br")
        with self.assertRaises(discord.ext.commands.UserInputError):
            await ctx.invoke()
        ocb_patch.assert_not_called()
        bqj_patch.assert_not_called()
        config.bot.process_commands.assert_not_called()

        # proceed
        ctx = mock_discord.get_ctx(doas, qui_quoi="bizz !kmd argz")
        await ctx.invoke()
        bqj_patch.assert_called_once_with(ctx, "bizz")
        ocb_patch.assert_called_once_with(ctx)
        config.bot.process_commands.assert_called_once_with(ctx.message)
        self.assertEqual(ctx.message.author, bqj_patch.return_value.member)
        self.assertEqual(ctx.message.content, "!kmd argz")


    @mock.patch("lgrez.blocs.one_command.bypass")
    async def test_secret(self, ocb_patch):
        """Unit tests for !secret command."""
        # async def secret(self, ctx, *, quoi)
        secret = self.cog.secret

        # proceed
        ctx = mock_discord.get_ctx(secret, quoi="krkrkrk")
        await ctx.invoke()
        ctx.message.delete.assert_called_once()
        ocb_patch.assert_called_once_with(ctx)
        config.bot.process_commands.assert_called_once_with(ctx.message)
        self.assertEqual(ctx.message.content, "krkrkrk")


    async def test_stop(self):
        """Unit tests for !stop command."""
        # async def stop(self, ctx)
        stop = self.cog.stop
        config.bot.in_command = [11, 12]

        # not in bot.in_command
        ctx = mock_discord.get_ctx(stop)
        ctx.channel.id = 13
        await ctx.invoke()
        self.assertEqual(config.bot.in_command, [11, 12])

        # in bot.in_command
        ctx = mock_discord.get_ctx(stop)
        ctx.channel.id = 12
        await ctx.invoke()
        self.assertEqual(config.bot.in_command, [11])


    async def test_help(self):
        """Unit tests for !help command."""
        # async def help(self, ctx, *, command=None)
        help = self.cog.help

        def _mock_cmd(name, help, short_doc, signature, cog=None,
                      runnable=True, aliases=[]):
            cmd = mock.MagicMock(discord.ext.commands.Command, name=name)
            cmd.configure_mock(
                name=name,
                help=help,
                short_doc=short_doc,
                signature=signature,
                cog=cog,
                can_run=mock.AsyncMock(return_value=runnable),
                aliases=aliases,
            )
            return cmd

        def _mock_cog(name, description, commands=[]):
            CogMock = type(name, (mock.MagicMock, ), {})
            cog = CogMock(discord.ext.commands.Cog, name=name)
            cog.configure_mock(
                description=description,
                commands=commands,
            )
            return cog

        compdoc = """Shorthand line.

        Descriptif de la commande, a ``texte Sphinx brut`` b
        Args:
            oui les arguments
        Warning:
            attention !

        :objet:`énorme`: klakla, :allo: !
        """

        cogs = {
            "cog1": _mock_cog("Cog1", "cogzz1"),
            "cog2": _mock_cog("Cog2", "cogzz2"),
            "cog3": _mock_cog("Cog3", "cogzz3"),
            "cog4": _mock_cog("Cog4", "cogzz4"),
            }
        cmds = [
            _mock_cmd("cmd1", "commz1\n\ndoc1", "szdk1", "sig1",
                      runnable=True, cog=cogs["cog1"]),
            _mock_cmd("cmd2", "commz2\n\ndoc2", "szdk2", "sig2",
                      runnable=False, cog=cogs["cog1"], aliases=["okm2"]),
            _mock_cmd("cm2b", "comm2b\n\ndo2b", "szd2b", "si2b",
                      runnable=True, cog=cogs["cog1"], aliases=["okm2b"]),
            _mock_cmd("cmd3", "commz3\n\ndoc3", "szdk3", "sig3",
                      runnable=True, cog=cogs["cog2"],
                      aliases=["okm31", "okm32"]),
            _mock_cmd("cmd4", f"commz4\n\n{compdoc}", "szdk4", "sig4",
                      runnable=True),
            _mock_cmd("cmd5", "commz5\n\ndoc5", "szdk5", "sig5",
                      runnable=False, cog=cogs["cog3"], aliases=["okm5"]),
        ]
        cogs["cog1"].get_commands.return_value = cmds[:3]
        cogs["cog2"].get_commands.return_value = [cmds[3]]
        cogs["cog3"].get_commands.return_value = [cmds[5]]

        config.bot.description = "deskrzz"
        config.bot.commands = cmds
        config.bot.cogs = cogs

        # list commands
        ctx = mock_discord.get_ctx(help)
        await ctx.invoke()
        ctx.assert_sent([
            "deskrzz", f"v{__version__}",
            "Cog1", "cogzz1", "!cmd1", "szdk1", "!cm2b", "szd2b",
            "Cog2", "cogzz2", "!cmd3", "szdk3",
            "Commandes isolées", "!cmd4", "szdk4",
        ])
        ctx.assert_not_sent([
            "Cog3", "cogzz3", "Cog4", "cogzz4",
            "!cmd2", "szdk2", "!cmd5", "szdk5",
        ])

        # !help <unknown command>
        ctx = mock_discord.get_ctx(help, command="blebele")
        await ctx.invoke()
        ctx.assert_sent("Commande '!blebele' non trouvée")

        # !help cmd1
        ctx = mock_discord.get_ctx(help, command="cmd1")
        await ctx.invoke()
        ctx.assert_sent([
            "!cmd1", "sig1", "commz1", "doc1"
        ])

        # !help !cmd2
        ctx = mock_discord.get_ctx(help, command="!cmd2")
        await ctx.invoke()
        ctx.assert_sent([
            "!cmd2", "sig2", "commz2", "doc2", "okm2"
        ])

        # !help ! cmd2b
        ctx = mock_discord.get_ctx(help, command="! cm2b")
        await ctx.invoke()
        ctx.assert_sent([
            "!cm2b", "si2b", "comm2b", "do2b", "okm2b"
        ])

        # !help okm31 (alias)
        ctx = mock_discord.get_ctx(help, command="okm31")
        await ctx.invoke()
        ctx.assert_sent([
            "!cmd3", "sig3", "commz3", "doc3", "okm31", "okm32"
        ])

        # !help cmd4 (complex doc, formatted)
        ctx = mock_discord.get_ctx(help, command="cmd4")
        await ctx.invoke()
        ctx.assert_sent([
            "!cmd4", "sig4", "commz4", "Shorthand line.",
            "a `texte Sphinx brut` b", "Arguments :", "Avertissement :",
            "`énorme`: klakla", ":allo:",
        ])
        ctx.assert_not_sent([
            "``texte", "Args:", "Warning:", ":objet:",
        ])

        # !help {otherprefix} okm5 (alias)
        config.bot.command_prefix = "@<>"
        ctx = mock_discord.get_ctx(help, command="@<> okm5")
        await ctx.invoke()
        ctx.assert_sent([
            "@<>cmd5", "sig5", "commz5", "doc5", "okm5"
        ])



    async def test_apropos(self):
        """Unit tests for !apropos command."""
        # async def apropos(self, ctx)
        apropos = self.cog.apropos
        config.bot.description = "deskrzz"
        config.bot.user.avatar_url = "uzavurlz"

        ctx = mock_discord.get_ctx(apropos)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("embed", ctx.send.call_args.kwargs)
        embed = ctx.send.call_args.kwargs["embed"]
        self.assertIn(f"v{__version__}", embed.title)
        self.assertEqual("deskrzz", embed.description)
        self.assertEqual("uzavurlz", embed.author.icon_url)
        self.assertIn("logo_espci.png", embed.image.url)
