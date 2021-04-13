import datetime
import unittest
from unittest import mock

from lgrez import config, bdd
from lgrez.features import open_close
from test import mock_discord, mock_bdd, mock_env


class TestOpenCloseFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.open_close utility functions."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    @unittest.SkipTest
    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.gestion_actions.get_actions")
    async def test_recup_joueurs(self, getact_patch):
        """Unit tests for open_close.recup_joueurs function."""
        # async def recup_joueurs(quoi, qui, heure=None)
        recup_joueurs = open_close.recup_joueurs
        mock_bdd.add_campsroles()
        i = 0
        joueurs = []
        for vote_condamne_ in [None, "non défini", "oh"]:
            for vote_maire_ in [None, "non défini", "ah"]:
                for vote_loups_ in [None, "non défini", "eh"]:
                    for votant_village in [True, False]:
                        for votant_loups in [True, False]:
                            for role_actif in [True, False]:
                                j = bdd.Joueur(
                                    discord_id=i, chan_id_=i,
                                    nom=f"Joueur{i}",
                                    vote_condamne_=vote_condamne_,
                                    vote_maire_=vote_maire_,
                                    vote_loups_=vote_loups_,
                                    votant_village=votant_village,
                                    votant_loups=votant_loups,
                                    role_actif=role_actif
                                )
                                joueurs.append(j)
                                i += 1
        bdd.Joueur.add(*joueurs)

        # bad quoi
        with self.assertRaises(ValueError):
            await recup_joueurs("bloup", "cond")
        getact_patch.assert_not_called()

        # bad qui
        with self.assertRaises(ValueError):
            await recup_joueurs("open", "bzzt")
        getact_patch.assert_not_called()
        with self.assertRaises(ValueError):
            await recup_joueurs("open", "19")     # non-existing action
        getact_patch.assert_not_called()

        # qui = "cond"
        results = await recup_joueurs("open", "cond")
        getact_patch.assert_not_called()
        for joueur in joueurs:
            if joueur.votant_village and joueur.vote_condamne_ is None:
                self.assertIn(joueur, results)
            else:
                self.assertNotIn(joueur, results)

        results = await recup_joueurs("remind", "cond")
        getact_patch.assert_not_called()
        for joueur in joueurs:
            if joueur.vote_condamne_ == "non défini":
                self.assertIn(joueur, results)
            else:
                self.assertNotIn(joueur, results)

        results = await recup_joueurs("close", "cond")
        getact_patch.assert_not_called()
        for joueur in joueurs:
            if joueur.vote_condamne_ is not None:
                self.assertIn(joueur, results)
            else:
                self.assertNotIn(joueur, results)

        # qui = "maire"
        results = await recup_joueurs("open", "maire")
        getact_patch.assert_not_called()
        for joueur in joueurs:
            if joueur.votant_village and joueur.vote_maire_ is None:
                self.assertIn(joueur, results)
            else:
                self.assertNotIn(joueur, results)

        results = await recup_joueurs("remind", "maire")
        getact_patch.assert_not_called()
        for joueur in joueurs:
            if joueur.vote_maire_ == "non défini":
                self.assertIn(joueur, results)
            else:
                self.assertNotIn(joueur, results)

        results = await recup_joueurs("close", "maire")
        getact_patch.assert_not_called()
        for joueur in joueurs:
            if joueur.vote_maire_ is not None:
                self.assertIn(joueur, results)
            else:
                self.assertNotIn(joueur, results)

        # qui = "loups"
        results = await recup_joueurs("open", "loups")
        getact_patch.assert_not_called()
        for joueur in joueurs:
            if joueur.votant_loups and joueur.vote_loups_ is None:
                self.assertIn(joueur, results)
            else:
                self.assertNotIn(joueur, results)

        results = await recup_joueurs("remind", "loups")
        getact_patch.assert_not_called()
        for joueur in joueurs:
            if joueur.vote_loups_ == "non défini":
                self.assertIn(joueur, results)
            else:
                self.assertNotIn(joueur, results)

        results = await recup_joueurs("close", "loups")
        getact_patch.assert_not_called()
        for joueur in joueurs:
            if joueur.vote_loups_ is not None:
                self.assertIn(joueur, results)
            else:
                self.assertNotIn(joueur, results)

        # qui = "action"
        with self.assertRaises(ValueError):
            await recup_joueurs("open", "action")
        getact_patch.assert_not_called()

        with self.assertRaises(ValueError):
            await recup_joueurs("open", "action", 15)
        getact_patch.assert_not_called()

        bdd.BaseAction(slug="ouiZ").add()
        bdd.BaseAction(slug="nonZ").add()
        bdd.BaseAction(slug="lalaZ").add()
        action1 = bdd.Action(id=1, joueur=joueurs[0], _base_slug="ouiZ")
        action2 = bdd.Action(id=23, joueur=joueurs[0], _base_slug="nonZ")
        action3 = bdd.Action(id=72, joueur=joueurs[1], _base_slug="lalaZ")
        bdd.Action.add(action1, action2, action3)

        getact_patch.return_value = [action1, action2, action3]
        results = await recup_joueurs("open", "action", "15h23")
        self.assertEqual(results, {joueurs[0]: [action1, action2],
                                   joueurs[1]: [action3]})
        getact_patch.assert_called_once_with(
            "open", bdd.ActionTrigger.temporel, datetime.time(15, 23)
        )
        getact_patch.reset_mock()

        results = await recup_joueurs("close", "action", "7h")
        self.assertEqual(results, {joueurs[0]: [action1, action2],
                                   joueurs[1]: [action3]})
        getact_patch.assert_called_once_with(
            "close", bdd.ActionTrigger.temporel, datetime.time(7, 0)
        )
        getact_patch.reset_mock()

        results = await recup_joueurs("remind", "action", "23h12")
        self.assertEqual(results, {joueurs[0]: [action1, action2],
                                   joueurs[1]: [action3]})
        getact_patch.assert_called_once_with(
            "remind", bdd.ActionTrigger.temporel, datetime.time(23, 12)
        )
        getact_patch.reset_mock()

        # qui = id
        with self.assertRaises(ValueError):
            await recup_joueurs("open", "3")    # Non-existing action
        getact_patch.assert_not_called()

        action3.decision_ = None
        action3.base.trigger_debut = bdd.ActionTrigger.perma
        action3.update()
        results = await recup_joueurs("open", "72")
        self.assertEqual(results, {joueurs[1]: [action3]})
        getact_patch.assert_not_called()

        action3.decision_ = "blabla"
        action3.update()
        results = await recup_joueurs("open", "72")
        self.assertEqual(results, {joueurs[1]: [action3]})
        getact_patch.assert_not_called()

        action3.decision_ = None
        action3.base.trigger_debut = bdd.ActionTrigger.mot_mjs
        action3.update()
        results = await recup_joueurs("open", "72")
        self.assertEqual(results, {joueurs[1]: [action3]})
        getact_patch.assert_not_called()

        action3.decision_ = "blabla"
        action3.update()
        results = await recup_joueurs("open", "72")
        self.assertEqual(results, {})
        getact_patch.assert_not_called()

        results = await recup_joueurs("remind", "72")
        self.assertEqual(results, {})
        getact_patch.assert_not_called()

        action3.decision_ = "rien"
        action3.update()
        results = await recup_joueurs("remind", "72")
        self.assertEqual(results, {joueurs[1]: [action3]})
        getact_patch.assert_not_called()

        results = await recup_joueurs("close", "72")
        self.assertEqual(results, {joueurs[1]: [action3]})
        getact_patch.assert_not_called()

        action3.decision_ = "blabla"
        action3.update()
        results = await recup_joueurs("close", "72")
        self.assertEqual(results, {joueurs[1]: [action3]})
        getact_patch.assert_not_called()

        action3.decision_ = None
        action3.update()
        results = await recup_joueurs("close", "72")
        self.assertEqual(results, {})
        getact_patch.assert_not_called()


    @mock_bdd.patch_db      # Empty database for this method
    async def test__do_refill(self):
        """Unit tests for open_close._do_refill function."""
        # async def _do_refill(motif, actions)
        _do_refill = open_close._do_refill

        config.refills_full = ["uikz"]
        config.refills_one = ["forgebonk", "rebootax", "divvvvvvin"]
        config.refills_divins = ["divvvvvvin"]

        mock_bdd.add_campsroles()
        joueur1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1")
        joueur2 = bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2")
        joueurs = [joueur1, joueur2]
        bdd.Joueur.add(*joueurs)
        actions = {}
        i = 0
        for kw in [*config.refills_full, *config.refills_one]:
            base = f"baz_{kw}"
            bdd.BaseAction(slug=base, refill=kw, base_charges=5 + i).add()
            i += 1
            actions[kw] = [
                bdd.Action(joueur=joueur1, _base_slug=base, charges=3),
                bdd.Action(joueur=joueur2, _base_slug=base, charges=3),
            ]
        action_none = bdd.Action(joueur=joueur1, _base_slug=base, charges=None)
        all_actions = {ac for acs in actions.values() for ac in acs}
        bdd.Action.add(*all_actions, action_none)

        # motif = full
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await _do_refill("uikz", list(all_actions))
        for action in all_actions:
            chan = chan1 if action.joueur == joueur1 else chan2
            sent = "\n".join(call.args[0] for call in chan.send.call_args_list)
            self.assertEqual(action.charges, action.base.base_charges)
            self.assertIn(str(action.base.slug), sent)
            self.assertIn(str(action.base.base_charges), sent)

        # motif = not full
        for action in all_actions:
            action.charges = 3
        config.session.commit()

        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await _do_refill("forgebonk", list(all_actions))
        for action in all_actions:
            chan = chan1 if action.joueur == joueur1 else chan2
            sent = "\n".join(call.args[0] for call in chan.send.call_args_list)
            self.assertEqual(action.charges, 4)
            self.assertIn(str(action.base.slug), sent)
            self.assertIn("4", sent)

        # motif = full, already full action
        bdd.BaseAction(slug="oui", base_charges=7).add()
        fa = bdd.Action(joueur=joueur1, _base_slug="oui", charges=7)
        fa.add()
        with mock_discord.mock_members_and_chans(joueur1):
            chan1 = joueur1.private_chan
            await _do_refill("uikz", [fa])
        self.assertEqual(fa.charges, 7)
        chan1.send.assert_not_called()

        # motif = not full, already full action
        with mock_discord.mock_members_and_chans(joueur1):
            chan1 = joueur1.private_chan
            await _do_refill("forgebonk", [fa])
        self.assertEqual(fa.charges, 8)
        chan1.send.assert_called_once()

        # perma action with no charges
        bdd.BaseAction(slug="non", trigger_debut=bdd.ActionTrigger.perma,
                       base_charges=7).add()
        pa = bdd.Action(id=13, joueur=joueur1, _base_slug="non", charges=0)
        pa.add()
        with mock_discord.mock_members_and_chans(joueur1):
            await _do_refill("forgebonk", [pa])
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 1)
        self.assertEqual(taches[0].commande, "!open 13")
        self.assertEqual(taches[0].action, pa)



@unittest.SkipTest
class TestOpenClose(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.open_close commands."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = open_close.OpenClose(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()

    @mock_bdd.patch_db      # Empty database for this method
    @mock_discord.interact()
    @mock.patch("lgrez.features.open_close.recup_joueurs")  # tested before
    @mock.patch("lgrez.features.gestion_actions.open_action")
    async def test_open(self, oa_patch, rj_patch):
        """Unit tests for !open command."""
        # async def open(self, ctx, qui, heure=None, heure_chain=None)
        open = self.cog.open
        mock_bdd.add_campsroles()
        joueur1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                             votant_village=True, votant_loups=True)
        joueur2 = bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2",
                             votant_village=True, votant_loups=True)
        joueur3 = bdd.Joueur(discord_id=3, chan_id_=31, nom="Joueur3")
        joueurs = [joueur1, joueur2, joueur3]
        bdd.Joueur.add(*joueurs)
        haros = [bdd.CandidHaro(joueur=joueur2, type=bdd.CandidHaroType.haro),
                 bdd.CandidHaro(joueur=joueur3, type=bdd.CandidHaroType.haro)]
        candids = [bdd.CandidHaro(joueur=joueur1,
                                  type=bdd.CandidHaroType.candidature),
                   bdd.CandidHaro(joueur=joueur3,
                                  type=bdd.CandidHaroType.candidature)]
        bdd.CandidHaro.add(*haros, *candids)
        bases = [bdd.BaseAction(slug=trigger.name, trigger_debut=trigger)
                 for trigger in bdd.ActionTrigger]
        ac_oc = [bdd.Action(joueur=joueur1, base=base)
                 for joueur in joueurs for base in bases]


        # bad qui
        ctx = mock_discord.get_ctx(open, "bzeepzopsl")
        rj_patch.side_effect = ValueError
        with self.assertRaises(ValueError):
            await ctx.invoke()
        rj_patch.assert_called_once_with("open", "bzeepzopsl", None)
        rj_patch.reset_mock(side_effect=True)
        oa_patch.assert_not_called()

        # qui = "cond", heure = None, heure_chain = None
        ctx = mock_discord.get_ctx(open, "cond")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("open", "cond", None)
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Ouverture vote
        self.assertEqual(joueur1.vote_condamne_, "non défini")
        self.assertEqual(joueur2.vote_condamne_, "non défini")
        self.assertIsNone(joueur3.vote_condamne_)
        # Information joueurs
        chan1.send.assert_called_once()
        self.assertIn("vote pour le condamné du jour est ouvert",
                      chan1.send.call_args.args[0])
        (await chan1.send()).add_reaction.assert_called_once_with(
            config.Emoji.bucher)
        chan2.send.assert_called_once()
        self.assertIn("vote pour le condamné du jour est ouvert",
                      chan2.send.call_args.args[0])
        (await chan2.send()).add_reaction.assert_called_once_with(
            config.Emoji.bucher)
        # Ouverture open_cond actions
        self.assertEqual(oa_patch.call_count, 3)
        self.assertEqual(
            [ac for ac in ac_oc
             if ac.base.trigger_debut == bdd.ActionTrigger.open_cond],
            [call.args[0] for call in oa_patch.call_args_list])
        oa_patch.reset_mock()
        # Réinitialisation haros
        self.assertFalse(bdd.CandidHaro.query.filter_by(
            type=bdd.CandidHaroType.haro
        ).all())
        self.assertEqual(bdd.CandidHaro.query.filter_by(
            type=bdd.CandidHaroType.candidature
        ).all(), candids)
        config.Channel.haros.send.assert_called_once
        self.assertIn("Nouveau vote",
                      config.Channel.haros.send.call_args.args[0])
        config.Channel.haros.send.reset_mock()
        # heure / heure_chain
        self.assertFalse(bdd.Tache.query.all())

        # qui = "cond", heure = 15h12, heure_chain = None
        ctx = mock_discord.get_ctx(open, "cond", heure="15h12")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        oa_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 2)
        self.assertEqual({tache.commande for tache in taches},
                         {"!remind cond", "!close cond"})
        bdd.Tache.delete(*taches)

        # qui = "cond", heure = 15h12, heure_chain = 7h
        ctx = mock_discord.get_ctx(open, "cond", heure="15h12",
                                   heure_chain="7h")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        oa_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 2)
        self.assertEqual({tache.commande for tache in taches},
                         {"!remind cond", "!close cond 7h 15h12"})
        bdd.Tache.delete(*taches)

        # ---- maire ----
        bdd.CandidHaro.delete(*haros, *candids)
        haros = [bdd.CandidHaro(joueur=joueur2, type=bdd.CandidHaroType.haro),
                 bdd.CandidHaro(joueur=joueur3, type=bdd.CandidHaroType.haro)]
        candids = [bdd.CandidHaro(joueur=joueur1,
                                  type=bdd.CandidHaroType.candidature),
                   bdd.CandidHaro(joueur=joueur3,
                                  type=bdd.CandidHaroType.candidature)]
        bdd.CandidHaro.add(*haros, *candids)

        # qui = "maire", heure = None, heure_chain = None
        ctx = mock_discord.get_ctx(open, "maire")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("open", "maire", None)
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Ouverture vote
        self.assertEqual(joueur1.vote_maire_, "non défini")
        self.assertEqual(joueur2.vote_maire_, "non défini")
        self.assertIsNone(joueur3.vote_maire_)
        # Information joueurs
        chan1.send.assert_called_once()
        self.assertIn("vote pour l'élection du maire est ouvert",
                      chan1.send.call_args.args[0])
        (await chan1.send()).add_reaction.assert_called_once_with(
            config.Emoji.maire)
        chan2.send.assert_called_once()
        self.assertIn("vote pour l'élection du maire est ouvert",
                      chan2.send.call_args.args[0])
        (await chan2.send()).add_reaction.assert_called_once_with(
            config.Emoji.maire)
        # Ouverture open_maire actions
        self.assertEqual(oa_patch.call_count, 3)
        self.assertEqual(
            [ac for ac in ac_oc
             if ac.base.trigger_debut == bdd.ActionTrigger.open_maire],
            [call.args[0] for call in oa_patch.call_args_list])
        oa_patch.reset_mock()
        # Réinitialisation haros
        self.assertFalse(bdd.CandidHaro.query.filter_by(
            type=bdd.CandidHaroType.candidature
        ).all())
        self.assertEqual(bdd.CandidHaro.query.filter_by(
            type=bdd.CandidHaroType.haro
        ).all(), haros)
        config.Channel.haros.send.assert_called_once
        self.assertIn("Nouveau vote",
                      config.Channel.haros.send.call_args.args[0])
        config.Channel.haros.send.reset_mock()
        # heure / heure_chain
        self.assertFalse(bdd.Tache.query.all())

        # qui = "maire", heure = 15h12, heure_chain = None
        ctx = mock_discord.get_ctx(open, "maire", heure="15h12")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        oa_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 2)
        self.assertEqual({tache.commande for tache in taches},
                         {"!remind maire", "!close maire"})
        bdd.Tache.delete(*taches)

        # qui = "maire", heure = 15h12, heure_chain = 7h
        ctx = mock_discord.get_ctx(open, "maire", heure="15h12",
                                   heure_chain="7h")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        oa_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 2)
        self.assertEqual({tache.commande for tache in taches},
                         {"!remind maire", "!close maire 7h 15h12"})
        bdd.Tache.delete(*taches)

        # ---- loups ----
        bdd.CandidHaro.delete(*haros, *candids)
        haros = [bdd.CandidHaro(joueur=joueur2, type=bdd.CandidHaroType.haro),
                 bdd.CandidHaro(joueur=joueur3, type=bdd.CandidHaroType.haro)]
        candids = [bdd.CandidHaro(joueur=joueur1,
                                  type=bdd.CandidHaroType.candidature),
                   bdd.CandidHaro(joueur=joueur3,
                                  type=bdd.CandidHaroType.candidature)]
        bdd.CandidHaro.add(*haros, *candids)

        # qui = "loups", heure = None, heure_chain = None
        ctx = mock_discord.get_ctx(open, "loups")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("open", "loups", None)
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Ouverture vote
        self.assertEqual(joueur1.vote_loups_, "non défini")
        self.assertEqual(joueur2.vote_loups_, "non défini")
        self.assertIsNone(joueur3.vote_loups_)
        # Information joueurs
        chan1.send.assert_called_once()
        self.assertIn("vote pour la victime de cette nuit est ouvert",
                      chan1.send.call_args.args[0])
        (await chan1.send()).add_reaction.assert_called_once_with(
            config.Emoji.lune)
        chan2.send.assert_called_once()
        self.assertIn("vote pour la victime de cette nuit est ouvert",
                      chan2.send.call_args.args[0])
        (await chan2.send()).add_reaction.assert_called_once_with(
            config.Emoji.lune)
        # Ouverture open_loups actions
        self.assertEqual(oa_patch.call_count, 3)
        self.assertEqual(
            [ac for ac in ac_oc
             if ac.base.trigger_debut == bdd.ActionTrigger.open_loups],
            [call.args[0] for call in oa_patch.call_args_list])
        oa_patch.reset_mock()
        # Non-réinitialisation haros
        self.assertEqual(len(bdd.CandidHaro.query.all()), 4)
        config.Channel.haros.send.assert_not_called()
        # heure / heure_chain
        self.assertFalse(bdd.Tache.query.all())

        # qui = "loups", heure = 15h12, heure_chain = None
        ctx = mock_discord.get_ctx(open, "loups", heure="15h12")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        oa_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 2)
        self.assertEqual({tache.commande for tache in taches},
                         {"!remind loups", "!close loups"})
        bdd.Tache.delete(*taches)

        # qui = "loups", heure = 15h12, heure_chain = 7h
        ctx = mock_discord.get_ctx(open, "loups", heure="15h12",
                                   heure_chain="7h")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        oa_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 2)
        self.assertEqual({tache.commande for tache in taches},
                         {"!remind loups", "!close loups 7h 15h12"})

        # ---- action ----
        bdd.BaseAction(slug="ouiz", trigger_debut=bdd.ActionTrigger.temporel,
                       heure_debut=datetime.time(15, 12)).add()
        action1 = bdd.Action(_base_slug="ouiz", joueur=joueur1)
        action2 = bdd.Action(_base_slug="ouiz", joueur=joueur1)
        action3 = bdd.Action(_base_slug="ouiz", joueur=joueur2)
        bdd.Action.add(action1, action2, action3)

        # qui = "action", heure = "15h12"
        ctx = mock_discord.get_ctx(open, "action", "15h12")
        rj_patch.return_value = {joueur1: [action1, action2],
                                 joueur2: [action3]}
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("open", "action", "15h12")
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Ouverture actions
        self.assertEqual(oa_patch.call_count, 3)
        self.assertEqual(
            [action1, action2, action3],
            [call.args[0] for call in oa_patch.call_args_list])
        oa_patch.reset_mock()


    @mock_bdd.patch_db      # Empty database for this method
    @mock_discord.interact()
    @mock.patch("lgrez.features.open_close.recup_joueurs")  # tested before
    @mock.patch("lgrez.features.gestion_actions.close_action")
    async def test_close(self, ca_patch, rj_patch):
        """Unit tests for !close command."""
        # async def close(self, ctx, qui, heure=None, heure_chain=None)
        close = self.cog.close
        mock_bdd.add_campsroles()
        joueur1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                             votant_village=True, votant_loups=True,
                             vote_condamne_="zeret", vote_maire_="goo",
                             vote_loups_="kowwwia")
        joueur2 = bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2",
                             votant_village=True, votant_loups=True,
                             vote_condamne_="zeret", vote_maire_="goo",
                             vote_loups_="kowwwia")
        joueur3 = bdd.Joueur(discord_id=3, chan_id_=31, nom="Joueur3",
                             vote_condamne_="zeret", vote_maire_="goo",
                             vote_loups_="kowwwia")
        joueurs = [joueur1, joueur2, joueur3]
        bdd.Joueur.add(*joueurs)
        bases = [bdd.BaseAction(slug=trigger.name, trigger_debut=trigger)
                 for trigger in bdd.ActionTrigger]
        ac_oc = [bdd.Action(joueur=joueur1, base=base)
                 for joueur in joueurs for base in bases]

        # bad qui
        ctx = mock_discord.get_ctx(close, "bzeepzopsl")
        rj_patch.side_effect = ValueError
        with self.assertRaises(ValueError):
            await ctx.invoke()
        rj_patch.assert_called_once_with("close", "bzeepzopsl", None)
        rj_patch.reset_mock(side_effect=True)
        ca_patch.assert_not_called()

        # qui = "cond", heure = None, heure_chain = None
        ctx = mock_discord.get_ctx(close, "cond")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("close", "cond", None)
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Fermeture vote
        self.assertIsNone(joueur1.vote_condamne_)
        self.assertIsNone(joueur2.vote_condamne_)
        self.assertEqual(joueur3.vote_condamne_, "zeret")
        # Information joueurs
        chan1.send.assert_called_once()
        self.assertIn("Fin du vote pour le condamné",
                      chan1.send.call_args.args[0])
        chan2.send.assert_called_once()
        self.assertIn("Fin du vote pour le condamné",
                      chan2.send.call_args.args[0])
        # Fermeture close_cond actions
        self.assertEqual(ca_patch.call_count, 3)
        self.assertEqual(
            [ac for ac in ac_oc
             if ac.base.trigger_debut == bdd.ActionTrigger.close_cond],
            [call.args[0] for call in ca_patch.call_args_list])
        ca_patch.reset_mock()
        # heure / heure_chain
        self.assertFalse(bdd.Tache.query.all())

        # qui = "cond", heure = 15h12, heure_chain = None
        ctx = mock_discord.get_ctx(close, "cond", heure="15h12")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        ca_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 1)
        self.assertEqual(taches[0].commande, "!open cond")
        bdd.Tache.delete(*taches)

        # qui = "cond", heure = 15h12, heure_chain = 7h
        ctx = mock_discord.get_ctx(close, "cond", heure="15h12",
                                   heure_chain="7h")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        ca_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 1)
        self.assertEqual(taches[0].commande, "!open cond 7h 15h12")
        bdd.Tache.delete(*taches)

        # ---- maire ----
        # qui = "maire", heure = None, heure_chain = None
        ctx = mock_discord.get_ctx(close, "maire")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("close", "maire", None)
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Fermeture vote
        self.assertIsNone(joueur1.vote_maire_)
        self.assertIsNone(joueur2.vote_maire_)
        self.assertEqual(joueur3.vote_maire_, "goo")
        # Information joueurs
        chan1.send.assert_called_once()
        self.assertIn("Fin du vote pour le maire",
                      chan1.send.call_args.args[0])
        chan2.send.assert_called_once()
        self.assertIn("Fin du vote pour le maire",
                      chan2.send.call_args.args[0])
        # Fermeture close_maire actions
        self.assertEqual(ca_patch.call_count, 3)
        self.assertEqual(
            [ac for ac in ac_oc
             if ac.base.trigger_debut == bdd.ActionTrigger.close_maire],
            [call.args[0] for call in ca_patch.call_args_list])
        ca_patch.reset_mock()
        # heure / heure_chain
        self.assertFalse(bdd.Tache.query.all())

        # qui = "maire", heure = 15h12, heure_chain = None
        ctx = mock_discord.get_ctx(close, "maire", heure="15h12")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        ca_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 1)
        self.assertEqual(taches[0].commande, "!open maire")
        bdd.Tache.delete(*taches)

        # qui = "maire", heure = 15h12, heure_chain = 7h
        ctx = mock_discord.get_ctx(close, "maire", heure="15h12",
                                   heure_chain="7h")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        ca_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 1)
        self.assertEqual(taches[0].commande, "!open maire 7h 15h12")
        bdd.Tache.delete(*taches)

        # ---- loups ----
        # qui = "loups", heure = None, heure_chain = None
        ctx = mock_discord.get_ctx(close, "loups")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("close", "loups", None)
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Fermeture vote
        self.assertIsNone(joueur1.vote_loups_)
        self.assertIsNone(joueur2.vote_loups_)
        self.assertEqual(joueur3.vote_loups_, "kowwwia")
        # Information joueurs
        chan1.send.assert_called_once()
        self.assertIn("Fin du vote pour la victime",
                      chan1.send.call_args.args[0])
        chan2.send.assert_called_once()
        self.assertIn("Fin du vote pour la victime",
                      chan2.send.call_args.args[0])
        # Fermeture close_loups actions
        self.assertEqual(ca_patch.call_count, 3)
        self.assertEqual(
            [ac for ac in ac_oc
             if ac.base.trigger_debut == bdd.ActionTrigger.close_loups],
            [call.args[0] for call in ca_patch.call_args_list])
        ca_patch.reset_mock()
        # heure / heure_chain
        self.assertFalse(bdd.Tache.query.all())

        # qui = "loups", heure = 15h12, heure_chain = None
        ctx = mock_discord.get_ctx(close, "loups", heure="15h12")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        ca_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 1)
        self.assertEqual(taches[0].commande, "!open loups")
        bdd.Tache.delete(*taches)

        # qui = "loups", heure = 15h12, heure_chain = 7h
        ctx = mock_discord.get_ctx(close, "loups", heure="15h12",
                                   heure_chain="7h")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.reset_mock(return_value=True)
        ca_patch.reset_mock()
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 1)
        self.assertEqual(taches[0].commande, "!open loups 7h 15h12")
        bdd.Tache.delete(*taches)

        # ---- action ----
        bdd.BaseAction(slug="ouiz", trigger_debut=bdd.ActionTrigger.temporel,
                       heure_debut=datetime.time(15, 12)).add()
        action1 = bdd.Action(_base_slug="ouiz", joueur=joueur1)
        action2 = bdd.Action(_base_slug="ouiz", joueur=joueur1)
        action3 = bdd.Action(_base_slug="ouiz", joueur=joueur2)
        bdd.Action.add(action1, action2, action3)

        # qui = "action", heure = "15h12"
        ctx = mock_discord.get_ctx(close, "action", "15h12")
        rj_patch.return_value = {joueur1: [action1, action2],
                                 joueur2: [action3]}
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("close", "action", "15h12")
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Fermeture actions
        self.assertEqual(ca_patch.call_count, 3)
        self.assertEqual(
            [action1, action2, action3],
            [call.args[0] for call in ca_patch.call_args_list])
        ca_patch.reset_mock()


    @mock_bdd.patch_db      # Empty database for this method
    @mock_discord.interact()
    @mock.patch("lgrez.features.open_close.recup_joueurs")  # tested before
    async def test_remind(self, rj_patch):
        """Unit tests for !remind command."""
        # async def remind(self, ctx, qui, heure=None)
        remind = self.cog.remind
        mock_bdd.add_campsroles()
        joueur1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                             votant_village=True, votant_loups=True,
                             vote_condamne_="non défini", vote_maire_="non défini",
                             vote_loups_="non défini")
        joueur2 = bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2",
                             votant_village=True, votant_loups=True,
                             vote_condamne_="non défini", vote_maire_="non défini",
                             vote_loups_="non défini")
        joueur3 = bdd.Joueur(discord_id=3, chan_id_=31, nom="Joueur3")
        joueurs = [joueur1, joueur2, joueur3]
        bdd.Joueur.add(*joueurs)
        bases = [bdd.BaseAction(slug=trigger.name, trigger_debut=trigger)
                 for trigger in bdd.ActionTrigger]
        ac_oc = [bdd.Action(joueur=joueur1, base=base)
                 for joueur in joueurs for base in bases]

        # bad qui
        ctx = mock_discord.get_ctx(remind, "bzeepzopsl")
        rj_patch.side_effect = ValueError
        with self.assertRaises(ValueError):
            await ctx.invoke()
        rj_patch.assert_called_once_with("remind", "bzeepzopsl", None)
        rj_patch.reset_mock(side_effect=True)

        # qui = "cond", heure = None
        ctx = mock_discord.get_ctx(remind, "cond")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("remind", "cond", None)
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Information joueurs
        chan1.send.assert_called_once()
        self.assertIn("pour voter pour le condamné",
                      chan1.send.call_args.args[0])
        chan2.send.assert_called_once()
        self.assertIn("pour voter pour le condamné",
                      chan2.send.call_args.args[0])

        # ---- maire ----
        # qui = "maire", heure = None
        ctx = mock_discord.get_ctx(remind, "maire")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("remind", "maire", None)
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Information joueurs
        chan1.send.assert_called_once()
        self.assertIn("pour élire le nouveau maire",
                      chan1.send.call_args.args[0])
        chan2.send.assert_called_once()
        self.assertIn("pour élire le nouveau maire",
                      chan2.send.call_args.args[0])

        # ---- loups ----
        # qui = "loups", heure = None
        ctx = mock_discord.get_ctx(remind, "loups")
        rj_patch.return_value = [joueur1, joueur2]
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("remind", "loups", None)
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Information joueurs
        chan1.send.assert_called_once()
        self.assertIn("pour voter pour la victime",
                      chan1.send.call_args.args[0])
        chan2.send.assert_called_once()
        self.assertIn("pour voter pour la victime",
                      chan2.send.call_args.args[0])

        # ---- action ----
        bdd.BaseAction(slug="ouiz", trigger_debut=bdd.ActionTrigger.temporel,
                       heure_debut=datetime.time(15, 12)).add()
        action1 = bdd.Action(_base_slug="ouiz", joueur=joueur1)
        action2 = bdd.Action(_base_slug="ouiz", joueur=joueur1)
        action3 = bdd.Action(_base_slug="ouiz", joueur=joueur2)
        bdd.Action.add(action1, action2, action3)

        # qui = "action", heure = "15h12"
        ctx = mock_discord.get_ctx(remind, "action", "15h12")
        rj_patch.return_value = {joueur1: [action1, action2],
                                 joueur2: [action3]}
        with mock_discord.mock_members_and_chans(joueur1, joueur2):
            chan1, chan2 = joueur1.private_chan, joueur2.private_chan
            await ctx.invoke()
        rj_patch.assert_called_once_with("remind", "action", "15h12")
        rj_patch.reset_mock(return_value=True)
        # Liste joueurs concernés
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        # Information joueurs
        self.assertEqual(chan1.send.call_count, 2)
        self.assertIn("pour utiliser ton action",
                      chan1.send.call_args.args[0])
        chan2.send.assert_called_once()
        self.assertIn("pour utiliser ton action",
                      chan2.send.call_args.args[0])


    @mock_bdd.patch_db      # Empty database for this method
    @mock_discord.interact()
    @mock.patch("lgrez.features.open_close._do_refill")  # tested before
    async def test_refill(self, dr_patch):
        """Unit tests for !refill command."""
        # async def refill(self, ctx, motif, *, cible=None)
        refill = self.cog.refill

        config.refills_full = ["uikz"]
        config.refills_one = ["forgebonk", "rebootax", "divvvvvvin"]
        config.refills_divins = ["divvvvvvin"]

        mock_bdd.add_campsroles()
        joueur1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1")
        joueur2 = bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2")
        joueurs = [joueur1, joueur2]
        bdd.Joueur.add(*joueurs)
        nondivin = set(config.refills_full
                       + config.refills_one) ^ set(config.refills_divins)
        bdd.BaseAction(slug="baz_all", refill=", ".join(nondivin)).add()
        act_all_refs = bdd.Action(joueur=joueur1, _base_slug="baz_all",
                                  charges=3)
        actions = {}
        for kw in [*config.refills_full, *config.refills_one]:
            base = f"baz_{kw}"
            bdd.BaseAction(slug=base, refill=kw).add()
            actions[kw] = [
                bdd.Action(joueur=joueur1, _base_slug=base, charges=3),
                bdd.Action(joueur=joueur2, _base_slug=base, charges=3),
                act_all_refs,
            ]
        action_none = bdd.Action(joueur=joueur1, _base_slug=base, charges=None)
        all_actions = {ac for acs in actions.values() for ac in acs}
        bdd.Action.add(*all_actions, action_none)

        # bad motif
        ctx = mock_discord.get_ctx(refill, "bzeepzopsl")
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("pas un motif valide", ctx.send.call_args.args[0])
        dr_patch.assert_not_called()

        # motif = divin, cible = "all", abort
        ctx = mock_discord.get_ctx(refill, "divvvvvvin", cible="all")
        with mock_discord.interact(("yes_no", False)):
            await ctx.invoke()
        ctx.assert_sent(
            "es-tu sûr ?",
            "Mission aborted",
        )
        dr_patch.assert_not_called()

        # motif = divin, cible = "all", proceed
        ctx = mock_discord.get_ctx(refill, "divvvvvvin", cible="all")
        with mock_discord.interact(("yes_no", True)):
            await ctx.invoke()
        ctx.assert_sent(
            "es-tu sûr ?",
            "répondant aux critères",
        )
        dr_patch.assert_called_once()
        motif, refilled = dr_patch.call_args.args
        self.assertEqual("divvvvvvin", motif)
        self.assertEqual(set(all_actions), set(refilled))
        dr_patch.reset_mock()

        # motif = divin, cible = Joueur1
        ctx = mock_discord.get_ctx(refill, "divvvvvvin", cible="Joueur1")
        await ctx.invoke()
        ctx.assert_sent("répondant aux critères")
        dr_patch.assert_called_once()
        motif, refilled = dr_patch.call_args.args
        self.assertEqual("divvvvvvin", motif)
        self.assertEqual(set(ac for ac in all_actions if ac.joueur == joueur1),
                         set(refilled))
        dr_patch.reset_mock()

        # motif = autre, cible = "all"
        for motif in ["uikz", "forgebonk", "rebootax"]:
            ctx = mock_discord.get_ctx(refill, motif, cible="all")
            await ctx.invoke()
            ctx.assert_sent("répondant aux critères")
            dr_patch.assert_called_once()
            motifc, refilled = dr_patch.call_args.args
            self.assertEqual(motif, motifc)
            self.assertEqual(set(actions[motif]), set(refilled))
            dr_patch.reset_mock()

        # motif = autre, cible = Joueur1
        for motif in ["uikz", "forgebonk", "rebootax"]:
            ctx = mock_discord.get_ctx(refill, motif, cible="Joueur1")
            await ctx.invoke()
            ctx.assert_sent("répondant aux critères")
            dr_patch.assert_called_once()
            motifc, refilled = dr_patch.call_args.args
            self.assertEqual(motif, motifc)
            self.assertEqual(set(ac for ac in actions[motif]
                                 if ac.joueur == joueur1),
                             set(refilled))
            dr_patch.reset_mock()


    @mock_bdd.patch_db      # Empty database for this method
    @mock_discord.interact()
    async def test_cparti(self):
        """Unit tests for !cparti command."""
        # async def cparti(self, ctx)
        cparti = self.cog.cparti

        mock_bdd.add_campsroles()
        joueur1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1")
        joueur2 = bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2")
        joueurs = [joueur1, joueur2]
        bdd.Joueur.add(*joueurs)
        bas = [
            bdd.BaseAction(slug="baz_strt", trigger_debut="start"),
            bdd.BaseAction(slug="baz_prm", trigger_debut="perma"),
            bdd.BaseAction(slug="baz_aut", trigger_debut="temporel")
        ]
        bdd.BaseAction.add(*bas)
        actions = [*[bdd.Action(base=base, joueur=joueur1) for base in bas],
                   *[bdd.Action(base=base, joueur=joueur2) for base in bas]]
        bdd.Action.add(*actions)

        # abort 1
        ctx = mock_discord.get_ctx(cparti)
        with mock_discord.interact(("yes_no", False)):
            await ctx.invoke()
        ctx.assert_sent(
            "",
            "Mission aborted",
        )

        # abort 2
        ctx = mock_discord.get_ctx(cparti)
        with mock_discord.interact(("yes_no", True), ("yes_no", False)):
            await ctx.invoke()
        ctx.assert_sent(
            "",
            "",
            "Mission aborted",
        )

        # proceed
        ctx = mock_discord.get_ctx(cparti)
        with mock_discord.interact(("yes_no", True), ("yes_no", True)):
            await ctx.invoke()
        ctx.assert_sent(
            "",
            "",
            "tout bon",
        )
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 8)
        commands_debuts = {
            " ".join(tache.commande.split(maxsplit=2)[:2]) for tache in taches
        }
        expected = {
            "!open cond",
            "!open maire",
            "!open loups",
            "!send all",
            *{f"!open {action.id}" for action in actions
              if action.base.slug in ("baz_strt", "baz_prm")}
        }
        self.assertEqual(commands_debuts, expected)
