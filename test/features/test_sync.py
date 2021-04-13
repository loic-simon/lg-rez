import datetime
import enum
import unittest
from unittest import mock

import sqlalchemy

from lgrez import config, bdd
from lgrez.features import sync
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


class TestSyncFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.sync utility functions."""

    def setUp(self):
        mock_discord.mock_config()
        config.tdb_main_sheet = "uéué"
        config.tdb_header_row = 7
        config.tdb_id_column = "C"
        config.tdb_main_columns = ("L", "P")
        config.tdb_tampon_columns = ("E", "I")

    def tearDown(self):
        mock_discord.unmock_config()

    @mock_bdd.patch_db      # Empty database for this method
    def test_transtype(self):
        """Unit tests for sync.transtype function."""
        # def transtype(value, col)
        transtype = sync.transtype
        mock_bdd.add_campsroles(2, 2)
        reac = bdd.Reaction(id=17, reponse="uiz")
        reac.add()
        # Table
        tab = bdd.Role                              # type String
        self.assertRaises(ValueError, transtype, None, tab)
        self.assertRaises(ValueError, transtype, 13, tab)
        self.assertRaises(ValueError, transtype, "role3", tab)
        self.assertEqual(bdd.Role.query.get("role1"), transtype("role1", tab))
        # Relationship
        rel = bdd.Joueur.attrs["role"]              # type String
        self.assertRaises(ValueError, transtype, None, rel)
        self.assertRaises(ValueError, transtype, 13, rel)
        self.assertRaises(ValueError, transtype, "role3", rel)
        self.assertEqual(bdd.Role.query.get("role1"), transtype("role1", rel))
        rel = bdd.Trigger.attrs["reaction"]         # type Integer
        self.assertRaises(ValueError, transtype, None, rel)
        self.assertRaises(ValueError, transtype, "bzzt", rel)
        self.assertRaises(ValueError, transtype, 13, rel)
        self.assertEqual(reac, transtype(17, rel))
        # None, colonne non nullable
        nonnull = sqlalchemy.Column("bzzt", sqlalchemy.String, nullable=False)
        self.assertRaises(ValueError, transtype, None, nonnull)
        self.assertRaises(ValueError, transtype, "", nonnull)
        self.assertRaises(ValueError, transtype, "None", nonnull)
        # None, colonne nullable
        null = sqlalchemy.Column("bzzt", sqlalchemy.String, nullable=True)
        self.assertIs(None, transtype(None, null))
        self.assertIs(None, transtype("", null))
        self.assertIs(None, transtype("None", null))
        # String
        strcol = sqlalchemy.Column("bzzt", sqlalchemy.String)
        self.assertEqual("42", transtype(42, strcol))
        self.assertEqual("{42: 43}", transtype({42: 43}, strcol))
        self.assertEqual(str(self), transtype(self, strcol))
        # Integer
        intcol = sqlalchemy.Column("bzzt", sqlalchemy.Integer)
        intcol2 = sqlalchemy.Column("bzzt", sqlalchemy.BigInteger)
        self.assertEqual(42, transtype("42", intcol))
        self.assertRaises(ValueError, transtype, "bz", intcol)
        self.assertEqual(42, transtype("42", intcol2))
        # Boolean
        boolcol = sqlalchemy.Column("bzzt", sqlalchemy.Boolean)
        self.assertIs(True, transtype(True, boolcol))
        self.assertIs(True, transtype(1, boolcol))
        self.assertIs(True, transtype("True", boolcol))
        self.assertIs(True, transtype("VRAI", boolcol))
        self.assertIs(False, transtype(False, boolcol))
        self.assertIs(False, transtype(0, boolcol))
        self.assertIs(False, transtype("False", boolcol))
        self.assertIs(False, transtype("FAUX", boolcol))
        self.assertRaises(ValueError, transtype, "bz", boolcol)
        # Time
        timecol = sqlalchemy.Column("bzzt", sqlalchemy.Time)
        self.assertEqual(datetime.time(13, 12), transtype("13:12", timecol))
        self.assertEqual(datetime.time(3, 1), transtype("3:1", timecol))
        self.assertEqual(datetime.time(3, 1), transtype("03:01", timecol))
        self.assertEqual(datetime.time(13, 12), transtype("13:12:15", timecol))
        self.assertRaises(ValueError, transtype, "bz", boolcol)
        # Enum
        class TestEnum(enum.Enum):
            bak = 1
            booz = 2
        enumcol = sqlalchemy.Column("bzzt", sqlalchemy.Enum(TestEnum))
        self.assertEqual(TestEnum.bak, transtype("bak", enumcol))
        self.assertEqual(TestEnum["booz"], transtype("booz", enumcol))
        self.assertRaises(ValueError, transtype, "bz", enumcol)
        # Other type
        strangecol = sqlalchemy.Column("bzzt", sqlalchemy.PickleType)
        self.assertRaises(ValueError, transtype, "bz", boolcol)


    @mock_bdd.patch_db      # Empty database for this method
    @mock_env.patch_env(LGREZ_TDB_SHEET_ID="bzoulip!")
    @mock.patch("lgrez.blocs.gsheets.connect")
    def test_get_sync(self, gconnect_patch):
        """Unit tests for sync.get_sync function."""
        # def get_sync()
        get_sync = sync.get_sync
        mock_bdd.add_campsroles(10, 10)
        bdd.Joueur.add(*base_joueurs())

        # mauvaise colonne primaire
        values = [0]*6 + [[0, 0, "bizzp"]]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        with self.assertRaises(ValueError) as cm:
            get_sync()
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        self.assertIn("`C7` vaut `bizzp`", cm.exception.args[0])
        self.assertIn(bdd.Joueur.primary_col.key, cm.exception.args[0])

        # mauvaise colonne
        values = [0]*6 + [[0, 0, bdd.Joueur.primary_col.key, "d", "e", "f",
                           "g", "h", "i", "j", "k", "koko"]]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        with self.assertRaises(ValueError) as cm:
            get_sync()
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        self.assertIn("`koko` n'est pas une colonne", cm.exception.args[0])

        # mauvais tampon
        values = [0]*6 + [[0, 0, bdd.Joueur.primary_col.key, "d", "koko",
                           "f", "g", "h", "i", "j", "k", "nom", "chambre",
                           "role", "camp", "statut", "koko"]]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        with self.assertRaises(ValueError) as cm:
            get_sync()
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        self.assertIn("koko", cm.exception.args[0])
        self.assertIn("n'est pas une colonne", cm.exception.args[0])

        # aucun joueur inscrit sur le TDB ==> delete all
        values = [0]*6 + [
            [0, 0, bdd.Joueur.primary_col.key, "d", "tampon_nom",
                "tampon_chambre", "tampon_role", "tampon_camp",
                "tampon_statut", "j", "k", "nom", "chambre", "role",
                "camp", "statut", "koko"],
        ]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        modifs = get_sync()
        self.assertEqual(modifs, [])        # renvoie une liste vide
        self.assertEqual(bdd.Joueur.query.all(), [])    # tout delete
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()

        # joueur hors base ==> delete all others + error
        bdd.Joueur.add(*base_joueurs())
        values = [0]*6 + [
            [0, 0, bdd.Joueur.primary_col.key, "d", "tampon_nom",
                "tampon_chambre", "tampon_role", "tampon_camp",
                "tampon_statut", "j", "k", "nom", "chambre", "role",
                "camp", "statut", "koko"],
            [0, 0, "notANumberSoWillBeSkipped"],
            [0, 0, "123", "d", "oui", "214", "role2", "camp2", "mort",
                "j", "k", "oui", "214", "role2", "camp2", "mort"],
        ]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        with self.assertRaises(ValueError) as cm:
           get_sync()
        self.assertEqual(bdd.Joueur.query.all(), [])    # tout delete
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()
        self.assertIn("Joueur `oui` hors base", cm.exception.args[0])

        # 0 modifs
        bdd.Joueur.add(*base_joueurs())
        values = [0]*6 + [
            [0, 0, bdd.Joueur.primary_col.key, "d", "tampon_nom",
                "tampon_chambre", "tampon_role", "tampon_camp",
                "tampon_statut", "j", "k", "nom", "chambre", "role",
                "camp", "statut", "koko"],
            [0, 0, "notANumberSoWillBeSkipped"],
            [0, 0, "1", "d", "Joueur1", "Ch1", "nonattr", "nonattr", "vivant",
                "j", "k", "Joueur1", "Ch1", "nonattr", "nonattr", "vivant"],
            [0, 0, "2", "d", "Joueur2", "Ch2", "role2", "camp2", "mort",
                "j", "k", "Joueur2", "Ch2", "role2", "camp2", "mort"],
            [0, 0, "3", "d", "Joueur3", "Ch3", "role3", "camp3", "MV",
                "j", "k", "Joueur3", "Ch3", "role3", "camp3", "MV"],
            [0, 0, "4", "d", "Joueur4", "Ch4", "role4", "camp4", "immortel",
                "j", "k", "Joueur4", "Ch4", "role4", "camp4", "immortel"],
        ]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        modifs = get_sync()
        self.assertEqual(modifs, [])        # renvoie une liste vide
        self.assertEqual(len(bdd.Joueur.query.all()), 4)    # no delete
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()

        # 1 modif pour 1 joueur
        values = [0]*6 + [
            [0, 0, bdd.Joueur.primary_col.key, "d", "tampon_nom",
                "tampon_chambre", "tampon_role", "tampon_camp",
                "tampon_statut", "j", "k", "nom", "chambre", "role",
                "camp", "statut", "koko"],
            [0, 0, "notANumberSoWillBeSkipped"],
            [0, 0, "1", "d", "Joueur1", "Ch1", "nonattr", "nonattr", "vivant",
                "j", "k", "Joueur1", "Ch1", "nonattr", "nonattr", "vivant"],
            [0, 0, "2", "d", "Joueur2", "Ch2", "role2", "camp2", "mort",
                "j", "k", "Joueur2", "Ch2.1", "role2", "camp2", "mort"],
            [0, 0, "3", "d", "Joueur3", "Ch3", "role3", "camp3", "MV",
                "j", "k", "Joueur3", "Ch3", "role3", "camp3", "MV"],
            [0, 0, "4", "d", "Joueur4", "Ch4", "role4", "camp4", "immortel",
                "j", "k", "Joueur4", "Ch4", "role4", "camp4", "immortel"],
        ]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        modifs = get_sync()
        self.assertEqual(modifs, [sync.TDBModif(2, "chambre", "Ch2.1", 9, 5)])
        self.assertEqual(len(bdd.Joueur.query.all()), 4)    # no delete
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()

        # 5 modifs pour 1 joueur
        values = [0]*6 + [
            [0, 0, bdd.Joueur.primary_col.key, "d", "tampon_nom",
                "tampon_chambre", "tampon_role", "tampon_camp",
                "tampon_statut", "j", "k", "nom", "chambre", "role",
                "camp", "statut", "koko"],
            [0, 0, "notANumberSoWillBeSkipped"],
            [0, 0, "1", "d", "Joueur1", "Ch1", "nonattr", "nonattr", "vivant",
                "j", "k", "Joueur1", "Ch1", "nonattr", "nonattr", "vivant"],
            [0, 0, "2", "d", "Joueur2", "Ch2", "role2", "camp2", "mort",
                "j", "k", "Joueur2.9", "Ch2.1", "role7", "camp9", "MV"],
            [0, 0, "3", "d", "Joueur3", "Ch3", "role3", "camp3", "MV",
                "j", "k", "Joueur3", "Ch3", "role3", "camp3", "MV"],
            [0, 0, "4", "d", "Joueur4", "Ch4", "role4", "camp4", "immortel",
                "j", "k", "Joueur4", "Ch4", "role4", "camp4", "immortel"],
        ]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        modifs = get_sync()
        self.assertEqual(modifs, [
            sync.TDBModif(2, "nom", "Joueur2.9", 9, 4),
            sync.TDBModif(2, "chambre", "Ch2.1", 9, 5),
            sync.TDBModif(2, "role", bdd.Role.query.get("role7"), 9, 6),
            sync.TDBModif(2, "camp", bdd.Camp.query.get("camp9"), 9, 7),
            sync.TDBModif(2, "statut", bdd.Statut.MV, 9, 8),
        ])
        self.assertEqual(len(bdd.Joueur.query.all()), 4)    # no delete
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()

        # 5 modifs pour 3 joueurs
        values = [0]*6 + [
            [0, 0, bdd.Joueur.primary_col.key, "d", "tampon_nom",
                "tampon_chambre", "tampon_role", "tampon_camp",
                "tampon_statut", "j", "k", "nom", "chambre", "role",
                "camp", "statut", "koko"],
            [0, 0, "notANumberSoWillBeSkipped"],
            [0, 0, "1", "d", "Joueur1", "Ch1", "nonattr", "nonattr", "vivant",
                "j", "k", "Joueur1", "Ch11", "nonattr", "nonattr", "vivant"],
            [0, 0, "2", "d", "Joueur2", "Ch2", "role2", "camp2", "mort",
                "j", "k", "Joueur2", "Ch2.1", "role7", "camp2", "MV"],
            [0, 0, "3", "d", "Joueur3", "Ch3", "role3", "camp3", "MV",
                "j", "k", "Joueur3", "Ch3", "role3", "camp3", "MV"],
            [0, 0, "4", "d", "Joueur4", "Ch4", "role4", "camp4", "immortel",
                "j", "k", "Joueur475", "Ch4", "role4", "camp4", "immortel"],
        ]
        sheet = mock.Mock(**{"get_all_values.return_value": values})
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        modifs = get_sync()
        self.assertEqual(modifs, [
            sync.TDBModif(1, "chambre", "Ch11", 8, 5),
            sync.TDBModif(2, "chambre", "Ch2.1", 9, 5),
            sync.TDBModif(2, "role", bdd.Role.query.get("role7"), 9, 6),
            sync.TDBModif(2, "statut", bdd.Statut.MV, 9, 8),
            sync.TDBModif(4, "nom", "Joueur475", 11, 4),
        ])
        self.assertEqual(len(bdd.Joueur.query.all()), 4)    # no delete
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gconnect_patch.reset_mock()


    @mock_env.patch_env(LGREZ_TDB_SHEET_ID="bzoulip!")
    @mock.patch("lgrez.blocs.gsheets.connect")
    @mock.patch("lgrez.blocs.gsheets.update")
    def test_validate_sync(self, gupdate_patch, gconnect_patch):
        """Unit tests for sync.validate_sync function."""
        # def validate_sync(modifs)
        validate_sync = sync.validate_sync
        # cas unique
        sheet = mock.Mock()
        workbook = mock.Mock(**{"worksheet.return_value": sheet})
        gconnect_patch.return_value = workbook
        validate_sync([123, "456", {"a": 2}])
        gconnect_patch.assert_called_once_with("bzoulip!")
        workbook.worksheet.assert_called_once_with("uéué")
        gupdate_patch.assert_called_once_with(sheet, 123, "456", {"a": 2})


    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.gestion_actions.open_action")
    @mock.patch("lgrez.features.gestion_actions.add_action")
    @mock.patch("lgrez.features.gestion_actions.delete_action")
    async def test_modif_joueur(self, da_patch, aa_patch, oa_patch):
        """Unit tests for sync.modif_joueur function."""
        # async def modif_joueur(joueur_id, modifs, silent=False)
        modif_joueur = sync.modif_joueur
        mock_bdd.add_campsroles(10, 10)
        joueurs = base_joueurs()
        bdd.Joueur.add(*joueurs)

        # joueur non existant
        with self.assertRaises(ValueError) as cm:
            await modif_joueur(17, [])

        # no modifs
        with mock_discord.mock_members_and_chans(*joueurs):
            done, cgl = await modif_joueur(1, [])
        self.assertEqual(done, [])
        self.assertIn("Joueur1", cgl)
        self.assertIn("NO MODIFS", cgl)

        # --- test un cas à la fois sur J3 ---
        joueur3 = joueurs[2]
        # nom, silent
        modif = sync.TDBModif(3, "nom", "jbzz", 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            with mock.patch("lgrez.config.private_chan_prefix", "[PCPR]"):
                member, chan = joueur3.member, joueur3.private_chan
                done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("nom : jbzz", cgl)
        member.edit.assert_called_once_with(nick="jbzz")
        chan.edit.assert_called_once_with(name="[PCPR]jbzz")
        chan.send.assert_not_called()
        self.assertEqual(joueur3.nom, "jbzz")
        joueur3.nom = "Joueur3"
        config.session.commit()
        # nom, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            with mock.patch("lgrez.config.private_chan_prefix", "[PCPR]"):
                member, chan = joueur3.member, joueur3.private_chan
                done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        member.edit.assert_called_once_with(nick="jbzz")
        chan.edit.assert_called_once_with(name="[PCPR]jbzz")
        chan.send.assert_called_once()
        self.assertIn("Tu t'appelles maintenant", chan.send.call_args.args[0])
        self.assertIn("jbzz", chan.send.call_args.args[0])
        self.assertEqual(joueur3.nom, "jbzz")
        joueur3.nom = "Joueur3"
        config.session.commit()

        # chambre, silent
        modif = sync.TDBModif(3, "chambre", "lointréloin", 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("chambre : lointréloin", cgl)
        chan.send.assert_not_called()
        self.assertEqual(joueur3.chambre, "lointréloin")
        joueur3.chambre = "Ch3"
        config.session.commit()
        # chambre, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        chan.send.assert_called_once()
        self.assertIn("Tu habites maintenant", chan.send.call_args.args[0])
        self.assertIn("lointréloin", chan.send.call_args.args[0])
        self.assertEqual(joueur3.chambre, "lointréloin")
        joueur3.chambre = "Ch3"
        config.session.commit()

        # statut = vivant, silent
        modif = sync.TDBModif(3, "statut", bdd.Statut.vivant, 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("statut : Statut.vivant", cgl)
        member.add_roles.assert_called_once_with(config.Role.joueur_en_vie)
        member.remove_roles.assert_called_once_with(config.Role.joueur_mort)
        chan.send.assert_not_called()
        self.assertEqual(joueur3.statut, bdd.Statut.vivant)
        joueur3.statut = bdd.Statut.MV
        config.session.commit()
        # statut = vivant, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        member.add_roles.assert_called_once_with(config.Role.joueur_en_vie)
        member.remove_roles.assert_called_once_with(config.Role.joueur_mort)
        chan.send.assert_called_once()
        self.assertIn("Tu es maintenant en vie", chan.send.call_args.args[0])
        self.assertEqual(joueur3.statut, bdd.Statut.vivant)
        joueur3.statut = bdd.Statut.MV
        config.session.commit()

        # statut = mort, silent
        oa_patch.assert_not_called()
        modif = sync.TDBModif(3, "statut", bdd.Statut.mort, 0, 0)
        bdd.BaseAction(slug="tpz",
                       trigger_debut=bdd.ActionTrigger.temporel).add()
        bdd.BaseAction(slug="mrz", trigger_debut=bdd.ActionTrigger.mort).add()
        actions = [bdd.Action(joueur=joueur3, _base_slug="tpz"),
                   bdd.Action(joueur=joueur3, _base_slug="mrz")]
        bdd.Action.add(*actions)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("statut : Statut.mort", cgl)
        member.add_roles.assert_called_once_with(config.Role.joueur_mort)
        member.remove_roles.assert_called_once_with(config.Role.joueur_en_vie)
        oa_patch.assert_called_once_with(actions[1])
        oa_patch.reset_mock()
        chan.send.assert_not_called()
        self.assertEqual(joueur3.statut, bdd.Statut.mort)
        joueur3.statut = bdd.Statut.MV
        config.session.commit()
        # statut = mort, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        member.add_roles.assert_called_once_with(config.Role.joueur_mort)
        member.remove_roles.assert_called_once_with(config.Role.joueur_en_vie)
        oa_patch.assert_called_once_with(actions[1])
        oa_patch.reset_mock()
        chan.send.assert_called_once()
        self.assertIn("Tu es malheureusement", chan.send.call_args.args[0])
        self.assertEqual(joueur3.statut, bdd.Statut.mort)
        # joueur3.statut = bdd.Statut.MV    # on laisse mort

        # statut = MV, silent
        modif = sync.TDBModif(3, "statut", bdd.Statut.MV, 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("statut : Statut.MV", cgl)
        member.add_roles.assert_called_once_with(config.Role.joueur_en_vie)
        member.remove_roles.assert_called_once_with(config.Role.joueur_mort)
        chan.send.assert_not_called()
        self.assertEqual(joueur3.statut, bdd.Statut.MV)
        joueur3.statut = bdd.Statut.mort    # on re-tue
        config.session.commit()
        # statut = MV, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        member.add_roles.assert_called_once_with(config.Role.joueur_en_vie)
        member.remove_roles.assert_called_once_with(config.Role.joueur_mort)
        chan.send.assert_called_once()
        self.assertIn("Tu viens d'être réduit", chan.send.call_args.args[0])
        self.assertEqual(joueur3.statut, bdd.Statut.MV)
        config.session.commit()             # on laisse MV

        # statut = autre, silent
        modif = sync.TDBModif(3, "statut", bdd.Statut.immortel, 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("statut : Statut.immortel", cgl)
        chan.send.assert_not_called()
        self.assertEqual(joueur3.statut, bdd.Statut.immortel)
        joueur3.statut = bdd.Statut.MV
        config.session.commit()
        # statut = autre, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        chan.send.assert_called_once()
        self.assertIn("Nouveau statut", chan.send.call_args.args[0])
        self.assertIn("immortel", chan.send.call_args.args[0])
        self.assertEqual(joueur3.statut, bdd.Statut.immortel)
        joueur3.statut = bdd.Statut.MV
        config.session.commit()

        # role, silent
        bas = [bdd.BaseAction(slug="ar3"),  bdd.BaseAction(slug="aautre"),
               bdd.BaseAction(slug="ar71"), bdd.BaseAction(slug="ar72")]
        role3, role7 = bdd.Role.query.get("role3"), bdd.Role.query.get("role7")
        role3.base_actions = [bas[0]]
        role7.base_actions = [bas[2], bas[3]]
        actions = [bdd.Action(joueur=joueur3, base=bas[0]),
                   bdd.Action(joueur=joueur3, base=bas[1])]
        bdd.Action.add(*actions, *bas)
        modif = sync.TDBModif(3, "role", bdd.Role.query.get("role7"), 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        # ancienne action de rôle supprimée ?
        da_patch.assert_called_once_with(actions[0])
        da_patch.reset_mock()
        # nouvelles actions de rôle créées ?
        aa_patch.assert_called()
        new_actions = [call.args[0] for call in aa_patch.call_args_list]
        self.assertEqual({(act.joueur, act.base) for act in new_actions},
                         {(joueur3, bas[2]), (joueur3, bas[3])})
        aa_patch.reset_mock()
        self.assertIn("Joueur3", cgl)
        self.assertIn("role7", cgl)
        chan.send.assert_not_called()
        config.session.commit()
        self.assertEqual(joueur3._role_slug, "role7")
        joueur3._role_slug = "role3"
        config.session.commit()

        # role, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        # ancienne action de rôle supprimée ?
        da_patch.assert_called_once_with(actions[0])
        da_patch.reset_mock()
        # nouvelles actions de rôle créées ?
        aa_patch.assert_called()
        new_actions = [call.args[0] for call in aa_patch.call_args_list]
        self.assertEqual({(act.joueur, act.base) for act in new_actions},
                         {(joueur3, bas[2]), (joueur3, bas[3])})
        aa_patch.reset_mock()
        chan.send.assert_called_once()
        self.assertIn("Ton nouveau rôle", chan.send.call_args.args[0])
        self.assertIn("Role7", chan.send.call_args.args[0])
        config.session.commit()
        self.assertEqual(joueur3._role_slug, "role7")
        joueur3._role_slug = "role3"
        config.session.commit()

        # camp, silent
        modif = sync.TDBModif(3, "camp", bdd.Camp.query.get("camp7"), 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("camp7", cgl)
        chan.send.assert_not_called()
        config.session.commit()
        self.assertEqual(joueur3._camp_slug, "camp7")
        joueur3._camp_slug = "camp3"
        config.session.commit()
        # camp, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        chan.send.assert_called_once()
        self.assertIn("Tu fais maintenant partie", chan.send.call_args.args[0])
        self.assertIn("Camp7", chan.send.call_args.args[0])
        config.session.commit()
        self.assertEqual(joueur3._camp_slug, "camp7")
        joueur3._camp_slug = "camp3"
        config.session.commit()

        # votant_village = False, silent
        modif = sync.TDBModif(3, "votant_village", False, 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("False", cgl)
        chan.send.assert_not_called()
        config.session.commit()
        self.assertEqual(joueur3.votant_village, False)
        joueur3.votant_village = True
        config.session.commit()
        # votant_village = False, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        chan.send.assert_called_once()
        self.assertIn("Tu ne peux maintenant", chan.send.call_args.args[0])
        self.assertIn("votes du village", chan.send.call_args.args[0])
        config.session.commit()
        self.assertEqual(joueur3.votant_village, False)
        # joueur3.votant_village = True     on laisse False
        config.session.commit()

        # votant_village = True, silent
        modif = sync.TDBModif(3, "votant_village", True, 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("True", cgl)
        chan.send.assert_not_called()
        config.session.commit()
        self.assertEqual(joueur3.votant_village, True)
        joueur3.votant_village = False
        config.session.commit()
        # votant_village = True, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        chan.send.assert_called_once()
        self.assertIn("Tu peux maintenant", chan.send.call_args.args[0])
        self.assertIn("votes du village", chan.send.call_args.args[0])
        config.session.commit()
        self.assertEqual(joueur3.votant_village, True)
        # joueur3.votant_village = False     on laisse True
        config.session.commit()

        # votant_loups = False, silent
        modif = sync.TDBModif(3, "votant_loups", False, 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("False", cgl)
        chan.send.assert_not_called()
        config.session.commit()
        self.assertEqual(joueur3.votant_loups, False)
        joueur3.votant_loups = True
        config.session.commit()
        # votant_loups = False, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        chan.send.assert_called_once()
        self.assertIn("Tu ne peux maintenant", chan.send.call_args.args[0])
        self.assertIn("votes des loups", chan.send.call_args.args[0])
        config.session.commit()
        self.assertEqual(joueur3.votant_loups, False)
        # joueur3.votant_loups = True     on laisse False
        config.session.commit()

        # votant_loups = True, silent
        modif = sync.TDBModif(3, "votant_loups", True, 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("True", cgl)
        chan.send.assert_not_called()
        config.session.commit()
        self.assertEqual(joueur3.votant_loups, True)
        joueur3.votant_loups = False
        config.session.commit()
        # votant_loups = True, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        chan.send.assert_called_once()
        self.assertIn("Tu peux maintenant", chan.send.call_args.args[0])
        self.assertIn("votes des loups", chan.send.call_args.args[0])
        config.session.commit()
        self.assertEqual(joueur3.votant_loups, True)
        # joueur3.votant_village = False     on laisse True
        config.session.commit()

        # role_actif = True, silent
        modif = sync.TDBModif(3, "role_actif", True, 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("True", cgl)
        chan.send.assert_not_called()
        config.session.commit()
        self.assertEqual(joueur3.role_actif, True)
        joueur3.role_actif = False
        config.session.commit()
        # role_actif = True, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        chan.send.assert_called_once()
        self.assertIn("Tu peux maintenant", chan.send.call_args.args[0])
        self.assertIn("utiliser tes pouvoirs", chan.send.call_args.args[0])
        config.session.commit()
        self.assertEqual(joueur3.role_actif, True)
        # joueur3.role_actif = False     on laisse True
        config.session.commit()

        # role_actif = False, silent
        modif = sync.TDBModif(3, "role_actif", False, 0, 0)
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], True)
        self.assertEqual(done, [modif])
        self.assertIn("Joueur3", cgl)
        self.assertIn("False", cgl)
        chan.send.assert_not_called()
        config.session.commit()
        self.assertEqual(joueur3.role_actif, False)
        joueur3.role_actif = True
        config.session.commit()
        # role_actif = False, verbose
        with mock_discord.mock_members_and_chans(joueur3):
            member, chan = joueur3.member, joueur3.private_chan
            done, cgl = await modif_joueur(3, [modif], False)
        self.assertEqual(done, [modif])
        chan.send.assert_called_once()
        self.assertIn("Tu ne peux maintenant", chan.send.call_args.args[0])
        self.assertIn("utiliser aucun pouvoir", chan.send.call_args.args[0])
        config.session.commit()
        self.assertEqual(joueur3.role_actif, False)
        # joueur3.votant_village = True     on laisse True
        config.session.commit()

        # --- test plusieurs modifs sur J3 ---
        # ==> well, it should work


class TestSync(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.features.sync commands."""

    def setUp(self):
        mock_discord.mock_config()
        self.cog = sync.Sync(config.bot)

    def tearDown(self):
        mock_discord.unmock_config()

    @mock_bdd.patch_db      # Empty database for this method
    @mock.patch("lgrez.features.sync.get_sync")         # tested before
    @mock.patch("lgrez.features.sync.validate_sync")    # tested before
    @mock.patch("lgrez.features.sync.modif_joueur")     # tested before
    async def test_sync(self, modif_patch, valid_patch, get_patch):
        """Unit tests for !sync command."""
        # async def sync(self, ctx, silent=False)
        sync_cmd = self.cog.sync
        mock_bdd.add_campsroles(10, 10)
        bdd.Joueur.add(*base_joueurs())

        # no modifs
        get_patch.return_value = []
        ctx = mock_discord.get_ctx(sync_cmd)
        await ctx.invoke()
        ctx.assert_sent("Récupération des modifications",
                        "Pas de nouvelles modificatons")
        get_patch.assert_called_once()
        get_patch.reset_mock(return_value=True)
        modif_patch.assert_not_called()
        valid_patch.assert_not_called()

        # 1 modif pour 1 joueur, abort
        modif = sync.TDBModif(4, "role", 42, 17, "role34")
        get_patch.return_value = [modif]
        ctx = mock_discord.get_ctx(sync_cmd)
        with mock_discord.interact(("yes_no", False)):
            await ctx.invoke()
        ctx.assert_sent("Récupération des modifications",
                        "1 modification(s) trouvée(s) pour 1 joueur",
                        "Mission aborted")
        get_patch.assert_called_once()
        get_patch.reset_mock(return_value=True)
        modif_patch.assert_not_called()
        valid_patch.assert_not_called()

        # 1 modif pour 1 joueur, error
        modif = sync.TDBModif(4, "role", 42, 17, "role34")
        get_patch.return_value = [modif]
        modif_patch.side_effect = ValueError("Pitre")
        ctx = mock_discord.get_ctx(sync_cmd)
        with mock_discord.interact(("yes_no", True)):
            with mock.patch("lgrez.blocs.tools.log") as log_patch:
                await ctx.invoke()
        ctx.assert_sent("Récupération des modifications",
                        "1 modification(s) trouvée(s) pour 1 joueur",
                        "Erreur joueur 4",
                        "Fait")
        log_patch.assert_called_once()
        self.assertIn("Pitre", log_patch.call_args.args[0])
        get_patch.assert_called_once()
        get_patch.reset_mock(return_value=True)
        modif_patch.assert_called_once_with(4, [modif], False)
        modif_patch.reset_mock(side_effect=True)
        valid_patch.assert_not_called()

        # 1 modif pour 1 joueur, success
        modif = sync.TDBModif(4, "role", 42, 17, "role34")
        get_patch.return_value = [modif]
        modif_patch.return_value = ([modif], "chglzoo")
        ctx = mock_discord.get_ctx(sync_cmd)
        with mock_discord.interact(("yes_no", True)):
            with mock.patch("lgrez.blocs.tools.log") as log_patch:
                await ctx.invoke()
        ctx.assert_sent("Récupération des modifications",
                        "1 modification(s) trouvée(s) pour 1 joueur",
                        "Fait")
        log_patch.assert_called_once()
        self.assertIn("chglzoo", log_patch.call_args.args[0])
        get_patch.assert_called_once()
        get_patch.reset_mock(return_value=True)
        modif_patch.assert_called_once_with(4, [modif], False)
        modif_patch.reset_mock(return_value=True)
        valid_patch.assert_called_once_with([modif])
        valid_patch.reset_mock()

        # 3 modifs pour 1 joueur, success
        modifs = [sync.TDBModif(4, "role", 42, 17, "role34"),
                  sync.TDBModif(4, "statut", 42, 19, bdd.Statut.mort),
                  sync.TDBModif(4, "votant_village", 42, 22, False)]
        get_patch.return_value = modifs
        modif_patch.return_value = (modifs, "chglzto")
        ctx = mock_discord.get_ctx(sync_cmd)
        with mock_discord.interact(("yes_no", True)):
            with mock.patch("lgrez.blocs.tools.log") as log_patch:
                await ctx.invoke()
        ctx.assert_sent("Récupération des modifications",
                        "3 modification(s) trouvée(s) pour 1 joueur",
                        "Fait")
        log_patch.assert_called_once()
        self.assertIn("chglzto", log_patch.call_args.args[0])
        get_patch.assert_called_once()
        get_patch.reset_mock(return_value=True)
        modif_patch.assert_called_once_with(4, modifs, False)
        modif_patch.reset_mock(return_value=True)
        valid_patch.assert_called_once_with(modifs)
        valid_patch.reset_mock()

        # 6 modifs pour 3 joueurs, success partiel
        modifs4 = [sync.TDBModif(4, "role", 42, 17, "role34"),
                   sync.TDBModif(4, "statut", 42, 19, bdd.Statut.mort),
                   sync.TDBModif(4, "votant_village", 42, 22, False)]
        modifs3 = [sync.TDBModif(3, "role", 41, 17, "role35"),
                   sync.TDBModif(3, "statut", 41, 19, bdd.Statut.vivant)]
        modifs2 = [sync.TDBModif(2, "votant_village", 40, 22, False)]
        modifs = modifs4 + modifs3 + modifs2
        get_patch.return_value = modifs
        modif_patch.side_effect = [(modifs4[:-1], "chglzto"),   # 4 : partiel
                                   ValueError("Pitre"),         # 3 : error
                                   (modifs2, "chglzoo")]        # 2 : tous
        ctx = mock_discord.get_ctx(sync_cmd)
        with mock_discord.interact(("yes_no", True)):
            with mock.patch("lgrez.blocs.tools.log") as log_patch:
                await ctx.invoke()
        ctx.assert_sent("Récupération des modifications",
                        "6 modification(s) trouvée(s) pour 3 joueur",
                        "Erreur joueur 3",
                        "Fait")
        log_patch.assert_called_once()
        self.assertIn("chglzto", log_patch.call_args.args[0])
        self.assertIn("Pitre", log_patch.call_args.args[0])
        self.assertIn("chglzoo", log_patch.call_args.args[0])
        get_patch.assert_called_once()
        get_patch.reset_mock(return_value=True)
        self.assertEqual(modif_patch.call_count, 3)
        modif_patch.assert_has_calls([mock.call(4, modifs4, False),
                                      mock.call(3, modifs3, False),
                                      mock.call(2, modifs2, False)])
        modif_patch.reset_mock(side_effect=True)
        valid_patch.assert_called_once_with(modifs4[:-1] + modifs2)
        valid_patch.reset_mock()

        # 1 modif pour 1 joueur, silent = "True"
        modif = sync.TDBModif(4, "role", 42, 17, "role34")
        get_patch.return_value = [modif]
        modif_patch.return_value = ([modif], "chglzoo")
        ctx = mock_discord.get_ctx(sync_cmd, "True")
        with mock_discord.interact(("yes_no", True)):
            with mock.patch("lgrez.blocs.tools.log") as log_patch:
                await ctx.invoke()
        ctx.assert_sent("Récupération des modifications",
                        "1 modification(s) trouvée(s) pour 1 joueur",
                        "Fait")
        log_patch.assert_called_once()
        self.assertIn("chglzoo", log_patch.call_args.args[0])
        get_patch.assert_called_once()
        get_patch.reset_mock(return_value=True)
        modif_patch.assert_called_once_with(4, [modif], True)
        modif_patch.reset_mock(return_value=True)
        valid_patch.assert_called_once_with([modif])
        valid_patch.reset_mock()

        # 1 modif pour 1 joueur, silent = "boogywoogie"
        modif = sync.TDBModif(4, "role", 42, 17, "role34")
        get_patch.return_value = [modif]
        modif_patch.return_value = ([modif], "chglzoo")
        ctx = mock_discord.get_ctx(sync_cmd, "boogywoogie")
        with mock_discord.interact(("yes_no", True)):
            with mock.patch("lgrez.blocs.tools.log") as log_patch:
                await ctx.invoke()
        ctx.assert_sent("Récupération des modifications",
                        "1 modification(s) trouvée(s) pour 1 joueur",
                        "Fait")
        log_patch.assert_called_once()
        self.assertIn("chglzoo", log_patch.call_args.args[0])
        get_patch.assert_called_once()
        get_patch.reset_mock(return_value=True)
        modif_patch.assert_called_once_with(4, [modif], True)
        modif_patch.reset_mock(return_value=True)
        valid_patch.assert_called_once_with([modif])
        valid_patch.reset_mock()


    @mock_bdd.patch_db      # Empty database for this method
    @mock_env.patch_env(LGREZ_ROLES_SHEET_ID="badapaf?")
    @mock.patch("lgrez.blocs.gsheets.connect")
    async def test_fillroles(self, gconnect_patch):
        """Unit tests for !fillroles command."""
        # async def fillroles(self, ctx)
        config.max_ciblages_per_action = 0
        fillroles = self.cog.fillroles
        camps, roles = mock_bdd.add_campsroles(10, 10)
        baseactions = [bdd.BaseAction(slug=f"ba{n}", roles=[roles[n]])
                       for n in range(10)]
        bdd.BaseAction.add(*baseactions)

        # missing sheet
        workbook = mock.Mock(**{"worksheet.side_effect":
                                gsheets.WorksheetNotFound})
        gconnect_patch.return_value = workbook
        ctx = mock_discord.get_ctx(fillroles)
        with self.assertRaises(ValueError) as cm:
            await ctx.invoke()
        self.assertIn("feuille 'camps' non trouvée", cm.exception.args[0])

        # missing column
        c_vals = [
            [0, "slug", "nom", "description", "public", "emojZZi"],
        ]
        sheets = {
            "camps": mock.Mock(**{"get_all_values.return_value": c_vals}),
        }
        workbook = mock.Mock(**{"worksheet.side_effect": lambda n: sheets[n]})
        gconnect_patch.return_value = workbook
        ctx = mock_discord.get_ctx(fillroles)
        with self.assertRaises(ValueError) as cm:
            await ctx.invoke()
        self.assertIn("colonne 'emoji' non trouvée", cm.exception.args[0])

        # all okay lets go
        c_vals = [
            ["slug", "nom", "description", "public", "emoji"],
            ["camp2", "Camp2", "", "TRUE", "emoji2"],       # unchanged
            ["camp3", "krouss", "", "TRUE", "emoji3"],      # changed once
            ["camp4", "krs", "kl", 'FALSE', "emoji42"],     # changed all
            ["camp17", "Camp-17", "", "TRUE", "em17i"],     # new 1
            ["camp23", "k23BS", "poo", "FALSE", "emo.2"],    # new 2
        ]
        r_vals = [
            ["slug", "prefixe", "nom", "camp", "description_courte",
             "description_longue"],
            ["role2", "", "Role2", "camp2", "", ""],            # unchanged
            ["role3", "z' ", "Role3", "camp3", "", ""],         # changed once
            ["role4", "y° ", "R4zz", "camp5", "dc4", "dl4"],    # changed all
            ["role17", "Lo ", "R17", "camp4", "", ""],          # new 1
            ["role23", "Lu ", "R.23", "camp23", "dc23", "dl23"],# 2 (new camp)
        ]
        b_vals = [
            ["slug", "trigger_debut", "trigger_fin", "instant", "heure_debut",
             "heure_fin", "base_cooldown", "base_charges", "refill", "lieu",
             "interaction_notaire", "interaction_gardien", "mage",
             "changement_cible", "roles"],
            ["ba2", "perma", "perma", "FALSE", "", "", "0",
             "", "", "", "", "", "", "", "role2"],          # unchanged
            ["ba3", "mort", "perma", "FALSE", "", "", "0",
             "", "", "", "", "", "", "", "role3"],          # changed once
            ["ba4", "temporel", "delta", "TRUE", " 19:15",
             " 00:00", "1", "2", "ref1, ref2", "liz", "inz",
             "igz", "mgz", "TRUE", "role4, role5"],         # changed all
            ["ba17", "perma", "perma", "FALSE", "",
             "", "0", "", "", "", "", "", "", "", ""],      # new 1
            ["ba23", "mort", "delta", "TRUE", "", " 00:10",
             "1", "2", "ref12, ref22", "liz2", "inz2",
             "igz2", "mgz2", "FALSE", "role9, role23"],     # new 2 (new role)
        ]
        sheets = {
            "camps": mock.Mock(**{"get_all_values.return_value": c_vals}),
            "roles": mock.Mock(**{"get_all_values.return_value": r_vals}),
            "baseactions": mock.Mock(**{"get_all_values.return_value": b_vals}),
        }
        workbook = mock.Mock(**{"worksheet.side_effect": lambda n: sheets[n]})
        gconnect_patch.return_value = workbook
        ctx = mock_discord.get_ctx(fillroles)
        await ctx.invoke()
        # fonctions de projection instances BDD -> liste
        def campvals(slug):
            c = bdd.Camp.query.get(slug)
            self.assertIsNot(None, c, f"camp {slug}")
            return [c.slug, c.nom, c.description, c.public, c.emoji]
        def rolevals(slug):
            r = bdd.Role.query.get(slug)
            self.assertIsNot(None, r, f"rôle {slug}")
            return [r.slug, r.prefixe, r.nom, r.camp, r.description_courte,
                    r.description_longue]
        def basevals(slug):
            b = bdd.BaseAction.query.get(slug)
            self.assertIsNot(None, b, f"base {slug}")
            return [b.slug, b.trigger_debut, b.trigger_fin, b.instant,
                    b.heure_debut, b.heure_fin, b.base_cooldown,
                    b.base_charges, b.refill, b.lieu, b.interaction_notaire,
                    b.interaction_gardien, b.mage, b.changement_cible,
                    set(b.roles)]
        # vérif camps
        self.assertEqual(campvals("camp1"),
                         ["camp1", "Camp1", "", True, "emoji1"])
        self.assertEqual(campvals("camp2"),
                         ["camp2", "Camp2", "", True, "emoji2"])
        self.assertEqual(campvals("camp3"),
                         ["camp3", "krouss", "", True, "emoji3"])
        self.assertEqual(campvals("camp4"),
                         ["camp4", "krs", "kl", False, "emoji42"])
        self.assertEqual(campvals("camp17"),
                         ["camp17", "Camp-17", "", True, "em17i"])
        self.assertEqual(campvals("camp23"),
                         ["camp23", "k23BS", "poo", False, "emo.2"])
        # vérif rôles
        self.assertEqual(rolevals("role1"),
                         ["role1", "", "Role1", camps[1], "", ""])
        self.assertEqual(rolevals("role2"),
                         ["role2", "", "Role2", camps[2], "", ""])
        self.assertEqual(rolevals("role3"),
                         ["role3", "z' ", "Role3", camps[3], "", ""])
        self.assertEqual(rolevals("role4"),
                         ["role4", "y° ", "R4zz", camps[5], "dc4", "dl4"])
        self.assertEqual(rolevals("role17"),
                         ["role17", "Lo ", "R17", camps[4], "", ""])
        camp23 = bdd.Camp.query.get("camp23")
        self.assertEqual(rolevals("role23"),
                         ["role23", "Lu ", "R.23", camp23, "dc23", "dl23"])
        # vérif baseactions
        self.assertEqual(basevals("ba1"),
                         ["ba1", bdd.ActionTrigger.perma,
                          bdd.ActionTrigger.perma, False, None, None, 0, None,
                          "", None, None, None, None, None, {roles[1]}])
        self.assertEqual(basevals("ba2"),
                         ["ba2", bdd.ActionTrigger.perma,
                          bdd.ActionTrigger.perma, False, None, None, 0, None,
                          "", None, None, None, None, None, {roles[2]}])
        self.assertEqual(basevals("ba3"),
                         ["ba3", bdd.ActionTrigger.mort,
                          bdd.ActionTrigger.perma, False, None, None, 0, None,
                          "", None, None, None, None, None, {roles[3]}])
        self.assertEqual(basevals("ba4"),
                         ["ba4", bdd.ActionTrigger.temporel,
                          bdd.ActionTrigger.delta, True, datetime.time(19, 15),
                          datetime.time(0, 0), 1, 2, "ref1, ref2", "liz",
                          "inz", "igz", "mgz", True, {roles[4], roles[5]}])
        self.assertEqual(basevals("ba17"),
                         ["ba17", bdd.ActionTrigger.perma,
                          bdd.ActionTrigger.perma, False, None, None, 0,
                          None, "", None, None, None, None, None, set()])
        role23 = bdd.Role.query.get("role23")
        self.assertEqual(basevals("ba23"),
                         ["ba23", bdd.ActionTrigger.mort,
                          bdd.ActionTrigger.delta, True, None,
                          datetime.time(0, 10), 1, 2, "ref12, ref22", "liz2",
                          "inz2", "igz2", "mgz2", False, {roles[9], role23}])

        # Remplissage de #rôles
        sent = "\n".join(call.args[0] if call.args
                         else call.kwargs["embed"].title
                         for call in config.Channel.roles.send.call_args_list)

        for role in bdd.Role.query.all():
            if role.camp.public:
                self.assertIn(role.nom, sent)
            else:
                self.assertNotIn(role.nom, sent)
        for camp in bdd.Camp.query.all():
            if camp.roles and camp.public:
                self.assertIn(camp.nom, sent)
            else:
                self.assertNotIn(camp.nom, sent)
