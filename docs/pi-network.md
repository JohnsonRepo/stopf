# Netzunabhängigkeit — Pi als WLAN-Access-Point

Damit die Maschine **ohne Heim-Router** steuerbar ist: Der Pi spannt sein eigenes
WLAN auf, das iPhone verbindet sich direkt. **App, Backend, Bonjour (`stopf.local`)
laufen unverändert** — es ändert sich nur das Netz darunter.

```
Zuhause:    iPhone ─► Heim-WLAN ─► Pi (stopf.local)        [Client-Modus]
Unterwegs:  iPhone ─► WLAN "Stopfmaschine" ─► Pi (10.42.0.1) [AP-Modus]
```

> Voraussetzung: Raspberry Pi OS **Bookworm** (nutzt NetworkManager). Prüfen mit
> `systemctl status NetworkManager`. Bei älterem OS mit `dhcpcd` siehe
> [Anhang](#anhang-älteres-os-ohne-networkmanager).

---

## Wichtig vorab: nur EIN WLAN-Radio

Der Pi Zero 2 W hat eine einzige Funkeinheit. Er ist **entweder** im Heim-WLAN
**oder** Access Point — nicht beides gleichzeitig. Im AP-Modus hat der Pi also
**kein Internet** (kein `apt`, kein `git pull`). Für Updates kurz zurück in den
Client-Modus.

---

## Umschalten

Beide Skripte liegen in `backend/pi/scripts/` und sind über `setup.sh` schon
auf dem Pi.

**In den AP-Modus (eigenes WLAN):**
```bash
cd ~/stopf/backend/pi
bash scripts/ap-mode.sh                       # SSID "Stopfmaschine", PW "stopfen2026"
bash scripts/ap-mode.sh MeinNetz GeheimesPW   # oder eigene Werte (PW >= 8 Zeichen)
```
Danach: iPhone-WLAN-Einstellungen → „Stopfmaschine" wählen → App öffnen.
Der Pi ist `http://10.42.0.1:8000` bzw. weiterhin `http://stopf.local:8000`.

**Zurück ins Heim-WLAN:**
```bash
cd ~/stopf/backend/pi
bash scripts/wifi-mode.sh
```

> **Die SSH-Sitzung bricht beim Umschalten ab** — das ist gewollt (das Radio
> wechselt das Netz). Die Skripte lösen den eigentlichen Wechsel per `systemd-run`
> von der Sitzung, der AP kommt also auch nach dem Abbruch sauber hoch. Danach
> einfach neu verbinden (im jeweils anderen Netz).

---

## Option A: AP immer an (einfachste Feld-Nutzung)

Wenn die Maschine fast immer unterwegs läuft, soll der AP beim Booten automatisch
starten. AP-Profil auf autoconnect setzen:
```bash
sudo nmcli connection modify stopf-ap connection.autoconnect yes
```
Dann ist der Pi nach jedem Einschalten direkt sein eigenes WLAN. Für Updates
zuhause `wifi-mode.sh` (schaltet AP ab, Heim-WLAN greift).

---

## Option B: Automatischer Fallback (Heim-WLAN wenn da, sonst AP)

Das Beste für „zuhause am Router, unterwegs autark" — NetworkManager bevorzugt
das Heim-WLAN und fällt nur auf den AP zurück, wenn keins erreichbar ist:

```bash
# Heim-WLAN hohe Priorität:
sudo nmcli connection modify "<HEIM-SSID>" connection.autoconnect-priority 10

# AP niedrige Priorität, aber autoconnect an:
sudo nmcli connection modify stopf-ap connection.autoconnect yes \
     connection.autoconnect-priority 1
```
Beim Boot verbindet sich der Pi mit dem Heim-WLAN, falls in Reichweite —
sonst aktiviert er den AP. Kein zusätzliches Dienst-/Dispatcher-Skript nötig.

> `<HEIM-SSID>` ist der Profilname; auflisten mit
> `nmcli -t -f NAME,TYPE connection show | grep wireless`.

---

## Verifizieren

1. AP aktivieren, am iPhone/Mac das WLAN „Stopfmaschine" beitreten
2. Browser: `http://10.42.0.1:8000/` → JSON mit `version` erscheint
3. `http://stopf.local:8000/docs` → Swagger (mDNS über AP funktioniert)
4. App → Tab Verbindung → Pi via Bonjour finden, oder `10.42.0.1` / Port `8000`
5. Zurückschalten: `wifi-mode.sh`, am Mac `ping stopf.local`

---

## Caveats

- **Kein Internet im AP-Modus** (Single-Radio) → Updates im Client-Modus.
- **SSH-Abbruch beim Umschalten** ist normal (siehe oben).
- **2,4 GHz only** — der Pi Zero 2 W kann kein 5 GHz; der AP ist 2,4-GHz-`bg`.
- **Stromversorgung:** AP-Betrieb zieht etwas mehr Strom — auf ein solides 5-V-Netzteil achten (Brownouts killen sonst WLAN).
- **Passwort ändern:** Default `stopfen2026` ist öffentlich (steht hier) — beim ersten echten Einsatz ein eigenes setzen.

---

## Anhang: älteres OS ohne NetworkManager

Falls `systemctl status NetworkManager` „not found" liefert (altes Pi OS mit
`dhcpcd`), bräuchte es den klassischen Weg mit `hostapd` + `dnsmasq` + statischer
`dhcpcd.conf`. Empfehlung: stattdessen auf Bookworm neu flashen — die
NetworkManager-Lösung oben ist deutlich wartungsärmer.
