from __future__ import annotations

import smtplib
import time
from datetime import datetime
from email.message import EmailMessage
from html import escape

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SMTPEmailService:
    """Send failure notifications for CI/CD pipeline runs."""

    def __init__(self) -> None:
        settings = get_settings()
        self.smtp_host = settings.smtp_host or "localhost"
        self.smtp_port = settings.smtp_port or 25
        self.smtp_username = settings.smtp_username or ""
        self.smtp_password = settings.smtp_password or ""
        self.from_email = settings.from_email or "noreply@example.com"
        self.to_email = settings.to_email or ""
        self.smtp_recipients = getattr(settings, "smtp_recipients", "") or ""
        self.email_alerts_enabled = getattr(settings, "email_alerts_enabled", True)
        self.recipients = self._build_recipients()
        self.max_retries = 3
        self.retry_delay_seconds = 2

    def send_failure_alert(
        self,
        *,
        pipeline_name: str,
        build_number: int,
        branch: str | None,
        commit_sha: str | None,
        status: str | None,
        duration: int | None,
        build_url: str | None,
        timestamp: datetime | None,
    ) -> bool:
        if not self.email_alerts_enabled:
            logger.info("Email alerts are disabled")
            return False

        if not self.recipients:
            logger.warning("Email recipient is not configured")
            return False

        subject = f"CI/CD Failure Alert: {pipeline_name} #{build_number}"
        html_body = self._build_html_body(
            pipeline_name=pipeline_name,
            build_number=build_number,
            branch=branch,
            commit_sha=commit_sha,
            status=status,
            duration=duration,
            build_url=build_url,
            timestamp=timestamp,
        )

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.from_email
        message["To"] = ", ".join(self.recipients)
        message.set_content("A CI/CD pipeline build failed. Please review the HTML content.")
        message.add_alternative(html_body, subtype="html")

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as smtp:
                    if self.smtp_username and self.smtp_password:
                        smtp.starttls()
                        smtp.login(self.smtp_username, self.smtp_password)
                    smtp.send_message(message)
                logger.info(
                    "Failure alert email sent",
                    extra={
                        "pipeline_name": pipeline_name,
                        "build_number": build_number,
                        "attempt": attempt + 1,
                    },
                )
                return True
            except (smtplib.SMTPException, TimeoutError, OSError, ConnectionError) as exc:
                last_error = exc
                logger.warning(
                    "Temporary SMTP failure while sending alert, retrying",
                    extra={
                        "pipeline_name": pipeline_name,
                        "build_number": build_number,
                        "attempt": attempt + 1,
                        "error": str(exc),
                    },
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay_seconds * (attempt + 1))

        logger.exception(
            "Failed to send email alert after retries",
            extra={"pipeline_name": pipeline_name, "build_number": build_number, "error": str(last_error)},
        )
        return False

    def _build_recipients(self) -> list[str]:
        recipients = [item.strip() for item in self.smtp_recipients.split(",") if item.strip()]
        if self.to_email:
            recipients.append(self.to_email.strip())
        return list(dict.fromkeys(recipients))

    def _build_html_body(
        self,
        *,
        pipeline_name: str,
        build_number: int,
        branch: str | None,
        commit_sha: str | None,
        status: str | None,
        duration: int | None,
        build_url: str | None,
        timestamp: datetime | None,
    ) -> str:
        branch_text = escape(branch or "unknown")
        commit_text = escape(commit_sha or "n/a")
        status_text = escape((status or "failure").upper())
        duration_text = escape(f"{duration}s" if duration is not None else "n/a")
        build_url_text = escape(build_url or "Not available")
        timestamp_text = escape((timestamp or datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S UTC"))
        return f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.5;">
            <h2 style="color: #b42318;">Pipeline Failure Alert</h2>
            <p>The pipeline <strong>{escape(pipeline_name)}</strong> reported a failed build <strong>#{build_number}</strong>.</p>
            <ul>
              <li><strong>Workflow:</strong> {escape(pipeline_name)}</li>
              <li><strong>Branch:</strong> {branch_text}</li>
              <li><strong>Commit SHA:</strong> {commit_text}</li>
              <li><strong>Status:</strong> {status_text}</li>
              <li><strong>Duration:</strong> {duration_text}</li>
              <li><strong>Build URL:</strong> <a href="{build_url_text}">{build_url_text}</a></li>
              <li><strong>Timestamp:</strong> {timestamp_text}</li>
            </ul>
            <p>Please investigate the failed run immediately.</p>
          </body>
        </html>
        """
