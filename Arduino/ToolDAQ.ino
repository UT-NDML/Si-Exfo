#include "HX711.h"
#include <Wire.h>
#include <Encoder.h>
#include <MovingAverage.h>
#include <PID_v1.h>

//#define calibration_factor -206950.0 //This value is obtained using the SparkFun_HX711_Calibration sketch
//#define zero_factor -63153 //This large value is obtained using the SparkFun_HX711_Calibration sketch

const int DOUT = 5;
const int CLK = 4;

double Setpoint, Input, Output;
double Kp = .01, Ki = 0.1, Kd = 0.001;
PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);
int enA = 9;

//double Setpointp, Inputp, Outputp;
double Inputp;
//double Kpp = 5, Kip = 20, Kdp = .5;
//PID myPIDp(&Inputp, &Outputp, &Setpointp, Kpp, Kip, Kdp, DIRECT);
//int PressurePin = 6;

Encoder myEnc(18, 19);
unsigned long measureTime = 0;
long newPosition = 1;
long oldPosition = 0;

volatile uint32_t rpm = 0;
MovingAverage average(10);

HX711 scale;

void setup()
{
  //initialize serial port
  Serial.begin(115200);
  Serial2.begin(115200);
  Setpoint = 0;
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, 255);
  myPID.SetSampleTime(25);
  pinMode(enA, OUTPUT);
  TCCR2B = (TCCR4B & 0xF8) | 0x01;

  average.reset(0.0);

  scale.begin(DOUT, CLK);
  scale.set_scale(-206950.0); //This value is obtained by using the SparkFun_HX711_Calibration sketch
  scale.set_offset(-61003);
}
void loop()
{
 
  Setpoint = map(analogRead(A0), 10, 1023, 0, 3600);
 
  newPosition = myEnc.read();
  rpm = ((abs(oldPosition - newPosition)) * 60000) / (44 * (millis() - measureTime));
  oldPosition = newPosition;
  average.update(rpm);
  measureTime = millis();

  Serial.print(measureTime);
  Serial.print(" ");
//  if (Serial2.read() == 'x') {
  Serial.print(Serial2.parseInt());
//  }
  Serial.print(" ");
  Serial.print(Inputp);
  //  Serial.print(" ");
//  Serial.print(rpm);
  Serial.println();

  noInterrupts();
  Inputp = scale.get_units(3); //3
  Input = average.get();

  myPID.Compute();
  analogWrite(enA, Output);
  interrupts();

}
