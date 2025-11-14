"""Support for MOOX Track device tracking.

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

from typing import Any

from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ATTR_CATEGORY, ATTR_MOOX_ID, ATTR_TRACKER, DOMAIN
from .coordinator import MooxServerCoordinator
from .entity import MooxServerEntity
from .helpers import get_coordinator_from_entry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up device tracker entities."""
    coordinator = get_coordinator_from_entry(entry)
    processed_device_ids: set[int] = set()

    def _async_add_new_entities() -> None:
        if not coordinator.data:
            return
        new_entities: list[MooxServerDeviceTracker] = []
        for device_id, device_data in coordinator.data.items():
            if device_id in processed_device_ids:
                continue
            device = device_data["device"]
            entity = MooxServerDeviceTracker(coordinator, device)
            new_entities.append(entity)
            processed_device_ids.add(device_id)
        if new_entities:
            async_add_entities(new_entities)

    _async_add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_entities))


class MooxServerDeviceTracker(MooxServerEntity, TrackerEntity):
    """Represent a tracked device."""

    _attr_has_entity_name = True
    _attr_name = "[01·TRK]"
    _attr_source_type = SourceType.GPS

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific attributes."""
        device = self.moox_device or {}
        return {
            **self.moox_attributes,
            ATTR_CATEGORY: device.get("category"),
            ATTR_MOOX_ID: device.get("id"),
            ATTR_TRACKER: DOMAIN,
        }

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        position = self.moox_position or {}
        return position.get("latitude")

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        position = self.moox_position or {}
        return position.get("longitude")

    @property
    def location_accuracy(self) -> float | None:
        """Return the gps accuracy of the device."""
        position = self.moox_position or {}
        return position.get("accuracy")
