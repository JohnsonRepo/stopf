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
#define FIRMWARE_VERSION "0.2.0"  // v0.2: + Tabak-Dosierung (Tilt-Servo + 2 Solenoide), Hopper-Motor, Magazin-Status
#endif

// --- Watchdog / Sicherheit ---
constexpr unsigned long WATCHDOG_TIMEOUT_MS = 5000;  // ohne Pi-Befehl → Stop
constexpr unsigned long COMMAND_TIMEOUT_MS  = 30000; // max. Dauer für eine Aktion

// --- Schrittmotor (NEMA 17 / Trommelmagazin-Antrieb) ---
constexpr int   STEPPER_STEPS_PER_REV = 200;
constexpr float STEPPER_MAX_SPEED     = 800.0f;   // Steps/Sekunde
constexpr float STEPPER_ACCEL         = 1500.0f;  // Steps/s²
constexpr int   DRUM_STEPS_PER_POS    = 200;      // Steps pro Hülsenposition (anpassen!)

// --- DC-Motoren (PWM 0–255 auf ENA/ENB) ---
// L298N Standard-Modul mit ENA/ENB: Drehzahl-Regelung in beide Richtungen.
constexpr uint8_t PRESS_SPEED_DEFAULT  = 200;
constexpr uint8_t PUSHER_SPEED_DEFAULT = 220;
constexpr unsigned long PRESS_TIMEOUT_MS  = 4000;
constexpr unsigned long PUSHER_TIMEOUT_MS = 4000;

// --- Servo Hülsen-Schieber ---
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
constexpr bool MAGAZIN_TRIGGERED_LEVEL = HIGH;

// --- Tabak-Dosierung (nur 2 Solenoide, kein Servo) ---
// Knock-Sequenz: beide Solenoide pulsen synchron, Tabak rieselt durch Schwerkraft
// und Impulsstöße in die Stopfposition. Kein Servo dazwischen.
constexpr unsigned long KNOCK_PULSE_ON_MS  = 80;   // Solenoid an pro Schlag
constexpr unsigned long KNOCK_PULSE_OFF_MS = 120;  // Pause nach Schlag (Erholung)
constexpr uint8_t       KNOCK_CYCLES_DEFAULT = 8;  // Anzahl Schläge pro Dose

// Solenoid-Sicherheit
constexpr unsigned long SOLENOID_PULSE_MAX_MS = 1000;  // max Einzelpuls — Heschen
                                                        // ist nicht für Dauer-ON
                                                        // ausgelegt!

// --- Hülsenmagazin-Motor (5 V Vibrationsmotor) ---
constexpr unsigned long HOPPER_DEFAULT_MS = 1500;       // Default-Lauf für "hopper run"
constexpr unsigned long HOPPER_RUN_MAX_MS = 4000;       // unter Watchdog (5 s)
