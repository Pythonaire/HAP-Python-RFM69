#include <Arduino.h>
#include <RH_RF69.h>
#include <RHDatagram.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <RTCZero.h>

#define BMEPOWER A3
#define SEN0308POWER A1
#define SEN0308DATA A0
#define VBATPIN A7 // measuring battery
// Feather M0 w/Radio
#define RF69_FREQ 433.0
#define RFM69_CS      8
#define RFM69_INT     3
#define RFM69_RST     4
#define CLIENT_ADDRESS 12 // RHDatagram
#define SERVER_ADDRESS 1 // RHDatagram

Adafruit_BME280 bme;
// Singleton instance of the radio driver
RH_RF69 rf69(RFM69_CS, RFM69_INT);
RHDatagram manager(rf69, CLIENT_ADDRESS);

/* Create an rtc object */
RTCZero rtc;
const bool resetTime = true;
const uint8_t wait = 30;
const byte seconds = 00;
const byte minutes = 00;
const byte hours = 10;    
const byte day = 1;
const byte month = 1;
const byte year = 20;

int Voltage;
int AirHumidity;
int AirTemperature;
int AirPressure;
int soilMeasurement;
int soilMoisture;

void ReadBattery() {
  //digitalWrite(VBATPIN, HIGH);delay(50);
  float measuredvbat = analogRead(VBATPIN);
  //digitalWrite(VBATPIN, LOW);
  measuredvbat *=2; // we divided by 2, so multiply back
  measuredvbat *=3.3; // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage
  if (measuredvbat>4.25f){measuredvbat=4.25f;}
  Voltage = roundf(100*measuredvbat/4.25f);
 };

 void ReadBME(){
   digitalWrite(BMEPOWER,HIGH);delay(50);
  //if (!bme.begin(0x76)) {
  //  Serial.println(F("Could not find a valid BME280 sensor, check wiring!"));
  //  while (1) delay(10);
  //}
  AirTemperature = 0;
  AirHumidity = 0;
  AirPressure = 0;
  bme.begin(0x76); delay(10);
  AirTemperature = roundf(bme.readTemperature());
  AirHumidity = roundf(bme.readHumidity());
  AirPressure = roundf(bme.readPressure() / 100.0F); // hPa
  digitalWrite(BMEPOWER, LOW);
 }

void ReadSEN0308() {
  digitalWrite(SEN0308POWER, HIGH);delay(100);
  soilMeasurement = 0;
  for (int i=0;i<5;i++)
  {soilMeasurement = soilMeasurement + analogRead(SEN0308DATA);delay(100);} 
  soilMoisture = roundf(soilMeasurement/5);
  digitalWrite(SEN0308POWER, LOW);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT); digitalWrite(LED_BUILTIN, LOW);// LED off       
  pinMode(BMEPOWER, OUTPUT);pinMode(SEN0308POWER, OUTPUT);pinMode(RFM69_RST, OUTPUT);
  //Serial.begin(9600);
  //while (!Serial){ delay(10);} 
  digitalWrite(RFM69_RST, HIGH); delay(10);
  digitalWrite(RFM69_RST, LOW); delay(10);
  if (!manager.init()) {
   //Serial.println("init failed"); 
    while (1);}
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250,
  //  +13dbM (for low power module) and No encryption
  if (!rf69.setFrequency(RF69_FREQ)) { 
  //Serial.println("setFrequency failed"); 
  while (1);
   }
  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(18, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW
  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
  rf69.setEncryptionKey(key); 
  rtc.begin(resetTime);
  rtc.setTime(hours, minutes, seconds);
  rtc.setDate(day, month, year);
};
void alarmMatch() {
  rtc.setTime(hours, minutes, seconds);
  rtc.setDate(day, month, year);
};
void loop()
{
ReadBattery();
ReadBME();
ReadSEN0308();
char rpacket[60]; // max packet length RFM69 60 Byte
// create JSON Form to easier produce on Server side
int n = sprintf(rpacket, "{'%d':{'B':%d,'AT':%d,'AH':%d,'AP':%d,'SH':%d}}", 
CLIENT_ADDRESS, Voltage, AirTemperature, AirHumidity, AirPressure, soilMoisture);
//Serial.printf("[%s] is a string %d chars long\n",rpacket,n);
uint8_t radiopacket[n]; // reduce to the needed packet size 'n'
memcpy(radiopacket, (const char*)rpacket, sizeof(rpacket));
manager.sendto(radiopacket, sizeof(radiopacket), SERVER_ADDRESS);
delay(50);
rf69.sleep(); 
rtc.setAlarmMinutes(wait);
rtc.setAlarmSeconds(0);
rtc.enableAlarm(rtc.MATCH_MMSS);
rtc.attachInterrupt(alarmMatch);
rtc.standbyMode();
};