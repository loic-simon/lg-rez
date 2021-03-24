import unittest
from unittest import mock

from lgrez import config
from lgrez.bdd import model_jeu
from test import mock_discord, mock_bdd, mock_env



class TestRole(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.model_jeu.Role methods."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    def test___repr__(self):
        """Unit tests for Role.__repr__ method."""
        # def __repr__(self)
        __repr__ = model_jeu.Role.__repr__
        slf = mock.Mock(model_jeu.Role, slug="slùgz",
                        prefixe="p' ", nom="n@@mz")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<Role 'slùgz' (p' n@@mz)>")


    def test_nom_complet(self):
        """Unit tests for Role.nom_complet property."""
        # @property def nom_complet(self)
        nom_complet = model_jeu.Role.nom_complet
        slf = mock.MagicMock(model_jeu.Role)
        nom = nom_complet.fget(slf)
        self.assertEqual(nom, f"{slf.prefixe}{slf.nom}")
        self.assertIsNone(nom_complet.fset)       # read-only
        self.assertIsNone(nom_complet.fdel)


    def test_default(self):
        """Unit tests for Role.default classmethod."""
        # @classmethod def default(cls)
        default = model_jeu.Role.default
        qry_patch = config.session.query.return_value
        # existing
        cls = mock.MagicMock()
        role = default()
        qry_patch.get.assert_called_once_with(config.default_role_slug)
        qry_patch.reset_mock()
        self.assertEqual(role, qry_patch.get.return_value)
        # existing - other than default
        cls = mock.MagicMock()
        _drs = config.default_role_slug
        config.default_role_slug = "bzbzbz"
        role = default()
        qry_patch.get.assert_called_once_with("bzbzbz")
        qry_patch.reset_mock()
        self.assertEqual(role, qry_patch.get.return_value)
        config.default_role_slug = _drs
        # not existing
        cls = mock.MagicMock()
        qry_patch.get.return_value = None
        with self.assertRaises(ValueError):
            default()
        qry_patch.get.assert_called_once_with(config.default_role_slug)


class TestCamp(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.model_jeu.Camp methods."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    def test___repr__(self):
        """Unit tests for Camp.__repr__ method."""
        # def __repr__(self)
        __repr__ = model_jeu.Camp.__repr__
        slf = mock.Mock(model_jeu.Camp, slug="slùgz", nom="n@@mz")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<Camp 'slùgz' (n@@mz)>")


    def test_discord_emoji(self):
        """Unit tests for Camp.discord_emoji property."""
        # @property def discord_emoji(self)
        discord_emoji = model_jeu.Camp.discord_emoji
        config.guild.emojis = [mock.Mock() for i in range(5)]
        for emo, name in zip(config.guild.emojis,
                             ["bz", "op", "glu", "fzoop", "paf"]):
            emo.configure_mock(name=name)
        # pas d'emoji prévu
        slf = mock.MagicMock(model_jeu.Camp, emoji=None)
        with self.assertRaises(ValueError):
            discord_emoji.fget(slf)
        # pas d'emoji sur le serv
        slf = mock.MagicMock(model_jeu.Camp, emoji="bloup")
        with self.assertRaises(ValueError):
            discord_emoji.fget(slf)
        # emoji
        slf = mock.MagicMock(model_jeu.Camp, emoji="fzoop")
        emoji = discord_emoji.fget(slf)
        self.assertEqual(emoji, config.guild.emojis[3])
        # read-only
        self.assertIsNone(discord_emoji.fset)
        self.assertIsNone(discord_emoji.fdel)


    def test_discord_emoji_or_none(self):
        """Unit tests for Camp.discord_emoji_or_none property."""
        # @property def discord_emoji_or_none(self)
        discord_emoji_or_none = model_jeu.Camp.discord_emoji_or_none
        # emoji
        slf = mock.MagicMock(model_jeu.Camp)
        emoji = discord_emoji_or_none.fget(slf)
        self.assertEqual(emoji, slf.discord_emoji)
        # pas d'emoji
        class PropertyMock(mock.MagicMock):
            @property
            def discord_emoji(self):
                raise ValueError
        slf = PropertyMock(model_jeu.Camp)
        emoji = discord_emoji_or_none.fget(slf)
        self.assertIsNone(emoji)
        # read-only
        self.assertIsNone(discord_emoji_or_none.fset)
        self.assertIsNone(discord_emoji_or_none.fdel)


    def test_default(self):
        """Unit tests for Camp.default classmethod."""
        # @classmethod def default(cls)
        default = model_jeu.Camp.default
        qry_patch = config.session.query.return_value
        # existing
        cls = mock.MagicMock()
        camp = default()
        qry_patch.get.assert_called_once_with(config.default_camp_slug)
        qry_patch.reset_mock()
        self.assertEqual(camp, qry_patch.get.return_value)
        # existing - other than default
        cls = mock.MagicMock()
        _drs = config.default_camp_slug
        config.default_camp_slug = "bzbzbz"
        camp = default()
        qry_patch.get.assert_called_once_with("bzbzbz")
        qry_patch.reset_mock()
        self.assertEqual(camp, qry_patch.get.return_value)
        config.default_camp_slug = _drs
        # not existing
        cls = mock.MagicMock()
        qry_patch.get.return_value = None
        with self.assertRaises(ValueError):
            default()
        qry_patch.get.assert_called_once_with(config.default_camp_slug)


class TestBaseAction(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.model_jeu.BaseAction methods."""

    def test___repr__(self):
        """Unit tests for BaseAction.__repr__ method."""
        # def __repr__(self)
        __repr__ = model_jeu.BaseAction.__repr__
        slf = mock.Mock(model_jeu.BaseAction, slug="slùgz")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<BaseAction 'slùgz'>")
