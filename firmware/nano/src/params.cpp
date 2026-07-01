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
    { "sol1_dwell_ms",         PT_U16, offsetof(Params, sol1_dwell_ms),         1,   1000  },
    { "sol2_dwell_ms",         PT_U16, offsetof(Params, sol2_dwell_ms),         1,   1000  },
    { "step_delay_ms",         PT_U16, offsetof(Params, step_delay_ms),         0,   10000 },
};
static const uint8_t PARAM_COUNT = sizeof(PARAM_TABLE) / sizeof(ParamDesc);

static uint8_t computeCrc() {
    const uint8_t* p = (const uint8_t*)&params;
    uint8_t c = 0;
    size_t n = sizeof(Params) - 1;   // crc-Byte selbst auslassen
    for (size_t i = 0; i < n; i++) c ^= p[i];
    return c;
}

void paramsLoadDefaults() {
    params.magic                  = PARAMS_MAGIC;
    params.version                = PARAMS_VERSION;
    params.drum_steps_per_pos     = 200;
    params.home_drum_timeout_ms   = 5000;
    params.servo_home             = 5;
    params.servo_load             = 85;
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

void paramsBegin() {
    EEPROM.get(0, params);
    if (params.magic   != PARAMS_MAGIC ||
        params.version != PARAMS_VERSION ||
        params.crc     != computeCrc()) {
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
