//
//  StatusStream.swift
//  WebSocket-Client für /ws/status mit Auto-Reconnect.
//
//  Pusht ~5 Hz MachineStatus. Bei Verbindungsabbruch wird mit Backoff
//  neu verbunden. Läuft solange start(url:) aktiv ist; stop() beendet sauber.
//

import Foundation
import Observation

@Observable
@MainActor
final class StatusStream {
    /// Letzter empfangener Status. Solange nichts kam: disconnected.
    private(set) var status: MachineStatus = .disconnected
    /// True sobald mindestens ein Frame über die aktuelle Verbindung kam.
    private(set) var live: Bool = false

    private var task: URLSessionWebSocketTask?
    private var session: URLSession?
    private var currentURL: URL?
    private var reconnectAttempt = 0
    private var running = false
    private var receiveLoop: Task<Void, Never>?

    /// Startet (oder wechselt) den Stream auf die gegebene Basis-URL (http://host:port).
    func start(baseURL: URL) {
        let wsURL = Self.websocketURL(from: baseURL)
        // Gleiche URL + läuft schon → nichts tun.
        if running, currentURL == wsURL { return }
        stop()
        currentURL = wsURL
        running = true
        reconnectAttempt = 0
        connect()
    }

    func stop() {
        running = false
        receiveLoop?.cancel()
        receiveLoop = nil
        task?.cancel(with: .goingAway, reason: nil)
        task = nil
        session?.invalidateAndCancel()
        session = nil
        live = false
    }

    // MARK: - Internal

    private func connect() {
        guard running, let url = currentURL else { return }
        let cfg = URLSessionConfiguration.default
        cfg.timeoutIntervalForRequest = 10
        let session = URLSession(configuration: cfg)
        self.session = session
        let task = session.webSocketTask(with: url)
        self.task = task
        task.resume()
        live = false
        startReceiveLoop()
    }

    private func startReceiveLoop() {
        receiveLoop?.cancel()
        receiveLoop = Task { @MainActor [weak self] in
            while true {
                guard let self, self.running, let task = self.task else { break }
                do {
                    let message = try await task.receive()
                    self.handle(message)
                } catch {
                    // Verbindung weg → Backoff + reconnect
                    self.scheduleReconnect()
                    break
                }
            }
        }
    }

    private func handle(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            decodeAndPublish(Data(text.utf8))
        case .data(let data):
            decodeAndPublish(data)
        @unknown default:
            break
        }
    }

    private func decodeAndPublish(_ data: Data) {
        // Ping-Antwort {"_kind":"pong"} ignorieren.
        if let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           obj["_kind"] as? String == "pong" {
            return
        }
        guard let s = try? JSONDecoder().decode(MachineStatus.self, from: data) else { return }
        status = s
        live = true
        reconnectAttempt = 0
    }

    private func scheduleReconnect() {
        guard running else { return }
        live = false
        task = nil
        session?.invalidateAndCancel()
        session = nil
        reconnectAttempt += 1
        // Backoff: 0.5s, 1s, 2s, … max 5s
        let delay = min(0.5 * pow(2.0, Double(reconnectAttempt - 1)), 5.0)
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(delay))
            guard let self, self.running else { return }
            self.connect()
        }
    }

    private static func websocketURL(from baseURL: URL) -> URL {
        var comps = URLComponents(url: baseURL, resolvingAgainstBaseURL: false)!
        comps.scheme = (comps.scheme == "https") ? "wss" : "ws"
        comps.path = "/ws/status"
        return comps.url!
    }
}
