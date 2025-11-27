"""Constants for MOOX Track.

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

import re
from logging import getLogger

DOMAIN = "moox_track"
LOGGER = getLogger(__name__)


def to_snake_case(camel_str: str) -> str:
    """Convert camelCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str).lower()


ATTR_CATEGORY = "category"
ATTR_GEOFENCE = "geofence"
ATTR_TRACKER = "tracker"
ATTR_MOOX_ID = "moox_id"

CONF_MAX_ACCURACY = "max_accuracy"
CONF_CUSTOM_ATTRIBUTES = "custom_attributes"
CONF_EVENTS = "events"
CONF_SKIP_ACCURACY_FILTER_FOR = "skip_accuracy_filter_for"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_EMAIL = "email"
CONF_USERNAME_DEPRECATED = "username"

# Grace period before escalating errors to user
# For credentials that previously worked: wait longer (server might be temporarily down)
AUTH_FAILURE_GRACE_PERIOD_HOURS = 12

# For credentials that NEVER worked: shorter grace period then prompt reauth
# This handles the case where we can't tell if it's wrong password or server down
AUTH_NEVER_WORKED_GRACE_PERIOD_HOURS = 1

EVENTS = {
    "deviceMoving": "device_moving",
    "commandResult": "command_result",
    "deviceFuelDrop": "device_fuel_drop",
    "deviceFuelIncrease": "device_fuel_increase",
    "geofenceEnter": "geofence_enter",
    "deviceOffline": "device_offline",
    "deviceInactive": "device_inactive",
    "driverChanged": "driver_changed",
    "geofenceExit": "geofence_exit",
    "deviceOverspeed": "device_overspeed",
    "deviceOnline": "device_online",
    "deviceStopped": "device_stopped",
    "maintenance": "maintenance",
    "alarm": "alarm",
    "textMessage": "text_message",
    "deviceUnknown": "device_unknown",
    "ignitionOff": "ignition_off",
    "ignitionOn": "ignition_on",
    "queuedCommandSent": "queued_command_sent",
    "media": "media",
}
