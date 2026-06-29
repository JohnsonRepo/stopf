//
//  AutoTab.swift
//  Automatik-Betrieb: Referenzfahrt, Vollsequenz starten/stoppen,
//  Live-Fortschritt der 9 Schritte, lokaler Tageszähler.
//

import SwiftUI

struct AutoTab: View {
    @Environment(AppState.self) private var app

    // Tageszähler lokal in der App (überlebt App-Neustart).
    @AppStorage("stopf.counter") private var counter: Int = 0
    @State private var lastStuffStep: Int = 0

    private var s: MachineStatus { app.status }
    private var running: Bool { s.state == .stuffing }
    private var homing: Bool { s.state == .homing }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    if !app.isLive {
                        NotReadyBanner(text: "Nicht verbunden — siehe Tab „Verbindung“.")
                    }

                    stateCard
                    controlButtons
                    sequenceList
                    counterCard
                }
                .padding()
                .padding(.bottom, 90)
            }
            .navigationTitle("Automatik")
            .onChange(of: s.step) { _, newStep in
                // Zähler erhöhen, wenn ein Stopf-Zyklus durch ist (Schritt 9 → 1).
                if running, lastStuffStep == 9, newStep == 1 {
                    counter += 1
                }
                if running { lastStuffStep = newStep }
            }
        }
    }

    // MARK: - State card

    private var stateCard: some View {
        VStack(spacing: 8) {
            Text(app.isLive ? s.state.displayName : "—")
                .font(.largeTitle.weight(.bold))
                .foregroundStyle(stateColor)
            if s.state.isBusy, s.step > 0 {
                Text(StuffStep.name(s.step))
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
            if let err = s.error, !err.isEmpty {
                Label(err, systemImage: "exclamationmark.triangle.fill")
                    .font(.callout)
                    .foregroundStyle(.orange)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
        .background(stateColor.opacity(0.1), in: RoundedRectangle(cornerRadius: 16))
    }

    private var stateColor: Color {
        switch s.state {
        case .idle:     return .green
        case .homing:   return .blue
        case .stuffing: return .indigo
        case .step:     return .teal
        case .error:    return .orange
        }
    }

    // MARK: - Controls

    private var controlButtons: some View {
        VStack(spacing: 12) {
            if running {
                ActionButton(title: "Stoppen", systemImage: "stop.fill",
                             tint: .red, disabled: false) {
                    app.emergencyStop()
                }
            } else {
                ActionButton(title: "STOPFEN starten", systemImage: "play.fill",
                             tint: .indigo, disabled: !app.isReady) {
                    lastStuffStep = 0
                    app.fire { try await $0.stuff() }
                }
            }

            HStack(spacing: 12) {
                ActionButton(title: "Referenzfahrt", systemImage: "house",
                             tint: .blue, disabled: !app.isReady) {
                    app.fire { try await $0.home() }
                }
                ActionButton(title: "Stop", systemImage: "stop",
                             tint: .gray, disabled: !app.isLive) {
                    app.emergencyStop()
                }
            }
        }
    }

    // MARK: - Sequence list

    private var sequenceList: some View {
        GroupBox {
            VStack(spacing: 0) {
                ForEach(StuffStep.all, id: \.self) { n in
                    HStack(spacing: 10) {
                        ZStack {
                            Circle()
                                .fill(stepColor(n))
                                .frame(width: 24, height: 24)
                            if isDone(n) {
                                Image(systemName: "checkmark")
                                    .font(.caption2.weight(.bold))
                                    .foregroundStyle(.white)
                            } else {
                                Text("\(n)")
                                    .font(.caption2.weight(.bold))
                                    .foregroundStyle(isCurrent(n) ? .white : .secondary)
                            }
                        }
                        Text(StuffStep.name(n))
                            .font(.callout)
                            .foregroundStyle(isCurrent(n) ? .primary : .secondary)
                            .fontWeight(isCurrent(n) ? .semibold : .regular)
                        Spacer()
                        if isCurrent(n) {
                            ProgressView().controlSize(.small)
                        }
                    }
                    .padding(.vertical, 6)
                    if n != StuffStep.all.last { Divider() }
                }
            }
        } label: {
            Label("Ablauf", systemImage: "list.number")
        }
    }

    private func isCurrent(_ n: Int) -> Bool {
        s.state.isBusy && s.step == n
    }
    private func isDone(_ n: Int) -> Bool {
        running && s.step > n
    }
    private func stepColor(_ n: Int) -> Color {
        if isCurrent(n) { return .indigo }
        if isDone(n)    { return .green }
        return Color.secondary.opacity(0.25)
    }

    // MARK: - Counter

    private var counterCard: some View {
        GroupBox {
            HStack {
                VStack(alignment: .leading) {
                    Text("Gestopft heute")
                        .font(.caption).foregroundStyle(.secondary)
                    Text("\(counter)")
                        .font(.system(size: 36, weight: .bold, design: .rounded))
                        .monospacedDigit()
                }
                Spacer()
                Button("Zurücksetzen") { counter = 0 }
                    .buttonStyle(.bordered)
                    .tint(.gray)
            }
        }
    }
}

#Preview {
    AutoTab()
        .environment(AppState())
}
