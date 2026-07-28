import base64
import hashlib
import hmac
from unittest.mock import MagicMock, patch

import httpx
import pytest

from line_client import LINE_REPLY_URL, reply_message, verify_signature


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
        mock_post.return_value.raise_for_status.assert_called_once()


def test_reply_message_raises_on_http_error():
    with patch("line_client.httpx.post") as mock_post:
        error_response = MagicMock(status_code=500)
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "server error", request=MagicMock(), response=error_response
        )
        mock_post.return_value = error_response

        with pytest.raises(httpx.HTTPStatusError):
            reply_message("token123", "reply-token-abc", "こんにちは")
