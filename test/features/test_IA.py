import unittest
from unittest import mock

import discord

from lgrez import config, bdd
from lgrez.features import IA
from test import mock_discord, mock_bdd


class TestIAFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.IA utility functions."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    async def test__build_sequence(self):
        """Unit tests for IA._build_sequence function."""
        # async def _build_sequence(ctx)
        _build_sequence = IA._build_sequence

        # message
        ctx = mock_discord.get_ctx(None)
        with mock_discord.interact(
            ("wait_for_react_clic", "mezzag"),
            ("wait_for_react_clic", False),
        ):
            seq = await _build_sequence(ctx)
        self.assertEqual(seq, "mezzag")
        ctx.assert_sent("Réaction du bot", "Puis")

        # command
        ctx = mock_discord.get_ctx(None)
        with mock_discord.interact(
            ("wait_for_react_clic", "!commandz"),
            ("wait_for_react_clic", False),
        ):
            seq = await _build_sequence(ctx)
        self.assertEqual(seq, f"{IA.MARK_CMD}commandz")
        ctx.assert_sent("Réaction du bot", "Puis")

        # command - other prefix
        ctx = mock_discord.get_ctx(None)
        config.bot.command_prefix = "PREFIXZ"
        with mock_discord.interact(
            ("wait_for_react_clic", "PREFIXZcommandz"),
            ("wait_for_react_clic", False),
        ):
            seq = await _build_sequence(ctx)
        self.assertEqual(seq, f"{IA.MARK_CMD}commandz")
        ctx.assert_sent("Réaction du bot", "Puis")
        config.bot.command_prefix = "!"

        # react
        ctx = mock_discord.get_ctx(None)
        reaczt = mock.NonCallableMock(discord.Emoji)
        reaczt.configure_mock(name="bon.")
        with mock_discord.interact(
            ("wait_for_react_clic", reaczt),
            ("wait_for_react_clic", False),
        ):
            seq = await _build_sequence(ctx)
        self.assertEqual(seq, f"{IA.MARK_REACT}bon.")
        ctx.assert_sent("Réaction du bot", "Puis")

        # several commands
        ctx = mock_discord.get_ctx(None)
        reaczt = mock.NonCallableMock(discord.Emoji)
        reaczt.configure_mock(name="bon.")
        with mock_discord.interact(
            ("wait_for_react_clic", "mezzage"),
            ("wait_for_react_clic", IA.MARK_THEN),
            ("wait_for_react_clic", reaczt),
            ("wait_for_react_clic", IA.MARK_OR),
            ("wait_for_react_clic", "oh"),
            ("wait_for_react_clic", IA.MARK_THEN),
            ("wait_for_react_clic", "!ouizz"),
            ("wait_for_react_clic", False),
        ):
            seq = await _build_sequence(ctx)
        self.assertEqual(seq,
            f"mezzage{IA.MARK_THEN}{IA.MARK_REACT}bon.{IA.MARK_OR}"
            f"oh{IA.MARK_THEN}{IA.MARK_CMD}ouizz"
        )
        ctx.assert_sent("Réaction du bot", "Puis", "Réaction du bot", "Puis",
                        "Réaction du bot", "Puis", "Réaction du bot", "Puis")


    def test_fetch_tenor(self):
        """Unit tests for IA.fetch_tenor function."""
        # def fetch_tenor(trigger)
        fetch_tenor = IA.fetch_tenor

        # request failed
        payload = mock.NonCallableMagicMock(__bool__=lambda self: False)
        with mock.patch("requests.get", return_value=payload):
            gif = fetch_tenor("bzzt")
        self.assertIs(None, gif)

        # no results
        payload = mock.NonCallableMagicMock(__bool__=lambda self: True,
                                            json=lambda: {"results": []})
        with mock.patch("requests.get", return_value=payload):
            gif = fetch_tenor("bzzt")
        self.assertIs(None, gif)

        # one result
        payload = mock.NonCallableMagicMock(
            __bool__=lambda self: True,
            json=lambda: {"results": [{"itemurl": "bzoot"}]}
        )
        with mock.patch("requests.get", return_value=payload):
            gif = fetch_tenor("bzzt")
        self.assertEqual("bzoot", gif)

        # more results
        payload = mock.NonCallableMagicMock(
            __bool__=lambda self: True,
            json=lambda: {"results": [{"itemurl": "bzoot"},
                                      {"itemurl": "notyou"},
                                      {"itemurl": "uneither"}]}
        )
        with mock.patch("requests.get", return_value=payload):
            gif = fetch_tenor("bzzt")
        self.assertEqual("bzoot", gif)


    async def test_trigger_at_mj(self):
        """Unit tests for IA.trigger_at_mj function."""
        # async def trigger_at_mj(message)
        trigger_at_mj = IA.trigger_at_mj

        # no mention
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "oo", role_mentions=[])
        rep = await trigger_at_mj(message)
        self.assertIs(rep, False)
        ctx.assert_sent()

        # other role mention
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "oo",
                                       role_mentions=[config.Role.joueur_mort])
        rep = await trigger_at_mj(message)
        self.assertIs(rep, False)
        ctx.assert_sent()

        # @MJ mention
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "oo",
                                       role_mentions=[config.Role.mj])
        rep = await trigger_at_mj(message)
        self.assertIs(rep, True)
        ctx.assert_sent("ils sont en route")


    @mock_bdd.patch_db      # Empty database for this method
    async def test_trigger_roles(self):
        """Unit tests for IA.trigger_roles function."""
        # async def trigger_roles(message, sensi=0.8)
        trigger_roles = IA.trigger_roles
        mock_bdd.add_campsroles(10, 10)

        # nothing
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "ooooo")
        rep = await trigger_roles(message)
        self.assertIs(rep, False)
        ctx.assert_sent()

        # one exact role found
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "Role3")
        role3 = bdd.Role.query.get("role3")
        role3.prefixe = "PREF@x"
        role3.description_courte = "D€$k00rt"
        role3.description_longue = "D€$k_longue"
        role3.camp = bdd.Camp.query.get("camp3")
        rep = await trigger_roles(message)
        self.assertIs(rep, True)
        ctx.assert_sent(["Role3", "PREF@x", "D€$k00rt", "D€$k_longue", "Camp3"])

        # high sensi
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "Rol")
        rep = await trigger_roles(message)
        self.assertIs(rep, False)
        ctx.assert_sent()

        # low sensi - more roles found
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "Rol")
        rep = await trigger_roles(message, sensi=0.5)
        self.assertIs(rep, True)
        ctx.assert_sent("Role")     # one selected


    @mock_bdd.patch_db      # Empty database for this method
    async def test_trigger_reactions(self):
        """Unit tests for IA.trigger_reactions function."""
        # async def trigger_reactions(message, chain=None, sensi=0.7,
        #                             debug=False)
        trigger_reactions = IA.trigger_reactions

        # no reactions
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "ooooo")
        rep = await trigger_reactions(message)
        self.assertIs(rep, False)
        ctx.assert_sent()

        # no matching reactions
        reac = bdd.Reaction(reponse="non")
        bdd.Trigger(trigger="oui", reaction=reac).add(reac)
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "ooo")
        rep = await trigger_reactions(message)
        self.assertIs(rep, False)
        ctx.assert_sent()

        # lower sensi -> matching
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "ooo")
        rep = await trigger_reactions(message, sensi=0.3)
        self.assertIs(rep, True)
        ctx.assert_sent("non")

        # command
        reac.reponse = f"{IA.MARK_CMD}commandz"
        reac.update()
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "oui")
        with mock.patch("lgrez.config.bot.process_commands") as pc_patch:
            rep = await trigger_reactions(message)
        self.assertIs(rep, True)
        self.assertEqual(message.content, "!commandz")
        ctx.assert_sent()
        pc_patch.assert_called_once_with(message)

        # command - other prefix
        reac.reponse = f"{IA.MARK_CMD}commandz"
        reac.update()
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "oui")
        config.bot.command_prefix = "PREFix"
        with mock.patch("lgrez.config.bot.process_commands") as pc_patch:
            rep = await trigger_reactions(message)
        config.bot.command_prefix = "!"
        self.assertIs(rep, True)
        self.assertEqual(message.content, "PREFixcommandz")
        ctx.assert_sent()
        pc_patch.assert_called_once_with(message)

        # react
        reac.reponse = f"{IA.MARK_REACT}bon."
        reac.update()
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "oui")
        rep = await trigger_reactions(message)
        self.assertIs(rep, True)
        ctx.assert_sent()
        message.add_reaction.assert_called_once_with("bon.")

        # several commands / reactions / texts
        reac.reponse = (f"mezzage{IA.MARK_THEN}{IA.MARK_REACT}bon."
                        f"{IA.MARK_THEN}{IA.MARK_CMD}ouizz"
                        f"{IA.MARK_THEN}aha!{IA.MARK_THEN}{IA.MARK_REACT}krr")
        reac.update()
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "oui")
        with mock.patch("lgrez.config.bot.process_commands") as pc_patch:
            rep = await trigger_reactions(message)
        self.assertIs(rep, True)
        ctx.assert_sent("mezzage", "aha!")
        self.assertEqual(message.add_reaction.mock_calls,
                         [mock.call("bon."), mock.call("krr")])
        self.assertEqual(message.content, "!ouizz")
        pc_patch.assert_called_once_with(message)

        # OR
        reac.reponse = (f"a{IA.MARK_OR}b")
        reac.update()
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "oui")
        na = 0
        nb = 0
        for i in range(1000):
            await trigger_reactions(message)
            sent = ctx.send.call_args.args[0]
            if sent == "a":
                na += 1
            elif sent == "b":
                nb += 1
            else:
                raise AssertionError("Sent something else!")
        self.assertGreater(na, 400)
        self.assertGreater(nb, 400)


    @mock.patch("lgrez.features.IA.trigger_reactions")
    async def test_trigger_sub_reactions(self, tr_patch):
        """Unit tests for IA.trigger_sub_reactions function."""
        # async def trigger_sub_reactions(message, sensi=0.9, debug=False)
        trigger_sub_reactions = IA.trigger_sub_reactions

        # empty message
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "")
        rep = await trigger_sub_reactions(message)
        self.assertIs(rep, False)
        tr_patch.assert_not_called()
        ctx.assert_sent()

        # one word
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "boo")
        rep = await trigger_sub_reactions(message)
        self.assertIs(rep, False)
        tr_patch.assert_not_called()
        ctx.assert_sent()

        # <= 4-length words
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "boo a baaz tok paaf")
        rep = await trigger_sub_reactions(message)
        self.assertIs(rep, False)
        tr_patch.assert_not_called()
        ctx.assert_sent()

        # one > 4-length word, return False
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "boo a baazA tok paaf")
        tr_patch.return_value = False
        rep = await trigger_sub_reactions(message)
        self.assertIs(rep, False)
        tr_patch.assert_called_once_with(message, chain="baazA",
                                         sensi=0.9, debug=False)
        ctx.assert_sent()
        tr_patch.reset_mock()

        # one > 4-length word, return True (and debug True)
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "boo a baazA tok paaf")
        tr_patch.return_value = True
        rep = await trigger_sub_reactions(message, debug=True)
        self.assertIs(rep, True)
        tr_patch.assert_called_once_with(message, chain="baazA",
                                         sensi=0.9, debug=True)
        ctx.assert_sent()
        tr_patch.reset_mock()

        # several > 4-length words, all False
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "book@! a baazA tok pa "
                                            "frooookpoozpzpzpzppa")
        tr_patch.side_effect = [False, False, False]
        rep = await trigger_sub_reactions(message)
        self.assertIs(rep, False)
        self.assertEqual(tr_patch.call_args_list, [
            mock.call(message, chain="frooookpoozpzpzpzppa", sensi=0.9,
                      debug=False),
            mock.call(message, chain="book@!", sensi=0.9, debug=False),
            mock.call(message, chain="baazA", sensi=0.9, debug=False),
        ])
        ctx.assert_sent()
        tr_patch.reset_mock()

        # several > 4-length words, second True
        ctx = mock_discord.get_ctx(None)
        message = mock_discord.message(ctx, "book@! a baazA tok pa "
                                            "frooookpoozpzpzpzppa")
        tr_patch.side_effect = [False, True]
        rep = await trigger_sub_reactions(message)
        self.assertIs(rep, True)
        self.assertEqual(tr_patch.call_args_list, [
            mock.call(message, chain="frooookpoozpzpzpzppa", sensi=0.9,
                      debug=False),
            mock.call(message, chain="book@!", sensi=0.9, debug=False),
        ])
        ctx.assert_sent()
        tr_patch.reset_mock()


    async def test_trigger_di(self):
        """Unit tests for IA.trigger_di function."""
        # async def trigger_di(message)
        trigger_di = IA.trigger_di
        diprefs = ["di", "dy", "dis ", "dit ", "dis-", "dit-"]
        criprefs = ["cri", "cry", "kri", "kry"]

        samples = {
            "": False,
            "boozabaka": False,
            **{f"{pref}kaboom": "kaboom" for pref in diprefs},
            **{f"{pref}kaé@@m": "KAÉ@@M" for pref in criprefs},
            **{f"aa{pref}ka{pref}oh": f"ka{pref}oh" for pref in diprefs},
        }

        # all samples
        for sample, result in samples.items():
            ctx = mock_discord.get_ctx(None)
            message = mock_discord.message(ctx, sample)
            rep = await trigger_di(message)
            if result is False:
                self.assertIs(rep, False)
                ctx.assert_sent()
            else:
                self.assertIs(rep, True)
                ctx.assert_sent(result)


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.IA.fetch_tenor")
    async def test_trigger_gif(self, ft_patch):
        """Unit tests for IA.trigger_gif function."""
        # async def trigger_gif(message)
        trigger_gif = IA.trigger_gif
        config.bot.in_fals = [12, 13]

        # not in FALS
        ctx = mock_discord.get_ctx(None)
        ctx.channel.id = 2
        message = mock_discord.message(ctx, "booza")
        rep = await trigger_gif(message)
        self.assertIs(rep, False)
        ft_patch.assert_not_called()
        ctx.assert_sent()

        # in FALS, return None
        ctx = mock_discord.get_ctx(None)
        ctx.channel.id = 12
        message = mock_discord.message(ctx, "booza")
        ft_patch.return_value = None
        rep = await trigger_gif(message)
        self.assertIs(rep, False)
        ft_patch.assert_called_once_with("booza")
        ctx.assert_sent()
        ft_patch.reset_mock()

        # in FALS, return a gif
        ctx = mock_discord.get_ctx(None)
        ctx.channel.id = 12
        message = mock_discord.message(ctx, "booza")
        ft_patch.return_value = "gif://cgénial"
        rep = await trigger_gif(message)
        self.assertIs(rep, True)
        ft_patch.assert_called_once_with("booza")
        ctx.assert_sent("gif://cgénial")
        ft_patch.reset_mock()

        config.bot.in_fals = []


    async def test_trigger_mot_unique(self):
        """Unit tests for IA.trigger_mot_unique function."""
        # async def trigger_mot_unique(message)
        trigger_mot_unique = IA.trigger_mot_unique

        samples = {
            "": False,
            "bla bla": False,
            "boozabaka": "Boozabaka ?",
            "booza-baka": "Booza-baka ?",
            "@!!!": "@!!! ?",
            "http://oui": False,
        }

        # all samples
        for sample, result in samples.items():
            ctx = mock_discord.get_ctx(None)
            message = mock_discord.message(ctx, sample)
            rep = await trigger_mot_unique(message)
            if result is False:
                self.assertIs(rep, False)
                ctx.assert_sent()
            else:
                self.assertIs(rep, True)
                ctx.assert_sent(result)


    async def test_trigger_a_ou_b(self):
        """Unit tests for IA.trigger_a_ou_b function."""
        # async def trigger_a_ou_b(message)
        trigger_a_ou_b = IA.trigger_a_ou_b

        samples = {
            "": False,
            "bla bla": False,
            "boozabaka": False,
            "booza ou baka": "Baka.",
            "a v à @ ou b. !??,!;;!": "B.",
            "a v à @ ou b. !??,!;;!a": "B. !??,!;;!a.",
        }

        # all samples
        for sample, result in samples.items():
            ctx = mock_discord.get_ctx(None)
            message = mock_discord.message(ctx, sample)
            rep = await trigger_a_ou_b(message)
            if result is False:
                self.assertIs(rep, False)
                ctx.assert_sent()
            else:
                self.assertIs(rep, True)
                ctx.assert_sent(result)


    async def test_default(self):
        """Unit tests for IA.default function."""
        # async def default(message)
        default = IA.default

        samples = {
            "": False,
            "bla bla": False,
            "boozabaka": False,
            "booza ou baka": "Baka.",
            "a v à @ ou b. !??,!;;!": "B.",
            "a v à @ ou b. !??,!;;!a": "B. !??,!;;!a.",
        }

        # all samples
        for sample, result in samples.items():
            ctx = mock_discord.get_ctx(None)
            message = mock_discord.message(ctx, sample)
            rep = await default(message)
            self.assertIs(rep, True)


    @mock.patch("lgrez.features.IA.trigger_at_mj")
    @mock.patch("lgrez.features.IA.trigger_gif")
    @mock.patch("lgrez.features.IA.trigger_roles")
    @mock.patch("lgrez.features.IA.trigger_reactions")
    @mock.patch("lgrez.features.IA.trigger_sub_reactions")
    @mock.patch("lgrez.features.IA.trigger_a_ou_b")
    @mock.patch("lgrez.features.IA.trigger_di")
    @mock.patch("lgrez.features.IA.trigger_mot_unique")
    @mock.patch("lgrez.features.IA.default")
    async def test_process_IA(self, *patches):
        """Unit tests for IA.process_IA function."""
        # async def process_IA(message, debug=False)
        process_IA = IA.process_IA
        # patches = reverse order of triggers

        # test if none triggered except default, then mot_unique, then...
        for i in range(len(patches)):
            # made reaction = patch[i]
            for ii, patch in enumerate(patches):
                if ii <= i:     # i and lower priority: return True
                    patch.return_value = True
                else:           # higher priority: return False
                    patch.return_value = False

            ctx = mock_discord.get_ctx(None)
            message = mock_discord.message(ctx, "")
            rep = await process_IA(message)
            for ii, patch in enumerate(patches):
                if ii >= i:     # i and higher priority: called
                    patch.assert_called_once()
                    self.assertEqual(patch.call_args.args[0], message)
                else:           # lower priority: not called
                    patch.assert_not_called()
                patch.reset_mock()



class TestGestionIA(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.IA commands."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = IA.GestionIA(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()


    async def test_stfu(self):
        """Unit tests for !stfu command."""
        # async def stfu(self, ctx, force=None)
        stfu = self.cog.stfu
        config.bot.in_stfu = [12, 13]

        # Not in STFU, no force
        ctx = mock_discord.get_ctx(stfu)
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("je me tais")
        self.assertIn(10, config.bot.in_stfu)

        # In STFU, no force
        ctx = mock_discord.get_ctx(stfu)
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("reparler")
        self.assertNotIn(10, config.bot.in_stfu)

        # Not in STFU, force "on"
        ctx = mock_discord.get_ctx(stfu, force="on")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("je me tais")
        self.assertIn(10, config.bot.in_stfu)

        # In STFU, force "on"
        ctx = mock_discord.get_ctx(stfu, force="on")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertIn(10, config.bot.in_stfu)
        config.bot.in_stfu.remove(10)

        # Not in STFU, force "start"
        ctx = mock_discord.get_ctx(stfu, force="start")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("je me tais")
        self.assertIn(10, config.bot.in_stfu)

        # In STFU, force "start"
        ctx = mock_discord.get_ctx(stfu, force="start")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertIn(10, config.bot.in_stfu)
        config.bot.in_stfu.remove(10)

        # Not in STFU, force "off"
        ctx = mock_discord.get_ctx(stfu, force="off")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertNotIn(10, config.bot.in_stfu)

        # In STFU, force "off"
        config.bot.in_stfu.append(10)
        ctx = mock_discord.get_ctx(stfu, force="off")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("reparler")
        self.assertNotIn(10, config.bot.in_stfu)

        # Not in STFU, force "stop"
        ctx = mock_discord.get_ctx(stfu, force="stop")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertNotIn(10, config.bot.in_stfu)

        # In STFU, force "stop"
        config.bot.in_stfu.append(10)
        ctx = mock_discord.get_ctx(stfu, force="stop")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("reparler")
        self.assertNotIn(10, config.bot.in_stfu)

        # Not in STFU, force autre
        ctx = mock_discord.get_ctx(stfu, force="bzzt")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertIn(10, config.bot.in_stfu)

        # In STFU, force autre
        ctx = mock_discord.get_ctx(stfu, force="bzzt")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertNotIn(10, config.bot.in_stfu)


    async def test_fals(self):
        """Unit tests for !fals command."""
        # async def fals(self, ctx, force=None)
        fals = self.cog.fals
        config.bot.in_fals = [12, 13]

        # Not in FALS, no force
        ctx = mock_discord.get_ctx(fals)
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("saucisse")
        self.assertIn(10, config.bot.in_fals)

        # In FALS, no force
        ctx = mock_discord.get_ctx(fals)
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("pas abuser")
        self.assertNotIn(10, config.bot.in_fals)

        # Not in FALS, force "on"
        ctx = mock_discord.get_ctx(fals, force="on")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("saucisse")
        self.assertIn(10, config.bot.in_fals)

        # In FALS, force "on"
        ctx = mock_discord.get_ctx(fals, force="on")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertIn(10, config.bot.in_fals)
        config.bot.in_fals.remove(10)

        # Not in FALS, force "start"
        ctx = mock_discord.get_ctx(fals, force="start")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("saucisse")
        self.assertIn(10, config.bot.in_fals)

        # In FALS, force "start"
        ctx = mock_discord.get_ctx(fals, force="start")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertIn(10, config.bot.in_fals)
        config.bot.in_fals.remove(10)

        # Not in FALS, force "off"
        ctx = mock_discord.get_ctx(fals, force="off")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertNotIn(10, config.bot.in_fals)

        # In FALS, force "off"
        config.bot.in_fals.append(10)
        ctx = mock_discord.get_ctx(fals, force="off")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("pas abuser")
        self.assertNotIn(10, config.bot.in_fals)

        # Not in FALS, force "stop"
        ctx = mock_discord.get_ctx(fals, force="stop")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertNotIn(10, config.bot.in_fals)

        # In FALS, force "stop"
        config.bot.in_fals.append(10)
        ctx = mock_discord.get_ctx(fals, force="stop")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent("pas abuser")
        self.assertNotIn(10, config.bot.in_fals)

        # Not in FALS, force autre
        ctx = mock_discord.get_ctx(fals, force="bzzt")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertIn(10, config.bot.in_fals)

        # In FALS, force autre
        ctx = mock_discord.get_ctx(fals, force="bzzt")
        ctx.channel.id = 10
        await ctx.invoke()
        ctx.assert_sent()
        self.assertNotIn(10, config.bot.in_fals)


    @mock.patch("lgrez.features.IA.process_IA")
    async def test_react(self, pia_patch):
        """Unit tests for !react command."""
        # async def react(self, ctx, *, trigger)
        react = self.cog.react

        class SaveContent:
            content = None
            @classmethod
            def save(cls, msg, debug=None):
                cls.content = msg.content

        pia_patch.side_effect = SaveContent.save

        # non-MJ
        ctx = mock_discord.get_ctx(react, trigger="booz")
        ctx.author.top_role = config.Role.joueur_en_vie
        ctx.message.content = "original"
        await ctx.invoke()
        pia_patch.assert_called_once_with(ctx.message, debug=False)
        self.assertEqual(SaveContent.content, "booz")
        self.assertEqual(ctx.message.content, "original")
        ctx.assert_sent()
        pia_patch.reset_mock()

        # MJ
        ctx = mock_discord.get_ctx(react, trigger="booz")
        ctx.author.top_role = config.Role.mj
        ctx.message.content = "original"
        await ctx.invoke()
        pia_patch.assert_called_once_with(ctx.message, debug=True)
        self.assertEqual(SaveContent.content, "booz")
        self.assertEqual(ctx.message.content, "original")
        ctx.assert_sent()


    @mock.patch("lgrez.features.IA.fetch_tenor")
    async def test_reactfals(self, ft_patch):
        """Unit tests for !reactfals command."""
        # async def reactfals(self, ctx, *, trigger)
        reactfals = self.cog.reactfals

        # no GIF
        ctx = mock_discord.get_ctx(reactfals, trigger="booz")
        ft_patch.return_value = None
        await ctx.invoke()
        ft_patch.assert_called_once_with("booz")
        ctx.assert_sent("Palaref")
        ft_patch.reset_mock()

        # MJ
        ctx = mock_discord.get_ctx(reactfals, trigger="booz")
        ft_patch.return_value = "giiiif"
        await ctx.invoke()
        ft_patch.assert_called_once_with("booz")
        ctx.assert_sent("giiiif")
        ft_patch.reset_mock()


    @mock_bdd.patch_db
    @mock.patch("lgrez.features.IA._build_sequence")
    async def test_addIA(self, bs_patch):
        """Unit tests for !addIA command."""
        # async def addIA(self, ctx, *, triggers=None)
        addIA = self.cog.addIA

        # no triggers, simple gave
        ctx = mock_discord.get_ctx(addIA)
        bs_patch.return_value = "s€quenZ"
        with mock_discord.interact(
            ("wait_for_message_here", mock_discord.message(ctx, "trigzz"))
        ):
            await ctx.invoke()
        bs_patch.assert_called_once_with(ctx)
        ctx.assert_sent("déclencheurs", "trigzz", "s€quenZ", "ajoutée en base")
        trig = bdd.Trigger.query.one()
        reac = bdd.Reaction.query.one()
        self.assertEqual(trig.trigger, "trigzz")
        self.assertEqual(trig.reaction, reac)
        self.assertEqual(reac.reponse, "s€quenZ")
        bdd.Trigger.delete(trig, reac)
        bs_patch.reset_mock()

        # complex triggers
        triggers = "trigger\n\nTR1; trégèrçù; trÉgÈrÇÙ   ;;  ❤\nah!"
        formated_trgz = ["trigger", "tr1", "tregercu", "tregercu", "❤", "ah!"]
        ctx = mock_discord.get_ctx(addIA, triggers=triggers)
        bs_patch.return_value = "s€quenZ"
        await ctx.invoke()
        bs_patch.assert_called_once_with(ctx)
        ctx.assert_sent(formated_trgz, "s€quenZ", "ajoutée en base")
        trigs = bdd.Trigger.query.all()
        reac = bdd.Reaction.query.one()
        self.assertEqual(len(trigs), 5)
        self.assertEqual({trig.trigger for trig in trigs}, set(formated_trgz))
        self.assertEqual([trig.reaction for trig in trigs], [reac]*5)
        self.assertEqual(reac.reponse, "s€quenZ")
        bs_patch.reset_mock()


    @mock_bdd.patch_db
    async def test_listIA(self):
        """Unit tests for !listIA command."""
        # async def listIA(self, ctx, trigger=None, sensi=0.5)
        listIA = self.cog.listIA

        reacs = [
            bdd.Reaction(reponse="s1quenZ"),
            bdd.Reaction(reponse="s€quenZ2"),
            bdd.Reaction(reponse="s€qu3enZ"),
            bdd.Reaction(reponse="s€4quenZ"),
            bdd.Reaction(reponse="s€que5nZ"*1000),
        ]
        triggers = [
            bdd.Trigger(trigger="trigz1", reaction=reacs[0]),
            bdd.Trigger(trigger="tr1gZ2", reaction=reacs[0]),
            bdd.Trigger(trigger="tr!Gz3", reaction=reacs[0]),
            bdd.Trigger(trigger="tr!Gz4", reaction=reacs[1]),
            bdd.Trigger(trigger="tr!Gz5", reaction=reacs[1]),
            bdd.Trigger(trigger="tr!Gz6", reaction=reacs[2]),
            bdd.Trigger(trigger="tr!Gz7", reaction=reacs[3]),
            bdd.Trigger(trigger="tr!G88", reaction=reacs[4]),
        ]
        bdd.Reaction.add(*reacs, *triggers)

        # list all
        ctx = mock_discord.get_ctx(listIA)
        await ctx.invoke()
        ctx.assert_sent([reac.reponse[:10] for reac in reacs]
                        + [trig.trigger for trig in triggers] + ["[...]"])
        ctx.assert_not_sent("s€que5nZ"*1000)

        # filter
        ctx = mock_discord.get_ctx(listIA, "1gZ2")
        await ctx.invoke()
        ctx.assert_sent(["tr1gZ2", "s1quenZ"])
        ctx.assert_not_sent(["s€quenZ2", "s€qu3enZ", "s€4quenZ", "s€que5nZ"])

        # filter & sensi
        ctx = mock_discord.get_ctx(listIA, "1gZ2", sensi=0.3)
        await ctx.invoke()
        ctx.assert_sent(["s1quenZ", "s€quenZ2", "s€qu3enZ", "s€4quenZ"])
        ctx.assert_not_sent("s€que5nZ")


    @mock_bdd.patch_db
    @mock.patch("lgrez.features.IA._build_sequence")
    async def test_modifIA(self, bs_patch):
        """Unit tests for !modifIA command."""
        # async def modifIA(self, ctx, *, trigger=None)
        modifIA = self.cog.modifIA

        reac = bdd.Reaction(reponse="s€quenZ")
        triggers = [
            bdd.Trigger(trigger="trigz1", reaction=reac),
            bdd.Trigger(trigger="tr1gZ2", reaction=reac),
            bdd.Trigger(trigger="tr!Gz3", reaction=reac),
        ]
        bdd.Reaction.add(reac, *triggers)

        # nothing found
        ctx = mock_discord.get_ctx(modifIA)
        bs_patch.return_value = "s€quenZ"
        with mock_discord.interact(
            ("wait_for_message_here", mock_discord.message(ctx, "ooooo"))
        ):
            await ctx.invoke()
        ctx.assert_sent("déclencheur", "Rien trouvé")
        bs_patch.assert_not_called()

        # modif triggers
        ctx = mock_discord.get_ctx(modifIA, trigger="trigz")
        with mock_discord.interact(
            ("wait_for_react_clic", 1),         # modif triggers
            ("wait_for_react_clic", "ahbon"),   # trigger 4
            ("wait_for_react_clic", "3"),       # delete trigger 3
            ("wait_for_react_clic", "0"),       # end
        ):
            await ctx.invoke()
        ctx.assert_sent(
            ["trigz1", "tr1gZ2", "tr!Gz3", "s€quenZ"], "Modifier",
            ["Supprimer", "ajouter", "trigz1", "tr1gZ2", "tr!Gz3"],
            ["Supprimer", "ajouter", "trigz1", "tr1gZ2", "tr!Gz3", "ahbon"],
            ["Supprimer", "ajouter", "trigz1", "tr1gZ2", "ahbon"],
            "Fini",
        )
        self.assertEqual(bdd.Reaction.query.one(), reac)
        self.assertEqual({trig.trigger for trig in reac.triggers},
                         {"trigz1", "tr1gZ2", "ahbon"})
        self.assertEqual(reac.reponse, "s€quenZ")
        bs_patch.assert_not_called()

        # delete all triggers
        ctx = mock_discord.get_ctx(modifIA, trigger="trigz")
        with mock_discord.interact(
            ("wait_for_react_clic", 1),         # modif triggers
            ("wait_for_react_clic", "3"),       # delete trigger 3
            ("wait_for_react_clic", "1"),       # delete trigger 1
            ("wait_for_react_clic", "1"),       # delete trigger 1
            ("wait_for_react_clic", "0"),       # end
        ):
            await ctx.invoke()
        ctx.assert_sent(
            ["trigz1", "tr1gZ2", "ahbon", "s€quenZ"], "Modifier",
            ["Supprimer", "ajouter", "trigz1", "tr1gZ2", "ahbon"],
            ["Supprimer", "ajouter", "trigz1", "tr1gZ2"],
            ["Supprimer", "ajouter", "tr1gZ2"],
            ["Supprimer", "ajouter"],
            "suppression",
        )
        self.assertEqual(len(bdd.Reaction.query.all()), 0)
        self.assertEqual(len(bdd.Trigger.query.all()), 0)
        bs_patch.assert_not_called()

        # modif sequence (simple)
        reac = bdd.Reaction(reponse="s€quenZ")
        triggers = [
            bdd.Trigger(trigger="trigz1", reaction=reac),
            bdd.Trigger(trigger="tr1gZ2", reaction=reac),
            bdd.Trigger(trigger="tr!Gz3", reaction=reac),
        ]
        bdd.Reaction.add(reac, *triggers)

        ctx = mock_discord.get_ctx(modifIA, trigger="trigz")
        bs_patch.return_value = "new_s€qu€nZ"
        with mock_discord.interact(
            ("wait_for_react_clic", 2),         # modif sequence
        ):
            await ctx.invoke()
        ctx.assert_sent(
            ["trigz1", "tr1gZ2", "tr!Gz3", "s€quenZ"], "Modifier",
            "Fini",
        )
        self.assertEqual(bdd.Reaction.query.one(), reac)
        self.assertEqual({trig.trigger for trig in reac.triggers},
                         {"trigz1", "tr1gZ2", "tr!Gz3"})
        self.assertEqual(reac.reponse, "new_s€qu€nZ")
        bs_patch.assert_called_once_with(ctx)
        bs_patch.reset_mock()

        # modif sequence (complex)
        reac.reponse = f"s€quenZ{IA.MARK_THEN}oui"
        reac.update()

        ctx = mock_discord.get_ctx(modifIA, trigger="trigz")
        bs_patch.return_value = "new_s€qu€nZ"
        with mock_discord.interact(
            ("wait_for_react_clic", 2),         # modif sequence
        ):
            await ctx.invoke()
        ctx.assert_sent(
            ["trigz1", "tr1gZ2", "tr!Gz3", "s€quenZ"], "Modifier",
            "modifiée rapidement",
            "Fini",
        )
        self.assertEqual(bdd.Reaction.query.one(), reac)
        self.assertEqual({trig.trigger for trig in reac.triggers},
                         {"trigz1", "tr1gZ2", "tr!Gz3"})
        self.assertEqual(reac.reponse, "new_s€qu€nZ")
        bs_patch.assert_called_once_with(ctx)
        bs_patch.reset_mock()

        # delete sequence
        ctx = mock_discord.get_ctx(modifIA, trigger="trigz")
        with mock_discord.interact(
            ("wait_for_react_clic", 0),         # dekete sequence
        ):
            await ctx.invoke()
        ctx.assert_sent(
            ["trigz1", "tr1gZ2", "tr!Gz3", "new_s€qu€nZ"], "Modifier",
            "Fini",
        )
        self.assertEqual(len(bdd.Reaction.query.all()), 0)
        self.assertEqual(len(bdd.Trigger.query.all()), 0)
        bs_patch.assert_not_called()
