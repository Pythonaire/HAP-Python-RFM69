# HAP-Python-RFM69

This implementation has two parts: The HAP-Python Gateway and a 433MHzBridge to requests and receive data to/from 433MHz devices.

## Equipment

For the HAP Gateway and the the 433MHz Bridge you can use Raspberry Pi's (Zero W, 3B+ 4) or other linux systems like Ubuntu.
The RFM69 devices are in my case Adafruit RFM69HCW Feather boards.

## Installation

## HAP-Python

To use this fist you need to install the HAP-Python HAP-Python <https://github.com/ikalchev/HAP-python> by:

````
sudo apt-get install libavahi-compat-libdnssd-dev
pip3 install HAP-python[QRCode]
`````

Because of Apple changing there Accessory implementation and i like to define my own Accessories, i use my own service and characteristic definitions.

````
loader = Loader(path_char='CharacteristicDefinition.json',path_service='ServiceDefinition.json')
...
driver = AccessoryDriver(port=51826, persist_file= persist_file, loader=loader)
````

Next you need to specify the RFM69 devices in a dictionary, with Node name and node number. See config.py. Note, that the name of your node must be the same as the corresponding HAP-Python device class.
The main script will read the node definition and load the corresponding device class for further information about the device itself. Each device class represent a HAP Accessory.

In Device.py you can find two examples: a weather sensor and a switch.
Each device class call data from the 433MHzBridge in the set interval. The 433MHzBridge use a Flask server to answer these requests and return sensor values, or send commands to and receive states from the switch.

At this time, the 433MHzBridge need the node definition too (RFM69.json). The next todo here is to automatically exchange node definitions across the whole implementation.

## 433MHzBridge

For the 433MHzBridge you will need Flask.

````
sudo pip3 install flask

`````







