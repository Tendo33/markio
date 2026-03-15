from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from markio.settings import settings


@dataclass(frozen=True)
class AuthUser:
    user_id: str
    role: str
    claims: dict


def _decode_segment(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    try:
        return base64.urlsafe_b64decode(segment + padding)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Malformed JWT segment") from exc


def _decode_json_segment(segment: str) -> dict:
    raw = _decode_segment(segment)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Malformed JWT payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("JWT payload is invalid")
    return payload


def _parse_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    return token.strip()


def _verify_hs256(token: str, secret: str, expected_alg: str) -> dict:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise ValueError("Malformed JWT") from exc

    header = _decode_json_segment(header_segment)
    payload = _decode_json_segment(payload_segment)
    algorithm = str(header.get("alg", ""))
    if algorithm != expected_alg:
        raise ValueError("JWT algorithm mismatch")

    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    signature = _decode_segment(signature_segment)
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("JWT signature verification failed")

    exp = payload.get("exp")
    if exp is None:
        raise ValueError("JWT exp is required")
    if not isinstance(exp, (int, float)):
        raise ValueError("JWT exp must be numeric")
    if time.time() >= float(exp):
        raise ValueError("JWT has expired")

    return payload


def _decode_and_validate_token(token: str) -> dict:
    algorithm = (settings.auth_jwt_algorithm or "HS256").strip().upper()
    if algorithm != "HS256":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unsupported JWT algorithm configuration",
        )
    secret = (settings.auth_jwt_secret or "").strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured",
        )
    try:
        return _verify_hs256(token=token, secret=secret, expected_alg=algorithm)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from None


async def require_auth_user(request: Request) -> AuthUser:
    token = _parse_bearer_token(request)
    claims = _decode_and_validate_token(token)

    user_id = str(claims.get("sub", "")).strip()
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    role = str(claims.get("role", "user") or "user").strip().lower()
    user = AuthUser(user_id=user_id, role=role or "user", claims=claims)
    request.state.auth_user = user
    return user


async def require_admin_user(user: AuthUser = Depends(require_auth_user)) -> AuthUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user
