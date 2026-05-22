// =====================================================
// config.h
// Konfigurationskonstanten (Defaults)
// Können später durch Pi-Befehle überschrieben werden
// =====================================================
#pragma once

// --- Build-Portabilität (PlatformIO vs. Arduino IDE) ---
// In PlatformIO kommen diese aus platformio.ini (-D SERIAL_BAUD=... etc.).
// Die Arduino IDE liest platformio.ini NICHT → hier Fallback-Defaults,
// damit der Code in BEIDEN Umgebungen kompiliert. Die #ifndef-Guards
// verhindern Doppel-Definitionen wenn das Build-Flag schon gesetzt ist.
#ifndef SERIAL_BAUD
#define SERIAL_BAUD 115200
#endif
#ifndef FIRMWARE_VERSION
#define FIRMWARE_VERSION "0.1.0"
#endif

// --- Watchdog / Sicherheit ---
constexpr unsigned long WATCHDOG_TIMEOUT_MS = 5000;  // ohne Pi-Befehl → Stop
constexpr unsigned long COMMAND_TIMEOUT_MS  = 30000; // max. Dauer für eine Aktion

// --- Schrittmotor (NEMA 17 mit T8-Spindel, 2mm Pitch) ---
constexpr int   STEPPER_STEPS_PER_REV = 200;
constexpr float STEPPER_MAX_SPEED     = 800.0f;   // Steps/Sekunde
constexpr float STEPPER_ACCEL         = 1500.0f;  // Steps/s²
constexpr int   STEPPER_FEED_STEPS    = 400;      // Default-Tabakdosis

// --- DC-Motoren (PWM 0–255 auf ENA/ENB) ---
// L298N Standard-Modul mit ENA/ENB: Drehzahl-Regelung in beide Richtungen.
constexpr uint8_t PRESS_SPEED_DEFAULT  = 200;
constexpr uint8_t PUSHER_SPEED_DEFAULT = 220;
constexpr unsigned long PRESS_TIMEOUT_MS  = 4000;
constexpr unsigned long PUSHER_TIMEOUT_MS = 4000;

// --- Servo (Hülsen-Schieber) ---
constexpr int SERVO_POS_HOME = 5;    // Hülse fertig aufgeschoben
constexpr int SERVO_POS_LOAD = 85;   // Hülse aufnehmen
constexpr int SERVO_MOVE_DELAY_MS = 500;

// --- Initiatoren (Logik) ---
// NPN-Sensoren → bei Detektion ziehen sie nach LOW (über Spannungsteiler)
// Wir prüfen mit digitalRead, Schwellwert ist HIGH/LOW
constexpr bool INIT_TRIGGERED_LEVEL = LOW;

// --- Magazin-Lichtschranke (Logik) ---
// Module-abhängig — typisch: Flagge im Schlitz blockiert IR-Licht →
// Phototransistor sperrt → DO-Pin via Pull-up auf HIGH.
// Falls dein Modul invertiert ist (Comparator): auf HIGH ändern.
// Test: status anzeigen, Flagge in den Schlitz halten, beobachten welcher
// Wert "blockiert" entspricht.
constexpr bool MAGAZIN_TRIGGERED_LEVEL = HIGH;

// --- Start-Taster (mechanisch, mit Software-Entprellung) ---
constexpr unsigned long BUTTON_DEBOUNCE_MS = 50;
