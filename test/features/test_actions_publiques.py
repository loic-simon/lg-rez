import unittest
from unittest import mock

from lgrez import config, bdd
from lgrez.features import actions_publiques
from test import mock_discord, mock_bdd, mock_env


class TestActionsPubliques(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.actions_publiques commands."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = actions_publiques.ActionsPubliques(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()

    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.config.Channel.haros.send")
    @mock.patch("lgrez.config.Channel.debats.send")
    @mock_discord.interact()
    async def test_haro(self, send_debats_patch, send_haros_patch):
        """Unit tests for !haro command."""
        # async def haro(self, ctx, *, cible=None)
        haro = self.cog.haro
        mock_bdd.add_campsroles()
        joueur = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                            vote_condamne_=None)
        joueur.add()
        cible = bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2")
        cible.add()

        # no vote
        ctx = mock_discord.get_ctx(haro, cible="Joueur2", _caller_id=1)
        await ctx.invoke()
        ctx.assert_sent("Pas de vote")
        self.assertFalse(bdd.CandidHaro.query.all())    # no haro created
        send_debats_patch.assert_not_called()
        send_haros_patch.assert_not_called()

        # cible = dead
        joueur.vote_condamne_ = "bzzzt"
        cible.statut = bdd.Statut.mort
        cible.update()
        ctx = mock_discord.get_ctx(haro, cible="Joueur2", _caller_id=1)
        await ctx.invoke()
        ctx.assert_sent("pas assez souffert")
        self.assertFalse(bdd.CandidHaro.query.all())    # no haro created
        send_debats_patch.assert_not_called()
        send_haros_patch.assert_not_called()

        # cible = immortel
        cible.statut = bdd.Statut.immortel
        cible.update()
        ctx = mock_discord.get_ctx(haro, cible="Joueur2", _caller_id=1)
        await ctx.invoke()
        ctx.assert_sent("Comment oses-tu")
        self.assertFalse(bdd.CandidHaro.query.all())    # no haro created
        send_debats_patch.assert_not_called()
        send_haros_patch.assert_not_called()

        # cible = MV : ok
        cible.statut = bdd.Statut.MV
        cible.update()

        ctx = mock_discord.get_ctx(haro, cible="Joueur2", _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message(".")),
                ("yes_no", False)):
            await ctx.invoke()

        ctx.assert_sent("quelle est la raison", "", "")
        self.assertFalse(bdd.CandidHaro.query.all())    # no haro created
        send_debats_patch.assert_not_called()
        send_haros_patch.assert_not_called()

        # ok, and abort
        cible.statut = bdd.Statut.vivant
        cible.update()

        ctx = mock_discord.get_ctx(haro, cible="Joueur2", _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("pakontan")),
                ("yes_no", False)):
            # give reason then abort (answer "no" at check)
            await ctx.invoke()
        ctx.assert_sent("quelle est la raison",
                        "tout bon ?",
                        "Mission aborted")
        embed = ctx.send.call_args_list[1].kwargs["embed"]
        self.assertIn("contre Joueur2", embed.title)
        self.assertIn("pakontan", embed.description)
        self.assertIn("Joueur1", embed.author.name)
        self.assertFalse(bdd.CandidHaro.query.all())    # no haro created
        send_debats_patch.assert_not_called()
        send_haros_patch.assert_not_called()

        # validate
        ctx = mock_discord.get_ctx(haro, cible="Joueur2", _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("pakontan")),
                ("yes_no", True)):
            # give reason then abort (answer "no" at check)
            await ctx.invoke()
        ctx.assert_sent("quelle est la raison",
                        "tout bon ?",
                        "c'est parti")
        embed = ctx.send.call_args_list[1].kwargs["embed"]
        haros = bdd.CandidHaro.query.all()
        self.assertEqual(len(haros), 2)    # 2 haros created
        self.assertEqual({haro.joueur for haro in haros}, {joueur, cible})
        self.assertEqual(haros[0].type, bdd.CandidHaroType.haro)
        self.assertEqual(haros[1].type, bdd.CandidHaroType.haro)
        send_haros_patch.assert_called_once()
        self.assertEqual(send_haros_patch.call_args.kwargs, {"embed": embed})
        send_haros_patch.reset_mock()
        send_debats_patch.assert_called_once()
        send_debats_patch.reset_mock()

        # validate, but haroted already registered
        bdd.CandidHaro.delete(*haros)
        self.assertFalse(bdd.CandidHaro.query.all())    # no haros
        bdd.CandidHaro(joueur=cible, type=bdd.CandidHaroType.haro).add()
        ctx = mock_discord.get_ctx(haro, cible="Joueur2", _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("pakontan")),
                ("yes_no", True)):
            # give reason then abort (answer "no" at check)
            await ctx.invoke()
        ctx.assert_sent("", "", "")
        haros = bdd.CandidHaro.query.all()
        self.assertEqual(len(haros), 2)    # 2 haros created
        self.assertEqual({haro.joueur for haro in haros}, {joueur, cible})
        self.assertEqual(haros[0].type, bdd.CandidHaroType.haro)
        self.assertEqual(haros[1].type, bdd.CandidHaroType.haro)
        send_haros_patch.assert_called_once()
        send_haros_patch.reset_mock()
        send_debats_patch.assert_called_once()
        send_debats_patch.reset_mock()

        # validate, but haroter already registered
        bdd.CandidHaro.delete(*haros)
        self.assertFalse(bdd.CandidHaro.query.all())    # no haros
        bdd.CandidHaro(joueur=joueur, type=bdd.CandidHaroType.haro).add()
        ctx = mock_discord.get_ctx(haro, cible="Joueur2", _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("pakontan")),
                ("yes_no", True)):
            # give reason then abort (answer "no" at check)
            await ctx.invoke()
        ctx.assert_sent("", "", "")
        haros = bdd.CandidHaro.query.all()
        self.assertEqual(len(haros), 2)    # 2 haros created
        self.assertEqual({haro.joueur for haro in haros}, {joueur, cible})
        self.assertEqual(haros[0].type, bdd.CandidHaroType.haro)
        self.assertEqual(haros[1].type, bdd.CandidHaroType.haro)
        send_haros_patch.assert_called_once()
        send_haros_patch.reset_mock()
        send_debats_patch.assert_called_once()
        send_debats_patch.reset_mock()

        # validate, but haroter and haroted already registered
        bdd.CandidHaro.delete(*haros)
        self.assertFalse(bdd.CandidHaro.query.all())    # no haros
        bdd.CandidHaro(joueur=joueur, type=bdd.CandidHaroType.haro).add()
        bdd.CandidHaro(joueur=cible, type=bdd.CandidHaroType.haro).add()
        ctx = mock_discord.get_ctx(haro, cible="Joueur2", _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("pakontan")),
                ("yes_no", True)):
            # give reason then abort (answer "no" at check)
            await ctx.invoke()
        ctx.assert_sent("", "", "")
        haros = bdd.CandidHaro.query.all()
        self.assertEqual(len(haros), 2)    # 2 haros created
        self.assertEqual({haro.joueur for haro in haros}, {joueur, cible})
        self.assertEqual(haros[0].type, bdd.CandidHaroType.haro)
        self.assertEqual(haros[1].type, bdd.CandidHaroType.haro)
        send_haros_patch.assert_called_once()
        send_haros_patch.reset_mock()
        send_debats_patch.assert_called_once()
        send_debats_patch.reset_mock()



    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.config.Channel.haros.send")
    @mock.patch("lgrez.config.Channel.debats.send")
    @mock_discord.interact()
    async def test_candid(self, send_debats_patch, send_candids_patch):
        """Unit tests for !candid command."""
        # async def candid(self, ctx)
        candid = self.cog.candid
        mock_bdd.add_campsroles()
        joueur = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                            vote_maire_=None)
        joueur.add()

        # no vote
        ctx = mock_discord.get_ctx(candid, _caller_id=1)
        await ctx.invoke()
        ctx.assert_sent("Pas de vote")
        self.assertFalse(bdd.CandidHaro.query.all())    # no candid created
        send_debats_patch.assert_not_called()
        send_candids_patch.assert_not_called()

        # joueur already candidated
        joueur.vote_maire_ = "bzzzt"
        cand = bdd.CandidHaro(joueur=joueur,
                                type=bdd.CandidHaroType.candidature)
        cand.add()
        ctx = mock_discord.get_ctx(candid, _caller_id=1)
        await ctx.invoke()
        ctx.assert_sent("déjà présenté")
        self.assertEqual(len(bdd.CandidHaro.query.all()), 1)    # none created
        send_debats_patch.assert_not_called()
        send_candids_patch.assert_not_called()

        # ok, and abort
        cand.delete()
        ctx = mock_discord.get_ctx(candid, _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("votépourmoi")),
                ("yes_no", False)):
            # give reason then abort (answer "no" at check)
            await ctx.invoke()
        ctx.assert_sent("Quel est ton programme",
                        "tout bon ?",
                        "Mission aborted")
        embed = ctx.send.call_args_list[1].kwargs["embed"]
        self.assertIn("Joueur1", embed.title)
        self.assertIn("votépourmoi", embed.description)
        self.assertIn("Joueur1", embed.author.name)
        self.assertFalse(bdd.CandidHaro.query.all())    # no candid created
        send_debats_patch.assert_not_called()
        send_candids_patch.assert_not_called()

        # validate
        ctx = mock_discord.get_ctx(candid, _caller_id=1)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("votépourmoi")),
                ("yes_no", True)):
            # give reason then abort (answer "no" at check)
            await ctx.invoke()
        ctx.assert_sent("Quel est ton programme",
                        "tout bon ?",
                        "c'est parti")
        embed = ctx.send.call_args_list[1].kwargs["embed"]
        candids = bdd.CandidHaro.query.all()
        self.assertEqual(len(candids), 1)    # 2 candids created
        self.assertEqual(candids[0].joueur, joueur)
        self.assertEqual(candids[0].type, bdd.CandidHaroType.candidature)
        send_candids_patch.assert_called_once()
        self.assertEqual(send_candids_patch.call_args.kwargs, {"embed": embed})
        send_candids_patch.reset_mock()
        send_debats_patch.assert_called_once()
        send_debats_patch.reset_mock()
