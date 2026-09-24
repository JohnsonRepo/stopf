// =====================================================
// params.cpp
// EEPROM-Persistenz + Name-basierter Zugriff
// =====================================================
#include "params.h"
#include <EEPROM.h>
#include <stddef.h>   // offsetof

Params params;

enum ParamType : uint8_t { PT_U8, PT_U16 };

struct ParamDesc {
    const char* name;
    ParamType   type;
    uint16_t    offset;
    uint16_t    minVal;
    uint16_t    maxVal;
};

// Eine Tabelle, eine Wahrheit. Reihenfolge muss nicht mit Struct übereinstimmen.
static const ParamDesc PARAM_TABLE[] = {
    { "drum_steps_per_pos",    PT_U16, offsetof(Params, drum_steps_per_pos),    1,   10000 },
    { "home_drum_timeout_ms",  PT_U16, offsetof(Params, home_drum_timeout_ms),  100, 60000 },
    { "servo_home",            PT_U8,  offsetof(Params, servo_home),            0,   180   },
    { "servo_load",            PT_U8,  offsetof(Params, servo_load),            0,   180   },
    { "servo_speed",           PT_U16, offsetof(Params, servo_speed),           0,   1000  },
    { "sleeve_switch",         PT_U8,  offsetof(Params, sleeve_switch),         0,   1     },
    { "knock_on_ms",           PT_U16, offsetof(Params, knock_on_ms),           1,   1000  },
    { "knock_off_ms",          PT_U16, offsetof(Params, knock_off_ms),          1,   2000  },
    { "knock_cycles",          PT_U8,  offsetof(Params, knock_cycles),          1,   50    },
    { "hopper_on_ms",          PT_U16, offsetof(Params, hopper_on_ms),          100, 60000 },
    { "hopper_off_ms",         PT_U16, offsetof(Params, hopper_off_ms),         100, 60000 },
    { "press_rev_ms",          PT_U16, offsetof(Params, press_rev_ms),          50,  10000 },
    { "press_fwd_timeout_ms",  PT_U16, offsetof(Params, press_fwd_timeout_ms),  100, 15000 },
    { "press_pwm",             PT_U8,  offsetof(Params, press_pwm),             60,  255   },
    { "pusher_fwd_timeout_ms", PT_U16, offsetof(Params, pusher_fwd_timeout_ms), 100, 10000 },
    { "pusher_rev_timeout_ms", PT_U16, offsetof(Params, pusher_rev_timeout_ms), 100, 10000 },
    { "pusher_pwm",            PT_U8,  offsetof(Params, pusher_pwm),            60,  255   },
    { "eject_fwd_ms",          PT_U16, offsetof(Params, eject_fwd_ms),          50,  5000  },
    { "sol1_dwell_ms",         PT_U16, offsetof(Params, sol1_dwell_ms),         1,   1000  },
    { "sol2_dwell_ms",         PT_U16, offsetof(Params, sol2_dwell_ms),         1,   1000  },
    { "step_delay_ms",         PT_U16, offsetof(Params, step_delay_ms),         0,   10000 },
};
static const uint8_t PARAM_COUNT = sizeof(PARAM_TABLE) / sizeof(ParamDesc);

// EEPROM-Layout v2 (Firmware 0.4.x). Nur noch zum Übernehmen der alten Werte
// beim ersten Boot mit v3 — NICHT ändern.
struct ParamsV2 {
    uint16_t magic;
    uint8_t  version;
    uint16_t drum_steps_per_pos;
    uint16_t home_drum_timeout_ms;
    uint8_t  servo_home;
    uint8_t  servo_load;
    uint16_t knock_on_ms;
    uint16_t knock_off_ms;
    uint8_t  knock_cycles;
    uint16_t hopper_on_ms;
    uint16_t hopper_off_ms;
    uint16_t press_rev_ms;
    uint16_t press_fwd_timeout_ms;
    uint8_t  press_pwm;
    uint16_t pusher_fwd_timeout_ms;
    uint16_t pusher_rev_timeout_ms;
    uint8_t  pusher_pwm;
    uint16_t eject_fwd_ms;
    uint16_t sol1_dwell_ms;
    uint16_t sol2_dwell_ms;
    uint16_t step_delay_ms;
    uint8_t  crc;
};
#if defined(__AVR__)   // AVR packt ohne Padding-Bytes → 37 Bytes wie im EEPROM
static_assert(sizeof(ParamsV2) == 37, "ParamsV2 muss exakt dem EEPROM-Layout v2 entsprechen");
#endif

// XOR über alle Bytes außer dem abschließenden crc-Byte.
static uint8_t xorCrc(const void* data, size_t sizeWithCrc) {
    const uint8_t* p = (const uint8_t*)data;
    uint8_t c = 0;
    for (size_t i = 0; i + 1 < sizeWithCrc; i++) c ^= p[i];
    return c;
}

static uint8_t computeCrc() {
    return xorCrc(&params, sizeof(Params));
}

void paramsLoadDefaults() {
    params.magic                  = PARAMS_MAGIC;
    params.version                = PARAMS_VERSION;
    params.drum_steps_per_pos     = 200;
    params.home_drum_timeout_ms   = 5000;
    params.servo_home             = 5;     // bewusst kleiner Schwenk: passt auch zur alten
    params.servo_load             = 85;    // Hebel-Mechanik. Für die Zahnstange kalibrieren.
    params.servo_speed            = 150;   // °/s → bei Ritzel Ø24 ca. 31 mm/s
    params.sleeve_switch          = 1;     // Verriegelung an; ohne verbauten Schalter auf 0
    params.knock_on_ms            = 80;
    params.knock_off_ms           = 120;
    params.knock_cycles           = 8;
    params.hopper_on_ms           = 20000;
    params.hopper_off_ms          = 10000;
    params.press_rev_ms           = 800;
    params.press_fwd_timeout_ms   = 4000;
    params.press_pwm              = 200;
    params.pusher_fwd_timeout_ms  = 4000;
    params.pusher_rev_timeout_ms  = 4000;
    params.pusher_pwm             = 220;
    params.eject_fwd_ms           = 400;
    params.sol1_dwell_ms          = 80;
    params.sol2_dwell_ms          = 80;
    params.step_delay_ms          = 500;
    params.crc                    = 0;   // wird in paramsSave() gesetzt
}

void paramsSave() {
    params.magic   = PARAMS_MAGIC;
    params.version = PARAMS_VERSION;
    params.crc     = computeCrc();
    EEPROM.put(0, params);
}

// v2 → v3: alle bisherigen (getunten) Werte übernehmen, nur die neuen Felder
// bekommen Defaults. Ohne das wären nach dem Flashen alle Einstellungen weg.
static bool migrateFromV2() {
    ParamsV2 old;
    EEPROM.get(0, old);
    if (old.magic != PARAMS_MAGIC || old.version != 2 ||
        old.crc != xorCrc(&old, sizeof(ParamsV2))) {
        return false;
    }
    paramsLoadDefaults();
    params.drum_steps_per_pos    = old.drum_steps_per_pos;
    params.home_drum_timeout_ms  = old.home_drum_timeout_ms;
    params.servo_home            = old.servo_home;
    params.servo_load            = old.servo_load;
    params.knock_on_ms           = old.knock_on_ms;
    params.knock_off_ms          = old.knock_off_ms;
    params.knock_cycles          = old.knock_cycles;
    params.hopper_on_ms          = old.hopper_on_ms;
    params.hopper_off_ms         = old.hopper_off_ms;
    params.press_rev_ms          = old.press_rev_ms;
    params.press_fwd_timeout_ms  = old.press_fwd_timeout_ms;
    params.press_pwm             = old.press_pwm;
    params.pusher_fwd_timeout_ms = old.pusher_fwd_timeout_ms;
    params.pusher_rev_timeout_ms = old.pusher_rev_timeout_ms;
    params.pusher_pwm            = old.pusher_pwm;
    params.eject_fwd_ms          = old.eject_fwd_ms;
    params.sol1_dwell_ms         = old.sol1_dwell_ms;
    params.sol2_dwell_ms         = old.sol2_dwell_ms;
    params.step_delay_ms         = old.step_delay_ms;
    paramsSave();
    return true;
}

void paramsBegin() {
    EEPROM.get(0, params);
    if (params.magic   == PARAMS_MAGIC &&
        params.version == PARAMS_VERSION &&
        params.crc     == computeCrc()) {
        return;
    }
    if (!migrateFromV2()) {
        paramsLoadDefaults();
        paramsSave();
    }
}

static const ParamDesc* findParam(const String& key) {
    for (uint8_t i = 0; i < PARAM_COUNT; i++) {
        if (key == PARAM_TABLE[i].name) return &PARAM_TABLE[i];
    }
    return nullptr;
}

bool paramsSetByName(const String& key, long value, const char*& errOut) {
    const ParamDesc* d = findParam(key);
    if (!d) { errOut = "unknown"; return false; }
    if (value < (long)d->minVal || value > (long)d->maxVal) {
        errOut = "range";
        return false;
    }
    uint8_t* base = (uint8_t*)&params;
    if (d->type == PT_U8) {
        *(uint8_t*)(base + d->offset) = (uint8_t)value;
    } else {
        *(uint16_t*)(base + d->offset) = (uint16_t)value;
    }
    paramsSave();
    return true;
}

bool paramsGetByName(const String& key, long& valueOut) {
    const ParamDesc* d = findParam(key);
    if (!d) return false;
    const uint8_t* base = (const uint8_t*)&params;
    if (d->type == PT_U8) {
        valueOut = *(const uint8_t*)(base + d->offset);
    } else {
        valueOut = *(const uint16_t*)(base + d->offset);
    }
    return true;
}

void paramsPrintAll() {
    Serial.print(F("ok params"));
    for (uint8_t i = 0; i < PARAM_COUNT; i++) {
        const ParamDesc& d = PARAM_TABLE[i];
        long v = 0;
        const uint8_t* base = (const uint8_t*)&params;
        if (d.type == PT_U8) v = *(const uint8_t*)(base + d.offset);
        else                 v = *(const uint16_t*)(base + d.offset);
        Serial.print(' ');
        Serial.print(d.name);
        Serial.print('=');
        Serial.print(v);
    }
    Serial.println();
}
