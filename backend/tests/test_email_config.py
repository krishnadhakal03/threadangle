from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def clean_email_env(monkeypatch):
    keys = [
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "SMTP_FROM",
        "SMTP_FROM_EMAIL",
        "SMTP_STARTTLS",
        "SMTP_USE_TLS",
        "CONTACT_TO_EMAIL",
        "ZOHO_EMAIL",
        "ZOHO_PASSWORD",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)

    import email_service

    email_service._email_config_logged = False
    yield
    email_service._email_config_logged = False


def test_smtp_config_supports_production_and_legacy_env(monkeypatch):
    import email_service

    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "smtp-user@example.test")
    monkeypatch.setenv("SMTP_PASSWORD", "fake-secret")
    monkeypatch.setenv("SMTP_FROM", "Threadangle <from@example.test>")
    monkeypatch.setenv("SMTP_STARTTLS", "true")
    monkeypatch.setenv("CONTACT_TO_EMAIL", "info@kriangle.com")

    config = email_service.get_smtp_config()

    assert config["host"] == "smtp.example.test"
    assert config["port"] == 587
    assert config["username"] == "smtp-user@example.test"
    assert config["password"] == "fake-secret"
    assert config["from_header"] == "Threadangle <from@example.test>"
    assert config["start_tls"] is True
    assert config["use_tls"] is False
    assert config["contact_to_email"] == "info@kriangle.com"

    monkeypatch.delenv("SMTP_USER")
    monkeypatch.setenv("ZOHO_EMAIL", "legacy@example.test")
    assert email_service.get_smtp_config()["username"] == "legacy@example.test"


@pytest.mark.asyncio
async def test_contact_notification_uses_contact_to_email_and_reply_to(monkeypatch):
    import email_service

    sent = AsyncMock(return_value={})
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_USER", "smtp-user@example.test")
    monkeypatch.setenv("SMTP_PASSWORD", "fake-secret")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "from@example.test")
    monkeypatch.setenv("CONTACT_TO_EMAIL", "info@kriangle.com")
    monkeypatch.setattr(email_service.aiosmtplib, "send", sent)

    ok = await email_service.send_admin_contact_notification(
        {
            "name": "Test User",
            "email": "visitor@example.test",
            "subject": "Question",
            "message": "This is a long enough test contact message.",
        }
    )

    assert ok is True
    message = sent.await_args.args[0]
    assert message["To"] == "info@kriangle.com"
    assert message["Reply-To"] == "visitor@example.test"


@pytest.mark.asyncio
async def test_missing_smtp_config_does_not_send_or_log_secret(monkeypatch, caplog):
    import email_service

    fake_secret = "super-secret-password"
    sent = AsyncMock(return_value={})
    monkeypatch.setenv("SMTP_PASSWORD", fake_secret)
    monkeypatch.setattr(email_service.aiosmtplib, "send", sent)

    ok = await email_service.send_email_async("user@example.test", "Subject", "<p>Body</p>")

    assert ok is False
    sent.assert_not_awaited()
    assert fake_secret not in caplog.text
