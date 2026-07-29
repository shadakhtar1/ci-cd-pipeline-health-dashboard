from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SMTPEmailService:
    """Send failure notifications for CI/CD pipeline runs."""

    def __init__(self) -> None:
        self.smtp_host = settings.smtp_host or "localhost"
        self.smtp_port = settings.smtp_port or 25
        self.smtp_username = settings.smtp_username or ""
        self.smtp_password = settings.smtp_password or ""
        self.from_email = settings.from_email or "noreply@example.com"
        self.to_email = settings.to_email or ""

    def send_failure_alert(self, *, pipeline_name: str, build_number: int, branch: str | None, duration: int | None, logs_url: str | None) -> bool:
        if not self.to_email:
            logger.warning("Email recipient is not configured")
            return False

        subject = f"CI/CD Failure Alert: {pipeline_name} #{build_number}"
        html_body = self._build_html_body(
            pipeline_name=pipeline_name,
            build_number=build_number,
            branch=branch,
            duration=duration,
            logs_url=logs_url,
        )

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.from_email
        message["To"] = self.to_email
        message.set_content("Plain text fallback")
        message.add_alternative(html_body, subtype="html")

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as smtp:
                if self.smtp_username and self.smtp_password:
                    smtp.starttls()
                    smtp.login(self.smtp_username, self.smtp_password)
                smtp.send_message(message)
            logger.info(
                "Failure alert email sent",
                extra={"pipeline_name": pipeline_name, "build_number": build_number},
            )
            return True
        except Exception as exc:
            logger.exception("Failed to send email alert", extra={"error": str(exc)})
            return False

    def _build_html_body(self, *, pipeline_name: str, build_number: int, branch: str | None, duration: int | None, logs_url: str | None) -> str:
        branch_text = branch or "unknown"
        duration_text = f"{duration}s" if duration is not None else "n/a"
        logs_text = logs_url or "Not available"
        return f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #222;">
            <h2>Pipeline Failure Alert</h2>
            <p>The pipeline <strong>{pipeline_name}</strong> failed during build <strong>#{build_number}</strong>.</p>
            <ul>
              <li><strong>Branch:</strong> {branch_text}</li>
              <li><strong>Duration:</strong> {duration_text}</li>
              <li><strong>Logs:</strong> <a href="{logs_text}">{logs_text}</a></li>
            </ul>
            <p>Please investigate the failed run immediately.</p>
          </body>
        </html>
        """
