//
//  Components.swift
//  Wiederverwendbare UI-Bausteine.
//

import SwiftUI

/// Kleiner Status-Punkt mit Label (für Sensor-/Aktor-Anzeige).
struct StatusDot: View {
    let label: String
    let active: Bool
    var activeColor: Color = .green
    var inactiveColor: Color = Color.secondary.opacity(0.35)

    var body: some View {
        VStack(spacing: 4) {
            Circle()
                .fill(active ? activeColor : inactiveColor)
                .frame(width: 14, height: 14)
                .overlay(
                    Circle().stroke(.black.opacity(0.1), lineWidth: 0.5)
                )
            Text(label)
                .font(.system(size: 9))
                .foregroundStyle(.secondary)
                .lineLimit(1)
        }
        .frame(minWidth: 38)
    }
}

/// Momentary-Button („Jog"): sendet beim Drücken `onPress`, hält die Aktion
/// durch periodisches Nachfeuern am Leben (füttert den Nano-Watchdog), und
/// sendet beim Loslassen `onRelease`. Ideal für Motor-Tippbetrieb.
struct MomentaryButton: View {
    let title: String
    let systemImage: String
    var tint: Color = .blue
    var disabled: Bool = false
    let onPress: () -> Void
    let onRelease: () -> Void

    @State private var pressed = false
    @State private var ticker: Task<Void, Never>?

    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: systemImage)
                .font(.title2)
            Text(title)
                .font(.caption.weight(.medium))
        }
        .frame(maxWidth: .infinity)
        .frame(height: 72)
        .background(
            (pressed ? tint : tint.opacity(0.15)),
            in: RoundedRectangle(cornerRadius: 14)
        )
        .foregroundStyle(pressed ? .white : tint)
        .opacity(disabled ? 0.4 : 1)
        .contentShape(RoundedRectangle(cornerRadius: 14))
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    guard !disabled, !pressed else { return }
                    pressed = true
                    onPress()
                    startTicker()
                }
                .onEnded { _ in
                    guard pressed else { return }
                    pressed = false
                    stopTicker()
                    onRelease()
                }
        )
    }

    private func startTicker() {
        ticker?.cancel()
        ticker = Task { @MainActor in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(1.5))
                if Task.isCancelled { break }
                // Richtung erneut senden → füttert Watchdog, hält Motor an.
                onPress()
            }
        }
    }

    private func stopTicker() {
        ticker?.cancel()
        ticker = nil
    }
}

/// Aktions-Button im einheitlichen Stil (für einmalige Befehle).
struct ActionButton: View {
    let title: String
    var systemImage: String? = nil
    var tint: Color = .blue
    var disabled: Bool = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                if let systemImage { Image(systemName: systemImage) }
                Text(title)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 10)
        }
        .buttonStyle(.borderedProminent)
        .tint(tint)
        .disabled(disabled)
    }
}

/// Banner für „Maschine nicht bereit / nicht verbunden".
struct NotReadyBanner: View {
    let text: String
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "info.circle.fill")
            Text(text).font(.callout)
            Spacer()
        }
        .padding(10)
        .background(.yellow.opacity(0.18), in: RoundedRectangle(cornerRadius: 10))
        .foregroundStyle(.secondary)
    }
}
