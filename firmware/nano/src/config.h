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
#define FIRMWARE_VERSION "0.3.3"   // v0.3.3: Stepper im Leerlauf stromlos (Halteström/Wärme sparen)
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

// --- Servo ---
// Bewegungs-"Reisezeit": Servo bekommt write(), wir warten kooperativ,
// bis er angekommen ist. Hardware-Eigenschaft, kein Tuning-Parameter.
constexpr unsigned long SERVO_MOVE_DELAY_MS = 500;
