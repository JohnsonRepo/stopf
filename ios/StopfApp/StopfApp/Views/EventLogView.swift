//
//  EventLogView.swift
//  Zeigt das Ereignis-Protokoll des Backends (Zustandswechsel, Fehler,
//  Nano-Abbrüche, System-Aktionen) — zum Nachvollziehen sporadischer Fehler.
//

import SwiftUI

struct EventLogView: View {
    @Environment(AppState.self) private var app

    @State private var events: [EventItem] = []
    @State private var loading = false
    @State private var loadError: String?

    var body: some View {
        List {
            if let loadError {
                Label(loadError, systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red).font(.callout)
            }
            if events.isEmpty && !loading && loadError == nil {
                ContentUnavailableView("Keine Ereignisse",
                                       systemImage: "checkmark.seal",
                                       description: Text("Seit dem letzten Backend-Start ist nichts protokolliert."))
            }
            ForEach(events) { e in
                HStack(alignment: .top, spacing: 10) {
                    Image(systemName: icon(e.level))
                        .foregroundStyle(color(e.level))
                        .font(.body)
                        .frame(width: 20)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(e.message)
                            .font(.callout)
                        Text(e.date, format: .dateTime.day().month().hour().minute().second())
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                            .monospacedDigit()
                    }
                }
                .padding(.vertical, 2)
            }
        }
        .navigationTitle("Fehlerprotokoll")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    Task { await load() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button(role: .destructive) {
                    Task {
                        try? await app.api.clearEvents()
                        await load()
                    }
                } label: {
                    Image(systemName: "trash")
                }
                .disabled(events.isEmpty)
            }
        }
        .task { await load() }
        .refreshable { await load() }
        .overlay {
            if loading && events.isEmpty {
                ProgressView()
            }
        }
    }

    private func load() async {
        loading = true
        loadError = nil
        do {
            events = try await app.api.events()
        } catch {
            loadError = error.localizedDescription
        }
        loading = false
    }

    private func icon(_ level: String) -> String {
        switch level {
        case "error": return "xmark.octagon.fill"
        case "warn":  return "exclamationmark.triangle.fill"
        default:       return "info.circle"
        }
    }

    private func color(_ level: String) -> Color {
        switch level {
        case "error": return .red
        case "warn":  return .orange
        default:       return .secondary
        }
    }
}

#Preview {
    NavigationStack { EventLogView() }
        .environment(AppState())
}
