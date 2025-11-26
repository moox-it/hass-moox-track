"""Sensor platform for MOOX Track.

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

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import MooxServerCoordinator
from .entity import MooxServerEntity
from .helpers import (
    convert_event_code_to_text,
    detect_alarms,
    detect_configuration_received,
    detect_warnings,
    get_coordinator_from_entry,
    process_obdii_data,
)
from .moox_client import DeviceModel, GeofenceModel, PositionModel

_T = TypeVar("_T")


@dataclass(frozen=True, kw_only=True)
class MooxSensorEntityDescription(SensorEntityDescription, Generic[_T]):
    """Describe a MOOX sensor entity."""

    data_key: Literal["position", "device", "geofence", "attributes"]
    entity_registry_enabled_default: bool = False
    entity_category: EntityCategory | None = EntityCategory.DIAGNOSTIC
    value_fn: Callable[[_T], StateType]


def _ensure_float(value: Any) -> float | None:
    """Convert a value to float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_nested(data: dict[str, Any], *path: str) -> Any:
    """Return nested dictionary value safely."""
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _knots_to_kmh(value: float | None) -> float | None:
    """Convert knots to kilometers per hour."""
    if value is None:
        return None
    return value * 1.852


SENSOR_DESCRIPTIONS: tuple[MooxSensorEntityDescription[Any], ...] = (
    MooxSensorEntityDescription[GeofenceModel | None](
        key="name",
        data_key="geofence",
        translation_key="geofence",
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: x.get("name")
        if x and isinstance(x, dict) and x.get("name")
        else None,
    ),
    MooxSensorEntityDescription[PositionModel](
        key="latitude",
        data_key="position",
        translation_key="latitude",
        entity_category=None,
        entity_registry_enabled_default=True,
        suggested_display_precision=6,
        native_unit_of_measurement=DEGREE,
        value_fn=lambda x: _ensure_float(x.get("latitude")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="longitude",
        data_key="position",
        translation_key="longitude",
        entity_category=None,
        entity_registry_enabled_default=True,
        suggested_display_precision=6,
        native_unit_of_measurement=DEGREE,
        value_fn=lambda x: _ensure_float(x.get("longitude")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="altitude",
        data_key="position",
        translation_key="altitude",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_display_precision=1,
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: _ensure_float(x.get("altitude")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="course",
        data_key="position",
        translation_key="course",
        entity_category=None,
        entity_registry_enabled_default=True,
        native_unit_of_measurement=DEGREE,
        suggested_display_precision=0,
        value_fn=lambda x: _ensure_float(x.get("course")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="accuracy",
        data_key="position",
        translation_key="accuracy",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=None,
        entity_registry_enabled_default=True,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_display_precision=1,
        value_fn=lambda x: _ensure_float(x.get("accuracy")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="speed_kmh",
        data_key="position",
        translation_key="speed_kmh",
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=0,
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: _knots_to_kmh(_ensure_float(x.get("speed"))),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.sat",
        data_key="position",
        translation_key="sat",
        entity_category=None,
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: _ensure_float((x.get("attributes") or {}).get("sat")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.rssi",
        data_key="position",
        translation_key="rssi",
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: _ensure_float((x.get("attributes") or {}).get("rssi")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.power",
        data_key="position",
        translation_key="power",
        entity_category=None,
        entity_registry_enabled_default=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        value_fn=lambda x: _ensure_float((x.get("attributes") or {}).get("power")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.odometer",
        data_key="position",
        translation_key="odometer",
        entity_category=None,
        entity_registry_enabled_default=True,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_display_precision=1,
        value_fn=lambda x: _ensure_float((x.get("attributes") or {}).get("odometer")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.event",
        data_key="position",
        translation_key="event",
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: convert_event_code_to_text(
            (x.get("attributes") or {}).get("event"),
            x.get("attributes") or {},
        ),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="alarms",
        data_key="position",
        translation_key="alarms",
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: ", ".join(alarms)
        if (alarms := detect_alarms(x.get("attributes") or {}, x))
        else None,
    ),
    MooxSensorEntityDescription[PositionModel](
        key="warnings",
        data_key="position",
        translation_key="warnings",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda x: ", ".join(warnings)
        if (warnings := detect_warnings(x.get("attributes") or {}, x))
        else None,
    ),
    MooxSensorEntityDescription[PositionModel](
        key="speed",
        data_key="position",
        translation_key="speed",
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
        suggested_display_precision=0,
        entity_category=None,
        entity_registry_enabled_default=False,
        value_fn=lambda x: _ensure_float(x.get("speed")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.io36",
        data_key="position",
        translation_key="rpm",
        entity_category=None,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: process_obdii_data(x.get("attributes") or {}).get("rpm"),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.io48",
        data_key="position",
        translation_key="fuel",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda x: process_obdii_data(x.get("attributes") or {}).get("fuel"),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.io281",
        data_key="position",
        translation_key="dtc_codes",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: process_obdii_data(x.get("attributes") or {}).get(
            "dtc_codes"
        ),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.io30",
        data_key="position",
        translation_key="dtc_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: process_obdii_data(x.get("attributes") or {}).get(
            "dtc_count"
        ),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="configuration_received",
        data_key="position",
        translation_key="configuration_received",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: "Yes"
        if detect_configuration_received(x.get("attributes") or {}).get("received")
        else "No",
    ),
    MooxSensorEntityDescription[PositionModel](
        key="attributes.batteryLevel",
        data_key="position",
        translation_key="battery_level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: (x.get("attributes") or {}).get("batteryLevel"),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="event_raw",
        data_key="position",
        translation_key="event_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: (x.get("attributes") or {}).get("event"),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="serverTime",
        data_key="position",
        translation_key="server_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: x.get("serverTime"),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="deviceTime",
        data_key="position",
        translation_key="device_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: x.get("deviceTime"),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="fixTime",
        data_key="position",
        translation_key="fix_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: x.get("fixTime"),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.latitude",
        data_key="position",
        translation_key="last_gps_fix_latitude",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=DEGREE,
        suggested_display_precision=6,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "latitude")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.longitude",
        data_key="position",
        translation_key="last_gps_fix_longitude",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=DEGREE,
        suggested_display_precision=6,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "longitude")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.altitude",
        data_key="position",
        translation_key="last_gps_fix_altitude",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_display_precision=1,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "altitude")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.speed",
        data_key="position",
        translation_key="last_gps_fix_speed",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
        suggested_display_precision=0,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "speed")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.speed_kmh",
        data_key="position",
        translation_key="last_gps_fix_speed_kmh",
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=0,
        value_fn=lambda x: _knots_to_kmh(
            _ensure_float(_get_nested(x, "lastGpsFix", "speed"))
        ),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.course",
        data_key="position",
        translation_key="last_gps_fix_course",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=DEGREE,
        suggested_display_precision=0,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "course")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.accuracy",
        data_key="position",
        translation_key="last_gps_fix_accuracy",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_display_precision=1,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "accuracy")),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.serverTime",
        data_key="position",
        translation_key="last_gps_fix_server_time",
        entity_category=None,
        entity_registry_enabled_default=False,
        value_fn=lambda x: _get_nested(x, "lastGpsFix", "serverTime"),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.deviceTime",
        data_key="position",
        translation_key="last_gps_fix_device_time",
        entity_category=None,
        entity_registry_enabled_default=False,
        value_fn=lambda x: _get_nested(x, "lastGpsFix", "deviceTime"),
    ),
    MooxSensorEntityDescription[PositionModel](
        key="lastGpsFix.fixTime",
        data_key="position",
        translation_key="last_gps_fix_fix_time",
        entity_category=None,
        entity_registry_enabled_default=False,
        value_fn=lambda x: _get_nested(x, "lastGpsFix", "fixTime"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator = get_coordinator_from_entry(entry)
    processed_device_ids: set[int] = set()

    def _async_add_new_entities() -> None:
        if not coordinator.data:
            return
        new_entities: list[MooxSensor[Any]] = []
        for device_id, device_data in coordinator.data.items():
            if device_id in processed_device_ids:
                continue
            device = device_data["device"]
            for description in SENSOR_DESCRIPTIONS:
                new_entities.append(
                    MooxSensor(
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


class MooxSensor(MooxServerEntity, SensorEntity, Generic[_T]):
    """Represent a MOOX sensor."""

    _attr_has_entity_name = True
    entity_description: MooxSensorEntityDescription[_T]

    def __init__(
        self,
        coordinator: MooxServerCoordinator,
        device: DeviceModel,
        description: MooxSensorEntityDescription[_T],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device)
        self.entity_description = description
        safe_key = description.key.replace(".", "_")
        self._attr_unique_id = f"{self.device_id}_{description.data_key}_{safe_key}"

    @property
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self.entity_description.value_fn(
            getattr(self, f"moox_{self.entity_description.data_key}")
        )
