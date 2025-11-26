[🇬🇧 Read in English](README.md)

# MOOX Track – Integrazione personalizzata per Home Assistant

[![Version](https://img.shields.io/badge/version-2.0.1-blue.svg)](https://github.com/moox-it/hass-moox-track) [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=moox-it&repository=hass-moox-track&category=integration) [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Integrazione professionale di tracciamento GPS per Home Assistant. Integra perfettamente i dispositivi MOOX Track nel tuo ecosistema domotico con tracciamento posizione in tempo reale, rilevamento eventi avanzato e monitoraggio completo dei veicoli.

---

## 🌟 Caratteristiche

- 📍 **Tracciamento GPS in Tempo Reale** - Device tracker con coordinate e dati di precisione completi
- 🗺️ **Supporto Geofence** - Rilevamento automatico zone e tracciamento geofence
- 🔋 **Monitoraggio Batteria** - Monitoraggio tensione batteria veicolo
- ⚡ **Velocità e Movimento** - Velocità in nodi e km/h, rilevamento movimento
- 🚨 **Rilevamento Eventi** - Conversione eventi (Accensione, Movimento, Traino, Jamming, Batteria)
- ⚠️ **Allarmi Intelligenti** - Diversi tipi di allarme (Velocità eccessiva, Incidente, Traino, ecc.)
- 🔔 **Rilevamento Avvisi** - Configurazione ricevuta, posizione approssimativa, modalità sleep
- 📡 **Qualità GPS** - Conteggio satelliti e monitoraggio RSSI
- 🔧 **Diagnostica OBD-II** - Giri motore, livello carburante, codici errore (solo dispositivi OBD-II; non FMB920/FMC920)
- 📊 **Sensori Completi** - 40+ sensori per dispositivo con State Class e Device Class corrette
- 🎯 **Pronto per Automazioni** - Trigger basati su eventi e automazioni basate su stato
- 🔐 **Zero Dipendenze** - Nessun pacchetto esterno, comunicazione diretta con server

---

## 🚀 Novità Versione 2.0.1

- ✅ **Gestione Silenziosa Scadenza Token** - Re-autenticazione automatica senza errori o intervento utente
- ✅ **Gestione Silenziosa Errori di Connessione** - Gestione elegante dell'irraggiungibilità del server con tentativi automatici
- ✅ **Affidabilità Pronta per Produzione** - Gestione completa dei casi limite e recupero robusto dagli errori
- ✅ **Gestione Errori Migliorata** - Migliore gestione delle risposte API malformate e casi limite
- ✅ **Stabilità Migliorata** - Funzionamento continuo anche durante problemi di rete o scadenza token

## 🚀 Novità Versione 2.0

- ✅ **Zero Dipendenze Esterne** - Installazione più veloce, sicurezza migliorata
- ✅ **Integrazione Config Flow** - Configurazione basata su UI (nessun YAML richiesto)
- ✅ **Compatibilità Migliorata** - Home Assistant 2025.11+
- ✅ **Prestazioni Migliorate** - Comunicazione diretta con server con aggiornamenti in tempo reale
- ✅ **Maggiore Affidabilità** - Strato di comunicazione proprietario

### ⚠️ Modifiche Incompatibili dalla 1.x

- **Config Flow Richiesto**: Rimuovi eventuali voci YAML `moox_track` e riconfigura via UI
- **Nessuna Dipendenza Esterna**: Rimossi pacchetti `pytraccar` e `stringcase`
- **Riconfigurazione Necessaria**: Configura nuovamente l'integrazione tramite **Impostazioni** → **Dispositivi e Servizi**

---

## 📦 Installazione

### Prerequisiti

- Home Assistant 2025.11 o più recente
- Account MOOX Track ([https://app.moox.it](https://app.moox.it))
- Almeno un dispositivo GPS registrato nel tuo account MOOX Track

> 💡 **Prova Account Demo**: Puoi testare l'integrazione con l'account demo:  
> **Email**: `demo@moox.it`  
> **Password**: `demo`

### Installazione HACS (Consigliata)

1. Apri **HACS** → **Integrazioni**
2. Clicca **⋮** → **Repository personalizzati**
3. Aggiungi repository: `https://github.com/moox-it/hass-moox-track`
4. Categoria: **Integration**
5. Installa **MOOX Track** e riavvia Home Assistant

> 💡 [Apri direttamente in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=moox-it&repository=hass-moox-track&category=integration)

### Installazione Manuale

1. Scarica l'ultima release da [GitHub](https://github.com/moox-it/hass-moox-track/releases)
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

**Esempio**: Imposta `Precisione Massima = 50` e `Salta Filtro Precisione Per = ["alarm"]` per:
- Accettare tutte le posizioni con precisione ≤ 50m in Home Assistant
- Filtrare posizioni con precisione > 50m in Home Assistant
- **MA** accettare posizioni con precisione > 50m se contengono attributo `alarm`

---

## 📱 Configurazione Dispositivo

**Importante**: Il rilevamento di eventi, allarmi e avvisi deve essere configurato nell'applicazione MOOX Track. L'integrazione legge e visualizza i valori trasmessi dal dispositivo.

### Configurazione Allarmi e Avvisi

Configura allarmi e avvisi utilizzando l'applicazione MOOX Track (app mobile o web - entrambe hanno la stessa configurazione):

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
   - Queste sono le geofence che muovono il sensore allarmi/avvisi

2. **Zone Home Assistant** (configurate in Home Assistant):
   - Create in Home Assistant **Impostazioni** → **Zone**
   - Utilizzate dal device tracker per mostrare `home`, `away`, o nome zona
   - Completamente separate dalle geofence app MOOX Track
   - Non generano allarmi - influenzano solo lo stato del device tracker

**Per Automazioni**: Se vuoi attivare automazioni basate su ingresso/uscita geofence, usa il sensore `alarms` con valori `"Enter Area"` o `"Exit Area"` (dalle geofence app MOOX Track), non le zone Home Assistant.

---

## 🔧 Entità e Sensori

### Struttura Entità

Ogni dispositivo crea:
- **1 Device Tracker** (`[01·TRK]`) - Entità tracciamento principale
- **20 Sensori Visibili** - GPS, movimento, sistema, eventi, allarmi
- **20 Sensori Diagnostici Nascosti** - Livello batteria, OBD-II, timestamp, dati ultimo fix GPS
- **5 Binary Sensor** - Movimento, accensione, stato, I/O

### Nomenclatura Entità

Le entità utilizzano tag brevi per ordinamento alfabetico nella UI di Home Assistant:
- `[01·TRK]` Device Tracker
- `[02·LOC]` Geofence
- `[03·GPS]` Coordinate GPS (latitudine, longitudine, altitudine)
- `[04·FIX]` Qualità Fix (rotta, precisione)
- `[05·MOV]` Movimento (velocità, movimento)
- `[06·IO]` Ingressi/Uscite (accensione, I/O digitale)
- `[07·SYS]` Sistema (satelliti, RSSI, tensione)
- `[08·LOG]` Logging (contachilometri, evento)
- `[09·ALM]` Allarmi
- `[10·WRN]` Avvisi
- `[11·OBD]` Diagnostica OBD-II
- `[12·CFG]` Configurazione
- `[90-94·DIA]` Sensori diagnostici

### Sensori Principali

| Sensore | Pattern Entity ID | Descrizione | Unità | State Class | Visibile | Diagnostico |
|:--------|:------------------|:-----------|:-----|:-----------|:-------:|:-----------:|
| **Device Tracker** | `device_tracker.{nome_dispositivo}` | Entità tracciamento principale | - | - | ✅ | ❌ |
| **Velocità (km/h)** | `sensor.{nome_dispositivo}_speed_kmh` | Velocità corrente | km/h | Measurement | ✅ | ❌ |
| **Velocità (kn)** | `sensor.{nome_dispositivo}_speed` | Velocità in nodi | kn | Measurement | ❌ | ❌ |
| **Altitudine** | `sensor.{nome_dispositivo}_altitude` | Elevazione | m | Measurement | ✅ | ❌ |
| **Livello Batteria** | `sensor.{nome_dispositivo}_battery_level` | Batteria veicolo | % | Measurement | ❌ | ✅ |
| **Tensione** | `sensor.{nome_dispositivo}_power` | Tensione veicolo | V | Measurement | ✅ | ❌ |
| **Contachilometri** | `sensor.{nome_dispositivo}_odometer` | Distanza totale | m | Total Increasing | ✅ | ❌ |
| **Evento** | `sensor.{nome_dispositivo}_event` | Testo evento | testo | - | ✅ | ❌ |
| **Allarmi** | `sensor.{nome_dispositivo}_alarms` | Allarmi rilevati | testo | - | ✅ | ❌ |
| **Avvisi** | `sensor.{nome_dispositivo}_warnings` | Avvisi rilevati | testo | - | ✅ | ✅ |
| **Geofence** | `sensor.{nome_dispositivo}_geofence` | Nome geofence corrente | testo | - | ✅ | ❌ |
| **Satelliti** | `sensor.{nome_dispositivo}_sat` | Conteggio satelliti GPS | - | Measurement | ✅ | ❌ |
| **RSSI** | `sensor.{nome_dispositivo}_rssi` | Forza segnale cellulare | dBm | - | ✅ | ❌ |
| **Movimento** | `binary_sensor.{nome_dispositivo}_motion` | Rilevamento movimento | - | - | ✅ | ❌ |
| **Accensione** | `binary_sensor.{nome_dispositivo}_ignition` | Stato accensione | - | - | ✅ | ❌ |
| **Stato** | `binary_sensor.{nome_dispositivo}_status` | Dispositivo online/offline | - | - | ✅ | ✅ |
| **RPM** | `sensor.{nome_dispositivo}_rpm` | Giri motore (OBD-II) | - | Measurement | ❌ | ❌ |
| **Livello Carburante** | `sensor.{nome_dispositivo}_fuel` | Percentuale carburante (OBD-II) | % | Measurement | ❌ | ❌ |
| **Codici DTC** | `sensor.{nome_dispositivo}_dtc_codes` | Codici diagnostici (OBD-II) | testo | - | ❌ | ✅ |
| **Conteggio DTC** | `sensor.{nome_dispositivo}_dtc_count` | Numero codici (OBD-II) | - | Measurement | ❌ | ✅ |

Vedi [Valori Sensore Evento](#valori-sensore-evento), [Valori Sensore Allarmi](#valori-sensore-allarmi) e [Valori Sensore Avvisi](#valori-sensore-avvisi) per tabelle dettagliate.

### Valori Sensore Evento {#valori-sensore-evento}

Il sensore Evento converte codici evento numerici in testo. **I valori sono in inglese** per compatibilità automazioni:

| Valore | Codice Evento | Descrizione |
|:-------|:-------------:|:-----------|
| `"Ignition Event"` | 239 | Stato accensione cambiato |
| `"Motion Event"` | 240 | Movimento dispositivo rilevato |
| `"Towing Event"` | 246 | Possibile traino veicolo |
| `"Jamming Event"` | 249 | Possibile jamming GPS |
| `"Battery Event"` | 252 | Evento relativo batteria |
| `"Unknown Event (XXX)"` | Altro | Codice sconosciuto (XXX = numerico) |
| `None` | - | Nessun evento |

**Esempio Automazione**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.mia_auto_event
    to: "Ignition Event"
```

### Valori Sensore Allarmi {#valori-sensore-allarmi}

Il sensore Allarmi visualizza valori allarme separati da virgola. **I valori sono in inglese** e possono contenere spazi. **Per le automazioni, è consigliato affidarsi agli allarmi piuttosto che agli eventi** poiché forniscono informazioni più specifiche.

**Elenco Completo Valori Allarme** (corrispondenza 1:1 con API):

| Valore Allarme (Home Assistant) | Valore API | Descrizione |
|:-------------------------------|:----------:|:-----------|
| `"General Alarm"` | `general` | Condizione allarme generale |
| `"Movement"` | `movement` | Movimento rilevato |
| `"Overspeed"` | `overspeed` | Velocità veicolo sopra soglia |
| `"Battery Voltage Below Limit"` | `lowPower` | Tensione batteria sotto limite sicuro |
| `"Ignition Off"` | `powerOff` | Accensione veicolo spenta |
| `"Ignition On"` | `powerOn` | Accensione veicolo accesa |
| `"Area"` | `geofence` | Allarme relativo geofence |
| `"Enter Area"` | `geofenceEnter` | Entrato in area geofence |
| `"Exit Area"` | `geofenceExit` | Uscito da area geofence |
| `"Possible Accident Detected"` | `accident` | Possibile incidente rilevato |
| `"Possible Vehicle Towing Detected"` | `tow` | Possibile traino veicolo rilevato |
| `"Excessive Idling"` | `idle` | Sosta eccessiva veicolo |
| `"Harsh Acceleration Detected"` | `hardAcceleration` | Accelerazione brusca rilevata |
| `"Harsh Braking Detected"` | `hardBraking` | Frenata brusca rilevata |
| `"Harsh Steering Detected"` | `hardCornering` | Sterzata brusca rilevata |
| `"GPS Disconnected From Battery"` | `powerCut` | Dispositivo GPS scollegato dall'alimentazione |
| `"Possible Jamming Attempt Detected"` | `jamming` | Possibile tentativo jamming GPS |

**Nota**: Più allarmi sono separati da virgola (es. `"General Alarm, Movement"`). La disponibilità degli allarmi dipende dal modello dispositivo e configurazione app MOOX Track.

**Mappatura Allarmi: App MOOX Track → Home Assistant**

| Nome Allarme (App MOOX Track) | Tipo Traccar | Evento Scatenato | Valore Allarme Home Assistant |
|:------------------------------|:------------|:-----------------|:------------------------------|
| Entra o esce da una zona (geofence) | `event.type: "geofenceEnter"` o `"geofenceExit"` | Ingresso/Uscita da zona geografica | `"Enter Area"` o `"Exit Area"` |
| Perimetro automatico (auto_geofence) | `attributes.alarm: "movement"` | Movimento veicolo a motore spento | `"Movement"` |
| Accensione o spegnimento (ignition_sensor) | `event.type: "ignitionOn"` o `"ignitionOff"` | Accensione/Spegnimento motore | `"Ignition On"` o `"Ignition Off"` |
| Limite di velocità (speed_limit) | `event.type: "deviceOverspeed"` | Superamento limite velocità | `"Overspeed"` |
| Forte impatto (collision_sensor) | `attributes.alarm: "accident"` | Rilevamento forte impatto | `"Possible Accident Detected"` |
| Controllo andatura (drive_care) | `attributes.alarm: "hardAcceleration"`, `"hardCornering"`, `"hardBraking"` | Accelerazione/Sterzata/Frenata brusca | `"Harsh Acceleration Detected"`, `"Harsh Steering Detected"`, `"Harsh Braking Detected"` |
| Sosta eccessiva (idling_sensor) | `attributes.alarm: "idle"` | Sosta eccessiva | `"Excessive Idling"` |
| Voltaggio batteria (battery_sensor) | `attributes.alarm: "lowPower"` | Voltaggio batteria sotto soglia | `"Battery Voltage Below Limit"` |
| Traino o sollevamento (towing_sensor) | `attributes.alarm: "tow"` | Traino/sollevamento a motore spento | `"Possible Vehicle Towing Detected"` |
| Taglio dei cavi (unplug_sensor) | `attributes.alarm: "powerCut"` | Dispositivo scollegato da batteria | `"GPS Disconnected From Battery"` |
| Interferenza sul segnale (Jamming) (jamming_sensor) | `attributes.alarm: "jamming"` | Interferenza segnale GPS | `"Possible Jamming Attempt Detected"` |

**Esempi Automazioni**:
```yaml
# Allarme singolo
trigger:
  - platform: state
    entity_id: sensor.mia_auto_alarms
    to: "Movement"

# Qualsiasi allarme contenente testo
trigger:
  - platform: state
    entity_id: sensor.mia_auto_alarms
condition:
  - condition: template
    value_template: "{{ 'Movement' in states('sensor.mia_auto_alarms') }}"
```

### Valori Sensore Avvisi {#valori-sensore-avvisi}

Il sensore Avvisi visualizza un avviso alla volta (priorità più alta):

| Valore | Priorità | Condizione |
|:-------|:--------:|:-----------|
| `"Configuration Received"` | 1 (Massima) | `attributes.result` presente, non in sleep mode |
| `"Approximate Position"` | 2 (Media) | Nessun satellite GPS ma RSSI > 0, non in sleep mode |
| `"Sleep Mode Active"` | 3 (Minima) | `attributes.io200` indica sleep mode |
| `None` | - | Nessun avviso |

**Esempio Automazione**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.mia_auto_warnings
    to: "Configuration Received"
```

### Sensori OBD-II

**Compatibilità Dispositivo**: I sensori OBD-II sono **disponibili solo** su dispositivi MOOX con interfaccia OBD-II. **Non compatibili** con dispositivi FMB920 e FMC920.

| Sensore | Descrizione | Unità |
|:--------|:-----------|:-----|
| **RPM** | Giri motore al minuto | - |
| **Livello Carburante** | Percentuale carburante | % |
| **Codici DTC** | Codici errore diagnostici (separati da virgola) | testo |
| **Conteggio DTC** | Numero codici errore | - |

Questi sensori sono **nascosti di default** e mostrano dati solo quando collegati a un dispositivo OBD-II compatibile.

---

## 🎯 Automazioni

### Automazioni Device Tracker

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

### Automazioni Basate su Eventi

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

**Struttura Payload Evento**:
Il payload dell'evento contiene:
- `device_moox_id` (int): ID dispositivo da MOOX Track
- `device_name` (str): Nome dispositivo
- `event` (str): Tipo evento in snake_case (es. `geofence_enter`)
- `type` (str): Tipo evento originale dall'API (es. `geofenceEnter`)
- `serverTime` (str): Timestamp evento dal server
- `attributes` (dict): Attributi aggiuntivi dell'evento

**Tipi di Evento Disponibili**:
- `device_moving`, `device_stopped`
- `geofence_enter`, `geofence_exit`
- `ignition_on`, `ignition_off`
- `device_online`, `device_offline`, `device_inactive`
- `device_overspeed`, `alarm`, `maintenance`
- `text_message`, `command_result`
- `device_fuel_drop`, `device_fuel_increase`
- `driver_changed`, `device_unknown`
- `queued_command_sent`, `media`

### Automazioni Basate su Sensori

```yaml
# Avviso batteria scarica
automation:
  - alias: "Avviso Batteria Scarica"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mia_auto_battery_level
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "🔋 Batteria Scarica"
          message: "Batteria auto al {{ states('sensor.mia_auto_battery_level') }}%"

# Monitoraggio velocità
automation:
  - alias: "Avviso Velocità Elevata"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mia_auto_speed_kmh
        above: 120
    action:
      - service: notify.mobile_app
        data:
          title: "⚡ Velocità Elevata"
          message: "Velocità auto: {{ states('sensor.mia_auto_speed_kmh') }} km/h"

# Rilevamento allarme (consigliato)
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

### Esempi Template

```yaml
# Verifica se dispositivo si sta muovendo
value_template: "{{ is_state('binary_sensor.mia_auto_motion', 'on') }}"

# Ottieni geofence corrente
value_template: "{{ states('sensor.mia_auto_geofence') }}"

# Verifica allarme specifico
value_template: "{{ 'Towing' in states('sensor.mia_auto_alarms') }}"

# Calcola distanza da casa
value_template: >
  {{ distance(
    homeassistant.config.as_dict()['latitude'],
    homeassistant.config.as_dict()['longitude'],
    state_attr('device_tracker.mia_auto', 'latitude'),
    state_attr('device_tracker.mia_auto', 'longitude')
  ) | round(2) }}
```

---

## 🔧 Configurazione Avanzata

### Attributi Personalizzati

Aggiungi attributi personalizzati nelle opzioni integrazione. Specifica una lista di nomi di attributi da estrarre dagli attributi del dispositivo o della posizione. Questi appariranno come attributi extra sul device tracker.

**Nota**: Gli attributi personalizzati vengono estratti dal dizionario `attributes` del dispositivo o della posizione. Non puoi aggiungere attributi calcolati usando template - solo attributi esistenti dall'API possono essere inclusi.

**Esempio**: Per includere gli attributi `io200` e `io36`:
- Aggiungi `io200` e `io36` alla lista Attributi Personalizzati nelle opzioni integrazione
- Questi attributi appariranno quindi sull'entità device tracker

### Filtraggio Precisione

Configura `Precisione Massima` per filtrare letture GPS imprecise **solo in Home Assistant**:

- **0** (default): Disabilita filtro, accetta tutte le posizioni
- **50**: Filtra posizioni con precisione > 50 metri
- **100**: Filtra posizioni con precisione > 100 metri

**Importante**: Questo filtro influisce solo su ciò che Home Assistant registra. Non cambia alcun parametro del dispositivo.

Usa `Salta Filtro Precisione Per` per bypassare filtro per eventi critici (es. `["alarm"]`).

### Intervallo Aggiornamento

- **Minimo**: 30 secondi
- **Default**: Usato come intervallo polling di fallback

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

### Posizioni Imprecise

1. Controlla che il dispositivo GPS abbia visuale chiara del cielo
2. Verifica livello batteria dispositivo
3. Regola `Precisione Massima` nelle opzioni integrazione (influisce solo su Home Assistant)
4. Controlla conteggio satelliti (sensore `sat`)

### Eventi/Allarmi Non Appaiono

1. **Configura nell'app MOOX Track**: Eventi/allarmi devono essere abilitati nelle impostazioni dispositivo
2. Controlla compatibilità modello dispositivo
3. Verifica che il dispositivo stia trasmettendo dati evento/allarme
4. Controlla sensore diagnostico `event_raw` per codici evento grezzi

### Sensori OBD-II Non Visibili

1. **Compatibilità Dispositivo**: Disponibili solo su dispositivi MOOX con interfaccia OBD-II
2. **Non Compatibili**: FMB920 e FMC920 non supportano OBD-II
3. Sensori nascosti di default - abilita nel registro entità se dispositivo è compatibile

---

## 📊 Dettagli Tecnici

### Unique ID Entità

Formato: `{deviceId}_{dataSource}_{key}`

Esempi:
- `12345` (device tracker)
- `12345_position_latitude`
- `12345_position_attributes.event`
- `12345_device_status`

### State Classes

- **Measurement**: Velocità, altitudine, batteria, satelliti, tensione, contachilometri, RPM, livello carburante
- **Total Increasing**: Contachilometri
- **None**: Evento, allarmi, avvisi, geofence, RSSI, timestamp

### Device Classes

- **Distance**: Contachilometri
- **Speed**: Sensori velocità
- **Motion**: Binary sensor movimento
- **Power**: Binary sensor accensione
- **None**: La maggior parte degli altri sensori

### Comunicazione

- **Connessione**: Connessione diretta a `app.moox.it` con aggiornamenti in tempo reale
- **Fallback**: Polling HTTP (intervallo configurabile, minimo 30 secondi)
- **Protocollo**: Solo HTTPS, nessuna dipendenza esterna

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
