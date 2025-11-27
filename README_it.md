[🇬🇧 Read in English](README.md)

# MOOX Track – Integrazione cloud per Home Assistant

[![Version](https://img.shields.io/badge/version-2.0.2-blue.svg)](https://github.com/moox-it/hass-moox-track) [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/) [![Open in HACS](https://img.shields.io/badge/HACS-Apri%20Repository-2b2c34?logo=homeassistant&logoColor=white)](https://my.home-assistant.io/redirect/hacs_repository/?owner=moox-it&repository=hass-moox-track&category=integration) [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

<img src="assets/branding/moox-track-logo.svg" alt="Logo MOOX Track" width="220" />

Integrazione cloud di tracciamento GPS per Home Assistant. Collega il tuo account MOOX Track e i veicoli dotati di dispositivi MOOX Track, abilitando tracciamento in tempo reale, allarmi avanzati e oltre 40 sensori per il monitoraggio continuo di flotte e mezzi H24, anche senza presidio.

---

## 🌟 Caratteristiche

- 📍 **Tracciamento GPS in tempo reale** - Device tracker con coordinate, accuratezza e mappatura sulle zone di Home Assistant
- 🗺️ **Doppio geofencing** - Allarmi nativi MOOX + zone Home Assistant per automazioni avanzate
- ⚡ **Velocità e movimento** - Velocità in nodi/kmh, stato movimento, odometro, rotta
- 🚨 **Eventi e allarmi** - Accensione, traino, jamming, overspeed, guida brusca, inattività e altro
- 📡 **Qualità segnale** - Satelliti, RSSI, qualità fix, warning con priorità
- 🔋 **Alimentazione** - Voltaggio veicolo, batteria %, rilevamento low-power
- 🔧 **OBD-II (opzionale)** - RPM, carburante, lista/counter DTC su tracker compatibili
- 🎯 **Pronto per automazioni** - 40+ sensori, eventi su event bus, diagnostica dettagliata
- 🔐 **Zero dipendenze esterne** - HTTPS diretto verso il cloud MOOX, nessun pacchetto Python aggiuntivo

---

## 📦 Installazione

### Prerequisiti

- Home Assistant 2025.11 o più recente
- Account MOOX Track ([https://app.moox.it](https://app.moox.it))
- Almeno un dispositivo GPS registrato nel tuo account MOOX Track

> 💡 **Prova Account Demo**: Email: `demo@moox.it` | Password: `demo`

### HACS (Consigliato)

1. Apri **HACS** → **Integrazioni**
2. Clicca **⋮** → **Repository personalizzati**
3. Aggiungi repository: `https://github.com/moox-it/hass-moox-track`
4. Categoria: **Integration**
5. Installa **MOOX Track** e riavvia Home Assistant

> 💡 [Apri direttamente in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=moox-it&repository=hass-moox-track&category=integration)

### Installazione Manuale

1. Scarica l'ultima [release](https://github.com/moox-it/hass-moox-track/releases)
2. Estrai `custom_components/moox_track` nella directory `/config/custom_components/`
3. Riavvia Home Assistant

---

## ⚙️ Configurazione

### Configurazione Iniziale

1. **Impostazioni** → **Dispositivi e Servizi** → **+ Aggiungi Integrazione**
2. Cerca **"MOOX Track"**
3. Inserisci email e password MOOX Track
4. I dispositivi verranno scoperti automaticamente

> 💡 [Apri config flow direttamente](https://my.home-assistant.io/redirect/config_flow_start/?domain=moox_track)

### Opzioni Integrazione

Configura tramite **Impostazioni** → **Dispositivi e Servizi** → **MOOX Track** → **Configura**:

- **Intervallo Aggiornamento** (secondi, minimo 30): Intervallo polling per aggiornamenti
- **Precisione Massima** (metri, default 0): Filtra posizioni con precisione peggiore di questo valore **solo in Home Assistant** (non cambia parametri dispositivo)
- **Attributi Personalizzati**: Aggiungi attributi personalizzati dai dati dispositivo/posizione al device tracker
- **Salta Filtro Precisione Per**: Attributi che bypassano filtro precisione (utile per allarmi critici)
- **Eventi**: Abilita eventi Home Assistant per tipi di evento selezionati

**Importante**: Il filtro `Precisione Massima` e le altre opzioni influenzano solo ciò che Home Assistant registra e visualizza. **Non cambiano** alcun parametro sul dispositivo GPS. La configurazione del dispositivo deve essere fatta tramite l'applicazione MOOX Track.

---

## 📱 Configurazione Dispositivo

**Importante**: Il rilevamento di eventi, allarmi e avvisi deve essere configurato nell'applicazione MOOX Track. L'integrazione legge e visualizza i valori trasmessi dal dispositivo.

### Configurazione Allarmi e Avvisi

1. Apri applicazione **MOOX Track** ([https://app.moox.it](https://app.moox.it) o app mobile)
2. Tocca/clicca nome dispositivo → **"Allarmi e avvisi"**
3. Abilita e configura eventi/allarmi/avvisi desiderati in base alle capacità del dispositivo

**Scarica Applicazioni**:
- **Web**: [https://app.moox.it](https://app.moox.it)
- **Android**: [Google Play Store](https://play.google.com/store/apps/details?id=moox.mooxtrack&hl=it)
- **iOS**: [Apple App Store](https://apps.apple.com/it/app/moox-track/id1505287138)

### Geofence: App vs Home Assistant

**Due Sistemi Separati**:

1. **Geofence App MOOX Track** (configurate nell'app):
   - Create e gestite nell'applicazione MOOX Track
   - Generano allarmi/avvisi quando il dispositivo entra/esce
   - Attivano il sensore `alarms` con valori come `"Enter Area"` o `"Exit Area"`

2. **Zone Home Assistant** (configurate in Home Assistant):
   - Create in Home Assistant **Impostazioni** → **Zone**
   - Utilizzate dal device tracker per mostrare `home`, `away`, o nome zona
   - Completamente separate dalle geofence app MOOX Track

**Per Automazioni**: Se vuoi attivare automazioni basate su ingresso/uscita geofence, usa il sensore `alarms` con valori `"Enter Area"` o `"Exit Area"` (dalle geofence app MOOX Track), non le zone Home Assistant.

---

## 🔧 Entità e Sensori

Ogni dispositivo crea:
- **1 Device Tracker** (`[01·TRK]`) - Entità tracciamento principale
- **20 Sensori Visibili** - GPS, movimento, sistema, eventi, allarmi
- **20 Sensori Diagnostici Nascosti** - Livello batteria, OBD-II, timestamp, dati ultimo fix GPS
- **5 Binary Sensor** - Movimento, accensione, stato, I/O

### Sensori Principali

| Sensore | Entity ID | Descrizione |
|:--------|:----------|:------------|
| **Device Tracker** | `device_tracker.{nome_dispositivo}` | Entità tracciamento principale |
| **Velocità (km/h)** | `sensor.{nome_dispositivo}_speed_kmh` | Velocità corrente |
| **Altitudine** | `sensor.{nome_dispositivo}_altitude` | Elevazione |
| **Tensione** | `sensor.{nome_dispositivo}_power` | Tensione veicolo |
| **Contachilometri** | `sensor.{nome_dispositivo}_odometer` | Distanza totale |
| **Evento** | `sensor.{nome_dispositivo}_event` | Testo evento |
| **Allarmi** | `sensor.{nome_dispositivo}_alarms` | Allarmi rilevati |
| **Geofence** | `sensor.{nome_dispositivo}_geofence` | Nome geofence corrente |
| **Satelliti** | `sensor.{nome_dispositivo}_sat` | Conteggio satelliti GPS |
| **RSSI** | `sensor.{nome_dispositivo}_rssi` | Forza segnale cellulare |
| **Movimento** | `binary_sensor.{nome_dispositivo}_motion` | Rilevamento movimento |
| **Accensione** | `binary_sensor.{nome_dispositivo}_ignition` | Stato accensione |

Vedi la [documentazione completa](docs_dev/docs/IT/ENTITA_E_SENSORI.md) per l'elenco completo di tutti i sensori e i loro valori.

---

## 🎯 Automazioni

### Esempio: Device Tracker

```yaml
automation:
  - alias: "Auto Lasciata Casa"
    trigger:
      - platform: state
        entity_id: device_tracker.mia_auto
        from: "home"
        to: "not_home"
    action:
      - service: notify.mobile_app
        data:
          title: "🚗 Avviso Auto"
          message: "L'auto ha lasciato casa"
```

### Esempio: Eventi

Abilita eventi nelle opzioni integrazione, poi ascolta `moox_track_event`:

```yaml
automation:
  - alias: "Avviso Ingresso Geofence"
    trigger:
      - platform: event
        event_type: moox_track_event
        event_data:
          event: geofence_enter
          device_name: "La Mia Auto"
    action:
      - service: notify.mobile_app
        data:
          title: "📍 Avviso Geofence"
          message: "{{ trigger.event.data.device_name }} è entrata in geofence"
```

### Esempio: Allarmi

```yaml
automation:
  - alias: "Avviso Movimento"
    trigger:
      - platform: state
        entity_id: sensor.mia_auto_alarms
    condition:
      - condition: template
        value_template: "{{ 'Movement' in states('sensor.mia_auto_alarms') }}"
    action:
      - service: notify.mobile_app
        data:
          title: "🚨 Avviso Movimento"
          message: "Movimento veicolo rilevato!"
```

---

## 🔍 Risoluzione Problemi

### L'Integrazione Non Si Connette

1. Verifica credenziali account MOOX Track
2. Controlla connettività internet
3. Verifica che Home Assistant possa raggiungere `app.moox.it`
4. Controlla log: **Impostazioni** → **Sistema** → **Log**

### Nessun Dispositivo Trovato

1. Assicurati che i dispositivi siano registrati nell'account MOOX Track
2. Verifica che i dispositivi siano online e stiano inviando dati
3. Ricarica integrazione: **Impostazioni** → **Dispositivi e Servizi** → **MOOX Track** → **⋮** → **Ricarica**

### Eventi/Allarmi Non Appaiono

1. **Configura nell'app MOOX Track**: Eventi/allarmi devono essere abilitati nelle impostazioni dispositivo
2. Controlla compatibilità modello dispositivo
3. Verifica che il dispositivo stia trasmettendo dati evento/allarme

---

## 🆘 Supporto

- **Documentazione**: [moox.it](https://moox.it)
- **Problemi**: [GitHub Issues](https://github.com/moox-it/hass-moox-track/issues)
- **Community**: Forum Community Home Assistant

**Prima di Segnalare Problemi**: Includi versione Home Assistant, versione integrazione, log rilevanti e passaggi per riprodurre.

---

## 🔐 Privacy e Sicurezza

- ✅ Credenziali crittografate e memorizzate in modo sicuro
- ✅ Comunicazione solo HTTPS
- ✅ Connessione diretta solo ai server MOOX Track
- ✅ Zero dipendenze esterne
- ✅ Nessun dato inviato a terze parti

---

## 📋 Changelog

### 2.0.2
- Riconnessione automatica: riprova continuamente in background per un massimo di 12 ore quando il server non è disponibile o ci sono problemi di connessione
- Recupero automatico sessione con logica di retry intelligente
- Dati in cache visualizzati durante la riconnessione
- Persistenza stato tra riavvii di Home Assistant

Vedi [CHANGELOG.md](CHANGELOG.md) per lo storico completo.

---

## 📄 Licenza

**Copyright © 2025 MOOX SRLS**

Concesso in licenza secondo la **Licenza Apache, Versione 2.0**.

MOOX SRLS  
P.IVA: 05013370753  
Via San Lazzaro n. 18  
73100 Lecce, Italia

Sito web: [moox.it](https://moox.it)  
Email: info@moox.it

Testo completo licenza: [LICENSE](LICENSE)

---

**Realizzato con ❤️ da MOOX SRLS**

*Integrazione professionale di tracciamento GPS per Home Assistant.*
