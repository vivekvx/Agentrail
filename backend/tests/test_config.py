from __future__ import annotations

import pytest

from app.core.config import _DEV_SECRET, Settings

STRONG = "x" * 32


def test_default_secret_allowed_in_development() -> None:
    s = Settings(environment="development", secret_key=_DEV_SECRET)
    assert s.is_production is False


def test_default_secret_rejected_in_production() -> None:
    with pytest.raises(ValueError, match="SECRET_KEY must be changed"):
        Settings(environment="production", secret_key=_DEV_SECRET)


def test_strong_secret_allowed_in_production() -> None:
    s = Settings(environment="production", secret_key=STRONG)
    assert s.is_production is True
    assert s.secret_key == STRONG


def test_short_secret_rejected_everywhere() -> None:
    with pytest.raises(ValueError, match="at least 16 characters"):
        Settings(environment="development", secret_key="short")


def test_invalid_algorithm_rejected() -> None:
    with pytest.raises(ValueError, match="algorithm"):
        Settings(secret_key=STRONG, algorithm="none")


@pytest.mark.parametrize("value", ["production", "Production", " PRODUCTION "])
def test_is_production_is_case_and_space_insensitive(value: str) -> None:
    with pytest.raises(ValueError, match="SECRET_KEY must be changed"):
        Settings(environment=value, secret_key=_DEV_SECRET)
