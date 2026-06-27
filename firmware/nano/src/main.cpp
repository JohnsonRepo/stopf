// =====================================================
// main.cpp
// Stopfmaschine - Arduino Nano Firmware (Test-Stage 0.2)
//
// Zweck: Einzeltests aller Motoren und Sensoren über Serial.
// Diese Version ist KEIN finaler Firmware-Stand, sondern eine
// Testbench, mit der du jede Komponente einzeln durchprobieren
// kannst, bevor die echte Stopfsequenz programmiert wird.
//
// Befehle (per Serial Monitor oder vom Pi, 115200 Baud):
//   help                → Übersicht
//   status              → Sensorwerte + Aktor-Zustände
//   stepper <steps>     → Schrittmotor um N Steps drehen (negativ = rückwärts)
//   press fwd|rev|stop  → DC-Press-Motor (drehzahlgeregelt via ENA)
//   pusher fwd|rev|stop → DC-Pusher-Motor (drehzahlgeregelt via ENB)
//   servo <0..180>      → Hülsen-Schieber-Servo
//   tabak_servo <0..180>→ Tabak-Tilt-Schwenkwand-Servo
//   solenoid 1|2 on|off|pulse <ms>
//                       → Heschen HS-0530B Hubmagnete via MOSFET
//   hopper on|off|run <ms>
//                       → 5V Hülsenmagazin-Motor via MOSFET
//   knock [<cycles>]    → komplette Tabak-Dosier-Sequenz
//   stop                → ALLES sofort aus
//   ping                → antwortet "pong"
// =====================================================

#include <Arduino.h>
#include <AccelStepper.h>
#include <Servo.h>
#include "pins.h"
#include "config.h"

// --- Globale Objekte ---
AccelStepper stepper(AccelStepper::DRIVER, PIN_STEPPER_STEP, PIN_STEPPER_DIR);
Servo tubeServo;     // Hülsen-Schieber (D11)
Servo tabakServo;    // Tabak-Tilt-Schwenkwand (A3)

// --- Watchdog ---
unsigned long lastCommandMs = 0;
bool watchdogTripped = false;

// --- Hilfsfunktionen ---
void allMotorsOff() {
    digitalWrite(PIN_STEPPER_EN, HIGH);  // EN HIGH = Treiber aus
    digitalWrite(PIN_PRESS_IN1, LOW);
    digitalWrite(PIN_PRESS_IN2, LOW);
    digitalWrite(PIN_PUSHER_IN3, LOW);
    digitalWrite(PIN_PUSHER_IN4, LOW);
    analogWrite(PIN_PRESS_ENA, 0);
    analogWrite(PIN_PUSHER_ENB, 0);
    // Tabak-Dosier-Aktoren auch in Safe State
    digitalWrite(PIN_SOLENOID_1, LOW);
    digitalWrite(PIN_SOLENOID_2, LOW);
    digitalWrite(PIN_HOPPER_MOTOR, LOW);
}

void enableStepper() {
    digitalWrite(PIN_STEPPER_EN, LOW);   // LOW = aktiv
}

// L298N Standard-Modul mit ENA/ENB:
//   Richtung über IN1/IN2 bzw. IN3/IN4, Drehzahl über ENA/ENB (PWM).
//   Drehzahl-Regelung funktioniert in BEIDE Richtungen.
void setPressMotor(const String& dir) {
    if (dir == "fwd") {
        digitalWrite(PIN_PRESS_IN1, HIGH);
        digitalWrite(PIN_PRESS_IN2, LOW);
        analogWrite(PIN_PRESS_ENA, PRESS_SPEED_DEFAULT);
        Serial.println("ok press fwd");
    } else if (dir == "rev") {
        digitalWrite(PIN_PRESS_IN1, LOW);
        digitalWrite(PIN_PRESS_IN2, HIGH);
        analogWrite(PIN_PRESS_ENA, PRESS_SPEED_DEFAULT);
        Serial.println("ok press rev");
    } else {
        digitalWrite(PIN_PRESS_IN1, LOW);
        digitalWrite(PIN_PRESS_IN2, LOW);
        analogWrite(PIN_PRESS_ENA, 0);
        Serial.println("ok press stop");
    }
}

void setPusherMotor(const String& dir) {
    if (dir == "fwd") {
        digitalWrite(PIN_PUSHER_IN3, HIGH);
        digitalWrite(PIN_PUSHER_IN4, LOW);
        analogWrite(PIN_PUSHER_ENB, PUSHER_SPEED_DEFAULT);
        Serial.println("ok pusher fwd");
    } else if (dir == "rev") {
        digitalWrite(PIN_PUSHER_IN3, LOW);
        digitalWrite(PIN_PUSHER_IN4, HIGH);
        analogWrite(PIN_PUSHER_ENB, PUSHER_SPEED_DEFAULT);
        Serial.println("ok pusher rev");
    } else {
        digitalWrite(PIN_PUSHER_IN3, LOW);
        digitalWrite(PIN_PUSHER_IN4, LOW);
        analogWrite(PIN_PUSHER_ENB, 0);
        Serial.println("ok pusher stop");
    }
}

void readSensors() {
    bool press     = (digitalRead(PIN_INIT_PRESS)      == INIT_TRIGGERED_LEVEL);
    bool pushFront = (digitalRead(PIN_INIT_PUSH_FRONT) == INIT_TRIGGERED_LEVEL);
    bool pushRear  = (digitalRead(PIN_INIT_PUSH_REAR)  == INIT_TRIGGERED_LEVEL);
    // Magazin-Gabellichtschranke (Index-Sensor an Stepper-Pulley/Trommel)
    bool magazin   = (digitalRead(PIN_MAGAZIN_SENSOR) == MAGAZIN_TRIGGERED_LEVEL);
    int  magazinRaw = digitalRead(PIN_MAGAZIN_SENSOR);
    // Aktor-Zustände (Output-Pins zurücklesen für Diagnose)
    int  sol1   = digitalRead(PIN_SOLENOID_1);
    int  sol2   = digitalRead(PIN_SOLENOID_2);
    int  hopper = digitalRead(PIN_HOPPER_MOTOR);

    Serial.print("status press=");
    Serial.print(press);
    Serial.print(" push_front=");
    Serial.print(pushFront);
    Serial.print(" push_rear=");
    Serial.print(pushRear);
    Serial.print(" magazin=");
    Serial.print(magazin);
    Serial.print(" magazin_raw=");
    Serial.print(magazinRaw);
    Serial.print(" sol1=");
    Serial.print(sol1);
    Serial.print(" sol2=");
    Serial.print(sol2);
    Serial.print(" hopper=");
    Serial.print(hopper);
    Serial.print(" stepper_pos=");
    Serial.println(stepper.currentPosition());
}

// --- Tabak-Dosier-Aktoren (MOSFET-getrieben) ---
void setSolenoid(uint8_t pin, const String& action) {
    const char* name = (pin == PIN_SOLENOID_1) ? "sol1" : "sol2";
    if (action == "on") {
        digitalWrite(pin, HIGH);
        Serial.print("ok ");  Serial.print(name); Serial.println(" on");
    } else if (action == "off") {
        digitalWrite(pin, LOW);
        Serial.print("ok ");  Serial.print(name); Serial.println(" off");
    } else if (action.startsWith("pulse ")) {
        unsigned long ms = action.substring(6).toInt();
        if (ms == 0 || ms > SOLENOID_PULSE_MAX_MS) {
            Serial.print("err pulse_ms_invalid:0<ms<=");
            Serial.println(SOLENOID_PULSE_MAX_MS);
            return;
        }
        digitalWrite(pin, HIGH);
        delay(ms);
        digitalWrite(pin, LOW);
        Serial.print("ok ");  Serial.print(name);
        Serial.print(" pulse "); Serial.println(ms);
    } else {
        Serial.print("err solenoid_action:");
        Serial.println(action);
    }
}

void setHopper(const String& action) {
    if (action == "on") {
        digitalWrite(PIN_HOPPER_MOTOR, HIGH);
        Serial.println("ok hopper on");
    } else if (action == "off") {
        digitalWrite(PIN_HOPPER_MOTOR, LOW);
        Serial.println("ok hopper off");
    } else if (action.startsWith("run ")) {
        unsigned long ms = action.substring(4).toInt();
        if (ms == 0) ms = HOPPER_DEFAULT_MS;
        if (ms > HOPPER_RUN_MAX_MS) {
            Serial.print("err hopper_run_max_ms:");
            Serial.println(HOPPER_RUN_MAX_MS);
            return;
        }
        digitalWrite(PIN_HOPPER_MOTOR, HIGH);
        delay(ms);
        digitalWrite(PIN_HOPPER_MOTOR, LOW);
        Serial.print("ok hopper run ");
        Serial.println(ms);
    } else {
        Serial.print("err hopper_action:");
        Serial.println(action);
    }
}

// Komplette Knock-Sequenz: Servo schwenkt + beide Solenoide pulsen synchron.
// Blockierend, aber Gesamt-Dauer ~1,6 s (8 × 200 ms) < Watchdog (5 s).
void runKnock(uint8_t cycles) {
    if (cycles == 0) cycles = KNOCK_CYCLES_DEFAULT;
    Serial.print("ok knock start cycles=");
    Serial.println(cycles);
    for (uint8_t i = 0; i < cycles; i++) {
        // Pulse: Servo nach hinten + Solenoide an
        tabakServo.write(TABAK_SERVO_REAR);
        digitalWrite(PIN_SOLENOID_1, HIGH);
        digitalWrite(PIN_SOLENOID_2, HIGH);
        delay(KNOCK_PULSE_ON_MS);
        // Pause: Solenoide aus + Servo nach vorne (Erholung)
        digitalWrite(PIN_SOLENOID_1, LOW);
        digitalWrite(PIN_SOLENOID_2, LOW);
        tabakServo.write(TABAK_SERVO_FRONT);
        delay(KNOCK_PULSE_OFF_MS);
        // Watchdog während Knock-Sequenz "füttern"
        lastCommandMs = millis();
    }
    Serial.println("ok knock done");
}

void printHelp() {
    Serial.println(F("=== Stopfmaschine Test-Firmware ==="));
    Serial.println(F("help               - this list"));
    Serial.println(F("ping               - connection test"));
    Serial.println(F("status             - sensor + actuator readout"));
    Serial.println(F("stepper <steps>    - move stepper N steps (+/-)"));
    Serial.println(F("press fwd|rev|stop - press DC motor"));
    Serial.println(F("pusher fwd|rev|stop- pusher DC motor"));
    Serial.println(F("servo <0..180>     - tube-servo angle (Huelsen)"));
    Serial.println(F("tabak_servo <0..180>"));
    Serial.println(F("                   - tobacco-tilt servo angle"));
    Serial.println(F("solenoid 1|2 on|off|pulse <ms>"));
    Serial.println(F("                   - 2x Heschen HS-0530B (Knock-Magnete)"));
    Serial.println(F("hopper on|off|run <ms>"));
    Serial.println(F("                   - 5V Huelsenmagazin-Motor"));
    Serial.println(F("knock [<cycles>]   - Tabak-Dosis: Servo+Solenoide N-mal"));
    Serial.println(F("stop               - emergency stop ALL"));
    Serial.println(F("==================================="));
}

// --- Befehlsverarbeitung ---
void handleCommand(String cmd) {
    cmd.trim();
    if (cmd.length() == 0) return;

    lastCommandMs = millis();
    watchdogTripped = false;

    if (cmd == "help") {
        printHelp();
    }
    else if (cmd == "ping") {
        Serial.println("pong");
    }
    else if (cmd == "status") {
        readSensors();
    }
    else if (cmd == "stop") {
        allMotorsOff();
        stepper.stop();
        Serial.println("ok stop");
    }
    else if (cmd.startsWith("stepper ")) {
        long steps = cmd.substring(8).toInt();
        enableStepper();
        stepper.move(steps);
        Serial.print("ok stepper ");
        Serial.println(steps);
    }
    else if (cmd.startsWith("press ")) {
        setPressMotor(cmd.substring(6));
    }
    else if (cmd.startsWith("pusher ")) {
        setPusherMotor(cmd.substring(7));
    }
    else if (cmd.startsWith("servo ")) {
        int angle = cmd.substring(6).toInt();
        angle = constrain(angle, 0, 180);
        tubeServo.write(angle);
        Serial.print("ok servo ");
        Serial.println(angle);
    }
    else if (cmd.startsWith("tabak_servo ")) {
        int angle = cmd.substring(12).toInt();
        angle = constrain(angle, 0, 180);
        tabakServo.write(angle);
        Serial.print("ok tabak_servo ");
        Serial.println(angle);
    }
    else if (cmd.startsWith("solenoid 1 ")) {
        setSolenoid(PIN_SOLENOID_1, cmd.substring(11));
    }
    else if (cmd.startsWith("solenoid 2 ")) {
        setSolenoid(PIN_SOLENOID_2, cmd.substring(11));
    }
    else if (cmd.startsWith("hopper ")) {
        setHopper(cmd.substring(7));
    }
    else if (cmd == "knock") {
        runKnock(KNOCK_CYCLES_DEFAULT);
    }
    else if (cmd.startsWith("knock ")) {
        runKnock((uint8_t) cmd.substring(6).toInt());
    }
    else {
        Serial.print("err unknown_command:");
        Serial.println(cmd);
    }
}

// --- Setup ---
void setup() {
    Serial.begin(SERIAL_BAUD);
    while (!Serial && millis() < 2000) { /* wait briefly */ }

    // Pin-Modi: L298N Standard (Press/Pusher)
    pinMode(PIN_STEPPER_EN, OUTPUT);
    pinMode(PIN_PRESS_IN1, OUTPUT);
    pinMode(PIN_PRESS_IN2, OUTPUT);
    pinMode(PIN_PUSHER_IN3, OUTPUT);
    pinMode(PIN_PUSHER_IN4, OUTPUT);
    pinMode(PIN_PRESS_ENA, OUTPUT);   // PWM
    pinMode(PIN_PUSHER_ENB, OUTPUT);  // PWM

    // Pin-Modi: MOSFET-Gates (Tabak-Solenoide + Hülsenmagazin-Motor)
    pinMode(PIN_SOLENOID_1, OUTPUT);
    pinMode(PIN_SOLENOID_2, OUTPUT);
    pinMode(PIN_HOPPER_MOTOR, OUTPUT);
    digitalWrite(PIN_SOLENOID_1, LOW);   // Solenoide explizit aus
    digitalWrite(PIN_SOLENOID_2, LOW);
    digitalWrite(PIN_HOPPER_MOTOR, LOW); // Motor aus

    // Sensor-Eingänge
    pinMode(PIN_INIT_PRESS, INPUT);
    pinMode(PIN_INIT_PUSH_FRONT, INPUT);
    pinMode(PIN_INIT_PUSH_REAR, INPUT);
    pinMode(PIN_MAGAZIN_SENSOR, INPUT_PULLUP);  // Opto-Modul Open-Collector-freundlich

    // Schrittmotor-Setup
    stepper.setMaxSpeed(STEPPER_MAX_SPEED);
    stepper.setAcceleration(STEPPER_ACCEL);

    // Servos: Hülsen-Schieber und Tabak-Tilt
    tubeServo.attach(PIN_SERVO);
    tubeServo.write(SERVO_POS_HOME);
    tabakServo.attach(PIN_TABAK_SERVO);
    tabakServo.write(TABAK_SERVO_FRONT);

    // Sicher starten
    allMotorsOff();
    lastCommandMs = millis();

    // Begrüßung
    Serial.println();
    Serial.print(F("ready firmware="));
    Serial.println(FIRMWARE_VERSION);
    Serial.println(F("type 'help' for commands"));
}

// --- Main Loop ---
void loop() {
    // 1) Serial-Befehle einlesen
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
            if (buffer.length() > 64) buffer = "";  // Schutz
        }
    }

    // 2) Schrittmotor non-blocking laufen lassen
    stepper.run();

    // 3) Watchdog: lange keine Kommunikation → alles aus
    if (!watchdogTripped &&
        (millis() - lastCommandMs > WATCHDOG_TIMEOUT_MS)) {
        // Nur beim allerersten Mal nach Boot nicht greifen
        if (lastCommandMs > 0) {
            allMotorsOff();
            Serial.println("warn watchdog_timeout motors_off");
            watchdogTripped = true;
        }
    }
}
