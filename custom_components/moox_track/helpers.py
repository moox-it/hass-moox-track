"""Helper functions for MOOX Track.

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

from typing import TYPE_CHECKING, Any, Iterable, cast

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import MooxServerCoordinator

from .moox_client import DeviceModel, GeofenceModel, PositionModel


def get_device(device_id: int, devices: list[DeviceModel]) -> DeviceModel | None:
    """Return the device with the given ID."""
    return next(
        (dev for dev in devices if dev.get("id") == device_id),
        None,
    )


def _normalize_id_list(raw_ids: Iterable[Any] | None) -> list[int]:
    """Normalize an iterable of raw IDs to a list of int."""
    if raw_ids is None:
        return []
    result: list[int] = []
    for raw in raw_ids:
        if raw is None:
            continue
        try:
            result.append(int(raw))
        except (ValueError, TypeError):
            continue
    return result


def get_first_geofence(
    geofences: list[GeofenceModel],
    target: list[int],
) -> GeofenceModel | None:
    """Return the first matching geofence."""
    if not target or not geofences:
        return None
    normalized_target = set(_normalize_id_list(target))
    if not normalized_target:
        return None
    for geofence in geofences:
        geofence_id = geofence.get("id")
        if geofence_id is None:
            continue
        try:
            if int(geofence_id) in normalized_target:
                return geofence
        except (ValueError, TypeError):
            continue
    return None


def get_geofence_ids(
    device: DeviceModel,
    position: PositionModel,
) -> list[int]:
    """Return geofence IDs from position or device."""
    geofence_ids = position.get("geofenceIds")
    if isinstance(geofence_ids, list):
        return _normalize_id_list(geofence_ids)

    geofence_ids = device.get("geofenceIds")
    if isinstance(geofence_ids, list):
        return _normalize_id_list(geofence_ids)

    return []


def get_coordinator_from_entry(entry: ConfigEntry) -> MooxServerCoordinator:
    """Get coordinator from config entry."""
    from .coordinator import MooxServerCoordinator

    coordinator = cast(MooxServerCoordinator, entry.runtime_data)
    if coordinator is None:
        raise RuntimeError("MOOX Track coordinator is not available")
    return coordinator


def convert_event_code_to_text(
    event_code: int | None,
    attributes: dict[str, Any],
) -> str | None:
    """Convert numeric event code to readable text."""
    if event_code is None or event_code == 0 or event_code == "":
        return None
    event_map = {
        239: "Ignition Event",
        240: "Motion Event",
        246: "Towing Event",
        249: "Jamming Event",
        252: "Battery Event",
    }
    return event_map.get(event_code, f"Unknown Event ({event_code})")


ALARM_MAP = {
    "general": "General Alarm",
    "sos": "SOS",
    "vibration": "Vibration",
    "movement": "Movement",
    "lowspeed": "Low Speed",
    "overspeed": "Overspeed",
    "fallDown": "Possible Fall Detected",
    "lowPower": "Battery Voltage Below Limit",
    "lowBattery": "GPS Battery Is Low",
    "fault": "Vehicle Failure Code Detected",
    "powerOff": "Ignition Off",
    "powerOn": "Ignition On",
    "door": "Door",
    "lock": "Lock",
    "unlock": "Unlock",
    "geofence": "Area",
    "geofenceEnter": "Enter Area",
    "geofenceExit": "Exit Area",
    "gpsAntennaCut": "GPS Antenna Removed",
    "accident": "Possible Accident Detected",
    "tow": "Possible Vehicle Towing Detected",
    "idle": "Excessive Idling",
    "highRpm": "High RPM",
    "hardAcceleration": "Harsh Acceleration Detected",
    "hardBraking": "Harsh Braking Detected",
    "hardCornering": "Harsh Steering Detected",
    "laneChange": "Lane Change Detected",
    "fatigueDriving": "Tired Driver",
    "powerCut": "GPS Disconnected From Battery",
    "powerRestored": "Alarm Cleared, GPS Connected To Battery",
    "jamming": "Possible Jamming Attempt Detected",
    "temperature": "Temperature",
    "parking": "Parking",
    "shock": "Impact",
    "bonnet": "Bonnet",
    "footBrake": "Foot Brake",
    "fuelLeak": "Fuel Leak",
    "tampering": "Tampering",
    "removing": "Removing",
}


def detect_alarms(
    attributes: dict[str, Any],
    position: PositionModel,
) -> list[str]:
    """Detect alarms from attributes."""
    alarm_value = attributes.get("alarm")
    if not alarm_value:
        return []

    alarm_str = str(alarm_value).lower()
    alarm_description = ALARM_MAP.get(alarm_str)

    if alarm_description:
        return [alarm_description]

    return [str(alarm_value).title()]


def detect_warnings(
    attributes: dict[str, Any],
    position: PositionModel,
) -> list[str]:
    """Detect warning conditions from attributes."""
    warnings: list[str] = []
    sleep_mode = attributes.get("io200")
    is_sleep_mode = sleep_mode is not None and sleep_mode != 0

    result = attributes.get("result")
    if result is not None and result != "" and not is_sleep_mode:
        warnings.append("Configuration Received")
        return warnings

    sat = attributes.get("sat")
    rssi = attributes.get("rssi")

    rssi_numeric = None
    if rssi is not None:
        try:
            rssi_numeric = float(rssi)
        except (ValueError, TypeError):
            pass

    if (
        (sat is None or sat == 0)
        and rssi_numeric is not None
        and rssi_numeric > 0
        and not is_sleep_mode
    ):
        warnings.append("Approximate Position")
        return warnings

    if is_sleep_mode:
        warnings.append("Sleep Mode Active")

    return warnings


def process_obdii_data(attributes: dict[str, Any]) -> dict[str, Any]:
    """Process OBD-II diagnostic data."""
    obdii: dict[str, Any] = {
        "rpm": None,
        "fuel": None,
        "dtc_codes": None,
        "dtc_count": 0,
        "has_errors": False,
    }

    io36 = attributes.get("io36")
    if io36 is not None:
        obdii["rpm"] = int(io36) if isinstance(io36, (int, float)) else None

    io48 = attributes.get("io48")
    if io48 is not None:
        obdii["fuel"] = int(io48) if isinstance(io48, (int, float)) else None

    io281 = attributes.get("io281")
    if io281 is not None and io281 != "":
        obdii["dtc_codes"] = str(io281)

    io30 = attributes.get("io30")
    if io30 is not None:
        obdii["dtc_count"] = int(io30) if isinstance(io30, (int, float)) else 0
        if obdii["dtc_count"] > 0:
            obdii["has_errors"] = True

    return obdii


def detect_configuration_received(attributes: dict[str, Any]) -> dict[str, Any]:
    """Detect when device has received a configuration command."""
    configuration: dict[str, Any] = {
        "received": False,
        "result": None,
        "parameters": [],
    }

    result = attributes.get("result")
    if result is None or result == "":
        return configuration

    result_str = str(result)
    if "New value " in result_str:
        configuration["received"] = True
        configuration["result"] = result_str

        param_string = result_str.replace("New value ", "").strip()
        param_strings = param_string.split(",")

        for param_string_item in param_strings:
            param_string_item = param_string_item.strip()
            if "=" in param_string_item:
                parts = param_string_item.split("=", 1)
                if len(parts) == 2:
                    parameter = {
                        "id": parts[0].strip(),
                        "value": parts[1].strip(),
                    }
                    configuration["parameters"].append(parameter)

    return configuration
