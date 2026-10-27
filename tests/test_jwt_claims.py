import base64
import hashlib
import hmac
import json
import time

import pytest

from markio.auth.jwt_auth import _verify_hs256

SECRET = "test-secret"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _token(payload_json: str) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64(payload_json.encode())
    signing_input = f"{header}.{body}".encode("ascii")
    sig = hmac.new(SECRET.encode(), signing_input, hashlib.sha256).digest()
    return f"{header}.{body}.{_b64(sig)}"


def _verify(payload_json: str) -> dict:
    return _verify_hs256(_token(payload_json), SECRET, "HS256")


def test_valid_token_without_nbf_still_accepted():
    exp = int(time.time()) + 60
    assert _verify(json.dumps({"sub": "u", "exp": exp}))["sub"] == "u"


def test_nbf_in_past_accepted():
    now = int(time.time())
    assert _verify(json.dumps({"sub": "u", "exp": now + 60, "nbf": now - 5}))


def test_nbf_in_future_rejected():
    now = int(time.time())
    with pytest.raises(ValueError, match="not yet valid"):
        _verify(json.dumps({"sub": "u", "exp": now + 600, "nbf": now + 300}))


@pytest.mark.parametrize("raw", ["Infinity", "NaN"])
def test_non_finite_exp_rejected(raw):
    with pytest.raises(ValueError, match="finite"):
        _verify('{"sub": "u", "exp": %s}' % raw)


def test_non_finite_nbf_rejected():
    exp = int(time.time()) + 60
    with pytest.raises(ValueError, match="nbf"):
        _verify('{"sub": "u", "exp": %d, "nbf": NaN}' % exp)
