//
//  Discovery.swift
//  Bonjour-Discovery des Pi-Backends (_stopf._tcp) via NWBrowser.
//

import Foundation
import Network
import Observation

struct DiscoveredService: Identifiable, Hashable {
    let id: String          // Bonjour-Name (eindeutig)
    let name: String        // Anzeigename
    let endpoint: NWEndpoint
    var host: String?       // aufgelöst (z.B. "stopf.local")
    var port: Int?
}

@Observable
@MainActor
final class Discovery {
    private(set) var services: [DiscoveredService] = []
    private(set) var isBrowsing = false

    private var browser: NWBrowser?

    func start() {
        guard browser == nil else { return }
        let params = NWParameters()
        params.includePeerToPeer = false
        let browser = NWBrowser(
            for: .bonjour(type: "_stopf._tcp", domain: nil),
            using: params
        )
        self.browser = browser

        browser.stateUpdateHandler = { state in
            Task { @MainActor [weak self] in
                guard let self else { return }
                switch state {
                case .ready, .setup:
                    self.isBrowsing = true
                case .failed, .cancelled:
                    self.isBrowsing = false
                default:
                    break
                }
            }
        }

        browser.browseResultsChangedHandler = { results, _ in
            Task { @MainActor [weak self] in
                self?.apply(results)
            }
        }

        browser.start(queue: .main)
        isBrowsing = true
    }

    func stop() {
        browser?.cancel()
        browser = nil
        isBrowsing = false
    }

    private func apply(_ results: Set<NWBrowser.Result>) {
        var found: [DiscoveredService] = []
        for result in results {
            guard case let .service(name, _, _, _) = result.endpoint else { continue }
            found.append(DiscoveredService(
                id: name,
                name: name,
                endpoint: result.endpoint,
                host: nil,
                port: nil
            ))
        }
        services = found.sorted { $0.name < $1.name }
    }

    /// Löst einen Bonjour-Endpoint zu host:port auf. Liefert eine baseURL.
    /// Bonjour-Namen sind nicht direkt URL-fähig — wir öffnen kurz eine
    /// NWConnection, lesen den aufgelösten Host und brechen wieder ab.
    func resolve(_ service: DiscoveredService) async -> URL? {
        let box = ResolveBox(endpoint: service.endpoint)
        return await withCheckedContinuation { continuation in
            box.begin(continuation: continuation)
        }
    }

    nonisolated static func hostString(_ host: NWEndpoint.Host) -> String {
        switch host {
        case .name(let n, _):
            return n
        case .ipv4(let addr):
            return "\(addr)".components(separatedBy: "%").first ?? "\(addr)"
        case .ipv6(let addr):
            // IPv6 in eckigen Klammern für URLs
            let raw = "\(addr)".components(separatedBy: "%").first ?? "\(addr)"
            return "[\(raw)]"
        @unknown default:
            return "\(host)"
        }
    }
}

/// Kapselt die einmalige Endpoint-Auflösung. `@unchecked Sendable`, weil der
/// interne Lock die Thread-Sicherheit garantiert — so dürfen die @Sendable
/// NWConnection-Handler darauf zugreifen, ohne dass non-Sendable Closures über
/// Queue-Grenzen wandern (Swift-6-konform).
//
// Das Projekt nutzt „main actor by default" (SWIFT_DEFAULT_ACTOR_ISOLATION =
// MainActor). Diese Box läuft aber bewusst NICHT auf dem Main-Actor — die
// NWConnection-Handler feuern auf einer Hintergrund-Queue. Daher sind alle
// Methoden explizit `nonisolated`; Thread-Sicherheit kommt vom NSLock.
//
private nonisolated final class ResolveBox: @unchecked Sendable {
    private let lock = NSLock()
    private var done = false
    private var continuation: CheckedContinuation<URL?, Never>?
    private let connection: NWConnection

    init(endpoint: NWEndpoint) {
        self.connection = NWConnection(to: endpoint, using: .tcp)
    }

    func begin(continuation: CheckedContinuation<URL?, Never>) {
        lock.lock()
        self.continuation = continuation
        lock.unlock()

        connection.stateUpdateHandler = { [self] state in
            switch state {
            case .ready:
                if let endpoint = connection.currentPath?.remoteEndpoint,
                   case let .hostPort(host, port) = endpoint {
                    let hostStr = Discovery.hostString(host)
                    finish(URL(string: "http://\(hostStr):\(port.rawValue)"))
                } else {
                    finish(nil)
                }
            case .failed, .cancelled:
                finish(nil)
            default:
                break
            }
        }
        connection.start(queue: .global())

        // Timeout-Sicherung
        DispatchQueue.global().asyncAfter(deadline: .now() + 4) { [self] in
            finish(nil)
        }
    }

    private func finish(_ url: URL?) {
        lock.lock()
        if done { lock.unlock(); return }
        done = true
        let c = continuation
        continuation = nil
        lock.unlock()
        connection.cancel()
        c?.resume(returning: url)
    }
}
