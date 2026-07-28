import base64
import hashlib
import hmac

from line_client import verify_signature


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
