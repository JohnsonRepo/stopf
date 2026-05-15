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

// --- Servo (Hülsen-Schieber) ---
constexpr uint8_t PIN_SERVO       = 11;

// --- Start-Taster (mechanischer Drucktaster, momentary) ---
// Verdrahtung: Taster zwischen D12 und GND.
// Interner Pull-up im Nano aktiviert → ungedrückt = HIGH, gedrückt = LOW.
// Kein externer Widerstand nötig.
constexpr uint8_t PIN_BUTTON      = 12;

// --- Status-LED (interne LED auf D13) ---
constexpr uint8_t PIN_STATUS_LED  = 13;

// --- Initiatoren (induktive Näherungssensoren über Spannungsteiler) ---
// Hinweis: 12V Sensorsignal über 10kΩ + 7,5kΩ Spannungsteiler auf 5V
constexpr uint8_t PIN_INIT_PRESS      = A0;
constexpr uint8_t PIN_INIT_PUSH_FRONT = A1;
constexpr uint8_t PIN_INIT_PUSH_REAR  = A2;

// --- Reserve ---
constexpr uint8_t PIN_RESERVE_A3      = A3;
constexpr uint8_t PIN_RESERVE_A4      = A4;
constexpr uint8_t PIN_MAGAZIN_SENSOR  = A5;  // für später (Hülsenmagazin)
