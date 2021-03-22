import datetime
import unittest
from unittest import mock

import discord
import freezegun

from lgrez import config, bdd
from lgrez.features import taches
from test import mock_discord, mock_bdd


class TestGestionTaches(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.taches commands."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = taches.GestionTaches(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()

    @mock_bdd.patch_db      # Empty database for this method
    async def test_taches(self):
        """Unit tests for !taches command."""
        # async def taches(self, ctx)
        taches_cmd = self.cog.taches

        # no taches
        ctx = mock_discord.get_ctx(taches_cmd)
        await ctx.invoke()
        ctx.assert_sent("Aucune tâche")

        # some taches
        bdd.Tache(timestamp=datetime.datetime.now(), commande="bloup").add()
        bdd.BaseAction(slug="baaz").add()
        bdd.Joueur(discord_id=123, chan_id_=2, nom="Joueur1").add()
        bdd.Action(id=13, _base_slug="baaz", _joueur_id=123).add()
        bdd.Tache(timestamp=datetime.datetime(2021, 5, 15, 18, 0, 0),
                  commande="bliip", _action_id=13).add()
        ctx = mock_discord.get_ctx(taches_cmd)
        await ctx.invoke()
        ctx.assert_sent("Tâches en attente")
        self.assertIn("bloup", ctx.send.call_args.args[0])
        self.assertIn("bliip", ctx.send.call_args.args[0])
        self.assertIn("baaz", ctx.send.call_args.args[0])
        self.assertIn("Joueur1", ctx.send.call_args.args[0])

        # a lot of taches
        bdd.Tache.add(*(bdd.Tache(timestamp=datetime.datetime.now(),
                                  commande=f"bloup{n}") for n in range(1000)))
        ctx = mock_discord.get_ctx(taches_cmd)
        await ctx.invoke()
        sent = "\n".join(call.args[0] for call in ctx.send.call_args_list)
        for n in range(1000):
            self.assertIn(f"bloup{n}", sent)


    @mock_bdd.patch_db      # Empty database for this method
    async def test_planif(self):
        """Unit tests for !planif command."""
        # async def planif(self, ctx, quand, *, commande)
        planif = self.cog.planif
        today = datetime.date.today()
        today_12h = datetime.datetime.combine(today, datetime.time(12, 0))
        firstmarch_12h = datetime.datetime(2021, 3, 1, 12, 0)

        # bad timestamp
        ctx = mock_discord.get_ctx(planif, "bzzt", commande="oui")
        with self.assertRaises(ValueError):
            await ctx.invoke()
        self.assertEqual(bdd.Tache.query.all(), [])

        # hh:mm after now
        ctx = mock_discord.get_ctx(planif, "18:10", commande="oui")
        with freezegun.freeze_time(today_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime.combine(
            today, datetime.time(18, 10)))
        self.assertEqual(tache.commande, "oui")
        tache.delete()

        # hh:mm:ss after now
        ctx = mock_discord.get_ctx(planif, "18:10:52", commande="non")
        with freezegun.freeze_time(today_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime.combine(
            today, datetime.time(18, 10, 52)))
        self.assertEqual(tache.commande, "non")
        tache.delete()

        # hh:mm before now, abort
        ctx = mock_discord.get_ctx(planif, "10:10", commande="oui")
        with freezegun.freeze_time(today_12h):
            with mock_discord.interact(("yes_no", False)):
                await ctx.invoke()
        self.assertEqual(bdd.Tache.query.all(), [])

        # hh:mm before now, proceed
        ctx = mock_discord.get_ctx(planif, "10:10", commande="oui")
        with freezegun.freeze_time(today_12h):
            with mock_discord.interact(("yes_no", True)):
                await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime.combine(
            today, datetime.time(10, 10)))
        self.assertEqual(tache.commande, "oui")
        tache.delete()

        # jj/mm-hh:mm after now
        ctx = mock_discord.get_ctx(planif, "05/03-09:07", commande="non")
        with freezegun.freeze_time(firstmarch_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2021, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "non")
        tache.delete()

        # j/m-h:m after now
        ctx = mock_discord.get_ctx(planif, "5/3-9:7", commande="non")
        with freezegun.freeze_time(firstmarch_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2021, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "non")
        tache.delete()

        # jj/mm-hh:mm before now
        ctx = mock_discord.get_ctx(planif, "05/02-09:07", commande="non")
        with freezegun.freeze_time(firstmarch_12h):
            with mock_discord.interact(("yes_no", True)):
                await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2021, 2, 5, 9, 7))
        self.assertEqual(tache.commande, "non")
        tache.delete()

        # jj/mm/aaaa-hh:mm after now
        ctx = mock_discord.get_ctx(planif, "05/03/2023-09:07", commande="non")
        with freezegun.freeze_time(firstmarch_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2023, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "non")
        tache.delete()

        # jj/mm/aaaa-hh:mm before now
        ctx = mock_discord.get_ctx(planif, "05/03/2020-09:07", commande="non")
        with freezegun.freeze_time(firstmarch_12h):
            with mock_discord.interact(("yes_no", True)):
                await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2020, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "non")
        tache.delete()

        # jj/mm-hh:mm after now, !open <non-existing action>
        ctx = mock_discord.get_ctx(planif, "05/03-09:07", commande="!open 77")
        with freezegun.freeze_time(firstmarch_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2021, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "!open 77")
        self.assertIsNone(tache.action)
        tache.delete()

        # jj/mm-hh:mm after now, !open <existing action>
        bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1").add()
        bdd.BaseAction(slug="ouiz").add()
        action = bdd.Action(id=78, _base_slug="ouiz", _joueur_id=1)
        action.add()
        ctx = mock_discord.get_ctx(planif, "05/03-09:07", commande="!open 78")
        with freezegun.freeze_time(firstmarch_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2021, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "!open 78")
        self.assertEqual(tache.action, action)
        tache.delete()

        # jj/mm-hh:mm after now, !close <non-existing action>
        ctx = mock_discord.get_ctx(planif, "05/03-09:07", commande="!close 77")
        with freezegun.freeze_time(firstmarch_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2021, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "!close 77")
        self.assertIsNone(tache.action)
        tache.delete()

        # jj/mm-hh:mm after now, !close <existing action>
        ctx = mock_discord.get_ctx(planif, "05/03-09:07", commande="!close 78")
        with freezegun.freeze_time(firstmarch_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2021, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "!close 78")
        self.assertEqual(tache.action, action)
        tache.delete()

        # jj/mm-hh:mm after now, !remind <non-existing action>
        ctx = mock_discord.get_ctx(planif, "05/03-09:07", commande="!remind 77")
        with freezegun.freeze_time(firstmarch_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2021, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "!remind 77")
        self.assertIsNone(tache.action)
        tache.delete()

        # jj/mm-hh:mm after now, !remind <existing action>
        ctx = mock_discord.get_ctx(planif, "05/03-09:07", commande="!remind 78")
        with freezegun.freeze_time(firstmarch_12h):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, datetime.datetime(2021, 3, 5, 9, 7))
        self.assertEqual(tache.commande, "!remind 78")
        self.assertEqual(tache.action, action)
        tache.delete()


    @mock_bdd.patch_db      # Empty database for this method
    async def test_delay(self):
        """Unit tests for !delay command."""
        # async def delay(self, ctx, duree, *, commande)
        delay = self.cog.delay
        now = datetime.datetime(2021, 3, 1, 12, 0)

        # bad duree
        bads = ["bzzt", "0h", "0m", "0s", "0h0m", "0h0s", "0m0s", "0h0m0s",
                "1h1", "1m1", "1s1", "1h1m1", "1h1s1", "1m1s1", "1m1m1s1"]
        for bad in bads:
            ctx = mock_discord.get_ctx(delay, bad, commande="oui")
            with self.assertRaises(discord.ext.commands.BadArgument):
                await ctx.invoke()
            self.assertEqual(bdd.Tache.query.all(), [])

        # diffrent ways
        oks = {
            "2h": datetime.timedelta(hours=2),
            "3m": datetime.timedelta(minutes=3),
            "5s": datetime.timedelta(seconds=5),
            "2h3m": datetime.timedelta(hours=2, minutes=3),
            "2h5s": datetime.timedelta(hours=2, seconds=5),
            "3m5s": datetime.timedelta(minutes=3, seconds=5),
            "2h3m5s": datetime.timedelta(hours=2, minutes=3, seconds=5),
        }
        for ok, delta in oks.items():
            ctx = mock_discord.get_ctx(delay, ok, commande="oui")
            with freezegun.freeze_time(now):
                await ctx.invoke()
            self.assertEqual(len(bdd.Tache.query.all()), 1)
            tache = bdd.Tache.query.one()
            self.assertEqual(tache.timestamp, now + delta)
            self.assertEqual(tache.commande, "oui")
            tache.delete()

        # ok, !open <non-existing action>
        ctx = mock_discord.get_ctx(delay, "3m5s", commande="!open 77")
        delta = oks["3m5s"]
        with freezegun.freeze_time(now):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, now + delta)
        self.assertEqual(tache.commande, "!open 77")
        self.assertIsNone(tache.action)
        tache.delete()

        # ok, !open <existing action>
        bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1").add()
        bdd.BaseAction(slug="ouiz").add()
        action = bdd.Action(id=78, _base_slug="ouiz", _joueur_id=1)
        action.add()
        ctx = mock_discord.get_ctx(delay, "3m5s", commande="!open 78")
        with freezegun.freeze_time(now):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, now + delta)
        self.assertEqual(tache.commande, "!open 78")
        self.assertEqual(tache.action, action)
        tache.delete()

        # ok, !close <non-existing action>
        ctx = mock_discord.get_ctx(delay, "3m5s", commande="!close 77")
        with freezegun.freeze_time(now):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, now + delta)
        self.assertEqual(tache.commande, "!close 77")
        self.assertIsNone(tache.action)
        tache.delete()

        # ok, !close <existing action>
        ctx = mock_discord.get_ctx(delay, "3m5s", commande="!close 78")
        with freezegun.freeze_time(now):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, now + delta)
        self.assertEqual(tache.commande, "!close 78")
        self.assertEqual(tache.action, action)
        tache.delete()

        # ok, !remind <non-existing action>
        ctx = mock_discord.get_ctx(delay, "3m5s", commande="!remind 77")
        with freezegun.freeze_time(now):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, now + delta)
        self.assertEqual(tache.commande, "!remind 77")
        self.assertIsNone(tache.action)
        tache.delete()

        # ok, !remind <existing action>
        ctx = mock_discord.get_ctx(delay, "3m5s", commande="!remind 78")
        with freezegun.freeze_time(now):
            await ctx.invoke()
        self.assertEqual(len(bdd.Tache.query.all()), 1)
        tache = bdd.Tache.query.one()
        self.assertEqual(tache.timestamp, now + delta)
        self.assertEqual(tache.commande, "!remind 78")
        self.assertEqual(tache.action, action)
        tache.delete()


    @mock_bdd.patch_db      # Empty database for this method
    async def test_cancel(self):
        """Unit tests for !cancel command."""
        # async def cancel(self, ctx, *ids)
        cancel = self.cog.cancel

        # no arg
        ctx = mock_discord.get_ctx(cancel)
        await ctx.invoke()
        ctx.assert_sent("Aucune tâche trouvée")

        # meaningless args
        ctx = mock_discord.get_ctx(cancel, "oh", "ezz", "O@!")
        await ctx.invoke()
        ctx.assert_sent("Aucune tâche trouvée")

        # nonexisting tasks
        ctx = mock_discord.get_ctx(cancel, "1", "2", "3")
        await ctx.invoke()
        ctx.assert_sent("Aucune tâche trouvée")

        # one existing task, abort
        bdd.Tache(id=9, timestamp=datetime.datetime.now(), commande="oz").add()
        ctx = mock_discord.get_ctx(cancel, "9")
        with mock_discord.interact(("yes_no", False)):
            await ctx.invoke()
        ctx.assert_sent("oz", "aborted")
        self.assertEqual(len(bdd.Tache.query.all()), 1)

        # one existing task, proceed
        ctx = mock_discord.get_ctx(cancel, "9")
        with mock_discord.interact(("yes_no", True)):
            await ctx.invoke()
        ctx.assert_sent("oz", "annulée")
        self.assertEqual(len(bdd.Tache.query.all()), 0)

        # two tasks and junk, abort
        bdd.Tache(id=3, timestamp=datetime.datetime.now(), commande="oz").add()
        bdd.Tache(id=5, timestamp=datetime.datetime.now(), commande="uz").add()
        ctx = mock_discord.get_ctx(cancel, "9", "az", "3", "5")
        with mock_discord.interact(("yes_no", False)):
            await ctx.invoke()
        ctx.assert_sent(["oz", "uz"], "aborted")
        self.assertEqual(len(bdd.Tache.query.all()), 2)

        # two tasks and junk, proceed
        ctx = mock_discord.get_ctx(cancel, "9", "az", "3", "5")
        with mock_discord.interact(("yes_no", True)):
            await ctx.invoke()
        ctx.assert_sent(["oz", "uz"], "annulée")
        self.assertEqual(len(bdd.Tache.query.all()), 0)
