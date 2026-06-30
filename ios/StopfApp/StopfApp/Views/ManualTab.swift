//
//  ManualTab.swift
//  Handbetrieb: Einzelaktoren testen + Stopfsequenz schrittweise durchgehen.
//  Befehle sind nur im Zustand „idle" erlaubt (Nano blockt sonst).
//

import SwiftUI

struct ManualTab: View {
    @Environment(AppState.self) private var app

    @State private var servoAngle: Double = 5
    @State private var knockCycles: Int = 8
    @State private var hopperTestMs: Double = 1500
    @State private var stepperSteps: Int = 200

    private var ready: Bool { app.isReady }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 18) {
                    if !app.isLive {
                        NotReadyBanner(text: "Nicht verbunden — siehe Tab „Verbindung“.")
                    } else if !ready {
                        NotReadyBanner(text: "Maschine ist beschäftigt (\(app.status.state.displayName)). Manuelle Befehle sind gesperrt.")
                    }

                    sensorsSection
                    pressPusherSection
                    servoSection
                    solenoidSection
                    knockSection
                    hopperSection
                    stepperSection
                    stepBystepSection
                }
                .padding()
                .padding(.bottom, 90)   // Platz für Notaus-Button
            }
            .navigationTitle("Handbetrieb")
            .scrollDismissesKeyboard(.interactively)
        }
    }

    // MARK: - Sensoren (Live)

    private var sensorsSection: some View {
        let s = app.status
        return GroupBox {
            VStack(spacing: 0) {
                SensorRow(name: "Initiator Presse", pin: "A0",
                          active: s.press, live: app.isLive)
                Divider()
                SensorRow(name: "Initiator Pusher vorn", pin: "A1",
                          active: s.pushFront, live: app.isLive)
                Divider()
                SensorRow(name: "Initiator Pusher hinten", pin: "A2",
                          active: s.pushRear, live: app.isLive)
                Divider()
                SensorRow(name: "Magazin-Lichtschranke", pin: "A5",
                          active: s.magazin, activeColor: .blue, live: app.isLive)
            }
        } label: {
            Label("Sensoren (live)", systemImage: "dot.radiowaves.left.and.right")
        }
    }

    // MARK: - Presse + Pusher (Jog)

    private var pressPusherSection: some View {
        GroupBox {
            VStack(spacing: 12) {
                Text("Halten = fahren · Loslassen = stop")
                    .font(.caption).foregroundStyle(.secondary)
                HStack(spacing: 12) {
                    MomentaryButton(title: "Presse vor", systemImage: "arrow.down",
                                    tint: .blue, disabled: !ready,
                                    onPress: { app.fire { try await $0.press(.fwd) } },
                                    onRelease: { app.fire { try await $0.press(.stop) } })
                    MomentaryButton(title: "Presse zurück", systemImage: "arrow.up",
                                    tint: .blue, disabled: !ready,
                                    onPress: { app.fire { try await $0.press(.rev) } },
                                    onRelease: { app.fire { try await $0.press(.stop) } })
                }
                HStack(spacing: 12) {
                    MomentaryButton(title: "Pusher vor", systemImage: "arrow.right",
                                    tint: .teal, disabled: !ready,
                                    onPress: { app.fire { try await $0.pusher(.fwd) } },
                                    onRelease: { app.fire { try await $0.pusher(.stop) } })
                    MomentaryButton(title: "Pusher zurück", systemImage: "arrow.left",
                                    tint: .teal, disabled: !ready,
                                    onPress: { app.fire { try await $0.pusher(.rev) } },
                                    onRelease: { app.fire { try await $0.pusher(.stop) } })
                }
            }
        } label: {
            Label("Presse & Pusher", systemImage: "arrow.up.and.down")
        }
    }

    // MARK: - Servo

    private var servoSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("Winkel")
                    Spacer()
                    Text("\(Int(servoAngle))°").monospacedDigit().foregroundStyle(.secondary)
                }
                Slider(value: $servoAngle, in: 0...180, step: 1) {
                    Text("Servo")
                } onEditingChanged: { editing in
                    if !editing { app.fire { try await $0.servo(Int(servoAngle)) } }
                }
                .disabled(!ready)
                HStack(spacing: 12) {
                    ActionButton(title: "Home", tint: .gray, disabled: !ready) {
                        servoAngle = 5
                        app.fire { try await $0.servo(5) }
                    }
                    ActionButton(title: "Laden", tint: .gray, disabled: !ready) {
                        servoAngle = 85
                        app.fire { try await $0.servo(85) }
                    }
                }
            }
        } label: {
            Label("Servo (Hülsen-Schieber)", systemImage: "slider.horizontal.below.rectangle")
        }
    }

    // MARK: - Solenoide

    private var solenoidSection: some View {
        GroupBox {
            VStack(spacing: 12) {
                ForEach([1, 2], id: \.self) { which in
                    HStack(spacing: 10) {
                        Text("Solenoid \(which)").frame(width: 90, alignment: .leading)
                        ActionButton(title: "Puls", tint: .orange, disabled: !ready) {
                            app.fire { try await $0.solenoid(which, action: "pulse", ms: 80) }
                        }
                        ActionButton(title: "An", tint: .orange, disabled: !ready) {
                            app.fire { try await $0.solenoid(which, action: "on") }
                        }
                        ActionButton(title: "Aus", tint: .gray, disabled: !ready) {
                            app.fire { try await $0.solenoid(which, action: "off") }
                        }
                    }
                }
                Text("„An“ dauerhaft nur kurz — Heschen-Magnete werden heiß.")
                    .font(.caption2).foregroundStyle(.secondary)
            }
        } label: {
            Label("Solenoide (Knock-Magnete)", systemImage: "bolt")
        }
    }

    // MARK: - Knock

    private var knockSection: some View {
        GroupBox {
            VStack(spacing: 12) {
                Stepper(value: $knockCycles, in: 1...50) {
                    HStack {
                        Text("Schläge")
                        Spacer()
                        Text("\(knockCycles)×").monospacedDigit().foregroundStyle(.secondary)
                    }
                }
                .disabled(!ready)
                ActionButton(title: "Knock starten", systemImage: "hammer",
                             tint: .indigo, disabled: !ready) {
                    app.fire { try await $0.knock(cycles: knockCycles) }
                }
            }
        } label: {
            Label("Knock", systemImage: "hammer")
        }
    }

    // MARK: - Hopper

    private var hopperSection: some View {
        GroupBox {
            VStack(spacing: 12) {
                HStack(spacing: 12) {
                    ActionButton(title: "Zyklus an", systemImage: "play",
                                 tint: .purple, disabled: !ready) {
                        app.fire { try await $0.hopper(action: "on") }
                    }
                    ActionButton(title: "Aus", systemImage: "stop",
                                 tint: .gray, disabled: !app.isLive) {
                        app.fire { try await $0.hopper(action: "off") }
                    }
                }
                HStack {
                    Text("Test")
                    Slider(value: $hopperTestMs, in: 200...4000, step: 100)
                    Text("\(Int(hopperTestMs)) ms")
                        .monospacedDigit().font(.caption).foregroundStyle(.secondary)
                        .frame(width: 64, alignment: .trailing)
                }
                ActionButton(title: "Test-Lauf", tint: .purple, disabled: !ready) {
                    app.fire { try await $0.hopper(action: "test", ms: Int(hopperTestMs)) }
                }
            }
        } label: {
            Label("Hülsen-Vortransport", systemImage: "shippingbox")
        }
    }

    // MARK: - Stepper

    private var stepperSection: some View {
        GroupBox {
            VStack(spacing: 12) {
                Stepper(value: $stepperSteps, in: -2000...2000, step: 50) {
                    HStack {
                        Text("Schritte")
                        Spacer()
                        Text("\(stepperSteps)").monospacedDigit().foregroundStyle(.secondary)
                    }
                }
                .disabled(!ready)
                ActionButton(title: "Trommel bewegen", systemImage: "circle.dotted",
                             tint: .brown, disabled: !ready) {
                    app.fire { try await $0.stepper(stepperSteps) }
                }
            }
        } label: {
            Label("Trommel (Stepper)", systemImage: "circle.dotted")
        }
    }

    // MARK: - Schritt-für-Schritt

    private var stepBystepSection: some View {
        GroupBox {
            VStack(spacing: 8) {
                Text("Einzelner Sequenz-Schritt (1–9)")
                    .font(.caption).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                ForEach(StuffStep.all, id: \.self) { n in
                    Button {
                        app.fire { try await $0.step(n) }
                    } label: {
                        HStack {
                            Text("\(n)")
                                .font(.caption.weight(.bold))
                                .frame(width: 22, height: 22)
                                .background(Circle().fill(.brown.opacity(0.2)))
                            Text(StuffStep.name(n))
                                .font(.callout)
                            Spacer()
                            Image(systemName: "play.fill")
                                .font(.caption)
                                .foregroundStyle(.brown)
                        }
                        .padding(.vertical, 4)
                    }
                    .buttonStyle(.plain)
                    .disabled(!ready)
                    .opacity(ready ? 1 : 0.4)
                    if n != StuffStep.all.last { Divider() }
                }
            }
        } label: {
            Label("Schritt-für-Schritt", systemImage: "list.number")
        }
    }
}

#Preview {
    ManualTab()
        .environment(AppState())
}
