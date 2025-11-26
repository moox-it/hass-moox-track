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
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, TypedDict, cast

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
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
            LOGGER.warning(
                "Update interval below minimum, using 30 seconds"
            )
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
            session_expired = False
            connection_error = False

            if isinstance(devices_result, MooxAuthenticationException):
                raise ConfigEntryAuthFailed from devices_result
            if isinstance(devices_result, MooxSessionExpiredException):
                session_expired = True
                devices = []
            elif isinstance(devices_result, MooxConnectionException):
                connection_error = True
                devices = []
            elif isinstance(devices_result, Exception):
                raise UpdateFailed(
                    f"Error fetching devices: {devices_result}"
                ) from devices_result
            else:
                devices = devices_result if isinstance(devices_result, list) else []

            if isinstance(positions_result, MooxAuthenticationException):
                raise ConfigEntryAuthFailed from positions_result
            if isinstance(positions_result, MooxSessionExpiredException):
                session_expired = True
                positions = []
            elif isinstance(positions_result, MooxConnectionException):
                connection_error = True
                positions = []
            elif isinstance(positions_result, Exception):
                raise UpdateFailed(
                    f"Error fetching positions: {positions_result}"
                ) from positions_result
            else:
                positions = (
                    positions_result if isinstance(positions_result, list) else []
                )

            if isinstance(geofences_result, MooxAuthenticationException):
                raise ConfigEntryAuthFailed from geofences_result
            if isinstance(geofences_result, MooxSessionExpiredException):
                session_expired = True
                geofences = []
            elif isinstance(geofences_result, MooxConnectionException):
                connection_error = True
                geofences = []
            elif isinstance(geofences_result, Exception):
                LOGGER.debug("Error fetching geofences: %s", geofences_result)
                geofences = []
            else:
                geofences = (
                    geofences_result if isinstance(geofences_result, list) else []
                )

        except MooxSessionExpiredException:
            if self.data:
                return self.data
            return {}
        except MooxConnectionException:
            if self.data:
                return self.data
            return {}
        except MooxAuthenticationException:
            raise ConfigEntryAuthFailed from None
        except MooxException as ex:
            raise UpdateFailed(f"Error updating data: {ex}") from ex

        if session_expired or connection_error:
            if self.data:
                return self.data
            return {}

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
                LOGGER.warning(
                    "Device missing id field: %s",
                    device.get("name", "unknown"),
                )
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
