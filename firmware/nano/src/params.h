// =====================================================
// params.h
// Live-tunbare Maschinenparameter, persistiert im EEPROM.
//
// Versionierter Struct mit Magic + CRC. Wenn beim Boot Magic
// oder CRC nicht stimmen → Defaults schreiben (self-healing
// nach erstem Flash, nach Struct-Änderungen, oder nach EEPROM-
// Korruption).
//
// App ändert per "set <key> <val>"; Nano antwortet "ok <k>=<v>"
// oder "err range:<min>..<max>".
// =====================================================
#pragma once

#include <Arduino.h>

constexpr uint16_t PARAMS_MAGIC   = 0xC51F;   // "Stopfmaschine" Marker
constexpr uint8_t  PARAMS_VERSION = 1;

struct Params {
    uint16_t magic;
    uint8_t  version;

    // Trommel (Stepper)
    uint16_t drum_steps_per_pos;     // Schritte pro Hülsenposition
    uint16_t home_drum_timeout_ms;   // Watchdog: Lichtschranke muss bis dann triggern

    // Servo (Hülsen-Schieber, D11)
    uint8_t  servo_home;             // 0..180°
    uint8_t  servo_load;             // 0..180°

    // Knock (beide Solenoide synchron)
    uint16_t knock_on_ms;            // Pulsdauer pro Schlag
    uint16_t knock_off_ms;           // Pause zwischen Schlägen
    uint8_t  knock_cycles;           // Anzahl Schläge pro Knock-Step

    // Hopper-Background (zyklischer 5V-Motor)
    uint16_t hopper_on_ms;           // Default 20000
    uint16_t hopper_off_ms;          // Default 10000

    // Presse
    uint16_t press_rev_ms;           // Rücklauf rein zeitgesteuert
    uint16_t press_fwd_timeout_ms;   // Vorlauf hat A0-Sensor, Timeout als Safety
    uint8_t  press_pwm;              // 0..255, ENA Duty Cycle

    // Pusher (beidseitig sensorgesteuert)
    uint16_t pusher_fwd_timeout_ms;  // bis A1 (Front)
    uint16_t pusher_rev_timeout_ms;  // bis A2 (Rear)
    uint8_t  pusher_pwm;             // 0..255, ENB Duty Cycle

    // Solenoide einzeln (Manual-Mode pulse-Defaultwerte)
    uint16_t sol1_dwell_ms;
    uint16_t sol2_dwell_ms;

    // Pause zwischen Stuff-Zyklen
    uint16_t step_delay_ms;

    uint8_t  crc;
};

extern Params params;

// Beim Boot aufrufen: lädt aus EEPROM oder schreibt Defaults.
void paramsBegin();

// Schreibt aktuelle Werte zurück ins EEPROM (mit frischer CRC).
void paramsSave();

// Setzt Defaults im RAM (nicht persistiert — Caller muss paramsSave()).
void paramsLoadDefaults();

// Setzt einen Wert per Name. Validiert Range. Persistiert sofort wenn ok.
// Rückgabe: true bei Erfolg, false bei unbekanntem Key / Range-Fehler.
// Bei false: errOut bekommt einen kurzen Grund (z.B. "range" oder "unknown").
bool paramsSetByName(const String& key, long value, const char*& errOut);

// Holt einen Wert per Name als long. Rückgabe: true bei Erfolg.
bool paramsGetByName(const String& key, long& valueOut);

// Gibt alle Parameter als "key=value" Liste auf Serial aus.
void paramsPrintAll();
