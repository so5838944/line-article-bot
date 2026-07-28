import base64
import hashlib
import hmac

import httpx

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def verify_signature(channel_secret: str, body: bytes, signature: str) -> bool:
    hash_value = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash_value).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature)


def reply_message(channel_access_token: str, reply_token: str, text: str) -> None:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {channel_access_token}",
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}],
    }
    response = httpx.post(LINE_REPLY_URL, headers=headers, json=payload, timeout=10.0)
    response.raise_for_status()
