#!/usr/bin/env bash
#
# flash-nano.sh — Nano-Firmware vom Pi aus flashen (Nano hängt am Pi-USB).
#
# Workflow:
#   1) Auf dem MAC die Firmware bauen + .hex auf den Pi kopieren:
#        cd firmware/nano && pio run
#        scp .pio/build/nano/firmware.hex maschine@stopf.local:/tmp/firmware.hex
#   2) Auf dem PI dieses Skript ausführen:
#        cd ~/stopf/backend/pi && bash scripts/flash-nano.sh
#
# Das Skript stoppt das Backend (gibt den Serial-Port frei), flasht mit
# avrdude und startet das Backend wieder.
#
set -euo pipefail

HEX="${1:-/tmp/firmware.hex}"
BAUD="${2:-57600}"          # CH340-Klon mit altem Bootloader = 57600; neuere Nanos = 115200
SERVICE="stopfmaschine"

# avrdude vorhanden?
if ! command -v avrdude >/dev/null 2>&1; then
    echo "==> Installiere avrdude ..."
    sudo apt-get update -qq && sudo apt-get install -y -qq avrdude
fi

# Hex vorhanden?
if [ ! -f "$HEX" ]; then
    echo "FEHLER: Hex-Datei nicht gefunden: $HEX"
    echo ""
    echo "Erst auf dem Mac bauen und kopieren:"
    echo "  cd firmware/nano && pio run"
    echo "  scp .pio/build/nano/firmware.hex $(whoami)@$(hostname).local:/tmp/firmware.hex"
    exit 1
fi

# Port finden (CH340 = ttyUSB0, echter Nano = ttyACM0)
PORT=""
for p in /dev/ttyUSB* /dev/ttyACM*; do
    [ -e "$p" ] && PORT="$p" && break
done
if [ -z "$PORT" ]; then
    echo "FEHLER: kein /dev/ttyUSB* oder /dev/ttyACM* gefunden — Nano am Pi angesteckt?"
    exit 1
fi
echo "==> Port: $PORT   Baud: $BAUD   Hex: $HEX"

# WICHTIG: Backend muss den Port freigeben.
echo "==> Stoppe $SERVICE (gibt Serial-Port frei) ..."
sudo systemctl stop "$SERVICE" 2>/dev/null || true
sleep 1

echo "==> Flashe Firmware ..."
set +e
avrdude -p atmega328p -c arduino -P "$PORT" -b "$BAUD" -D -U "flash:w:${HEX}:i"
RC=$?
set -e

echo "==> Starte $SERVICE wieder ..."
sudo systemctl start "$SERVICE"

echo ""
if [ "$RC" -eq 0 ]; then
    echo "============================================================"
    echo " OK — Firmware geflasht."
    echo "   Prüfen:  curl http://localhost:8000/   (nano_connected:true?)"
    echo "============================================================"
else
    echo "============================================================"
    echo " FEHLER beim Flashen (rc=$RC)."
    echo " Bei 'stk500_getsync() not in sync' den anderen Baud probieren:"
    echo "   bash scripts/flash-nano.sh $HEX 115200"
    echo "============================================================"
fi
exit "$RC"
