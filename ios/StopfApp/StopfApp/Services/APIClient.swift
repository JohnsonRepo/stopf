//
//  APIClient.swift
//  REST-Client (async/await) für das Pi-Backend v0.3.0.
//

import Foundation

struct CommandResponse: Codable {
    let sent: String
    let reply: String
    let ok: Bool
}

enum APIError: LocalizedError {
    case noBaseURL
    case http(Int)
    case transport(String)
    case decoding(String)

    var errorDescription: String? {
        switch self {
        case .noBaseURL:       return "Keine Verbindung konfiguriert."
        case .http(let code):  return "HTTP-Fehler \(code)."
        case .transport(let m): return "Netzwerkfehler: \(m)"
        case .decoding(let m): return "Antwort nicht lesbar: \(m)"
        }
    }
}

/// Stateless bzgl. Verbindung — baseURL wird pro Call übergeben (kommt aus AppState),
/// damit ein Host-Wechsel sofort greift.
struct APIClient {
    var baseURL: URL?

    private var session: URLSession {
        let cfg = URLSessionConfiguration.default
        cfg.timeoutIntervalForRequest = 5
        cfg.waitsForConnectivity = false
        return URLSession(configuration: cfg)
    }

    // MARK: - Generic request

    private func request<T: Decodable>(
        _ path: String,
        method: String = "GET",
        query: [String: String] = [:],
        body: Encodable? = nil,
        as type: T.Type
    ) async throws -> T {
        guard let baseURL else { throw APIError.noBaseURL }
        var comps = URLComponents(url: baseURL.appendingPathComponent(path),
                                  resolvingAgainstBaseURL: false)!
        if !query.isEmpty {
            comps.queryItems = query.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        var req = URLRequest(url: comps.url!)
        req.httpMethod = method
        if let body {
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = try JSONEncoder().encode(AnyEncodable(body))
        }

        do {
            let (data, resp) = try await session.data(for: req)
            guard let http = resp as? HTTPURLResponse else {
                throw APIError.transport("keine HTTP-Antwort")
            }
            guard (200..<300).contains(http.statusCode) else {
                throw APIError.http(http.statusCode)
            }
            do {
                return try JSONDecoder().decode(T.self, from: data)
            } catch {
                throw APIError.decoding(error.localizedDescription)
            }
        } catch let e as APIError {
            throw e
        } catch {
            throw APIError.transport(error.localizedDescription)
        }
    }

    @discardableResult
    private func command(_ path: String, method: String = "POST",
                         query: [String: String] = [:],
                         body: Encodable? = nil) async throws -> CommandResponse {
        try await request(path, method: method, query: query, body: body, as: CommandResponse.self)
    }

    // MARK: - Health / Status / Params

    func health() async throws -> HealthInfo {
        try await request("/", as: HealthInfo.self)
    }

    func status() async throws -> MachineStatus {
        try await request("/status", as: MachineStatus.self)
    }

    func params() async throws -> [String: Int] {
        try await request("/params", as: [String: Int].self)
    }

    @discardableResult
    func setParam(_ key: String, _ value: Int) async throws -> CommandResponse {
        try await command("/params/\(key)", method: "PUT", query: ["value": String(value)])
    }

    @discardableResult
    func setParams(_ values: [String: Int]) async throws -> CommandResponse {
        try await command("/params", method: "PUT", body: values)
    }

    // MARK: - Sequence

    @discardableResult func home()  async throws -> CommandResponse { try await command("/sequence/home") }
    @discardableResult func stuff() async throws -> CommandResponse { try await command("/sequence/stuff") }
    @discardableResult func stop()  async throws -> CommandResponse { try await command("/sequence/stop") }
    @discardableResult func step(_ n: Int) async throws -> CommandResponse {
        try await command("/sequence/step", body: ["n": n])
    }

    // MARK: - Manual

    @discardableResult func stepper(_ steps: Int) async throws -> CommandResponse {
        try await command("/manual/stepper", body: ["steps": steps])
    }
    @discardableResult func press(_ dir: MotorDirection) async throws -> CommandResponse {
        try await command("/manual/press", body: ["direction": dir.rawValue])
    }
    @discardableResult func pusher(_ dir: MotorDirection) async throws -> CommandResponse {
        try await command("/manual/pusher", body: ["direction": dir.rawValue])
    }
    @discardableResult func servo(_ angle: Int) async throws -> CommandResponse {
        try await command("/manual/servo", body: ["angle": angle])
    }
    @discardableResult func solenoid(_ which: Int, action: String, ms: Int? = nil) async throws -> CommandResponse {
        try await command("/manual/solenoid/\(which)", body: ActionBody(action: action, ms: ms))
    }
    @discardableResult func hopper(action: String, ms: Int? = nil) async throws -> CommandResponse {
        try await command("/manual/hopper", body: ActionBody(action: action, ms: ms))
    }
    @discardableResult func knock(cycles: Int? = nil) async throws -> CommandResponse {
        try await command("/manual/knock", body: KnockBody(cycles: cycles))
    }
}

enum MotorDirection: String { case fwd, rev, stop }

/// Body für solenoid/hopper: `ms` nur serialisieren wenn gesetzt.
private struct ActionBody: Encodable {
    let action: String
    let ms: Int?
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(action, forKey: .action)
        try c.encodeIfPresent(ms, forKey: .ms)
    }
    enum CodingKeys: String, CodingKey { case action, ms }
}

private struct KnockBody: Encodable {
    let cycles: Int?
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encodeIfPresent(cycles, forKey: .cycles)
    }
    enum CodingKeys: String, CodingKey { case cycles }
}

struct HealthInfo: Codable {
    let service: String
    let version: String
    let nanoConnected: Bool
    let nanoPort: String

    enum CodingKeys: String, CodingKey {
        case service, version
        case nanoConnected = "nano_connected"
        case nanoPort = "nano_port"
    }
}

// MARK: - Encodable type-erasure (für generische JSON-Bodies)

private struct AnyEncodable: Encodable {
    private let encodeFunc: (Encoder) throws -> Void
    init(_ wrapped: Encodable) {
        encodeFunc = wrapped.encode
    }
    func encode(to encoder: Encoder) throws {
        try encodeFunc(encoder)
    }
}
