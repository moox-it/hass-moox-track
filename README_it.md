[🇬🇧 English](README.md)

# MOOX-Track Custom Component per HASS

MOOX-Track Custom Component per HASS (hass-moox-track) è un "Componente Custom" che connette i tuoi dispositivi MOOX Track ad Home Assistant, creando per ciascuno un'identità del tipo "Device Tracker"

## Installazione

Installa il componente custom copiando la cartella "moox_track" nella cartella "/config/custom_components" della tua installazione di HASS.
In alternativa puoi trovare questa repository su HACS.

```bash
cp moox_track /config/custom_components
```

## Uso

Aggiungi in /config/configuration.yaml
```yaml
device_tracker:
  - platform: moox_track
    username: latua@email.it
    password: latuapassword
```

## Crediti
Questo componente custom è possibile grazie al encomiabile lavoro di:
Joakim Sørensen (@ludeeus) e tutto il team che contribuisce allo sviluppo e al mantenimento di @home-assistant

## Licenza
[mpl-2.0](http://www.apache.org/licenses/LICENSE-2.0)