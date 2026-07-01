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
            .disabled(!app.isLive)

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
            Text("Update holt den neuesten Code (git pull) und startet den Dienst neu — braucht Internet (Client-Modus). Vor dem Stromtrennen immer herunterfahren (schützt die SD-Karte).")
        }
        .confirmationDialog("Backend aktualisieren?", isPresented: $confirmUpdate, titleVisibility: .visible) {
            Button("Aktualisieren") {
                app.fire { try await $0.update() }
                app.showToast("Update läuft — git pull + Neustart, in ~30-60 s wieder verbunden.")
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text("Holt den neuesten Stand von GitHub und startet das Backend neu. Die App verliert kurz die Verbindung. Nur im Client-Modus (Internet nötig).")
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
