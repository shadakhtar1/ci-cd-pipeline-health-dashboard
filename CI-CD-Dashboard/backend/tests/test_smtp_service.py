from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import smtplib

from app.mail.smtp_service import SMTPEmailService


class FakeSMTP:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.sent_messages = []
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        pass

    def login(self, username, password):
        self.username = username
        self.password = password

    def send_message(self, message):
        self.calls += 1
        self.sent_messages.append(message)


def test_send_failure_alert_retries_after_transient_smtp_error():
    settings = SimpleNamespace(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user",
        smtp_password="pass",
        from_email="alerts@example.com",
        to_email="ops@example.com",
        smtp_recipients="team@example.com,alerts@example.com",
    )

    smtp_instances = []

    class FlakySMTP(FakeSMTP):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            smtp_instances.append(self)

        def __enter__(self):
            return self

        def send_message(self, message):
            self.calls += 1
            if len(smtp_instances) == 1:
                raise smtplib.SMTPException("temporary failure")
            self.sent_messages.append(message)

    with patch("app.mail.smtp_service.get_settings", return_value=settings), patch("app.mail.smtp_service.smtplib.SMTP", FlakySMTP):
        service = SMTPEmailService()
        result = service.send_failure_alert(
            pipeline_name="deploy",
            build_number=42,
            branch="main",
            commit_sha="abc123",
            status="failure",
            duration=320,
            build_url="https://ci.example/builds/42",
            timestamp=datetime(2026, 7, 31, 12, 0, 0),
            repository="octo/demo",
            workflow_name="deploy",
            started_at=datetime(2026, 7, 31, 11, 0, 0),
        )

    assert result is True
    assert len(smtp_instances) == 2
    assert smtp_instances[-1].calls == 1
    sent_message = smtp_instances[-1].sent_messages[0]
    assert sent_message["Subject"] == "CI/CD Alert: Workflow Failed"
    html_payload = sent_message.get_payload()[1].get_payload()
    assert "Workflow Name" in html_payload
    assert "Repository" in html_payload
    assert "Started Time" in html_payload


def test_send_failure_alert_uses_html_template_and_recipients():
    settings = SimpleNamespace(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        from_email="alerts@example.com",
        to_email="primary@example.com",
        smtp_recipients="ops@example.com,devops@example.com",
    )

    with patch("app.mail.smtp_service.get_settings", return_value=settings), patch("app.mail.smtp_service.smtplib.SMTP", FakeSMTP):
        service = SMTPEmailService()
        result = service.send_failure_alert(
            pipeline_name="build",
            build_number=7,
            branch="release/1.0",
            commit_sha="deadbeef",
            status="failure",
            duration=180,
            build_url="https://ci.example/builds/7",
            timestamp=datetime(2026, 7, 31, 12, 30, 0),
            repository="octo/demo",
            workflow_name="build",
            started_at=datetime(2026, 7, 31, 12, 0, 0),
        )

    assert result is True
    assert service.recipients == ["ops@example.com", "devops@example.com", "primary@example.com"]
