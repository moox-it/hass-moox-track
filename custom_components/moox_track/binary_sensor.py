"""Binary sensor platform for MOOX Track.

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

from dataclasses import dataclass
from typing import Any, Callable, Generic, Literal, TypeVar

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MooxServerCoordinator
from .entity import MooxServerEntity
from .helpers import get_coordinator_from_entry
from .moox_client import DeviceModel, PositionModel

_T = TypeVar("_T")


@dataclass(frozen=True, kw_only=True)
class MooxBinarySensorEntityDescription(BinarySensorEntityDescription, Generic[_T]):
    """Describe a MOOX binary sensor entity."""

    data_key: Literal["position", "device", "geofence", "attributes"]
    entity_registry_enabled_default: bool = False
    entity_category: EntityCategory | None = EntityCategory.DIAGNOSTIC
    value_fn: Callable[[_T], bool | None]


def _to_bool(value: Any) -> bool | None:
    """Convert a value to bool."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ("true", "1", "on", "yes")
    return None


BINARY_SENSOR_DESCRIPTIONS: tuple[MooxBinarySensorEntityDescription[Any], ...] = (
    MooxBinarySensorEntityDescription[PositionModel](
        key="attributes.motion",
        data_key="position",
        translation_key="motion",
        device_class=BinarySensorDeviceClass.MOTION,
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: _to_bool((x.get("attributes") or {}).get("motion")),
    ),
    MooxBinarySensorEntityDescription[PositionModel](
        key="attributes.ignition",
        data_key="position",
        translation_key="ignition",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: _to_bool((x.get("attributes") or {}).get("ignition")),
    ),
    MooxBinarySensorEntityDescription[PositionModel](
        key="attributes.out1",
        data_key="position",
        translation_key="out1",
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: _to_bool((x.get("attributes") or {}).get("out1")),
    ),
    MooxBinarySensorEntityDescription[DeviceModel](
        key="status",
        data_key="device",
        translation_key="status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda x: None if (s := x["status"]) == "unknown" else s == "online",
    ),
    MooxBinarySensorEntityDescription[PositionModel](
        key="attributes.di1",
        data_key="position",
        translation_key="di1",
        entity_category=None,
        entity_registry_enabled_default=False,
        value_fn=lambda x: _to_bool((x.get("attributes") or {}).get("di1")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator = get_coordinator_from_entry(entry)
    processed_device_ids: set[int] = set()

    def _async_add_new_entities() -> None:
        if not coordinator.data:
            return
        new_entities: list[MooxBinarySensor[Any]] = []
        for device_id, device_data in coordinator.data.items():
            if device_id in processed_device_ids:
                continue
            device = device_data["device"]
            for description in BINARY_SENSOR_DESCRIPTIONS:
                new_entities.append(
                    MooxBinarySensor(
                        coordinator=coordinator,
                        device=device,
                        description=description,
                    )
                )
            processed_device_ids.add(device_id)
        if new_entities:
            async_add_entities(new_entities)

    _async_add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_entities))


class MooxBinarySensor(MooxServerEntity, BinarySensorEntity, Generic[_T]):
    """Represent a MOOX binary sensor."""

    _attr_has_entity_name = True
    entity_description: MooxBinarySensorEntityDescription[_T]

    def __init__(
        self,
        coordinator: MooxServerCoordinator,
        device: DeviceModel,
        description: MooxBinarySensorEntityDescription[_T],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device)
        self.entity_description = description
        safe_key = description.key.replace(".", "_")
        self._attr_unique_id = f"{self.device_id}_{description.data_key}_{safe_key}"

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        return self.entity_description.value_fn(
            getattr(self, f"moox_{self.entity_description.data_key}")
        )
