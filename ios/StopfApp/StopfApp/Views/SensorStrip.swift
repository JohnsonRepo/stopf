//
//  SensorStrip.swift
//  Permanente Leiste mit Live-Sensor- und Aktor-Zuständen.
//  Wird in RootView über der TabView gepinnt (in jedem Tab sichtbar).
//

import SwiftUI

struct SensorStrip: View {
    @Environment(AppState.self) private var app

    var body: some View {
        let s = app.status
        VStack(spacing: 6) {
            // Zeile 1: Verbindung + State
            HStack(spacing: 8) {
                Circle()
                    .fill(app.isLive ? .green : .red)
                    .frame(width: 9, height: 9)
                Text(app.isLive ? s.state.displayName : "Getrennt")
                    .font(.caption.weight(.semibold))
                if app.isLive, s.state.isBusy, s.step > 0 {
                    Text("· \(StuffStep.name(s.step))")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
                Spacer()
                if let err = s.error, !err.isEmpty {
                    Label(err, systemImage: "exclamationmark.triangle.fill")
                        .font(.caption2)
                        .foregroundStyle(.orange)
                        .lineLimit(1)
                }
            }

            // Zeile 2: Sensoren + Aktoren
            HStack(spacing: 2) {
                StatusDot(label: "Presse", active: s.press)
                StatusDot(label: "Push V", active: s.pushFront)
                StatusDot(label: "Push H", active: s.pushRear)
                StatusDot(label: "Magazin", active: s.magazin, activeColor: .blue)
                Divider().frame(height: 28)
                StatusDot(label: "Sol 1", active: s.sol1, activeColor: .orange)
                StatusDot(label: "Sol 2", active: s.sol2, activeColor: .orange)
                StatusDot(label: "Hopper", active: s.hopper, activeColor: .purple)
            }
            .opacity(app.isLive ? 1 : 0.4)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.bar)
        .overlay(alignment: .bottom) {
            Divider()
        }
    }
}
