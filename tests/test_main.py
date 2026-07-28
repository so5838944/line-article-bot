import base64
import hashlib
import hmac
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _signature_headers(body: bytes) -> dict:
    hash_value = hmac.new(
        main.LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256
    ).digest()
    signature = base64.b64encode(hash_value).decode("utf-8")
    return {"X-Line-Signature": signature}


def test_webhook_rejects_invalid_signature():
    body = json.dumps({"events": []}).encode("utf-8")

    response = client.post(
        "/webhook", content=body, headers={"X-Line-Signature": "invalid"}
    )

    assert response.status_code == 401


def test_webhook_replies_with_draft_for_text_message():
    body = json.dumps({
        "events": [{
            "type": "message",
            "replyToken": "reply-token-abc",
            "message": {"type": "text", "text": "今日フォロワーが伸びた話"},
        }]
    }).encode("utf-8")

    with patch.object(
        main.gemini_client, "generate_draft", return_value="生成された草稿"
    ) as mock_generate, patch("main.reply_message") as mock_reply:
        response = client.post("/webhook", content=body, headers=_signature_headers(body))

    assert response.status_code == 200
    mock_generate.assert_called_once_with("今日フォロワーが伸びた話")
    mock_reply.assert_called_once_with(
        main.LINE_CHANNEL_ACCESS_TOKEN, "reply-token-abc", "生成された草稿"
    )


def test_webhook_asks_for_text_when_message_is_not_text():
    body = json.dumps({
        "events": [{
            "type": "message",
            "replyToken": "reply-token-abc",
            "message": {"type": "image"},
        }]
    }).encode("utf-8")

    with patch("main.reply_message") as mock_reply:
        response = client.post("/webhook", content=body, headers=_signature_headers(body))

    assert response.status_code == 200
    mock_reply.assert_called_once_with(
        main.LINE_CHANNEL_ACCESS_TOKEN, "reply-token-abc", "テキストで送ってください。"
    )


def test_webhook_asks_for_more_detail_when_message_too_short():
    body = json.dumps({
        "events": [{
            "type": "message",
            "replyToken": "reply-token-abc",
            "message": {"type": "text", "text": "ok"},
        }]
    }).encode("utf-8")

    with patch("main.reply_message") as mock_reply:
        response = client.post("/webhook", content=body, headers=_signature_headers(body))

    assert response.status_code == 200
    mock_reply.assert_called_once_with(
        main.LINE_CHANNEL_ACCESS_TOKEN, "reply-token-abc", "もう少し詳しく送ってください。"
    )


def test_webhook_replies_with_error_message_when_gemini_fails():
    body = json.dumps({
        "events": [{
            "type": "message",
            "replyToken": "reply-token-abc",
            "message": {"type": "text", "text": "今日フォロワーが伸びた話"},
        }]
    }).encode("utf-8")

    with patch.object(
        main.gemini_client, "generate_draft", side_effect=RuntimeError("boom")
    ), patch("main.reply_message") as mock_reply:
        response = client.post("/webhook", content=body, headers=_signature_headers(body))

    assert response.status_code == 200
    mock_reply.assert_called_once_with(
        main.LINE_CHANNEL_ACCESS_TOKEN,
        "reply-token-abc",
        "生成に失敗しました。もう一度送ってください。",
    )
