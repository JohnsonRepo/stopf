// =====================================================
// pins.h
// Zentrale Pin-Belegung für Arduino Nano
// Stopfmaschine v0.1
// =====================================================
#pragma once

// --- A4988 (Schrittmotor / Förderschnecke) ---
constexpr uint8_t PIN_STEPPER_STEP = 2;
constexpr uint8_t PIN_STEPPER_DIR  = 3;
constexpr uint8_t PIN_STEPPER_EN   = 4;   // EN ist invertiert: LOW = aktiv

// --- L298N Standard-Modul (DC-Motoren: Presse + Pusher) ---
// Großes Modul mit Kühlkörper, Schraubklemmen und ENA/ENB.
// Drehzahl-Regelung über separate Enable-Pins (echtes PWM in beide Richtungen).
//
// WICHTIG (Timer-Konflikt): Servo.h belegt auf dem ATmega328 Timer1 und
// deaktiviert damit PWM (analogWrite) auf D9/D10. ENA/ENB MÜSSEN deshalb auf
// Timer0-PWM-Pins (D5/D6) liegen. Die IN-Pins sind reine digitale
// Richtungspins — die dürfen auf D7–D10 (kein PWM nötig).
//
//   D5  ──► L298N ENA  (PWM Timer0, Presse Drehzahl)
//   D6  ──► L298N ENB  (PWM Timer0, Pusher Drehzahl)
//   D7  ──► L298N IN1  (Presse Richtung A, digital)
//   D8  ──► L298N IN2  (Presse Richtung B, digital)
//   D9  ──► L298N IN3  (Pusher Richtung A, digital)
//   D10 ──► L298N IN4  (Pusher Richtung B, digital)
constexpr uint8_t PIN_PRESS_ENA   = 5;    // PWM (Timer0, Servo-unabhängig)
constexpr uint8_t PIN_PUSHER_ENB  = 6;    // PWM (Timer0, Servo-unabhängig)
constexpr uint8_t PIN_PRESS_IN1   = 7;    // digital
constexpr uint8_t PIN_PRESS_IN2   = 8;    // digital
constexpr uint8_t PIN_PUSHER_IN3  = 9;    // digital (Servo killt hier nur PWM)
constexpr uint8_t PIN_PUSHER_IN4  = 10;   // digital

// --- Servo Hülsen-Schieber ---
constexpr uint8_t PIN_SERVO          = 11;

// --- Hülsenmagazin-Motor (kleiner DC-Motor, 5 V, ~40 mA) ---
// Verdrahtung: Nano D12 → 1 kΩ → Gate eines kleinen N-MOSFETs (2N7000 / IRLZ44N).
// Motor zwischen 5V-Bus und Drain. Source an GND. 1N4148 als Flyback-Diode
// parallel zum Motor (Kathode an +5V). Nano-Pin direkt würde 40 mA grenzwertig
// belasten — MOSFET-Treiber ist sicherer.
// Steuerung: digital ON/OFF (D12 ist nicht PWM-fähig; Vibrationsmotor braucht
// keine Drehzahl-Regelung).
constexpr uint8_t PIN_HOPPER_MOTOR   = 12;

// --- Hubmagnet #2 (Top-Druck, Tabak-Dosierung) ---
// Verdrahtung: Nano D13 → 100 Ω → Gate eines IRLZ44N (Logic-Level-MOSFET).
// Solenoid zwischen 12V-Bus und Drain. Source an GND. 1N5819 Flyback parallel
// zum Solenoid (Kathode an +12V).
// L298N-Mini wurde verworfen: ~2,5 V Spannungsabfall + Wärme bei Halteströmen.
// MOSFET: < 20 mV Drop, kein Wärmeproblem, Solenoid sieht volle 12 V.
constexpr uint8_t PIN_SOLENOID_2     = 13;

// --- Initiatoren (induktive Näherungssensoren über Spannungsteiler) ---
// Hinweis: 12V Sensorsignal über 10kΩ + 7,5kΩ Spannungsteiler auf 5V
constexpr uint8_t PIN_INIT_PRESS      = A0;
constexpr uint8_t PIN_INIT_PUSH_FRONT = A1;
constexpr uint8_t PIN_INIT_PUSH_REAR  = A2;

// --- Tabak-Dosierung (Tilt-Schwenkwand + 2 Solenoide via MOSFETs) ---
// Mechanismus aus Fraens' vollautomatischer Variante:
//   - Tabak-Servo (Mini-Servo) schwenkt eine Tilt-Wand vor/zurück
//   - 2× Heschen HS-0530B Hubmagnete pulsieren (Front-Knock + Top-Druck)
//   - Pro Solenoid: 1× IRLZ44N MOSFET + 1× 1N5819 Flyback-Diode
//   - Solenoid #2 siehe oben (D13), Solenoid #1 hier:
constexpr uint8_t PIN_TABAK_SERVO    = A3;  // Servo-Lib läuft auf Analog-Pins
constexpr uint8_t PIN_SOLENOID_1     = A4;  // → MOSFET → Heschen HS-0530B (Front-Knock)

// --- Magazin-Lichtschranke (Trommel-Index) ---
constexpr uint8_t PIN_MAGAZIN_SENSOR = A5;  // Gabellichtschranke, direkt 5 V-Logik

// === Steuerung ist komplett remote-only (Pi → Serial → Nano). ===
// Manueller Start-Taster entfällt — kein physischer Pin reserviert.
