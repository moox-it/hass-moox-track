[🇮🇹 Read in Italian](README_it.md)

# MOOX Track – Cloud integration for Home Assistant

[![Version](https://img.shields.io/badge/version-2.0.2-blue.svg)](https://github.com/moox-it/hass-moox-track) [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/) [![Open in HACS](https://img.shields.io/badge/HACS-Open%20Repository-2b2c34?logo=homeassistant&logoColor=white)](https://my.home-assistant.io/redirect/hacs_repository/?owner=moox-it&repository=hass-moox-track&category=integration) [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

<img src="assets/branding/moox-track-logo.svg" alt="MOOX Track logo" width="220" />

Cloud GPS tracking integration for Home Assistant. Connect your MOOX Track account and vehicles equipped with MOOX devices to enable real-time tracking, advanced alarms, and more than 40 sensors for continuous 24/7 fleet monitoring without supervision.

---

## 🌟 Features

- 📍 **Real-time GPS tracking** – Device tracker with coordinates, accuracy, and Home Assistant zone mapping
- 🗺️ **Dual geofencing** – Native MOOX alarms plus Home Assistant zones for advanced automations
- ⚡ **Speed and motion** – Speed in knots/kmh, motion status, odometer, course
- 🚨 **Events and alarms** – Ignition, towing, jamming, overspeed, harsh driving, inactivity, and more
- 📡 **Signal quality** – Satellites, RSSI, GPS fix quality, prioritized warnings
- 🔋 **Power** – Vehicle voltage, battery %, low-power detection
- 🔧 **OBD-II (optional)** – RPM, fuel, DTC list/counter on compatible trackers
- 🎯 **Automation ready** – 40+ sensors, Home Assistant events, detailed diagnostics
- 🔐 **Zero external dependencies** – Direct HTTPS to the MOOX cloud, no extra Python packages

---

## 📦 Installation

### Prerequisites

- Home Assistant 2025.11 or newer
- MOOX Track account ([https://app.moox.it](https://app.moox.it))
- At least one GPS device registered to your MOOX Track account

> 💡 **Demo account**: Email `demo@moox.it` | Password `demo`

### HACS (recommended)

1. Open **HACS** → **Integrations**
2. Click **⋮** → **Custom repositories**
3. Add repository `https://github.com/moox-it/hass-moox-track`
4. Category: **Integration**
5. Install **MOOX Track** and restart Home Assistant

> 💡 [Open directly in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=moox-it&repository=hass-moox-track&category=integration)

### Manual installation

1. Download the latest [release](https://github.com/moox-it/hass-moox-track/releases)
2. Extract `custom_components/moox_track` into `/config/custom_components/`
3. Restart Home Assistant

---

## ⚙️ Configuration

### Initial setup

1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Search for **"MOOX Track"**
3. Enter your MOOX Track email and password
4. Devices will be discovered automatically

> 💡 [Open the config flow directly](https://my.home-assistant.io/redirect/config_flow_start/?domain=moox_track)

### Integration options

Configure via **Settings** → **Devices & Services** → **MOOX Track** → **Configure**:

- **Update interval** (seconds, minimum 30): Poll interval for updates
- **Max accuracy** (meters, default 0): Ignore positions with worse accuracy **inside Home Assistant only** (does not change device parameters)
- **Custom attributes**: Copy custom attributes from device/position data to the device tracker
- **Skip accuracy filter for**: Attributes that bypass the accuracy filter (useful for critical alarms)
- **Events**: Enable Home Assistant events for selected event types

**Important:** The `Max accuracy` filter and other options only affect what Home Assistant stores and displays. They **do not** change any parameter on the GPS device. Device configuration must be managed via the MOOX Track app.

---

## 📱 Device configuration

**Important:** Event, alarm, and warning detection must be configured in the MOOX Track application. The integration reads and displays the values transmitted by the device.

### Alarm and warning configuration

1. Open the **MOOX Track** application ([https://app.moox.it](https://app.moox.it) or mobile app)
2. Tap/click the device name → **"Alarms and warnings"**
3. Enable and configure the desired events/alarms/warnings based on device capabilities

**Download the apps**:
- **Web**: [https://app.moox.it](https://app.moox.it)
- **Android**: [Google Play Store](https://play.google.com/store/apps/details?id=moox.mooxtrack&hl=it)
- **iOS**: [Apple App Store](https://apps.apple.com/it/app/moox-track/id1505287138)

### Geofence: app vs Home Assistant

**Two separate systems:**

1. **MOOX Track app geofences** (configured in the app):
   - Created and managed inside the MOOX Track application
   - Generate alarms/warnings when the device enters/exits
   - Trigger the `alarms` sensor with values like `"Enter Area"` or `"Exit Area"`

2. **Home Assistant zones** (configured in Home Assistant):
   - Created under **Settings** → **Zones**
   - Used by the device tracker to show `home`, `away`, or the zone name
   - Completely separate from the app geofences

**For automations:** If you want to trigger automations on geofence entry/exit, use the `alarms` sensor with values `"Enter Area"` or `"Exit Area"` (from the MOOX Track app geofences), not Home Assistant zones.

---

## 🔧 Entities and sensors

Each device creates:
- **1 Device Tracker** (`[01·TRK]`) – Main tracking entity
- **20 Visible Sensors** – GPS, motion, system, events, alarms
- **20 Hidden Diagnostic Sensors** – Battery level, OBD-II, timestamps, last GPS fix data
- **5 Binary Sensors** – Motion, ignition, state, I/O

### Key sensors

| Sensor | Entity ID | Description |
|:--------|:----------|:------------|
| **Device tracker** | `device_tracker.{device_name}` | Main tracking entity |
| **Speed (km/h)** | `sensor.{device_name}_speed_kmh` | Current speed |
| **Altitude** | `sensor.{device_name}_altitude` | Elevation |
| **Voltage** | `sensor.{device_name}_power` | Vehicle voltage |
| **Odometer** | `sensor.{device_name}_odometer` | Total distance |
| **Event** | `sensor.{device_name}_event` | Event text |
| **Alarms** | `sensor.{device_name}_alarms` | Detected alarms |
| **Geofence** | `sensor.{device_name}_geofence` | Current geofence name |
| **Satellites** | `sensor.{device_name}_sat` | GPS satellite count |
| **RSSI** | `sensor.{device_name}_rssi` | Cellular signal strength |
| **Motion** | `binary_sensor.{device_name}_motion` | Motion detection |
| **Ignition** | `binary_sensor.{device_name}_ignition` | Ignition state |

See the [full documentation](docs_dev/docs/IT/ENTITA_E_SENSORI.md) for the complete list of sensors and their values.

---

## 🎯 Automations

### Example: device tracker

```yaml
automation:
  - alias: "Car left home"
    trigger:
      - platform: state
        entity_id: device_tracker.my_car
        from: "home"
        to: "not_home"
    action:
      - service: notify.mobile_app
        data:
          title: "🚗 Vehicle alert"
          message: "The car left home"
```

### Example: events

Enable events in the integration options, then listen for `moox_track_event`:

```yaml
automation:
  - alias: "Geofence entry alert"
    trigger:
      - platform: event
        event_type: moox_track_event
        event_data:
          event: geofence_enter
          device_name: "My Car"
    action:
      - service: notify.mobile_app
        data:
          title: "📍 Geofence alert"
          message: "{{ trigger.event.data.device_name }} entered a geofence"
```

### Example: alarms

```yaml
automation:
  - alias: "Movement alert"
    trigger:
      - platform: state
        entity_id: sensor.my_car_alarms
    condition:
      - condition: template
        value_template: "{{ 'Movement' in states('sensor.my_car_alarms') }}"
    action:
      - service: notify.mobile_app
        data:
          title: "🚨 Movement alert"
          message: "Vehicle movement detected!"
```

---

## 🔍 Troubleshooting

### Integration will not connect

1. Verify MOOX Track account credentials
2. Check internet connectivity
3. Ensure Home Assistant can reach `app.moox.it`
4. Check the logs: **Settings** → **System** → **Logs**

### No devices found

1. Make sure the devices are registered in the MOOX Track account
2. Confirm the devices are online and sending data
3. Reload the integration: **Settings** → **Devices & Services** → **MOOX Track** → **⋮** → **Reload**

### Events/alarms do not appear

1. **Configure them in the MOOX Track app**: Events/alarms must be enabled in the device settings
2. Check the device model compatibility
3. Ensure the device is transmitting alarm/event data

---

## 🆘 Support

- **Documentation**: [moox.it](https://moox.it)
- **Issues**: [GitHub Issues](https://github.com/moox-it/hass-moox-track/issues)
- **Community**: Home Assistant Community Forum

**Before reporting an issue**: Include Home Assistant version, integration version, relevant logs, and reproduction steps.

---

## 🔐 Privacy and security

- ✅ Credentials encrypted and stored securely
- ✅ HTTPS-only communication
- ✅ Direct connection to MOOX Track servers
- ✅ Zero external dependencies
- ✅ No data shared with third parties

---

## 📋 Changelog

### 2.0.2
- Automatic reconnection: continuously retries in the background for up to 12 hours when the server is unavailable or there are connection issues
- Automatic session recovery with smart retry logic
- Cached data displayed while reconnecting
- State persistence across Home Assistant restarts

See [CHANGELOG.md](CHANGELOG.md) for full history.

---

## 📄 License

**Copyright © 2025 MOOX SRLS**

Licensed under the **Apache License, Version 2.0**.

MOOX SRLS  
VAT: 05013370753  
Via San Lazzaro n. 18  
73100 Lecce, Italy

Website: [moox.it](https://moox.it)  
Email: info@moox.it

Full license text: [LICENSE](LICENSE)

---

**Made with ❤️ by MOOX SRLS**

*Professional GPS tracking integration for Home Assistant.*
