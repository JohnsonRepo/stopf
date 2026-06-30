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

## 8. Sauberes Herunterfahren (wichtig!)

**Nie einfach den Strom (12 V) ziehen, während der Pi läuft** — ein hartes
Abschalten während eines SD-Schreibvorgangs kann das Dateisystem beschädigen
(dann bootet der Pi nicht mehr und muss neu geflasht werden).

Stattdessen den Pi vorher **sauber herunterfahren**:

- **In der App:** Tab *Verbindung* → *System* → **Pi herunterfahren** → warten bis
  die grüne LED aus ist → dann 12 V trennen. (`setup.sh` richtet die nötige
  `sudo`-Regel automatisch ein — nur `poweroff`/`reboot`, sonst nichts.)
- **Per SSH:** `sudo poweroff`, dann LED-Aus abwarten, dann Strom trennen.

### Kugelsicher: Read-only-Dateisystem (Overlay FS)

Für ein Gerät ohne echten Aus-Schalter ist das die robusteste Lösung — danach
kann **kein** Stromziehen mehr die Karte beschädigen:

```bash
sudo raspi-config        # → Performance Options → Overlay File System → Enable
sudo reboot
```

Das Root-Dateisystem liegt dann schreibgeschützt im RAM. **Nachteil:** Änderungen
(auch `update.sh`) sind erst nach Deaktivieren wieder dauerhaft:

```bash
sudo raspi-config        # Overlay FS → Disable
sudo reboot
# ... update.sh / Änderungen ...
sudo raspi-config        # Overlay FS → Enable
sudo reboot
```

Empfehlung: Erst alles fertig einrichten und testen, dann Overlay FS aktivieren.

---

## 9. Nano-Firmware aktualisieren (über den Pi)

Der Nano bleibt am Pi-USB — du musst ihn nicht abstecken. Die Firmware wird auf
dem **Mac** gebaut (dort läuft PlatformIO), das fertige `.hex` per `scp` auf den
Pi kopiert, und der Pi flasht mit `avrdude`.

**Auf dem Mac:**
```bash
cd "<Projektpfad>/firmware/nano"
pio run                                    # baut .pio/build/nano/firmware.hex
scp .pio/build/nano/firmware.hex maschine@stopf.local:/tmp/firmware.hex
```

**Auf dem Pi:**
```bash
cd ~/stopf/backend/pi
bash scripts/flash-nano.sh                 # stoppt Backend, flasht, startet Backend
```

Das Skript gibt den Serial-Port frei (Backend stoppen ist sonst der häufigste
Fehler), erkennt den Port automatisch und nutzt Baud **57600** (CH340-Klon mit
altem Bootloader). Bei `not in sync` mit `115200` erneut:
`bash scripts/flash-nano.sh /tmp/firmware.hex 115200`.

> Alternativ alles in einem vom Mac aus:
> ```bash
> ssh maschine@stopf.local "cd ~/stopf/backend/pi && bash scripts/flash-nano.sh"
> ```
> (vorher das `.hex` wie oben per scp kopieren)

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

**Pi bootet gar nicht mehr / nicht im Netz (grüne LED flackert nicht)**
- Meist Folge von **hartem Stromabschalten** → SD-Karte korrupt.
- Per Mini-HDMI an Monitor prüfen (Dateisystem-Fehler sichtbar?).
- Lösung: SD **neu flashen** (Abschnitt 1), dann `git clone` + `setup.sh` —
  dank GitHub in ~15 Min wieder einsatzbereit.
- **Danach unbedingt** sauberes Herunterfahren nutzen (Abschnitt 8), sonst
  passiert es wieder.
