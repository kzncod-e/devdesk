import pytest

from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("s3cret!")
    assert h != "s3cret!"
    assert verify_password("s3cret!", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_roundtrip():
    token = create_token(subject="42", token_type="access", secret="k", minutes=15)
    payload = decode_token(token, secret="k")
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_jwt_rejects_bad_secret():
    token = create_token(subject="42", token_type="access", secret="k", minutes=15)
    with pytest.raises(Exception):
        decode_token(token, secret="other")


def test_jwt_rejects_expired():
    token = create_token(subject="42", token_type="access", secret="k", minutes=-1)
    with pytest.raises(Exception):
        decode_token(token, secret="k")
