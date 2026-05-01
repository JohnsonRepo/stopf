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

// --- L298N (DC-Motoren: Presse + Pusher) ---
constexpr uint8_t PIN_PRESS_IN1   = 5;
constexpr uint8_t PIN_PRESS_IN2   = 6;
constexpr uint8_t PIN_PUSHER_IN3  = 7;
constexpr uint8_t PIN_PUSHER_IN4  = 8;
constexpr uint8_t PIN_PRESS_ENA   = 9;    // PWM
constexpr uint8_t PIN_PUSHER_ENB  = 10;   // PWM

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
