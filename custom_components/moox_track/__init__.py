"""The MOOX Track integration.

Copyright 2025 MOOX SRLS
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

from datetime import timedelta
from typing import cast

from aiohttp import CookieJar

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .const import CONF_EMAIL, CONF_EVENTS, CONF_USERNAME_DEPRECATED, LOGGER
from .coordinator import MooxServerCoordinator
from .moox_client import MooxClient

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]


def _get_email_from_entry(entry: ConfigEntry) -> str | None:
    """Get email from config entry, supporting both old and new keys."""
    return entry.data.get(CONF_EMAIL) or entry.data.get(CONF_USERNAME_DEPRECATED)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MOOX Track from a config entry."""
    email = _get_email_from_entry(entry)
    if not email or CONF_PASSWORD not in entry.data:
        raise ConfigEntryAuthFailed("Email and password are required for MOOX Track")

    ssl = entry.data.get(CONF_SSL, True)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, True)
    client_session = async_create_clientsession(
        hass,
        cookie_jar=CookieJar(unsafe=not ssl or not verify_ssl),
    )
    coordinator = MooxServerCoordinator(
        hass=hass,
        config_entry=entry,
        client=MooxClient(
            client_session=client_session,
            host=entry.data.get(CONF_HOST, "app.moox.it"),
            port=entry.data.get(CONF_PORT, 443),
            username=email,
            password=entry.data[CONF_PASSWORD],
            ssl=ssl,
            verify_ssl=verify_ssl,
        ),
    )

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    if entry.options.get(CONF_EVENTS):
        entry.async_on_unload(
            async_track_time_interval(
                hass,
                coordinator.import_events,
                timedelta(seconds=30),
                cancel_on_shutdown=True,
                name="moox_track_import_events",
            )
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: MooxServerCoordinator | None = cast(
        MooxServerCoordinator | None, entry.runtime_data
    )
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        if coordinator:
            try:
                await coordinator.client.close_websocket()
            except (AttributeError, RuntimeError, ConnectionError):
                pass
        entry.runtime_data = None
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle an options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry from older versions."""
    LOGGER.debug("Migrating MOOX Track config entry from version %s", entry.version)
    version = entry.version

    if version < 1:
        data = dict(entry.data)
        if CONF_USERNAME_DEPRECATED not in data or CONF_PASSWORD not in data:
            return False
        if CONF_HOST not in data:
            data[CONF_HOST] = "app.moox.it"
        if CONF_PORT not in data:
            data[CONF_PORT] = 443
        if CONF_SSL not in data:
            data[CONF_SSL] = True
        if CONF_VERIFY_SSL not in data:
            data[CONF_VERIFY_SSL] = True
        hass.config_entries.async_update_entry(entry, data=data, version=1)
        version = 1
        LOGGER.info("Migrated MOOX Track config entry to version 1")

    if version < 2:
        data = dict(entry.data)
        if CONF_USERNAME_DEPRECATED in data:
            data[CONF_EMAIL] = data[CONF_USERNAME_DEPRECATED]
            del data[CONF_USERNAME_DEPRECATED]
        elif CONF_EMAIL not in data:
            LOGGER.error("Cannot migrate MOOX Track config entry: missing email")
            return False
        hass.config_entries.async_update_entry(entry, data=data, version=2)
        LOGGER.info("Migrated MOOX Track config entry to version 2")

    return True
