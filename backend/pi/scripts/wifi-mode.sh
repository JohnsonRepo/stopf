#!/usr/bin/env bash
#
# wifi-mode.sh — zurück vom AP-Modus ins Heim-WLAN (NetworkManager).
#
# Deaktiviert das AP-Profil; NetworkManager verbindet sich danach automatisch
# mit dem gespeicherten Heim-WLAN (autoconnect).
#
# Aufruf auf dem Pi (z.B. über die AP-Verbindung, ssh maschine@10.42.0.1):
#   bash scripts/wifi-mode.sh
#
set -euo pipefail

CON="stopf-ap"

if ! command -v nmcli >/dev/null 2>&1; then
    echo "FEHLER: NetworkManager (nmcli) nicht gefunden."
    exit 1
fi

echo "==> Schalte zurück in den Client-Modus (Heim-WLAN)."
echo " ! Eine SSH-Sitzung über das AP-WLAN (10.42.0.1) bricht jetzt ab —"
echo "   danach ist der Pi wieder als stopf.local im Heim-WLAN erreichbar."

# Gespeicherte WLAN-Profile außer dem AP zur Info auflisten
echo "   Gespeicherte WLAN-Profile:"
nmcli -t -f NAME,TYPE connection show | awk -F: '$2 ~ /wireless/ && $1 != "'"$CON"'" {print "     - " $1}'

# Detached, damit der Wechsel den SSH-Abbruch übersteht:
# AP runter, dann Gerät neu verbinden → NM nimmt das autoconnect-Heimprofil.
sudo systemd-run --collect bash -c "nmcli connection down '$CON' 2>/dev/null || true; nmcli device connect wlan0 || true"

echo "==> Umschaltung läuft. Neu verbinden mit: ssh maschine@stopf.local"
