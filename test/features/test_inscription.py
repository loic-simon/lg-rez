import datetime
import unittest
from unittest import mock

import discord
import freezegun

from lgrez import config, bdd
from lgrez.features import inscription
from lgrez.blocs import gsheets
from test import mock_discord, mock_bdd, mock_env


class TestInscriptionFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.inscription functions."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()


    @mock.patch("lgrez.blocs.tools.channel")
    async def test_new_channel(self, ch_patch):
        """Unit tests for inscription.new_channel function."""
        # async def new_channel(member)
        new_channel = inscription.new_channel
        categ = mock.MagicMock(discord.CategoryChannel)

        # < 50 channels
        categ.channels = [0]*49
        ch_patch.return_value = categ
        member = mock.MagicMock(discord.Member)
        member.guild.create_text_channel = mock.AsyncMock()
        chan = await new_channel(member)
        ch_patch.assert_called_once()
        member.guild.create_text_channel.assert_called_once_with(
            f"{config.private_chan_prefix}{member.name}",
            topic=str(member.id), category=categ
        )
        chan.set_permissions.assert_called_once_with(
            member, read_messages=True, send_messages=True
        )
        ch_patch.reset_mock()

        # 50 <= channels < 100, cat 2 déjà existante
        categ.channels = [0]*50
        categ2 = mock.MagicMock(discord.CategoryChannel)
        categ2.channels = [0]*49
        ch_patch.side_effect = [categ, categ2]
        member = mock.MagicMock(discord.Member)
        member.guild.create_text_channel = mock.AsyncMock()
        chan = await new_channel(member)
        ch_patch.assert_called()
        self.assertEqual(ch_patch.call_count, 2)
        categ.clone.assert_not_called()
        self.assertEqual([call.args[0] for call in ch_patch.call_args_list],
                         [f"{config.private_chan_category_name}",
                          f"{config.private_chan_category_name} 2"])
        member.guild.create_text_channel.assert_called_once_with(
            f"{config.private_chan_prefix}{member.name}",
            topic=str(member.id), category=categ2
        )
        chan.set_permissions.assert_called_once_with(
            member, read_messages=True, send_messages=True
        )
        ch_patch.reset_mock()

        # 50 <= channels < 100, cat 2 non existante
        ch_patch.side_effect = [categ, None]
        member = mock.MagicMock(discord.Member)
        member.guild.create_text_channel = mock.AsyncMock()
        chan = await new_channel(member)
        ch_patch.assert_called()
        self.assertEqual(ch_patch.call_count, 2)
        categ.clone.assert_called_once_with(
            name=f"{config.private_chan_category_name} 2"
        )
        self.assertEqual([call.args[0] for call in ch_patch.call_args_list],
                         [f"{config.private_chan_category_name}",
                          f"{config.private_chan_category_name} 2"])
        member.guild.create_text_channel.assert_called_once_with(
            f"{config.private_chan_prefix}{member.name}",
            topic=str(member.id), category=categ.clone.return_value
        )
        chan.set_permissions.assert_called_once_with(
            member, read_messages=True, send_messages=True
        )
        ch_patch.reset_mock()
        categ.clone.reset_mock()

        # 100 <= channels, cat 3 déjà existante
        categ2.channels = [0]*50
        categ3 = mock.MagicMock(discord.CategoryChannel)
        categ3.channels = [0]*49
        ch_patch.side_effect = [categ, categ2, categ3]
        member = mock.MagicMock(discord.Member)
        member.guild.create_text_channel = mock.AsyncMock()
        chan = await new_channel(member)
        ch_patch.assert_called()
        self.assertEqual(ch_patch.call_count, 3)
        categ.clone.assert_not_called()
        self.assertEqual([call.args[0] for call in ch_patch.call_args_list],
                         [f"{config.private_chan_category_name}",
                          f"{config.private_chan_category_name} 2",
                          f"{config.private_chan_category_name} 3"])
        member.guild.create_text_channel.assert_called_once_with(
            f"{config.private_chan_prefix}{member.name}",
            topic=str(member.id), category=categ3
        )
        chan.set_permissions.assert_called_once_with(
            member, read_messages=True, send_messages=True
        )
        ch_patch.reset_mock()

        # 100 <= channels, cat 3 non existante
        ch_patch.side_effect = [categ, categ2, None]
        member = mock.MagicMock(discord.Member)
        member.guild.create_text_channel = mock.AsyncMock()
        chan = await new_channel(member)
        ch_patch.assert_called()
        self.assertEqual(ch_patch.call_count, 3)
        categ.clone.assert_called_once_with(
            name=f"{config.private_chan_category_name} 3"
        )
        self.assertEqual([call.args[0] for call in ch_patch.call_args_list],
                         [f"{config.private_chan_category_name}",
                          f"{config.private_chan_category_name} 2",
                          f"{config.private_chan_category_name} 3"])
        member.guild.create_text_channel.assert_called_once_with(
            f"{config.private_chan_prefix}{member.name}",
            topic=str(member.id), category=categ.clone.return_value
        )
        chan.set_permissions.assert_called_once_with(
            member, read_messages=True, send_messages=True
        )


    @mock_env.patch_env(LGREZ_TDB_SHEET_ID="bzoulip!")
    @mock.patch("lgrez.blocs.gsheets.connect")
    @mock.patch("lgrez.blocs.gsheets.update")
    async def test_register_on_tdb(self, gupdate_patch, gconnect_patch):
        """Unit tests for inscription.register_on_tdb function."""
        # def register_on_tdb(joueur)
        register_on_tdb = inscription.register_on_tdb
        config.tdb_main_sheet = "uéué"
        config.tdb_header_row = 7
        config.tdb_id_column = "C"
        config.tdb_main_columns = ("O", "V")
        config.tdb_tampon_columns = ("E", "L")

        jr = mock.Mock()

        # mauvaise colonne primaire
        values = [0]*6 + [[0, 0, "bizzp"]]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        with self.assertRaises(ValueError) as cm:
            register_on_tdb(jr)
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        self.assertIn("`C7` vaut `bizzp`", cm.exception.args[0])
        self.assertIn(bdd.Joueur.primary_col.key, cm.exception.args[0])
        gupdate_patch.assert_not_called()

        # mauvaise colonne
        values = [0]*6 + [[0, 0, bdd.Joueur.primary_col.key, "d", "e", "f",
                           "g", "h", "i", "j", "k", "l", "m", "n", "koko"]]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        with self.assertRaises(ValueError) as cm:
            register_on_tdb(jr)
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        self.assertIn("`koko` n'est pas une colonne", cm.exception.args[0])
        gupdate_patch.assert_not_called()

        # mauvais tampon
        values = [0]*6 + [[0, 0, bdd.Joueur.primary_col.key, "d", "koko",
                           "f", "g", "h", "i", "j", "k", "l", "m", "n", "nom",
                           "chambre", "statut", "role", "camp",
                           "votant_village", "votant_loups", "role_actif",
                            "koko"]]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        with self.assertRaises(ValueError) as cm:
            register_on_tdb(jr)
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        self.assertIn("koko", cm.exception.args[0])
        self.assertIn("n'est pas une colonne", cm.exception.args[0])
        gupdate_patch.assert_not_called()

        # aucun joueur inscrit sur le TDB
        values = [0]*6 + [
            [0, 0, bdd.Joueur.primary_col.key, "d", "tampon_nom",
                "tampon_chambre", "tampon_statut", "tampon_role",
                "tampon_camp", "tampon_votant_village", "tampon_votant_loups",
                "tampon_role_actif", "m", "n", "nom", "chambre", "statut",
                "role", "camp", "votant_village", "votant_loups", "role_actif",
                "koko"],
        ]
        base = values
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        register_on_tdb(jr)
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        gupdate_patch.assert_called_once()
        usheet, *modifs = gupdate_patch.call_args.args
        self.assertEqual(usheet, sheet)
        mods = {
            gsheets.Modif(7, 2, jr.discord_id),
            gsheets.Modif(7, 4, jr.nom), gsheets.Modif(7, 14, jr.nom),
            gsheets.Modif(7, 5, jr.chambre), gsheets.Modif(7, 15, jr.chambre),
            gsheets.Modif(7, 6, jr.statut), gsheets.Modif(7, 16, jr.statut),
            gsheets.Modif(7, 7, jr.role), gsheets.Modif(7, 17, jr.role),
            gsheets.Modif(7, 8, jr.camp), gsheets.Modif(7, 18, jr.camp),
            gsheets.Modif(7, 9, jr.votant_village),
            gsheets.Modif(7, 19, jr.votant_village),
            gsheets.Modif(7, 10, jr.votant_loups),
            gsheets.Modif(7, 20, jr.votant_loups),
            gsheets.Modif(7, 11, jr.role_actif),
            gsheets.Modif(7, 21, jr.role_actif),
        }
        self.assertEqual(mods, set(modifs))
        gupdate_patch.reset_mock()

        # junk en dessous du header
        values = base + [
            [0, 0, "brzzz"],
            [0, 0, "brozozoz"],
        ]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        register_on_tdb(jr)
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        gupdate_patch.assert_called_once()
        usheet, *modifs = gupdate_patch.call_args.args
        self.assertEqual(usheet, sheet)
        mods = {
            gsheets.Modif(7, 2, jr.discord_id),
            gsheets.Modif(7, 4, jr.nom), gsheets.Modif(7, 14, jr.nom),
            gsheets.Modif(7, 5, jr.chambre), gsheets.Modif(7, 15, jr.chambre),
            gsheets.Modif(7, 6, jr.statut), gsheets.Modif(7, 16, jr.statut),
            gsheets.Modif(7, 7, jr.role), gsheets.Modif(7, 17, jr.role),
            gsheets.Modif(7, 8, jr.camp), gsheets.Modif(7, 18, jr.camp),
            gsheets.Modif(7, 9, jr.votant_village),
            gsheets.Modif(7, 19, jr.votant_village),
            gsheets.Modif(7, 10, jr.votant_loups),
            gsheets.Modif(7, 20, jr.votant_loups),
            gsheets.Modif(7, 11, jr.role_actif),
            gsheets.Modif(7, 21, jr.role_actif),
        }
        self.assertEqual(mods, set(modifs))
        gupdate_patch.reset_mock()

        # 3 joueurs inscrits
        values = base + [
            [0, 0, "1351"],
            [0, 0, "313"],
            [0, 0, "1101"],
            [0, 0, "junk"],
        ]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        register_on_tdb(jr)
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        gupdate_patch.assert_called_once()
        usheet, *modifs = gupdate_patch.call_args.args
        self.assertEqual(usheet, sheet)
        mods = {
            gsheets.Modif(10, 2, jr.discord_id),
            gsheets.Modif(10, 4, jr.nom), gsheets.Modif(10, 14, jr.nom),
            gsheets.Modif(10, 5, jr.chambre),
            gsheets.Modif(10, 15, jr.chambre),
            gsheets.Modif(10, 6, jr.statut), gsheets.Modif(10, 16, jr.statut),
            gsheets.Modif(10, 7, jr.role), gsheets.Modif(10, 17, jr.role),
            gsheets.Modif(10, 8, jr.camp), gsheets.Modif(10, 18, jr.camp),
            gsheets.Modif(10, 9, jr.votant_village),
            gsheets.Modif(10, 19, jr.votant_village),
            gsheets.Modif(10, 10, jr.votant_loups),
            gsheets.Modif(10, 20, jr.votant_loups),
            gsheets.Modif(10, 11, jr.role_actif),
            gsheets.Modif(10, 21, jr.role_actif),
        }
        self.assertEqual(mods, set(modifs))


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.inscription.new_channel")
    @mock.patch("lgrez.features.inscription.register_on_tdb")
    @mock.patch("lgrez.blocs.tools.sleep")
    async def test_main(self, sleep_patch, reg_patch, newchan_patch):
        """Unit tests for inscription.main function."""
        # async def main(member)
        main = inscription.main
        mock_bdd.add_campsroles()

        joueur1 = bdd.Joueur(discord_id=1, chan_id_=11, nom="Joueur 1")
        joueur1.add()

        newchan_patch.return_value = mock_discord.chan("bzzt", id=798)

        # Joueur inscrit en base
        with mock_discord.mock_members_and_chans(joueur1):
            member = joueur1.member
            chan = joueur1.private_chan
            await main(member)
        chan.set_permissions.assert_called_once_with(
            member, read_messages=True, send_messages=True
        )
        mock_discord.assert_sent(chan, f"{member.mention} tu es déjà inscrit")
        reg_patch.assert_not_called()
        newchan_patch.assert_not_called()
        sleep_patch.assert_not_called()
        joueur1.delete()

        # Joueur en cours d'inscription -> abort
        chan = mock_discord.chan("bzz", topic="123456")
        config.guild.text_channels = [chan]
        member = mock.Mock(discord.Member, id=123456)
        with mock_discord.interact(("yes_no", False)):
            await main(member)
        chan.set_permissions.assert_called_once_with(
            member, read_messages=True, send_messages=True
        )
        mock_discord.assert_sent(chan, f"{member.mention}, par ici",
                                 f"Bienvenue {member.mention}",
                                 f"finalisons ton inscription",
                                 f"C'est bon pour toi ?",
                                 "Pas de soucis")
        reg_patch.assert_not_called()
        newchan_patch.assert_not_called()
        sleep_patch.assert_called()
        sleep_patch.reset_mock()

        # Joueur arrivant -> abort
        member = mock.Mock(discord.Member, id=145)
        with mock_discord.interact(("yes_no", False)):
            await main(member)
        newchan_patch.assert_called_once_with(member)
        chan = newchan_patch.return_value
        mock_discord.assert_sent(chan, f"Bienvenue {member.mention}",
                                 f"finalisons ton inscription",
                                 f"C'est bon pour toi ?",
                                 "Pas de soucis")
        reg_patch.assert_not_called()
        newchan_patch.reset_mock()
        sleep_patch.assert_called()
        sleep_patch.reset_mock()

        # Joueur arrivant -> ok -> name -> troll -> good name
        # demande_chambre False
        config.demande_chambre = False
        member = mock.Mock(discord.Member, id=145)
        member.top_role.__lt__ = lambda s, o: True  # role < MJ
        member.display_name = "Pr-Z N0 N"
        with mock_discord.interact(
            ("yes_no", True),
            ("wait_for_message", mock.NonCallableMock(discord.Message,
                                                      content="préz")),
            ("wait_for_message", mock.NonCallableMock(discord.Message,
                                                      content="no n")),
            ("yes_no", False),
            ("wait_for_message", mock.NonCallableMock(discord.Message,
                                                      content="pr-z")),
            ("wait_for_message", mock.NonCallableMock(discord.Message,
                                                      content="n0 n")),
            ("yes_no", True),
        ):
            await main(member)
        newchan_patch.assert_called_once_with(member)
        chan = newchan_patch.return_value
        mock_discord.assert_sent(
            chan, f"Bienvenue {member.mention}", "finalisons ton inscription",
            f"C'est bon pour toi ?", ["Parfait", "prénom"], "prénom",
            "nom de famille", "Préz No N", "prénom", "nom de famille",
            "Pr-Z N0 N", "Je t'ai renommé", "Je t'inscris",
            "Tu es maintenant inscrit", "quelques dernières choses",
            "c'est tout bon"
        )
        chan.edit.assert_any_call(
            name=f"{config.private_chan_prefix}Pr-Z N0 N"
        )
        member.edit.assert_called_once_with(nick="Pr-Z N0 N")
        member.edit.reset_mock()
        self.assertEqual(len(bdd.Joueur.query.all()), 1)
        jr = bdd.Joueur.query.one()
        self.assertEqual(
            [jr.discord_id, jr.chan_id_, jr.nom, jr.chambre, jr.statut,
             jr.role, jr.camp, jr.votant_village, jr.votant_loups,
             jr.role_actif],
            [145, 798, "Pr-Z N0 N", None, bdd.Statut.vivant,
             bdd.Role.default(), bdd.Camp.default(), True, False, False]
        )
        member.add_roles.assert_called_once_with(config.Role.joueur_en_vie)
        chan.edit.assert_any_call(topic=mock.ANY)
        reg_patch.assert_called_once_with(jr)
        reg_patch.reset_mock()
        newchan_patch.reset_mock()
        sleep_patch.assert_called()
        sleep_patch.reset_mock()
        jr.delete()

        # Joueur arrivant -> ok -> name -> chambre -> pas à la Rez
        config.demande_chambre = True
        member = mock.Mock(discord.Member, id=145)
        member.top_role.__lt__ = lambda s, o: True  # role < MJ
        member.display_name = "Pr-Z N0 N"
        with mock_discord.interact(
            ("yes_no", True),
            ("wait_for_message", mock.NonCallableMock(discord.Message,
                                                      content="pr-z")),
            ("wait_for_message", mock.NonCallableMock(discord.Message,
                                                      content="n0 n")),
            ("yes_no", True),
            ("yes_no", False),
        ):
            await main(member)
        newchan_patch.assert_called_once_with(member)
        chan = newchan_patch.return_value
        mock_discord.assert_sent(
            chan, f"Bienvenue {member.mention}", "finalisons ton inscription",
            f"C'est bon pour toi ?", ["Parfait", "prénom"], "prénom",
            "nom de famille",
            "Pr-Z N0 N", "Je t'ai renommé", "habites-tu à la Rez",
            "Je t'inscris", "Tu es maintenant inscrit",
            "quelques dernières choses", "c'est tout bon"
        )
        chan.edit.assert_any_call(
            name=f"{config.private_chan_prefix}Pr-Z N0 N"
        )
        member.edit.assert_called_once_with(nick="Pr-Z N0 N")
        member.edit.reset_mock()
        self.assertEqual(len(bdd.Joueur.query.all()), 1)
        jr = bdd.Joueur.query.one()
        self.assertEqual(
            [jr.discord_id, jr.chan_id_, jr.nom, jr.chambre, jr.statut,
             jr.role, jr.camp, jr.votant_village, jr.votant_loups,
             jr.role_actif],
            [145, 798, "Pr-Z N0 N", config.chambre_mj, bdd.Statut.vivant,
             bdd.Role.default(), bdd.Camp.default(), True, False, False]
        )
        member.add_roles.assert_called_once_with(config.Role.joueur_en_vie)
        chan.edit.assert_any_call(topic=mock.ANY)
        reg_patch.assert_called_once_with(jr)
        reg_patch.reset_mock()
        newchan_patch.reset_mock()
        sleep_patch.assert_called()
        sleep_patch.reset_mock()
        jr.delete()

        # Joueur arrivant -> ok -> name -> chambre -> à la Rez
        config.demande_chambre = True
        member = mock.Mock(discord.Member, id=145)
        member.top_role.__lt__ = lambda s, o: True  # role < MJ
        member.display_name = "Pr-Z N0 N"
        with mock_discord.interact(
            ("yes_no", True),
            ("wait_for_message", mock.NonCallableMock(discord.Message,
                                                      content="pr-z")),
            ("wait_for_message", mock.NonCallableMock(discord.Message,
                                                      content="n0 n")),
            ("yes_no", True),
            ("yes_no", True),
            ("wait_for_message", mock.NonCallableMock(discord.Message,
                                                      content="214")),
        ):
            await main(member)
        newchan_patch.assert_called_once_with(member)
        chan = newchan_patch.return_value
        mock_discord.assert_sent(
            chan, f"Bienvenue {member.mention}", "finalisons ton inscription",
            f"C'est bon pour toi ?", ["Parfait", "prénom"], "prénom",
            "nom de famille",
            "Pr-Z N0 N", "Je t'ai renommé", "habites-tu à la Rez",
            "quelle est ta chambre", "Je t'inscris",
            "Tu es maintenant inscrit", "quelques dernières choses",
            "c'est tout bon"
        )
        chan.edit.assert_any_call(
            name=f"{config.private_chan_prefix}Pr-Z N0 N"
        )
        member.edit.assert_called_once_with(nick="Pr-Z N0 N")
        member.edit.reset_mock()
        self.assertEqual(len(bdd.Joueur.query.all()), 1)
        jr = bdd.Joueur.query.one()
        self.assertEqual(
            [jr.discord_id, jr.chan_id_, jr.nom, jr.chambre, jr.statut,
             jr.role, jr.camp, jr.votant_village, jr.votant_loups,
             jr.role_actif],
            [145, 798, "Pr-Z N0 N", "214", bdd.Statut.vivant,
             bdd.Role.default(), bdd.Camp.default(), True, False, False]
        )
        member.add_roles.assert_called_once_with(config.Role.joueur_en_vie)
        chan.edit.assert_any_call(topic=mock.ANY)
        reg_patch.assert_called_once_with(jr)
        reg_patch.reset_mock()
        newchan_patch.reset_mock()
        sleep_patch.assert_called()
        sleep_patch.reset_mock()
        jr.delete()
