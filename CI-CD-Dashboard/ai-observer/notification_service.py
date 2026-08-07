"""SMTP notification service for AI observer incident reports."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console


class NotificationService:
    """Send incident notifications by email with optional attachments."""

    def __init__(self) -> None:
        """Load SMTP configuration from environment variables."""
        load_dotenv()
        self.console = Console()
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_to = os.getenv("EMAIL_TO")

    def send_email(
        self,
        subject: str,
        body: str,
        attachment: str | None = None,
    ) -> bool:
        """Send an email with an optional attachment and return success status."""
        self.console.print("[cyan]Sending notification email...[/cyan]")

        if not all([self.smtp_host, self.smtp_username, self.smtp_password, self.email_from, self.email_to]):
            self.console.print("[yellow]SMTP configuration is incomplete.[/yellow]")
            return False

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.email_from
        message["To"] = self.email_to
        message.set_content(body)

        if attachment:
            attachment_path = Path(attachment)
            if attachment_path.exists():
                message.add_attachment(
                    attachment_path.read_bytes(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=attachment_path.name,
                )
            else:
                self.console.print("[yellow]Attachment file does not exist.[/yellow]")
                return False

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp_client:
                smtp_client.starttls()
                smtp_client.login(self.smtp_username, self.smtp_password)
                smtp_client.send_message(message)
            self.console.print("[green]Notification email sent successfully.[/green]")
            return True
        except Exception as exc:  # noqa: BLE001
            self.console.print(f"[yellow]Failed to send notification email: {exc}[/yellow]")
            return False
