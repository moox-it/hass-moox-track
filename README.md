# MOOX Track – Custom Integration for Home Assistant

[![Version](https://img.shields.io/badge/version-2.0.1-blue.svg)](https://github.com/moox-it/hass-moox-track) [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=moox-it&repository=hass-moox-track&category=integration) [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

[🇮🇹 Leggi in Italiano](README_it.md)

Professional GPS tracking integration for Home Assistant. Seamlessly integrate MOOX Track devices into your smart home ecosystem with real-time location tracking, advanced event detection, and comprehensive vehicle monitoring.

---

## 🌟 Features

- 📍 **Real-time GPS Tracking** - Device tracker with full coordinate and accuracy data
- 🗺️ **Geofence Support** - Automatic zone detection and geofence tracking
- 🔋 **Battery Monitoring** - Vehicle battery voltage monitoring
- ⚡ **Speed & Movement** - Speed in knots and km/h, motion detection
- 🚨 **Event Detection** - Event conversion (Ignition, Motion, Towing, Jamming, Battery)
- ⚠️ **Smart Alarms** - Multiple alarm types (Overspeed, Accident, Towing, etc.)
- 🔔 **Warning Detection** - Configuration received, approximate position, sleep mode
- 📡 **GPS Quality** - Satellite count and RSSI monitoring
- 🔧 **OBD-II Diagnostics** - RPM, fuel level, DTC codes (OBD-II devices only; not FMB920/FMC920)
- 📊 **Comprehensive Sensors** - 40+ sensors per device with proper State Classes and Device Classes
- 🎯 **Automation Ready** - Event-based triggers and state-based automations
- 🔐 **Zero Dependencies** - No external packages, direct server communication

---

## 🚀 Version 2.0.1 Highlights

- ✅ **Silent Token Expiration Handling** - Automatic re-authentication without errors or user intervention
- ✅ **Silent Connection Error Handling** - Graceful handling of server unreachability with automatic retries
- ✅ **Production-Ready Reliability** - Comprehensive edge case handling and robust error recovery
- ✅ **Enhanced Error Handling** - Better handling of malformed API responses and edge cases
- ✅ **Improved Stability** - Continuous operation even during network issues or token expiration

## 🚀 Version 2.0 Highlights

- ✅ **Zero External Dependencies** - Faster installation, enhanced security
- ✅ **Config Flow Integration** - UI-based configuration (no YAML required)
- ✅ **Enhanced Compatibility** - Home Assistant 2025.11+
- ✅ **Improved Performance** - Direct server communication with real-time updates
- ✅ **Better Reliability** - Proprietary communication layer

### ⚠️ Breaking Changes from 1.x

- **Config Flow Required**: Remove any `moox_track` YAML entries and reconfigure via UI
- **No External Dependencies**: Removed `pytraccar` and `stringcase` packages
- **Reconfiguration Needed**: Set up integration again through **Settings** → **Devices & Services**

---

## 📦 Installation

### Prerequisites

- Home Assistant 2025.11 or newer
- MOOX Track account ([https://app.moox.it](https://app.moox.it))
- At least one GPS device registered in your MOOX Track account

> 💡 **Try Demo Account**: You can test the integration with the demo account:  
> **Email**: `demo@moox.it`  
> **Password**: `demo`

### HACS Installation (Recommended)

1. Open **HACS** → **Integrations**
2. Click **⋮** → **Custom repositories**
3. Add repository: `https://github.com/moox-it/hass-moox-track`
4. Category: **Integration**
5. Install **MOOX Track** and restart Home Assistant

> 💡 [Open directly in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=moox-it&repository=hass-moox-track&category=integration)

### Manual Installation

1. Download latest release from [GitHub](https://github.com/moox-it/hass-moox-track/releases)
2. Extract `custom_components/moox_track` to your `/config/custom_components/` directory
3. Restart Home Assistant

---

## ⚙️ Configuration

### Initial Setup

1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Search for **"MOOX Track"**
3. Enter your MOOX Track email and password
4. Devices will be automatically discovered

> 💡 [Open config flow directly](https://my.home-assistant.io/redirect/config_flow_start/?domain=moox_track)

### Integration Options

Configure via **Settings** → **Devices & Services** → **MOOX Track** → **Configure**:

- **Update Interval** (seconds, minimum 30): Polling interval for updates
- **Max Accuracy** (meters, default 0): Filter positions with accuracy worse than this value **in Home Assistant only** (does not change device parameters)
- **Custom Attributes**: Add custom attributes from device/position data to device tracker
- **Skip Accuracy Filter For**: Attributes that bypass accuracy filter (useful for critical alarms)
- **Events**: Enable Home Assistant events for selected event types

**Important**: The `Max Accuracy` filter and other options only affect what Home Assistant records and displays. They **do not change** any parameters on your GPS device. Device configuration must be done through the MOOX Track application.

**Example**: Set `Max Accuracy = 50` and `Skip Accuracy Filter For = ["alarm"]` to:
- Accept all positions with accuracy ≤ 50m in Home Assistant
- Filter positions with accuracy > 50m in Home Assistant
- **BUT** accept positions with accuracy > 50m if they contain `alarm` attribute

---

## 📱 Device Configuration

**Important**: Event, alarm, and warning detection must be configured in the MOOX Track application. The integration reads and displays values transmitted by your device.

### Configure Alarms and Warnings

Configure alarms and warnings using the MOOX Track application (mobile app or web app - both have the same configuration):

1. Open **MOOX Track** application ([https://app.moox.it](https://app.moox.it) or mobile app)
2. Tap/click device name → **"Alarms and Warnings"**
3. Enable and configure desired events/alarms/warnings according to your device capabilities

**Download Applications**:
- **Web**: [https://app.moox.it](https://app.moox.it)
- **Android**: [Google Play Store](https://play.google.com/store/apps/details?id=moox.mooxtrack&hl=it)
- **iOS**: [Apple App Store](https://apps.apple.com/it/app/moox-track/id1505287138)

### Geofences: App vs Home Assistant

**Two Separate Systems**:

1. **MOOX Track App Geofences** (configured in the app):
   - Created and managed in the MOOX Track application
   - Generate alarms/warnings when device enters/exits
   - Trigger the `alarms` sensor with values like `"Enter Area"` or `"Exit Area"`
   - These are the geofences that move the alarms/warnings sensor

2. **Home Assistant Zones** (configured in Home Assistant):
   - Created in Home Assistant **Settings** → **Zones**
   - Used by the device tracker to show `home`, `away`, or zone name
   - Completely separate from MOOX Track app geofences
   - Do not generate alarms - they only affect device tracker state

**For Automations**: If you want to trigger automations based on geofence entry/exit, use the `alarms` sensor with values `"Enter Area"` or `"Exit Area"` (from MOOX Track app geofences), not Home Assistant zones.

---

## 🔧 Entities & Sensors

### Entity Structure

Each device creates:
- **1 Device Tracker** (`[01·TRK]`) - Main tracking entity
- **20 Visible Sensors** - GPS, movement, system, events, alarms
- **20 Hidden Diagnostic Sensors** - Battery level, OBD-II, timestamps, last GPS fix data
- **5 Binary Sensors** - Motion, ignition, status, I/O

### Entity Naming

Entities use short tags for alphabetical sorting in Home Assistant UI:
- `[01·TRK]` Device Tracker
- `[02·LOC]` Geofence
- `[03·GPS]` GPS Coordinates (latitude, longitude, altitude)
- `[04·FIX]` Fix Quality (course, accuracy)
- `[05·MOV]` Movement (speed, motion)
- `[06·IO]` Inputs/Outputs (ignition, digital I/O)
- `[07·SYS]` System (satellites, RSSI, power)
- `[08·LOG]` Logging (odometer, event)
- `[09·ALM]` Alarms
- `[10·WRN]` Warnings
- `[11·OBD]` OBD-II Diagnostics
- `[12·CFG]` Configuration
- `[90-94·DIA]` Diagnostic sensors

### Key Sensors

| Sensor | Entity ID Pattern | Description | Unit | State Class | Visible | Diagnostic |
|:-------|:------------------|:-----------|:-----|:-----------|:-------:|:----------:|
| **Device Tracker** | `device_tracker.{device_name}` | Main tracking entity | - | - | ✅ | ❌ |
| **Speed (km/h)** | `sensor.{device_name}_speed_kmh` | Current speed | km/h | Measurement | ✅ | ❌ |
| **Speed (kn)** | `sensor.{device_name}_speed` | Speed in knots | kn | Measurement | ❌ | ❌ |
| **Altitude** | `sensor.{device_name}_altitude` | Elevation | m | Measurement | ✅ | ❌ |
| **Battery Level** | `sensor.{device_name}_battery_level` | Vehicle battery | % | Measurement | ❌ | ✅ |
| **Power** | `sensor.{device_name}_power` | Vehicle voltage | V | Measurement | ✅ | ❌ |
| **Odometer** | `sensor.{device_name}_odometer` | Total distance | m | Total Increasing | ✅ | ❌ |
| **Event** | `sensor.{device_name}_event` | Event text | text | - | ✅ | ❌ |
| **Alarms** | `sensor.{device_name}_alarms` | Detected alarms | text | - | ✅ | ❌ |
| **Warnings** | `sensor.{device_name}_warnings` | Detected warnings | text | - | ✅ | ✅ |
| **Geofence** | `sensor.{device_name}_geofence` | Current geofence name | text | - | ✅ | ❌ |
| **Satellites** | `sensor.{device_name}_sat` | GPS satellite count | - | Measurement | ✅ | ❌ |
| **RSSI** | `sensor.{device_name}_rssi` | Cellular signal strength | dBm | - | ✅ | ❌ |
| **Motion** | `binary_sensor.{device_name}_motion` | Motion detection | - | - | ✅ | ❌ |
| **Ignition** | `binary_sensor.{device_name}_ignition` | Ignition state | - | - | ✅ | ❌ |
| **Status** | `binary_sensor.{device_name}_status` | Device online/offline | - | - | ✅ | ✅ |
| **RPM** | `sensor.{device_name}_rpm` | Engine RPM (OBD-II) | - | Measurement | ❌ | ❌ |
| **Fuel Level** | `sensor.{device_name}_fuel` | Fuel percentage (OBD-II) | % | Measurement | ❌ | ❌ |
| **DTC Codes** | `sensor.{device_name}_dtc_codes` | Diagnostic codes (OBD-II) | text | - | ❌ | ✅ |
| **DTC Count** | `sensor.{device_name}_dtc_count` | Number of codes (OBD-II) | - | Measurement | ❌ | ✅ |

See [Event Sensor Values](#event-sensor-values), [Alarms Sensor Values](#alarms-sensor-values), and [Warnings Sensor Values](#warnings-sensor-values) for detailed value tables.

### Event Sensor Values {#event-sensor-values}

The Event sensor converts numeric event codes to text. **Values are in English** for automation compatibility:

| Value | Event Code | Description |
|:------|:----------:|:-----------|
| `"Ignition Event"` | 239 | Ignition state changed |
| `"Motion Event"` | 240 | Device movement detected |
| `"Towing Event"` | 246 | Possible vehicle towing |
| `"Jamming Event"` | 249 | Possible GPS jamming |
| `"Battery Event"` | 252 | Battery-related event |
| `"Unknown Event (XXX)"` | Other | Unknown code (XXX = numeric) |
| `None` | - | No event |

**Automation Example**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.my_car_event
    to: "Ignition Event"
```

### Alarms Sensor Values {#alarms-sensor-values}

The Alarms sensor displays comma-separated alarm values. **Values are in English** and may contain spaces. **For automations, it's recommended to rely on alarms rather than events** as they provide more specific information.

**Complete List of Alarm Values** (1:1 correspondence with API):

| Alarm Value (Home Assistant) | API Value | Description |
|:---------------------------|:---------:|:-----------|
| `"General Alarm"` | `general` | General alarm condition |
| `"Movement"` | `movement` | Movement detected |
| `"Overspeed"` | `overspeed` | Vehicle speed above threshold |
| `"Battery Voltage Below Limit"` | `lowPower` | Battery voltage below safe limit |
| `"Ignition Off"` | `powerOff` | Vehicle ignition turned off |
| `"Ignition On"` | `powerOn` | Vehicle ignition turned on |
| `"Area"` | `geofence` | Geofence-related alarm |
| `"Enter Area"` | `geofenceEnter` | Entered geofence area |
| `"Exit Area"` | `geofenceExit` | Exited geofence area |
| `"Possible Accident Detected"` | `accident` | Possible accident detected |
| `"Possible Vehicle Towing Detected"` | `tow` | Possible vehicle towing detected |
| `"Excessive Idling"` | `idle` | Vehicle idling for extended period |
| `"Harsh Acceleration Detected"` | `hardAcceleration` | Sudden acceleration detected |
| `"Harsh Braking Detected"` | `hardBraking` | Sudden braking detected |
| `"Harsh Steering Detected"` | `hardCornering` | Sudden steering/cornering detected |
| `"GPS Disconnected From Battery"` | `powerCut` | GPS device disconnected from power |
| `"Possible Jamming Attempt Detected"` | `jamming` | Possible GPS jamming attempt |

**Note**: Multiple alarms are comma-separated (e.g., `"General Alarm, Movement"`). Alarm availability depends on device model and MOOX Track app configuration.

**Alarm Mapping: MOOX Track App → Home Assistant**

| Alarm Name (MOOX Track App) | Traccar Type | Triggered Event | Home Assistant Alarm Value |
|:---------------------------|:------------|:----------------|:--------------------------|
| Enter or exit from a zone (geofence) | `event.type: "geofenceEnter"` or `"geofenceExit"` | Geofence entry/exit | `"Enter Area"` or `"Exit Area"` |
| Automatic perimeter (auto_geofence) | `attributes.alarm: "movement"` | Vehicle movement with engine off | `"Movement"` |
| Ignition on/off (ignition_sensor) | `event.type: "ignitionOn"` or `"ignitionOff"` | Ignition on/off | `"Ignition On"` or `"Ignition Off"` |
| Speed limit (speed_limit) | `event.type: "deviceOverspeed"` | Speed limit exceeded | `"Overspeed"` |
| Strong impact (collision_sensor) | `attributes.alarm: "accident"` | Strong impact detected | `"Possible Accident Detected"` |
| Driving behavior (drive_care) | `attributes.alarm: "hardAcceleration"`, `"hardCornering"`, `"hardBraking"` | Harsh acceleration/steering/braking | `"Harsh Acceleration Detected"`, `"Harsh Steering Detected"`, `"Harsh Braking Detected"` |
| Excessive idling (idling_sensor) | `attributes.alarm: "idle"` | Excessive idling | `"Excessive Idling"` |
| Battery voltage (battery_sensor) | `attributes.alarm: "lowPower"` | Battery voltage below threshold | `"Battery Voltage Below Limit"` |
| Towing or lifting (towing_sensor) | `attributes.alarm: "tow"` | Towing/lifting with engine off | `"Possible Vehicle Towing Detected"` |
| Cable cut (unplug_sensor) | `attributes.alarm: "powerCut"` | Device disconnected from battery | `"GPS Disconnected From Battery"` |
| Signal interference (Jamming) (jamming_sensor) | `attributes.alarm: "jamming"` | GPS signal interference | `"Possible Jamming Attempt Detected"` |

**Automation Examples**:
```yaml
# Single alarm
trigger:
  - platform: state
    entity_id: sensor.my_car_alarms
    to: "Movement"

# Any alarm containing text
trigger:
  - platform: state
    entity_id: sensor.my_car_alarms
condition:
  - condition: template
    value_template: "{{ 'Movement' in states('sensor.my_car_alarms') }}"
```

### Warnings Sensor Values {#warnings-sensor-values}

The Warnings sensor displays one warning at a time (highest priority):

| Value | Priority | Condition |
|:------|:--------:|:----------|
| `"Configuration Received"` | 1 (Highest) | `attributes.result` present, not in sleep mode |
| `"Approximate Position"` | 2 (Medium) | No GPS satellites but RSSI > 0, not in sleep mode |
| `"Sleep Mode Active"` | 3 (Lowest) | `attributes.io200` indicates sleep mode |
| `None` | - | No warnings |

**Automation Example**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.my_car_warnings
    to: "Configuration Received"
```

### OBD-II Sensors

**Device Compatibility**: OBD-II sensors are **only available** on MOOX devices with OBD-II interface. **Not compatible** with FMB920 and FMC920 devices.

| Sensor | Description | Unit |
|:-------|:-----------|:-----|
| **RPM** | Engine revolutions per minute | - |
| **Fuel Level** | Fuel percentage | % |
| **DTC Codes** | Diagnostic trouble codes (comma-separated) | text |
| **DTC Count** | Number of trouble codes | - |

These sensors are **hidden by default** and only display data when connected to a compatible OBD-II device.

---

## 🎯 Automations

### Device Tracker Automations

```yaml
automation:
  - alias: "Car Left Home"
    trigger:
      - platform: state
        entity_id: device_tracker.my_car
        from: "home"
        to: "not_home"
    action:
      - service: notify.mobile_app
        data:
          title: "🚗 Car Alert"
          message: "Car has left home"
```

### Event-Based Automations

Enable events in integration options, then listen to `moox_track_event`:

```yaml
automation:
  - alias: "Geofence Enter Alert"
    trigger:
      - platform: event
        event_type: moox_track_event
        event_data:
          event: geofence_enter
          device_name: "My Car"
    action:
      - service: notify.mobile_app
        data:
          title: "📍 Geofence Alert"
          message: "{{ trigger.event.data.device_name }} entered geofence"
```

**Event Payload Structure**:
The event payload contains:
- `device_moox_id` (int): Device ID from MOOX Track
- `device_name` (str): Device name
- `event` (str): Event type in snake_case (e.g., `geofence_enter`)
- `type` (str): Original event type from API (e.g., `geofenceEnter`)
- `serverTime` (str): Event timestamp from server
- `attributes` (dict): Additional event attributes

**Available Event Types**:
- `device_moving`, `device_stopped`
- `geofence_enter`, `geofence_exit`
- `ignition_on`, `ignition_off`
- `device_online`, `device_offline`, `device_inactive`
- `device_overspeed`, `alarm`, `maintenance`
- `text_message`, `command_result`
- `device_fuel_drop`, `device_fuel_increase`
- `driver_changed`, `device_unknown`
- `queued_command_sent`, `media`

### Sensor-Based Automations

```yaml
# Low battery alert
automation:
  - alias: "Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_car_battery_level
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "🔋 Low Battery"
          message: "Car battery is at {{ states('sensor.my_car_battery_level') }}%"

# Speed monitoring
automation:
  - alias: "High Speed Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_car_speed_kmh
        above: 120
    action:
      - service: notify.mobile_app
        data:
          title: "⚡ High Speed"
          message: "Car speed: {{ states('sensor.my_car_speed_kmh') }} km/h"

# Alarm detection (recommended)
automation:
  - alias: "Movement Alert"
    trigger:
      - platform: state
        entity_id: sensor.my_car_alarms
    condition:
      - condition: template
        value_template: "{{ 'Movement' in states('sensor.my_car_alarms') }}"
    action:
      - service: notify.mobile_app
        data:
          title: "🚨 Movement Alert"
          message: "Vehicle movement detected!"
```

### Template Examples

```yaml
# Check if device is moving
value_template: "{{ is_state('binary_sensor.my_car_motion', 'on') }}"

# Get current geofence
value_template: "{{ states('sensor.my_car_geofence') }}"

# Check for specific alarm
value_template: "{{ 'Towing' in states('sensor.my_car_alarms') }}"

# Calculate distance from home
value_template: >
  {{ distance(
    homeassistant.config.as_dict()['latitude'],
    homeassistant.config.as_dict()['longitude'],
    state_attr('device_tracker.my_car', 'latitude'),
    state_attr('device_tracker.my_car', 'longitude')
  ) | round(2) }}
```

---

## 🔧 Advanced Configuration

### Custom Attributes

Add custom attributes in integration options. Specify a list of attribute names to extract from device or position attributes. These will appear as extra attributes on the device tracker.

**Note**: Custom attributes are extracted from the device's or position's `attributes` dictionary. You cannot add calculated attributes using templates - only existing attributes from the API can be included.

**Example**: To include the `io200` and `io36` attributes:
- Add `io200` and `io36` to the Custom Attributes list in integration options
- These attributes will then appear on the device tracker entity

### Accuracy Filtering

Configure `Max Accuracy` to filter inaccurate GPS readings **in Home Assistant only**:

- **0** (default): Disable filter, accept all positions
- **50**: Filter positions with accuracy > 50 meters
- **100**: Filter positions with accuracy > 100 meters

**Important**: This filter only affects what Home Assistant records. It does not change any device parameters.

Use `Skip Accuracy Filter For` to bypass filter for critical events (e.g., `["alarm"]`).

### Update Interval

- **Minimum**: 30 seconds
- **Default**: Used as fallback polling interval

---

## 🔍 Troubleshooting

### Integration Won't Connect

1. Verify credentials in MOOX Track account
2. Check internet connectivity
3. Verify Home Assistant can reach `app.moox.it`
4. Check logs: **Settings** → **System** → **Logs**

### No Devices Found

1. Ensure devices are registered in MOOX Track account
2. Verify devices are online and sending data
3. Reload integration: **Settings** → **Devices & Services** → **MOOX Track** → **⋮** → **Reload**

### Inaccurate Positions

1. Check GPS device has clear sky view
2. Verify device battery level
3. Adjust `Max Accuracy` in integration options (only affects Home Assistant)
4. Check satellite count (`sat` sensor)

### Events/Alarms Not Appearing

1. **Configure in MOOX Track app**: Events/alarms must be enabled in device settings
2. Check device model compatibility
3. Verify device is transmitting event/alarm data
4. Check `event_raw` diagnostic sensor for raw event codes

### OBD-II Sensors Not Showing

1. **Device Compatibility**: Only available on MOOX devices with OBD-II interface
2. **Not Compatible**: FMB920 and FMC920 do not support OBD-II
3. Sensors are hidden by default - enable in entity registry if device is compatible

---

## 📊 Technical Details

### Entity Unique IDs

Format: `{deviceId}_{dataSource}_{key}`

Examples:
- `12345` (device tracker)
- `12345_position_latitude`
- `12345_position_attributes.event`
- `12345_device_status`

### State Classes

- **Measurement**: Speed, altitude, battery, satellites, power, odometer, RPM, fuel level
- **Total Increasing**: Odometer
- **None**: Event, alarms, warnings, geofence, RSSI, timestamps

### Device Classes

- **Distance**: Odometer
- **Speed**: Speed sensors
- **Motion**: Motion binary sensor
- **Power**: Ignition binary sensor
- **None**: Most other sensors

### Communication

- **Connection**: Direct connection to `app.moox.it` with real-time updates
- **Fallback**: HTTP polling (configurable interval, minimum 30 seconds)
- **Protocol**: HTTPS only, no external dependencies

---

## 🆘 Support

- **Documentation**: [moox.it](https://moox.it)
- **Issues**: [GitHub Issues](https://github.com/moox-it/hass-moox-track/issues)
- **Community**: Home Assistant Community Forum

**Before Reporting Issues**: Include Home Assistant version, integration version, relevant logs, and steps to reproduce.

---

## 🔐 Privacy & Security

- ✅ Credentials encrypted and stored securely
- ✅ HTTPS-only communication
- ✅ Direct connection to MOOX Track servers only
- ✅ Zero external dependencies
- ✅ No data sent to third parties

---

## 📄 License

**Copyright © 2025 MOOX SRLS**

Licensed under the **Apache License, Version 2.0**.

MOOX SRLS  
P.IVA: 05013370753  
Via San Lazzaro n. 18  
73100 Lecce, Italy

Website: [moox.it](https://moox.it)  
Email: info@moox.it

Full license text: [LICENSE](LICENSE)

---

**Made with ❤️ by MOOX SRLS**

*Professional GPS tracking integration for Home Assistant.*
