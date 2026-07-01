#!/usr/bin/env bash
#
# setup.sh — Bootstrap des Stopfmaschine-Backends auf dem Raspberry Pi.
#
# Idempotent: kann gefahrlos mehrfach laufen. Erkennt User, Repo-Pfad und
# Serial-Port automatisch und generiert daraus die systemd-Unit.
#
# Aufruf auf dem Pi:
#   cd ~/stopf/backend/pi
#   bash scripts/setup.sh
#
set -euo pipefail

# --- Pfade / User ermitteln ---------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../backend/pi/scripts
PI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"                        # .../backend/pi
RUN_USER="${SUDO_USER:-$USER}"
VENV="$PI_DIR/.venv"

echo "==> Stopfmaschine Backend-Setup"
echo "    User:      $RUN_USER"
echo "    Backend:   $PI_DIR"
echo "    venv:      $VENV"

# --- 1) Systempakete ----------------------------------------------------------
echo "==> Systempakete (python3-venv, avahi-daemon, avrdude) ..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip avahi-daemon avrdude

# --- 2) Serielle Rechte -------------------------------------------------------
# Damit das Backend ohne root /dev/ttyUSB0 bzw. /dev/ttyACM0 öffnen darf.
if ! id -nG "$RUN_USER" | grep -qw dialout; then
    echo "==> Füge $RUN_USER zur Gruppe 'dialout' hinzu (Logout nötig zum Greifen)"
    sudo usermod -aG dialout "$RUN_USER"
    NEED_RELOGIN=1
else
    echo "==> $RUN_USER ist bereits in 'dialout'"
fi

# --- 3) Serial-Port erkennen --------------------------------------------------
# CH340-Klone melden sich meist als ttyUSB0, echte Nanos als ttyACM0.
SERIAL_PORT="/dev/ttyACM0"
if ls /dev/ttyUSB* >/dev/null 2>&1; then
    SERIAL_PORT="$(ls /dev/ttyUSB* | head -n1)"
elif ls /dev/ttyACM* >/dev/null 2>&1; then
    SERIAL_PORT="$(ls /dev/ttyACM* | head -n1)"
else
    echo "    ! Kein ttyUSB/ttyACM gefunden — Nano angesteckt? Nutze Default $SERIAL_PORT"
    echo "      (Das Backend macht zur Laufzeit ohnehin Auto-Detect.)"
fi
echo "==> Serial-Port: $SERIAL_PORT"

# --- 4) Virtuelle Umgebung + Abhängigkeiten -----------------------------------
if [ ! -d "$VENV" ]; then
    echo "==> Erstelle venv ..."
    python3 -m venv "$VENV"
fi
echo "==> Installiere Python-Abhängigkeiten (piwheels liefert ARM-Wheels) ..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$PI_DIR/requirements.txt"

# --- 5) Schneller Import-Test -------------------------------------------------
echo "==> Teste Import ..."
( cd "$PI_DIR" && "$VENV/bin/python" -c "from app.main import app; print('    OK, API v' + app.version)" )

# --- 6) systemd-Unit generieren ----------------------------------------------
echo "==> Schreibe systemd-Unit /etc/systemd/system/stopfmaschine.service ..."
sudo tee /etc/systemd/system/stopfmaschine.service >/dev/null <<UNIT
[Unit]
Description=Stopfmaschine FastAPI Backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$PI_DIR
Environment="STOPF_SERIAL_PORT=$SERIAL_PORT"
ExecStart=$VENV/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

# Oneshot-Dienst zum Nano-Flashen (von der App ausgelöst). Läuft in EIGENER
# cgroup → das Stoppen von stopfmaschine (durch flash-nano.sh) killt avrdude
# nicht. Kein enable/start — wird per `systemctl start` on-demand getriggert.
echo "==> Schreibe systemd-Unit /etc/systemd/system/stopf-flash.service ..."
sudo tee /etc/systemd/system/stopf-flash.service >/dev/null <<UNIT
[Unit]
Description=Stopfmaschine Nano-Firmware flashen (oneshot)

[Service]
Type=oneshot
User=$RUN_USER
WorkingDirectory=$PI_DIR
ExecStart=/bin/bash $SCRIPT_DIR/flash-nano.sh
UNIT

sudo systemctl daemon-reload
sudo systemctl enable stopfmaschine >/dev/null 2>&1 || true
sudo systemctl restart stopfmaschine
echo "==> Dienst gestartet."

# --- 7) sudo-Regeln für App-gesteuerte System-Aktionen ------------------------
# Der Backend-User darf NUR diese eng begrenzten Kommandos ohne Passwort:
#   - poweroff/reboot                    → Herunterfahren/Neustart aus der App
#   - systemctl restart/stop/start stopfmaschine → Update-Neustart + Flash
#   - systemctl start --no-block stopf-flash.service → Nano-Flash aus der App
# Sonst nichts.
echo "==> Richte sudo-Regeln für Shutdown/Reboot/Update/Flash ein ..."
POWEROFF_BIN="$(command -v poweroff || echo /usr/sbin/poweroff)"
REBOOT_BIN="$(command -v reboot || echo /usr/sbin/reboot)"
SYSTEMCTL_BIN="$(command -v systemctl || echo /usr/bin/systemctl)"
SUDOERS_TMP="$(mktemp)"
cat > "$SUDOERS_TMP" <<SUDO
$RUN_USER ALL=(root) NOPASSWD: $POWEROFF_BIN, $REBOOT_BIN, $SYSTEMCTL_BIN restart stopfmaschine, $SYSTEMCTL_BIN stop stopfmaschine, $SYSTEMCTL_BIN start stopfmaschine, $SYSTEMCTL_BIN start --no-block stopf-flash.service
SUDO
# Erst validieren, dann erst installieren (kaputte sudoers = Aussperrung!)
if sudo visudo -cf "$SUDOERS_TMP" >/dev/null 2>&1; then
    sudo cp "$SUDOERS_TMP" /etc/sudoers.d/stopf-power
    sudo chmod 0440 /etc/sudoers.d/stopf-power
    echo "    OK: App darf poweroff/reboot + Update + Nano-Flash."
else
    echo "    ! sudoers-Validierung fehlgeschlagen — übersprungen (App-System-Aktionen deaktiviert)."
fi
rm -f "$SUDOERS_TMP"

# --- 8) avahi / mDNS ----------------------------------------------------------
echo "==> Installiere mDNS-Service (_stopf._tcp) ..."
sudo cp "$SCRIPT_DIR/avahi-stopf.service" /etc/avahi/services/stopf.service
sudo systemctl reload avahi-daemon || sudo systemctl restart avahi-daemon

# --- 9) WLAN-Energiesparmodus abschalten --------------------------------------
# Der Pi Zero 2 W wird sonst per WLAN-Powersave zeitweise unansprechbar
# ("Verbindung klappt erst nach mehreren Versuchen"). Auf einem netzgespeisten
# Gerät bringt Powersave nichts — dauerhaft aus.
if [ -d /etc/NetworkManager ]; then
    echo "==> Schalte WLAN-Energiesparmodus ab (NetworkManager) ..."
    sudo tee /etc/NetworkManager/conf.d/wifi-powersave-off.conf >/dev/null <<'PSAVE'
[connection]
wifi.powersave = 2
PSAVE
    sudo systemctl restart NetworkManager || true
else
    # Fallback ohne NetworkManager
    sudo iwconfig wlan0 power off 2>/dev/null || true
fi

# --- Fertig -------------------------------------------------------------------
HOSTNAME_LOCAL="$(hostname).local"
echo ""
echo "============================================================"
echo " Setup fertig."
echo "   Status:   sudo systemctl status stopfmaschine"
echo "   Logs:     journalctl -u stopfmaschine -f"
echo "   Test:     curl http://localhost:8000/"
echo "   Vom Mac:  http://$HOSTNAME_LOCAL:8000/docs"
echo "============================================================"
if [ "${NEED_RELOGIN:-0}" = "1" ]; then
    echo ""
    echo " ! WICHTIG: Du wurdest neu zur Gruppe 'dialout' hinzugefügt."
    echo "   Der Dienst läuft als systemd-Service und greift die Gruppe"
    echo "   beim Start — ein Reboot stellt sicher, dass alles passt:"
    echo "       sudo reboot"
fi
