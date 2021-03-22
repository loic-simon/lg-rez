import unittest
from unittest import mock

from lgrez.bdd import model_ia



class TestReaction(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.model_ia.Reaction methods."""

    def test___repr__(self):
        """Unit tests for Reaction.__repr__ method."""
        # def __repr__(self)
        __repr__ = model_ia.Reaction.__repr__
        # < 15
        slf = mock.Mock(model_ia.Reaction, id=11, reponse="blebelebel")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<Reaction #11 (blebelebel...)>")
        # > 15
        slf = mock.Mock(model_ia.Reaction, id=11,
                        reponse="blebelebelpof^psdmlsqd*^ùfmqsfpspdofsdf")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<Reaction #11 (blebelebelpof^p...)>")


class TestTrigger(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.model_ia.Trigger methods."""

    def test___repr__(self):
        """Unit tests for Trigger.__repr__ method."""
        # def __repr__(self)
        __repr__ = model_ia.Trigger.__repr__
        # < 15
        slf = mock.Mock(model_ia.Trigger, id=11, trigger="blebelebel")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<Trigger #11 (blebelebel...)>")
        # > 15
        slf = mock.Mock(model_ia.Trigger, id=11,
                        trigger="blebelebelpof^psdmlsqd*^ùfmqsfpspdofsdf")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<Trigger #11 (blebelebelpof^p...)>")
