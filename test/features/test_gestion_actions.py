import datetime
import unittest
from unittest import mock

import discord
import freezegun

from lgrez import config, bdd
from lgrez.features import gestion_actions
from lgrez.blocs import gsheets
from test import mock_discord, mock_bdd, mock_env


def base_joueurs():
    return [
        bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1", chambre="Ch1",
                   statut=bdd.Statut.vivant, role=bdd.Role.default(),
                   camp=bdd.Camp.default(), votant_village=False,
                   votant_loups=False, role_actif=False),
        bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2", chambre="Ch2",
                   statut=bdd.Statut.mort, _role_slug="role2",
                   _camp_slug="camp2", votant_village=True,
                   votant_loups=False, role_actif=False),
        bdd.Joueur(discord_id=3, chan_id_=31, nom="Joueur3", chambre="Ch3",
                   statut=bdd.Statut.MV, _role_slug="role3",
                   _camp_slug="camp3", votant_village=True,
                   votant_loups=True, role_actif=False),
        bdd.Joueur(discord_id=4, chan_id_=41, nom="Joueur4", chambre="Ch4",
                   statut=bdd.Statut.immortel, _role_slug="role4",
                   _camp_slug="camp4", votant_village=True,
                   votant_loups=True, role_actif=True),
    ]


class TestGestionActionsFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.gestion_actions functions."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()


    @mock_bdd.patch_db      # Empty database for this method
    def test_add_action(self):
        """Unit tests for gestion_actions.add_action function."""
        # def add_action(action)
        add_action = gestion_actions.add_action
        mock_bdd.add_campsroles()
        j1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1")
        j1.add()

        # basic
        ba1 = bdd.BaseAction(slug="ba1", trigger_debut=bdd.ActionTrigger.mort)
        ba1.add()
        act1 = bdd.Action(base=ba1, joueur=j1)
        add_action(act1)
        self.assertEqual(bdd.Action.query.all(), [act1])
        self.assertEqual(bdd.Tache.query.all(), [])
        act1.delete()

        # temporel
        ba2 = bdd.BaseAction(slug="ba2",
                             trigger_debut=bdd.ActionTrigger.temporel,
                             heure_debut=datetime.time(15, 2))
        ba2.add()
        act2 = bdd.Action(id=25, base=ba2, joueur=j1)
        add_action(act2)
        self.assertEqual(bdd.Action.query.all(), [act2])
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp.time(), datetime.time(15, 2))
        self.assertEqual(tache.commande, "!open 25")
        self.assertEqual(tache.action, act2)
        act2.delete()
        tache.delete()

        # perma
        ba3 = bdd.BaseAction(slug="ba3", trigger_debut=bdd.ActionTrigger.perma)
        ba3.add()
        act3 = bdd.Action(id=23, base=ba3, joueur=j1)
        add_action(act3)
        self.assertEqual(bdd.Action.query.all(), [act3])
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertAlmostEqual(tache.timestamp, datetime.datetime.now(),
                               delta=datetime.timedelta(seconds=1))
        self.assertEqual(tache.commande, "!open 23")
        self.assertEqual(tache.action, act3)


    @mock_bdd.patch_db      # Empty database for this method
    def test_delete_action(self):
        """Unit tests for gestion_actions.delete_action function."""
        # def delete_action(action)
        delete_action = gestion_actions.delete_action
        mock_bdd.add_campsroles()
        j1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1")
        j1.add()

        # no taches
        ba1 = bdd.BaseAction(slug="ba1")
        ba1.add()
        act1 = bdd.Action(base=ba1, joueur=j1)
        act1.add()
        delete_action(act1)
        self.assertEqual(bdd.Action.query.all(), [])
        self.assertEqual(bdd.Tache.query.all(), [])

        # some taches
        act1 = bdd.Action(base=ba1, joueur=j1)
        act1.add()
        bdd.Tache(timestamp=datetime.datetime.now(), commande="t1",
                  action=act1).add()
        bdd.Tache(timestamp=datetime.datetime(2021, 3, 15, 15, 2, 0),
                  commande="t2", action=act1).add()
        delete_action(act1)
        self.assertEqual(bdd.Action.query.all(), [])
        self.assertEqual(bdd.Tache.query.all(), [])


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.gestion_actions.close_action")
    @mock.patch("lgrez.blocs.tools.log")
    async def test_open_action(self, log_patch, ca_patch):
        """Unit tests for gestion_actions.open_action function."""
        # async def open_action(action)
        open_action = gestion_actions.open_action
        mock_bdd.add_campsroles()
        j1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                        role_actif=True)
        j1.add()

        # test préliminaire 1 - en cooldown, non temporel
        ba1 = bdd.BaseAction(slug="ba1")
        ba1.add()
        act1 = bdd.Action(base=ba1, joueur=j1, cooldown=3)
        act1.add()
        with mock_discord.mock_members_and_chans(j1):
            await open_action(act1)
        self.assertEqual(act1.cooldown, 2)
        log_patch.assert_called_once()
        self.assertIn(repr(act1), log_patch.call_args.args[0])
        self.assertIn("en cooldown", log_patch.call_args.args[0])
        self.assertEqual(bdd.Tache.query.all(), [])
        ca_patch.assert_not_called()
        log_patch.reset_mock()

        # test préliminaire 2 - en cooldown, temporel
        ba2 = bdd.BaseAction(slug="ba2",
                             trigger_debut=bdd.ActionTrigger.temporel,
                             heure_debut=datetime.time(15, 2))
        ba2.add()
        act2 = bdd.Action(id=23, base=ba2, joueur=j1, cooldown=3)
        act2.add()
        with mock_discord.mock_members_and_chans(j1):
            await open_action(act2)
        self.assertEqual(act2.cooldown, 2)
        log_patch.assert_called_once()
        self.assertIn(repr(act2), log_patch.call_args.args[0])
        self.assertIn("en cooldown", log_patch.call_args.args[0])
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp.time(), datetime.time(15, 2))
        self.assertEqual(tache.commande, "!open 23")
        self.assertEqual(tache.action, act2)
        log_patch.reset_mock()
        ca_patch.assert_not_called()
        tache.delete()

        # test préliminaire 3 - role non actif, non temporel
        j2 = bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2",
                        role_actif=False)
        j2.add()
        act3 = bdd.Action(id=24, base=ba1, joueur=j2, cooldown=0)
        act3.add()
        with mock_discord.mock_members_and_chans(j2):
            await open_action(act3)
        self.assertEqual(act3.cooldown, 0)
        log_patch.assert_called_once()
        self.assertIn(repr(act3), log_patch.call_args.args[0])
        self.assertIn("role_actif == False", log_patch.call_args.args[0])
        self.assertEqual(bdd.Tache.query.all(), [])
        ca_patch.assert_not_called()
        log_patch.reset_mock()

        # test préliminaire 4 - role non actif, temporel
        act4 = bdd.Action(id=25, base=ba2, joueur=j2, cooldown=0)
        act4.add()
        with mock_discord.mock_members_and_chans(j2):
            await open_action(act4)
        self.assertEqual(act4.cooldown, 0)
        log_patch.assert_called_once()
        self.assertIn(repr(act4), log_patch.call_args.args[0])
        self.assertIn("role_actif == False", log_patch.call_args.args[0])
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp.time(), datetime.time(15, 2))
        self.assertEqual(tache.commande, "!open 25")
        self.assertEqual(tache.action, act4)
        log_patch.reset_mock()
        ca_patch.assert_not_called()
        tache.delete()

        # test préliminaire 5 - action automatique, non temporelle
        ba3 = bdd.BaseAction(slug="ba3",
                             trigger_debut=bdd.ActionTrigger.perma,
                             trigger_fin=bdd.ActionTrigger.auto)
        ba3.add()
        act5 = bdd.Action(id=27, base=ba3, joueur=j1, cooldown=0)
        act5.add()
        with mock_discord.mock_members_and_chans(j1):
            await open_action(act5)
        self.assertEqual(act5.cooldown, 0)
        log_patch.assert_called_once()
        self.assertIn(repr(act5), log_patch.call_args.args[0])
        self.assertIn("automatique", log_patch.call_args.args[0])
        self.assertEqual(bdd.Tache.query.all(), [])
        ca_patch.assert_called_once_with(act5)
        log_patch.reset_mock()
        ca_patch.reset_mock()

        # test préliminaire 6 - action automatique, temporelle
        ba4 = bdd.BaseAction(slug="ba4",
                             trigger_debut=bdd.ActionTrigger.temporel,
                             heure_debut=datetime.time(15, 2),
                             trigger_fin=bdd.ActionTrigger.auto)
        ba4.add()
        act6 = bdd.Action(id=28, base=ba4, joueur=j1, cooldown=0)
        act6.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await open_action(act6)
        self.assertEqual(act6.cooldown, 0)
        log_patch.assert_called_once()
        self.assertIn("ba4", log_patch.call_args.args[0])
        self.assertIn("Joueur1", log_patch.call_args.args[0])
        self.assertIn("pas vraiment automatique", log_patch.call_args.args[0])
        self.assertIn(str(config.Role.mj.mention), log_patch.call_args.args[0])
        self.assertIn(str(chan.mention), log_patch.call_args.args[0])
        self.assertEqual(bdd.Tache.query.all(), [])
        ca_patch.assert_called_once_with(act6)
        log_patch.reset_mock()
        ca_patch.reset_mock()


        # --- fin des tests préliminaires
        # fin hors temp/delta/perma, déjà ouverte
        ba5 = bdd.BaseAction(slug="ba5",
                             trigger_debut=bdd.ActionTrigger.open_cond,
                             trigger_fin=bdd.ActionTrigger.close_cond)
        ba5.add()
        act7 = bdd.Action(base=ba5, joueur=j1, decision_="rien")
        act7.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await open_action(act7)
        mock_discord.assert_sent(chan, [
            "tu peux utiliser quand tu le souhaites", "ba5", "!action",
        ])
        mock_discord.assert_not_sent(chan, "tu as jusqu'à")
        self.assertEqual(act7.decision_, "rien")
        chan.send.return_value.add_reaction.assert_called_once_with(
            config.Emoji.action
        )
        self.assertEqual(bdd.Tache.query.all(), [])
        log_patch.assert_not_called()
        ca_patch.assert_not_called()

        # fin hors temp/delta/perma, fermée
        ba6 = bdd.BaseAction(slug="ba6",
                             trigger_debut=bdd.ActionTrigger.open_cond,
                             trigger_fin=bdd.ActionTrigger.close_cond)
        ba6.add()
        act8 = bdd.Action(id=30, base=ba6, joueur=j1, decision_=None)
        act8.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await open_action(act8)
        mock_discord.assert_sent(chan, [
            "Tu peux maintenant utiliser", "ba6", "!action",
        ])
        mock_discord.assert_not_sent(chan, "tu as jusqu'à")
        chan.send.return_value.add_reaction.assert_called_once_with(
            config.Emoji.action
        )
        self.assertEqual(act8.decision_, "rien")
        self.assertEqual(bdd.Tache.query.all(), [])
        log_patch.assert_not_called()
        ca_patch.assert_not_called()


        # fin temp, déjà ouverte
        ba7 = bdd.BaseAction(slug="ba7",
                             trigger_debut=bdd.ActionTrigger.open_cond,
                             trigger_fin=bdd.ActionTrigger.temporel,
                             heure_fin=datetime.time(15, 2))
        ba7.add()
        act9 = bdd.Action(id=31, base=ba7, joueur=j1, decision_="rien")
        act9.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await open_action(act9)
        mock_discord.assert_sent(chan, [
            "tu peux utiliser quand tu le souhaites", "ba7", "!action",
            f"Tu as jusqu'à {datetime.time(15, 2)}"
        ])
        chan.send.return_value.add_reaction.assert_called_once_with(
            config.Emoji.action
        )
        self.assertEqual(act9.decision_, "rien")
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 2)
        self.assertEqual([tache.action for tache in taches], [act9]*2)
        self.assertEqual(
            {(tache.commande, tache.timestamp.time()) for tache in taches},
            {("!close 31", datetime.time(15, 2)),
             ("!remind 31", datetime.time(14, 32))}
        )
        bdd.Tache.delete(*taches)
        log_patch.assert_not_called()
        ca_patch.assert_not_called()

        # fin temp, fermée
        ba8 = bdd.BaseAction(slug="ba8",
                             trigger_debut=bdd.ActionTrigger.open_cond,
                             trigger_fin=bdd.ActionTrigger.temporel,
                             heure_fin=datetime.time(15, 2))
        ba8.add()
        act10 = bdd.Action(id=32, base=ba8, joueur=j1, decision_=None)
        act10.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await open_action(act10)
        mock_discord.assert_sent(chan, [
            "Tu peux maintenant utiliser", "ba8", "!action",
            f"Tu as jusqu'à {datetime.time(15, 2)}"
        ])
        self.assertEqual(act10.decision_, "rien")
        chan.send.return_value.add_reaction.assert_called_once_with(
            config.Emoji.action
        )
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 2)
        self.assertEqual([tache.action for tache in taches], [act10]*2)
        self.assertEqual(
            {(tache.commande, tache.timestamp.time()) for tache in taches},
            {("!close 32", datetime.time(15, 2)),
             ("!remind 32", datetime.time(14, 32))}
        )
        bdd.Tache.delete(*taches)
        log_patch.assert_not_called()
        ca_patch.assert_not_called()


        # fin delta (fermée)
        ba9 = bdd.BaseAction(slug="ba9",
                             trigger_debut=bdd.ActionTrigger.open_cond,
                             trigger_fin=bdd.ActionTrigger.delta,
                             heure_fin=datetime.time(1, 10, 7))
        ba9.add()
        act11 = bdd.Action(id=33, base=ba9, joueur=j1, decision_=None)
        act11.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            with freezegun.freeze_time(datetime.datetime(1, 1, 1, 16, 28, 4)):
                await open_action(act11)
        mock_discord.assert_sent(chan, [
            "Tu peux maintenant utiliser", "ba9", "!action",
            f"Tu as jusqu'à {datetime.time(17, 38, 11)}"
        ])
        self.assertEqual(act11.decision_, "rien")
        chan.send.return_value.add_reaction.assert_called_once_with(
            config.Emoji.action
        )
        taches = bdd.Tache.query.all()
        self.assertEqual(len(taches), 2)
        self.assertEqual([tache.action for tache in taches], [act11]*2)
        self.assertEqual(
            {(tache.commande, tache.timestamp.time()) for tache in taches},
            {("!close 33", datetime.time(17, 38, 11)),
             ("!remind 33", datetime.time(17, 8, 11))}
        )
        bdd.Tache.delete(*taches)
        log_patch.assert_not_called()
        ca_patch.assert_not_called()


        # fin perma (fermée) - WE d'abord
        ba10 = bdd.BaseAction(slug="ba10",
                             trigger_debut=bdd.ActionTrigger.open_cond,
                             trigger_fin=bdd.ActionTrigger.perma)
        ba10.add()
        act12 = bdd.Action(id=34, base=ba10, joueur=j1, decision_=None)
        act12.add()
        with mock.patch("lgrez.blocs.tools.next_occurence",
                        return_value=datetime.datetime(1, 1, 1, 16, 28, 4)), \
             mock.patch("lgrez.blocs.tools.debut_pause",
                        return_value=datetime.datetime(1, 1, 1, 15, 28, 4)), \
             mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await open_action(act12)
        mock_discord.assert_sent(chan, [
            "Tu peux maintenant utiliser", "ba10", "!action",
        ])
        self.assertEqual(act12.decision_, "rien")
        mock_discord.assert_not_sent(chan, "Tu as jusqu'à",)
        chan.send.return_value.add_reaction.assert_called_once_with(
            config.Emoji.action
        )
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.action, act12)
        self.assertEqual(tache.commande, "!close 34")
        self.assertEqual(tache.timestamp.time(), datetime.time(15, 28, 4))
        tache.delete()
        log_patch.assert_not_called()
        ca_patch.assert_not_called()

        # fin perma (fermée) - prochaine ouverture d'abord
        ba11 = bdd.BaseAction(slug="ba11",
                             trigger_debut=bdd.ActionTrigger.open_cond,
                             trigger_fin=bdd.ActionTrigger.perma)
        ba11.add()
        act13 = bdd.Action(id=35, base=ba11, joueur=j1, decision_=None)
        act13.add()
        with mock.patch("lgrez.blocs.tools.next_occurence",
                        return_value=datetime.datetime(1, 1, 1, 16, 28, 4)), \
             mock.patch("lgrez.blocs.tools.debut_pause",
                        return_value=datetime.datetime(1, 1, 1, 17, 28, 4)), \
             mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await open_action(act13)
        mock_discord.assert_sent(chan, [
            "Tu peux maintenant utiliser", "ba11", "!action",
        ])
        self.assertEqual(act13.decision_, "rien")
        mock_discord.assert_not_sent(chan, "Tu as jusqu'à",)
        chan.send.return_value.add_reaction.assert_called_once_with(
            config.Emoji.action
        )
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.action, act13)
        self.assertEqual(tache.commande, "!open 35")
        self.assertEqual(tache.timestamp.time(), datetime.time(16, 28, 4))
        tache.delete()
        log_patch.assert_not_called()
        ca_patch.assert_not_called()


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.gestion_actions.delete_action")
    async def test_close_action(self, da_patch):
        """Unit tests for gestion_actions.close_action function."""
        # async def close_action(action)
        close_action = gestion_actions.close_action
        mock_bdd.add_campsroles()
        j1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1")
        j1.add()

        # pas de décision, no base_cooldown, no temporel/perma
        ba1 = bdd.BaseAction(slug="ba1", instant=False, base_cooldown=0,
                             trigger_debut=bdd.ActionTrigger.open_cond)
        ba1.add()
        act1 = bdd.Action(base=ba1, joueur=j1, decision_="rien")
        act1.add()
        await close_action(act1)
        self.assertIsNone(act1.decision_)
        self.assertEqual(bdd.Tache.query.all(), [])
        da_patch.assert_not_called()

        # pas de décision, base_cooldown = 4, no temporel/perma
        ba2 = bdd.BaseAction(slug="ba2", instant=False, base_cooldown=4,
                             trigger_debut=bdd.ActionTrigger.open_cond)
        ba2.add()
        act2 = bdd.Action(base=ba2, joueur=j1, cooldown=0, decision_="rien")
        act2.add()
        await close_action(act2)
        self.assertIsNone(act2.decision_)
        self.assertEqual(act2.cooldown, 4)
        self.assertEqual(bdd.Tache.query.all(), [])
        da_patch.assert_not_called()

        # pas de décision, no base_cooldown, temporel
        ba3 = bdd.BaseAction(slug="ba3", instant=False, base_cooldown=0,
                             trigger_debut=bdd.ActionTrigger.temporel,
                             heure_debut=datetime.time(15, 2))
        ba3.add()
        act3 = bdd.Action(id=3, base=ba3, joueur=j1, decision_="rien")
        act3.add()
        with mock.patch("lgrez.blocs.tools.next_occurence") as no_patch:
            no_patch.return_value = datetime.datetime(1, 1, 1, 15, 2)
            await close_action(act3)
        no_patch.assert_called_once_with(datetime.time(15, 2))
        self.assertIsNone(act3.decision_)
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, no_patch.return_value)
        self.assertEqual(tache.commande, "!open 3")
        self.assertEqual(tache.action, act3)
        tache.delete()
        da_patch.assert_not_called()

        # pas de décision, no base_cooldown, perma
        ba4 = bdd.BaseAction(slug="ba4", instant=False, base_cooldown=0,
                             trigger_debut=bdd.ActionTrigger.perma)
        ba4.add()
        act4 = bdd.Action(id=4, base=ba4, joueur=j1, decision_="rien")
        act4.add()
        with mock.patch("lgrez.blocs.tools.fin_pause") as fp_patch:
            fp_patch.return_value = datetime.datetime(1, 1, 1, 10, 4)
            await close_action(act4)
        fp_patch.assert_called_once()
        self.assertIsNone(act4.decision_)
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, fp_patch.return_value)
        self.assertEqual(tache.commande, "!open 4")
        self.assertEqual(tache.action, act4)
        tache.delete()
        da_patch.assert_not_called()

        # décision, no base_cooldown, no temporel/perma, no charges ==> no diff
        act11 = bdd.Action(base=ba1, joueur=j1, decision_="ach ja",
                           charges=None)
        act11.add()
        await close_action(act11)
        self.assertIsNone(act11.decision_)
        self.assertIsNone(act11.charges)
        self.assertEqual(bdd.Tache.query.all(), [])
        da_patch.assert_not_called()

        # décision, no base_cooldown, no temporel/perma, 4 charges
        act12 = bdd.Action(base=ba1, joueur=j1, decision_="ach ja", charges=4)
        act12.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await close_action(act12)
        self.assertIsNone(act12.decision_)
        self.assertEqual(act12.charges, 3)
        mock_discord.assert_sent(chan, "Il te reste 3 charge")
        mock_discord.assert_not_sent(chan, "pour cette semaine")
        self.assertEqual(bdd.Tache.query.all(), [])
        da_patch.assert_not_called()

        # décision, no base_cooldown, no temporel/perma, 4 charges, refill WE
        ba1b = bdd.BaseAction(slug="ba1b", instant=False, base_cooldown=0,
                              trigger_debut=bdd.ActionTrigger.open_cond,
                              refill="weekends, other")
        ba1b.add()
        act13 = bdd.Action(base=ba1b, joueur=j1, decision_="ach ja", charges=4)
        act13.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await close_action(act13)
        self.assertIsNone(act13.decision_)
        self.assertEqual(act13.charges, 3)
        mock_discord.assert_sent(chan, "Il te reste 3 charge")
        mock_discord.assert_sent(chan, "pour cette semaine")
        self.assertEqual(bdd.Tache.query.all(), [])
        da_patch.assert_not_called()

        # décision, no base_cooldown, no temporel/perma, 1 charge
        act14 = bdd.Action(id=37, base=ba1, joueur=j1, decision_="ach ja",
                           charges=1)
        act14.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await close_action(act14)
        da_patch.assert_called_once_with(act14)     # deleted
        mock_discord.assert_sent(chan, "Il te reste 0 charge")
        mock_discord.assert_not_sent(chan, "pour cette semaine")
        self.assertEqual(bdd.Tache.query.all(), [])
        da_patch.reset_mock()

        # décision, no base_cooldown, no temporel/perma, 1 charge, refill WE
        act13 = bdd.Action(base=ba1b, joueur=j1, decision_="ach ja", charges=1)
        act13.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await close_action(act13)
        self.assertIsNone(act13.decision_)
        self.assertEqual(act13.charges, 0)      # not deleted
        mock_discord.assert_sent(chan, "Il te reste 0 charge")
        mock_discord.assert_sent(chan, "pour cette semaine")
        self.assertEqual(bdd.Tache.query.all(), [])
        da_patch.assert_not_called()

        # décision, no base_cooldown, no temporel/perma, 1 charge, refill autre
        ba1c = bdd.BaseAction(slug="ba1c", instant=False, base_cooldown=0,
                              trigger_debut=bdd.ActionTrigger.open_cond,
                              refill="brzzz")
        ba1c.add()
        act13 = bdd.Action(base=ba1c, joueur=j1, decision_="ach ja", charges=1)
        act13.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await close_action(act13)
        self.assertIsNone(act13.decision_)
        self.assertEqual(act13.charges, 0)      # not deleted
        mock_discord.assert_sent(chan, "Il te reste 0 charge")
        mock_discord.assert_not_sent(chan, "pour cette semaine")
        self.assertEqual(bdd.Tache.query.all(), [])
        da_patch.assert_not_called()

        # deleted et plein d'autre trucs
        batro = bdd.BaseAction(slug="batro", instant=False, base_cooldown=2,
                              trigger_debut=bdd.ActionTrigger.perma,
                              refill="brzzz")
        act14 = bdd.Action(base=ba1, joueur=j1, decision_="ach ja", charges=1)
        act14.add()
        with mock_discord.mock_members_and_chans(j1):
            chan = j1.private_chan
            await close_action(act14)
        da_patch.assert_called_once_with(act14)     # deleted
        mock_discord.assert_sent(chan, "Il te reste 0 charge")
        mock_discord.assert_not_sent(chan, "pour cette semaine")
        self.assertEqual(bdd.Tache.query.all(), [])
        da_patch.reset_mock()


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.gestion_actions.delete_action")
    async def test_get_actions(self, da_patch):
        """Unit tests for gestion_actions.get_actions function."""
        # def get_actions(quoi, trigger, heure=None)
        get_actions = gestion_actions.get_actions
        mock_bdd.add_campsroles()
        j1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1")
        j1.add()
        perma, temporel = bdd.ActionTrigger.perma, bdd.ActionTrigger.temporel
        bap = bdd.BaseAction(slug="bap", trigger_debut=perma,
                             trigger_fin=perma)
        bat = bdd.BaseAction(slug="bat", trigger_debut=temporel,
                             heure_debut=datetime.time(15, 4),
                             trigger_fin=temporel,
                             heure_fin=datetime.time(22, 15))
        bdd.BaseAction.add(bap, bat)
        act_pn = bdd.Action(id=1, base=bap, joueur=j1, decision_=None)
        act_pr = bdd.Action(id=2, base=bap, joueur=j1, decision_="rien")
        act_pq = bdd.Action(id=3, base=bap, joueur=j1, decision_="qqch")
        act_tn = bdd.Action(id=4, base=bat, joueur=j1, decision_=None)
        act_tr = bdd.Action(id=5, base=bat, joueur=j1, decision_="rien")
        act_tq = bdd.Action(id=6, base=bat, joueur=j1, decision_="qqch")
        bdd.Action.add(act_pn, act_pr, act_pq, act_tn, act_tr, act_tq)

        samples = {
            ("open", bdd.ActionTrigger.mort, None): set(),
            ("close", bdd.ActionTrigger.mort, None): set(),
            ("remind", bdd.ActionTrigger.mort, None): set(),
            ("open", perma, None): {act_pn},
            ("close", perma, None): {act_pr, act_pq},
            ("remind", perma, None): {act_pr},
            ("open", temporel, None): discord.ext.commands.UserInputError,
            ("close", temporel, None): discord.ext.commands.UserInputError,
            ("remind", temporel, None): discord.ext.commands.UserInputError,
            ("open", temporel, datetime.time(15, 4)): {act_tn},
            ("close", temporel, datetime.time(15, 4)): set(),
            ("remind", temporel, datetime.time(15, 4)): set(),
            ("open", temporel, datetime.time(22, 15)): set(),
            ("close", temporel, datetime.time(22, 15)): {act_tr, act_tq},
            ("remind", temporel, datetime.time(22, 15)): {act_tr},
            ("open", temporel, datetime.time(3, 25)): set(),
            ("close", temporel, datetime.time(3, 25)): set(),
            ("remind", temporel, datetime.time(3, 25)): set(),
            ("bzz", perma, None): discord.ext.commands.UserInputError,
        }

        for ((quoi, trigger, heure), result) in samples.items():
            if isinstance(result, type) and issubclass(result, Exception):
                with self.assertRaises(result):
                    if heure:
                        get_actions(quoi, trigger, heure)
                    else:
                        get_actions(quoi, trigger, heure)
            else:
                if heure:
                    actions = get_actions(quoi, trigger, heure)
                else:
                    actions = get_actions(quoi, trigger, heure)
                self.assertEqual(set(actions), result)
