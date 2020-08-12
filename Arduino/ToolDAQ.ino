/*
 Based on ArduinoDRO by Yuriy Krushelnytskiy
 Edits for exfoliation by Maritn Ward
 *******************************************
 
 ArduinoDRO + Tach V5.11
 
 iGaging/AccuRemote Digital Scales Controller V3.3
 Created 5 July 2014
 Update 15 July 2014
 Copyright (C) 2014 Yuriy Krushelnytskiy, http://www.yuriystoys.com
 
 
 Updated 02 January 2016 by Ryszard Malinowski
 http://www.rysium.com 

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

 
 Version 2.b - Added support for tachometer on axis T with accurate timing
 Version 3.0 - Added option to send rpm raw data (time and count)
 Version 5.2 - Correction to retrieving scale sign bit.
 Version 5.2 - Corrected scale frequency clock.
 Version 5.2 - Added option to pre-scale tach reading compensating for more than one tach pulse per rotation.
 Version 5.3 - Added option to average and round tach output values.
 Version 5.3 - Added option to select max tach update frequency
 Version 5.4 - Replace Yuriy's method of clocking scales with method written by Les Jones
 Version 5.5 - Optimizing the scale reading logic using method written by Les Jones
 Version 5.6 - Adding 4us delay between scale clock signal change and reading first axis data
 Version 5.7 - Added option to smooth DRO reading by implementing weighted average with automatic smoothing factor
 Version 5.8 - Correction to calculate average for scale X. Increase weighted average sample size to 32.
 Version 5.9 - Reduce flickering on RPM display.  Remove long delay in RPM displaying Zero after the rotation stops.
 Version 5.10 - Add "smart rounding" on tach display.  Fix 1% tach rounding.  Support processors running at 8MHz clock.
 Version 5.11 - Add "touch probe" support.
 
 
 NOTE: This program supports pulse sensor to measure rpm and switch type touch probe .  
 
 Configuration parameters:
  SCALE_<n>_ENABLED
    Defines if DRO functionality on axis <n> should be supported.  
    If supported DRO scale should be connected to I/O pin defined in constant "<n>DataPin" and 
    DRO data is sent to serial port with corresponding axis prefix (X, Y, Z or W)
    Clock pin is common for all scales should be connected to I/O pin defined in constant "clockPin" 
    Possible values:
      1 = DRO functionality on axis <n> is supported
      0 = DRO functionality on axis <n> is not supported
    Default value = 1

  SCALE_CLK_PIN
    Defines the I/O pin where clock signal for all DRO scales is connected
    Possible values:
      integer number between 2 and 13
    Default value = 2

  SCALE_<n>_PIN
    Defines the I/O pin where DRO data signal for selected scale is connected
    Possible values:
      integer number between 2 and 13
    Default values = 3, 4, 5, 6 (for corresponding axis X, Y, Z and W)

  SCALE_<n>_AVERAGE_ENABLED
    Defines if DRO reading should be averaged using weighted average calculation with automating smoothing factor.   
    If average is enabled the reading is much more stable without "jumping" and "flickering" when the scale "can't decide" on the value.  
    Note: This value is not used when corresponding SCALE_<n>_ENABLED is 0 
    Possible values:
      0 = exact measured from the scale is sent
      1 = scale reading averaged using weighted average calculation with automatic smoothing factor
    Default value = 1

  AXIS_AVERAGE_COUNT
    Defines the number of last DRO readings that will be used to calculate weighted average for DRO.
    For machines with power feed on any axis change this value to lower number i.e. 8 or 16.
    Possible values:
      integer number between 4 and 32 
    Recommended values:
      16 for machines with power feed 
      32 for all manual machines
    Default value = 24

  UART_BAUD_RATE
    Defines the serial port baud rate.  Make sure it matches the Bluetooth module's baud rate.
    Recommended value:
      1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200
    Default value = 9600

  UPDATE_FREQUENCY
    Defines the Frequency in Hz (number of timer per second) the scales are read and the data is sent to the application.
    Possible values:
      any integer number between 1 and 64 
    Default value = 24
    
 */
 

// DRO config (if axis is not connected change in the corresponding constant value from "1" to "0")
#define SCALE_X_ENABLED 1

// I/O ports config (change pin numbers if DRO, Tach sensor or Tach LED feedback is connected to different ports)
#define SCALE_CLK_PIN 2

#define SCALE_X_PIN 3

// DRO rounding On/Off (if not enabled change in the corresponding constant value from "1" to "0")
#define SCALE_X_AVERAGE_ENABLED 0

// DRO rounding sample size.  Change it to 16 for machines with power feed
#define AXIS_AVERAGE_COUNT 24

// General Settings
#define UART_BAUD_RATE 9600       //  Set this so it matches the BT module's BAUD rate 
#define UPDATE_FREQUENCY 24       //  Frequency in Hz (number of timer per second the scales are read and the data is sent to the application)

//---END OF CONFIGURATION PARAMETERS ---


//---DO NOT CHANGE THE CODE BELOW UNLESS YOU KNOW WHAT YOU ARE DOING ---

/* iGaging Clock Settings (do not change) */
#define SCALE_CLK_PULSES 21       //iGaging and Accuremote scales use 21 bit format
#define SCALE_CLK_FREQUENCY 9000    //iGaging scales run at about 9-10KHz
#define SCALE_CLK_DUTY 20       // iGaging scales clock run at 20% PWM duty (22us = ON out of 111us cycle)

/* weighted average constants */ 
#define FILTER_SLOW_EMA AXIS_AVERAGE_COUNT  // Slow movement EMA
#define FILTER_FAST_EMA 2           // Fast movement EMA

#if (SCALE_X_ENABLED > 0) || (SCALE_Y_ENABLED > 0) || (SCALE_Z_ENABLED > 0) || (SCALE_W_ENABLED > 0)
#define DRO_ENABLED 1
#else
#define DRO_ENABLED 0
#endif

#if (SCALE_X_AVERAGE_ENABLED > 0) || (SCALE_Y_AVERAGE_ENABLED > 0) || (SCALE_Z_AVERAGE_ENABLED > 0) || (SCALE_W_AVERAGE_ENABLED > 0)
#define SCALE_AVERAGE_ENABLED 1
#else
#define SCALE_AVERAGE_ENABLED 0
#endif

// Define registers and pins for ports
#if SCALE_CLK_PIN < 8 
#define CLK_PIN_BIT SCALE_CLK_PIN
#define SCALE_CLK_DDR DDRD
#define SCALE_CLK_OUTPUT_PORT PORTD
#else
#define CLK_PIN_BIT (SCALE_CLK_PIN - 8)
#define SCALE_CLK_DDR DDRB
#define SCALE_CLK_OUTPUT_PORT PORTB
#endif

#if SCALE_X_PIN < 8 
#define X_PIN_BIT SCALE_X_PIN
#define X_DDR DDRD
#define X_INPUT_PORT PIND
#else
#define X_PIN_BIT (SCALE_X_PIN - 8)
#define X_DDR DDRB
#define X_INPUT_PORT PINB
#endif


// Some constants calculated here

int const updateFrequencyCounterLimit = (int) (((unsigned long) SCALE_CLK_FREQUENCY) /((unsigned long) UPDATE_FREQUENCY));
int const clockCounterLimit = (int) (((unsigned long) (F_CPU/8)) / (unsigned long) SCALE_CLK_FREQUENCY) - 10;
int const scaleClockDutyLimit = (int) (((unsigned long) (F_CPU/800)) * ((unsigned long) SCALE_CLK_DUTY) / (unsigned long) SCALE_CLK_FREQUENCY);
int const scaleClockFirstReadDelay = (int) ((unsigned long) F_CPU/4000000);


//variables that will store the DRO readout
volatile boolean tickTimerFlag;
volatile int updateFrequencyCounter;

// Axis count
#if SCALE_X_ENABLED > 0
volatile long xValue;
volatile long xReportedValue;
#endif
#if SCALE_X_AVERAGE_ENABLED > 0
volatile long axisLastReadX[AXIS_AVERAGE_COUNT];
volatile int axisLastReadPositionX;
volatile long axisAMAValueX;
#endif

// HX711 Load Cell

#include "HX711.h"

#define calibration_factor -206950.0 //This value is obtained using the SparkFun_HX711_Calibration sketch
#define zero_factor -17605 //This large value is obtained using the SparkFun_HX711_Calibration sketch

#define DOUT  5
#define CLK  4

HX711 scale(DOUT, CLK);

//The setup function is called once at startup of the sketch
void setup()
{
  cli();
  tickTimerFlag = false;
  updateFrequencyCounter = 0;

// Initialize DRO values
#if DRO_ENABLED > 0
  
  // clock pin should be set as output
  SCALE_CLK_DDR |= _BV(CLK_PIN_BIT);
  // set the clock pin to low
  SCALE_CLK_OUTPUT_PORT &= ~_BV(CLK_PIN_BIT);

  //data pins should be set as inputs
#if SCALE_X_ENABLED > 0
    X_DDR &= ~_BV(X_PIN_BIT);
  xValue = 0L;
  xReportedValue = 0L;
#if SCALE_X_AVERAGE_ENABLED > 0
  initializeAxisAverage(axisLastReadX, axisLastReadPositionX, axisAMAValueX);
#endif
#endif

#endif

  //initialize serial port
  Serial.begin(UART_BAUD_RATE);

  //initialize timers
  setupClkTimer();

  sei();  

}


// The loop function is called in an endless loop
void loop()
{

  if (tickTimerFlag) {
    tickTimerFlag = false;

#if DRO_ENABLED > 0
    //print DRO positions to the serial port
#if SCALE_X_ENABLED > 0
#if SCALE_X_AVERAGE_ENABLED > 0
    scaleValueRounded(xReportedValue, axisLastReadX, axisLastReadPositionX, axisAMAValueX);
#endif
    //Serial.print(F("X"));
    Serial.print(millis()/1000);
    Serial.print(" ");
    Serial.print((long)xReportedValue);
    Serial.print(" ");
    //Serial.print(scale.get_units(), 2);
    Serial.println();
#endif

#endif

  }
}


//initializes clock timer
void setupClkTimer()
{
  updateFrequencyCounter = 0;

  TCCR2A = 0;     // set entire TCCR2A register to 0
  TCCR2B = 0;     // same for TCCR2B

  // set compare match registers
#if DRO_ENABLED > 0
  OCR2A = scaleClockDutyLimit;      // default 44 = 22us
#else
  OCR2A = clockCounterLimit - 1;
#endif
  OCR2B = clockCounterLimit;      // default 222 = 111us

  // turn on Fast PWM mode
  TCCR2A |= _BV(WGM21) | _BV(WGM20);

  // Set CS21 bit for 8 prescaler //CS20 for no prescaler
  TCCR2B |= _BV(CS21);

  //initialize counter value to start at low pulse
#if DRO_ENABLED > 0
  TCNT2  = scaleClockDutyLimit + 1;
#else
  TCNT2  = 0;
#endif
  // enable timer compare interrupt A and B
  TIMSK2 |= _BV(OCIE2A) | _BV(OCIE2B);
  
}



/* Interrupt Service Routines */

// Timer 2 interrupt B ( Switches clock pin from low to high 21 times) at the end of clock counter limit
ISR(TIMER2_COMPB_vect) {

  // Set counter back to zero  
  TCNT2  = 0;  
#if DRO_ENABLED > 0
  // Only set the clock high if updateFrequencyCounter less than 21
  if (updateFrequencyCounter < SCALE_CLK_PULSES) {
    // Set clock pin high
    SCALE_CLK_OUTPUT_PORT |= _BV(CLK_PIN_BIT);
  }
#endif
}


// Timer 2 interrupt A ( Switches clock pin from high to low) at the end of clock PWM Duty counter limit
ISR(TIMER2_COMPA_vect) 
{
#if DRO_ENABLED > 0

  // Control the scale clock for only first 21 loops
  if (updateFrequencyCounter < SCALE_CLK_PULSES) {
  
    // Set clock low if high and then delay 2us
    if (SCALE_CLK_OUTPUT_PORT & _BV(CLK_PIN_BIT)) {
      SCALE_CLK_OUTPUT_PORT &= ~_BV(CLK_PIN_BIT);
      TCNT2  = scaleClockDutyLimit - scaleClockFirstReadDelay;
      return;
    }

    // read the pin state and shift it into the appropriate variables
    // Logic by Les Jones:
    //  If data pin is HIGH set bit 20th of the axis value to '1'.  Then shift axis value one bit to the right
    //  This is called 20 times (for bits received from 0 to 19)
    if (updateFrequencyCounter < SCALE_CLK_PULSES - 1) {
#if SCALE_X_ENABLED > 0
      if (X_INPUT_PORT & _BV(X_PIN_BIT))
        xValue |= ((long)0x00100000 );
      xValue >>= 1;
#endif



    } else if (updateFrequencyCounter == SCALE_CLK_PULSES - 1) {

      //If 21-st bit is 'HIGH' inverse the sign of the axis readout
#if SCALE_X_ENABLED > 0
      if (X_INPUT_PORT & _BV(X_PIN_BIT))
        xValue |= ((long)0xfff00000);
      xReportedValue = xValue;
      xValue = 0L;
#endif

      // Tell the main loop, that it's time to sent data
      tickTimerFlag = true;

    }
  }
#else
  if (updateFrequencyCounter == 0) {
    // Tell the main loop, that it's time to sent data
    tickTimerFlag = true;
  }
#endif
  
  updateFrequencyCounter++;
  // Start of next cycle 
  if ( updateFrequencyCounter >= updateFrequencyCounterLimit) {
    updateFrequencyCounter = 0;
  }

}


#if DRO_ENABLED > 0
#if SCALE_AVERAGE_ENABLED > 0
inline void initializeAxisAverage(volatile long axisLastRead[], volatile int &axisLastReadPosition, volatile long &axisAMAValue) {
  
  for (axisLastReadPosition = 0; axisLastReadPosition < (int) AXIS_AVERAGE_COUNT; axisLastReadPosition++) {
    axisLastRead[axisLastReadPosition] = 0;
  }
  axisLastReadPosition = 0;
  axisAMAValue = 0;

}

inline void scaleValueRounded(volatile long &ReportedValue, volatile long axisLastRead[], volatile int &axisLastReadPosition, volatile long &axisAMAValue)
{

  int last_pos; 
  int first_pos;
  int prev_pos;
  int filter_pos;


  long dir;
  long minValue = longMax;
  long maxValue = longMin;
  long volatility = 0;
  long valueRange;
  long ssc;
  long constant;
  long delta;

  // Save current read and increment position 
  axisLastRead[axisLastReadPosition] = ReportedValue;
  last_pos = axisLastReadPosition;

  axisLastReadPosition++;
  if (axisLastReadPosition == (int) AXIS_AVERAGE_COUNT) {
    axisLastReadPosition = 0;
  }
  first_pos = axisLastReadPosition;
  
    dir = (axisLastRead[first_pos] - axisLastRead[last_pos]) * ((long) 100);

    // Calculate the volatility in the counts by taking the sum of the differences
    prev_pos = first_pos;
    for (filter_pos = (first_pos + 1) % AXIS_AVERAGE_COUNT;
         filter_pos != first_pos;
         filter_pos = (filter_pos + 1) % AXIS_AVERAGE_COUNT)
    {
        minValue = MIN(minValue, axisLastRead[filter_pos]);
        maxValue = MAX(maxValue, axisLastRead[filter_pos]);
        volatility += ABS(axisLastRead[filter_pos] - axisLastRead[prev_pos]);
        prev_pos = filter_pos;
    }

    // Just return the read if there is no volatility to avoid divide by 0
    if (volatility == (long) 0)
    {
    axisAMAValue = axisLastRead[last_pos] * ((long) 100);
    return;
    }
  
    // If the last AMA is not within twice the sample range, then assume the position jumped
    // and reset the AMA to the current read
  maxValue = maxValue * ((long) 100);
  minValue = minValue * ((long) 100);
    valueRange = maxValue - minValue;
    if (axisAMAValue > maxValue + valueRange + ((long) 100) ||
        axisAMAValue < minValue - valueRange - ((long) 100))
    {
    axisAMAValue = axisLastRead[last_pos] * ((long) 100);
    return;
    }

    // Calculate the smoothing constant
    ssc = (ABS(dir / volatility) * fastSc) + slowSc;
    constant = (ssc * ssc) / ((long) 10000);

    // Calculate the new average
  delta = axisLastRead[last_pos] - (axisAMAValue / ((long) 100));
  axisAMAValue = axisAMAValue + constant * delta; 

    ReportedValue = (axisAMAValue + ((long) 50)) / ((long) 100);
  return;

}

inline long MIN(long value1, long value2){
  if(value1 > value2) {
    return value2;
  } else {
    return value1;
  }
}

inline long MAX(long value1, long value2){
  if(value1 > value2) {
    return value1;
  } else {
    return value2;
  }
}

inline long ABS(long value){
  if(value < 0) {
    return -value;
  } else {
    return value;
  }
}

#endif
#endif

