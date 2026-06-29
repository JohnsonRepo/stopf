//
//  MachineStatus.swift
//  Spiegelt das MachineStatus-Schema des Pi-Backends (v0.3.0).
//

import Foundation

enum MachineState: String, Codable, CaseIterable {
    case idle
    case homing
    case stuffing
    case step
    case error

    var displayName: String {
        switch self {
        case .idle:     return "Bereit"
        case .homing:   return "Referenzfahrt"
        case .stuffing: return "Stopfen läuft"
        case .step:     return "Einzelschritt"
        case .error:    return "Fehler"
        }
    }

    var isBusy: Bool {
        self == .homing || self == .stuffing || self == .step
    }
}

struct MachineStatus: Codable, Equatable {
    var connected: Bool
    var state: MachineState
    var step: Int
    var error: String?
    var press: Bool
    var pushFront: Bool
    var pushRear: Bool
    var magazin: Bool
    var sol1: Bool
    var sol2: Bool
    var hopper: Bool
    var hopperEnabled: Bool
    var stepperPos: Int

    enum CodingKeys: String, CodingKey {
        case connected
        case state
        case step
        case error
        case press
        case pushFront = "push_front"
        case pushRear = "push_rear"
        case magazin
        case sol1
        case sol2
        case hopper
        case hopperEnabled = "hopper_enabled"
        case stepperPos = "stepper_pos"
    }

    /// Defensiv: unbekannte State-Strings (z.B. neue Firmware) → .error statt Crash.
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        connected     = try c.decodeIfPresent(Bool.self, forKey: .connected) ?? false
        let rawState  = try c.decodeIfPresent(String.self, forKey: .state) ?? "error"
        state         = MachineState(rawValue: rawState) ?? .error
        step          = try c.decodeIfPresent(Int.self, forKey: .step) ?? 0
        error         = try c.decodeIfPresent(String.self, forKey: .error)
        press         = try c.decodeIfPresent(Bool.self, forKey: .press) ?? false
        pushFront     = try c.decodeIfPresent(Bool.self, forKey: .pushFront) ?? false
        pushRear      = try c.decodeIfPresent(Bool.self, forKey: .pushRear) ?? false
        magazin       = try c.decodeIfPresent(Bool.self, forKey: .magazin) ?? false
        sol1          = try c.decodeIfPresent(Bool.self, forKey: .sol1) ?? false
        sol2          = try c.decodeIfPresent(Bool.self, forKey: .sol2) ?? false
        hopper        = try c.decodeIfPresent(Bool.self, forKey: .hopper) ?? false
        hopperEnabled = try c.decodeIfPresent(Bool.self, forKey: .hopperEnabled) ?? false
        stepperPos    = try c.decodeIfPresent(Int.self, forKey: .stepperPos) ?? 0
    }

    /// Platzhalter-Status, solange keine Verbindung steht.
    static let disconnected = MachineStatus(
        connected: false, state: .idle, step: 0, error: nil,
        press: false, pushFront: false, pushRear: false, magazin: false,
        sol1: false, sol2: false, hopper: false, hopperEnabled: false, stepperPos: 0
    )

    /// Memberwise-Init (für Previews / Defaults), da custom decoder den default verdeckt.
    init(connected: Bool, state: MachineState, step: Int, error: String?,
         press: Bool, pushFront: Bool, pushRear: Bool, magazin: Bool,
         sol1: Bool, sol2: Bool, hopper: Bool, hopperEnabled: Bool, stepperPos: Int) {
        self.connected = connected
        self.state = state
        self.step = step
        self.error = error
        self.press = press
        self.pushFront = pushFront
        self.pushRear = pushRear
        self.magazin = magazin
        self.sol1 = sol1
        self.sol2 = sol2
        self.hopper = hopper
        self.hopperEnabled = hopperEnabled
        self.stepperPos = stepperPos
    }
}

/// Klartext-Namen der 9 Stuff-Schritte (Index 1..9), gespiegelt zur Nano-Firmware.
enum StuffStep {
    static let names: [Int: String] = [
        1: "Trommel weiterdrehen",
        2: "Servo → Hülse aufschieben",
        3: "Servo → Home",
        4: "Knock (Tabak dosieren)",
        5: "Presse vor (bis Sensor)",
        6: "Presse zurück (Zeit)",
        7: "Pusher vor (bis Sensor)",
        8: "Pusher zurück (bis Sensor)",
        9: "Pause",
    ]

    static func name(_ n: Int) -> String {
        names[n] ?? "Schritt \(n)"
    }

    static let all: [Int] = Array(1...9)
}
