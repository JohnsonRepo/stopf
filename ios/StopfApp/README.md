# Stopfmaschine — iOS App

SwiftUI-App zur Fernsteuerung der Stopfmaschine über das Pi-Backend (FastAPI v0.3.0).

- **Min-Target:** iOS 17.0
- **Architektur:** SwiftUI + `@Observable` (Observation framework), async/await
- **Keine 3rd-Party-Dependencies** — nur Foundation, SwiftUI, Network

## Verbindung

Die App spricht ausschließlich mit dem Pi (nicht direkt mit dem Nano):

```
iPhone  ──HTTP/JSON + WebSocket──►  Pi (stopf.local:8000)  ──USB-Serial──►  Nano
```

Discovery via Bonjour (`_stopf._tcp`), mit manueller Host-Eingabe als Fallback.

---

## Xcode-Projekt anlegen (einmalig)

Ich kann die `.xcodeproj`-Datei nicht zuverlässig per Hand erzeugen — die legst du
in 6 Klicks selbst an, danach werden die mitgelieferten Swift-Files importiert.

1. **Xcode öffnen** → *File ▸ New ▸ Project…*
2. *iOS ▸ App* wählen → **Next**
3. Felder:
   - Product Name: `StopfApp`
   - Team: dein Apple-ID-"Personal Team" (kostenlos, sideload-tauglich)
   - Organization Identifier: z.B. `com.deinname`
   - Interface: **SwiftUI**
   - Language: **Swift**
   - Storage: **None** (kein Core Data)
4. Als Speicherort **diesen Ordner** (`ios/StopfApp/`) wählen.
   ⚠️ Xcode legt `StopfApp/StopfApp/` an — genau dort liegen schon die Sources.
   Wenn Xcode fragt ob es überschreiben soll: die von Xcode generierte
   `StopfApp.swift` und `ContentView.swift` **löschen** und stattdessen die
   mitgelieferten Files behalten (siehe unten).
5. Projekt-Settings ▸ *General* ▸ **Minimum Deployments = iOS 17.0**.
6. Die mitgelieferten Ordner `Models/`, `Services/`, `Views/` per Drag&Drop in den
   Xcode-Navigator ziehen (falls nicht automatisch erkannt). "Create groups" wählen.

### Auto-generierte Files ersetzen
Xcode erzeugt beim Anlegen `StopfAppApp.swift` (oder `StopfApp.swift`) und
`ContentView.swift`. Beide löschen — dieses Repo bringt `StopfApp.swift` (App-Entry)
und `Views/RootView.swift` mit.

---

## Info.plist-Einträge (Pflicht für Bonjour + HTTP im LAN)

Ab Xcode 13 gibt es keine sichtbare `Info.plist` mehr by default. Trage die Keys
unter *Target ▸ Info ▸ Custom iOS Target Properties* ein, oder füge die
mitgelieferte `Info-additions.plist`-Snippets manuell hinzu:

| Key | Typ | Wert |
|---|---|---|
| `NSLocalNetworkUsageDescription` | String | `Die App sucht die Stopfmaschine im lokalen Netzwerk.` |
| `NSBonjourServices` | Array | Item 0 (String): `_stopf._tcp` |
| `NSAppTransportSecurity` | Dict | siehe unten |

**ATS (HTTP statt HTTPS im lokalen Netz erlauben):**
```
NSAppTransportSecurity (Dictionary)
└─ NSAllowsLocalNetworking (Boolean) = YES
```
`NSAllowsLocalNetworking` erlaubt Klartext-HTTP nur zu `.local`-Hostnamen und
privaten IP-Bereichen — genau unser Fall. Kein generelles
`NSAllowsArbitraryLoads` nötig.

---

## Build & Run

1. iPhone per USB anstecken (oder Simulator — Bonjour funktioniert im Sim nur
   eingeschränkt, manuelle Eingabe `Mac-IP:8000` nutzen wenn das Backend auf dem
   Mac läuft).
2. In Xcode oben das Zielgerät wählen → **⌘R**.
3. Beim ersten Start: iOS fragt nach *Lokales Netzwerk*-Berechtigung → **Erlauben**.
4. Settings-Tab → "Suchen" → Pi sollte als `Stopfmaschine on …` auftauchen.

---

## Projektstruktur

```
StopfApp/
├── StopfApp.swift            App-Entry (@main)
├── Models/
│   ├── MachineStatus.swift   Status-Snapshot vom Nano
│   └── Params.swift          18 EEPROM-Parameter + UI-Metadaten
├── Services/
│   ├── AppState.swift        zentrale @Observable-Config + Clients
│   ├── APIClient.swift       REST (async/await)
│   ├── StatusStream.swift    WebSocket + Auto-Reconnect
│   └── Discovery.swift       Bonjour NWBrowser
└── Views/
    ├── RootView.swift        TabView + Notaus-Overlay (folgt in 3b)
    └── SettingsTab.swift     Verbindung/Discovery
```

Die Tabs Auto / Manual / Parameter folgen in den nächsten Phasen (3c–3e).
