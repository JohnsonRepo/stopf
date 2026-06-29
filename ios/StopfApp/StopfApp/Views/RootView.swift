//
//  RootView.swift
//  TabView + permanenter Sensor-Strip + Notaus-Overlay + Toast.
//

import SwiftUI

struct RootView: View {
    @Environment(AppState.self) private var app

    var body: some View {
        ZStack(alignment: .bottomTrailing) {
            VStack(spacing: 0) {
                SensorStrip()
                TabView {
                    AutoTab()
                        .tabItem { Label("Auto", systemImage: "play.circle") }
                    ManualTab()
                        .tabItem { Label("Manuell", systemImage: "hand.tap") }
                    ParamsTab()
                        .tabItem { Label("Parameter", systemImage: "slider.horizontal.3") }
                    SettingsTab()
                        .tabItem { Label("Verbindung", systemImage: "wifi") }
                }
            }

            EmergencyButton()
                .padding(.trailing, 16)
                .padding(.bottom, 58)   // über der Tab-Bar schweben
        }
        .overlay(alignment: .top) {
            if let toast = app.toast {
                ToastView(message: toast)
                    .padding(.top, 4)
            }
        }
        .animation(.snappy, value: app.toast)
    }
}

#Preview {
    RootView()
        .environment(AppState())
}
