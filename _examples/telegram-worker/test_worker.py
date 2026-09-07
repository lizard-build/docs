import unittest
from unittest.mock import Mock
from worker import process_updates


class WorkerTests(unittest.TestCase):
    def test_echo_and_offset(self):
        send = Mock()
        offset = process_updates([{"update_id": 8, "message": {"text": "hello", "chat": {"id": 12}}}], send)
        send.assert_called_once_with("sendMessage", {"chat_id": 12, "text": "Echo: hello"})
        self.assertEqual(offset, 9)

    def test_ignores_non_text_but_advances(self):
        send = Mock()
        self.assertEqual(process_updates([{"update_id": 9, "message": {"photo": []}}], send), 10)
        send.assert_not_called()

    def test_failed_send_does_not_confirm_update(self):
        send = Mock(side_effect=RuntimeError("unavailable"))
        with self.assertRaises(RuntimeError):
            process_updates([{"update_id": 8, "message": {"text": "hello", "chat": {"id": 12}}}], send)

    def test_empty_poll(self):
        self.assertIsNone(process_updates([], Mock()))


if __name__ == "__main__":
    unittest.main()
