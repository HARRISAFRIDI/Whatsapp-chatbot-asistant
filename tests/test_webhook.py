import hashlib
import hmac
import json
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


class WebhookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.secret_patch = patch.object(settings, "whatsapp_app_secret", "test-secret")
        self.secret_patch.start()
        self.addCleanup(self.secret_patch.stop)

    def _signature(self, body: bytes) -> str:
        digest = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def test_verification_returns_challenge_for_matching_token(self) -> None:
        with patch.object(settings, "whatsapp_verify_token", "verify-me"):
            response = self.client.get(
                "/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "verify-me",
                    "hub.challenge": "challenge-value",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "challenge-value")

    def test_post_rejects_invalid_signature(self) -> None:
        response = self.client.post(
            "/webhook",
            content=b"{}",
            headers={"X-Hub-Signature-256": "sha256=invalid"},
        )

        self.assertEqual(response.status_code, 401)

    def test_post_replies_to_text_and_ignores_status_updates(self) -> None:
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "15551234567",
                                        "text": {"body": " Hello Webora "},
                                    }
                                ],
                                "statuses": [{"id": "message-id"}],
                            }
                        }
                    ]
                }
            ]
        }
        body = json.dumps(payload).encode()
        send = AsyncMock()
        with (
            patch("app.main.generate_reply", return_value="Hello!"),
            patch("app.main.send_message", send),
        ):
            response = self.client.post(
                "/webhook",
                content=body,
                headers={"X-Hub-Signature-256": self._signature(body)},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        send.assert_awaited_once_with("15551234567", "Hello!")


if __name__ == "__main__":
    unittest.main()
