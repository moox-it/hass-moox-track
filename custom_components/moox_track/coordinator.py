"""Data update coordinator for MOOX Track.

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

import asyncio
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, TypedDict, cast

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    AUTH_FAILURE_GRACE_PERIOD_HOURS,
    AUTH_NEVER_WORKED_GRACE_PERIOD_HOURS,
    CONF_CUSTOM_ATTRIBUTES,
    CONF_EVENTS,
    CONF_MAX_ACCURACY,
    CONF_SKIP_ACCURACY_FILTER_FOR,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    EVENTS,
    LOGGER,
    to_snake_case,
)
from .helpers import get_device, get_first_geofence, get_geofence_ids
from .moox_client import (
    DeviceModel,
    GeofenceModel,
    MooxAuthenticationException,
    MooxClient,
    MooxConnectionException,
    MooxException,
    MooxSessionExpiredException,
    PositionModel,
)


class MooxServerCoordinatorDataDevice(TypedDict):
    """Coordinator data for a single device."""

    device: DeviceModel
    geofence: GeofenceModel | None
    position: PositionModel
    attributes: dict[str, Any]


MooxServerCoordinatorData: TypeAlias = dict[int, MooxServerCoordinatorDataDevice]

AUTH_FAILURE_STORAGE_VERSION = 1
AUTH_FAILURE_STORAGE_KEY = "auth_failure_state"


class MooxServerCoordinator(DataUpdateCoordinator[MooxServerCoordinatorData]):
    """Coordinator to manage fetching MOOX Track data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: MooxClient,
    ) -> None:
        """Initialize the coordinator."""
        update_interval_seconds = config_entry.options.get(CONF_UPDATE_INTERVAL, 30)
        if update_interval_seconds < 30:
            update_interval_seconds = 30
            LOGGER.warning("Update interval below minimum, using 30 seconds")
        update_interval = (
            timedelta(seconds=update_interval_seconds)
            if update_interval_seconds > 0
            else None
        )
        super().__init__(
            hass=hass,
            logger=LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.client = client
        self.custom_attributes = config_entry.options.get(CONF_CUSTOM_ATTRIBUTES, [])
        self.events = config_entry.options.get(CONF_EVENTS, [])
        self.max_accuracy = config_entry.options.get(CONF_MAX_ACCURACY, 0.0)
        self.skip_accuracy_filter_for = config_entry.options.get(
            CONF_SKIP_ACCURACY_FILTER_FOR, []
        )
        self._geofences: list[GeofenceModel] = []
        self._last_event_import: datetime | None = None
        self._first_auth_failure_time: datetime | None = None
        self._auth_failure_store: Store[dict[str, Any]] = Store(
            hass,
            AUTH_FAILURE_STORAGE_VERSION,
            f"{DOMAIN}.{config_entry.entry_id}.{AUTH_FAILURE_STORAGE_KEY}",
        )
        self._storage_loaded = False
        self._storage_loading = False
        self._first_successful_update = False

    async def _load_auth_failure_state(self) -> None:
        """Load persisted auth failure state from storage."""
        if self._storage_loaded:
            return
        if self._storage_loading:
            while self._storage_loading and not self._storage_loaded:
                await asyncio.sleep(0.01)
            return
        self._storage_loading = True
        try:
            data = await self._auth_failure_store.async_load()
            if data and isinstance(data, dict):
                timestamp_str = data.get("first_auth_failure_time")
                if timestamp_str:
                    loaded_dt = datetime.fromisoformat(timestamp_str)
                    if loaded_dt.tzinfo is None:
                        loaded_dt = loaded_dt.replace(tzinfo=timezone.utc)
                    self._first_auth_failure_time = loaded_dt
            self._storage_loaded = True
        except Exception:
            self._first_auth_failure_time = None
            self._storage_loaded = True
        finally:
            self._storage_loading = False

    async def _save_auth_failure_state(self) -> None:
        """Persist auth failure state to storage."""
        try:
            if self._first_auth_failure_time is None:
                await self._auth_failure_store.async_remove()
            else:
                await self._auth_failure_store.async_save({
                    "first_auth_failure_time": self._first_auth_failure_time.isoformat(),
                })
        except Exception:
            pass

    async def _handle_server_failure(
        self, exception: MooxException, is_auth_failure: bool = False
    ) -> bool:
        """Handle server failure with grace period.

        Returns True if should escalate to user, False to continue with cached data.
        """
        ever_authenticated = self.client.ever_authenticated

        if is_auth_failure and not ever_authenticated:
            LOGGER.warning("Unable to sign in. Please verify your credentials.")
            return True

        await self._load_auth_failure_state()
        now = dt_util.utcnow()

        if ever_authenticated:
            grace_period_hours = AUTH_FAILURE_GRACE_PERIOD_HOURS
        else:
            grace_period_hours = AUTH_NEVER_WORKED_GRACE_PERIOD_HOURS

        if self._first_auth_failure_time is None:
            self._first_auth_failure_time = now
            await self._save_auth_failure_state()
            LOGGER.info("Connection issue. Retrying automatically. You'll be notified if action is needed.")
            return False

        hours_since_first_failure = (
            now - self._first_auth_failure_time
        ).total_seconds() / 3600

        if hours_since_first_failure < grace_period_hours:
            return False

        old_time = self._first_auth_failure_time
        try:
            self._first_auth_failure_time = None
            await self._save_auth_failure_state()
        except Exception:
            self._first_auth_failure_time = old_time

        LOGGER.warning("Unable to reconnect. Please sign in again to continue.")
        return True

    async def _clear_failure_tracking(self) -> None:
        """Clear failure tracking after successful update."""
        await self._load_auth_failure_state()

        if self._first_auth_failure_time is not None:
            LOGGER.info("Connection restored. Everything is working normally.")
            self._first_auth_failure_time = None
            await self._save_auth_failure_state()
        elif not self._first_successful_update:
            LOGGER.info("Connected to MOOX Track. Real-time device tracking is now active.")
            self._first_successful_update = True

    async def _async_update_data(self) -> MooxServerCoordinatorData:
        """Fetch data from MOOX Track."""
        data: MooxServerCoordinatorData = {}
        try:
            results = await asyncio.gather(
                self.client.get_devices(),
                self.client.get_positions(),
                self.client.get_geofences(),
                return_exceptions=True,
            )

            devices_result, positions_result, geofences_result = results

            auth_failure: MooxAuthenticationException | None = None
            session_failure: MooxSessionExpiredException | None = None
            connection_failure: MooxConnectionException | None = None
            other_failure: MooxException | None = None

            for result in (devices_result, positions_result, geofences_result):
                if isinstance(result, MooxAuthenticationException):
                    auth_failure = auth_failure or result
                elif isinstance(result, MooxSessionExpiredException):
                    session_failure = session_failure or result
                elif isinstance(result, MooxConnectionException):
                    connection_failure = connection_failure or result
                elif isinstance(result, MooxException):
                    other_failure = other_failure or result

            if auth_failure is not None:
                if await self._handle_server_failure(auth_failure, is_auth_failure=True):
                    raise ConfigEntryAuthFailed from auth_failure
                if self.data:
                    return self.data
                return {}

            if session_failure is not None:
                if await self._handle_server_failure(session_failure, is_auth_failure=True):
                    raise ConfigEntryAuthFailed from session_failure
                if self.data:
                    return self.data
                return {}

            if connection_failure is not None:
                if await self._handle_server_failure(connection_failure, is_auth_failure=False):
                    if not self.client.ever_authenticated:
                        raise ConfigEntryAuthFailed from connection_failure
                    raise UpdateFailed(
                        f"Server connection errors for over "
                        f"{AUTH_FAILURE_GRACE_PERIOD_HOURS} hours"
                    ) from connection_failure
                if self.data:
                    return self.data
                return {}

            if other_failure is not None:
                if await self._handle_server_failure(other_failure, is_auth_failure=False):
                    if not self.client.ever_authenticated:
                        raise ConfigEntryAuthFailed from other_failure
                    raise UpdateFailed(
                        f"Server errors for over {AUTH_FAILURE_GRACE_PERIOD_HOURS} hours"
                    ) from other_failure
                if self.data:
                    return self.data
                return {}

            if isinstance(devices_result, Exception):
                raise UpdateFailed(f"Error fetching devices: {devices_result}") from devices_result
            devices = devices_result if isinstance(devices_result, list) else []

            if isinstance(positions_result, Exception):
                raise UpdateFailed(f"Error fetching positions: {positions_result}") from positions_result
            positions = positions_result if isinstance(positions_result, list) else []

            if isinstance(geofences_result, Exception):
                geofences = []
            else:
                geofences = geofences_result if isinstance(geofences_result, list) else []

        except MooxAuthenticationException as ex:
            if await self._handle_server_failure(ex, is_auth_failure=True):
                raise ConfigEntryAuthFailed from ex
            if self.data:
                return self.data
            return {}
        except MooxSessionExpiredException as ex:
            if await self._handle_server_failure(ex, is_auth_failure=True):
                raise ConfigEntryAuthFailed from ex
            if self.data:
                return self.data
            return {}
        except MooxConnectionException as ex:
            if await self._handle_server_failure(ex, is_auth_failure=False):
                if not self.client.ever_authenticated:
                    raise ConfigEntryAuthFailed from ex
                raise UpdateFailed(
                    f"Server connection errors for over {AUTH_FAILURE_GRACE_PERIOD_HOURS} hours"
                ) from ex
            if self.data:
                return self.data
            return {}
        except MooxException as ex:
            if await self._handle_server_failure(ex, is_auth_failure=False):
                if not self.client.ever_authenticated:
                    raise ConfigEntryAuthFailed from ex
                raise UpdateFailed(
                    f"Server errors for over {AUTH_FAILURE_GRACE_PERIOD_HOURS} hours"
                ) from ex
            if self.data:
                return self.data
            return {}

        await self._clear_failure_tracking()

        if TYPE_CHECKING:
            assert isinstance(devices, list[DeviceModel])  # type: ignore[misc]
            assert isinstance(positions, list[PositionModel])  # type: ignore[misc]
            assert isinstance(geofences, list[GeofenceModel])  # type: ignore[misc]

        self._geofences = geofences

        for position in positions:
            device_id = position.get("deviceId")
            if device_id is None:
                continue
            if (device := get_device(device_id, devices)) is None:
                continue

            attr = self._get_custom_attributes_if_accurate(device, position)
            if attr is None:
                continue

            geofence_ids = get_geofence_ids(device, position)
            matched_geofence = get_first_geofence(geofences, geofence_ids)
            data[device_id] = {
                "device": device,
                "geofence": matched_geofence,
                "position": position,
                "attributes": attr,
            }

        for device in devices:
            device_id = device.get("id")
            if device_id is None:
                LOGGER.warning("Device missing id: %s", device.get("name", "unknown"))
                continue
            if device_id not in data:
                data[device_id] = {
                    "device": device,
                    "geofence": None,
                    "position": cast(PositionModel, {}),
                    "attributes": {},
                }

        return data

    async def import_events(self, _: datetime) -> None:
        """Import events from MOOX Track."""
        if not self.events or not self.data:
            return

        end_time = dt_util.utcnow().replace(tzinfo=None)
        start_time = self._last_event_import

        try:
            events = await self.client.get_reports_events(
                devices=list(self.data),
                start_time=start_time,
                end_time=end_time,
                event_types=self.events,
            )
        except (MooxException, AttributeError):
            return

        if not events:
            return

        self._last_event_import = end_time
        for event in events:
            if not isinstance(event, dict):
                continue
            event_type = event.get("type")
            device_id = event.get("deviceId")
            event_time = event.get("eventTime")
            event_attrs = event.get("attributes") or {}

            if not event_type or device_id is None or not isinstance(event_type, str):
                continue
            if device_id not in self.data:
                continue

            device = self.data[device_id].get("device")
            event_name = EVENTS.get(event_type, to_snake_case(event_type))
            payload = {
                "device_moox_id": device_id,
                "device_name": device.get("name") if device else None,
                "event": event_name,
                "type": event_type,
                "serverTime": event_time,
                "attributes": event_attrs,
            }
            self.hass.bus.async_fire(f"{DOMAIN}_event", payload)

    def _get_custom_attributes_if_accurate(
        self,
        device: DeviceModel,
        position: PositionModel,
    ) -> dict[str, Any] | None:
        """Return custom attributes if position passes accuracy filter."""
        attr = {}
        skip_accuracy_filter = False

        for custom_attr in self.custom_attributes:
            if custom_attr in self.skip_accuracy_filter_for:
                skip_accuracy_filter = True
            device_attrs = device.get("attributes") or {}
            position_attrs = position.get("attributes") or {}
            attr[custom_attr] = device_attrs.get(
                custom_attr,
                position_attrs.get(custom_attr, None),
            )

        accuracy = position.get("accuracy") or 0.0
        if (
            not skip_accuracy_filter
            and self.max_accuracy > 0
            and accuracy > self.max_accuracy
        ):
            return None
        return attr
