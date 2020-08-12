/*
 Based on ArduinoDRO by Yuriy Krushelnytskiy
 Edits for exfoliation by Maritn Ward
 *******************************************

  ArduinoDRO + Tach V3

  Reading Grizzly iGaging Digital Scales V2.1 Created 19 January 2012
  Updated 03 April 2013
  by Yuriy Krushelnytskiy
  http://www.yuriystoys.com

  Updated 01 June 2014 by Ryszard Malinowski
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

  Added support for tachometer on axis T (input pin 7)

  NOTE: This program supports hall-sensor to measure rpm.  The tach output format for Android DRO is T<time>/<retation>.
  Android DRO application must support this format for axis T.

  Configuration parameters:
  <n>AxisSupported
    Defines if DRO functionality on axis <n> should be supported.
    If supported DRO scale should be connected to I/O pin defined in constant "<n>DataPin" and
    DRO data is sent to serial port with corresponding axis prefix (X, Y, Z or W)
    Clock pin is common for all scales should be connected to I/O pin defined in constant "clockPin"
    Possible values:
      true = DRO functionality on axis <n> is supported
      false = DRO functionality on axis <n> is not supported
    Default value = true

  tachSupported
    Defines if tach sensor functionality should be supported.
    If supported tach sensor should be connected to I/O pin defined in constant "tachPin" and
    rpm value is sent to serial port with axis prefix "T"
    Possible values:
      true = tach sensor functionality is supported
      false = tach sensor functionality is not supported
    Default value = true

  clockPin
    Defines the I/O pin where clock signal for all DRO scales is connected
    Possible values:
      integer number between 2 and 13
    Default value = 2

  <n>DataPin
    Defines the I/O pin where DRO data signal for selected scale is connected
    Possible values:
      integer number between 2 and 13
    Default values = 3, 4, 5, 6 (for corresponding axis X, Y, Z and W)

  tachPin
    Defines the I/O pin where tach sensor signal is connected
    Possible values:
      integer number between 2 and 13
    Default value = 7

  tachLedFeedbackPin
    Defines the I/O pin where tach LED feedback is connected.
    Tach LED feedback indicates the status of tachPin for debugging purposes
    Possible values:
      integer number between 2 and 13
    Default value = 13 (on-board LED)

  minRpmDelay
    Defines the delay (in milliseconds) in showing 0 when rotation stops.  If rpm is so low and time between tach pulse
    changes longer than this value, value zero rpm ("T0;") will be sent to the serial port.
    Note: this number will determine the slowest rpm that can be measured.  In order to measure smaller rpm I suggest
          to use a sensor with more than one "ticks per revolution" (for example hall sensor with two or more magnets).
          The number of "ticks per revolution" should be set in tachometer setting in Android app.
    Possible values:
      any integer number > 0
    Default value = 1200 (the minimum rpm measured will be 50 rpm)

---VL61080X---
    This example shows how to change the range scaling factor
of the VL6180X. The sensor uses 1x scaling by default,
giving range measurements in units of mm. Increasing the
scaling to 2x or 3x makes it give raw values in units of 2
mm or 3 mm instead. In other words, a bigger scaling factor
increases the sensor's potential maximum range but reduces

*/


// DRO config (if axis is not connected change in the corresponding constant value from "true" to "false")
boolean const xAxisSupported = true;


// I/O ports config (change pin numbers if DRO, Tach sensor or Tach LED feedback is connected to different ports)
int const clockPin = 2;

int const xDataPin = 3;

//---END OF CONFIGURATION PARAMETERS ---

boolean const droSupported = (xAxisSupported);

//variables that will store the readout
volatile long xCoord;

// HX711 Load Cell

#include "HX711.h"
#include <Wire.h>
#include <VL6180XM.h>

#define calibration_factor 206950.0 //This value is obtained using the SparkFun_HX711_Calibration sketch
#define zero_factor -63153 //This large value is obtained using the SparkFun_HX711_Calibration sketch

#define DOUT  5
#define CLK  4

HX711 scale(DOUT, CLK);

unsigned long tms;

VL6180XM sensor;
//The setup function is called once at startup of the sketch
void setup()
{
  //clock pin should be set as output
  if (droSupported)
    pinMode(clockPin, OUTPUT);

  //data pins should be set as inputs
  if (xAxisSupported)
    pinMode(xDataPin, INPUT);

  //initialize serial port
  Serial.begin(9600);

  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
  scale.set_offset(zero_factor);

  Wire.begin();
  sensor.init();
  sensor.configureDefault();
  sensor.setTimeout(500);
}


// The loop function is called in an endless loop
void loop()
{

  tms = millis();

  //readTach() is called so often to provide the greatest accuracy
  if (droSupported)
  {
    xCoord = 0;

    int bitOffset;

    //read the first 20 bits
    for (bitOffset = 0; bitOffset < 21; bitOffset++)
    {
      tickTock();

      //read the pin state and shift it into the appropriate variables
      if (xAxisSupported)
        xCoord |= ((long)digitalRead(xDataPin) << bitOffset);

    }

    tickTock();

    //read the last bit (signified the sign)
    //if it's high, fill 11 leftmost bits with "1"s
    if (xAxisSupported) {
      if (digitalRead(xDataPin) == HIGH)
        xCoord |= ((long)0x7ff << 21);
    }

    //print DRO positions to the serial port
    Serial.print(tms);
    Serial.print(" ");
    if (xAxisSupported) {
      //Serial.print("X");

      Serial.print((long)xCoord);
    }
    Serial.print(" ");
    Serial.print(scale.get_units(), 2);

    Serial.print(" ");
    Serial.print(sensor.readRangeSingleRaw());
    Serial.println();
  }
  delay(1);
}


// Clock DRO scales
inline void tickTock()
{
  //tick
  digitalWrite(clockPin, HIGH);

  //If the scale output is floating all over the place comment lines 99-102 and uncomment line 106.

  //Alternative 1: Use "software" delay (works better on UNO)
  //give the scales a few microseconds to think about it
  for (byte i = 0; i < 20; i++)
  {
    __asm__("nop\n\t");
  }

  //Alternative 2: Use proper delay
  //give the scales a few microseconds to think about it
  //delayMicroseconds(2);

  //tock
  digitalWrite(clockPin, LOW);
}
