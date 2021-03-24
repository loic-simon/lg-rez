import unittest
from unittest import mock

from lgrez.blocs import webhook



class TestWebhook(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.blocs.webhook module."""

    @mock.patch("discord_webhook.DiscordWebhook")
    def test_send(self, wh_patch):
        """Unit tests for webhook.send function."""
        # def send(message, url)
        send = webhook.send
        # unique case
        message = mock.Mock()
        url = mock.Mock()
        rep = send(message, url)
        wh_patch.assert_called_once_with(content=message, url=url)
        wh_patch.return_value.execute.assert_called_once()
        self.assertEqual(rep, wh_patch.return_value.execute.return_value)
