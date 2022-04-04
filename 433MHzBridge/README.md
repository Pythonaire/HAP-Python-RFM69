# communication between 433MHz network and HAP-Python Gateway

The system is configured for two comminications:

- "spontanously" sensor data: in this case sensors deliver data by there own interval over the 433MHz network. The 433 MHzBridge detect incoming data and store them.
- "time critical" communication: to control a switch.

To communicate with the HAP-Python Gateway, Flask is used. The last states of sensor or switches are hold in the cache - the last values received from sensors or the last state requested by the HAP-Python Gateway and the response from the 433MHz device.
As tested, through thick walls and over obstacles a signal delay of 0.3 ms on the 433 MHz network is a good value.

