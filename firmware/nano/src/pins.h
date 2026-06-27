// =====================================================
// pins.h
// Zentrale Pin-Belegung für Arduino Nano
// Stopfmaschine v0.2
// =====================================================
#pragma once

// --- A4988 (Schrittmotor / Trommelmagazin-Antrieb) ---
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

// --- Servo (Hülsen-Schieber) ---
constexpr uint8_t PIN_SERVO       = 11;

// --- Start-Taster (mechanischer Drucktaster, momentary) ---
// Verdrahtung: Taster zwischen D12 und GND.
// Interner Pull-up im Nano aktiviert → ungedrückt = HIGH, gedrückt = LOW.
// Kein externer Widerstand nötig.
constexpr uint8_t PIN_BUTTON      = 12;

// --- Solenoid-Treiber (Tabak-Knocking) ---
// HINWEIS: Das L298N-Mini-Modul hat die Dauer-/Halteströme der Solenoide NICHT
// überlebt → Solenoide laufen jetzt an einem zweiten Standard-L298N (#2).
// Steuerung unverändert: IN1/IN3 toggeln, IN2/IN4 hardwired GND, ENA/ENB per
// Jumper dauerhaft HIGH (Solenoide brauchen nur EIN/AUS).
// D13 war onboard Status-LED, jetzt Solenoid #2 (Top-Druck).
//
// EMPFOHLENE MIGRATION (sauberer + thermisch unkritisch): beide Solenoide auf
// ein Logic-Level-MOSFET-Board legen — siehe docs/mosfet-driver.md. Pin-Namen
// bleiben dann gleich (PIN_SOL_FRONT/PIN_SOL_TOP gehen direkt aufs MOSFET-Gate).
constexpr uint8_t PIN_SOL_TOP     = 13;   // L298N #2 IN3 (bzw. MOSFET-Gate) → Heschen HS-0530B Top-Druck

// --- Initiatoren (induktive Näherungssensoren über Spannungsteiler) ---
// Hinweis: 12V Sensorsignal über 10kΩ + 7,5kΩ Spannungsteiler auf 5V
constexpr uint8_t PIN_INIT_PRESS      = A0;
constexpr uint8_t PIN_INIT_PUSH_FRONT = A1;
constexpr uint8_t PIN_INIT_PUSH_REAR  = A2;

// --- Tabak-Dosierung (Tilt-Schwenkwand + 2 Solenoide) ---
// Mechanismus aus Fraens' vollautomatischer Variante:
//   - Tabak-Servo schwenkt Tilt-Wand vor/zurück
//   - 2× Heschen HS-0530B Hubmagnete pulsieren (Front-Knock + Top-Druck)
//   - Treiber: Standard-L298N #2 (Mini-Modul ausgefallen) bzw. MOSFET-Board
//     (siehe docs/mosfet-driver.md)
constexpr uint8_t PIN_TABAK_SERVO  = A3;  // Servo-Lib läuft auch auf Analog-Pins
constexpr uint8_t PIN_SOL_FRONT    = A4;  // → L298N #2 IN1 (bzw. MOSFET-Gate) (Front-Knock)

// --- 3. DC-Motor (unidirektional, NEU) ---
// Läuft nur in EINE Richtung → keine H-Brücke nötig, ein einzelner
// Logic-Level-MOSFET (z. B. IRLZ44N) reicht. Treiber-Details + Pin-Frage
// (der Nano hat KEINEN freien PWM-Pin mehr!) siehe docs/mosfet-driver.md.
// Auf dem Nano daher nur als EIN/AUS über A5 möglich (Magazin-Sensor müsste
// dafür weichen); echte Drehzahl-Regelung (PWM) → ESP32. Bewusst noch KEIN
// Pin fest vergeben, bis Controller/Modus entschieden sind.

// --- Magazin-Lichtschranke (Gabellichtschranke, direkt 5V-Logik) ---
constexpr uint8_t PIN_MAGAZIN_SENSOR = A5;
