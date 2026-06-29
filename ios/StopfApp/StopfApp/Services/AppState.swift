//
//  AppState.swift
//  Zentrale, beobachtbare App-Konfiguration + Service-Instanzen.
//
//  Hält die Verbindungs-Basis-URL (persistiert via UserDefaults), den
//  APIClient, den StatusStream und die Discovery. Views greifen über
//  @Environment(AppState.self) darauf zu.
//

import Foundation
import Observation
#if canImport(UIKit)
import UIKit
#endif

@Observable
@MainActor
final class AppState {
    /// Persistierter Host (z.B. "stopf.local" oder "192.168.1.42").
    var host: String {
        didSet { UserDefaults.standard.set(host, forKey: "stopf.host"); rewire() }
    }
    /// Persistierter Port.
    var port: Int {
        didSet { UserDefaults.standard.set(port, forKey: "stopf.port"); rewire() }
    }

    let statusStream = StatusStream()
    let discovery = Discovery()

    /// Letztes Ergebnis eines manuellen Verbindungstests.
    var lastHealth: HealthInfo?
    var lastError: String?

    init() {
        let savedHost = UserDefaults.standard.string(forKey: "stopf.host") ?? "stopf.local"
        let savedPort = UserDefaults.standard.integer(forKey: "stopf.port")
        self.host = savedHost
        self.port = savedPort == 0 ? 8000 : savedPort
    }

    /// Basis-URL aus host:port. Nil wenn host leer.
    var baseURL: URL? {
        guard !host.isEmpty else { return nil }
        return URL(string: "http://\(host):\(port)")
    }

    /// Frischer APIClient mit aktueller baseURL (Struct → günstig).
    var api: APIClient { APIClient(baseURL: baseURL) }

    /// Live-Status-Snapshot (Convenience).
    var status: MachineStatus { statusStream.status }
    var isLive: Bool { statusStream.live }

    /// True wenn die Maschine für Manual-/Sequenz-Befehle bereit ist.
    var isReady: Bool { isLive && status.state == .idle }

    /// Kurzlebige Fehlermeldung für Toast-Anzeige.
    var toast: String?
    private var toastClearTask: Task<Void, Never>?

    /// Feuert einen API-Befehl „fire-and-forget", sammelt Fehler als Toast.
    /// Views rufen z.B. `app.fire { try await $0.press(.fwd) }`.
    func fire(_ action: @escaping (APIClient) async throws -> CommandResponse) {
        let client = api
        Task { @MainActor in
            do {
                let resp = try await action(client)
                if !resp.ok { showToast(resp.reply) }
            } catch {
                showToast(error.localizedDescription)
            }
        }
    }

    /// Notaus: sofort stoppen + Haptik. Funktioniert immer (auch wenn nicht ready).
    func emergencyStop() {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
        #endif
        fire { try await $0.stop() }
    }

    func showToast(_ message: String) {
        toast = message
        toastClearTask?.cancel()
        toastClearTask = Task { @MainActor in
            try? await Task.sleep(for: .seconds(4))
            if !Task.isCancelled { toast = nil }
        }
    }

    /// Startet den Status-Stream (idempotent). Beim App-Start + nach Host-Wechsel.
    func connect() {
        guard let baseURL else { return }
        statusStream.start(baseURL: baseURL)
    }

    func disconnect() {
        statusStream.stop()
    }

    /// Manueller Verbindungstest: GET / auswerten.
    func testConnection() async {
        lastError = nil
        lastHealth = nil
        do {
            lastHealth = try await api.health()
        } catch {
            lastError = error.localizedDescription
        }
    }

    /// Übernimmt einen aufgelösten Bonjour-Host als aktive Verbindung.
    func applyDiscovered(host: String, port: Int) {
        self.host = host
        self.port = port
        // rewire() läuft via didSet
    }

    /// Nach Host/Port-Änderung: Stream neu verbinden.
    private func rewire() {
        guard let baseURL else { return }
        statusStream.start(baseURL: baseURL)
    }
}
