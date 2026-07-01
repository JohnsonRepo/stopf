#!/usr/bin/env bash
#
# flash-nano.sh — Nano-Firmware vom Pi aus flashen (Nano hängt am Pi-USB).
#
# Default flasht den ins Repo eingecheckten Hex (firmware/nano/firmware.hex),
# den `git pull` / der App-Update mitbringt. So kann auch die App flashen,
# ohne dass auf dem Pi eine Toolchain nötig ist.
#
# Aufruf:
#   bash scripts/flash-nano.sh                 # eingecheckter Repo-Hex
#   bash scripts/flash-nano.sh /pfad/x.hex     # anderer Hex
#   bash scripts/flash-nano.sh <hex> 115200    # anderer Baud (neuer Bootloader)
#
# Stoppt das Backend (gibt den Serial-Port frei), flasht mit avrdude und
# startet das Backend wieder. Wird von der App über den Dienst stopf-flash
# ausgelöst (eigene cgroup → überlebt den Backend-Stop).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_HEX="$(cd "$SCRIPT_DIR/../../.." && pwd)/firmware/nano/firmware.hex"

HEX="${1:-$REPO_HEX}"
BAUD="${2:-57600}"          # CH340-Klon mit altem Bootloader = 57600; neuere Nanos = 115200
SERVICE="stopfmaschine"

# avrdude vorhanden? (Interaktiv nachinstallieren; im Dienst ist es via setup.sh da.)
if ! command -v avrdude >/dev/null 2>&1; then
    echo "==> Installiere avrdude ..."
    sudo -n apt-get install -y -qq avrdude || {
        echo "FEHLER: avrdude fehlt und konnte nicht installiert werden."
        exit 1
    }
fi

# Hex vorhanden?
if [ ! -f "$HEX" ]; then
    echo "FEHLER: Hex-Datei nicht gefunden: $HEX"
    echo "Erwartet den eingecheckten Hex: $REPO_HEX"
    echo "Auf dem Mac bauen + committen: cd firmware/nano && pio run && cp .pio/build/nano/firmware.hex firmware.hex"
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
sudo -n systemctl stop "$SERVICE" 2>/dev/null || true
sleep 1

echo "==> Flashe Firmware ..."
set +e
avrdude -p atmega328p -c arduino -P "$PORT" -b "$BAUD" -D -U "flash:w:${HEX}:i"
RC=$?
set -e

echo "==> Starte $SERVICE wieder ..."
sudo -n systemctl start "$SERVICE"

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
