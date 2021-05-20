[🇮🇹 Italiano](README_it.md)

# MOOX-Track Custom Component for HASS

MOOX-Track Custom Component for HASS (hass-moox-track) is a custom component that connects your MOOX Track devices to Home Assistant as "Device Trackers"

## Installation

Install the custom component coping "moox_track" folder inside "/config/custom_components" in your HASS installation. Alternatively you can find this repository on HACS.

```bash
cp moox_track /config/custom_components
```

## Usage

Add in /config/configuration.yaml
```yaml
device_tracker:
  - platform: moox_track
    username: your@email.it
    password: yourpassword
```

## Credits
This custom component is based on the fantastic work of:
Joakim Sørensen (@ludeeus), The Home Assistant Contributors and Team @home-assistant

## License
[mpl-2.0](http://www.apache.org/licenses/LICENSE-2.0)