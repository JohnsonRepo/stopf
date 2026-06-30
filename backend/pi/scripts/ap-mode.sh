#!/usr/bin/env bash
#
# ap-mode.sh — Pi als WLAN-Access-Point (Netzunabhängigkeit).
#
# Der Pi spannt sein eigenes WLAN auf; das iPhone verbindet sich direkt,
# ganz ohne Heim-Router. App, Bonjour (stopf.local) und das Backend laufen
# unverändert weiter — NetworkManager macht DHCP + NAT automatisch
# (ipv4.method shared → Pi ist 10.42.0.1).
#
# Aufruf auf dem Pi:
#   bash scripts/ap-mode.sh [SSID] [PASSWORT]
# Default: SSID "Stopfmaschine", Passwort "stopfen2026"
#
# WICHTIG: Der Pi hat nur EIN WLAN-Radio. Im AP-Modus ist er NICHT mit dem
# Heim-WLAN verbunden (kein Internet/kein apt). Zurück mit wifi-mode.sh.
#
set -euo pipefail

AP_SSID="${1:-Stopfmaschine}"
AP_PSK="${2:-stopfen2026}"
CON="stopf-ap"
IFACE="wlan0"

if ! command -v nmcli >/dev/null 2>&1; then
    echo "FEHLER: NetworkManager (nmcli) nicht gefunden."
    echo "Dieses Skript setzt Raspberry Pi OS Bookworm (NetworkManager) voraus."
    echo "Prüfen: systemctl status NetworkManager"
    exit 1
fi

if [ "${#AP_PSK}" -lt 8 ]; then
    echo "FEHLER: WLAN-Passwort muss mindestens 8 Zeichen haben (WPA2)."
    exit 1
fi

echo "==> Lege Access-Point-Profil an: $CON (SSID: $AP_SSID)"

# Idempotent: altes Profil entfernen
nmcli connection delete "$CON" >/dev/null 2>&1 || true

# AP-Profil. 'shared' aktiviert NMs internen DHCP-Server + NAT.
nmcli connection add type wifi ifname "$IFACE" con-name "$CON" \
    autoconnect no ssid "$AP_SSID"
nmcli connection modify "$CON" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    ipv4.method shared \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "$AP_PSK"

echo ""
echo "============================================================"
echo " Access Point wird aktiviert"
echo "   SSID:     $AP_SSID"
echo "   Passwort: $AP_PSK"
echo "   Pi-IP:    http://10.42.0.1:8000"
echo "   mDNS:     http://stopf.local:8000  (sobald iPhone im AP)"
echo "------------------------------------------------------------"
echo " ! Deine SSH-Sitzung über das Heim-WLAN bricht jetzt ab —"
echo "   das ist normal. Verbinde dein Gerät mit dem WLAN"
echo "   \"$AP_SSID\" und nutze dann stopf.local bzw. 10.42.0.1."
echo "============================================================"

# Den eigentlichen Umschalt-Befehl von der SSH-Sitzung lösen (systemd-run),
# damit er den Abbruch der Verbindung übersteht und der AP sicher hochkommt.
sudo systemd-run --collect nmcli connection up "$CON"
