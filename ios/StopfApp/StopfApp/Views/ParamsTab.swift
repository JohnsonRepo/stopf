//
//  ParamsTab.swift
//  Lädt die EEPROM-Parameter vom Nano, lässt sie editieren und zurückschreiben.
//

import SwiftUI
import Observation

@Observable
@MainActor
final class ParamsStore {
    /// Aktuell editierte Werte (key → value).
    var values: [String: Int] = [:]
    /// Vom Nano geladene Referenzwerte (für Dirty-Erkennung).
    private(set) var loaded: [String: Int] = [:]

    var isLoading = false
    var isSaving = false
    var loadError: String?

    var dirtyKeys: Set<String> {
        var s = Set<String>()
        for (k, v) in values where loaded[k] != v { s.insert(k) }
        return s
    }
    var isDirty: Bool { !dirtyKeys.isEmpty }

    func load(_ api: APIClient) async {
        isLoading = true
        loadError = nil
        defer { isLoading = false }
        do {
            let p = try await api.params()
            if p.isEmpty {
                loadError = "Keine Parameter empfangen (Nano verbunden?)."
            }
            loaded = p
            values = p
        } catch {
            loadError = error.localizedDescription
        }
    }

    /// Schreibt nur geänderte Keys als Batch zurück.
    func save(_ api: APIClient) async -> String? {
        guard isDirty else { return nil }
        isSaving = true
        defer { isSaving = false }
        let changed = dirtyKeys.reduce(into: [String: Int]()) { acc, k in
            acc[k] = values[k]
        }
        do {
            let resp = try await api.setParams(changed)
            // Erfolgreiche Keys als geladen markieren.
            for (k, v) in changed { loaded[k] = v }
            return resp.ok ? nil : resp.reply
        } catch {
            return error.localizedDescription
        }
    }

    func binding(for key: String, default def: Int) -> Binding<Double> {
        Binding(
            get: { Double(self.values[key] ?? self.loaded[key] ?? def) },
            set: { self.values[key] = Int($0) }
        )
    }

    func intValue(_ key: String) -> Int {
        values[key] ?? loaded[key] ?? 0
    }
}

struct ParamsTab: View {
    @Environment(AppState.self) private var app
    @State private var store = ParamsStore()
    @State private var saveError: String?

    var body: some View {
        NavigationStack {
            Group {
                if store.isLoading && store.loaded.isEmpty {
                    ProgressView("Lade Parameter…")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if store.loaded.isEmpty {
                    emptyState
                } else {
                    paramForm
                }
            }
            .navigationTitle("Parameter")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button {
                        Task { await store.load(app.api) }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .disabled(store.isLoading)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Speichern") {
                        Task {
                            saveError = await store.save(app.api)
                            if let saveError { app.showToast(saveError) }
                        }
                    }
                    .disabled(!store.isDirty || store.isSaving)
                    .fontWeight(.semibold)
                }
            }
            .task {
                if store.loaded.isEmpty { await store.load(app.api) }
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "slider.horizontal.3")
                .font(.system(size: 48)).foregroundStyle(.secondary)
            Text(store.loadError ?? "Keine Parameter geladen.")
                .foregroundStyle(.secondary).multilineTextAlignment(.center)
            Button("Erneut laden") { Task { await store.load(app.api) } }
                .buttonStyle(.borderedProminent)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var paramForm: some View {
        Form {
            if store.isDirty {
                Section {
                    Label("\(store.dirtyKeys.count) ungespeicherte Änderung(en)",
                          systemImage: "pencil.circle.fill")
                        .foregroundStyle(.orange)
                }
            }
            ForEach(ParamCatalog.orderedGroups) { group in
                Section {
                    ForEach(ParamCatalog.specs(in: group)) { spec in
                        ParamRow(spec: spec, store: store)
                    }
                } header: {
                    Label(group.rawValue, systemImage: group.symbol)
                }
            }
        }
    }
}

/// Eine Parameter-Zeile: Label + Wert + Slider, dirty-markiert.
struct ParamRow: View {
    let spec: ParamSpec
    let store: ParamsStore

    private var isDirty: Bool { store.dirtyKeys.contains(spec.key) }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(spec.label)
                if isDirty {
                    Circle().fill(.orange).frame(width: 6, height: 6)
                }
                Spacer()
                Text("\(store.intValue(spec.key))\(spec.unit.isEmpty ? "" : " \(spec.unit)")")
                    .monospacedDigit()
                    .foregroundStyle(isDirty ? .orange : .secondary)
            }
            HStack(spacing: 12) {
                Stepper("", value: stepperBinding, in: spec.minVal...spec.maxVal, step: spec.step)
                    .labelsHidden()
                Slider(
                    value: store.binding(for: spec.key, default: spec.minVal),
                    in: Double(spec.minVal)...Double(spec.maxVal),
                    step: Double(spec.step)
                )
            }
        }
        .padding(.vertical, 2)
    }

    private var stepperBinding: Binding<Int> {
        Binding(
            get: { store.intValue(spec.key) },
            set: { store.values[spec.key] = $0 }
        )
    }
}

#Preview {
    ParamsTab()
        .environment(AppState())
}
