//
//  StopfApp.swift
//  App-Entry. Erzeugt den AppState und injiziert ihn in die View-Hierarchie.
//

import SwiftUI

@main
struct StopfApp: App {
    @State private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(appState)
                .onAppear {
                    appState.connect()
                    appState.discovery.start()
                }
        }
    }
}
