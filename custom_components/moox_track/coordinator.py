"""Data update coordinator for MOOX Track.

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

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, TypedDict, cast

from .moox_client import (
    MooxClient,
    DeviceModel,
    GeofenceModel,
    PositionModel,
    SubscriptionData,
    MooxAuthenticationException,
    MooxException,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.dispatcher import async_dispatcher_send
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


class MooxServerCoordinatorDataDevice(TypedDict):
    """MOOX Server coordinator data."""

    device: DeviceModel
    geofence: GeofenceModel | None
    position: PositionModel
    attributes: dict[str, Any]


type MooxServerCoordinatorData = dict[int, MooxServerCoordinatorDataDevice]


class MooxServerCoordinator(DataUpdateCoordinator[MooxServerCoordinatorData]):
    """Coordinator to manage fetching MOOX Track data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: MooxClient,
    ) -> None:
        """Initialize global MOOX Server data updater."""
        update_interval_seconds = config_entry.options.get(CONF_UPDATE_INTERVAL, 30)
        if update_interval_seconds < 30:
            update_interval_seconds = 30
            LOGGER.warning(
                "Update interval was set to less than 30 seconds, using minimum of 30 seconds"
            )
        update_interval = timedelta(seconds=update_interval_seconds) if update_interval_seconds > 0 else None
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
        self._should_log_subscription_error: bool = True

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
            
            if isinstance(devices_result, MooxAuthenticationException):
                raise ConfigEntryAuthFailed from devices_result
            if isinstance(devices_result, Exception):
                raise UpdateFailed(
                    f"Error fetching devices: {devices_result}"
                ) from devices_result
            devices = devices_result
            if not isinstance(devices, list):
                LOGGER.error("Invalid devices response: expected list, got %s", type(devices).__name__)
                devices = []
            
            if isinstance(positions_result, MooxAuthenticationException):
                raise ConfigEntryAuthFailed from positions_result
            if isinstance(positions_result, Exception):
                raise UpdateFailed(
                    f"Error fetching positions: {positions_result}"
                ) from positions_result
            positions = positions_result
            if not isinstance(positions, list):
                LOGGER.error("Invalid positions response: expected list, got %s", type(positions).__name__)
                positions = []
            
            if isinstance(geofences_result, MooxAuthenticationException):
                raise ConfigEntryAuthFailed from geofences_result
            if isinstance(geofences_result, Exception):
                LOGGER.warning("Error fetching geofences: %s", geofences_result)
                geofences = []
            else:
                geofences = geofences_result
                if not isinstance(geofences, list):
                    LOGGER.warning("Invalid geofences response: expected list, got %s", type(geofences).__name__)
                    geofences = []
                
        except MooxAuthenticationException:
            raise ConfigEntryAuthFailed from None
        except MooxException as ex:
            raise UpdateFailed(f"Error while updating device data: {ex}") from ex

        if TYPE_CHECKING:
            assert isinstance(devices, list[DeviceModel])  # type: ignore[misc]
            assert isinstance(positions, list[PositionModel])  # type: ignore[misc]
            assert isinstance(geofences, list[GeofenceModel])  # type: ignore[misc]

        self._geofences = geofences

        # First, process positions and add devices with valid positions
        for position in positions:
            device_id = position["deviceId"]
            if (device := get_device(device_id, devices)) is None:
                continue

            if (
                attr
                := self._return_custom_attributes_if_not_filtered_by_accuracy_configuration(
                    device, position
                )
            ) is None:
                continue

            geofence_ids = get_geofence_ids(device, position)
            matched_geofence = get_first_geofence(geofences, geofence_ids)
            data[device_id] = {
                "device": device,
                "geofence": matched_geofence,
                "position": position,
                "attributes": attr,
            }

        # Then, add devices without positions (or with filtered positions)
        devices_added_count = 0
        for device in devices:
            device_id = device.get("id")
            if device_id is None:
                LOGGER.warning(
                    "Device missing id field, skipping device: %s",
                    device.get("name", "unknown"),
                )
                continue
            if device_id not in data:
                # Device has no valid position, add it with empty position
                data[device_id] = {
                    "device": device,
                    "geofence": None,
                    "position": cast(PositionModel, {}),
                    "attributes": {},
                }
                devices_added_count += 1

        return data

    async def handle_subscription_data(self, data: SubscriptionData) -> None:
        """Handle subscription data."""
        self._should_log_subscription_error = True
        update_devices = set()
        for device in data.get("devices") or []:
            device_id = device.get("id")
            if device_id is None:
                continue
            if device_id not in self.data:
                continue

            if (
                attr
                := self._return_custom_attributes_if_not_filtered_by_accuracy_configuration(
                    device, self.data[device_id]["position"]
                )
            ) is None:
                continue

            self.data[device_id]["device"] = device
            self.data[device_id]["attributes"] = attr
            update_devices.add(device_id)

        for position in data.get("positions") or []:
            if (device_id := position["deviceId"]) not in self.data:
                continue

            if (
                attr
                := self._return_custom_attributes_if_not_filtered_by_accuracy_configuration(
                    self.data[device_id]["device"], position
                )
            ) is None:
                continue

            self.data[device_id]["position"] = position
            self.data[device_id]["attributes"] = attr
            self.data[device_id]["geofence"] = get_first_geofence(
                self._geofences,
                get_geofence_ids(self.data[device_id]["device"], position),
            )
            update_devices.add(device_id)

        for device_id in update_devices:
            async_dispatcher_send(self.hass, f"{DOMAIN}_{device_id}")

    async def import_events(self, _: datetime) -> None:
        """Import events from MOOX Track."""
        if not self.events:
            return
            
        end_time = dt_util.utcnow().replace(tzinfo=None)
        start_time = None

        if self._last_event_import is not None:
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
            event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", None)
            device_id = event.get("deviceId") if isinstance(event, dict) else getattr(event, "deviceId", None)
            event_time = event.get("eventTime") if isinstance(event, dict) else getattr(event, "eventTime", None)
            event_attrs = event.get("attributes") if isinstance(event, dict) else getattr(event, "attributes", {})
            
            if not event_type or not device_id:
                continue
                
            if device_id not in self.data:
                continue
                
            device = self.data[device_id]["device"]
            event_name = EVENTS.get(event_type, to_snake_case(event_type))
            payload = {
                "device_moox_id": device_id,
                "device_name": device["name"] if device else None,
                "event": event_name,
                "type": event_type,
                "serverTime": event_time,
                "attributes": event_attrs,
            }
            self.hass.bus.async_fire(f"{DOMAIN}_event", payload)

    async def subscribe(self) -> None:
        """Subscribe to events via WebSocket.
        
        Note: This method is not called in the current implementation.
        The integration uses polling instead for reliability.
        """
        if not hasattr(self.client, 'subscribe'):
            return
        
        retry_count = 0
        max_backoff = 60
        
        while True:
            try:
                await self.client.subscribe(self.handle_subscription_data)
                retry_count = 0
                self._should_log_subscription_error = True
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                raise
            except MooxAuthenticationException:
                raise ConfigEntryAuthFailed from None
            except MooxException as ex:
                if self._should_log_subscription_error:
                    self._should_log_subscription_error = False
                    self.logger.error(
                        "Error while subscribing to MOOX Track: %s. Will retry with exponential backoff.",
                        ex
                    )
                backoff_time = min(2 ** retry_count, max_backoff)
                retry_count += 1
                await asyncio.sleep(backoff_time)
            except AttributeError:
                return

    def _return_custom_attributes_if_not_filtered_by_accuracy_configuration(
        self,
        device: DeviceModel,
        position: PositionModel,
    ) -> dict[str, Any] | None:
        """Return a dictionary of custom attributes if not filtered by accuracy configuration."""
        attr = {}
        skip_accuracy_filter = False

        for custom_attr in self.custom_attributes:
            if custom_attr in self.skip_accuracy_filter_for:
                skip_accuracy_filter = True
            attr[custom_attr] = device.get("attributes", {}).get(
                custom_attr,
                position.get("attributes", {}).get(custom_attr, None),
            )

        accuracy = position.get("accuracy") or 0.0
        if (
            not skip_accuracy_filter
            and self.max_accuracy > 0
            and accuracy > self.max_accuracy
        ):
            return None
        return attr
