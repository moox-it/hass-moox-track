"""Config flow for MOOX Track."""
from homeassistant.helpers import config_entry_flow

from .const import DOMAIN

config_entry_flow.register_webhook_flow(
    DOMAIN,
    "MOOX Track Webhook",
    {"docs_url": "https://moox.it"},
)
