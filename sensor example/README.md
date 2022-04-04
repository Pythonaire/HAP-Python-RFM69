# example for weather and soil moisture sensor

- base on a Adafruit RFM69HCW, a BME280 (temperature, air humidity and air pressure) and a DFRobot capacitive sensor measurement
- return Battery state, temperature, humidity, pressure and soil humidity
- powered by Lipo battery, the RTC library is used to set the board into deep sleep between measurements. On wakeup a 2N7000 Mosfet is triggered by PIN and switch the sensors on. After measuring, the trigger PIN is set to LOW, the sensor will be powered off and the board goes into deep sleep.
- the sensor will send his data by its own interval, no need of SEND/ACK needed. The 433 MHZBridge store all new incoming data.
