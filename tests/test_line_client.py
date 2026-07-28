import base64
import hashlib
import hmac
from unittest.mock import MagicMock, patch

from line_client import LINE_REPLY_URL, verify_signature


def _sign(secret: str, body: bytes) -> str:
    hash_value = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(hash_value).decode("utf-8")


def test_verify_signature_accepts_valid_signature():
    secret = "test-secret"
    body = b'{"events": []}'
    signature = _sign(secret, body)

    assert verify_signature(secret, body, signature) is True


def test_verify_signature_rejects_invalid_signature():
    secret = "test-secret"
    body = b'{"events": []}'

    assert verify_signature(secret, body, "not-a-valid-signature") is False


from line_client import reply_message


def test_reply_message_sends_correct_payload():
    with patch("line_client.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)

        reply_message("token123", "reply-token-abc", "こんにちは")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == LINE_REPLY_URL
        assert kwargs["headers"]["Authorization"] == "Bearer token123"
        assert kwargs["json"]["replyToken"] == "reply-token-abc"
        assert kwargs["json"]["messages"][0] == {"type": "text", "text": "こんにちは"}
