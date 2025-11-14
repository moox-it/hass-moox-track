"""Support for MOOX Track sensors.

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

from dataclasses import dataclass
from typing import Any, Callable, Literal

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
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
)
from homeassistant.const import EntityCategory
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


@dataclass(frozen=True, kw_only=True)
class MooxServerSensorEntityDescription[_T](SensorEntityDescription):
    """Describe MOOX Server sensor entity."""

    data_key: Literal["position", "device", "geofence", "attributes"]
    entity_registry_enabled_default = False
    entity_category = EntityCategory.DIAGNOSTIC
    value_fn: Callable[[_T], StateType]


def _ensure_float(value: Any) -> float | None:
    """Try to convert a value to float."""
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




MOOX_SERVER_SENSOR_ENTITY_DESCRIPTIONS: tuple[
    MooxServerSensorEntityDescription[Any], ...
] = (
    # 2. [02·LOC] Geofence
    MooxServerSensorEntityDescription[GeofenceModel | None](
        key="name",
        data_key="geofence",
        translation_key="geofence",
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: x.get("name") if x and isinstance(x, dict) and x.get("name") else None,
    ),
    # 3. [03·GPS] Latitude
    MooxServerSensorEntityDescription[PositionModel](
        key="latitude",
        data_key="position",
        translation_key="latitude",
        entity_category=None,
        entity_registry_enabled_default=True,
        suggested_display_precision=6,
        native_unit_of_measurement=DEGREE,
        value_fn=lambda x: _ensure_float(x.get("latitude")),
    ),
    # 4. [03·GPS] Longitude
    MooxServerSensorEntityDescription[PositionModel](
        key="longitude",
        data_key="position",
        translation_key="longitude",
        entity_category=None,
        entity_registry_enabled_default=True,
        suggested_display_precision=6,
        native_unit_of_measurement=DEGREE,
        value_fn=lambda x: _ensure_float(x.get("longitude")),
    ),
    # 5. [03·GPS] Altitude
    MooxServerSensorEntityDescription[PositionModel](
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
    # 6. [04·FIX] Course
    MooxServerSensorEntityDescription[PositionModel](
        key="course",
        data_key="position",
        translation_key="course",
        entity_category=None,
        entity_registry_enabled_default=True,
        native_unit_of_measurement=DEGREE,
        suggested_display_precision=0,
        value_fn=lambda x: _ensure_float(x.get("course")),
    ),
    # 7. [04·FIX] Accuracy
    MooxServerSensorEntityDescription[PositionModel](
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
    # 8. [05·MOV] Speed (km/h)
    MooxServerSensorEntityDescription[PositionModel](
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
    # 13. [07·SYS] Satellites
    MooxServerSensorEntityDescription[PositionModel](
        key="attributes.sat",
        data_key="position",
        translation_key="sat",
        entity_category=None,
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: _ensure_float((x.get("attributes") or {}).get("sat")),
    ),
    # 14. [07·SYS] RSSI
    MooxServerSensorEntityDescription[PositionModel](
        key="attributes.rssi",
        data_key="position",
        translation_key="rssi",
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: _ensure_float((x.get("attributes") or {}).get("rssi")),
    ),
    # 15. [07·SYS] Power
    MooxServerSensorEntityDescription[PositionModel](
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
    # 16. [08·LOG] Odometer
    MooxServerSensorEntityDescription[PositionModel](
        key="attributes.odometer",
        data_key="position",
        translation_key="odometer",
        entity_category=None,
        entity_registry_enabled_default=True,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_display_precision=1,
        value_fn=lambda x: _ensure_float(
            (x.get("attributes") or {}).get("odometer")
        ),
    ),
    # 17. [08·LOG] Event
    MooxServerSensorEntityDescription[PositionModel](
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
    # 18. [09·ALM] Alarms
    MooxServerSensorEntityDescription[PositionModel](
        key="alarms",
        data_key="position",
        translation_key="alarms",
        entity_category=None,
        entity_registry_enabled_default=True,
        value_fn=lambda x: ", ".join(alarms)
        if (alarms := detect_alarms(x.get("attributes") or {}, x))
        else None,
    ),
    # 19. [10·WRN] Warnings
    MooxServerSensorEntityDescription[PositionModel](
        key="warnings",
        data_key="position",
        translation_key="warnings",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        value_fn=lambda x: ", ".join(warnings)
        if (warnings := detect_warnings(x.get("attributes") or {}, x))
        else None,
    ),
    # 21. [05·MOV] Speed (kn) - hidden
    MooxServerSensorEntityDescription[PositionModel](
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
    # 23. [11·OBD] RPM - diagnostic hidden
    MooxServerSensorEntityDescription[PositionModel](
        key="attributes.io36",
        data_key="position",
        translation_key="rpm",
        entity_category=None,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: process_obdii_data(x.get("attributes") or {}).get("rpm"),
    ),
    # 24. [11·OBD] Fuel
    MooxServerSensorEntityDescription[PositionModel](
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
    # 25. [11·OBD] Diagnostic Trouble Codes
    MooxServerSensorEntityDescription[PositionModel](
        key="attributes.io281",
        data_key="position",
        translation_key="dtc_codes",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: process_obdii_data(x.get("attributes") or {}).get(
            "dtc_codes"
        ),
    ),
    # 26. [11·OBD] Diagnostic Trouble Codes Count
    MooxServerSensorEntityDescription[PositionModel](
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
    # 27. [12·CFG] Configuration Received
    MooxServerSensorEntityDescription[PositionModel](
        key="configuration_received",
        data_key="position",
        translation_key="configuration_received",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: "Yes"
        if detect_configuration_received(x.get("attributes") or {}).get("received")
        else "No",
    ),
    # 28. [90·DIA] Battery Level
    MooxServerSensorEntityDescription[PositionModel](
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
    # 29. [90·DIA] Event Raw
    MooxServerSensorEntityDescription[PositionModel](
        key="event_raw",
        data_key="position",
        translation_key="event_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: (x.get("attributes") or {}).get("event"),
    ),
    # 30. [91·DIA] Server Time
    MooxServerSensorEntityDescription[PositionModel](
        key="serverTime",
        data_key="position",
        translation_key="server_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: x.get("serverTime"),
    ),
    # 31. [91·DIA] Device Time
    MooxServerSensorEntityDescription[PositionModel](
        key="deviceTime",
        data_key="position",
        translation_key="device_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: x.get("deviceTime"),
    ),
    # 32. [91·DIA] Fix Time
    MooxServerSensorEntityDescription[PositionModel](
        key="fixTime",
        data_key="position",
        translation_key="fix_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda x: x.get("fixTime"),
    ),
    # 33. [92·DIA] Last GPS Fix Latitude
    MooxServerSensorEntityDescription[PositionModel](
        key="lastGpsFix.latitude",
        data_key="position",
        translation_key="last_gps_fix_latitude",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=DEGREE,
        suggested_display_precision=6,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "latitude")),
    ),
    # 34. [92·DIA] Last GPS Fix Longitude
    MooxServerSensorEntityDescription[PositionModel](
        key="lastGpsFix.longitude",
        data_key="position",
        translation_key="last_gps_fix_longitude",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=DEGREE,
        suggested_display_precision=6,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "longitude")),
    ),
    # 35. [92·DIA] Last GPS Fix Altitude
    MooxServerSensorEntityDescription[PositionModel](
        key="lastGpsFix.altitude",
        data_key="position",
        translation_key="last_gps_fix_altitude",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_display_precision=1,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "altitude")),
    ),
    # 36. [93·DIA] Last GPS Fix Speed (kn)
    MooxServerSensorEntityDescription[PositionModel](
        key="lastGpsFix.speed",
        data_key="position",
        translation_key="last_gps_fix_speed",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
        suggested_display_precision=0,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "speed")),
    ),
    # 37. [93·DIA] Last GPS Fix Speed (km/h)
    MooxServerSensorEntityDescription[PositionModel](
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
    # 38. [93·DIA] Last GPS Fix Course
    MooxServerSensorEntityDescription[PositionModel](
        key="lastGpsFix.course",
        data_key="position",
        translation_key="last_gps_fix_course",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=DEGREE,
        suggested_display_precision=0,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "course")),
    ),
    # 39. [93·DIA] Last GPS Fix Accuracy
    MooxServerSensorEntityDescription[PositionModel](
        key="lastGpsFix.accuracy",
        data_key="position",
        translation_key="last_gps_fix_accuracy",
        entity_category=None,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_display_precision=1,
        value_fn=lambda x: _ensure_float(_get_nested(x, "lastGpsFix", "accuracy")),
    ),
    # 40. [94·DIA] Last GPS Fix Server Time
    MooxServerSensorEntityDescription[PositionModel](
        key="lastGpsFix.serverTime",
        data_key="position",
        translation_key="last_gps_fix_server_time",
        entity_category=None,
        entity_registry_enabled_default=False,
        value_fn=lambda x: _get_nested(x, "lastGpsFix", "serverTime"),
    ),
    # 41. [94·DIA] Last GPS Fix Device Time
    MooxServerSensorEntityDescription[PositionModel](
        key="lastGpsFix.deviceTime",
        data_key="position",
        translation_key="last_gps_fix_device_time",
        entity_category=None,
        entity_registry_enabled_default=False,
        value_fn=lambda x: _get_nested(x, "lastGpsFix", "deviceTime"),
    ),
    # 42. [94·DIA] Last GPS Fix Fix Time
    MooxServerSensorEntityDescription[PositionModel](
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
        new_entities: list[MooxServerSensor[Any]] = []
        for device_id, device_data in coordinator.data.items():
            if device_id in processed_device_ids:
                continue
            device = device_data["device"]
            for description in MOOX_SERVER_SENSOR_ENTITY_DESCRIPTIONS:
                entity = MooxServerSensor(
                    coordinator=coordinator,
                    device=device,
                    description=description,
                )
                new_entities.append(entity)
            processed_device_ids.add(device_id)
        if new_entities:
            async_add_entities(new_entities)

    _async_add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_entities))


class MooxServerSensor[_T](MooxServerEntity, SensorEntity):
    """Represent a tracked device."""

    _attr_has_entity_name = True
    entity_description: MooxServerSensorEntityDescription[_T]

    def __init__(
        self,
        coordinator: MooxServerCoordinator,
        device: DeviceModel,
        description: MooxServerSensorEntityDescription[_T],
    ) -> None:
        """Initialize the MOOX Server sensor."""
        super().__init__(coordinator, device)
        self.entity_description = description
        # Replace dots with underscores in key for unique_id safety
        safe_key = description.key.replace(".", "_")
        self._attr_unique_id = (
            f"{self.device_id}_{description.data_key}_{safe_key}"
        )

    @property
    def native_value(self) -> StateType:
        """Return the value of the sensor."""
        return self.entity_description.value_fn(
            getattr(self, f"moox_{self.entity_description.data_key}")
        )
