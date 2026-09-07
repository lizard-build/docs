import unittest
from check_bot import check


class PreflightTests(unittest.TestCase):
    def test_polling_bot(self):
        calls = []
        def call(token, method, payload):
            calls.append(method)
            return {"username": "example_bot"} if method == "getMe" else {"url": ""}
        self.assertEqual(check("test-only", call), "example_bot")
        self.assertEqual(calls, ["getMe", "getWebhookInfo"])

    def test_rejects_webhook_without_changing_it(self):
        def call(token, method, payload):
            return {"username": "example_bot"} if method == "getMe" else {"url": "https://example.test/hook"}
        with self.assertRaisesRegex(RuntimeError, "active webhook"):
            check("test-only", call)

    def test_auth_failure_stops_before_webhook_lookup(self):
        calls = []
        def call(token, method, payload):
            calls.append(method)
            raise RuntimeError("Unauthorized")
        with self.assertRaises(RuntimeError):
            check("test-only", call)
        self.assertEqual(calls, ["getMe"])
