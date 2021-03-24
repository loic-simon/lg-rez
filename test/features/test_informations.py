import unittest
from unittest import mock

from lgrez import config, bdd
from lgrez.features import informations
from test import mock_discord, mock_bdd


class TestInformations(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.informations."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = informations.Informations(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()

    @mock_bdd.patch_db      # Empty database for this method
    async def test_roles(self):
        """Unit tests for !roles command."""
        # async def roles(self, ctx, *, filtre=None)
        roles = self.cog.roles

        # !roles with no roles
        ctx = mock_discord.get_ctx(roles)
        await ctx.invoke()
        ctx.assert_sent("Rôles trouvés :")

        mock_bdd.add_campsroles(300, 300)       # several panes

        # !roles with a lot of roles
        emoji1 = mock.Mock(name="<:emoji1:>")
        emoji1.configure_mock(name="emoji1")
        ctx = mock_discord.get_ctx(roles)
        with mock.patch("lgrez.config.guild.emojis", [emoji1]):
            await ctx.invoke()
        sent = "\n".join(call.args[0] for call in ctx.send.call_args_list)
        self.assertIn("Role1", sent)
        self.assertIn("emoji1", sent)
        self.assertNotIn("emoji2", sent)

        bdd.Role(slug="chz", nom="ChienZ", description_courte="zoo",
                 description_longue="zpp"*12,
                 camp=bdd.Camp.query.get("camp42")).add()

        # !roles <camp>
        ctx = mock_discord.get_ctx(roles, filtre="camp42")
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Role42", ctx.send.call_args.args[0])
        self.assertIn("ChienZ", ctx.send.call_args.args[0])

        # !roles <role>
        ctx = mock_discord.get_ctx(roles, filtre="chz")
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("ChienZ", ctx.send.call_args.args[0])
        self.assertIn("Camp42", ctx.send.call_args.args[0])
        self.assertIn("zoo", ctx.send.call_args.args[0])
        self.assertIn("zppzpp", ctx.send.call_args.args[0])


    @mock_bdd.patch_db      # Empty database for this method
    async def test_rolede(self):
        """Unit tests for !rolede command."""
        # async def rolede(self, ctx, *, cible=None)
        rolede = self.cog.rolede
        mock_bdd.add_campsroles(10, 10)
        bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                   _role_slug="role7").add()

        # !rolede with existing cible
        ctx = mock_discord.get_ctx(rolede, cible="Joueur1")
        await ctx.invoke()
        ctx.assert_sent("Role7")

        # !rolede with no cible
        ctx = mock_discord.get_ctx(rolede)
        with mock_discord.interact(
                ("wait_for_message_here", ctx.new_message("zzz")),
                ("wait_for_message_here", ctx.new_message("zzz")),
                ("wait_for_message_here", ctx.new_message("Joueur1"))):
            await ctx.invoke()
        ctx.assert_sent("", "", "", "Role7")


    @mock_bdd.patch_db      # Empty database for this method
    async def test_quiest(self):
        """Unit tests for !quiest command."""
        # async def quiest(self, ctx, *, nomrole)
        quiest = self.cog.quiest
        mock_bdd.add_campsroles(10, 10)
        bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                   _role_slug="role7").add()
        bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2",
                   _role_slug="role8").add()
        bdd.Joueur(discord_id=3, chan_id_=31, nom="Joueur3",
                   _role_slug="role8").add()
        bdd.Joueur(discord_id=4, chan_id_=41, nom="Joueur4",
                   _role_slug="role8", statut=bdd.Statut.mort).add()

        # !quiest with non-existing nomrole
        ctx = mock_discord.get_ctx(quiest, nomrole="zzzzz")
        await ctx.invoke()
        ctx.assert_sent("")

        # !quiest with existing nomrole
        ctx = mock_discord.get_ctx(quiest, nomrole="role7")
        await ctx.invoke()
        ctx.assert_sent("Joueur1")

        # check several players & dead
        ctx = mock_discord.get_ctx(quiest, nomrole="role8")
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertIn("Joueur3", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur4", ctx.send.call_args.args[0])


    @mock_bdd.patch_db      # Empty database for this method
    async def test_menu(self):
        """Unit tests for !menu command."""
        # async def menu(self, ctx)
        menu = self.cog.menu
        mock_bdd.add_campsroles(10, 10)
        joueur = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                            _role_slug="role7")
        joueur.add()

        # no vote nor actions
        ctx = mock_discord.get_ctx(menu, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("MENU", ctx.send.call_args.args[0])
        self.assertIn("Aucun vote en cours", ctx.send.call_args.args[0])
        self.assertIn("Aucune action en cours", ctx.send.call_args.args[0])

        # all votes, no actions
        joueur.vote_condamne_ = "zoopla"
        joueur.vote_maire_ = "zooplo"
        joueur.vote_loups_ = "zoopli"
        joueur.update()
        ctx = mock_discord.get_ctx(menu, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        sent = ctx.send.call_args.args[0]
        self.assertIn("Vote pour le bûcher en cours", sent)
        self.assertIn("Vote pour le maire en cours", sent)
        self.assertIn("Vote des loups en cours", sent)
        self.assertIn("zoopla", sent)
        self.assertIn("zooplo", sent)
        self.assertIn("zoopli", sent)
        self.assertIn("Aucune action en cours", sent)

        # all votes, one action but closed
        bdd.BaseAction(slug="ouiZ", trigger_debut=bdd.ActionTrigger.perma,
                       trigger_fin=bdd.ActionTrigger.perma).add()
        action = bdd.Action(joueur=joueur, _base_slug="ouiZ")
        action.add()
        ctx = mock_discord.get_ctx(menu, _caller_id=1)
        await ctx.invoke()
        ctx.assert_sent("Aucune action en cours")

        # all votes, one action
        action.decision_ = "neIn"
        ctx = mock_discord.get_ctx(menu, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        sent = ctx.send.call_args.args[0]
        self.assertIn("Action en cours", sent)
        self.assertIn("ouiZ", sent)
        self.assertIn("neIn", sent)

        # all votes, two actions
        bdd.BaseAction(slug="JaJaJa", trigger_debut=bdd.ActionTrigger.mot_mjs,
                       trigger_fin=bdd.ActionTrigger.perma).add()
        bdd.Action(joueur=joueur, _base_slug="JaJaJa", decision_="o0ps").add()
        ctx = mock_discord.get_ctx(menu, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        sent = ctx.send.call_args.args[0]
        self.assertIn("Action en cours", sent)
        self.assertIn("JaJaJa", sent)
        self.assertIn("o0ps", sent)


    @mock_bdd.patch_db      # Empty database for this method
    async def test_infos(self):
        """Unit tests for !infos command."""
        # async def infos(self, ctx)
        infos = self.cog.infos
        mock_bdd.add_campsroles(10, 10)
        joueur = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                            _role_slug="role7")
        joueur.add()

        # no actions
        ctx = mock_discord.get_ctx(infos, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Role7", ctx.send.call_args.args[0])
        self.assertIn("role7", ctx.send.call_args.args[0])
        self.assertIn("Aucune action disponible", ctx.send.call_args.args[0])

        # one action
        bdd.BaseAction(slug="ouiZ", trigger_debut=bdd.ActionTrigger.perma,
                       trigger_fin=bdd.ActionTrigger.perma).add()
        bdd.Action(joueur=joueur, _base_slug="ouiZ").add()
        ctx = mock_discord.get_ctx(infos, _caller_id=1)
        await ctx.invoke()
        ctx.assert_sent("ouiZ")

        # test every triggers
        names = []
        for trigger in bdd.ActionTrigger:
            name = f"test{trigger.name}"
            bdd.BaseAction(slug=name, trigger_debut=trigger,
                           trigger_fin=trigger).add()
            bdd.Action(joueur=joueur, _base_slug=name).add()
            names.append(name)
        ctx = mock_discord.get_ctx(infos, _caller_id=1)
        await ctx.invoke()
        ctx.send.assert_called_once()
        for name in names:
            self.assertIn(name, ctx.send.call_args.args[0])


    @mock_bdd.patch_db      # Empty database for this method
    async def test_vivants_morts(self):
        """Unit tests for !vivants and !morts commands."""
        # async def vivants(self, ctx)
        # async def morts(self, ctx)
        vivants = self.cog.vivants
        morts = self.cog.morts

        # no players
        ctx = mock_discord.get_ctx(vivants)
        await ctx.invoke()
        ctx.send.assert_called_once()

        ctx = mock_discord.get_ctx(morts)
        await ctx.invoke()
        ctx.send.assert_called_once()

        # vivants only
        mock_bdd.add_campsroles()
        bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur1",
                   statut=bdd.Statut.vivant).add()
        bdd.Joueur(discord_id=2, chan_id_=21, nom="Joueur2",
                   chambre="ch2", statut=bdd.Statut.vivant).add()

        ctx = mock_discord.get_ctx(vivants)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Joueur1", ctx.send.call_args.args[0])
        self.assertIn("Joueur2", ctx.send.call_args.args[0])
        self.assertIn("ch2", ctx.send.call_args.args[0])

        ctx = mock_discord.get_ctx(morts)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertNotIn("Joueur1", ctx.send.call_args.args[0])

        # all status
        bdd.Joueur(discord_id=3, chan_id_=31, nom="Joueur3",
                   statut=bdd.Statut.mort).add()
        bdd.Joueur(discord_id=4, chan_id_=41, nom="Joueur4",
                   chambre="ch4", statut=bdd.Statut.mort).add()
        bdd.Joueur(discord_id=5, chan_id_=51, nom="Joueur5",
                   statut=bdd.Statut.MV).add()
        bdd.Joueur(discord_id=6, chan_id_=61, nom="Joueur6",
                   statut=bdd.Statut.immortel).add()

        ctx = mock_discord.get_ctx(vivants)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertNotIn("Joueur3", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur4", ctx.send.call_args.args[0])
        self.assertNotIn("ch4", ctx.send.call_args.args[0])
        self.assertIn("Joueur5", ctx.send.call_args.args[0])
        self.assertIn("Joueur6", ctx.send.call_args.args[0])

        ctx = mock_discord.get_ctx(morts)
        await ctx.invoke()
        ctx.send.assert_called_once()
        self.assertIn("Joueur3", ctx.send.call_args.args[0])
        self.assertIn("Joueur4", ctx.send.call_args.args[0])
        self.assertNotIn("ch4", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur5", ctx.send.call_args.args[0])
        self.assertNotIn("Joueur6", ctx.send.call_args.args[0])

        # more players
        for i in range(100):
            bdd.Joueur(discord_id=100+i, chan_id_=i, nom=f"Joueur{100+i}",
                       chambre=f"ch{100+i}", statut=bdd.Statut.vivant).add()
            bdd.Joueur(discord_id=200+i, chan_id_=i, nom=f"Joueur{200+i}",
                       statut=bdd.Statut.mort).add()

        ctx = mock_discord.get_ctx(vivants)
        await ctx.invoke()
        ctx.send.assert_called()
        sent = "\n".join(call.args[0] for call in ctx.send.call_args_list)
        for i in range(100):
            self.assertIn(f"Joueur{100+i}", sent)
            self.assertIn(f"ch{100+i}", sent)

        ctx = mock_discord.get_ctx(morts)
        await ctx.invoke()
        ctx.send.assert_called()
        sent = "\n".join(call.args[0] for call in ctx.send.call_args_list)
        for i in range(100):
            self.assertIn(f"Joueur{200+i}", sent)
