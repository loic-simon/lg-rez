import unittest
from unittest import mock

from lgrez import config
from lgrez.bdd import model_joueurs
from test import mock_discord, mock_bdd, mock_env



class TestJoueur(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.model_joueurs.Joueur methods."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    def test___repr__(self):
        """Unit tests for Joueur.__repr__ method."""
        # def __repr__(self)
        __repr__ = model_joueurs.Joueur.__repr__
        slf = mock.Mock(model_joueurs.Joueur, discord_id=12345, nom="n@@mz")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<Joueur #12345 (n@@mz)>")


    def test_member(self):
        """Unit tests for Joueur.member property."""
        # @property def member(self)
        member = model_joueurs.Joueur.member
        # existant
        slf = mock.MagicMock(model_joueurs.Joueur)
        mbr = member.fget(slf)
        config.guild.get_member.assert_called_once_with(slf.discord_id)
        self.assertEqual(mbr, config.guild.get_member.return_value)
        config.guild.reset_mock()
        # not existant
        slf = mock.MagicMock(model_joueurs.Joueur)
        config.guild.get_member.return_value = None
        with self.assertRaises(ValueError):
            member.fget(slf)
        config.guild.get_member.assert_called_once_with(slf.discord_id)


    def test_private_chan(self):
        """Unit tests for Joueur.private_chan property."""
        # @property def private_chan(self)
        private_chan = model_joueurs.Joueur.private_chan
        # existant
        slf = mock.MagicMock(model_joueurs.Joueur)
        mbr = private_chan.fget(slf)
        config.guild.get_channel.assert_called_once_with(slf.chan_id_)
        self.assertEqual(mbr, config.guild.get_channel.return_value)
        config.guild.reset_mock()
        # not existant
        slf = mock.MagicMock(model_joueurs.Joueur)
        config.guild.get_channel.return_value = None
        with self.assertRaises(ValueError):
            private_chan.fget(slf)
        config.guild.get_channel.assert_called_once_with(slf.chan_id_)


    def test_from_member(self):
        """Unit tests for Joueur.from_member classmethod."""
        # @classmethod def from_member(cls, member)
        from_member = model_joueurs.Joueur.from_member
        query = config.session.query.return_value
        # existant
        member = mock.MagicMock()
        jr = from_member(member)
        query.get.assert_called_once_with(member.id)
        self.assertEqual(jr, query.get.return_value)
        query.reset_mock()
        # not existant
        member = mock.MagicMock()
        query.get.return_value = None
        with self.assertRaises(ValueError):
            from_member(member)
        query.get.assert_called_once_with(member.id)



class TestCandidHaro(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.model_joueurs.CandidHaro methods."""

    def test___repr__(self):
        """Unit tests for CandidHaro.__repr__ method."""
        # def __repr__(self)
        __repr__ = model_joueurs.CandidHaro.__repr__
        slf = mock.Mock(model_joueurs.CandidHaro, id=11,
                        joueur="j00rz", type="oui")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<CandidHaro #11 (j00rz/oui)>")
