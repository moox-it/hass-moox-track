"""Diagnostics platform for MOOX Track.

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

from homeassistant.components.diagnostics import REDACTED, async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .coordinator import MooxServerCoordinator
from .helpers import get_coordinator_from_entry

KEYS_TO_REDACT = {
    "area",
    CONF_ADDRESS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
}


def _entity_state(
    hass: HomeAssistant,
    entity: er.RegistryEntry,
    coordinator: MooxServerCoordinator,
) -> dict[str, Any] | None:
    """Get entity state with address redaction."""
    coordinator_data = coordinator.data or {}
    states_to_redact = {
        position_address
        for device_data in coordinator_data.values()
        if (position := device_data.get("position")) and isinstance(position, dict)
        if (position_address := position.get("address"))
    }
    return (
        {
            "state": state.state if state.state not in states_to_redact else REDACTED,
            "attributes": state.attributes,
        }
        if (state := hass.states.get(entity.entity_id))
        else None
    )


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = get_coordinator_from_entry(config_entry)
    entity_registry = er.async_get(hass)

    entities = er.async_entries_for_config_entry(
        entity_registry,
        config_entry_id=config_entry.entry_id,
    )

    return async_redact_data(
        {
            "config_entry_options": dict(config_entry.options),
            "coordinator_data": coordinator.data,
            "entities": [
                {
                    "entity_id": entity.entity_id,
                    "disabled": entity.disabled,
                    "unit_of_measurement": entity.unit_of_measurement,
                    "state": _entity_state(hass, entity, coordinator),
                }
                for entity in entities
            ],
        },
        KEYS_TO_REDACT,
    )


async def async_get_device_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device: dr.DeviceEntry,
) -> dict[str, Any]:
    """Return device diagnostics."""
    coordinator = get_coordinator_from_entry(entry)
    entity_registry = er.async_get(hass)

    entities = er.async_entries_for_device(
        entity_registry,
        device_id=device.id,
        include_disabled_entities=True,
    )

    return async_redact_data(
        {
            "config_entry_options": dict(entry.options),
            "coordinator_data": coordinator.data,
            "entities": [
                {
                    "entity_id": entity.entity_id,
                    "disabled": entity.disabled,
                    "unit_of_measurement": entity.unit_of_measurement,
                    "state": _entity_state(hass, entity, coordinator),
                }
                for entity in entities
            ],
        },
        KEYS_TO_REDACT,
    )
