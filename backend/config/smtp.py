"""
SMTP Configuration
------------------
Retrieves SMTP configuration from LocalStack Secrets Manager.
Falls back to Mailpit defaults for local development.

Usage:
    from backend.config.smtp import get_smtp_config, SMTPConfig

    config = await get_smtp_config()
    # Use config.host, config.port, config.from_email, etc.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional

from backend.config.services import SERVICES

logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    """SMTP server configuration"""

    host: str
    port: int
    from_email: str
    from_name: str = "Agent Foundry"
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = False
    use_ssl: bool = False

    def __repr__(self) -> str:
        """Safe repr that doesn't expose password"""
        return (
            f"SMTPConfig(host={self.host!r}, port={self.port}, "
            f"from_email={self.from_email!r}, use_tls={self.use_tls})"
        )


# Cache the config after first load
_cached_config: Optional[SMTPConfig] = None


def get_default_smtp_config() -> SMTPConfig:
    """
    Get default SMTP configuration using service discovery.
    Uses Mailpit for local development.
    """
    return SMTPConfig(
        host=SERVICES.MAILPIT,
        port=SERVICES.MAILPIT_SMTP_PORT,
        from_email="noreply@agentfoundry.local",
        from_name="Agent Foundry",
        use_tls=False,
        use_ssl=False,
    )


async def get_smtp_config(force_reload: bool = False) -> SMTPConfig:
    """
    Get SMTP configuration from LocalStack or defaults.

    Configuration is retrieved from LocalStack Secrets Manager at path:
    agentfoundry/dev/platform/smtp_config

    Falls back to Mailpit defaults if not configured.

    Args:
        force_reload: If True, bypass cache and reload from LocalStack

    Returns:
        SMTPConfig dataclass with connection details
    """
    global _cached_config

    if _cached_config is not None and not force_reload:
        return _cached_config

    try:
        from backend.config.secrets import secrets_manager

        # Try to load from LocalStack
        secret_value = await secrets_manager.get_secret(
            organization_id="platform",
            secret_name="smtp_config",
            domain_id=None,
        )

        if secret_value:
            config_data = json.loads(secret_value)
            _cached_config = SMTPConfig(
                host=config_data.get("host", SERVICES.MAILPIT),
                port=config_data.get("port", SERVICES.MAILPIT_SMTP_PORT),
                from_email=config_data.get("from_email", "noreply@agentfoundry.local"),
                from_name=config_data.get("from_name", "Agent Foundry"),
                username=config_data.get("username"),
                password=config_data.get("password"),
                use_tls=config_data.get("use_tls", False),
                use_ssl=config_data.get("use_ssl", False),
            )
            logger.info(f"SMTP config loaded from LocalStack: {_cached_config}")
            return _cached_config

    except Exception as e:
        logger.warning(f"Failed to load SMTP config from LocalStack: {e}")

    # Fall back to defaults (Mailpit)
    logger.info("Using default SMTP config (Mailpit)")
    _cached_config = get_default_smtp_config()
    return _cached_config


def get_smtp_config_sync() -> SMTPConfig:
    """
    Synchronous version - returns cached config or defaults.

    Note: This won't load from LocalStack if not already cached.
    Use get_smtp_config() async version for full functionality.
    """
    global _cached_config

    if _cached_config is not None:
        return _cached_config

    return get_default_smtp_config()


async def send_email(
    to: str | list[str],
    subject: str,
    body: str,
    html: Optional[str] = None,
    config: Optional[SMTPConfig] = None,
) -> bool:
    """
    Send an email using the configured SMTP server.

    Args:
        to: Recipient email address(es)
        subject: Email subject line
        body: Plain text body
        html: Optional HTML body
        config: Optional SMTPConfig override

    Returns:
        True if sent successfully, False otherwise
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    if config is None:
        config = await get_smtp_config()

    # Normalize recipients
    recipients = [to] if isinstance(to, str) else to

    # Build message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{config.from_name} <{config.from_email}>"
    msg["To"] = ", ".join(recipients)

    # Attach plain text
    msg.attach(MIMEText(body, "plain"))

    # Attach HTML if provided
    if html:
        msg.attach(MIMEText(html, "html"))

    try:
        # Connect to SMTP server
        if config.use_ssl:
            server = smtplib.SMTP_SSL(config.host, config.port)
        else:
            server = smtplib.SMTP(config.host, config.port)

        if config.use_tls:
            server.starttls()

        # Authenticate if credentials provided
        if config.username and config.password:
            server.login(config.username, config.password)

        # Send email
        server.sendmail(config.from_email, recipients, msg.as_string())
        server.quit()

        logger.info(f"Email sent to {recipients}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {recipients}: {e}")
        return False
