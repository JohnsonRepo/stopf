// =====================================================
// main.cpp
// Stopfmaschine - Arduino Nano Firmware (Test-Stage 0.1)
//
// Zweck: Einzeltests aller Motoren und Sensoren über Serial.
// Diese Version ist KEIN finaler Firmware-Stand, sondern eine
// Testbench, mit der du jede Komponente einzeln durchprobieren
// kannst, bevor die echte Stopfsequenz programmiert wird.
//
// Befehle (per Serial Monitor oder vom Pi, 115200 Baud):
//   help              → Übersicht
//   status            → aktuelle Sensorwerte
//   stepper <steps>   → Schrittmotor um N Steps drehen (negativ = rückwärts)
//   press fwd|rev|stop
//   pusher fwd|rev|stop
//   servo <0..180>    → Servo auf Winkel fahren
//   stop              → ALLES sofort aus
//   ping              → antwortet "pong"
// =====================================================

#include <Arduino.h>
#include <AccelStepper.h>
#include <Servo.h>
#include "pins.h"
#include "config.h"

// --- Globale Objekte ---
AccelStepper stepper(AccelStepper::DRIVER, PIN_STEPPER_STEP, PIN_STEPPER_DIR);
Servo tubeServo;

// --- Watchdog ---
unsigned long lastCommandMs = 0;
bool watchdogTripped = false;

// --- Hilfsfunktionen ---
void allMotorsOff() {
    digitalWrite(PIN_STEPPER_EN, HIGH);  // EN HIGH = Treiber aus
    // Beide IN-Pins LOW → Bremse (Motor kurzgeschlossen gegen GND)
    // Wegen "PWM-on-IN" muss analogWrite(0) für die PWM-Pins reichen,
    // digitalWrite LOW für die Direction-Pins.
    analogWrite(PIN_PRESS_IN1, 0);
    digitalWrite(PIN_PRESS_IN2, LOW);
    analogWrite(PIN_PUSHER_IN3, 0);
    digitalWrite(PIN_PUSHER_IN4, LOW);
}

void enableStepper() {
    digitalWrite(PIN_STEPPER_EN, LOW);   // LOW = aktiv
}

// L298N Mini-Modul ohne ENA/ENB:
//   FWD = PWM auf IN_a (Timer0-Pin), IN_b LOW          → drehzahlgeregelt
//   REV = IN_a LOW, IN_b HIGH (digital, volle Drehzahl) → Retraction
//   Stop = beide LOW                                    → Bremse
void setPressMotor(const String& dir) {
    if (dir == "fwd") {
        digitalWrite(PIN_PRESS_IN2, LOW);
        analogWrite(PIN_PRESS_IN1, PRESS_SPEED_DEFAULT);
        Serial.println("ok press fwd");
    } else if (dir == "rev") {
        analogWrite(PIN_PRESS_IN1, 0);          // PWM aus
        digitalWrite(PIN_PRESS_IN2, HIGH);      // volle Drehzahl rückwärts
        Serial.println("ok press rev");
    } else {
        analogWrite(PIN_PRESS_IN1, 0);
        digitalWrite(PIN_PRESS_IN2, LOW);
        Serial.println("ok press stop");
    }
}

void setPusherMotor(const String& dir) {
    if (dir == "fwd") {
        digitalWrite(PIN_PUSHER_IN4, LOW);
        analogWrite(PIN_PUSHER_IN3, PUSHER_SPEED_DEFAULT);
        Serial.println("ok pusher fwd");
    } else if (dir == "rev") {
        analogWrite(PIN_PUSHER_IN3, 0);
        digitalWrite(PIN_PUSHER_IN4, HIGH);
        Serial.println("ok pusher rev");
    } else {
        analogWrite(PIN_PUSHER_IN3, 0);
        digitalWrite(PIN_PUSHER_IN4, LOW);
        Serial.println("ok pusher stop");
    }
}

void readSensors() {
    bool press     = (digitalRead(PIN_INIT_PRESS)      == INIT_TRIGGERED_LEVEL);
    bool pushFront = (digitalRead(PIN_INIT_PUSH_FRONT) == INIT_TRIGGERED_LEVEL);
    bool pushRear  = (digitalRead(PIN_INIT_PUSH_REAR)  == INIT_TRIGGERED_LEVEL);
    bool touch     = (digitalRead(PIN_TOUCH) == HIGH);

    Serial.print("status press=");
    Serial.print(press);
    Serial.print(" push_front=");
    Serial.print(pushFront);
    Serial.print(" push_rear=");
    Serial.print(pushRear);
    Serial.print(" touch=");
    Serial.print(touch);
    Serial.print(" stepper_pos=");
    Serial.println(stepper.currentPosition());
}

void printHelp() {
    Serial.println(F("=== Stopfmaschine Test-Firmware ==="));
    Serial.println(F("help               - this list"));
    Serial.println(F("ping               - connection test"));
    Serial.println(F("status             - sensor readout"));
    Serial.println(F("stepper <steps>    - move stepper N steps (+/-)"));
    Serial.println(F("press fwd|rev|stop - press motor"));
    Serial.println(F("pusher fwd|rev|stop- pusher motor"));
    Serial.println(F("servo <0..180>     - servo angle"));
    Serial.println(F("stop               - emergency stop ALL"));
    Serial.println(F("==================================="));
}

// --- Befehlsverarbeitung ---
void handleCommand(String cmd) {
    cmd.trim();
    if (cmd.length() == 0) return;

    lastCommandMs = millis();
    watchdogTripped = false;
    digitalWrite(PIN_STATUS_LED, HIGH);

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
    pinMode(PIN_PRESS_IN1, OUTPUT);   // PWM
    pinMode(PIN_PRESS_IN2, OUTPUT);   // digital
    pinMode(PIN_PUSHER_IN3, OUTPUT);  // PWM
    pinMode(PIN_PUSHER_IN4, OUTPUT);  // digital
    pinMode(PIN_STATUS_LED, OUTPUT);

    pinMode(PIN_INIT_PRESS, INPUT);
    pinMode(PIN_INIT_PUSH_FRONT, INPUT);
    pinMode(PIN_INIT_PUSH_REAR, INPUT);
    pinMode(PIN_TOUCH, INPUT);

    // Schrittmotor-Setup
    stepper.setMaxSpeed(STEPPER_MAX_SPEED);
    stepper.setAcceleration(STEPPER_ACCEL);

    // Servo
    tubeServo.attach(PIN_SERVO);
    tubeServo.write(SERVO_POS_HOME);

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
            digitalWrite(PIN_STATUS_LED, LOW);
            Serial.println("warn watchdog_timeout motors_off");
            watchdogTripped = true;
        }
    }
}
