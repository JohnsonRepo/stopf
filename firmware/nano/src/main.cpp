// =====================================================
// main.cpp
// Stopfmaschine - Arduino Nano Firmware v0.3.0
//
// Architektur:
//   - Live-tunbare Parameter im EEPROM (params.h/cpp)
//   - Kooperative State-Machine (home / stuff / step / idle / error)
//   - Background-Hopper-Cycle parallel zur Hauptsequenz
//   - Alle Sequenz-Befehle non-blocking — `stop` greift sofort
//
// Befehle (115200 Baud):
//   help                     - Liste
//   ping                     - "pong"
//   status                   - state + sensoren + aktoren als key=value
//   params                   - alle EEPROM-Parameter
//   get <key>                - einzelner Parameter
//   set <key> <value>        - Parameter setzen (validiert + persistiert)
//   home                     - Referenzfahrt (Trommel → Lichtschranke, Pusher → A2)
//   stuff                    - Vollsequenz, läuft endlos bis `stop`
//   step <n>                 - Einzelschritt (1..9 = Stuff-Steps)
//   stop                     - Notaus, alles aus, Mode → IDLE
//
//   --- Manual (nur erlaubt wenn state=idle) ---
//   stepper <steps>          - relative Stepper-Bewegung
//   press fwd|rev|stop       - DC-Motor Presse (PWM aus params.press_pwm)
//   pusher fwd|rev|stop      - DC-Motor Pusher (PWM aus params.pusher_pwm)
//   servo <0..180>           - Hülsen-Schieber-Servo
//   solenoid 1|2 off|pulse <ms>   (Dauer-ON deaktiviert — Magnet-Schutz)
//   hopper on|off|test <ms>  - on = Background-Cycle, test = einmaliger Run
//   knock [<cycles>]         - läuft als Step (kann via stop abgebrochen werden)
// =====================================================

#include <Arduino.h>
#include <AccelStepper.h>
#include <Servo.h>
#include "pins.h"
#include "config.h"
#include "params.h"

// --- Hardware ---
AccelStepper stepper(AccelStepper::DRIVER, PIN_STEPPER_STEP, PIN_STEPPER_DIR);
Servo        tubeServo;

// --- Watchdog ---
unsigned long lastCommandMs = 0;
bool          watchdogTripped = false;

// --- State-Machine ---
enum Mode : uint8_t {
    MODE_IDLE     = 0,
    MODE_HOMING   = 1,
    MODE_STUFFING = 2,
    MODE_STEP     = 3,
    MODE_ERROR    = 4
};

// Stuff steps 1..9, Home steps 101..104
constexpr uint8_t STEP_DRUM       = 1;
constexpr uint8_t STEP_SERVO_LOAD = 2;
constexpr uint8_t STEP_SERVO_HOME = 3;
constexpr uint8_t STEP_KNOCK      = 4;
constexpr uint8_t STEP_PRESS_FWD  = 5;
constexpr uint8_t STEP_PRESS_REV  = 6;
constexpr uint8_t STEP_PUSH_FWD   = 7;
constexpr uint8_t STEP_PUSH_REV   = 8;
constexpr uint8_t STEP_DELAY      = 9;
constexpr uint8_t STUFF_STEP_MIN  = 1;
constexpr uint8_t STUFF_STEP_MAX  = 9;

constexpr uint8_t HOME_DRUM      = 101;
constexpr uint8_t HOME_PUSH_REV  = 102;
constexpr uint8_t HOME_SERVO     = 103;
constexpr uint8_t HOME_PRESS_REV = 104;
constexpr uint8_t HOME_DONE      = 105;

Mode          currentMode    = MODE_IDLE;
uint8_t       currentStep    = 0;
unsigned long stepStartedMs  = 0;
char          errorMsg[24]   = "";

// Knock-Sub-State (innerhalb STEP_KNOCK)
uint8_t       knockCounter      = 0;
bool          knockPhaseOn      = false;
unsigned long knockPhaseStartMs = 0;
uint8_t       knockTargetCycles = 0;  // für Manual-Knock mit eigener Cycle-Zahl

// Hopper-Background
bool          hopperEnabled      = false;
unsigned long hopperCycleStartMs = 0;
unsigned long hopperManualUntil  = 0;  // für `hopper test <ms>` (Manual)

// =====================================================
// Hardware-Helpers
// =====================================================

static void allMotorsOff() {
    digitalWrite(PIN_STEPPER_EN, HIGH);
    digitalWrite(PIN_PRESS_IN1, LOW);
    digitalWrite(PIN_PRESS_IN2, LOW);
    digitalWrite(PIN_PUSHER_IN3, LOW);
    digitalWrite(PIN_PUSHER_IN4, LOW);
    analogWrite(PIN_PRESS_ENA, 0);
    analogWrite(PIN_PUSHER_ENB, 0);
    digitalWrite(PIN_SOLENOID_1, LOW);
    digitalWrite(PIN_SOLENOID_2, LOW);
    digitalWrite(PIN_HOPPER_MOTOR, LOW);
}

static void enableStepper() { digitalWrite(PIN_STEPPER_EN, LOW); }

static void pressDrive(const char* dir) {
    if (strcmp(dir, "fwd") == 0) {
        digitalWrite(PIN_PRESS_IN1, HIGH);
        digitalWrite(PIN_PRESS_IN2, LOW);
        analogWrite(PIN_PRESS_ENA, params.press_pwm);
    } else if (strcmp(dir, "rev") == 0) {
        digitalWrite(PIN_PRESS_IN1, LOW);
        digitalWrite(PIN_PRESS_IN2, HIGH);
        analogWrite(PIN_PRESS_ENA, params.press_pwm);
    } else {
        digitalWrite(PIN_PRESS_IN1, LOW);
        digitalWrite(PIN_PRESS_IN2, LOW);
        analogWrite(PIN_PRESS_ENA, 0);
    }
}

static void pusherDrive(const char* dir) {
    if (strcmp(dir, "fwd") == 0) {
        digitalWrite(PIN_PUSHER_IN3, HIGH);
        digitalWrite(PIN_PUSHER_IN4, LOW);
        analogWrite(PIN_PUSHER_ENB, params.pusher_pwm);
    } else if (strcmp(dir, "rev") == 0) {
        digitalWrite(PIN_PUSHER_IN3, LOW);
        digitalWrite(PIN_PUSHER_IN4, HIGH);
        analogWrite(PIN_PUSHER_ENB, params.pusher_pwm);
    } else {
        digitalWrite(PIN_PUSHER_IN3, LOW);
        digitalWrite(PIN_PUSHER_IN4, LOW);
        analogWrite(PIN_PUSHER_ENB, 0);
    }
}

// =====================================================
// State-Machine
// =====================================================

static void setError(const char* msg) {
    strncpy(errorMsg, msg, sizeof(errorMsg) - 1);
    errorMsg[sizeof(errorMsg) - 1] = '\0';
    currentMode = MODE_ERROR;
    allMotorsOff();
    hopperEnabled = false;
    Serial.print(F("err sequence:")); Serial.println(errorMsg);
}

static void clearError() { errorMsg[0] = '\0'; }

static void enterStep(uint8_t step);

static void advanceStep() {
    if (currentMode == MODE_STEP) {
        // Einzelschritt fertig → zurück zu IDLE
        currentMode = MODE_IDLE;
        currentStep = 0;
        return;
    }
    if (currentMode == MODE_STUFFING) {
        uint8_t next = currentStep + 1;
        if (next > STUFF_STEP_MAX) next = STUFF_STEP_MIN;
        enterStep(next);
        return;
    }
    if (currentMode == MODE_HOMING) {
        switch (currentStep) {
            case HOME_DRUM:      enterStep(HOME_PUSH_REV);  break;
            case HOME_PUSH_REV:  enterStep(HOME_SERVO);     break;
            case HOME_SERVO:     enterStep(HOME_PRESS_REV); break;
            case HOME_PRESS_REV:
                currentMode = MODE_IDLE;
                currentStep = 0;
                Serial.println(F("ok home_done"));
                break;
        }
    }
}

static void enterStep(uint8_t step) {
    currentStep   = step;
    stepStartedMs = millis();

    switch (step) {
        // ----- Stuff steps -----
        case STEP_DRUM:
            enableStepper();
            stepper.setMaxSpeed(STEPPER_MAX_SPEED);
            stepper.move(params.drum_steps_per_pos);
            break;

        case STEP_SERVO_LOAD:
            tubeServo.write(params.servo_load);
            break;

        case STEP_SERVO_HOME:
            tubeServo.write(params.servo_home);
            break;

        case STEP_KNOCK:
            knockCounter      = 0;
            knockPhaseOn      = true;
            knockPhaseStartMs = millis();
            knockTargetCycles = (knockTargetCycles > 0) ? knockTargetCycles : params.knock_cycles;
            digitalWrite(PIN_SOLENOID_1, HIGH);
            digitalWrite(PIN_SOLENOID_2, HIGH);
            break;

        case STEP_PRESS_FWD:
            pressDrive("fwd");
            break;

        case STEP_PRESS_REV:
            pressDrive("rev");
            break;

        case STEP_PUSH_FWD:
            pusherDrive("fwd");
            break;

        case STEP_PUSH_REV:
            pusherDrive("rev");
            break;

        case STEP_DELAY:
            // nichts zu starten, nur warten
            break;

        // ----- Home steps -----
        case HOME_DRUM:
            enableStepper();
            stepper.setMaxSpeed(STEPPER_HOME_SPEED);
            // große Distanz in eine Richtung — wir stoppen über den Sensor
            stepper.move((long)STEPPER_STEPS_PER_REV * 4);
            break;

        case HOME_PUSH_REV:
            pusherDrive("rev");
            break;

        case HOME_SERVO:
            tubeServo.write(params.servo_home);
            break;

        case HOME_PRESS_REV:
            pressDrive("rev");
            break;
    }
}

static void tickKnock() {
    unsigned long now = millis();
    if (knockPhaseOn) {
        if (now - knockPhaseStartMs >= params.knock_on_ms) {
            digitalWrite(PIN_SOLENOID_1, LOW);
            digitalWrite(PIN_SOLENOID_2, LOW);
            knockPhaseOn      = false;
            knockPhaseStartMs = now;
        }
    } else {
        if (now - knockPhaseStartMs >= params.knock_off_ms) {
            knockCounter++;
            if (knockCounter >= knockTargetCycles) {
                knockTargetCycles = 0;  // reset für nächstes Mal
                advanceStep();
                return;
            }
            digitalWrite(PIN_SOLENOID_1, HIGH);
            digitalWrite(PIN_SOLENOID_2, HIGH);
            knockPhaseOn      = true;
            knockPhaseStartMs = now;
        }
    }
}

static void tickStep() {
    unsigned long now = millis();

    switch (currentStep) {
        case STEP_DRUM:
            if (stepper.distanceToGo() == 0) advanceStep();
            break;

        case STEP_SERVO_LOAD:
        case STEP_SERVO_HOME:
        case HOME_SERVO:
            if (now - stepStartedMs >= SERVO_MOVE_DELAY_MS) advanceStep();
            break;

        case STEP_KNOCK:
            tickKnock();
            break;

        case STEP_PRESS_FWD:
            if (digitalRead(PIN_INIT_PRESS) == INIT_TRIGGERED_LEVEL) {
                pressDrive("stop");
                advanceStep();
            } else if (now - stepStartedMs > params.press_fwd_timeout_ms) {
                pressDrive("stop");
                setError("press_fwd_timeout");
            }
            break;

        case STEP_PRESS_REV:
        case HOME_PRESS_REV:
            if (now - stepStartedMs >= params.press_rev_ms) {
                pressDrive("stop");
                advanceStep();
            }
            break;

        case STEP_PUSH_FWD:
            if (digitalRead(PIN_INIT_PUSH_FRONT) == INIT_TRIGGERED_LEVEL) {
                pusherDrive("stop");
                advanceStep();
            } else if (now - stepStartedMs > params.pusher_fwd_timeout_ms) {
                pusherDrive("stop");
                setError("pusher_fwd_timeout");
            }
            break;

        case STEP_PUSH_REV:
        case HOME_PUSH_REV:
            if (digitalRead(PIN_INIT_PUSH_REAR) == INIT_TRIGGERED_LEVEL) {
                pusherDrive("stop");
                advanceStep();
            } else if (now - stepStartedMs > params.pusher_rev_timeout_ms) {
                pusherDrive("stop");
                setError("pusher_rev_timeout");
            }
            break;

        case STEP_DELAY:
            if (now - stepStartedMs >= params.step_delay_ms) advanceStep();
            break;

        case HOME_DRUM:
            if (digitalRead(PIN_MAGAZIN_SENSOR) == MAGAZIN_TRIGGERED_LEVEL) {
                stepper.setCurrentPosition(0);
                stepper.move(0);
                stepper.setMaxSpeed(STEPPER_MAX_SPEED);  // zurück auf normal
                advanceStep();
            } else if (now - stepStartedMs > params.home_drum_timeout_ms) {
                stepper.move(0);
                setError("home_drum_timeout");
            }
            break;
    }
}

static void tickStateMachine() {
    if (currentMode == MODE_IDLE || currentMode == MODE_ERROR) return;
    tickStep();
    // Self-Heartbeat: solange wir arbeiten, frischen Watchdog auf.
    lastCommandMs = millis();
}

// =====================================================
// Background-Hopper-Cycle
// =====================================================

static void tickHopper() {
    unsigned long now = millis();

    // Manueller Einmal-Run hat Vorrang
    if (hopperManualUntil > 0) {
        if ((long)(now - hopperManualUntil) >= 0) {
            digitalWrite(PIN_HOPPER_MOTOR, LOW);
            hopperManualUntil = 0;
        } else {
            digitalWrite(PIN_HOPPER_MOTOR, HIGH);
        }
        return;
    }

    if (!hopperEnabled) {
        digitalWrite(PIN_HOPPER_MOTOR, LOW);
        return;
    }

    unsigned long period = (unsigned long)params.hopper_on_ms + (unsigned long)params.hopper_off_ms;
    if (period == 0) { digitalWrite(PIN_HOPPER_MOTOR, LOW); return; }
    unsigned long t = (now - hopperCycleStartMs) % period;
    bool shouldRun = (t >= params.hopper_off_ms);   // off-Phase zuerst, dann on
    digitalWrite(PIN_HOPPER_MOTOR, shouldRun ? HIGH : LOW);
}

// =====================================================
// Befehle starten
// =====================================================

static void startHome() {
    if (currentMode != MODE_IDLE && currentMode != MODE_ERROR) {
        Serial.println(F("err busy"));
        return;
    }
    clearError();
    currentMode = MODE_HOMING;
    hopperEnabled = false;
    enterStep(HOME_DRUM);
    Serial.println(F("ok homing"));
}

static void startStuff() {
    if (currentMode != MODE_IDLE && currentMode != MODE_ERROR) {
        Serial.println(F("err busy"));
        return;
    }
    clearError();
    currentMode = MODE_STUFFING;
    hopperEnabled = true;
    hopperCycleStartMs = millis();
    enterStep(STEP_DRUM);
    Serial.println(F("ok stuffing"));
}

static void startStep(uint8_t n) {
    if (currentMode != MODE_IDLE && currentMode != MODE_ERROR) {
        Serial.println(F("err busy"));
        return;
    }
    if (n < STUFF_STEP_MIN || n > STUFF_STEP_MAX) {
        Serial.print(F("err step_range:1..")); Serial.println(STUFF_STEP_MAX);
        return;
    }
    clearError();
    currentMode = MODE_STEP;
    enterStep(n);
    Serial.print(F("ok step=")); Serial.println(n);
}

static void doStop() {
    allMotorsOff();
    stepper.stop();
    stepper.move(0);
    stepper.setMaxSpeed(STEPPER_MAX_SPEED);
    knockTargetCycles = 0;
    hopperEnabled = false;
    hopperManualUntil = 0;
    currentMode = MODE_IDLE;
    currentStep = 0;
    clearError();
    Serial.println(F("ok stop"));
}

// =====================================================
// Status / Help
// =====================================================

static const char* modeName(Mode m) {
    switch (m) {
        case MODE_IDLE:     return "idle";
        case MODE_HOMING:   return "homing";
        case MODE_STUFFING: return "stuffing";
        case MODE_STEP:     return "step";
        case MODE_ERROR:    return "error";
    }
    return "?";
}

static void printStatus() {
    bool press     = (digitalRead(PIN_INIT_PRESS)      == INIT_TRIGGERED_LEVEL);
    bool pushFront = (digitalRead(PIN_INIT_PUSH_FRONT) == INIT_TRIGGERED_LEVEL);
    bool pushRear  = (digitalRead(PIN_INIT_PUSH_REAR)  == INIT_TRIGGERED_LEVEL);
    bool magazin   = (digitalRead(PIN_MAGAZIN_SENSOR)  == MAGAZIN_TRIGGERED_LEVEL);

    Serial.print(F("status state="));    Serial.print(modeName(currentMode));
    Serial.print(F(" step="));            Serial.print(currentStep);
    Serial.print(F(" error="));           Serial.print(errorMsg[0] ? errorMsg : "");
    Serial.print(F(" press="));           Serial.print(press);
    Serial.print(F(" push_front="));      Serial.print(pushFront);
    Serial.print(F(" push_rear="));       Serial.print(pushRear);
    Serial.print(F(" magazin="));         Serial.print(magazin);
    Serial.print(F(" sol1="));            Serial.print(digitalRead(PIN_SOLENOID_1));
    Serial.print(F(" sol2="));            Serial.print(digitalRead(PIN_SOLENOID_2));
    Serial.print(F(" hopper="));          Serial.print(digitalRead(PIN_HOPPER_MOTOR));
    Serial.print(F(" hopper_enabled="));  Serial.print(hopperEnabled ? 1 : 0);
    Serial.print(F(" stepper_pos="));     Serial.println(stepper.currentPosition());
}

static void printHelp() {
    Serial.println(F("=== Stopfmaschine v0.3 ==="));
    Serial.println(F("ping | status | help"));
    Serial.println(F("params | get <k> | set <k> <v>"));
    Serial.println(F("home | stuff | step <1..9> | stop"));
    Serial.println(F("stepper <steps>"));
    Serial.println(F("press fwd|rev|stop  (PWM aus params.press_pwm)"));
    Serial.println(F("pusher fwd|rev|stop (PWM aus params.pusher_pwm)"));
    Serial.println(F("servo <0..180>"));
    Serial.println(F("solenoid 1|2 off|pulse <ms>   (Dauer-ON deaktiviert)"));
    Serial.println(F("hopper on|off|test <ms>   (on = 10s/20s Cycle)"));
    Serial.println(F("knock [<cycles>]"));
    Serial.println(F("========================="));
}

// =====================================================
// Manual-Befehle (nur im IDLE-Mode)
// =====================================================

static bool requireIdle() {
    if (currentMode == MODE_IDLE) return true;
    Serial.print(F("err busy mode=")); Serial.println(modeName(currentMode));
    return false;
}

static void cmdSolenoid(uint8_t pin, const String& action) {
    const char* name = (pin == PIN_SOLENOID_1) ? "sol1" : "sol2";
    if (action == "on") {
        // Dauer-ON ist DEAKTIVIERT. Die Heschen-Magnete sind nicht für
        // Dauerbetrieb ausgelegt (hat schon eine Sicherung gekostet). Es gibt
        // nur noch pulse/off — so kann kein Pfad (App, API, Serial) einen
        // Magneten dauerhaft halten. Pin sicherheitshalber auf LOW.
        digitalWrite(pin, LOW);
        Serial.print(F("err on_disabled ")); Serial.println(name);
    } else if (action == "off") {
        digitalWrite(pin, LOW);
        Serial.print(F("ok ")); Serial.print(name); Serial.println(F(" off"));
    } else if (action.startsWith("pulse ")) {
        unsigned long ms = action.substring(6).toInt();
        if (ms == 0 || ms > SOLENOID_PULSE_MAX_MS) {
            Serial.print(F("err pulse_ms:1..")); Serial.println(SOLENOID_PULSE_MAX_MS);
            return;
        }
        digitalWrite(pin, HIGH);
        delay(ms);   // Manual-Pulse darf blocken, ist <1 s
        digitalWrite(pin, LOW);
        Serial.print(F("ok ")); Serial.print(name);
        Serial.print(F(" pulse ")); Serial.println(ms);
    } else {
        Serial.print(F("err sol_action:")); Serial.println(action);
    }
}

static void cmdHopper(const String& action) {
    if (action == "on") {
        hopperEnabled = true;
        hopperCycleStartMs = millis();
        Serial.println(F("ok hopper=cyclic"));
    } else if (action == "off") {
        hopperEnabled = false;
        hopperManualUntil = 0;
        digitalWrite(PIN_HOPPER_MOTOR, LOW);
        Serial.println(F("ok hopper=off"));
    } else if (action.startsWith("test ")) {
        unsigned long ms = action.substring(5).toInt();
        if (ms == 0 || ms > HOPPER_RUN_MAX_MS) {
            Serial.print(F("err hopper_test_ms:1..")); Serial.println(HOPPER_RUN_MAX_MS);
            return;
        }
        hopperManualUntil = millis() + ms;
        Serial.print(F("ok hopper test ")); Serial.println(ms);
    } else {
        Serial.print(F("err hopper_action:")); Serial.println(action);
    }
}

// =====================================================
// Befehls-Parser
// =====================================================

static void handleCommand(String cmd) {
    cmd.trim();
    if (cmd.length() == 0) return;

    lastCommandMs = millis();
    watchdogTripped = false;

    // --- Immer erlaubt ---
    if (cmd == "ping")    { Serial.println(F("pong")); return; }
    if (cmd == "help")    { printHelp(); return; }
    if (cmd == "status")  { printStatus(); return; }
    if (cmd == "stop")    { doStop(); return; }
    if (cmd == "params")  { paramsPrintAll(); return; }

    if (cmd.startsWith("get ")) {
        String k = cmd.substring(4); k.trim();
        long v;
        if (paramsGetByName(k, v)) {
            Serial.print(F("ok ")); Serial.print(k); Serial.print('='); Serial.println(v);
        } else {
            Serial.print(F("err unknown:")); Serial.println(k);
        }
        return;
    }
    if (cmd.startsWith("set ")) {
        String rest = cmd.substring(4); rest.trim();
        int sp = rest.indexOf(' ');
        if (sp < 0) { Serial.println(F("err usage:set <key> <value>")); return; }
        String k = rest.substring(0, sp);
        long v   = rest.substring(sp + 1).toInt();
        const char* err = "";
        if (paramsSetByName(k, v, err)) {
            Serial.print(F("ok ")); Serial.print(k); Serial.print('='); Serial.println(v);
        } else {
            Serial.print(F("err ")); Serial.print(err);
            Serial.print(':'); Serial.println(k);
        }
        return;
    }

    if (cmd == "home")  { startHome();  return; }
    if (cmd == "stuff") { startStuff(); return; }
    if (cmd.startsWith("step ")) {
        startStep((uint8_t)cmd.substring(5).toInt());
        return;
    }

    // --- Manual: nur im IDLE ---
    if (cmd.startsWith("stepper ")) {
        if (!requireIdle()) return;
        long steps = cmd.substring(8).toInt();
        enableStepper();
        stepper.setMaxSpeed(STEPPER_MAX_SPEED);
        stepper.move(steps);
        Serial.print(F("ok stepper ")); Serial.println(steps);
        return;
    }
    if (cmd.startsWith("press ")) {
        if (!requireIdle()) return;
        String d = cmd.substring(6); d.trim();
        pressDrive(d.c_str());
        Serial.print(F("ok press ")); Serial.println(d);
        return;
    }
    if (cmd.startsWith("pusher ")) {
        if (!requireIdle()) return;
        String d = cmd.substring(7); d.trim();
        pusherDrive(d.c_str());
        Serial.print(F("ok pusher ")); Serial.println(d);
        return;
    }
    if (cmd.startsWith("servo ")) {
        if (!requireIdle()) return;
        int angle = constrain(cmd.substring(6).toInt(), 0, 180);
        tubeServo.write(angle);
        Serial.print(F("ok servo ")); Serial.println(angle);
        return;
    }
    if (cmd.startsWith("solenoid 1 ")) {
        if (!requireIdle()) return;
        cmdSolenoid(PIN_SOLENOID_1, cmd.substring(11));
        return;
    }
    if (cmd.startsWith("solenoid 2 ")) {
        if (!requireIdle()) return;
        cmdSolenoid(PIN_SOLENOID_2, cmd.substring(11));
        return;
    }
    if (cmd.startsWith("hopper ")) {
        // hopper darf auch in stuffing manipuliert werden? Nein, Konsistenz.
        // Außer "off" als Sicherheit:
        String action = cmd.substring(7); action.trim();
        if (action == "off") { cmdHopper(action); return; }
        if (!requireIdle()) return;
        cmdHopper(action);
        return;
    }
    if (cmd == "knock") {
        if (!requireIdle()) return;
        knockTargetCycles = 0;  // → nimmt params.knock_cycles
        clearError();
        currentMode = MODE_STEP;
        enterStep(STEP_KNOCK);
        Serial.println(F("ok knock"));
        return;
    }
    if (cmd.startsWith("knock ")) {
        if (!requireIdle()) return;
        uint8_t n = (uint8_t)cmd.substring(6).toInt();
        if (n == 0) n = params.knock_cycles;
        knockTargetCycles = n;
        clearError();
        currentMode = MODE_STEP;
        enterStep(STEP_KNOCK);
        Serial.print(F("ok knock ")); Serial.println(n);
        return;
    }

    Serial.print(F("err unknown_command:")); Serial.println(cmd);
}

// =====================================================
// Setup / Loop
// =====================================================

void setup() {
    Serial.begin(SERIAL_BAUD);
    while (!Serial && millis() < 2000) {}

    paramsBegin();   // lädt aus EEPROM oder schreibt Defaults

    pinMode(PIN_STEPPER_EN, OUTPUT);
    pinMode(PIN_PRESS_IN1, OUTPUT);
    pinMode(PIN_PRESS_IN2, OUTPUT);
    pinMode(PIN_PUSHER_IN3, OUTPUT);
    pinMode(PIN_PUSHER_IN4, OUTPUT);
    pinMode(PIN_PRESS_ENA, OUTPUT);
    pinMode(PIN_PUSHER_ENB, OUTPUT);
    pinMode(PIN_SOLENOID_1, OUTPUT);
    pinMode(PIN_SOLENOID_2, OUTPUT);
    pinMode(PIN_HOPPER_MOTOR, OUTPUT);
    digitalWrite(PIN_SOLENOID_1, LOW);
    digitalWrite(PIN_SOLENOID_2, LOW);
    digitalWrite(PIN_HOPPER_MOTOR, LOW);

    pinMode(PIN_INIT_PRESS, INPUT);
    pinMode(PIN_INIT_PUSH_FRONT, INPUT);
    pinMode(PIN_INIT_PUSH_REAR, INPUT);
    pinMode(PIN_MAGAZIN_SENSOR, INPUT_PULLUP);

    stepper.setMaxSpeed(STEPPER_MAX_SPEED);
    stepper.setAcceleration(STEPPER_ACCEL);

    tubeServo.attach(PIN_SERVO);
    tubeServo.write(params.servo_home);

    allMotorsOff();
    lastCommandMs = millis();

    Serial.println();
    Serial.print(F("ready firmware="));
    Serial.println(FIRMWARE_VERSION);
    Serial.println(F("type 'help' for commands"));
}

void loop() {
    // 1) Serial einlesen
    static String buffer;
    while (Serial.available() > 0) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            if (buffer.length() > 0) {
                handleCommand(buffer);
                buffer = "";
            }
        } else {
            buffer += c;
            if (buffer.length() > 64) buffer = "";
        }
    }

    // 2) Stepper non-blocking ticken
    stepper.run();

    // 3) State-Machine (home/stuff/step) ticken
    tickStateMachine();

    // 4) Hopper-Background
    tickHopper();

    // 5) Watchdog — greift nur im IDLE
    if (!watchdogTripped &&
        currentMode == MODE_IDLE &&
        (millis() - lastCommandMs > WATCHDOG_TIMEOUT_MS) &&
        lastCommandMs > 0) {
        allMotorsOff();
        hopperEnabled = false;
        Serial.println(F("warn watchdog_timeout"));
        watchdogTripped = true;
    }
}
