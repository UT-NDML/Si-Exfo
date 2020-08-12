/*
 Based on ArduinoDRO by Yuriy Krushelnytskiy
 Edits for exfoliation by Martin Ward
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
*/
#include "HX711.h"
#include <Wire.h>
#include "VL6180XMM.cpp"
#include <Encoder.h>
#include <MovingAverage.h>
#include <PID_v1.h>

#define calibration_factor -206950.0 //This value is obtained using the SparkFun_HX711_Calibration sketch
#define zero_factor -63153 //This large value is obtained using the SparkFun_HX711_Calibration sketch

const int DOUT = 5;
const int CLK = 4;

// DRO config (if axis is not connected change in the corresponding constant value from "true" to "false")
boolean const xAxisSupported = true;

// I/O ports config (change pin numbers if DRO, Tach sensor or Tach LED feedback is connected to different ports)
int const clockPin = 2;

int const xDataPin = 3;

//---END OF CONFIGURATION PARAMETERS ---

boolean const droSupported = (xAxisSupported);

//variables that will store the readout
volatile long xCoord;

double Setpoint, Input, Output;
double Kp = .2, Ki = 0.45, Kd = 0.01;
PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);
int enA = 9;

double Setpointp, Inputp, Outputp;
double Kpp = 5, Kip = 20, Kdp = .5;
PID myPIDp(&Inputp, &Outputp, &Setpointp, Kpp, Kip, Kdp, DIRECT);
int PressurePin = 6;

Encoder myEnc(18, 19);
unsigned long measureTime = 0;
long newPosition = 1;
long oldPosition = 0;

volatile uint32_t rpm = 0;
MovingAverage average(5);

//HX711 scale(DOUT, CLK);
HX711 scale;

VL6180XMM sensor;

void setup()
{
  //clock pin should be set as output
  pinMode(clockPin, OUTPUT);
  //data pins should be set as inputs
  pinMode(xDataPin, INPUT);
  //initialize serial port
  Serial.begin(9600);

  Setpoint = 0;
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, 255);
  myPID.SetSampleTime(25);
  pinMode(PressurePin, OUTPUT);  // sets the pin as output
  TCCR4B = (TCCR4B & 0xF8) | 0x01;

  Setpointp = 0;
  myPIDp.SetMode(AUTOMATIC);
  myPIDp.SetOutputLimits(0, 255);
  myPIDp.SetSampleTime(25);
  pinMode(enA, OUTPUT);
  TCCR2B = (TCCR2B & 0xF8) | 0x01;

  average.reset(0.0);

  scale.begin(DOUT, CLK);
  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
  scale.set_offset(zero_factor);

  Wire.begin();
  sensor.init();
  sensor.configureDefault();
  sensor.setTimeout(500);
}
//float mapfloat(float x, float in_min, float in_max, float out_min, float out_max)
//{
//  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
//}
void loop()
{
  xCoord = 0;

  int bitOffset;

  //read the first 20 bits
  for (bitOffset = 0; bitOffset < 21; bitOffset++)
  {
    tickTock();
    //read the pin state and shift it into the appropriate variables
    xCoord |= ((long)digitalRead(xDataPin) << bitOffset);
  }

  tickTock();

  //read the last bit (signified the sign)
  //if it's high, fill 11 leftmost bits with "1"s
  if (digitalRead(xDataPin) == HIGH)
    xCoord |= ((long)0x7ff << 21);

  Setpoint = map(analogRead(A0), 10, 1023, 0, 3600);
  //  Setpointp = mapfloat(analogRead(A1), 1, 1023, 0.0, 9.0);
  Setpointp = map(analogRead(A1), 1, 1023, 0.0, 900) / 100;

  newPosition = myEnc.read();
  rpm = ((abs(oldPosition - newPosition)) * 60000) / (44 * (millis() - measureTime));
  oldPosition = newPosition;
  average.update(rpm);
  Input = average.get();

  Inputp = scale.get_units();
  measureTime = millis();

  Serial.print(measureTime);
  Serial.print(" ");
  Serial.print((long)xCoord);
  Serial.print(" ");
  Serial.print(Inputp);
  Serial.print(" ");
  Serial.print(sensor.readRangeSingleRaw());
  Serial.print(" ");
  Serial.print(rpm);
  Serial.println();

  noInterrupts();
  myPID.Compute();
  myPIDp.Compute();

  analogWrite(enA, Output);
  analogWrite(PressurePin, Outputp);
  interrupts();

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
