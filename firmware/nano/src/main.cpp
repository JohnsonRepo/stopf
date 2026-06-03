// =====================================================
// main.cpp
// Stopfmaschine - Arduino Nano Firmware (Test-Stage 0.2)
//
// Zweck: Einzeltests aller Motoren, Solenoide und Sensoren über Serial.
//
// Befehle (115200 Baud):
//   help                    → Übersicht
//   status                  → Sensorwerte + button-Zustand
//   stepper <steps>         → Trommel-Schrittmotor N Steps drehen
//   press fwd|rev|stop
//   pusher fwd|rev|stop
//   servo <0..180>          → Hülsen-Servo (D11)
//   tabakservo <0..180>     → Tabak-Tilt-Servo (A3)
//   knock1 on|off           → Hubmagnet Front-Knock (A4)
//   knock2 on|off           → Hubmagnet Top-Druck (D13)
//   stop                    → ALLES sofort aus
//   ping                    → antwortet "pong"
// =====================================================

#include <Arduino.h>
#include <AccelStepper.h>
#include <Servo.h>
#include "pins.h"
#include "config.h"

// --- Globale Objekte ---
AccelStepper stepper(AccelStepper::DRIVER, PIN_STEPPER_STEP, PIN_STEPPER_DIR);
Servo tubeServo;
Servo tabakServo;

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
    digitalWrite(PIN_SOL_FRONT, LOW);
    digitalWrite(PIN_SOL_TOP, LOW);
}

void enableStepper() {
    digitalWrite(PIN_STEPPER_EN, LOW);   // LOW = aktiv
}

// L298N Standard-Modul mit ENA/ENB:
//   Richtung über IN1/IN2 bzw. IN3/IN4, Drehzahl über ENA/ENB (PWM).
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
    // Mechanischer Taster mit internem Pull-up: ungedrückt = HIGH, gedrückt = LOW.
    bool button    = (digitalRead(PIN_BUTTON) == LOW);
    // Magazin-Gabellichtschranke (Index-Sensor an Stepper-Pulley/Trommel)
    bool magazin   = (digitalRead(PIN_MAGAZIN_SENSOR) == MAGAZIN_TRIGGERED_LEVEL);
    // Roher Pegel zusätzlich — hilft beim Kalibrieren der Polarität
    int  magazinRaw = digitalRead(PIN_MAGAZIN_SENSOR);

    Serial.print("status press=");
    Serial.print(press);
    Serial.print(" push_front=");
    Serial.print(pushFront);
    Serial.print(" push_rear=");
    Serial.print(pushRear);
    Serial.print(" button=");
    Serial.print(button);
    Serial.print(" magazin=");
    Serial.print(magazin);
    Serial.print(" magazin_raw=");
    Serial.print(magazinRaw);
    Serial.print(" stepper_pos=");
    Serial.println(stepper.currentPosition());
}

void printHelp() {
    Serial.println(F("=== Stopfmaschine Test-Firmware v0.2 ==="));
    Serial.println(F("help                    - this list"));
    Serial.println(F("ping                    - connection test"));
    Serial.println(F("status                  - sensor readout"));
    Serial.println(F("stepper <steps>         - drum stepper N steps (+/-)"));
    Serial.println(F("press fwd|rev|stop      - press motor"));
    Serial.println(F("pusher fwd|rev|stop     - pusher motor"));
    Serial.println(F("servo <0..180>          - tube servo D11"));
    Serial.println(F("tabakservo <0..180>     - tabak tilt servo A3"));
    Serial.println(F("knock1 on|off           - solenoid front-knock A4"));
    Serial.println(F("knock2 on|off           - solenoid top-push D13"));
    Serial.println(F("stop                    - emergency stop ALL"));
    Serial.println(F("========================================"));
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
        int angle = constrain(cmd.substring(6).toInt(), 0, 180);
        tubeServo.write(angle);
        Serial.print("ok servo ");
        Serial.println(angle);
    }
    else if (cmd.startsWith("tabakservo ")) {
        int angle = constrain(cmd.substring(11).toInt(), 0, 180);
        tabakServo.write(angle);
        Serial.print("ok tabakservo ");
        Serial.println(angle);
    }
    else if (cmd.startsWith("knock1 ")) {
        String state = cmd.substring(7);
        state.trim();
        digitalWrite(PIN_SOL_FRONT, state == "on" ? HIGH : LOW);
        Serial.print("ok knock1 ");
        Serial.println(state);
    }
    else if (cmd.startsWith("knock2 ")) {
        String state = cmd.substring(7);
        state.trim();
        digitalWrite(PIN_SOL_TOP, state == "on" ? HIGH : LOW);
        Serial.print("ok knock2 ");
        Serial.println(state);
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

    // Pin-Modi
    pinMode(PIN_STEPPER_EN, OUTPUT);
    pinMode(PIN_PRESS_IN1, OUTPUT);
    pinMode(PIN_PRESS_IN2, OUTPUT);
    pinMode(PIN_PUSHER_IN3, OUTPUT);
    pinMode(PIN_PUSHER_IN4, OUTPUT);
    pinMode(PIN_PRESS_ENA, OUTPUT);   // PWM
    pinMode(PIN_PUSHER_ENB, OUTPUT);  // PWM
    pinMode(PIN_SOL_FRONT, OUTPUT);   // Hubmagnet Front-Knock
    pinMode(PIN_SOL_TOP, OUTPUT);     // Hubmagnet Top-Druck

    pinMode(PIN_INIT_PRESS, INPUT);
    pinMode(PIN_INIT_PUSH_FRONT, INPUT);
    pinMode(PIN_INIT_PUSH_REAR, INPUT);
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    pinMode(PIN_MAGAZIN_SENSOR, INPUT_PULLUP);  // Open-Collector-Opto: externer Pull-up des Moduls dominiert wenn vorhanden

    // Schrittmotor-Setup (Trommelmagazin)
    stepper.setMaxSpeed(STEPPER_MAX_SPEED);
    stepper.setAcceleration(STEPPER_ACCEL);

    // Servos
    tubeServo.attach(PIN_SERVO);
    tubeServo.write(SERVO_POS_HOME);

    tabakServo.attach(PIN_TABAK_SERVO);
    tabakServo.write(TABAK_SERVO_REAR);

    // Sicher starten
    allMotorsOff();
    lastCommandMs = millis();

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
        if (lastCommandMs > 0) {
            allMotorsOff();
            Serial.println("warn watchdog_timeout motors_off");
            watchdogTripped = true;
        }
    }
}
