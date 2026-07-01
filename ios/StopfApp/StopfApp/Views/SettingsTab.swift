//
//  SettingsTab.swift
//  Verbindungs-Konfiguration: Bonjour-Discovery + manuelle Eingabe + Test.
//

import SwiftUI

struct SettingsTab: View {
    @Environment(AppState.self) private var app

    @State private var hostField: String = ""
    @State private var portField: String = ""
    @State private var testing = false
    @State private var resolving: String?   // id des gerade aufgelösten Service
    @State private var confirmShutdown = false
    @State private var confirmReboot = false
    @State private var confirmUpdate = false
    @State private var confirmUpdate2 = false
    @State private var confirmFlash = false
    @State private var confirmFlash2 = false

    /// Update nur möglich, wenn verbunden UND der Pi Internet hat.
    private var canUpdate: Bool { app.isLive && (app.lastHealth?.internet ?? false) }

    private var systemFooter: String {
        canUpdate
        ? "Update holt den neuesten Code (git pull) und startet den Dienst neu. Vor dem Stromtrennen immer herunterfahren (schützt die SD-Karte)."
        : "Update ist nur möglich, wenn der Pi Internet hat (Client-Modus). Im AP-Modus deaktiviert."
    }

    var body: some View {
        NavigationStack {
            Form {
                connectionStatusSection
                discoverySection
                manualSection
                testSection
                systemSection
            }
            .navigationTitle("Verbindung")
            .onAppear {
                hostField = app.host
                portField = String(app.port)
                app.discovery.start()
                // Health (inkl. Internet-Status) frisch holen → Update-Button-Gating
                Task { await app.testConnection() }
            }
        }
    }

    // MARK: - Status

    private var connectionStatusSection: some View {
        Section("Status") {
            HStack {
                Circle()
                    .fill(app.isLive ? .green : .red)
                    .frame(width: 12, height: 12)
                VStack(alignment: .leading, spacing: 2) {
                    Text(app.isLive ? "Verbunden" : "Getrennt")
                        .font(.headline)
                    if let url = app.baseURL {
                        Text(url.absoluteString)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                Spacer()
                if app.isLive {
                    Text(app.status.state.displayName)
                        .font(.caption.weight(.medium))
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    // MARK: - Discovery

    private var discoverySection: some View {
        Section {
            if app.discovery.services.isEmpty {
                HStack {
                    if app.discovery.isBrowsing {
                        ProgressView()
                        Text("Suche im Netzwerk…")
                            .foregroundStyle(.secondary)
                    } else {
                        Text("Nichts gefunden")
                            .foregroundStyle(.secondary)
                    }
                }
            } else {
                ForEach(app.discovery.services) { svc in
                    Button {
                        Task { await connectTo(svc) }
                    } label: {
                        HStack {
                            Image(systemName: "server.rack")
                                .foregroundStyle(.blue)
                            Text(svc.name)
                            Spacer()
                            if resolving == svc.id {
                                ProgressView()
                            } else {
                                Image(systemName: "chevron.right")
                                    .font(.caption)
                                    .foregroundStyle(.tertiary)
                            }
                        }
                    }
                    .disabled(resolving != nil)
                }
            }
        } header: {
            HStack {
                Text("Gefundene Geräte")
                Spacer()
                Button {
                    app.discovery.stop()
                    app.discovery.start()
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
            }
        } footer: {
            Text("Sucht automatisch nach „_stopf._tcp“ im lokalen WLAN.")
        }
    }

    // MARK: - Manual entry

    private var manualSection: some View {
        Section("Manuell") {
            HStack {
                Text("Host")
                Spacer()
                TextField("stopf.local", text: $hostField)
                    .multilineTextAlignment(.trailing)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .keyboardType(.URL)
            }
            HStack {
                Text("Port")
                Spacer()
                TextField("8000", text: $portField)
                    .multilineTextAlignment(.trailing)
                    .keyboardType(.numberPad)
            }
            Button("Übernehmen") {
                applyManual()
            }
            .disabled(hostField.trimmingCharacters(in: .whitespaces).isEmpty)
        }
    }

    // MARK: - Test

    private var testSection: some View {
        Section {
            Button {
                Task {
                    testing = true
                    await app.testConnection()
                    testing = false
                }
            } label: {
                HStack {
                    Text("Verbindung testen")
                    Spacer()
                    if testing { ProgressView() }
                }
            }

            if let h = app.lastHealth {
                LabeledContent("Backend", value: "v\(h.version)")
                LabeledContent("Nano") {
                    Label(h.nanoConnected ? "verbunden" : "getrennt",
                          systemImage: h.nanoConnected ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .foregroundStyle(h.nanoConnected ? .green : .red)
                        .labelStyle(.titleAndIcon)
                }
                LabeledContent("Port", value: h.nanoPort)
                LabeledContent("Internet") {
                    Label(h.internet == true ? "verbunden" : "getrennt",
                          systemImage: h.internet == true ? "wifi" : "wifi.slash")
                        .foregroundStyle(h.internet == true ? .green : .secondary)
                        .labelStyle(.titleAndIcon)
                }
            }
            if let e = app.lastError {
                Label(e, systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red)
                    .font(.caption)
            }
        } footer: {
            Text("„Backend“ ist der Pi, „Nano“ die serielle Verbindung Pi → Arduino.")
        }
    }

    // MARK: - System (Power)

    private var systemSection: some View {
        Section {
            Button {
                confirmUpdate = true
            } label: {
                Label("Backend aktualisieren", systemImage: "arrow.down.circle")
            }
            .disabled(!canUpdate)

            Button {
                confirmFlash = true
            } label: {
                Label("Nano-Firmware flashen", systemImage: "cpu")
            }
            .disabled(!app.isReady)

            Button(role: .destructive) {
                confirmShutdown = true
            } label: {
                Label("Pi herunterfahren", systemImage: "power")
            }
            .disabled(!app.isLive)

            Button {
                confirmReboot = true
            } label: {
                Label("Pi neu starten", systemImage: "arrow.clockwise.circle")
            }
            .disabled(!app.isLive)
        } header: {
            Text("System")
        } footer: {
            Text(systemFooter)
        }
        // Schritt 1
        .confirmationDialog("Backend aktualisieren?", isPresented: $confirmUpdate, titleVisibility: .visible) {
            Button("Weiter …") {
                // kleiner Versatz, damit der zweite Dialog zuverlässig erscheint
                Task { @MainActor in
                    try? await Task.sleep(for: .milliseconds(300))
                    confirmUpdate2 = true
                }
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text("Holt den neuesten Stand von GitHub und startet das Backend neu. Die App verliert dabei kurz die Verbindung.")
        }
        // Schritt 2 (zweite Bestätigung)
        .confirmationDialog("Wirklich jetzt aktualisieren?", isPresented: $confirmUpdate2, titleVisibility: .visible) {
            Button("Jetzt aktualisieren", role: .destructive) {
                app.fire { try await $0.update() }
                app.showToast("Update läuft — git pull + Neustart, in ~30-60 s wieder verbunden.")
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text("Der laufende Betrieb wird unterbrochen. Nur fortfahren, wenn die Maschine nicht gerade stopft.")
        }
        // Nano-Flash Schritt 1
        .confirmationDialog("Nano-Firmware flashen?", isPresented: $confirmFlash, titleVisibility: .visible) {
            Button("Weiter …") {
                Task { @MainActor in
                    try? await Task.sleep(for: .milliseconds(300))
                    confirmFlash2 = true
                }
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text("Überschreibt die Firmware auf dem Nano mit dem Stand im Repo (firmware.hex). Vorher „Backend aktualisieren“, damit der neueste Hex da ist.")
        }
        // Nano-Flash Schritt 2 (zweite Bestätigung)
        .confirmationDialog("Wirklich jetzt flashen?", isPresented: $confirmFlash2, titleVisibility: .visible) {
            Button("Jetzt flashen", role: .destructive) {
                app.fire { try await $0.flashNano() }
                app.showToast("Nano wird geflasht — Backend pausiert ~20-40 s. Nicht den Strom trennen!")
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text("Der Flash-Vorgang darf NICHT unterbrochen werden (kein Stromtrennen). Nur im Ruhezustand ausführen.")
        }
        .confirmationDialog("Pi herunterfahren?", isPresented: $confirmShutdown, titleVisibility: .visible) {
            Button("Herunterfahren", role: .destructive) {
                app.fire { try await $0.shutdown() }
                app.showToast("Pi fährt herunter — warte bis die grüne LED aus ist, dann 12 V trennen.")
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text("Die Maschine wird gestoppt und der Pi heruntergefahren. Die App verliert danach die Verbindung.")
        }
        .confirmationDialog("Pi neu starten?", isPresented: $confirmReboot, titleVisibility: .visible) {
            Button("Neu starten", role: .destructive) {
                app.fire { try await $0.reboot() }
                app.showToast("Pi startet neu — in ~30 s wieder verbunden.")
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text("Die Maschine wird gestoppt und der Pi neu gestartet.")
        }
    }

    // MARK: - Actions

    private func applyManual() {
        let host = hostField.trimmingCharacters(in: .whitespaces)
        let port = Int(portField) ?? 8000
        app.applyDiscovered(host: host, port: port)
        Task {
            testing = true
            await app.testConnection()
            testing = false
        }
    }

    private func connectTo(_ svc: DiscoveredService) async {
        resolving = svc.id
        defer { resolving = nil }
        guard let url = await app.discovery.resolve(svc),
              let host = url.host() else {
            app.lastError = "Konnte \(svc.name) nicht auflösen."
            return
        }
        let port = url.port ?? 8000
        hostField = host
        portField = String(port)
        app.applyDiscovered(host: host, port: port)
        await app.testConnection()
    }
}

#Preview {
    SettingsTab()
        .environment(AppState())
}
