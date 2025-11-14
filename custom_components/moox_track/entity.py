"""Base entity for MOOX Track.

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

from typing import Any, cast

from .moox_client import DeviceModel, GeofenceModel, PositionModel

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MooxServerCoordinator


class MooxServerEntity(CoordinatorEntity[MooxServerCoordinator]):
    """Base entity for MOOX Track."""

    def __init__(
        self,
        coordinator: MooxServerCoordinator,
        device: DeviceModel,
    ) -> None:
        """Initialize the MOOX Track entity."""
        super().__init__(coordinator)
        self.device_id = device["id"]
        device_model = device.get("model", "")
        if device_model == "FMB920":
            device_model = "FMx920"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self.device_id))},
            model=device_model,
            name=device["name"],
            manufacturer="MOOX",
        )
        self._attr_unique_id = str(self.device_id)
        self._cached_device: DeviceModel = device
        self._cached_geofence: GeofenceModel | None = None
        self._cached_position: PositionModel = cast(PositionModel, {})
        self._cached_attributes: dict[str, Any] = {}
        self._refresh_cached_data()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.data and self.device_id in self.coordinator.data)

    @property
    def moox_device(self) -> DeviceModel:
        """Return the device."""
        if self.coordinator.data and self.device_id in self.coordinator.data:
            self._cached_device = self.coordinator.data[self.device_id]["device"]
        return self._cached_device

    @property
    def moox_geofence(self) -> GeofenceModel | None:
        """Return the geofence."""
        if self.coordinator.data and self.device_id in self.coordinator.data:
            self._cached_geofence = self.coordinator.data[self.device_id]["geofence"]
        return self._cached_geofence

    @property
    def moox_position(self) -> PositionModel:
        """Return the position."""
        if self.coordinator.data and self.device_id in self.coordinator.data:
            self._cached_position = self.coordinator.data[self.device_id]["position"]
        return self._cached_position

    @property
    def moox_attributes(self) -> dict[str, Any]:
        """Return the attributes."""
        if self.coordinator.data and self.device_id in self.coordinator.data:
            self._cached_attributes = (
                self.coordinator.data[self.device_id].get("attributes") or {}
            )
        return self._cached_attributes

    def _refresh_cached_data(self) -> None:
        """Refresh cached coordinator data for this entity."""
        if not self.coordinator.data or self.device_id not in self.coordinator.data:
            return
        device_data = self.coordinator.data[self.device_id]
        self._cached_device = device_data["device"]
        self._cached_geofence = device_data["geofence"]
        self._cached_position = device_data["position"]
        self._cached_attributes = device_data.get("attributes") or {}

    def _handle_coordinator_update(self) -> None:
        """Update caches when coordinator data changes."""
        self._refresh_cached_data()
        super()._handle_coordinator_update()

    async def async_added_to_hass(self) -> None:
        """Entity added to hass."""
        self._refresh_cached_data()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self.device_id}",
                self.async_write_ha_state,
            )
        )
        await super().async_added_to_hass()
