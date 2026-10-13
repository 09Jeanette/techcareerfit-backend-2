"""Optional SMTP email. If SMTP_HOST is empty, messages are logged instead of sent."""
import logging
import smtplib
from email.message import EmailMessage

from ..config import get_settings

log = logging.getLogger("mailer")


def send(to: str, subject: str, body: str) -> bool:
    s = get_settings()
    if not s.smtp_host:
        log.info("SMTP disabled. Would send to %s: %s", to, subject)
        return False
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = s.smtp_from, to, subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            if s.smtp_user:
                smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(msg)
        return True
    except Exception:  # never break a request because email failed
        log.exception("Email to %s failed", to)
        return False
