import unittest
from unittest import mock

import discord

from lgrez import config, bdd
from lgrez.features import annexe
from test import mock_discord, mock_bdd



class TestAnnexe(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.annexe commands."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = annexe.Annexe(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()


    async def test_roll(self):
        """Unit tests for !roll command."""
        # async def roll(self, ctx, *, XdY)
        roll = self.cog.roll

        samples = {
            "": False,
            "grzz": False,
            "1d6": True,
            "17d6": True,
            "17d6+3": True,
            "17d6-3": True,
            "17d6 + 3": True,
            "17d6 - 3": True,
            "17d6 + 3d15 + 2": True,
            "17d6-3d15-2": True,
            "17d0-3d15-2": False,
            "0d6-3d15-2": False,
            "17d6-3d15-0": True,
        }

        for sample, result in samples.items():
            ctx = mock_discord.get_ctx(roll, XdY=sample)
            if result:
                await ctx.invoke()
                ctx.assert_sent("=")
            else:
                with self.assertRaises(discord.ext.commands.UserInputError):
                    await ctx.invoke()


    async def test_coinflip(self):
        """Unit tests for !coinflip command."""
        # async def coinflip(self, ctx)
        coinflip = self.cog.coinflip

        ctx = mock_discord.get_ctx(coinflip)
        p, c = 0, 0
        for i in range(1000):
            await ctx.invoke()
            if ctx.send.call_args.args[0] == "Pile":
                p += 1
            elif ctx.send.call_args.args[0] == "Face":
                c += 1
            else:
                raise AssertionError("returned wtf thing")

        self.assertGreater(p, 400)
        self.assertGreater(c, 400)


    @unittest.SkipTest
    async def test_ping(self):
        """Unit tests for !ping command."""
        # async def ping(self, ctx)
        ping = self.cog.ping


    @mock_bdd.patch_db
    async def test_addhere(self):
        """Unit tests for !addhere command."""
        # async def addhere(self, ctx, *joueurs)
        addhere = self.cog.addhere

        mock_bdd.add_campsroles(10, 10)
        joueurs = [
            bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                       statut=bdd.Statut.vivant, _role_slug="role1",
                       votant_village=True, votant_loups=False,
                       role_actif=False),
            bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2",
                       chambre="ch2", statut=bdd.Statut.vivant,
                       votant_village=True, votant_loups=False,
                       role_actif=False),
            bdd.Joueur(discord_id=3, chan_id_=31, nom="Joueur3",
                       statut=bdd.Statut.mort, _role_slug="role3",
                       _camp_slug="camp3", votant_village=True,
                       votant_loups=False, role_actif=True),
            bdd.Joueur(discord_id=4, chan_id_=41, nom="Joueur4",
                       chambre="ch 4", statut=bdd.Statut.mort,
                       votant_village=False, votant_loups=False,
                       role_actif=True),
            bdd.Joueur(discord_id=5, chan_id_=51, nom="Joueur 5",
                       statut=bdd.Statut.MV, _camp_slug="camp3",
                       votant_village=False, votant_loups=False,
                       role_actif=False),
            bdd.Joueur(discord_id=6, chan_id_=61, nom="Joueur6",
                       statut=bdd.Statut.immortel, _role_slug="role3",
                       votant_village=False, votant_loups=True,
                       role_actif=False),
        ]
        bdd.Joueur.add(*joueurs)

        # cible = bat filtre
        ctx = mock_discord.get_ctx(addhere, "biz=oui")
        with self.assertRaises(discord.ext.commands.UserInputError) as cm:
            await ctx.invoke()
        self.assertIn("critère 'biz' incorrect", cm.exception.args[0])

        # cible = all filtres
        crits = {
            "discord_id=3": [2],
            "chan_id_=21": [1],
            "nom=Joueur4": [3],
            "nom=Joueur 5": [4],
            "chambre=ch2": [1],
            "chambre=ch 4": [3],
            "statut=vivant": [0, 1],
            "statut=mort": [2, 3],
            "statut=MV": [4],
            "statut=immortel": [5],
            "role=role1": [0],
            "role=role3": [2, 5],
            "camp=camp3": [2, 4],
            "votant_village=True": [0, 1, 2],
            "votant_village=1": [0, 1, 2],
            "votant_village=faux": [3, 4, 5],
            "votant_loups=vrai": [5],
            "votant_loups=0": [0, 1, 2, 3, 4],
            "role_actif=True": [2, 3],
            "role_actif=False": [0, 1, 4, 5],
        }
        for crit, ijs in crits.items():
            ctx = mock_discord.get_ctx(addhere, crit)
            with mock_discord.mock_members_and_chans(*joueurs):
                members = [joueur.member for joueur in joueurs]
                with mock_discord.interact(("yes_no", False)):
                    await ctx.invoke()
            ctx.assert_sent(*[joueurs[ij].nom for ij in ijs], "Fini")
            self.assertEqual(ctx.channel.set_permissions.call_count, len(ijs))
            ctx.channel.set_permissions.assert_has_calls([
                mock.call(member, read_messages=True, send_messages=True)
                for ij, member in enumerate(members)
                if ij in ijs
            ])
            ctx.channel.purge.assert_not_called()

        # cible = non-existing joueur, correct
        ctx = mock_discord.get_ctx(addhere, "gouzigouzi")
        with mock_discord.interact(
            ("wait_for_message_here", mock_discord.message(ctx, "krr")),
            ("wait_for_message_here", mock_discord.message(ctx, "Joueur2")),
            ("yes_no", False),
        ):
            with mock_discord.mock_members_and_chans(*joueurs):
                members = [joueur.member for joueur in joueurs]
                await ctx.invoke()
        ctx.assert_sent("Aucune entrée trouvée", "Aucune entrée trouvée",
                        "Joueur2", "Fini")
        ctx.channel.set_permissions.assert_called_once_with(
            members[1], read_messages=True, send_messages=True
        )
        ctx.channel.purge.assert_not_called()

        # cible = existing joueur
        ctx = mock_discord.get_ctx(addhere, "Joueur 5")
        with mock_discord.mock_members_and_chans(*joueurs):
            members = [joueur.member for joueur in joueurs]
            with mock_discord.interact(("yes_no", False)):
                await ctx.invoke()
        ctx.assert_sent("Joueur 5", "Fini")
        ctx.channel.set_permissions.assert_called_once_with(
            members[4], read_messages=True, send_messages=True
        )
        ctx.channel.purge.assert_not_called()

        # cible = several joueurs, correct some
        ctx = mock_discord.get_ctx(addhere, "Joueur2", "kwdzz", "Joueur 5")
        with mock_discord.interact(
            ("wait_for_message_here", mock_discord.message(ctx, "krr")),
            ("wait_for_message_here", mock_discord.message(ctx, "Joueur4")),
            ("yes_no", False),
        ):
            with mock_discord.mock_members_and_chans(*joueurs):
                members = [joueur.member for joueur in joueurs]
                await ctx.invoke()
        ctx.assert_sent("Aucune entrée trouvée", "Aucune entrée trouvée",
                        "Joueur2", "Joueur4", "Joueur 5", "Fini")
        self.assertEqual(ctx.channel.set_permissions.call_count, 3)
        ctx.channel.set_permissions.assert_has_calls([
            mock.call(members[1], read_messages=True, send_messages=True),
            mock.call(members[3], read_messages=True, send_messages=True),
            mock.call(members[4], read_messages=True, send_messages=True),
        ])
        ctx.channel.purge.assert_not_called()

        # cible = existing joueur, purge
        ctx = mock_discord.get_ctx(addhere, "Joueur 5")
        with mock_discord.mock_members_and_chans(*joueurs):
            members = [joueur.member for joueur in joueurs]
            with mock_discord.interact(("yes_no", True)):
                await ctx.invoke()
        ctx.assert_sent("Joueur 5", "Fini")
        ctx.channel.set_permissions.assert_called_once_with(
            members[4], read_messages=True, send_messages=True
        )
        ctx.channel.purge.assert_called_once()


    async def test_purge(self):
        """Unit tests for !purge command."""
        # async def purge(self, ctx, N=None)
        purge = self.cog.purge

        # purge all, abort
        ctx = mock_discord.get_ctx(purge)
        with mock_discord.interact(("yes_no", False)):
            await ctx.invoke()
        ctx.assert_sent("Supprimer tous")
        ctx.channel.purge.assert_not_called()

        # purge all, proceed
        ctx = mock_discord.get_ctx(purge)
        with mock_discord.interact(("yes_no", True)):
            await ctx.invoke()
        ctx.assert_sent("Supprimer tous")
        ctx.channel.purge.assert_called_once_with(limit=None)

        # purge 15, abort
        ctx = mock_discord.get_ctx(purge, "15")
        with mock_discord.interact(("yes_no", False)):
            await ctx.invoke()
        ctx.assert_sent("Supprimer les 15")
        ctx.channel.purge.assert_not_called()

        # purge 15, proceed
        ctx = mock_discord.get_ctx(purge, "15")
        with mock_discord.interact(("yes_no", True)):
            await ctx.invoke()
        ctx.assert_sent("Supprimer les 15")
        ctx.channel.purge.assert_called_once_with(limit=17)


    @unittest.SkipTest
    async def test_akinator(self):
        """Unit tests for !akinator command."""
        # async def akinator(self, ctx)
        akinator = self.cog.akinator


    @unittest.SkipTest
    async def test_xkcd(self):
        """Unit tests for !xkcd command."""
        # async def xkcd(self, ctx, N)
        xkcd = self.cog.xkcd
