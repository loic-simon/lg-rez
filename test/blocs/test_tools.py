import asyncio
import datetime
import unittest
from unittest import mock

import discord
from discord.ext import commands
import freezegun

from lgrez import config, bdd
from lgrez.blocs import tools
from test import mock_discord



class TestToolsObjectsUtilities(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.tools utility functions (section 1)."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    def test__find_by_mention_or_name(self):
        """Unit tests for tools._find_by_mention_or_name function."""
        # def _find_by_mention_or_name(collec, val, pattern=None,
        #                              must_be_found=False, raiser=None)
        _find_by_mention_or_name = tools._find_by_mention_or_name
        names = ["ab", "dzk", "0077"]
        ids = [125, 1213135, 1218819]
        collec = [mock.Mock() for i in range(3)]
        for mk, name, id in zip(collec, names, ids):
            mk.configure_mock(id=id, name=name)

        # val False
        ret = _find_by_mention_or_name(collec, "")
        self.assertIsNone(ret)
        # val & must_be_found True
        with self.assertRaises(ValueError):
            _find_by_mention_or_name(collec, "", must_be_found=True)

        # val by name found
        ret = _find_by_mention_or_name(collec, "dzk")
        self.assertEqual(ret, collec[1])
        # val by name not found
        ret = _find_by_mention_or_name(collec, "dzK")
        self.assertIsNone(ret)
        # val by name not found & must_be_found True
        with self.assertRaises(ValueError):
            _find_by_mention_or_name(collec, "dzK", must_be_found=True)

        # val by pattern found
        ret = _find_by_mention_or_name(collec, "<1218819>",
                                       pattern=r"<([0-9]{7})>")
        self.assertEqual(ret, collec[2])
        # val by pattern not found
        ret = _find_by_mention_or_name(collec, "<1218820>",
                                       pattern=r"<([0-9]{7})>")
        self.assertIsNone(ret)
        # val by pattern not found & must_be_found True
        with self.assertRaises(ValueError):
            _find_by_mention_or_name(collec, "<1218820>", must_be_found=True,
                                     pattern=r"<([0-9]{7})>")


    @mock.patch("lgrez.blocs.tools._find_by_mention_or_name")
    def test_channel(self, fbn_patch):
        """Unit tests for tools.channel function."""
        # def channel(nom, must_be_found=True)
        channel = tools.channel
        nom = mock.Mock()
        # no arg
        res = channel(nom)
        fbn_patch.assert_called_once_with(
            config.guild.channels, nom, pattern="<#([0-9]{18})>",
            must_be_found=True, raiser=mock.ANY)
        self.assertEqual(res, fbn_patch.return_value)
        fbn_patch.reset_mock()
        # MBF False
        res = channel(nom, must_be_found=False)
        fbn_patch.assert_called_once_with(
            config.guild.channels, nom, pattern="<#([0-9]{18})>",
            must_be_found=False, raiser=mock.ANY)
        self.assertEqual(res, fbn_patch.return_value)


    @mock.patch("lgrez.blocs.tools._find_by_mention_or_name")
    def test_role(self, fbn_patch):
        """Unit tests for tools.role function."""
        # def role(nom, must_be_found=True)
        role = tools.role
        nom = mock.Mock()
        # no arg
        res = role(nom)
        fbn_patch.assert_called_once_with(
            config.guild.roles, nom, pattern="<@&([0-9]{18})>",
            must_be_found=True, raiser=mock.ANY)
        self.assertEqual(res, fbn_patch.return_value)
        fbn_patch.reset_mock()
        # MBF False
        res = role(nom, must_be_found=False)
        fbn_patch.assert_called_once_with(
            config.guild.roles, nom, pattern="<@&([0-9]{18})>",
            must_be_found=False, raiser=mock.ANY)
        self.assertEqual(res, fbn_patch.return_value)


    @mock.patch("lgrez.blocs.tools._find_by_mention_or_name")
    def test_member(self, fbn_patch):
        """Unit tests for tools.member function."""
        # def member(nom, must_be_found=True)
        member = tools.member
        nom = mock.Mock()
        # no arg
        res = member(nom)
        fbn_patch.assert_called_once_with(
            config.guild.members, nom, pattern="<@!([0-9]{18})>",
            must_be_found=True, raiser=mock.ANY)
        self.assertEqual(res, fbn_patch.return_value)
        fbn_patch.reset_mock()
        # MBF False
        res = member(nom, must_be_found=False)
        fbn_patch.assert_called_once_with(
            config.guild.members, nom, pattern="<@!([0-9]{18})>",
            must_be_found=False, raiser=mock.ANY)
        self.assertEqual(res, fbn_patch.return_value)


    @mock.patch("lgrez.blocs.tools._find_by_mention_or_name")
    def test_emoji(self, fbn_patch):
        """Unit tests for tools.emoji function."""
        # def emoji(nom, must_be_found=True)
        emoji = tools.emoji
        nom = mock.Mock()
        # no arg
        res = emoji(nom)
        fbn_patch.assert_called_once_with(
            config.guild.emojis, nom, pattern="<:.*:([0-9]{18})>",
            must_be_found=True, raiser=mock.ANY)
        self.assertEqual(res, fbn_patch.return_value)
        fbn_patch.reset_mock()
        # MBF False
        res = emoji(nom, must_be_found=False)
        fbn_patch.assert_called_once_with(
            config.guild.emojis, nom, pattern="<:.*:([0-9]{18})>",
            must_be_found=False, raiser=mock.ANY)
        self.assertEqual(res, fbn_patch.return_value)


    def test_mention_MJ(self):
        """Unit tests for tools.mention_MJ function."""
        # def mention_MJ(arg)
        mention_MJ = tools.mention_MJ
        _rmjn = config.Role.mj.name
        config.Role.mj.name = "bzzt"
        # arg = webhook
        arg = mock.Mock(discord.User)
        res = mention_MJ(arg)
        self.assertEqual(res, config.Role.mj.mention)
        # arg = Member < MJ
        arg = mock.Mock(discord.Member)
        arg.top_role.__ge__=lambda s, o: False
        res = mention_MJ(arg)
        self.assertEqual(res, config.Role.mj.mention)
        # arg = Member >= MJ
        arg = mock.Mock(discord.Member)
        arg.top_role.__ge__=lambda s, o: True
        res = mention_MJ(arg)
        self.assertEqual(res, "@bzzt")
        # arg = Context < MJ
        arg = mock.Mock(commands.Context, author=mock.Mock(discord.Member))
        arg.author.top_role.__ge__=lambda s, o: False
        res = mention_MJ(arg)
        self.assertEqual(res, config.Role.mj.mention)
        # arg = Context >= MJ
        arg.author.top_role.__ge__=lambda s, o: True
        res = mention_MJ(arg)
        self.assertEqual(res, "@bzzt")
        # reset
        config.Role.mj.name = _rmjn



class TestToolsDecorators(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.tools decorators (section 3)."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    async def test_mjs_only(self):
        """Unit tests for tools.mjs_only check."""
        # mjs_only = commands.check_any(...)
        # ==> mjs_only.predicate = coroutine ctx -> bool
        mjs_only = tools.mjs_only
        # webhook
        ctx = mock_discord.get_ctx()
        ctx.message.webhook_id = 12
        self.assertTrue(await mjs_only.predicate(ctx))
        # non-MJ
        ctx = mock_discord.get_ctx()
        ctx.author.roles = [config.Role.everyone, config.Role.joueur_en_vie]
        with self.assertRaises(commands.CheckAnyFailure):
            await mjs_only.predicate(ctx)
        # Rédacteur
        ctx.author.roles = [config.Role.everyone, config.Role.joueur_en_vie,
                            config.Role.redacteur]
        with self.assertRaises(commands.CheckAnyFailure):
            await mjs_only.predicate(ctx)
        # MJ
        ctx.author.roles = [config.Role.everyone, config.Role.mj]
        self.assertTrue(await mjs_only.predicate(ctx))


    async def test_mjs_et_redacteurs(self):
        """Unit tests for tools.mjs_et_redacteurs check."""
        # mjs_et_redacteurs = commands.check_any(...)
        # ==> mjs_et_redacteurs.predicate = coroutine ctx -> bool
        mjs_et_redacteurs = tools.mjs_et_redacteurs
        # webhook
        ctx = mock_discord.get_ctx()
        ctx.message.webhook_id = 12
        self.assertTrue(await mjs_et_redacteurs.predicate(ctx))
        # non-MJ
        ctx = mock_discord.get_ctx()
        ctx.author.roles = [config.Role.everyone, config.Role.joueur_en_vie]
        with self.assertRaises(commands.CheckAnyFailure):
            await mjs_et_redacteurs.predicate(ctx)
        # Rédacteur
        ctx.author.roles = [config.Role.everyone, config.Role.joueur_en_vie,
                            config.Role.redacteur]
        self.assertTrue(await mjs_et_redacteurs.predicate(ctx))
        # MJ
        ctx.author.roles = [config.Role.everyone, config.Role.mj]
        self.assertTrue(await mjs_et_redacteurs.predicate(ctx))


    async def test_joueurs_only(self):
        """Unit tests for tools.joueurs_only check."""
        # joueurs_only = commands.check_any(...)
        # ==> joueurs_only.predicate = coroutine ctx -> bool
        joueurs_only = tools.joueurs_only
        # webhook
        ctx = mock_discord.get_ctx()
        ctx.message.webhook_id = 12
        with self.assertRaises(commands.MissingAnyRole):
            await joueurs_only.predicate(ctx)
        # non-MJ
        ctx = mock_discord.get_ctx()
        ctx.author.roles = [config.Role.everyone, config.Role.joueur_en_vie]
        self.assertTrue(await joueurs_only.predicate(ctx))
        # Joueur mort
        ctx.author.roles = [config.Role.everyone, config.Role.joueur_mort]
        self.assertTrue(await joueurs_only.predicate(ctx))
        # MJ
        ctx.author.roles = [config.Role.everyone, config.Role.mj]
        with self.assertRaises(commands.MissingAnyRole):
            await joueurs_only.predicate(ctx)


    async def test_vivants_only(self):
        """Unit tests for tools.vivants_only check."""
        # vivants_only = commands.check_any(...)
        # ==> vivants_only.predicate = coroutine ctx -> bool
        vivants_only = tools.vivants_only
        # webhook
        ctx = mock_discord.get_ctx()
        ctx.message.webhook_id = 12
        with self.assertRaises(commands.MissingRole):
            await vivants_only.predicate(ctx)
        # non-MJ
        ctx = mock_discord.get_ctx()
        ctx.author.roles = [config.Role.everyone, config.Role.joueur_en_vie]
        self.assertTrue(await vivants_only.predicate(ctx))
        # Joueur mort
        ctx.author.roles = [config.Role.everyone, config.Role.joueur_mort]
        with self.assertRaises(commands.MissingRole):
            await vivants_only.predicate(ctx)
        # Joueur mort + rédacteur
        ctx.author.roles = [config.Role.everyone, config.Role.joueur_mort,
                            config.Role.redacteur]
        with self.assertRaises(commands.MissingRole):
            await vivants_only.predicate(ctx)
        # MJ
        ctx.author.roles = [config.Role.everyone, config.Role.mj]
        with self.assertRaises(commands.MissingRole):
            await vivants_only.predicate(ctx)


    @mock.patch("lgrez.bdd.Joueur.from_member")
    async def test_private(self, fm_patch):
        """Unit tests for tools.private decorator."""
        # def private(callback)
        private = tools.private
        callback = mock.AsyncMock()
        _pcp = config.private_chan_prefix
        config.private_chan_prefix = "pr€f-!x-"
        cog = mock.Mock()
        args = [mock.Mock() for i in range(5)]
        kwargs = {str(i): mock.Mock() for i in range(5)}

        # ok
        ctx = mock_discord.get_ctx()
        ctx.channel.name = "pr€f-!x-alloàtous"
        new = private(callback)
        await new(cog, ctx, *args, **kwargs)
        ctx.message.delete.assert_not_called()
        fm_patch.assert_not_called()
        ctx.assert_sent()
        callback.assert_called_once_with(cog, ctx, *args, **kwargs)
        callback.reset_mock()

        # not ok
        ctx = mock_discord.get_ctx()
        ctx.channel.name = "ono-alloàtous"
        ctx.message.content = "gzzzz"
        new = private(callback)
        await new(cog, ctx, *args, **kwargs)
        ctx.message.delete.assert_called_once()
        fm_patch.assert_called_once_with(ctx.author)
        ctx.assert_sent(["gzzzz", "interdite en dehors de ta conv privée"])
        self.assertEqual(ctx.channel, fm_patch.return_value.private_chan)
        callback.assert_called_once_with(cog, ctx, *args, **kwargs)

        # restore
        config.private_chan_prefix = _pcp



class TestToolsPlayerInteractors(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.tools player interactors (section 4)."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    async def test_wait_for_message(self):
        """Unit tests for tools.wait_for_message function."""
        # async def wait_for_message(check, trigger_on_commands=False)
        wait_for_message = tools.wait_for_message
        def primocheck(mess):
            return (mess.author != config.bot.user
                    and len(mess.content) > 4)

        # basic, pass
        config.bot.wait_for = mock.AsyncMock(return_value=mock.Mock(
            discord.Message, content="gloup"))
        mess = await wait_for_message(primocheck)
        config.bot.wait_for.assert_called_once_with("message", check=mock.ANY)
        check = config.bot.wait_for.call_args.kwargs["check"]
        self.assertTrue(check(mock.Mock(discord.Message, content="hmmooo")))
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmm")))
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmooo",
                                         author=config.bot.user)))
        self.assertTrue(check(mock.Mock(discord.Message, content="stop")))
        self.assertFalse(check(mock.Mock(discord.Message, content="!hmmo")))
        self.assertTrue(check(mock.Mock(discord.Message, content="!stop")))
        self.assertEqual(mess, config.bot.wait_for.return_value)

        # basic, stop, user
        config.bot.wait_for = mock.AsyncMock(return_value=mock.Mock(
            discord.Message, content="stop"))
        with self.assertRaises(tools.CommandExit) as cm:
            await wait_for_message(primocheck)
        config.bot.wait_for.assert_called_once_with("message", check=mock.ANY)
        self.assertIn("Arrêt demandé", cm.exception.args[0])

        # basic, stop, bot
        config.bot.wait_for = mock.AsyncMock(return_value=mock.Mock(
            discord.Message, content="stop", author=config.bot.user))
        with self.assertRaises(tools.CommandExit) as cm:
            await wait_for_message(primocheck)
        config.bot.wait_for.assert_called_once_with("message", check=mock.ANY)
        self.assertIn("Arrêt commande précédente", cm.exception.args[0])

        # toc True, pass
        config.bot.wait_for = mock.AsyncMock(return_value=mock.Mock(
            discord.Message, content="gloup"))
        mess = await wait_for_message(primocheck, trigger_on_commands=True)
        config.bot.wait_for.assert_called_once_with("message", check=mock.ANY)
        check = config.bot.wait_for.call_args.kwargs["check"]
        self.assertTrue(check(mock.Mock(discord.Message, content="hmmooo")))
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmm")))
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmooo",
                                         author=config.bot.user)))
        self.assertTrue(check(mock.Mock(discord.Message, content="stop")))
        self.assertTrue(check(mock.Mock(discord.Message, content="!hmmo")))
        self.assertTrue(check(mock.Mock(discord.Message, content="!stop")))
        self.assertEqual(mess, config.bot.wait_for.return_value)


    @mock.patch("lgrez.blocs.tools.wait_for_message")
    async def test_wait_for_message_here(self, wfm_patch):
        """Unit tests for tools.wait_for_message_here function."""
        # async def wait_for_message_here(ctx, trigger_on_commands=False)
        wait_for_message_here = tools.wait_for_message_here
        ctx = mock_discord.get_ctx()

        # basic
        wfm_patch.return_value = mock.Mock(discord.Message, content="gloup")
        mess = await wait_for_message_here(ctx)
        wfm_patch.assert_called_once_with(check=mock.ANY,
                                          trigger_on_commands=False)
        check = wfm_patch.call_args.kwargs["check"]
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmooo")))
        self.assertTrue(check(mock.Mock(discord.Message, content="hmmooo",
                                        channel=ctx.channel)))
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmooo",
                                         author=config.bot.user,
                                         channel=ctx.channel)))
        self.assertEqual(mess, wfm_patch.return_value)
        wfm_patch.reset_mock()

        # toc True
        wfm_patch.return_value = mock.Mock(discord.Message, content="gloup")
        mess = await wait_for_message_here(ctx, trigger_on_commands=True)
        wfm_patch.assert_called_once_with(check=mock.ANY,
                                          trigger_on_commands=True)
        check = wfm_patch.call_args.kwargs["check"]
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmooo")))
        self.assertTrue(check(mock.Mock(discord.Message, content="hmmooo",
                                        channel=ctx.channel)))
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmooo",
                                         author=config.bot.user,
                                         channel=ctx.channel)))
        self.assertEqual(mess, wfm_patch.return_value)


    @mock.patch("lgrez.blocs.tools.wait_for_message")
    async def test_boucle_message(self, wfm_patch):
        """Unit tests for tools.boucle_message function."""
        # async def boucle_message(chan, in_message, condition_sortie,
        #                          rep_message=None)
        boucle_message = tools.boucle_message

        # illegal
        with self.assertRaises(ValueError):
            await boucle_message(mock.Mock(), "", mock.Mock())

        # in_message only
        chan = mock_discord.chan(".")
        msgs = [mock.Mock(discord.Message, content="gloup1"),
                mock.Mock(discord.Message, content="gloup2"),
                mock.Mock(discord.Message, content="gloup3")]
        wfm_patch.side_effect = msgs
        condition_sortie = mock.Mock(side_effect=[False, False, True])
        mess = await boucle_message(chan, "in-m", condition_sortie)
        mock_discord.assert_sent(chan, "in-m", "in-m", "in-m")
        self.assertEqual(wfm_patch.call_count, 3)
        self.assertEqual(condition_sortie.call_count, 3)
        condition_sortie.assert_has_calls([mock.call(msg) for msg in msgs])
        check = wfm_patch.call_args.args[0]
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmooo")))
        self.assertTrue(check(mock.Mock(discord.Message, content="hmmooo",
                                        channel=chan)))
        self.assertFalse(check(mock.Mock(discord.Message, content="hmmooo",
                                         author=config.bot.user,
                                         channel=chan)))
        self.assertEqual(mess, msgs[2])
        wfm_patch.reset_mock()

        # rep_message only
        chan = mock_discord.chan(".")
        msgs = [mock.Mock(discord.Message, content="gloup1"),
                mock.Mock(discord.Message, content="gloup2")]
        wfm_patch.side_effect = msgs
        condition_sortie = mock.Mock(side_effect=[False, True])
        mess = await boucle_message(chan, "", condition_sortie, "rep-m")
        mock_discord.assert_sent(chan, "rep-m")
        self.assertEqual(wfm_patch.call_count, 2)
        self.assertEqual(condition_sortie.call_count, 2)
        condition_sortie.assert_has_calls([mock.call(msg) for msg in msgs])
        self.assertEqual(mess, msgs[1])
        wfm_patch.reset_mock()

        # in_message and rep_message
        chan = mock_discord.chan(".")
        msgs = [mock.Mock(discord.Message, content="gloup1"),
                mock.Mock(discord.Message, content="gloup2"),
                mock.Mock(discord.Message, content="gloup3"),
                mock.Mock(discord.Message, content="gloup4")]
        wfm_patch.side_effect = msgs
        condition_sortie = mock.Mock(side_effect=[False, False, False, True])
        mess = await boucle_message(chan, "in-m", condition_sortie, "rep-m")
        mock_discord.assert_sent(chan, "in-m", "rep-m", "rep-m", "rep-m")
        self.assertEqual(wfm_patch.call_count, 4)
        self.assertEqual(condition_sortie.call_count, 4)
        condition_sortie.assert_has_calls([mock.call(msg) for msg in msgs])
        self.assertEqual(mess, msgs[3])
        wfm_patch.reset_mock()


    @mock.patch("lgrez.bdd.Joueur.from_member")
    @mock.patch("lgrez.bdd.Joueur.find_nearest")
    @mock.patch("lgrez.blocs.tools.member")
    async def test_boucle_query_joueur(self, mb_patch, find_patch, fm_patch):
        """Unit tests for tools.boucle_query_joueur function."""
        # async def boucle_query_joueur(ctx, cible=None, message=None,
        #                               sensi=0.5)
        boucle_query_joueur = tools.boucle_query_joueur
        ctx = mock_discord.get_ctx()

        # simple, first answer direct
        with mock_discord.interact(
            ("wait_for_message_here",
             mock_discord.message(ctx, "([)>>]}{<gl()zz()[}]{><)"))):
            jr = await boucle_query_joueur(ctx)
        mb_patch.assert_called_once_with("gl()zz", must_be_found=False)
        fm_patch.assert_called_once_with(mb_patch.return_value)
        self.assertEqual(jr, fm_patch.return_value)
        find_patch.assert_not_called()
        mb_patch.reset_mock()
        fm_patch.reset_mock()
        ctx.assert_sent()

        cible = mock.Mock()
        jr = await boucle_query_joueur(ctx, cible)
        mb_patch.assert_called_once_with(cible, must_be_found=False)
        fm_patch.assert_called_once_with(mb_patch.return_value)
        self.assertEqual(jr, fm_patch.return_value)
        find_patch.assert_not_called()
        mb_patch.reset_mock()
        fm_patch.reset_mock()
        ctx.assert_sent()

        # simple, first answer direct but not inscit -> fn exact
        fm_patch.side_effect = ValueError
        expjr = mock.Mock()
        find_patch.return_value = [(expjr, 1)]
        with mock_discord.interact(("wait_for_message_here",
                                    mock_discord.message(ctx, "<gloozz>"))):
            jr = await boucle_query_joueur(ctx)
        mb_patch.assert_called_once_with("gloozz", must_be_found=False)
        fm_patch.assert_called_once_with(mb_patch.return_value)
        find_patch.assert_called_once_with(
            "gloozz", col=bdd.Joueur.nom, sensi=0.5,
            solo_si_parfait=False, match_first_word=True)
        self.assertEqual(jr, expjr)
        find_patch.reset_mock()
        mb_patch.reset_mock()
        fm_patch.reset_mock()
        ctx.assert_sent()

        # cible given, first answer direct but not inscit -> fn exact (+seed)
        cible = mock.Mock()
        fm_patch.side_effect = ValueError
        expjr = mock.Mock()
        find_patch.return_value = [(expjr, 1)]
        jr = await boucle_query_joueur(ctx, cible, sensi=0.3)
        mb_patch.assert_called_once_with(cible, must_be_found=False)
        fm_patch.assert_called_once_with(mb_patch.return_value)
        find_patch.assert_called_once_with(
            cible, col=bdd.Joueur.nom, sensi=0.3,
            solo_si_parfait=False, match_first_word=True)
        self.assertEqual(jr, expjr)
        find_patch.reset_mock()
        mb_patch.reset_mock()
        fm_patch.reset_mock(side_effect=True)
        ctx.assert_sent()

        # simple, no member found -> fn approx, OK
        mb_patch.return_value = None
        expjr = mock.Mock(nom="boulip")
        find_patch.return_value = [(expjr, 0.8)]
        with mock_discord.interact(("wait_for_message_here",
                                    mock_discord.message(ctx, "<gloozz>")),
                ("yes_no", True)):
            jr = await boucle_query_joueur(ctx)
        mb_patch.assert_called_once_with("gloozz", must_be_found=False)
        find_patch.assert_called_once_with(
            "gloozz", col=bdd.Joueur.nom, sensi=0.5,
            solo_si_parfait=False, match_first_word=True)
        self.assertEqual(jr, expjr)
        fm_patch.assert_not_called()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["qu'une correspondance", "boulip"])
        ctx.reset_mock()

        # cible given, no member found -> fn approx, OK
        cible = mock.Mock()
        mb_patch.return_value = None
        expjr = mock.Mock(nom="boulip")
        find_patch.return_value = [(expjr, 0.8)]
        with mock_discord.interact(("yes_no", True)):
            jr = await boucle_query_joueur(ctx, cible)
        mb_patch.assert_called_once_with(cible, must_be_found=False)
        find_patch.assert_called_once_with(
            cible, col=bdd.Joueur.nom, sensi=0.5,
            solo_si_parfait=False, match_first_word=True)
        self.assertEqual(jr, expjr)
        fm_patch.assert_not_called()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["qu'une correspondance", "boulip"])
        ctx.reset_mock()


        # simple, no member found -> fn several, choice
        cible = mock.Mock()
        mb_patch.return_value = None
        expjrs = [mock.Mock(nom="boulip"), mock.Mock(nom="boul2"),
                  mock.Mock(nom="boo3"), mock.Mock(nom="bblbl4")]
        find_patch.return_value = list(zip(expjrs, [0.8, 0.8, 0.7, 0.5]))
        with mock_discord.interact(("wait_for_message_here",
                                    mock_discord.message(ctx, "<gloozz>")),
                ("choice", 3)) as int:
            jr = await boucle_query_joueur(ctx)
        mb_patch.assert_called_once_with("gloozz", must_be_found=False)
        find_patch.assert_called_once_with(
            "gloozz", col=bdd.Joueur.nom, sensi=0.5,
            solo_si_parfait=False, match_first_word=True)
        self.assertEqual(jr, expjrs[2])
        int.patchs["choice"].assert_called_with(config.bot, mock.ANY, 4)
        fm_patch.assert_not_called()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["joueurs les plus proches", f"1️⃣. boulip",
                         f"2️⃣. boul2", f"3️⃣. boo3", f"4️⃣. bblbl4",
                         "réagissant", "répondant"])
        ctx.reset_mock()

        # cible given, no member found -> fn several, choice (with > 10)
        cible = mock.Mock()
        mb_patch.return_value = None
        expjrs = [mock.Mock(nom=f"boul{i}") for i in range(15)]
        find_patch.return_value = list(zip(expjrs, [0.8]*15))
        with mock_discord.interact(("choice", 5)) as int:
            jr = await boucle_query_joueur(ctx, cible)
        mb_patch.assert_called_once_with(cible, must_be_found=False)
        find_patch.assert_called_once_with(
            cible, col=bdd.Joueur.nom, sensi=0.5,
            solo_si_parfait=False, match_first_word=True)
        self.assertEqual(jr, expjrs[4])
        int.patchs["choice"].assert_called_with(config.bot, mock.ANY, 10)
        fm_patch.assert_not_called()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["joueurs les plus proches", f"boul{0}",
                         f"🔟. boul9", "réagissant", "répondant"])
        ctx.reset_mock()


        # simple, no member found -> fn approx, DENY -> direct
        j2 = mock.Mock()
        mb_patch.side_effect = [None, j2]
        expjr = mock.Mock(nom="boulip")
        find_patch.return_value = [(expjr, 0.8)]
        with mock_discord.interact(("wait_for_message_here",
                                    mock_discord.message(ctx, "<gloozz>")),
             ("yes_no", False),
             ("wait_for_message_here", mock_discord.message(ctx, "<othy>"))):
            jr = await boucle_query_joueur(ctx)
        self.assertEqual(mb_patch.call_count, 2)
        mb_patch.assert_has_calls([
            mock.call("gloozz", must_be_found=False),
            mock.call("othy", must_be_found=False)])
        find_patch.assert_called_once_with(
            "gloozz", col=bdd.Joueur.nom, sensi=0.5,
            solo_si_parfait=False, match_first_word=True)
        fm_patch.assert_called_once_with(j2)
        self.assertEqual(jr, fm_patch.return_value)
        fm_patch.reset_mock()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["qu'une correspondance", "boulip"],
                         "d'accord, alors qui")
        ctx.reset_mock()

        # cible given, no member found -> fn approx, DENY -> direct
        cible = mock.Mock()
        j2 = mock.Mock()
        mb_patch.side_effect = [None, j2]
        expjr = mock.Mock(nom="boulip")
        find_patch.return_value = [(expjr, 0.8)]
        with mock_discord.interact(("yes_no", False),
             ("wait_for_message_here", mock_discord.message(ctx, "<othy>"))):
            jr = await boucle_query_joueur(ctx, cible)
        self.assertEqual(mb_patch.call_count, 2)
        mb_patch.assert_has_calls([
            mock.call(cible, must_be_found=False),
            mock.call("othy", must_be_found=False)])
        find_patch.assert_called_once_with(
            cible, col=bdd.Joueur.nom, sensi=0.5,
            solo_si_parfait=False, match_first_word=True)
        fm_patch.assert_called_once_with(j2)
        self.assertEqual(jr, fm_patch.return_value)
        fm_patch.reset_mock()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["qu'une correspondance", "boulip"],
                         "d'accord, alors qui")
        ctx.reset_mock()


        # simple, no member found -> fn none, redo -> direct
        j2 = mock.Mock()
        mb_patch.side_effect = [None, j2]
        find_patch.return_value = []
        with mock_discord.interact(("wait_for_message_here",
                                    mock_discord.message(ctx, "<gloozz>")),
             ("wait_for_message_here", mock_discord.message(ctx, "<othy>"))):
            jr = await boucle_query_joueur(ctx)
        self.assertEqual(mb_patch.call_count, 2)
        mb_patch.assert_has_calls([
            mock.call("gloozz", must_be_found=False),
            mock.call("othy", must_be_found=False)])
        find_patch.assert_called_once_with(
            "gloozz", col=bdd.Joueur.nom, sensi=0.5,
            solo_si_parfait=False, match_first_word=True)
        fm_patch.assert_called_once_with(j2)
        self.assertEqual(jr, fm_patch.return_value)
        fm_patch.reset_mock()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["Aucune entrée", "réessayer"])
        ctx.reset_mock()

        # cible given, no member found -> fn none -> direct
        cible = mock.Mock()
        j2 = mock.Mock()
        mb_patch.side_effect = [None, j2]
        find_patch.return_value = []
        with mock_discord.interact(
             ("wait_for_message_here", mock_discord.message(ctx, "<othy>"))):
            jr = await boucle_query_joueur(ctx, cible)
        self.assertEqual(mb_patch.call_count, 2)
        mb_patch.assert_has_calls([
            mock.call(cible, must_be_found=False),
            mock.call("othy", must_be_found=False)])
        find_patch.assert_called_once_with(
            cible, col=bdd.Joueur.nom, sensi=0.5,
            solo_si_parfait=False, match_first_word=True)
        fm_patch.assert_called_once_with(j2)
        self.assertEqual(jr, fm_patch.return_value)
        fm_patch.reset_mock()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["Aucune entrée", "réessayer"])
        ctx.reset_mock()

        # cible given, no member found -> fn none -> re none -> re -> -> direct
        cible = mock.Mock()
        j2 = mock.Mock()
        mb_patch.side_effect = [None, None, None, j2]
        find_patch.return_value = []
        with mock_discord.interact(
             ("wait_for_message_here", mock_discord.message(ctx, "<othy>")),
             ("wait_for_message_here", mock_discord.message(ctx, "(oula)")),
             ("wait_for_message_here", mock_discord.message(ctx, "{méssi}"))):
            jr = await boucle_query_joueur(ctx, cible)
        self.assertEqual(mb_patch.call_count, 4)
        mb_patch.assert_has_calls([
            mock.call(cible, must_be_found=False),
            mock.call("othy", must_be_found=False),
            mock.call("oula", must_be_found=False),
            mock.call("méssi", must_be_found=False)])
        self.assertEqual(find_patch.call_count, 3)
        find_patch.assert_has_calls([
            mock.call(cible, col=bdd.Joueur.nom, sensi=0.5,
                      solo_si_parfait=False, match_first_word=True),
            mock.call("othy", col=bdd.Joueur.nom, sensi=0.5,
                      solo_si_parfait=False, match_first_word=True),
            mock.call("oula", col=bdd.Joueur.nom, sensi=0.5,
                      solo_si_parfait=False, match_first_word=True)])
        fm_patch.assert_called_once_with(j2)
        self.assertEqual(jr, fm_patch.return_value)
        fm_patch.reset_mock()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["Aucune entrée", "réessayer"],
                        ["Aucune entrée", "réessayer"],
                        ["Aucune entrée", "réessayer"])
        ctx.reset_mock()

        # > 5 none
        cible = mock.Mock()
        mb_patch.side_effect = [None, None, None, None, None, None]
        find_patch.return_value = []
        with self.assertRaises(RuntimeError):
            with mock_discord.interact(
                 ("wait_for_message_here", mock_discord.message(ctx, "<ot>")),
                 ("wait_for_message_here", mock_discord.message(ctx, "(ou)")),
                 ("wait_for_message_here", mock_discord.message(ctx, "{mé}")),
                 ("wait_for_message_here", mock_discord.message(ctx, "[al]")),
                 ("wait_for_message_here", mock_discord.message(ctx, "po"))):
                jr = await boucle_query_joueur(ctx, cible)
        self.assertEqual(mb_patch.call_count, 5)
        self.assertEqual(find_patch.call_count, 5)
        fm_patch.assert_not_called()
        find_patch.reset_mock()
        mb_patch.reset_mock()
        ctx.assert_sent(["Aucune entrée", "réessayer"],
                        ["Aucune entrée", "réessayer"],
                        ["Aucune entrée", "réessayer"],
                        ["Aucune entrée", "réessayer"],
                        ["Aucune entrée", "réessayer"],
                        ["Et puis non"])
        ctx.reset_mock()


    @mock.patch("lgrez.blocs.tools.wait_for_message", new_callable=mock.Mock)
    @mock.patch("asyncio.create_task")
    @mock.patch("asyncio.wait")
    async def test_wait_for_react_clic(self, aw_patch, act_patch, wfm_patch):
        """Unit tests for tools.wait_for_react_clic function."""
        # async def wait_for_react_clic(message, emojis={}, *,
        #                               process_text=False, text_filter=None,
        #                               post_converter=None,
        #                               trigger_all_reacts=False,
        #                               trigger_on_commands=False)
        wait_for_react_clic = tools.wait_for_react_clic
        ctx = mock_discord.get_ctx()

        # simple, clic on react
        message = mock_discord.message(ctx)
        tasks = [mock.Mock(), mock.Mock()]      # react, message
        tasks[0].result.return_value.emoji = config.Emoji.lune
        act_patch.side_effect = tasks
        aw_patch.return_value = {tasks[0]}, {tasks[1]}

        ret = await wait_for_react_clic(message, {config.Emoji.lune: 1337,
                                                  "❤": 1565})
        config.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                    check=mock.ANY)
        wfm_patch.assert_called_once_with(trigger_on_commands=False,
                                          check=mock.ANY)
        react_check = config.bot.wait_for.call_args.kwargs["check"]
        message_check = wfm_patch.call_args.kwargs["check"]
        self.assertEqual(act_patch.call_count, 2)
        act_patch.assert_has_calls([mock.call(config.bot.wait_for.return_value),
                                    mock.call(wfm_patch.return_value)])
        aw_patch.assert_called_once_with(tasks,
                                         return_when=asyncio.FIRST_COMPLETED)
        self.assertEqual(message.remove_reaction.call_count, 2)
        message.remove_reaction.assert_has_calls([
            mock.call(config.Emoji.lune, config.bot.user),
            mock.call("❤", config.bot.user)])
        self.assertEqual(ret, 1337)
        aw_patch.reset_mock()
        act_patch.reset_mock()
        wfm_patch.reset_mock()

        # interlude: check checks
        message.id = 15
        config.bot.user.id = 33
        coeur = mock.Mock(discord.PartialEmoji)
        coeur.configure_mock(name="❤")
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=31,
                                               emoji=config.Emoji.maire)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=33,
                                               emoji=config.Emoji.maire)))
        self.assertFalse(react_check(mock.Mock(message_id=15, user_id=31,
                                               emoji=config.Emoji.maire)))
        self.assertFalse(react_check(mock.Mock(message_id=15, user_id=33,
                                               emoji=config.Emoji.maire)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=31,
                                               emoji=coeur)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=33,
                                               emoji=coeur)))
        self.assertTrue(react_check(mock.Mock(message_id=15, user_id=31,
                                               emoji=coeur)))
        self.assertFalse(react_check(mock.Mock(message_id=15, user_id=33,
                                               emoji=coeur)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=31,
                                               emoji=config.Emoji.lune)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=33,
                                               emoji=config.Emoji.lune)))
        self.assertTrue(react_check(mock.Mock(message_id=15, user_id=31,
                                               emoji=config.Emoji.lune)))
        self.assertFalse(react_check(mock.Mock(message_id=15, user_id=33,
                                               emoji=config.Emoji.lune)))
        chan = message.channel
        auth = config.bot.user
        self.assertFalse(message_check(mock.Mock(channel=chan, author="meh")))
        # messages not detected
        config.bot.wait_for.reset_mock()

        # message response
        message = mock_discord.message(ctx)
        tasks = [mock.Mock(), mock.Mock()]      # react, message
        tasks[1].result.return_value = mock.Mock(discord.Message,
                                                 content="alloz")
        act_patch.side_effect = tasks
        aw_patch.return_value = {tasks[1]}, {tasks[0]}

        ret = await wait_for_react_clic(message, {config.Emoji.lune: 1337},
                                        process_text=True)
        config.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                    check=mock.ANY)
        wfm_patch.assert_called_once_with(trigger_on_commands=False,
                                          check=mock.ANY)
        message_check = wfm_patch.call_args.kwargs["check"]
        self.assertEqual(act_patch.call_count, 2)
        act_patch.assert_has_calls(
            [mock.call(config.bot.wait_for.return_value),
             mock.call(wfm_patch.return_value)])
        aw_patch.assert_called_once_with(
            tasks, return_when=asyncio.FIRST_COMPLETED)
        mess = tasks[1].result.return_value
        message.clear_reactions.assert_called_once()
        self.assertEqual(ret, "alloz")
        aw_patch.reset_mock()
        act_patch.reset_mock()
        wfm_patch.reset_mock()
        config.bot.wait_for.reset_mock()

        # interlude: check check
        chan = message.channel
        auth = config.bot.user
        self.assertFalse(message_check(mock.Mock(channel="oh", author="meh")))
        self.assertFalse(message_check(mock.Mock(channel="oh", author=auth)))
        self.assertTrue(message_check(mock.Mock(channel=chan, author="meh")))
        self.assertFalse(message_check(mock.Mock(channel=chan, author=auth)))

        # simple, clic on react unicode
        message = mock_discord.message(ctx)
        tasks = [mock.Mock(), mock.Mock()]      # react, message
        tasks[0].result.return_value.emoji = "❤"
        act_patch.side_effect = tasks
        aw_patch.return_value = {tasks[0]}, {tasks[1]}

        ret = await wait_for_react_clic(message, {config.Emoji.lune: 1337,
                                                  "❤": 1565})
        config.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                    check=mock.ANY)
        wfm_patch.assert_called_once_with(trigger_on_commands=False,
                                          check=mock.ANY)
        react_check = config.bot.wait_for.call_args.kwargs["check"]
        message_check = wfm_patch.call_args.kwargs["check"]
        self.assertEqual(act_patch.call_count, 2)
        act_patch.assert_has_calls([mock.call(config.bot.wait_for.return_value),
                                    mock.call(wfm_patch.return_value)])
        aw_patch.assert_called_once_with(tasks,
                                         return_when=asyncio.FIRST_COMPLETED)
        self.assertEqual(message.remove_reaction.call_count, 2)
        message.remove_reaction.assert_has_calls([
            mock.call(config.Emoji.lune, config.bot.user),
            mock.call("❤", config.bot.user)])
        self.assertEqual(ret, 1565)
        aw_patch.reset_mock()
        act_patch.reset_mock()
        wfm_patch.reset_mock()
        config.bot.wait_for.reset_mock()

        # emoji list, clic on custom
        message = mock_discord.message(ctx)
        tasks = [mock.Mock(), mock.Mock()]      # react, message
        tasks[0].result.return_value.emoji = config.Emoji.lune
        act_patch.side_effect = tasks
        aw_patch.return_value = {tasks[0]}, {tasks[1]}

        ret = await wait_for_react_clic(message, [config.Emoji.lune, "❤"])
        config.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                    check=mock.ANY)
        wfm_patch.assert_called_once_with(trigger_on_commands=False,
                                          check=mock.ANY)
        react_check = config.bot.wait_for.call_args.kwargs["check"]
        message_check = wfm_patch.call_args.kwargs["check"]
        self.assertEqual(act_patch.call_count, 2)
        act_patch.assert_has_calls([mock.call(config.bot.wait_for.return_value),
                                    mock.call(wfm_patch.return_value)])
        aw_patch.assert_called_once_with(tasks,
                                         return_when=asyncio.FIRST_COMPLETED)
        self.assertEqual(message.remove_reaction.call_count, 2)
        message.remove_reaction.assert_has_calls([
            mock.call(config.Emoji.lune, config.bot.user),
            mock.call("❤", config.bot.user)])
        self.assertEqual(ret, config.Emoji.lune)
        aw_patch.reset_mock()
        act_patch.reset_mock()
        wfm_patch.reset_mock()
        config.bot.wait_for.reset_mock()

        # emoji list, clic on custom
        message = mock_discord.message(ctx)
        tasks = [mock.Mock(), mock.Mock()]      # react, message
        tasks[0].result.return_value.emoji = "❤"
        act_patch.side_effect = tasks
        aw_patch.return_value = {tasks[0]}, {tasks[1]}

        ret = await wait_for_react_clic(message, [config.Emoji.lune, "❤"])
        config.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                    check=mock.ANY)
        wfm_patch.assert_called_once_with(trigger_on_commands=False,
                                          check=mock.ANY)
        react_check = config.bot.wait_for.call_args.kwargs["check"]
        message_check = wfm_patch.call_args.kwargs["check"]
        self.assertEqual(act_patch.call_count, 2)
        act_patch.assert_has_calls([mock.call(config.bot.wait_for.return_value),
                                    mock.call(wfm_patch.return_value)])
        aw_patch.assert_called_once_with(tasks,
                                         return_when=asyncio.FIRST_COMPLETED)
        self.assertEqual(message.remove_reaction.call_count, 2)
        message.remove_reaction.assert_has_calls([
            mock.call(config.Emoji.lune, config.bot.user),
            mock.call("❤", config.bot.user)])
        self.assertEqual(ret, "❤")
        aw_patch.reset_mock()
        act_patch.reset_mock()
        wfm_patch.reset_mock()
        config.bot.wait_for.reset_mock()

        # trigger_all_reacts, clic on custom
        message = mock_discord.message(ctx)
        tasks = [mock.Mock(), mock.Mock()]      # react, message
        tasks[0].result.return_value.emoji = config.Emoji.maire
        act_patch.side_effect = tasks
        aw_patch.return_value = {tasks[0]}, {tasks[1]}

        ret = await wait_for_react_clic(message, [config.Emoji.lune, "❤"],
                                        trigger_all_reacts=True)
        config.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                    check=mock.ANY)
        wfm_patch.assert_called_once_with(trigger_on_commands=False,
                                          check=mock.ANY)
        react_check = config.bot.wait_for.call_args.kwargs["check"]
        self.assertEqual(act_patch.call_count, 2)
        act_patch.assert_has_calls([mock.call(config.bot.wait_for.return_value),
                                    mock.call(wfm_patch.return_value)])
        aw_patch.assert_called_once_with(tasks,
                                         return_when=asyncio.FIRST_COMPLETED)
        self.assertEqual(message.remove_reaction.call_count, 2)
        message.remove_reaction.assert_has_calls([
            mock.call(config.Emoji.lune, config.bot.user),
            mock.call("❤", config.bot.user)])
        self.assertEqual(ret, config.Emoji.maire)
        aw_patch.reset_mock()
        act_patch.reset_mock()
        wfm_patch.reset_mock()
        config.bot.wait_for.reset_mock()

        # interlude: check checks
        message.id = 15
        config.bot.user.id = 33
        coeur = mock.Mock(discord.PartialEmoji)
        coeur.configure_mock(name="❤")
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=31,
                                               emoji=config.Emoji.maire)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=33,
                                               emoji=config.Emoji.maire)))
        self.assertTrue(react_check(mock.Mock(message_id=15, user_id=31,
                                               emoji=config.Emoji.maire)))
        self.assertFalse(react_check(mock.Mock(message_id=15, user_id=33,
                                               emoji=config.Emoji.maire)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=31,
                                               emoji=coeur)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=33,
                                               emoji=coeur)))
        self.assertTrue(react_check(mock.Mock(message_id=15, user_id=31,
                                               emoji=coeur)))
        self.assertFalse(react_check(mock.Mock(message_id=15, user_id=33,
                                               emoji=coeur)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=31,
                                               emoji=config.Emoji.lune)))
        self.assertFalse(react_check(mock.Mock(message_id=11, user_id=33,
                                               emoji=config.Emoji.lune)))
        self.assertTrue(react_check(mock.Mock(message_id=15, user_id=31,
                                               emoji=config.Emoji.lune)))
        self.assertFalse(react_check(mock.Mock(message_id=15, user_id=33,
                                               emoji=config.Emoji.lune)))

        # message response - text_filter len >= 5 (and trigger_on_commands)
        message = mock_discord.message(ctx)
        tasks = [mock.Mock(), mock.Mock()]      # react, message
        tasks[1].result.return_value = mock.Mock(discord.Message,
                                                 content="alloz")
        act_patch.side_effect = tasks
        aw_patch.return_value = {tasks[1]}, {tasks[0]}

        ret = await wait_for_react_clic(
            message, {config.Emoji.lune: 1337}, process_text=True,
            text_filter=lambda s: len(s) >= 5, trigger_on_commands=True)
        config.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                    check=mock.ANY)
        wfm_patch.assert_called_once_with(trigger_on_commands=True,
                                          check=mock.ANY)
        message_check = wfm_patch.call_args.kwargs["check"]
        self.assertEqual(act_patch.call_count, 2)
        act_patch.assert_has_calls(
            [mock.call(config.bot.wait_for.return_value),
             mock.call(wfm_patch.return_value)])
        aw_patch.assert_called_once_with(
            tasks, return_when=asyncio.FIRST_COMPLETED)
        mess = tasks[1].result.return_value
        message.clear_reactions.assert_called_once()
        self.assertEqual(ret, "alloz")
        aw_patch.reset_mock()
        act_patch.reset_mock()
        wfm_patch.reset_mock()
        config.bot.wait_for.reset_mock()
        # check check
        chan = message.channel
        auth = config.bot.user
        self.assertFalse(message_check(mock.Mock(channel="oh", author="meh",
                                                 content="ala")))
        self.assertFalse(message_check(mock.Mock(channel="oh", author=auth,
                                                 content="ala")))
        self.assertFalse(message_check(mock.Mock(channel=chan, author="meh",
                                                 content="ala")))
        self.assertFalse(message_check(mock.Mock(channel=chan, author=auth,
                                                 content="ala")))
        self.assertFalse(message_check(mock.Mock(channel="oh", author="meh",
                                                 content="alala")))
        self.assertFalse(message_check(mock.Mock(channel="oh", author=auth,
                                                 content="alala")))
        self.assertTrue(message_check(mock.Mock(channel=chan, author="meh",
                                                 content="alala")))
        self.assertFalse(message_check(mock.Mock(channel=chan, author=auth,
                                                 content="alala")))

        # message response - post_converter
        message = mock_discord.message(ctx)
        tasks = [mock.Mock(), mock.Mock()]      # react, message
        tasks[1].result.return_value = mock.Mock(discord.Message,
                                                 content="alloz")
        act_patch.side_effect = tasks
        aw_patch.return_value = {tasks[1]}, {tasks[0]}
        ret = await wait_for_react_clic(
            message, {config.Emoji.lune: 1337}, process_text=True,
            post_converter=lambda s: hash(s) + 19.7)
        config.bot.wait_for.assert_called_once_with('raw_reaction_add',
                                                    check=mock.ANY)
        wfm_patch.assert_called_once_with(trigger_on_commands=False,
                                          check=mock.ANY)
        message_check = wfm_patch.call_args.kwargs["check"]
        self.assertEqual(act_patch.call_count, 2)
        act_patch.assert_has_calls(
            [mock.call(config.bot.wait_for.return_value),
             mock.call(wfm_patch.return_value)])
        aw_patch.assert_called_once_with(
            tasks, return_when=asyncio.FIRST_COMPLETED)
        mess = tasks[1].result.return_value
        message.clear_reactions.assert_called_once()
        self.assertEqual(ret, hash("alloz") + 19.7)
        aw_patch.reset_mock()
        act_patch.reset_mock()
        wfm_patch.reset_mock()
        config.bot.wait_for.reset_mock()

        # exception raised
        message = mock_discord.message(ctx)
        config.bot.wait_for.side_effect = RuntimeError
        with self.assertRaises(RuntimeError):
            ret = await wait_for_react_clic(message, {config.Emoji.lune: 1337})
        message.clear_reactions.assert_called_once()
        aw_patch.assert_not_called()
        act_patch.assert_not_called()
        wfm_patch.assert_not_called()
        config.bot.wait_for.assert_called_once()
        config.bot.wait_for.reset_mock()


    @mock.patch("lgrez.blocs.tools.wait_for_react_clic")
    async def test_yes_no(self, wfrc_patch):
        """Unit tests for tools.yes_no function."""
        # async def yes_no(message)
        yes_no = tools.yes_no

        # single case
        message = mock.Mock()
        ret = await yes_no(message)
        wfrc_patch.assert_called_once_with(
            message, emojis={"✅": True, "❎": False}, process_text=True,
            text_filter=mock.ANY, post_converter=mock.ANY
        )
        text_filter = wfrc_patch.call_args.kwargs["text_filter"]
        self.assertTrue(text_filter("oui"))
        self.assertTrue(text_filter("OUI"))
        self.assertTrue(text_filter("OuI"))
        self.assertTrue(text_filter("yes"))
        self.assertTrue(text_filter("YeS"))
        self.assertTrue(text_filter("1"))
        self.assertTrue(text_filter("non"))
        self.assertTrue(text_filter("NON"))
        self.assertTrue(text_filter("NoN"))
        self.assertTrue(text_filter("no"))
        self.assertTrue(text_filter("NO"))
        self.assertTrue(text_filter("0"))
        self.assertFalse(text_filter("."))
        self.assertFalse(text_filter("ye"))
        self.assertFalse(text_filter("ou"))
        self.assertFalse(text_filter("bloup"))
        self.assertFalse(text_filter("2"))

        post_converter = wfrc_patch.call_args.kwargs["post_converter"]
        self.assertTrue(post_converter("oui"))
        self.assertTrue(post_converter("OUI"))
        self.assertTrue(post_converter("OuI"))
        self.assertTrue(post_converter("yes"))
        self.assertTrue(post_converter("YeS"))
        self.assertTrue(post_converter("1"))
        self.assertFalse(post_converter("non"))
        self.assertFalse(post_converter("NON"))
        self.assertFalse(post_converter("NoN"))
        self.assertFalse(post_converter("no"))
        self.assertFalse(post_converter("NO"))
        self.assertFalse(post_converter("0"))


    @mock.patch("lgrez.blocs.tools.wait_for_react_clic")
    async def test_choice(self, wfrc_patch):
        """Unit tests for tools.choice function."""
        # async def choice(message, N, start=1, *, additionnal={})
        choice = tools.choice

        # simple
        message = mock.Mock()
        ret = await choice(message, 3)
        wfrc_patch.assert_called_once_with(
            message, emojis={"1️⃣": 1, "2️⃣": 2, "3️⃣": 3}, process_text=True,
            text_filter=mock.ANY, post_converter=int
        )
        text_filter = wfrc_patch.call_args.kwargs["text_filter"]
        self.assertFalse(text_filter("0"))
        self.assertTrue(text_filter("1"))
        self.assertTrue(text_filter("2"))
        self.assertTrue(text_filter("3"))
        self.assertFalse(text_filter("4"))
        self.assertFalse(text_filter("."))
        self.assertFalse(text_filter("yes"))
        self.assertFalse(text_filter("ou"))
        self.assertFalse(text_filter("bloup"))
        wfrc_patch.reset_mock()

        # with start
        message = mock.Mock()
        ret = await choice(message, 7, start=4)
        wfrc_patch.assert_called_once_with(
            message, emojis={"4️⃣": 4, "5️⃣": 5, "6️⃣": 6, "7️⃣": 7},
            process_text=True, text_filter=mock.ANY, post_converter=int
        )
        text_filter = wfrc_patch.call_args.kwargs["text_filter"]
        self.assertFalse(text_filter("0"))
        self.assertFalse(text_filter("1"))
        self.assertFalse(text_filter("2"))
        self.assertFalse(text_filter("3"))
        self.assertTrue(text_filter("4"))
        self.assertTrue(text_filter("5"))
        self.assertTrue(text_filter("6"))
        self.assertTrue(text_filter("7"))
        self.assertFalse(text_filter("8"))
        self.assertFalse(text_filter("yes"))
        wfrc_patch.reset_mock()

        # with start and aditionnal
        message = mock.Mock()
        ret = await choice(message, 7, start=4,
                           additionnal={config.Emoji.lune: 1337, "❤": "zebi"})
        wfrc_patch.assert_called_once_with(
            message, emojis={"4️⃣": 4, "5️⃣": 5, "6️⃣": 6, "7️⃣": 7,
                             config.Emoji.lune: 1337, "❤": "zebi"},
            process_text=True, text_filter=mock.ANY, post_converter=int
        )
        text_filter = wfrc_patch.call_args.kwargs["text_filter"]
        self.assertFalse(text_filter("0"))
        self.assertFalse(text_filter("1"))
        self.assertFalse(text_filter("2"))
        self.assertFalse(text_filter("3"))
        self.assertTrue(text_filter("4"))
        self.assertTrue(text_filter("5"))
        self.assertTrue(text_filter("6"))
        self.assertTrue(text_filter("7"))
        self.assertFalse(text_filter("8"))
        self.assertFalse(text_filter("yes"))


    @mock.patch("asyncio.sleep")
    async def test_sleep(self, sleep_patch):
        """Unit tests for tools.sleep function."""
        # async def sleep(chan, tps)
        sleep = tools.sleep
        chan = mock_discord.chan(".")
        await sleep(chan, 17.5)
        chan.typing.assert_called_once()
        sleep_patch.assert_called_once_with(17.5)



class TestToolsEmojisUtilities(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.tools emoji utility functions (section 5)."""

    def test_montre(self):
        """Unit tests for tools.montre function."""
        # def montre(heure=None)
        montre = tools.montre

        samples = {
            "kokf": ValueError,
            "ahb": ValueError,
            "7ha": ValueError,
            "7h": "\N{CLOCK FACE SEVEN OCLOCK}",
            "13h": "\N{CLOCK FACE ONE OCLOCK}",
            "0h": "\N{CLOCK FACE TWELVE OCLOCK}",
            "7h14": "\N{CLOCK FACE SEVEN OCLOCK}",
            "7h15": "\N{CLOCK FACE SEVEN OCLOCK}",
            "7h16": "\N{CLOCK FACE SEVEN-THIRTY}",
            "7h44": "\N{CLOCK FACE SEVEN-THIRTY}",
            "7h45": "\N{CLOCK FACE EIGHT OCLOCK}",
            "7h46": "\N{CLOCK FACE EIGHT OCLOCK}",
            "7h59": "\N{CLOCK FACE EIGHT OCLOCK}",
            "19h14": "\N{CLOCK FACE SEVEN OCLOCK}",
            "19h15": "\N{CLOCK FACE SEVEN OCLOCK}",
            "19h16": "\N{CLOCK FACE SEVEN-THIRTY}",
            "19h44": "\N{CLOCK FACE SEVEN-THIRTY}",
            "19h45": "\N{CLOCK FACE EIGHT OCLOCK}",
            "19h46": "\N{CLOCK FACE EIGHT OCLOCK}",
            "19h59": "\N{CLOCK FACE EIGHT OCLOCK}",
            "23h59": "\N{CLOCK FACE TWELVE OCLOCK}",
        }
        for sample, result in samples.items():
            if isinstance(result, type) and issubclass(result, Exception):
                with self.assertRaises(result):
                    montre(sample)
            else:
                self.assertEqual(montre(sample), result, msg=sample)
                with freezegun.freeze_time(sample):
                    self.assertEqual(montre(), result, msg=sample)


    def test_emoji_chiffre(self):
        """Unit tests for tools.emoji_chiffre function."""
        # def emoji_chiffre(chiffre, multi=False)
        emoji_chiffre = tools.emoji_chiffre

        samples = {
            -1: ValueError,
            11: ValueError,
            7.5: ValueError,
            0: "0️⃣",
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            10: "🔟",
        }
        samples_multionly = {
            72: "7️⃣2️⃣",
            75334: "7️⃣5️⃣3️⃣3️⃣4️⃣",
            100000: "1️⃣0️⃣0️⃣0️⃣0️⃣0️⃣",
        }
        for sample, result in samples.items():
            if isinstance(result, type) and issubclass(result, Exception):
                with self.assertRaises(result):
                    emoji_chiffre(sample)
            else:
                self.assertEqual(emoji_chiffre(sample), result, msg=sample)

        for sample, result in samples_multionly.items():
            with self.assertRaises(ValueError):
                emoji_chiffre(sample)
            self.assertEqual(emoji_chiffre(sample, multi=True), result,
                             msg=sample)


    def test_super_chiffre(self):
        """Unit tests for tools.super_chiffre function."""
        # def super_chiffre(chiffre, multi=False)
        super_chiffre = tools.super_chiffre

        samples = {
            -1: ValueError,
            11: ValueError,
            7.5: ValueError,
            0: "⁰",
            1: "¹",
            2: "²",
            3: "³",
            4: "⁴",
            5: "⁵",
            6: "⁶",
            7: "⁷",
            8: "⁸",
            9: "⁹",
        }
        samples_multionly = {
            10: "¹⁰",
            72: "⁷²",
            75334: "⁷⁵³³⁴",
            100000: "¹⁰⁰⁰⁰⁰",
        }
        for sample, result in samples.items():
            if isinstance(result, type) and issubclass(result, Exception):
                with self.assertRaises(result):
                    super_chiffre(sample)
            else:
                self.assertEqual(super_chiffre(sample), result, msg=sample)

        for sample, result in samples_multionly.items():
            with self.assertRaises(ValueError):
                super_chiffre(sample)
            self.assertEqual(super_chiffre(sample, multi=True), result,
                             msg=sample)


    def test_sub_chiffre(self):
        """Unit tests for tools.sub_chiffre function."""
        # def sub_chiffre(chiffre, multi=False)
        sub_chiffre = tools.sub_chiffre

        samples = {
            -1: ValueError,
            11: ValueError,
            7.5: ValueError,
            0: "₀",
            1: "₁",
            2: "₂",
            3: "₃",
            4: "₄",
            5: "₅",
            6: "₆",
            7: "₇",
            8: "₈",
            9: "₉",
        }
        samples_multionly = {
            10: "₁₀",
            72: "₇₂",
            75334: "₇₅₃₃₄",
            100000: "₁₀₀₀₀₀",
        }
        for sample, result in samples.items():
            if isinstance(result, type) and issubclass(result, Exception):
                with self.assertRaises(result):
                    sub_chiffre(sample)
            else:
                self.assertEqual(sub_chiffre(sample), result, msg=sample)

        for sample, result in samples_multionly.items():
            with self.assertRaises(ValueError):
                sub_chiffre(sample)
            self.assertEqual(sub_chiffre(sample, multi=True), result,
                             msg=sample)



class TestToolsTimeUtilities(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.tools time utility functions (section 6)."""

    def test_heure_to_time(self):
        """Unit tests for tools.heure_to_time function."""
        # def heure_to_time(heure=None)
        heure_to_time = tools.heure_to_time

        samples = {
            "kokf": ValueError,
            "ahb": ValueError,
            "7ha": ValueError,
            "h2": ValueError,
            "7h": datetime.time(7, 0),
            "13h": datetime.time(13, 0),
            "0h": datetime.time(0, 0),
            "0h0": datetime.time(0, 0),
            "0h00": datetime.time(0, 0),
            "00h00": datetime.time(0, 0),
            "7h14": datetime.time(7, 14),
            "07h46": datetime.time(7, 46),
            "7h59": datetime.time(7, 59),
            "19h04": datetime.time(19, 4),
            "19h5": datetime.time(19, 5),
            "19h59": datetime.time(19, 59),
            "23h59": datetime.time(23, 59),
            "7h60": ValueError,
            "24h12": ValueError,
            "-1h2": ValueError,
            "a:b": ValueError,
            "7:a": ValueError,
            ":2": ValueError,
            "7:": datetime.time(7, 0),
            "13:": datetime.time(13, 0),
            "0:": datetime.time(0, 0),
            "0:0": datetime.time(0, 0),
            "0:00": datetime.time(0, 0),
            "00:00": datetime.time(0, 0),
            "7:14": datetime.time(7, 14),
            "07:46": datetime.time(7, 46),
            "7:59": datetime.time(7, 59),
            "19:04": datetime.time(19, 4),
            "19:5": datetime.time(19, 5),
            "19:59": datetime.time(19, 59),
            "23:59": datetime.time(23, 59),
            "7:60": ValueError,
            "24:12": ValueError,
            "-1:2": ValueError,
        }
        for sample, result in samples.items():
            if isinstance(result, type) and issubclass(result, Exception):
                with self.assertRaises(result):
                    heure_to_time(sample)
            else:
                self.assertEqual(heure_to_time(sample), result, msg=sample)


    def test_time_to_heure(self):
        """Unit tests for tools.time_to_heure function."""
        # def time_to_heure(tps, sep="h", force_minutes=False)
        time_to_heure = tools.time_to_heure

        samples = {
            datetime.time(7, 0): ("7h", "7h00", "7<S€>", "7<S€>00"),
            datetime.time(13, 0): ("13h", "13h00", "13<S€>", "13<S€>00"),
            datetime.time(0, 0): ("0h", "0h00", "0<S€>", "0<S€>00"),
            datetime.time(7, 14): ("7h14", "7h14", "7<S€>14", "7<S€>14"),
            datetime.time(7, 46): ("7h46", "7h46", "7<S€>46", "7<S€>46"),
            datetime.time(7, 59): ("7h59", "7h59", "7<S€>59", "7<S€>59"),
            datetime.time(19, 4): ("19h04", "19h04", "19<S€>04", "19<S€>04"),
            datetime.time(19, 59): ("19h59", "19h59", "19<S€>59", "19<S€>59"),
            datetime.time(23, 59): ("23h59", "23h59", "23<S€>59", "23<S€>59"),
        }

        for sp, expected in samples.items():
            results = [
                time_to_heure(sp), time_to_heure(sp, force_minutes=True),
                time_to_heure(sp, sep="<S€>"),
                time_to_heure(sp, sep="<S€>", force_minutes=True),
            ]
            self.assertEqual(list(expected), results, msg=sp)


    def test_debut_pause(self):
        """Unit tests for tools.debut_pause function."""
        # def debut_pause()
        debut_pause = tools.debut_pause
        # on se place la semaine du 1 mars 2021, parce que lundi = 1

        res1 = datetime.datetime(2021, 3, 5, 19, 0)     # vendredi 19h
        res2 = datetime.datetime(2021, 3, 12, 19, 0)    # semaine d'après

        samples1 = [
            datetime.datetime(2021, 3, 1, 0, 0),
            datetime.datetime(2021, 3, 1, 12, 15),
            datetime.datetime(2021, 3, 1, 23, 59),
            datetime.datetime(2021, 3, 2, 0, 0),
            datetime.datetime(2021, 3, 2, 12, 15),
            datetime.datetime(2021, 3, 2, 23, 59),
            datetime.datetime(2021, 3, 3, 0, 0),
            datetime.datetime(2021, 3, 3, 12, 15),
            datetime.datetime(2021, 3, 3, 23, 59),
            datetime.datetime(2021, 3, 4, 0, 0),
            datetime.datetime(2021, 3, 4, 12, 15),
            datetime.datetime(2021, 3, 4, 23, 59),
            datetime.datetime(2021, 3, 5, 0, 0),
            datetime.datetime(2021, 3, 5, 12, 15),
            datetime.datetime(2021, 3, 5, 18, 59),
            datetime.datetime(2021, 3, 5, 19, 0),
        ]
        samples2 = [
            datetime.datetime(2021, 3, 5, 19, 0, 1),
            datetime.datetime(2021, 3, 5, 19, 1),
            datetime.datetime(2021, 3, 5, 23, 59),
            datetime.datetime(2021, 3, 6, 0, 0),
            datetime.datetime(2021, 3, 6, 12, 15),
            datetime.datetime(2021, 3, 6, 23, 59),
            datetime.datetime(2021, 3, 7, 0, 0),
            datetime.datetime(2021, 3, 7, 12, 15),
            datetime.datetime(2021, 3, 7, 23, 59),
        ]

        for sample in samples1:
            with freezegun.freeze_time(sample):
                self.assertEqual(debut_pause(), res1, msg=sample)
        for sample in samples2:
            with freezegun.freeze_time(sample):
                self.assertEqual(debut_pause(), res2, msg=sample)


    def test_fin_pause(self):
        """Unit tests for tools.fin_pause function."""
        # def fin_pause()
        fin_pause = tools.fin_pause
        # on se place la semaine du 1 mars 2021, parce que lundi = 1

        res1 = datetime.datetime(2021, 3, 7, 19, 0)     # dimanche 19h
        res2 = datetime.datetime(2021, 3, 14, 19, 0)    # semaine d'après

        samples1 = [
            datetime.datetime(2021, 3, 1, 0, 0),
            datetime.datetime(2021, 3, 1, 12, 15),
            datetime.datetime(2021, 3, 1, 23, 59),
            datetime.datetime(2021, 3, 2, 0, 0),
            datetime.datetime(2021, 3, 2, 12, 15),
            datetime.datetime(2021, 3, 2, 23, 59),
            datetime.datetime(2021, 3, 3, 0, 0),
            datetime.datetime(2021, 3, 3, 12, 15),
            datetime.datetime(2021, 3, 3, 23, 59),
            datetime.datetime(2021, 3, 4, 0, 0),
            datetime.datetime(2021, 3, 4, 12, 15),
            datetime.datetime(2021, 3, 4, 23, 59),
            datetime.datetime(2021, 3, 5, 0, 0),
            datetime.datetime(2021, 3, 5, 12, 15),
            datetime.datetime(2021, 3, 5, 23, 59),
            datetime.datetime(2021, 3, 6, 0, 0),
            datetime.datetime(2021, 3, 6, 12, 15),
            datetime.datetime(2021, 3, 6, 23, 59),
            datetime.datetime(2021, 3, 7, 0, 0),
            datetime.datetime(2021, 3, 7, 12, 15),
            datetime.datetime(2021, 3, 7, 18, 59),
            datetime.datetime(2021, 3, 7, 19, 0),
        ]
        samples2 = [
            datetime.datetime(2021, 3, 7, 19, 0, 1),
            datetime.datetime(2021, 3, 7, 19, 1),
            datetime.datetime(2021, 3, 7, 23, 59),
        ]

        for sample in samples1:
            with freezegun.freeze_time(sample):
                self.assertEqual(fin_pause(), res1, msg=sample)
        for sample in samples2:
            with freezegun.freeze_time(sample):
                self.assertEqual(fin_pause(), res2, msg=sample)


    @mock.patch("lgrez.blocs.tools.debut_pause")
    @mock.patch("lgrez.blocs.tools.fin_pause")
    def test_en_pause(self, fin_patch, debut_patch):
        """Unit tests for tools.en_pause function."""
        # def en_pause()
        en_pause = tools.en_pause
        # oui
        fin_patch.return_value = 1
        debut_patch.return_value = 2
        self.assertTrue(en_pause())
        # non
        fin_patch.return_value = 3
        debut_patch.return_value = 2
        self.assertFalse(en_pause())
        # equal -> False
        fin_patch.return_value = 2
        debut_patch.return_value = 2
        self.assertFalse(en_pause())


    def test_next_occurence(self):
        """Unit tests for tools.next_occurence function."""
        # def next_occurence(tps)
        next_occurence = tools.next_occurence
        # on se place la semaine du 1 mars 2021, parce que lundi = 1

        samples = {}
        for i in range(1, 4):       # identique lundi -> mercredi
            samples.update({
            (datetime.datetime(2021, 3, i, 0, 0),   datetime.time(10, 0)): 0,
            (datetime.datetime(2021, 3, i, 0, 0),   datetime.time(14, 0)): 0,
            (datetime.datetime(2021, 3, i, 0, 0),   datetime.time(19, 0)): 0,
            (datetime.datetime(2021, 3, i, 0, 0),   datetime.time(22, 0)): 0,
            (datetime.datetime(2021, 3, i, 12, 15), datetime.time(10, 0)): 1,
            (datetime.datetime(2021, 3, i, 12, 15), datetime.time(14, 0)): 0,
            (datetime.datetime(2021, 3, i, 12, 15), datetime.time(19, 0)): 0,
            (datetime.datetime(2021, 3, i, 12, 15), datetime.time(22, 0)): 0,
            (datetime.datetime(2021, 3, i, 23, 59), datetime.time(10, 0)): 1,
            (datetime.datetime(2021, 3, i, 23, 59), datetime.time(14, 0)): 1,
            (datetime.datetime(2021, 3, i, 23, 59), datetime.time(19, 0)): 1,
            (datetime.datetime(2021, 3, i, 23, 59), datetime.time(22, 0)): 1,
            })
        samples.update({
            (datetime.datetime(2021, 3, 4, 0, 0),   datetime.time(10, 0)): 0,
            (datetime.datetime(2021, 3, 4, 0, 0),   datetime.time(14, 0)): 0,
            (datetime.datetime(2021, 3, 4, 0, 0),   datetime.time(19, 0)): 0,
            (datetime.datetime(2021, 3, 4, 0, 0),   datetime.time(22, 0)): 0,
            (datetime.datetime(2021, 3, 4, 12, 15), datetime.time(10, 0)): 1,
            (datetime.datetime(2021, 3, 4, 12, 15), datetime.time(14, 0)): 0,
            (datetime.datetime(2021, 3, 4, 12, 15), datetime.time(19, 0)): 0,
            (datetime.datetime(2021, 3, 4, 12, 15), datetime.time(22, 0)): 0,
            (datetime.datetime(2021, 3, 4, 23, 59), datetime.time(10, 0)): 1,
            (datetime.datetime(2021, 3, 4, 23, 59), datetime.time(14, 0)): 1,
            (datetime.datetime(2021, 3, 4, 23, 59), datetime.time(19, 0)): 3,
            (datetime.datetime(2021, 3, 4, 23, 59), datetime.time(22, 0)): 3,
            (datetime.datetime(2021, 3, 5, 0, 0),   datetime.time(10, 0)): 0,
            (datetime.datetime(2021, 3, 5, 0, 0),   datetime.time(14, 0)): 0,
            (datetime.datetime(2021, 3, 5, 0, 0),   datetime.time(19, 0)): 2,
            (datetime.datetime(2021, 3, 5, 0, 0),   datetime.time(22, 0)): 2,
            (datetime.datetime(2021, 3, 5, 12, 15), datetime.time(10, 0)): 3,
            (datetime.datetime(2021, 3, 5, 12, 15), datetime.time(14, 0)): 0,
            (datetime.datetime(2021, 3, 5, 12, 15), datetime.time(19, 0)): 2,
            (datetime.datetime(2021, 3, 5, 12, 15), datetime.time(22, 0)): 2,
            (datetime.datetime(2021, 3, 5, 23, 59), datetime.time(10, 0)): 3,
            (datetime.datetime(2021, 3, 5, 23, 59), datetime.time(14, 0)): 3,
            (datetime.datetime(2021, 3, 5, 23, 59), datetime.time(19, 0)): 2,
            (datetime.datetime(2021, 3, 5, 23, 59), datetime.time(22, 0)): 2,
            (datetime.datetime(2021, 3, 6, 0, 0),   datetime.time(10, 0)): 2,
            (datetime.datetime(2021, 3, 6, 0, 0),   datetime.time(14, 0)): 2,
            (datetime.datetime(2021, 3, 6, 0, 0),   datetime.time(19, 0)): 1,
            (datetime.datetime(2021, 3, 6, 0, 0),   datetime.time(22, 0)): 1,
            (datetime.datetime(2021, 3, 6, 12, 15), datetime.time(10, 0)): 2,
            (datetime.datetime(2021, 3, 6, 12, 15), datetime.time(14, 0)): 2,
            (datetime.datetime(2021, 3, 6, 12, 15), datetime.time(19, 0)): 1,
            (datetime.datetime(2021, 3, 6, 12, 15), datetime.time(22, 0)): 1,
            (datetime.datetime(2021, 3, 6, 23, 59), datetime.time(10, 0)): 2,
            (datetime.datetime(2021, 3, 6, 23, 59), datetime.time(14, 0)): 2,
            (datetime.datetime(2021, 3, 6, 23, 59), datetime.time(19, 0)): 1,
            (datetime.datetime(2021, 3, 6, 23, 59), datetime.time(22, 0)): 1,
            (datetime.datetime(2021, 3, 7, 0, 0),   datetime.time(10, 0)): 1,
            (datetime.datetime(2021, 3, 7, 0, 0),   datetime.time(14, 0)): 1,
            (datetime.datetime(2021, 3, 7, 0, 0),   datetime.time(19, 0)): 0,
            (datetime.datetime(2021, 3, 7, 0, 0),   datetime.time(22, 0)): 0,
            (datetime.datetime(2021, 3, 7, 12, 15), datetime.time(10, 0)): 1,
            (datetime.datetime(2021, 3, 7, 12, 15), datetime.time(14, 0)): 1,
            (datetime.datetime(2021, 3, 7, 12, 15), datetime.time(19, 0)): 0,
            (datetime.datetime(2021, 3, 7, 12, 15), datetime.time(22, 0)): 0,
            (datetime.datetime(2021, 3, 7, 23, 59), datetime.time(10, 0)): 1,
            (datetime.datetime(2021, 3, 7, 23, 59), datetime.time(14, 0)): 1,
            (datetime.datetime(2021, 3, 7, 23, 59), datetime.time(19, 0)): 1,
            (datetime.datetime(2021, 3, 7, 23, 59), datetime.time(22, 0)): 1,
        })

        for (now, tps), delta in samples.items():
            with freezegun.freeze_time(now):
                result = next_occurence(tps)

            self.assertEqual(tps, result.time(), msg=(now, tps))
            self.assertEqual(now.date() + datetime.timedelta(days=delta),
                                 result.date(), msg=(now, tps))



class TestToolsSplittersLoggers(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.tools split/log functions (section 6)."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()


    def test_smooth_split(self):
        """Unit tests for tools.smooth_split function."""
        # def smooth_split(mess, N=1990, sep='\n', rep='')
        smooth_split = tools.smooth_split

        # simple
        self.assertEqual(smooth_split("oui"), ["oui"])
        self.assertEqual(smooth_split("\noui\n"), ["\noui\n"])
        self.assertEqual(smooth_split("o"*1990), ["o"*1990])
        self.assertEqual(smooth_split("o"*1990 + "\n"), ["o"*1990])
        self.assertEqual(smooth_split("o"*1991), ["o"*1990, "o"])
        self.assertEqual(smooth_split("o"*1000 + "\n" + "o"*1000),
                         ["o"*1000, "o"*1000])
        self.assertEqual(smooth_split("o"*1990 + "\n" + "o"*1000),
                         ["o"*1990, "o"*1000])
        self.assertEqual(smooth_split("o"*1991 + "\n" + "o"*1000),
                         ["o"*1990, "o\n" + "o"*1000])
        self.assertEqual(smooth_split("o"*3981), ["o"*1990, "o"*1990, "o"])
        self.assertEqual(smooth_split("o"*2590 + "\n" + "o"*1000),
                         ["o"*1990, "o"*600 + "\n" + "o"*1000])
        self.assertEqual(smooth_split("o"*2590 + "\n" + "o"*1500),
                         ["o"*1990, "o"*600, "o"*1500])

        # custom N
        self.assertEqual(smooth_split("oui", N=30), ["oui"])
        self.assertEqual(smooth_split("\noui\n", N=30), ["\noui\n"])
        self.assertEqual(smooth_split("o"*30, N=30), ["o"*30])
        self.assertEqual(smooth_split("o"*30 + "\n", N=30), ["o"*30])
        self.assertEqual(smooth_split("o"*31, N=30), ["o"*30, "o"])
        self.assertEqual(smooth_split("o"*20 + "\n" + "o"*20, N=30),
                         ["o"*20, "o"*20])
        self.assertEqual(smooth_split("o"*30 + "\n" + "o"*20, N=30),
                         ["o"*30, "o"*20])
        self.assertEqual(smooth_split("o"*31 + "\n" + "o"*20, N=30),
                         ["o"*30, "o\n" + "o"*20])
        self.assertEqual(smooth_split("o"*61, N=30), ["o"*30, "o"*30, "o"])
        self.assertEqual(smooth_split("o"*36 + "\n" + "o"*20, N=30),
                         ["o"*30, "o"*6 + "\n" + "o"*20])
        self.assertEqual(smooth_split("o"*36 + "\n" + "o"*27, N=30),
                         ["o"*30, "o"*6, "o"*27])

        # custom N and sep
        self.assertEqual(smooth_split("oui", N=30, sep="$"), ["oui"])
        self.assertEqual(smooth_split("$oui$", N=30, sep="$"), ["$oui$"])
        self.assertEqual(smooth_split("o"*30, N=30, sep="$"), ["o"*30])
        self.assertEqual(smooth_split("o"*30 + "$", N=30, sep="$"), ["o"*30])
        self.assertEqual(smooth_split("o"*31, N=30, sep="$"), ["o"*30, "o"])
        self.assertEqual(smooth_split("o"*20 + "$" + "o"*20, N=30, sep="$"),
                         ["o"*20, "o"*20])
        self.assertEqual(smooth_split("o"*30 + "$" + "o"*20, N=30, sep="$"),
                         ["o"*30, "o"*20])
        self.assertEqual(smooth_split("o"*31 + "$" + "o"*20, N=30, sep="$"),
                         ["o"*30, "o$" + "o"*20])
        self.assertEqual(smooth_split("o"*61, N=30, sep="$"),
                         ["o"*30, "o"*30, "o"])
        self.assertEqual(smooth_split("o"*36 + "$" + "o"*20, N=30, sep="$"),
                         ["o"*30, "o"*6 + "$" + "o"*20])
        self.assertEqual(smooth_split("o"*36 + "$" + "o"*27, N=30, sep="$"),
                         ["o"*30, "o"*6, "o"*27])

        # custom N and rep
        self.assertEqual(smooth_split("oui", N=30, rep="<REP>"), ["oui"])
        self.assertEqual(smooth_split("\noui\n", N=30, rep="<REP>"),
                         ["\noui\n"])
        self.assertEqual(smooth_split("o"*30, N=30, rep="<REP>"), ["o"*30])
        self.assertEqual(smooth_split("o"*30 + "\n", N=30, rep="<REP>"),
                         ["o"*30 + "<REP>"])
        self.assertEqual(smooth_split("o"*31, N=30, rep="<REP>"),
                         ["o"*30 + "<REP>", "o"])
        self.assertEqual(
            smooth_split("o"*20 + "\n" + "o"*20, N=30, rep="<REP>"),
            ["o"*20 + "<REP>", "o"*20])
        self.assertEqual(
            smooth_split("o"*30 + "\n" + "o"*20, N=30, rep="<REP>"),
            ["o"*30 + "<REP>", "o"*20])
        self.assertEqual(
            smooth_split("o"*31 + "\n" + "o"*20, N=30, rep="<REP>"),
            ["o"*30 + "<REP>", "o\n" + "o"*20])
        self.assertEqual(smooth_split("o"*61, N=30, rep="<REP>"),
                         ["o"*30 + "<REP>", "o"*30 + "<REP>", "o"])
        self.assertEqual(
            smooth_split("o"*36 + "\n" + "o"*20, N=30, rep="<REP>"),
            ["o"*30 + "<REP>", "o"*6 + "\n" + "o"*20])
        self.assertEqual(
            smooth_split("o"*36 + "\n" + "o"*27, N=30, rep="<REP>"),
            ["o"*30 + "<REP>", "o"*6 + "<REP>", "o"*27])


    @mock.patch("lgrez.blocs.tools.smooth_split")
    async def test_send_blocs(self, ss_patch):
        """Unit tests for tools.send_blocs function."""
        # async def send_blocs(messageable, mess, *, N=1990, sep='\n', rep='')
        send_blocs = tools.send_blocs
        # simple
        mgbl, mess = mock.Mock(send=mock.AsyncMock()), mock.Mock()
        ss_patch.return_value = ["oui"]
        messages = await send_blocs(mgbl, mess)
        ss_patch.assert_called_once_with(mess, N=1990, sep='\n', rep='')
        mgbl.send.assert_called_once_with("oui")
        self.assertEqual(messages, [mgbl.send.return_value])
        ss_patch.reset_mock()
        # complex
        mgbl, mess = mock.Mock(send=mock.AsyncMock()), mock.Mock()
        ss_patch.return_value = ["oui", "non", "meh"]
        retmess = [mock.Mock(), mock.Mock(), mock.Mock()]
        mgbl.send.side_effect = retmess
        messages = await send_blocs(mgbl, mess, N=12, sep='$', rep='ùùù')
        ss_patch.assert_called_once_with(mess, N=12, sep='$', rep='ùùù')
        self.assertEqual(mgbl.send.call_count, 3)
        mgbl.send.assert_has_calls([mock.call("oui"), mock.call("non"),
                                    mock.call("meh")])
        self.assertEqual(messages, retmess)
        ss_patch.reset_mock()


    @mock.patch("lgrez.blocs.tools.smooth_split")
    @mock.patch("lgrez.blocs.tools.code_bloc")
    async def test_send_code_blocs(self, cb_patch, ss_patch):
        """Unit tests for tools.send_code_blocs function."""
        # async def send_code_blocs(messageable, mess, *, N=1990, sep='\n',
        #                           rep='', prefixe="", langage="")
        send_code_blocs = tools.send_code_blocs

        # simple
        mgbl, mess = mock.Mock(send=mock.AsyncMock()), "groolk"
        ss_patch.return_value = ["oui"]
        messages = await send_code_blocs(mgbl, mess)
        ss_patch.assert_called_once_with("groolk", N=1990, sep='\n', rep='')
        cb_patch.assert_called_once_with("oui", langage="")
        mgbl.send.assert_called_once_with(cb_patch.return_value)
        self.assertEqual(messages, [mgbl.send.return_value])
        ss_patch.reset_mock()
        cb_patch.reset_mock()

        # complex
        mgbl, mess = mock.Mock(send=mock.AsyncMock()), "groolk"
        ss_patch.return_value = ["oui", "non", "meh"]
        retmess = [mock.Mock(), mock.Mock(), mock.Mock()]
        mgbl.send.side_effect = retmess
        retcbs = [mock.Mock(), mock.Mock(), mock.Mock()]
        cb_patch.side_effect = retcbs
        messages = await send_code_blocs(mgbl, mess, N=12, sep='$', rep='ùùù',
                                         langage="oh")
        ss_patch.assert_called_once_with("groolk", N=12, sep='$', rep='ùùù')
        self.assertEqual(cb_patch.call_count, 3)
        cb_patch.assert_has_calls([mock.call("oui", langage="oh"),
                                   mock.call("non", langage="oh"),
                                   mock.call("meh", langage="oh")])
        self.assertEqual(mgbl.send.call_count, 3)
        mgbl.send.assert_has_calls([mock.call(mk) for mk in retcbs])
        self.assertEqual(messages, retmess)
        ss_patch.reset_mock()
        cb_patch.reset_mock()

        # with prefix
        mgbl, mess = mock.Mock(send=mock.AsyncMock()), "groolk"
        ss_patch.return_value = ["PREF::\noui", "non", "meh"]
        retmess = [mock.Mock(), mock.Mock(), mock.Mock()]
        mgbl.send.side_effect = retmess
        retcbs = ["<<oui>>", "<<non>>", "<<meh>>"]
        cb_patch.side_effect = retcbs
        messages = await send_code_blocs(mgbl, mess, N=12, sep='$', rep='ùùù',
                                         langage="oh", prefixe="PREF::")
        ss_patch.assert_called_once_with("PREF::\ngroolk", N=12, sep='$',
                                         rep='ùùù')
        self.assertEqual(cb_patch.call_count, 3)
        cb_patch.assert_has_calls([mock.call("oui", langage="oh"),
                                   mock.call("non", langage="oh"),
                                   mock.call("meh", langage="oh")])
        self.assertEqual(mgbl.send.call_count, 3)
        mgbl.send.assert_has_calls([mock.call("PREF::\n<<oui>>"),
                                    mock.call("<<non>>"),
                                    mock.call("<<meh>>")])
        self.assertEqual(messages, retmess)
        ss_patch.reset_mock()
        cb_patch.reset_mock()


    @mock.patch("lgrez.blocs.tools.send_blocs")
    @mock.patch("lgrez.blocs.tools.send_code_blocs")
    async def test_log(self, scb_patch, sb_patch):
        """Unit tests for tools.log function."""
        # async def log(message, *, code=False, N=1990, sep='\n', rep='',
        #               prefixe="", langage="")
        log = tools.log

        # simple - code False
        messages = await log("groolk")
        sb_patch.assert_called_once_with(
            config.Channel.logs, "groolk", N=1990, sep='\n', rep='')
        self.assertEqual(messages, sb_patch.return_value)
        sb_patch.reset_mock()
        scb_patch.assert_not_called()

        # simple - code True
        messages = await log("groolk", code=True)
        scb_patch.assert_called_once_with(
            config.Channel.logs, "groolk", N=1990, sep='\n', rep='',
            prefixe="", langage="")
        self.assertEqual(messages, scb_patch.return_value)
        scb_patch.reset_mock()
        sb_patch.assert_not_called()

        # complex - code False
        messages = await log("groolk", N=12, sep='$', rep='ùùù',
                             langage="oh", prefixe="PREF::")
        sb_patch.assert_called_once_with(
            config.Channel.logs, "PREF::\ngroolk", N=12, sep='$', rep='ùùù')
        self.assertEqual(messages, sb_patch.return_value)
        sb_patch.reset_mock()
        scb_patch.assert_not_called()

        # complex - code True
        messages = await log("groolk", code=True, N=12, sep='$', rep='ùùù',
                             langage="oh", prefixe="PREF::")
        scb_patch.assert_called_once_with(
            config.Channel.logs, "groolk", N=12, sep='$', rep='ùùù',
            prefixe="PREF::", langage="oh")
        self.assertEqual(messages, scb_patch.return_value)
        scb_patch.reset_mock()
        sb_patch.assert_not_called()



class TestToolsMiscellaneous(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.tools misc. functions (sections 7 & 8)."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()


    @mock.patch("lgrez.bdd.Joueur.from_member")
    async def test_create_context(self, jfm_patch):
        """Unit tests for tools.create_context function."""
        # async def create_context(member, content)
        create_context = tools.create_context
        member = mock.Mock()
        mess = mock.Mock()
        chan = jfm_patch.return_value.private_chan
        chan.history.return_value.flatten = mock.AsyncMock(return_value=[mess])

        ctx = await create_context(member, "ouiZZ")
        chan.history.assert_called_once_with(limit=1)
        jfm_patch.assert_called_once_with(member)
        config.bot.get_context.assert_called_once_with(mock.ANY)
        self.assertEqual(mess, config.bot.get_context.call_args.args[0])
        self.assertEqual(mess.author, member)
        self.assertEqual(mess.content, "ouiZZ")
        self.assertEqual(ctx, config.bot.get_context.return_value)


    def test_remove_accents(self):
        """Unit tests for tools.remove_accents function."""
        # def remove_accents(text)
        remove_accents = tools.remove_accents
        samples = {
            "": "",
            "allo": "allo",
            "AllO": "AllO",
            "énorme ÉNORME": "enorme ENORME",
            "àéïìùÀÉÏÌÙ‰": "aeiiuAEIIU‰",
            "énorme?♥♦♣♠": "enorme?♥♦♣♠",
        }
        for sample, result in samples.items():
            self.assertEqual(remove_accents(sample), result)

    @unittest.SkipTest
    def test_eval_accols(rep, globals_=None, locals_=None, debug=False):
        """Unit tests for tools.eval_accols function."""
        # def eval_accols(text)
        eval_accols = tools.eval_accols

    def test_bold(self):
        """Unit tests for tools.bold function."""
        # def bold(text)
        bold = tools.bold
        self.assertEqual(bold("sample"), "**sample**")

    def test_ital(self):
        """Unit tests for tools.ital function."""
        # def ital(text)
        ital = tools.ital
        self.assertEqual(ital("sample"), "*sample*")

    def test_soul(self):
        """Unit tests for tools.soul function."""
        # def soul(text)
        soul = tools.soul
        self.assertEqual(soul("sample"), "__sample__")

    def test_strike(self):
        """Unit tests for tools.strike function."""
        # def strike(text)
        strike = tools.strike
        self.assertEqual(strike("sample"), "~~sample~~")

    def test_code(self):
        """Unit tests for tools.code function."""
        # def code(text)
        code = tools.code
        self.assertEqual(code("sample"), "`sample`")

    def test_code_bloc(self):
        """Unit tests for tools.code_bloc function."""
        # def code_bloc(text, language="")
        code_bloc = tools.code_bloc
        self.assertEqual(code_bloc("sample"), "```\nsample```")
        self.assertEqual(code_bloc("sample", langage="bzz"),
                         "```bzz\nsample```")

    def test_quote(self):
        """Unit tests for tools.quote function."""
        # def quote(text)
        quote = tools.quote
        self.assertEqual(quote("sample"), "> sample")

    def test_quote_bloc(self):
        """Unit tests for tools.quote_bloc function."""
        # def quote_bloc(text)
        quote_bloc = tools.quote_bloc
        self.assertEqual(quote_bloc("sample"), ">>> sample")

    def test_spoiler(self):
        """Unit tests for tools.spoiler function."""
        # def spoiler(text)
        spoiler = tools.spoiler
        self.assertEqual(spoiler("sample"), "||sample||")
