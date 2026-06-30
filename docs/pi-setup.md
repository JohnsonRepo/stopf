# Raspberry Pi Zero 2 W — Setup

Schritt-für-Schritt vom leeren Pi bis zum laufenden Backend, das die iOS-App
und der Nano finden. Ziel: Der Pi ist als `stopf.local:8000` erreichbar und
startet das Backend automatisch beim Booten.

```
iPhone  ──WLAN──►  Pi Zero 2 W (stopf.local:8000)  ──USB──►  Arduino Nano
```

> Für den Betrieb **ohne Heim-Router** (Pi als eigener Access Point) siehe
> [pi-network.md](pi-network.md).

---

## 1. SD-Karte flashen (am Mac)

1. **Raspberry Pi Imager** installieren: <https://www.raspberrypi.com/software/>
2. Imager öffnen:
   - **Gerät:** Raspberry Pi Zero 2 W
   - **OS:** *Raspberry Pi OS Lite (64-bit)* — kein Desktop nötig, spart RAM
   - **Speicher:** deine SD-Karte
3. **⚙️ / „Weiter" → Einstellungen bearbeiten** (der wichtige Teil für headless):
   - **Hostname:** `stopf`  → damit wird der Pi automatisch `stopf.local`
   - **Benutzer:** `maschine` + Passwort (merken!)
   - **WLAN:** SSID + Passwort + Land (`DE`)
   - **SSH aktivieren** (Reiter „Dienste") → *Passwort-Authentifizierung*
4. Schreiben lassen, SD-Karte in den Pi, Strom dran.

> Erster Boot dauert 1–2 Min. Der Pi hängt sich ins WLAN und ist dann per SSH da.

---

## 2. Per SSH einloggen (am Mac)

```bash
ssh maschine@stopf.local
```

(Benutzernamen anpassen.) Beim ersten Mal Fingerprint mit `yes` bestätigen.

Falls `stopf.local` nicht auflöst → siehe [Troubleshooting](#troubleshooting).

---

## 3. Code auf den Pi bringen

**Variante A — git (wenn das Repo erreichbar ist):**
```bash
git clone https://github.com/JohnsonRepo/stopf.git ~/stopf
```

**Variante B — vom Mac kopieren (rsync):** auf dem **Mac** ausführen:
```bash
rsync -av --exclude '.venv' --exclude '.git' \
  "/Users/jonaskilian/Documents/Claude/Projects/stopf/stopfmaschine_starter/" \
  maschine@stopf.local:~/stopf/
```

Danach liegt das Backend unter `~/stopf/backend/pi`.

---

## 4. Setup-Skript ausführen (auf dem Pi)

```bash
cd ~/stopf/backend/pi
bash scripts/setup.sh
```

Das Skript erledigt automatisch:
- Systempakete (`python3-venv`, `avahi-daemon`)
- `dialout`-Gruppe (Serial-Zugriff ohne root)
- Serial-Port erkennen (CH340-Klon = meist `/dev/ttyUSB0`)
- venv + `pip install -r requirements.txt`
- Import-Test
- **systemd-Unit** mit deinem echten User/Pfad generieren + aktivieren
- **mDNS-Service** `_stopf._tcp` installieren

Am Ende steht eine Zusammenfassung. Wenn du neu zur `dialout`-Gruppe kamst:
```bash
sudo reboot
```

---

## 5. Nano anschließen

Nano per USB an den Pi (Micro-USB-Datenport, nicht nur PWR). Prüfen:

```bash
ls /dev/ttyUSB* /dev/ttyACM*      # sollte einen Port zeigen
journalctl -u stopfmaschine -f    # Log live; "Connected to Nano on ..." erwartet
```

Falls der Port von der Setup-Annahme abweicht, einmal anpassen:
```bash
sudo systemctl edit --full stopfmaschine   # Environment="STOPF_SERIAL_PORT=..." ändern
sudo systemctl restart stopfmaschine
```
> Das Backend macht zur Laufzeit ohnehin Auto-Detect über `ttyUSB`/`ttyACM`,
> der explizite Port ist nur die erste Wahl.

---

## 6. Verifizieren

**Auf dem Pi:**
```bash
curl http://localhost:8000/            # {"service":"stopfmaschine",...,"nano_connected":true}
curl http://localhost:8000/status      # geparster Maschinenstatus
```

**Am Mac (Browser):**
- `http://stopf.local:8000/docs` → interaktive API (Swagger)
- Dort `GET /params` testen → sollte die 18 EEPROM-Werte liefern

**Am iPhone:**
- App → Tab **Verbindung** → Pi sollte als *„Stopfmaschine on stopf"* erscheinen
- Antippen → verbindet → Sensor-Strip wird grün/live

---

## 7. Betrieb

| Aktion | Befehl |
|---|---|
| Status | `sudo systemctl status stopfmaschine` |
| Logs live | `journalctl -u stopfmaschine -f` |
| Neustart | `sudo systemctl restart stopfmaschine` |
| Stoppen | `sudo systemctl stop stopfmaschine` |
| Nach Code-Update | erneut `rsync`/`git pull`, dann `restart` |

Der Dienst startet automatisch beim Boot und nach Abstürzen (`Restart=on-failure`).

---

## Troubleshooting

**`stopf.local` löst nicht auf (Mac/iPhone finden den Pi nicht)**
- Pi und Gerät im **selben WLAN** (2,4 GHz — Pi Zero 2 W kann kein 5 GHz)?
- Per IP testen: am Pi `hostname -I`, dann `http://<IP>:8000/docs`
- avahi läuft? `systemctl status avahi-daemon`

**Backend startet nicht**
- `journalctl -u stopfmaschine -e` ansehen
- Häufig: venv-Pfad falsch (setup.sh erneut laufen lassen)

**Nano wird nicht gefunden (`nano_connected:false`)**
- `ls /dev/ttyUSB* /dev/ttyACM*` — Port da?
- `groups` muss `dialout` enthalten (sonst Reboot nach setup.sh)
- USB-Datenkabel, nicht nur Ladekabel?
- Anderer USB-Port am Pi (Zero 2 W: der mit „USB" beschriftete, nicht „PWR")

**iPhone findet Pi nicht via Bonjour**
- In der App manuell `stopf.local` + Port `8000` eintragen
- Local-Network-Permission beim ersten Start erlaubt?

**pip-Install ist langsam / bricht ab (Pi Zero 2 W hat wenig RAM)**
- piwheels liefert vorgebaute ARM-Wheels — normalerweise kein Kompilieren nötig
- Bei OOM: temporär Swap erhöhen (`sudo dphys-swapfile ...`) oder Pakete einzeln
