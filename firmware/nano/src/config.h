// =====================================================
// config.h
// Konstanten, die NICHT zur Laufzeit veränderbar sind.
// Alle live-tunbaren Werte stehen in params.h (EEPROM).
// =====================================================
#pragma once

// --- Build-Portabilität (PlatformIO vs. Arduino IDE) ---
#ifndef SERIAL_BAUD
#define SERIAL_BAUD 115200
#endif
#ifndef FIRMWARE_VERSION
#define FIRMWARE_VERSION "0.5.0"   // v0.5.0: Hülsen-Schieber mit Zahnstange: Servo-Rampe (servo_speed),
                                   //         Endschalter A3 + Trommel-Verriegelung (sleeve_switch),
                                   //         Referenzfahrt erst Linearachsen, dann Trommel,
                                   //         EEPROM-Params v3 übernehmen die Werte aus v2
                                   // v0.4.0: Auswurf-Schritte 9/10 (Kippe vom Stutzen zurück in
                                   //         die Trommel drücken) + Safety-Timeout Presse-Rückfahrt
                                   // v0.3.3: Stepper im Leerlauf stromlos (Halteström/Wärme sparen)
                                   // v0.3.2: press_fwd_timeout_ms bis 15000 ms
                                   // v0.3.1: Solenoid Dauer-ON deaktiviert (Magnet-Schutz)
                                   // v0.3:   EEPROM-Params, kooperative State-Machine, Background-Hopper
#endif

// --- Sicherheit / Limits ---
// Watchdog greift nur im Mode IDLE; bei laufender Sequenz "füttert" sich der
// Nano selbst. Sonst würde stuff/home nach 5 s gekillt.
constexpr unsigned long WATCHDOG_TIMEOUT_MS = 5000;

// Solenoid-Hardlimit: Heschen HS-0530B ist NICHT für Dauer-ON ausgelegt.
constexpr unsigned long SOLENOID_PULSE_MAX_MS = 1000;

// Manueller Hopper-Test (run-Befehl) — Background-Cycle ist davon unabhängig.
constexpr unsigned long HOPPER_RUN_MAX_MS = 4000;

// Sicherheits-Reserve für die zeitgesteuerte Presse-Rückfahrt: läuft der Motor
// länger als press_rev_ms + diese Reserve, wird hart gestoppt und ein Fehler
// gesetzt (statt endlos gegen den Anschlag zu drücken).
constexpr unsigned long PRESS_REV_SAFETY_MARGIN_MS = 2000;

// --- Schrittmotor (Hardware-Limits, nicht Aufgabe) ---
constexpr int   STEPPER_STEPS_PER_REV = 200;
constexpr float STEPPER_MAX_SPEED     = 800.0f;
constexpr float STEPPER_ACCEL         = 1500.0f;
constexpr float STEPPER_HOME_SPEED    = 300.0f;   // langsamer beim Referenzieren

// --- Sensor-Logik ---
// NPN-Initiatoren ziehen bei Detektion nach LOW.
constexpr bool INIT_TRIGGERED_LEVEL = LOW;
// Gabellichtschranke an der Trommel: Flagge blockt Licht → DO HIGH.
constexpr bool MAGAZIN_TRIGGERED_LEVEL = HIGH;

// --- Servo (Hülsen-Schieber) ---
// Die Firmware fährt den Sollwinkel als Rampe mit params.servo_speed (°/s).
// Der Servo hängt der Rampe etwas hinterher → nach Rampen-Ende noch kurz
// nachlaufen lassen. Ohne Rampe (servo_speed = 0) springt der Sollwinkel,
// dann gilt die volle Reisezeit. Hardware-Eigenschaften, keine Tuning-Parameter.
constexpr unsigned long SERVO_SETTLE_MS     = 150;
constexpr unsigned long SERVO_MOVE_DELAY_MS = 500;

// --- Hülsen-Schieber-Endschalter (A3) ---
// Schalter gedrückt (Schieber in Home) → LOW.
constexpr bool SLEEVE_HOME_TRIGGERED_LEVEL = LOW;
// So lange darf der Schalter nach Rampen-Ende auf sich warten lassen, sonst
// Fehler sleeve_home_timeout (Schieber klemmt oder servo_home falsch).
constexpr unsigned long SLEEVE_HOME_TIMEOUT_MS = 1000;
