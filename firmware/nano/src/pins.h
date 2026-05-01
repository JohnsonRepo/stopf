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

// --- L298N Mini-Modul (DC-Motoren: Presse + Pusher) ---
// HINWEIS: Verwendetes Modul hat KEIN ENA/ENB (intern auf "always enabled" verdrahtet).
// Drehzahl-Regelung läuft daher via PWM direkt auf dem aktiven IN-Pin
// ("sign-magnitude PWM"). Vorwärts = PWM auf IN1/IN3, Rückwärts = digital HIGH
// auf IN2/IN4 (volle Drehzahl, da Retraction in der Stopfsequenz unkritisch).
//
// Pin-Wahl: PRESS_IN1 und PUSHER_IN3 müssen PWM-fähig sein (Timer0: D5, D6).
// Servo nutzt Timer1 → D9/D10 PWM ist blockiert → daher Pusher NICHT auf D9/D10.
//
//   D5 (Timer0 PWM) ──► L298N IN1   (Presse FWD, drehzahlgeregelt)
//   D7              ──► L298N IN2   (Presse REV, volle Drehzahl)
//   D6 (Timer0 PWM) ──► L298N IN3   (Pusher FWD, drehzahlgeregelt)
//   D8              ──► L298N IN4   (Pusher REV, volle Drehzahl)
constexpr uint8_t PIN_PRESS_IN1   = 5;    // PWM (forward, Timer0)
constexpr uint8_t PIN_PRESS_IN2   = 7;    // digital (reverse)
constexpr uint8_t PIN_PUSHER_IN3  = 6;    // PWM (forward, Timer0)
constexpr uint8_t PIN_PUSHER_IN4  = 8;    // digital (reverse)
// D9, D10 sind frei (entfallen ENA/ENB) — Reserve für I²C-Display, Endschalter, etc.

// --- Servo (Hülsen-Schieber) ---
constexpr uint8_t PIN_SERVO       = 11;

// --- Touch-Button (Start) ---
constexpr uint8_t PIN_TOUCH       = 12;

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
