import unittest
from unittest import mock

import discord

from lgrez import config, bdd
from lgrez.features import communication
from test import mock_discord, mock_bdd


class TestCommunication(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.communication commands."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = communication.Communication(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()


    @unittest.SkipTest
    @mock_bdd.patch_db      # Empty database for this method
    async def test_embed(self):
        """Unit tests for !embed command."""
        # async def embed(self, ctx, key=None, *, val=None)
        embed = self.cog.embed


    @mock_bdd.patch_db      # Empty database for this method
    async def test_send(self):
        """Unit tests for !send command."""
        # async def send(self, ctx, cible, *, message)
        send = self.cog.send
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

        # cible = "all"
        ctx = mock_discord.get_ctx(send, "all", message="ouizz")
        with mock_discord.mock_members_and_chans(*joueurs):
            chans = [joueur.private_chan for joueur in joueurs]
            await ctx.invoke()
        ctx.assert_sent("6 trouvé", "Fini")
        for chan in chans:
            chan.send.assert_called_once_with("ouizz")

        # cible = "vivants"
        ctx = mock_discord.get_ctx(send, "vivants", message="nonkk")
        with mock_discord.mock_members_and_chans(*joueurs):
            chans = [joueur.private_chan for joueur in joueurs]
            await ctx.invoke()
        ctx.assert_sent("3 trouvé", "Fini")
        for i, chan in enumerate(chans):
            if i in [0, 1, 4]:
                chan.send.assert_called_once_with("nonkk")
            else:
                chan.send.assert_not_called()

        # cible = "morts"
        ctx = mock_discord.get_ctx(send, "morts", message="bzzk.!")
        with mock_discord.mock_members_and_chans(*joueurs):
            chans = [joueur.private_chan for joueur in joueurs]
            await ctx.invoke()
        ctx.assert_sent("2 trouvé", "Fini")
        for i, chan in enumerate(chans):
            if i in [2, 3]:
                chan.send.assert_called_once_with("bzzk.!")
            else:
                chan.send.assert_not_called()

        # cible = bat crit
        ctx = mock_discord.get_ctx(send, "biz=oui", message="hmm")
        with self.assertRaises(discord.ext.commands.UserInputError) as cm:
            await ctx.invoke()
        self.assertIn("critère 'biz' incorrect", cm.exception.args[0])


        # cible = all crits
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
            ctx = mock_discord.get_ctx(send, crit, message="bakka")
            with mock_discord.mock_members_and_chans(*joueurs):
                chans = [joueur.private_chan for joueur in joueurs]
                await ctx.invoke()
            ctx.assert_sent(f"{len(ijs)} trouvé", "Fini")
            for i, chan in enumerate(chans):
                if i in ijs:
                    chan.send.assert_called_once_with("bakka")
                else:
                    chan.send.assert_not_called()

        # cible = non-existing joueur, correct
        ctx = mock_discord.get_ctx(send, "gouzigouzi", message="oui")
        with mock_discord.interact(
            ("wait_for_message_here", mock_discord.message(ctx, "krr")),
            ("wait_for_message_here", mock_discord.message(ctx, "Joueur2")),
        ):
            with mock_discord.mock_members_and_chans(*joueurs):
                chans = [joueur.private_chan for joueur in joueurs]
                await ctx.invoke()
        ctx.assert_sent("Aucune entrée trouvée", "Aucune entrée trouvée",
                        "1 trouvé", "Fini")
        for i, chan in enumerate(chans):
            if i == 1:
                chan.send.assert_called_once_with("oui")
            else:
                chan.send.assert_not_called()

        # cible = existing joueur, correct
        ctx = mock_discord.get_ctx(send, "Joueur 5", message="oui")
        with mock_discord.mock_members_and_chans(*joueurs):
            chans = [joueur.private_chan for joueur in joueurs]
            await ctx.invoke()
        ctx.assert_sent("1 trouvé", "Fini")
        for i, chan in enumerate(chans):
            if i == 4:
                chan.send.assert_called_once_with("oui")
            else:
                chan.send.assert_not_called()

        # cible = all, test eval
        ctx = mock_discord.get_ctx(send, "all", message=
            "Salut {member.mention}, tu t'appelles {joueur.role}, rôle "
            "{joueur.role.nom}, camp {joueur.camp.nom}, chan {chan.name}"
        )
        with mock_discord.mock_members_and_chans(*joueurs):
            members = [joueur.member for joueur in joueurs]
            chans = [joueur.private_chan for joueur in joueurs]
            await ctx.invoke()
        ctx.assert_sent("6 trouvé", "Fini")
        for joueur, chan, member in zip(joueurs, chans, members):
            chan.send.assert_called_once_with(
                f"Salut {member.mention}, tu t'appelles {joueur.role}, rôle "
                f"{joueur.role.nom}, camp {joueur.camp.nom}, chan {chan.name}"
            )


    @mock_bdd.patch_db      # Empty database for this method
    async def test_post(self):
        """Unit tests for !post command."""
        # async def post(self, ctx, chan, *, message)
        post = self.cog.post
        joueurs = [
            bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1"),
            bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2"),
            bdd.Joueur(discord_id=3, chan_id_=31, nom="Joueur3"),
            bdd.Joueur(discord_id=4, chan_id_=41, nom="Joueur4"),
            bdd.Joueur(discord_id=5, chan_id_=51, nom="Joueur5"),
            bdd.Joueur(discord_id=6, chan_id_=61, nom="Joueur6"),
        ]
        bdd.Joueur.add(*joueurs)

        chans = [mock_discord.chan("logs", id=153447897153447897),
                mock_discord.chan("rôles", id=564894149416486431)]

        # cible = "logs"
        ctx = mock_discord.get_ctx(post, "logs", message="ouizz")
        _chans = config.guild.channels
        config.guild.channels = chans
        await ctx.invoke()
        config.guild.channels = _chans
        ctx.assert_sent("Fait")
        chans[0].send.assert_called_once_with("ouizz")
        chans[0].send.reset_mock()
        chans[1].send.assert_not_called()

        # cible = mention de #logs
        ctx = mock_discord.get_ctx(post, "<#153447897153447897>", message="oz")
        _chans = config.guild.channels
        config.guild.channels = chans
        await ctx.invoke()
        config.guild.channels = _chans
        ctx.assert_sent("Fait")
        chans[0].send.assert_called_once_with("oz")
        chans[0].send.reset_mock()
        chans[1].send.assert_not_called()


    @unittest.SkipTest
    @mock_bdd.patch_db      # Empty database for this method
    async def test_plot(self):
        """Unit tests for !send command."""
        # async def plot(self, ctx, type)
        plot = self.cog.plot


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.config.Channel.annonces.send")
    async def test_annoncemort(self, as_patch):
        """Unit tests for !annoncemort command."""
        # async def annoncemort(self, ctx, *, victime=None)
        annoncemort = self.cog.annoncemort
        mock_bdd.add_campsroles(10, 10)
        joueurs = [
            bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                       statut=bdd.Statut.vivant, _role_slug="role1"),
            bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2",
                       chambre="ch2", statut=bdd.Statut.vivant),
            bdd.Joueur(discord_id=3, chan_id_=31, nom="Joueur3",
                       statut=bdd.Statut.mort, _role_slug="role3",
                       _camp_slug="camp3"),
            bdd.Joueur(discord_id=4, chan_id_=41, nom="Joueur4",
                       chambre="ch 4", statut=bdd.Statut.mort),
            bdd.Joueur(discord_id=5, chan_id_=51, nom="Joueur5",
                       statut=bdd.Statut.MV, _role_slug="role5"),
            bdd.Joueur(discord_id=6, chan_id_=61, nom="Joueur6",
                       statut=bdd.Statut.immortel, _role_slug="role3"),
        ]
        bdd.Joueur.add(*joueurs)

        # victime = None, correct "Joueur3", role ok, abort
        ctx = mock_discord.get_ctx(annoncemort)
        with mock_discord.interact(
            ("wait_for_message_here", mock_discord.message(ctx, "bzz")),
            ("wait_for_message_here", mock_discord.message(ctx, "Joueur3")),
            ("yes_no", True),                   # rôle à afficher
            ("wait_for_message_here", mock_discord.message(ctx, "oui")),
            ("yes_no", False),                  # abort
        ):
            await ctx.invoke(cog=self.cog)
        ctx.assert_sent("Qui", "Aucune entrée trouvée", "Rôle à afficher",
                        "Contexte", "Ça part", "Mission aborted")
        as_patch.assert_not_called()

        # victime = "Joueur3", role ok, proceed
        ctx = mock_discord.get_ctx(annoncemort, victime="Joueur3")
        with mock_discord.interact(
            ("yes_no", True),                   # rôle à afficher
            ("wait_for_message_here", mock_discord.message(ctx, "oui")),
            ("yes_no", True),                   # proceed
        ):
            await ctx.invoke(cog=self.cog)
        ctx.assert_sent("Rôle à afficher", "Contexte", "Ça part",
                        "c'est parti")
        as_patch.assert_called_once()
        self.assertIn("quelque chose", as_patch.call_args.args[0])
        embed = as_patch.call_args.kwargs["embed"]
        self.assertIn("Joueur3", embed.title)
        self.assertIn("Role3", embed.title)
        self.assertIn("oui", embed.description)
        self.assertEqual(discord.Embed.Empty, embed.thumbnail.url)
        # standard role: no emoji
        as_patch.reset_mock()

        # victime = "Joueur3", role ok, proceed + emoji
        ctx = mock_discord.get_ctx(annoncemort, victime="Joueur3")
        emoji3 = mock.NonCallableMock(discord.Emoji)
        emoji3.configure_mock(name="emoji3", url="bzooop")
        _emojis = config.guild.emojis
        config.guild.emojis = [emoji3]
        with mock_discord.interact(
            ("yes_no", True),                   # rôle à afficher
            ("wait_for_message_here", mock_discord.message(ctx, "oui")),
            ("yes_no", True),                   # proceed
        ):
            await ctx.invoke(cog=self.cog)
        config.guild.emojis = _emojis
        ctx.assert_sent("Rôle à afficher", "Contexte", "Ça part",
                        "c'est parti")
        as_patch.assert_called_once()
        self.assertIn("quelque chose", as_patch.call_args.args[0])
        embed = as_patch.call_args.kwargs["embed"]
        self.assertIn("Joueur3", embed.title)
        self.assertIn("Role3", embed.title)
        self.assertIn("oui", embed.description)
        self.assertEqual("bzooop", embed.thumbnail.url)
        as_patch.reset_mock()

        # victime = "Joueur5" (MV), role ok no MV, proceed
        ctx = mock_discord.get_ctx(annoncemort, victime="Joueur5")
        with mock_discord.interact(
            ("yes_no", True),                   # rôle à afficher
            ("yes_no", False),                  # afficher la MVance
            ("wait_for_message_here", mock_discord.message(ctx, "oui")),
            ("yes_no", True),                   # proceed
        ):
            await ctx.invoke(cog=self.cog)
        ctx.assert_sent("Rôle à afficher", "Annoncer la mort-vivance",
                         "Contexte", "Ça part", "c'est parti")
        as_patch.assert_called_once()
        self.assertIn("quelque chose", as_patch.call_args.args[0])
        embed = as_patch.call_args.kwargs["embed"]
        self.assertIn("Joueur5", embed.title)
        self.assertIn("Role5", embed.title)
        self.assertNotIn("Mort-Vivant", embed.title)
        self.assertIn("oui", embed.description)
        as_patch.reset_mock()

        # victime = "Joueur5" (MV), role ok no MV, proceed
        ctx = mock_discord.get_ctx(annoncemort, victime="Joueur5")
        with mock_discord.interact(
            ("yes_no", True),                   # rôle à afficher
            ("yes_no", True),                   # afficher la MVance
            ("wait_for_message_here", mock_discord.message(ctx, "oui")),
            ("yes_no", True),                   # proceed
        ):
            await ctx.invoke(cog=self.cog)
        ctx.assert_sent("Rôle à afficher", "Annoncer la mort-vivance",
                         "Contexte", "Ça part", "c'est parti")
        as_patch.assert_called_once()
        self.assertIn("quelque chose", as_patch.call_args.args[0])
        embed = as_patch.call_args.kwargs["embed"]
        self.assertIn("Joueur5", embed.title)
        self.assertIn("Role5", embed.title)
        self.assertIn("Mort-Vivant", embed.title)
        self.assertIn("oui", embed.description)
        as_patch.reset_mock()

        role_village = bdd.Role(slug="")

        # victime = "Joueur3", role not ok usoab, proceed
        ctx = mock_discord.get_ctx(annoncemort, victime="Joueur3")
        with mock_discord.interact(
            ("yes_no", False),                  # rôle à afficher
            ("wait_for_message_here", mock_discord.message(ctx, "RolZZZ")),
            ("wait_for_react_clic", mock.NonCallableMock(discord.Emoji,
                                                         url="bzooop")),
            ("wait_for_message_here", mock_discord.message(ctx, "oui")),
            ("yes_no", True),                   # proceed
        ):
            await ctx.invoke(cog=self.cog)
        ctx.assert_sent("Rôle à afficher", "Rôle à afficher", "Camp",
                        "Contexte", "Ça part", "c'est parti")
        as_patch.assert_called_once()
        self.assertIn("quelque chose", as_patch.call_args.args[0])
        embed = as_patch.call_args.kwargs["embed"]
        self.assertIn("Joueur3", embed.title)
        self.assertIn("RolZZZ", embed.title)
        self.assertIn("oui", embed.description)
        self.assertEqual("bzooop", embed.thumbnail.url)
        as_patch.reset_mock()
