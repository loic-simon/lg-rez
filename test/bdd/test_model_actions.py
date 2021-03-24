import datetime
import unittest
from unittest import mock

import freezegun

from lgrez import config
from lgrez.bdd import model_actions
from lgrez.blocs import webhook
from test import mock_discord, mock_env



class TestAction(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.model_actions.Action methods."""

    def test___repr__(self):
        """Unit tests for Action.__repr__ method."""
        # def __repr__(self)
        __repr__ = model_actions.Action.__repr__
        slf = mock.Mock(model_actions.Action, id=11, base="bazz", joueur="j0r")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<Action #11 (bazz/j0r)>")


class TestTache(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.model_actions.Tache methods."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    def test___repr__(self):
        """Unit tests for Tache.__repr__ method."""
        # def __repr__(self)
        __repr__ = model_actions.Tache.__repr__
        slf = mock.Mock(model_actions.Tache, id=11, commande="blebelebelpof")
        rpr = __repr__(slf)
        self.assertEqual(rpr, "<Tache #11 (blebelebelpof)>")

    def test_handler(self):
        """Unit tests for Tache.handler property."""
        # @property def handler(self)
        handler = model_actions.Tache.handler
        config.bot.tasks = {11: mock.Mock(), 13: mock.Mock()}
        # Getter - Enregistrée
        slf = mock.Mock(model_actions.Tache, id=11)
        hdlr = handler.fget(slf)
        self.assertEqual(hdlr, config.bot.tasks[11])
        # Getter - Non enregistrée
        slf = mock.Mock(model_actions.Tache, id=12)
        with self.assertRaises(RuntimeError):
            handler.fget(slf)
        # Setter
        value = mock.Mock()
        handler.fset(slf, value)
        self.assertEqual(config.bot.tasks.get(12), value)
        with self.assertRaises(RuntimeError):
            handler.fset(mock.Mock(model_actions.Tache, id=None), value)
        # Deleter - Enregistrée
        handler.fdel(slf)
        self.assertNotIn(12, config.bot.tasks)
        # Deleter - Non enregistrée
        handler.fdel(slf)
        self.assertNotIn(12, config.bot.tasks)


    @mock_env.patch_env(LGREZ_WEBHOOK_URL="uiui://oh")
    @mock.patch("lgrez.blocs.webhook.send")
    def test_execute(self, send_patch):
        """Unit tests for Tache.execute method."""
        # def execute(self)
        execute = model_actions.Tache.execute

        # too soon
        webhook._last_time = 132
        slf = mock.Mock(model_actions.Tache)
        with freezegun.freeze_time(datetime.datetime.utcfromtimestamp(133.5)):
            execute(slf)
        config.loop.call_later.assert_called_once_with(2, slf.execute)
        config.loop.reset_mock()

        # perfect (+2s), envoi OK
        webhook._last_time = 132
        slf = mock.Mock(model_actions.Tache)
        send_patch.return_value = True
        with freezegun.freeze_time(datetime.datetime.utcfromtimestamp(134)):
            execute(slf)
        self.assertEqual(webhook._last_time, 134)
        send_patch.assert_called_once_with(slf.commande, url="uiui://oh")
        send_patch.reset_mock()
        slf.delete.assert_called_once()
        config.loop.call_later.assert_not_called()

        # large, envoi échec
        webhook._last_time = 132
        slf = mock.Mock(model_actions.Tache)
        send_patch.return_value = False
        with freezegun.freeze_time(datetime.datetime.utcfromtimestamp(334)):
            execute(slf)
        self.assertEqual(webhook._last_time, 334)
        send_patch.assert_called_once_with(slf.commande, url="uiui://oh")
        slf.delete.assert_not_called()
        config.loop.call_later.assert_called_once_with(2, slf.execute)


    def test_register(self):
        """Unit tests for Tache.register method."""
        # def register(self)
        register = model_actions.Tache.register

        tache_timestamp = datetime.datetime(2021, 4, 25, 12, 2)
        now_timestamp = datetime.datetime(2021, 3, 22, 2, 20, 4)
        delay = (tache_timestamp - now_timestamp).total_seconds()

        slf = mock.Mock(model_actions.Tache, timestamp=tache_timestamp)
        with freezegun.freeze_time(now_timestamp):
            register(slf)
        config.loop.call_later.assert_called_once_with(delay, slf.execute)
        self.assertEqual(slf.handler, config.loop.call_later.return_value)


    def test_cancel(self):
        """Unit tests for Tache.cancel method."""
        # def cancel(self)
        cancel = model_actions.Tache.cancel
        slf = mock.Mock(model_actions.Tache)
        class EffectSaver:
            called = False
            @classmethod
            def save(cls):
                cls.called = True
        slf.handler = mock.Mock()
        slf.handler.cancel.side_effect = EffectSaver.save
        self.assertTrue(hasattr(slf, "handler"))
        cancel(slf)
        self.assertFalse(hasattr(slf, "handler"))
        self.assertTrue(EffectSaver.called)

        # no handler
        slf = mock.Mock(model_actions.Tache)
        slf.handler.cancel.side_effect = RuntimeError
        cancel(slf)
        self.assertTrue(hasattr(slf, "handler"))


    @mock.patch("lgrez.bdd.base.TableBase.add")
    def test_add(self, sa_patch):
        """Unit tests for Tache.add method."""
        # def add(self, *other)
        add = model_actions.Tache.add
        # one
        slf = mock.Mock(model_actions.Tache)
        add(slf)
        slf.register.assert_called_once()
        sa_patch.assert_called_once()
        sa_patch.reset_mock()
        # several
        slf = mock.Mock(model_actions.Tache)
        other = [mock.Mock(model_actions.Tache) for i in range(5)]
        add(slf, *other)
        slf.register.assert_called_once()
        for oth in other:
            oth.register.assert_called_once()
        sa_patch.assert_called_once_with(*other)


    @mock.patch("lgrez.bdd.base.TableBase.delete")
    def test_delete(self, sd_patch):
        """Unit tests for Tache.delete method."""
        # def delete(self, *other)
        delete = model_actions.Tache.delete
        # one
        slf = mock.Mock(model_actions.Tache)
        delete(slf)
        slf.cancel.assert_called_once()
        sd_patch.assert_called_once()
        sd_patch.reset_mock()
        # several
        slf = mock.Mock(model_actions.Tache)
        other = [mock.Mock(model_actions.Tache) for i in range(5)]
        delete(slf, *other)
        slf.cancel.assert_called_once()
        for oth in other:
            oth.cancel.assert_called_once()
        sd_patch.assert_called_once_with(*other)
