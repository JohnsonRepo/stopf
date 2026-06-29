//
//  EmergencyButton.swift
//  Immer sichtbarer Notaus. Sendet `stop`, stoppt alle Aktoren sofort.
//

import SwiftUI

struct EmergencyButton: View {
    @Environment(AppState.self) private var app
    @State private var flashing = false

    var body: some View {
        Button {
            app.emergencyStop()
        } label: {
            VStack(spacing: 2) {
                Image(systemName: "hand.raised.fill")
                    .font(.system(size: 22, weight: .bold))
                Text("STOP")
                    .font(.system(size: 11, weight: .heavy))
            }
            .foregroundStyle(.white)
            .frame(width: 68, height: 68)
            .background(
                Circle().fill(.red)
            )
            .overlay(
                Circle().stroke(.white, lineWidth: 3)
            )
            .shadow(color: .black.opacity(0.3), radius: 6, y: 3)
        }
        .accessibilityLabel("Notaus")
    }
}

/// Transiente Fehlermeldung oben am Bildschirmrand.
struct ToastView: View {
    let message: String
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "exclamationmark.circle.fill")
            Text(message)
                .font(.callout.weight(.medium))
                .lineLimit(2)
        }
        .foregroundStyle(.white)
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(.red.opacity(0.92), in: Capsule())
        .shadow(radius: 4, y: 2)
        .padding(.horizontal)
        .transition(.move(edge: .top).combined(with: .opacity))
    }
}
