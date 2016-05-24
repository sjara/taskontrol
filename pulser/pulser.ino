/*
Module that produces pulse trains.

*/

//#define HARDWARE_TEST


#define BOARD_LED_PIN 13

// PINS
int TRIGGER_UP_PIN = 53;
int TRIGGER_DOWN_PIN = 51;
int OUTPUT_UP_PIN = 23;
int OUTPUT_DOWN_PIN = 25;

// Variables
int state = 0;
int onTime = 10;  // In millisec if using delay(), in microsec if using delayMicrosec()
int offTime = 20; // In millisec if using delay(), in microsec if using delayMicrosec()

void setup() {
    pinMode(BOARD_LED_PIN, OUTPUT);
    pinMode(TRIGGER_UP_PIN, INPUT); // INPUT_PULLDOWN
    pinMode(TRIGGER_DOWN_PIN, INPUT_PULLUP);
    pinMode(OUTPUT_UP_PIN, OUTPUT);
    pinMode(OUTPUT_DOWN_PIN, OUTPUT);

    digitalWrite(BOARD_LED_PIN, LOW);    // sets the LED off
    digitalWrite(OUTPUT_UP_PIN, LOW);
    digitalWrite(OUTPUT_DOWN_PIN, HIGH);
}


void loop() {
  
    if (digitalRead(TRIGGER_UP_PIN) || !digitalRead(TRIGGER_DOWN_PIN)) {
        if (state) {
            digitalWrite(BOARD_LED_PIN, LOW);
            digitalWrite(OUTPUT_UP_PIN, LOW);
            digitalWrite(OUTPUT_DOWN_PIN, HIGH);
            //delayMicroseconds(offTime);
            delay(offTime);
            state = 0;
        }
        else {        
            digitalWrite(BOARD_LED_PIN, HIGH);
            digitalWrite(OUTPUT_UP_PIN, HIGH);
            digitalWrite(OUTPUT_DOWN_PIN, LOW);
            //delayMicroseconds(onTime);
            delay(onTime);
            state = 1;
        }
    }
    else {
        state = 0;
        digitalWrite(BOARD_LED_PIN, LOW);
        digitalWrite(OUTPUT_UP_PIN, LOW);
        digitalWrite(OUTPUT_DOWN_PIN, HIGH);
    } 
}

