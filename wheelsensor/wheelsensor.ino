/*
Wheelsensor using Arduino UNO and rotary encoder.

It keeps track of the position of the rotary encoder and it will send
it together with a timestamp via the serial port when requested.

It also allows setting (upper an lower) velocity thresholds to trigger
changes of a binary output. For this feature, it uses the Arduino's
internal Timer1 to calculate instantaneous velocity of the rotary
encoder at each time period. The sampling period can be defined by the
user. The default is 20 ms.
*/

#define VERSION        "0.2"

// -- Serial commands --
#define OK                    0xaa
#define TEST_CONNECTION       0x02
#define GET_VERSION           0x03
#define GET_POSITION          0x04
#define SET_THRESHOLD_MOVE    0x05
#define GET_THRESHOLD_MOVE    0x06
#define SET_THRESHOLD_STOP    0x07
#define GET_THRESHOLD_STOP    0x08
#define SET_SAMPLING_PERIOD   0x09
#define GET_SAMPLING_PERIOD   0x0a
#define ERROR                 0xff

// -- Input and outputs --
int outputA = 2; // Arduino pin connected to rotary encoder output A
int outputB = 4; // Arduino pin connected to rotary encoder output B
int aState;      // State of encoder output A
int aLastState;  // Last state of encoder output A
unsigned char serialByte; // For receiving serial communications

// -- Encoder position variables --
long positionCounter = 0;    // Cumulative encoder position counter
long lastPosition = 0;       // Previous encoder position
long velocity = 0;           // Instantaneous velocity of encoder
unsigned long timeStamp = 0; // Time since Arduino was started in ms

boolean runState = 0;     // To track if wheel is moving
int binaryOutputPin = 13; // Output pin to indicate some wheel event
int thresholdMove = 10;   // Velocity threshold that sets output pin high
int thresholdStop = 1;    // Velocity threshold that sets output pin low
unsigned int samplingPeriod = 20; // Velocity sampling period (ms). Must be even.

// -- Timer1 variables
const uint16_t t1_load = 0; // Timer1 counter value
unsigned int t1_comp = samplingPeriod * 62.5; // Initialize Timer1 compare value
// t1_comp = ((x * 0.001 * 16,000,000) / (256)) for a desired x
// milliseconds to pass every counter increment (The constants
// simplify to 62.5)
// Examples:
// 125 > 2 ms
// 625 > 10 ms
// 32150 > 500 ms
// Note: Since 62.5 is odd, if samplingPeriod is an odd
// number, there will be an extra 0.5, and the timer
// will not be counting to exactly the time you want it
// to on every cycle. So only set samplingPeriod to be
// an even number.

void send_position(unsigned long timeStamp, long positionCounter) {
    // Send time and position separated by space
    Serial.print(timeStamp);
    Serial.print(" ");
    Serial.print(positionCounter);
    Serial.println();
}

void setup() {
  // Initialize binary output
  pinMode(binaryOutputPin, OUTPUT);
  digitalWrite(binaryOutputPin, LOW);

  // Set up input pins for rotary encoder
  pinMode(outputA, INPUT);
  pinMode(outputB, INPUT);
  aLastState = digitalRead(outputA); // Read initial state of encoder output A

  Serial.begin(115200); // Initialize serial port
  setUpTimer1();        // Initialize Timer1
}


void loop() {
  // Reads the current state of the outputA
  aState = digitalRead(outputA);

  // If the previous and the current state of the outputA
  // are different then a pulse occurred
  if (aState != aLastState) {
    // If the outputB state is different to the outputA state,
    // then the encoder is rotating clockwise.
    // Otherwise, it's rotating counterclockwise
    if (digitalRead(outputB) != aState) {
      positionCounter ++;
    }
    else {
      positionCounter --;
    }
  }

  // Updates the previous state of outputA with the current state
  aLastState = aState;

  // Check for serial commands from the client
  while (Serial.available() > 0) {
    serialByte = Serial.read();
    switch(serialByte) {
      case TEST_CONNECTION: {
	Serial.write(OK);
	break;
      }
      case GET_VERSION: {
	Serial.println(VERSION);
	break;
      }
      case SET_THRESHOLD_MOVE: {
	thresholdMove = read_int32_serial();
	break;
      }
      case GET_THRESHOLD_MOVE: {
	Serial.println(thresholdMove);
	break;
      }
      case SET_SAMPLING_PERIOD: {
	samplingPeriod = read_int32_serial();
	t1_comp = samplingPeriod * (125 / 2);
	setUpTimer1();
	break;
      }
      case GET_SAMPLING_PERIOD: {
	Serial.println(samplingPeriod);
	break;
      }
      case GET_POSITION: {
	timeStamp = millis();
	send_position(timeStamp, positionCounter);
	break;
      }
    }
  }
}


ISR(TIMER1_COMPA_vect) {
  // Reset the timer counter
  TCNT1 = t1_load;

  // Calculate the velocity
  velocity = abs(positionCounter - lastPosition);
  // If the velocity is over the threshold:
  if (velocity > thresholdMove) {
    // Mouse is running
    runState = 1;
    // Set binary output pin high
    digitalWrite(binaryOutputPin, HIGH);
  }
  else {
    // Mouse isn't running
    runState = 0;
    // Set binary output pin low
    digitalWrite(binaryOutputPin, LOW);
  }

  // Update the last position to be the current position
  // for the next velocity calculation
  lastPosition = positionCounter;
}


void setUpTimer1() {
  cli(); // Stop interrupts
  TCCR1A = 0; // Reset Timer1 control register A

  // Set Timer1 prescaler to 256
  TCCR1B |= (1 << CS12);
  TCCR1B &= ~(1 << CS11);
  TCCR1B &= ~(1 << CS10);

  TCNT1 = t1_load; // Reset Timer1
  OCR1A = t1_comp; // Set compare value
  TIMSK1 = (1 << OCIE1A); // Enable Timer1 overflow interrupt
  sei(); // Enable interrupts
}


unsigned long read_int32_serial() {
  // Read four bytes and combine them (little endian order, LSB first)
  long value = 0;
  for (int ind=0; ind<4; ind++) {
    while (!Serial.available()) {}  // Wait for data
    serialByte = Serial.read();
    value = ((long) serialByte << (8*ind)) | value;
  }
  return value;
}
