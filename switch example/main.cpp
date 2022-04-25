// Messageing client with the RH_RF69 class. Using RHDatagram for addressing.
// Packet header contains to, from, if and flags.
#include <Arduino.h>
#include <SPI.h>
#include <RH_RF69.h>
#include <RHDatagram.h>

// Feather M0 w/Radio
#define RF69_FREQ 433.0
#define RFM69_CS      8
#define RFM69_INT     7 // caution differ to M0 boards
#define RFM69_RST     4

#define CLIENT_ADDRESS 11 // RHDatagram
#define SERVER_ADDRESS 1 // RHDatagram

RH_RF69 rf69(RFM69_CS, RFM69_INT);
RHDatagram manager(rf69, CLIENT_ADDRESS);
uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];

void state(String s){
  int return_state = 0;
  if (s == "2") {
    if (digitalRead(LED_BUILTIN)) {return_state =1;}
    else {return_state = 0;}
  }
  if (s == "1") {
      return_state = 1;
      digitalWrite(LED_BUILTIN, HIGH);}
  if (s == "0"){
      return_state = 0;
      digitalWrite(LED_BUILTIN, LOW);}
    char rpacket[60];
    int n = sprintf(rpacket, "{'%d': %d}", CLIENT_ADDRESS, return_state);
    uint8_t radiopacket[n]; // reduce to the needed packet size 'n'
    //Serial.print("reply with data: ");
    //Serial.println(rpacket);
    memcpy(radiopacket, (const char*)rpacket, sizeof(rpacket));
    // for testing, give the server time to switch between send and receive
    delay(100); 
    manager.sendto(radiopacket, sizeof(radiopacket), SERVER_ADDRESS);
};

String convertToString(char * a, uint8_t size)
{ int i;
String x = "";
for (i=0;i< size;i++)
{x = x +a[i];}
return x;
};

void setup() {
  //Serial.begin(9600);
  //while (!Serial) { delay(1);}
  pinMode(LED_BUILTIN, OUTPUT); digitalWrite(LED_BUILTIN, LOW); // LED off
  // manual reset the radio
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, HIGH); delay(10);
  digitalWrite(RFM69_RST, LOW); delay(10);
  if (!manager.init()) {
    //Serial.println("init failed"); 
    while (1);}
    //Serial.println("RFM69 radio init OK!");
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250,
  //  +13dbM (for low power module) and No encryption
  if (!rf69.setFrequency(RF69_FREQ)) 
  { 
    //Serial.println("setFrequency failed"); 
    while (1);}
    //Serial.println("RFM69 radio frequency OK!");
  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(18, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW
  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 
                    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
  rf69.setEncryptionKey(key);
  state("0"); // restarted
};

void loop() {
   if (manager.available())
  {
    // Wait for a message addressed to us from the client
    uint8_t len = sizeof(buf);
    uint8_t from = SERVER_ADDRESS;
    if (manager.recvfrom(buf, &len, &from))
    {
      //String s = convertToString((char*)buf,len);
      state((char*)buf);
    }
  }
};