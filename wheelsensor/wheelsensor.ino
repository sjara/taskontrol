/*
Movement sensor (using computer mouse) for Arduino DUE.
This can be used for example to sense the rotation of a wheel.

This version reports movement with the LED and sends every event via serial.
It allows changing the sampling period and the number of periods
for detecing a STOP event.


Timer interrupt based on:
http://2manyprojects.net/timer-interrupts

TO DO:
- It may send events of 0 movement when moving in Y (not X)

*/

// Require mouse control library
#include <MouseController.h>

#define ledPin 13

#define OK                    0xaa
#define RESET                 0x01  // OBSOLETE
#define TEST_CONNECTION       0x02
#define GET_POSITION          0x03
#define GET_INTERVAL          0x04
#define GET_SPEED             0x05
#define SET_THRESHOLD_MOVE    0x06
#define GET_THRESHOLD_MOVE    0x07
#define SET_THRESHOLD_STOP    0x08
#define GET_THRESHOLD_STOP    0x09
#define SET_SAMPLING_FACTOR   0x0a
#define GET_SAMPLING_FACTOR   0x0b
#define SET_N_PERIODS         0x0c
#define GET_N_PERIODS         0x0d
#define GET_SERVER_VERSION    0x0e
#define GET_TICK_TIMES        0x0f
#define RUN                   0xee
#define SET_DEBUG_MODE        0xf0
#define ERROR                 0xff

#define VERSION        "0.1"

//#define MAX_N_PERIODS  200
//#define BUFFER_SIZE    256

USBHost usb; // Initialize USB Controller
MouseController mouse(usb); // Attach mouse controller to USB

unsigned char debugMode = 0;

// Generic variables (to test timer)
int state = false;

// For serial
unsigned char serialByte;

// To get speed
int mouseXchange;
long avgTickRate = 0; // Total count in interval of duration = (nPeriods * sa
unsigned long lastTime = 0;
unsigned long thisTime = 0;

// Thresholds for detecting movement or no movement
unsigned char thresholdMove = 10;   // Pixels per unit time
unsigned char thresholdStop = 1;
unsigned char samplingPeriodFactor = 1; // Multiplier of 100ms
unsigned char periodsStop = 1;

unsigned char periodsSoFar = 0;

//long timerPeriod = 65600; // 0.1 seconds
long timerPeriod;
//  65600 / 656000 = 0.1 seconds
// 131200 / 656000 = 0.2 seconds


// -- This function intercepts mouse movements --
void mouseMoved() {
  TC_Start(TC2, 1);
  // NOTE: We are using abs() to detect movement in either direction
  mouseXchange = mouse.getXChange();
  if (abs(mouseXchange)>=thresholdMove) {
    digitalWrite(ledPin, true);
    periodsSoFar = 0;
  }
  else if (abs(mouseXchange)<=thresholdStop) {
    periodsSoFar++;
    if (periodsSoFar>=periodsStop) {
      digitalWrite(ledPin, false);
      periodsSoFar = 0;
    }
  }

  if(debugMode)
    Serial.println(mouseXchange); // DEBUG
}


// -- Timer interrupt handler --
void TC7_Handler() {
  // We need to get the status to clear it and allow the interrupt to fire again
  TC_GetStatus(TC2, 1); // Reser timer interrupt
  //digitalWrite(ledPin, false); // Turn output pin off
  periodsSoFar++;
  if (periodsSoFar>=periodsStop) {
    digitalWrite(ledPin, false);
    periodsSoFar = 0;
  }

  if(debugMode)
    Serial.println("..Stopped.."); // DEBUG
}


// -- Enable timer interrupt --
void enable_timer_interrupt() {
  // Turn on the timer clock in the power management controller
  pmc_set_writeprotect(false); // Disable write protection for pmc registers
  pmc_enable_periph_clk(ID_TC7); // Enable peripheral clock TC7
  // We want wavesel 01 with RC
  TC_Configure(TC2, 1,
	       TC_CMR_WAVE | TC_CMR_WAVSEL_UP_RC | TC_CMR_TCCLKS_TIMER_CLOCK4); 
  TC_SetRC(TC2, 1, timerPeriod);
  TC_Start(TC2, 1);
  // Enable timer interrupts on the timer
  TC2->TC_CHANNEL[1].TC_IER=TC_IER_CPCS;   // IER = interrupt enable register
  TC2->TC_CHANNEL[1].TC_IDR=~TC_IER_CPCS;  // IDR = interrupt disable register
  /* Enable the interrupt in the nested vector interrupt controller */
  /* TC4_IRQn where 4 is the timer number * timer channels (3) + the channel number (=(1*3)+1) for timer1 channel1 */
  NVIC_EnableIRQ(TC7_IRQn);
}


void setup() {
  Serial.begin(115200);
  pinMode(ledPin, OUTPUT);

  byte ready=0;
  while(!ready) {
    if (Serial.available()>0) {
      serialByte = Serial.read();
      switch(serialByte) {
        case TEST_CONNECTION: {
	  Serial.write(OK);
	  break;
	}
        case SET_THRESHOLD_MOVE: {
	  while (!Serial.available()) {}  // Wait for data
	  thresholdMove = Serial.read();
	  break;
	}
        case GET_THRESHOLD_MOVE: {
	  Serial.println(thresholdMove);
	  break;
	}
        case SET_THRESHOLD_STOP: {
	  while (!Serial.available()) {}  // Wait for data
	  thresholdStop = Serial.read();
	  break;
	}
        case GET_THRESHOLD_STOP: {
	  Serial.println(thresholdStop);
	  break;
	}
        case SET_SAMPLING_FACTOR: {
	  while (!Serial.available()) {}  // Wait for data
	  samplingPeriodFactor = Serial.read();
	  break;
	}
        case SET_N_PERIODS: {
	  while (!Serial.available()) {}  // Wait for data
	  periodsStop = Serial.read();
	  break;
	}
        case SET_DEBUG_MODE: {
	  while (!Serial.available()) {}  // Wait for data
	  debugMode = Serial.read();
	  break;
	}
        case RUN: {
	  ready=1;
	  break;
	}
      }
    }
  }
  timerPeriod = samplingPeriodFactor * 65600;
  Serial.println("--- Wheel sensor ---");
  Serial.print("THRESHOLD MOVE: ");
  Serial.println(thresholdMove);
  Serial.print("THRESHOLD STOP: ");
  Serial.println(thresholdStop);
  Serial.print("N PERIODS TO STOP: ");
  Serial.println(periodsStop);
  Serial.print("SAMPLING PERIOD FACTOR: ");
  Serial.println(samplingPeriodFactor);
  Serial.println("STARTING!");
  enable_timer_interrupt();
}


void loop() {
  usb.Task();
}

