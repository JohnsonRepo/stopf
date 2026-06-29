//
//  Params.swift
//  Spiegelt die 18 EEPROM-Parameter der Nano-Firmware v0.3.0.
//
//  Backend liefert /params als flaches {key: Int}-Dictionary; wir halten es
//  genauso (Dictionary statt Struct), damit neue Parameter in der Firmware
//  nicht zwingend einen App-Update erfordern. Die UI-Metadaten (Label, Range,
//  Einheit, Gruppe) stehen in ParamSpec.
//

import Foundation

/// Beschreibt einen Parameter für die generische Slider-/Stepper-UI.
struct ParamSpec: Identifiable {
    let key: String
    let label: String
    let group: ParamGroup
    let minVal: Int
    let maxVal: Int
    let unit: String
    let step: Int          // Schrittweite im UI-Stepper

    var id: String { key }
}

enum ParamGroup: String, CaseIterable, Identifiable {
    case drum    = "Trommel"
    case servo   = "Servo (Hülsen-Schieber)"
    case knock   = "Knock (Tabak-Dosierung)"
    case hopper  = "Hülsen-Vortransport"
    case press   = "Presse"
    case pusher  = "Pusher"
    case solenoid = "Solenoide (Manual-Puls)"
    case sequence = "Sequenz"

    var id: String { rawValue }

    /// SF-Symbol pro Gruppe (für Section-Header).
    var symbol: String {
        switch self {
        case .drum:     return "circle.dotted"
        case .servo:    return "slider.horizontal.below.rectangle"
        case .knock:    return "hammer"
        case .hopper:   return "shippingbox"
        case .press:    return "arrow.down.to.line.compact"
        case .pusher:   return "arrow.left.and.right"
        case .solenoid: return "bolt"
        case .sequence: return "timer"
        }
    }
}

/// Single Source of Truth für UI-Darstellung. Ranges MÜSSEN zu params.cpp passen.
enum ParamCatalog {
    static let specs: [ParamSpec] = [
        // Trommel
        .init(key: "drum_steps_per_pos",    label: "Schritte pro Position", group: .drum,   minVal: 1,   maxVal: 10000, unit: "Steps", step: 1),
        .init(key: "home_drum_timeout_ms",  label: "Home-Timeout",          group: .drum,   minVal: 100, maxVal: 60000, unit: "ms",    step: 100),
        // Servo
        .init(key: "servo_home",            label: "Position Home",         group: .servo,  minVal: 0,   maxVal: 180,   unit: "°",     step: 1),
        .init(key: "servo_load",            label: "Position Laden",        group: .servo,  minVal: 0,   maxVal: 180,   unit: "°",     step: 1),
        // Knock
        .init(key: "knock_cycles",          label: "Anzahl Schläge",        group: .knock,  minVal: 1,   maxVal: 50,    unit: "×",     step: 1),
        .init(key: "knock_on_ms",           label: "Schlag-Dauer",          group: .knock,  minVal: 1,   maxVal: 1000,  unit: "ms",    step: 5),
        .init(key: "knock_off_ms",          label: "Pause zwischen Schlägen", group: .knock, minVal: 1, maxVal: 2000,  unit: "ms",    step: 5),
        // Hopper
        .init(key: "hopper_on_ms",          label: "An-Zeit",               group: .hopper, minVal: 100, maxVal: 60000, unit: "ms",    step: 500),
        .init(key: "hopper_off_ms",         label: "Aus-Zeit",              group: .hopper, minVal: 100, maxVal: 60000, unit: "ms",    step: 500),
        // Presse
        .init(key: "press_pwm",             label: "Drehzahl (PWM)",        group: .press,  minVal: 60,  maxVal: 255,   unit: "",      step: 5),
        .init(key: "press_rev_ms",          label: "Rücklauf-Dauer",        group: .press,  minVal: 50,  maxVal: 10000, unit: "ms",    step: 50),
        .init(key: "press_fwd_timeout_ms",  label: "Vorlauf-Timeout",       group: .press,  minVal: 100, maxVal: 10000, unit: "ms",    step: 100),
        // Pusher
        .init(key: "pusher_pwm",            label: "Drehzahl (PWM)",        group: .pusher, minVal: 60,  maxVal: 255,   unit: "",      step: 5),
        .init(key: "pusher_fwd_timeout_ms", label: "Vorlauf-Timeout",       group: .pusher, minVal: 100, maxVal: 10000, unit: "ms",    step: 100),
        .init(key: "pusher_rev_timeout_ms", label: "Rücklauf-Timeout",      group: .pusher, minVal: 100, maxVal: 10000, unit: "ms",    step: 100),
        // Solenoide
        .init(key: "sol1_dwell_ms",         label: "Solenoid 1 Puls",       group: .solenoid, minVal: 1, maxVal: 1000, unit: "ms",    step: 5),
        .init(key: "sol2_dwell_ms",         label: "Solenoid 2 Puls",       group: .solenoid, minVal: 1, maxVal: 1000, unit: "ms",    step: 5),
        // Sequenz
        .init(key: "step_delay_ms",         label: "Pause zwischen Zyklen", group: .sequence, minVal: 0, maxVal: 10000, unit: "ms",   step: 50),
    ]

    static func specs(in group: ParamGroup) -> [ParamSpec] {
        specs.filter { $0.group == group }
    }

    static func spec(for key: String) -> ParamSpec? {
        specs.first { $0.key == key }
    }

    /// Reihenfolge der Gruppen wie sie im Param-Tab erscheinen.
    static let orderedGroups: [ParamGroup] = [
        .drum, .servo, .knock, .hopper, .press, .pusher, .solenoid, .sequence
    ]
}
