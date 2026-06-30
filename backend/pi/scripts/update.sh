#!/usr/bin/env bash
#
# update.sh — Code aktualisieren und Dienst neu starten (auf dem Pi).
#
# Holt neuen Code (git pull, falls Git-Deployment), aktualisiert bei Bedarf
# die Python-Abhängigkeiten und startet das Backend neu.
#
# Aufruf auf dem Pi:
#   cd ~/stopf/backend/pi
#   bash scripts/update.sh
#
# Hinweis: Im AP-Modus hat der Pi kein Internet → git pull schlägt fehl.
# Für Updates kurz in den Client-Modus (wifi-mode.sh).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PI_DIR/../.." && pwd)"
VENV="$PI_DIR/.venv"
SERVICE="stopfmaschine"

echo "==> Update aus $REPO_ROOT"

# --- 1) Code holen --------------------------------------------------------
REQ_BEFORE=""
[ -f "$PI_DIR/requirements.txt" ] && REQ_BEFORE="$(sha1sum "$PI_DIR/requirements.txt" | awk '{print $1}')"

if git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "==> git pull ..."
    git -C "$REPO_ROOT" pull --ff-only
else
    echo " ! Kein Git-Repo erkannt — Code wurde per rsync deployed."
    echo "   Bitte zuerst vom Mac neu synchronisieren, dann dieses Skript erneut:"
    echo "     rsync -av --exclude '.venv' --exclude '.git' \\"
    echo "       \"<Mac-Projektpfad>/\" $(whoami)@\$(hostname).local:~/stopf/"
    echo "   (Fahre fort, falls du bereits frisch rsynct hast.)"
fi

# --- 2) Abhängigkeiten nur bei Änderung neu installieren ------------------
REQ_AFTER=""
[ -f "$PI_DIR/requirements.txt" ] && REQ_AFTER="$(sha1sum "$PI_DIR/requirements.txt" | awk '{print $1}')"

if [ ! -d "$VENV" ]; then
    echo " ! venv fehlt — bitte einmalig 'bash scripts/setup.sh' ausführen."
    exit 1
fi
if [ "$REQ_BEFORE" != "$REQ_AFTER" ]; then
    echo "==> requirements.txt geändert → Abhängigkeiten aktualisieren ..."
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -r "$PI_DIR/requirements.txt"
else
    echo "==> requirements.txt unverändert → kein pip-Install nötig."
fi

# --- 3) Import-Test (fängt kaputten Code ab, bevor neu gestartet wird) ----
echo "==> Import-Test ..."
( cd "$PI_DIR" && "$VENV/bin/python" -c "from app.main import app; print('    OK, API v' + app.version)" )

# --- 4) Dienst neu starten -----------------------------------------------
echo "==> Starte $SERVICE neu ..."
sudo systemctl restart "$SERVICE"
sleep 1
systemctl is-active --quiet "$SERVICE" && echo "    läuft." || {
    echo " ! Dienst nicht aktiv — Log:"; journalctl -u "$SERVICE" -n 15 --no-pager; exit 1;
}

echo ""
echo "Fertig. Test:  curl http://localhost:8000/"
