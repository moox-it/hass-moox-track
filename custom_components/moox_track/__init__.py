"""The MOOX Track integration.

This integration is based on Home Assistant's original implementation, which we adapted and extended to ensure stable operation and full compatibility with MOOX Track.

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
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .const import CONF_EVENTS
from .coordinator import MooxServerCoordinator
from .moox_client import MooxClient

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MOOX Track from a config entry."""
    if CONF_USERNAME not in entry.data or CONF_PASSWORD not in entry.data:
        raise ConfigEntryAuthFailed(
            "Username and password are required for MOOX Track"
        )
    # Ensure required fields exist (with defaults for migration compatibility)
    ssl = entry.data.get(CONF_SSL, True)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, True)
    client_session = async_create_clientsession(
        hass,
        cookie_jar=CookieJar(
            unsafe=not ssl or not verify_ssl
        ),
    )
    coordinator = MooxServerCoordinator(
        hass=hass,
        config_entry=entry,
        client=MooxClient(
            client_session=client_session,
            host=entry.data.get(CONF_HOST, "app.moox.it"),
            port=entry.data.get(CONF_PORT, 443),
            username=entry.data[CONF_USERNAME],
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
        # Clean up any WebSocket connections if they exist
        # Note: WebSocket is not actively used, but cleanup is safe
        if coordinator and hasattr(coordinator.client, "close_websocket"):
            try:
                await coordinator.client.close_websocket()
            except (AttributeError, RuntimeError, ConnectionError):
                # Ignore cleanup errors during shutdown
                pass
        entry.runtime_data = None
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle an options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry from older versions."""
    if entry.version == 0:
        data = dict(entry.data)
        if CONF_USERNAME not in data or CONF_PASSWORD not in data:
            return False
        # Add default server settings if missing (for migration from old versions)
        if CONF_HOST not in data:
            data[CONF_HOST] = "app.moox.it"
        if CONF_PORT not in data:
            data[CONF_PORT] = 443
        if CONF_SSL not in data:
            data[CONF_SSL] = True
        if CONF_VERIFY_SSL not in data:
            data[CONF_VERIFY_SSL] = True
        hass.config_entries.async_update_entry(entry, data=data, version=1)
        return True
    
    return True
