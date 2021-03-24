import unittest
from unittest import mock

from lgrez import config, bdd
from lgrez.features import voter_agir
from test import mock_discord, mock_bdd, mock_env


class TestVoterAgirFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.voter_agir utility functions."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    @mock_bdd.patch_db      # Empty database for this method
    @mock_env.patch_env(LGREZ_DATA_SHEET_ID="uiz")
    @mock.patch("lgrez.blocs.gsheets.connect")
    async def test_export_vote(self, gconnect_patch):
        """Unit tests for voter_agir.export_vote function."""
        # def export_vote(vote, joueur)
        export_vote = voter_agir.export_vote
        mock_bdd.add_campsroles(10, 10)
        joueur = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                            _role_slug="role7", _camp_slug="camp8",
                            vote_condamne_="oh", vote_maire_="ah",
                            vote_loups_="eh")
        joueur.add()
        bdd.BaseAction(slug="ouiZ").add()
        bdd.BaseAction(slug="nonZ").add()
        bdd.BaseAction(slug="lalaZ").add()
        bdd.Action(joueur=joueur, _base_slug="ouiZ", decision_="dZ1").add()
        bdd.Action(joueur=joueur, _base_slug="nonZ", decision_="dZ2").add()
        bdd.Action(joueur=joueur, _base_slug="lalaZ", decision_=None).add()

        # no LGREZ_DATA_SHEET_ID
        with mock_env.patch_env(LGREZ_DATA_SHEET_ID=None):
            with self.assertRaises(RuntimeError):
                export_vote("cond", joueur)
        gconnect_patch.assert_not_called()

        # vote = bad value
        with self.assertRaises(ValueError):
            export_vote("bzz", joueur)
        gconnect_patch.assert_not_called()

        # vote = "cond"
        export_vote("cond", joueur)
        gconnect_patch.assert_called_once_with("uiz")
        gconnect_patch().worksheet.assert_called_with("votecond_brut")
        gconnect_patch().worksheet().append_row.assert_called_once()
        appened = gconnect_patch().worksheet().append_row.call_args.args[0]
        self.assertEqual(["Joueur1", "oh"], appened[1:])
        gconnect_patch.reset_mock(return_value=True)

        # vote = "maire"
        export_vote("maire", joueur)
        gconnect_patch.assert_called_once_with("uiz")
        gconnect_patch().worksheet.assert_called_with("votemaire_brut")
        gconnect_patch().worksheet().append_row.assert_called_once()
        appened = gconnect_patch().worksheet().append_row.call_args.args[0]
        self.assertEqual(["Joueur1", "ah"], appened[1:])
        gconnect_patch.reset_mock(return_value=True)

        # vote = "loups"
        export_vote("loups", joueur)
        gconnect_patch.assert_called_once_with("uiz")
        gconnect_patch().worksheet.assert_called_with("voteloups_brut")
        gconnect_patch().worksheet().append_row.assert_called_once()
        appened = gconnect_patch().worksheet().append_row.call_args.args[0]
        self.assertEqual(["Joueur1", "camp8", "eh"], appened[1:])
        gconnect_patch.reset_mock(return_value=True)

        # vote = "action"
        export_vote("action", joueur)
        gconnect_patch.assert_called_once_with("uiz")
        gconnect_patch().worksheet.assert_called_with("actions_brut")
        gconnect_patch().worksheet().append_row.assert_called_once()
        appened = gconnect_patch().worksheet().append_row.call_args.args[0]
        self.assertEqual(["Joueur1", "role7", "camp8"], appened[1:4])
        self.assertIn("ouiZ", appened[4])
        self.assertIn("dZ1", appened[4])
        self.assertIn("nonZ", appened[4])
        self.assertIn("dZ2", appened[4])
        self.assertNotIn("lalaZ", appened[4])



class TestVoterAgir(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.voter_agir commands."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = voter_agir.VoterAgir(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()
        

    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.voter_agir.export_vote")    # tested before
    async def test_vote(self, export_patch):
        """Unit tests for !vote command."""
        # async def vote(self, ctx, *, cible=None)
        vote = self.cog.vote
        mock_bdd.add_campsroles()
        joueur = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                            votant_village=False, vote_condamne_="oh")
        joueur.add()

        # votant_village False
        ctx = mock_discord.get_ctx(vote, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("pas autorisé", ctx.send.call_args.args[0])
        export_patch.assert_not_called()

        # no vote
        joueur.votant_village = True
        joueur.vote_condamne_ = None
        joueur.update()
        ctx = mock_discord.get_ctx(vote, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("pas de vote", ctx.send.call_args.args[0].lower())
        export_patch.assert_not_called()

        # not haroted
        joueur.vote_condamne_ = "oh"
        joueur.update()
        bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2").add()
        ctx = mock_discord.get_ctx(vote, cible="Joueur2", _caller_id=1)
        with mock_discord.interact(("yes_no", False)):
            # abort (answer "no" at non-haroted warning)
            await ctx.invoke()
        calls = ctx.send.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertIn("n'a pas (encore) subi", calls[0].args[0])
        self.assertIn("mission aborted", calls[1].args[0])
        export_patch.assert_not_called()

        # closed during haro check
        def close_vote(_):
            joueur.vote_condamne_ = None
            joueur.update()
            return True
        ctx = mock_discord.get_ctx(vote, cible="Joueur2", _caller_id=1)
        with mock.patch("lgrez.blocs.tools.yes_no", side_effect=close_vote):
            # close vote and answer "yes" at non-haroted warning
            await ctx.invoke()
        calls = ctx.send.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertIn("a fermé entre temps", calls[1].args[0])
        export_patch.assert_not_called()

        # ok
        joueur.vote_condamne_ = "oh"        # reopen vote
        joueur.update()
        bdd.CandidHaro(_joueur_id=2, type=bdd.CandidHaroType.haro).add()
        ctx = mock_discord.get_ctx(vote, cible="Joueur2", _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertIn("bien pris en compte", ctx.send.call_args.args[0])
        self.assertEqual(joueur.vote_condamne_, "Joueur2")
        export_patch.assert_called_once_with("cond", joueur)
        export_patch.reset_mock()

        # ok, cible not specified
        joueur.vote_condamne_ = "oh"        # reset vote
        joueur.update()
        ctx = mock_discord.get_ctx(vote, _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("zzz")),
                ("wait_for_message_here", ctx.new_message("zzz")),
                ("wait_for_message_here", ctx.new_message("Joueur2"))):
            await ctx.invoke()
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertIn("bien pris en compte", ctx.send.call_args.args[0])
        self.assertEqual(joueur.vote_condamne_, "Joueur2")
        export_patch.assert_called_once_with("cond", joueur)
        export_patch.reset_mock()


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.voter_agir.export_vote")    # tested before
    async def test_votemaire(self, export_patch):
        """Unit tests for !votemaire command."""
        # async def votemaire(self, ctx, *, cible=None)
        votemaire = self.cog.votemaire
        mock_bdd.add_campsroles()
        joueur = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                            votant_village=False, vote_maire_="oh")
        joueur.add()
        export_patch.assert_not_called()

        # votant_village False
        ctx = mock_discord.get_ctx(votemaire, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("pas autorisé", ctx.send.call_args.args[0])
        export_patch.assert_not_called()

        # no votemaire
        joueur.votant_village = True
        joueur.vote_maire_ = None
        joueur.update()
        ctx = mock_discord.get_ctx(votemaire, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("pas de vote", ctx.send.call_args.args[0].lower())
        export_patch.assert_not_called()

        # not candid
        joueur.vote_maire_ = "oh"
        joueur.update()
        bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2").add()
        ctx = mock_discord.get_ctx(votemaire, cible="Joueur2", _caller_id=1)
        with mock_discord.interact(("yes_no", False)):
            # abort (answer "no" at non-haroted warning)
            await ctx.invoke()
        calls = ctx.send.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertIn("ne s'est pas (encore) présenté", calls[0].args[0])
        self.assertIn("mission aborted", calls[1].args[0])
        export_patch.assert_not_called()

        # closed during haro check
        def close_vote(_):
            joueur.vote_maire_ = None
            joueur.update()
            return True
        ctx = mock_discord.get_ctx(votemaire, cible="Joueur2", _caller_id=1)
        with mock_discord.interact(("yes_no", close_vote)):
            # close votemaire and answer "yes" at non-haroted warning
            await ctx.invoke()
        calls = ctx.send.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertIn("a fermé entre temps", calls[1].args[0])
        export_patch.assert_not_called()

        # ok
        joueur.vote_maire_ = "oh"        # reopen votemaire
        joueur.update()
        bdd.CandidHaro(_joueur_id=2, type=bdd.CandidHaroType.candidature).add()
        ctx = mock_discord.get_ctx(votemaire, cible="Joueur2", _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertIn("bien pris en compte", ctx.send.call_args.args[0])
        self.assertEqual(joueur.vote_maire_, "Joueur2")
        export_patch.assert_called_once_with("maire", joueur)
        export_patch.reset_mock()

        # ok, cible not specified
        joueur.vote_maire_ = "oh"        # reset votemaire
        joueur.update()
        ctx = mock_discord.get_ctx(votemaire, _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("zzz")),
                ("wait_for_message_here", ctx.new_message("zzz")),
                ("wait_for_message_here", ctx.new_message("Joueur2"))):
            await ctx.invoke()
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertIn("bien pris en compte", ctx.send.call_args.args[0])
        self.assertEqual(joueur.vote_maire_, "Joueur2")
        export_patch.assert_called_once_with("maire", joueur)
        export_patch.reset_mock()


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.voter_agir.export_vote")    # tested before
    async def test_voteloups(self, export_patch):
        """Unit tests for !voteloups command."""
        # async def voteloups(self, ctx, *, cible=None)
        voteloups = self.cog.voteloups
        mock_bdd.add_campsroles()
        joueur = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                            votant_loups=False, vote_loups_="oh")
        joueur.add()

        # votant_loups False
        ctx = mock_discord.get_ctx(voteloups, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("pas autorisé", ctx.send.call_args.args[0])
        export_patch.assert_not_called()

        # no voteloups
        joueur.votant_loups = True
        joueur.vote_loups_ = None
        joueur.update()
        ctx = mock_discord.get_ctx(voteloups, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("pas de vote", ctx.send.call_args.args[0].lower())
        export_patch.assert_not_called()

        # closed during cible choice
        joueur.vote_loups_ = "oh"
        joueur.update()
        cible = bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2")
        cible.add()

        ctx = mock_discord.get_ctx(voteloups, _caller_id=1)

        def close_vote(*args, **kwargs):
            joueur.vote_loups_ = None
            joueur.update()
            return ctx.new_message("Joueur2")

        with mock_discord.interact(("wait_for_message_here", close_vote)):
            # close voteloups and return cible
            await ctx.invoke()
        self.assertEqual(ctx.send.call_count, 2)
        self.assertIn("a fermé entre temps", ctx.send.call_args.args[0])
        export_patch.assert_not_called()

        # ok
        joueur.vote_loups_ = "oh"        # reopen voteloups
        joueur.update()
        ctx = mock_discord.get_ctx(voteloups, cible="Joueur2", _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertIn("bien pris en compte", ctx.send.call_args.args[0])
        self.assertEqual(joueur.vote_loups_, "Joueur2")
        export_patch.assert_called_once_with("loups", joueur)
        export_patch.reset_mock()

        # ok, cible not specified
        joueur.vote_loups_ = "oh"        # reset voteloups
        joueur.update()
        ctx = mock_discord.get_ctx(voteloups, _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("zzz")),
                ("wait_for_message_here", ctx.new_message("zzz")),
                ("wait_for_message_here", ctx.new_message("Joueur2"))):
            await ctx.invoke()
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertIn("bien pris en compte", ctx.send.call_args.args[0])
        self.assertEqual(joueur.vote_loups_, "Joueur2")
        export_patch.assert_called_once_with("loups", joueur)
        export_patch.reset_mock()


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.gestion_actions.close_action")
    @mock.patch("lgrez.features.voter_agir.export_vote")    # tested before
    async def test_action(self, export_patch, ca_patch):
        """Unit tests for !action command."""
        # async def action(self, ctx, *, decision=None)
        action = self.cog.action
        mock_bdd.add_campsroles()
        joueur = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                            role_actif=False)
        joueur.add()

        # role_actif False
        ctx = mock_discord.get_ctx(action, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("ne peux pas utiliser", ctx.send.call_args.args[0])
        export_patch.assert_not_called()
        ca_patch.assert_not_called()

        # no actions
        joueur.role_actif = True
        joueur.update()
        ctx = mock_discord.get_ctx(action, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Aucune action en cours", ctx.send.call_args.args[0])
        export_patch.assert_not_called()
        ca_patch.assert_not_called()

        # 1 closed action
        bdd.BaseAction(slug="ouiZ").add()
        action1 = bdd.Action(joueur=joueur, _base_slug="ouiZ")
        action1.add()
        ctx = mock_discord.get_ctx(action, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Aucune action en cours", ctx.send.call_args.args[0])
        export_patch.assert_not_called()
        ca_patch.assert_not_called()

        # 1 open action and decision_
        action1.decision_ = "oh"
        action1.update()
        ctx = mock_discord.get_ctx(action, decision="boo", _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("boo", ctx.send.call_args.args[0])
        self.assertIn("bien prise en compte", ctx.send.call_args.args[0])
        self.assertIn("ouiZ", ctx.send.call_args.args[0])
        self.assertEqual(action1.decision_, "boo")
        export_patch.assert_called_once_with("action", joueur)
        export_patch.reset_mock()
        ca_patch.assert_not_called()

        # 1 open action and no decision_
        action1.decision_ = "oh"
        action1.update()
        ctx = mock_discord.get_ctx(action, _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("boo"))):
            await ctx.invoke()
        ctx.send.assert_called()
        self.assertIn("boo", ctx.send.call_args.args[0])
        self.assertIn("bien prise en compte", ctx.send.call_args.args[0])
        self.assertIn("ouiZ", ctx.send.call_args.args[0])
        self.assertEqual(action1.decision_, "boo")
        export_patch.assert_called_once_with("action", joueur)
        export_patch.reset_mock()
        ca_patch.assert_not_called()

        # 1 open INSTANT action and abort
        action1.decision_ = "oh"
        action1.base.instant = True
        action1.update()
        ctx = mock_discord.get_ctx(action, decision="boo", _caller_id=1)
        with mock_discord.interact(("yes_no", False)):
            # abort (answer "no" at instant warning)
            await ctx.invoke()
        ctx.send.assert_called()
        calls = ctx.send.call_args_list
        self.assertIn("conséquence instantanée", calls[0].args[0])
        self.assertIn("Ça part ?", calls[0].args[0])
        self.assertIn("aborted", calls[1].args[0])
        self.assertEqual(action1.decision_, "oh")
        export_patch.assert_not_called()
        ca_patch.assert_not_called()

        # 1 open INSTANT action and proceed
        ctx = mock_discord.get_ctx(action, decision="boo", _caller_id=1)
        with mock_discord.interact(("yes_no", True)):
            # proceed (answer "yes" at instant warning)
            await ctx.invoke()
        ctx.assert_sent("Attention", [str(config.Role.mj.mention),
                                      "conséquence instantanée"])
        self.assertEqual(action1.decision_, "boo")
        export_patch.assert_called_once_with("action", joueur)
        export_patch.reset_mock()
        ca_patch.assert_called_once_with(action1)
        ca_patch.reset_mock()

        # 1 open action and closed during decision choice
        action1.decision_ = "oh"
        action1.base.instant = False
        action1.update()

        def close_action(*args, **kwargs):
            action1.decision_ = None
            action1.update()
            return ctx.new_message("boo")
        ctx = mock_discord.get_ctx(action, _caller_id=1)
        with mock_discord.interact(("wait_for_message_here", close_action)):
            # close action and return decision
            await ctx.invoke()
        ctx.send.assert_called()
        self.assertIn("a fermé entre temps", ctx.send.call_args.args[0])
        export_patch.assert_not_called()
        ca_patch.assert_not_called()

        # 2 open actions and decision_: ask
        action1.decision_ = "oh"
        action1.update()
        bdd.BaseAction(slug="nonZ").add()
        action2 = bdd.Action(joueur=joueur, _base_slug="nonZ", decision_="uh")
        action2.add()
        ctx = mock_discord.get_ctx(action, decision="ih", _caller_id=1)

        with mock_discord.interact(
                ("choice", 2),
                ("wait_for_message_here", ctx.new_message("boo"))):
            await ctx.invoke()
        ctx.send.assert_called()
        calls = ctx.send.call_args_list
        self.assertIn("ouiZ", calls[0].args[0])
        self.assertIn("nonZ", calls[0].args[0])
        self.assertIn("Pour laquelle", calls[0].args[0])
        self.assertIn("nonZ", calls[1].args[0])
        self.assertIn("veux-tu faire", calls[1].args[0])
        self.assertIn("boo", calls[2].args[0])
        self.assertIn("bien prise en compte", calls[2].args[0])
        self.assertIn("nonZ", calls[2].args[0])
        self.assertEqual(action1.decision_, "oh")
        self.assertEqual(action2.decision_, "boo")
        export_patch.assert_called_once_with("action", joueur)
        ca_patch.assert_not_called()
