#!/usr/bin/env python3
#import atexit
import logging
import os
import signal
import config
import Devices
from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.loader import Loader as Loader

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

persist_file = 'devices.state'

"""
The bridge mixed up normal devices reached by Wifi, Devices connect through databases and RFM69 based devices connected through 433 MHz network.
RFM69 devices:
    Node numbers of RFM69 devices are stored in the config.py Class.
    example:
    NODES = {"Pumpe":11,"Weather":12}
The the dictionary key must refer to the device class, the value is the RFM69 node number to reach the 433MHz connected device.
While loading/importing Devices, classes and Nodes will be binded 
"""
loader = Loader(path_char='CharacteristicDefinition.json',path_service='ServiceDefinition.json')

#def exit_handler():
#    CallRTCDevice.set()
#    logging.info('****** terminate setInterval ********')


#atexit.register(exit_handler)

def get_bridge(driver):
    bridge = Bridge(driver, 'MacServer')
    # mixed Devices
    Nodes = {}
    for i in list(config.RFMNETWORK.values()):
        Nodes.update(i)
    for className, NodeNumber in Nodes.items():
        DeviceClass = getattr(Devices, className)
        bridge.add_accessory(DeviceClass(NodeNumber, driver, className))
        logging.info('****** add RFM69 Accessory: {0}, Number: {1} *****'.format(className, NodeNumber))
    Soil = Devices.Moisture(12, driver, 'Soil Moisture') # needed to be separated because of new eve app
    bridge.add_accessory(Soil)
    return bridge

try:
    driver = AccessoryDriver(port=51826, persist_file= persist_file, loader=loader)
    driver.add_accessory(accessory=get_bridge(driver))
    signal.signal(signal.SIGTERM, driver.signal_handler)
    driver.start()
except Exception as e:
    logging.info('**** Could connect HAP Service: {0}'.format(e))
    os.kill(os.getpid(), signal.SIGKILL)