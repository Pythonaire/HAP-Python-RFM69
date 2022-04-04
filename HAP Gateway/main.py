#!/usr/bin/env python3
import logging, signal, os, time, sys
from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver
import Devices
from pyhap.loader import Loader as Loader

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

persist_file = 'devices.state'

"""
by importing Devices, the node definitions are loaded, see config.py
NODES = {"MyNodeName":11,"MyNodeName":12, ....}
The the dictionary key must refer to the device class, the value is the RFM69 node number to reach the 433MHz connected device.
with 'loader' own HAP service and characteristics are loaded
"""
loader = Loader(path_char='CharacteristicDefinition.json',path_service='ServiceDefinition.json')

def get_bridge(driver):
    bridge = Bridge(driver, 'MyHAPBridge')
    for item in Devices.NODES: # load devices/class defined by 'NODES' dictionary in config.py
        DeviceClass = getattr(Devices,item)
        NodeNumber = Devices.NODES[item]
        bridge.add_accessory(DeviceClass(NodeNumber, driver, item))
        logging.info('****** add RFM69 Accessory: {0}, Number: {1} *****'.format(item, NodeNumber))
    SOIL = Devices.Moisture(12, driver, 'Soil Moisture') # needed to be separated because of new eve app
    bridge.add_accessory(SOIL)
    return bridge

try:
    driver = AccessoryDriver(port=51826, persist_file= persist_file, loader=loader)
    driver.add_accessory(accessory=get_bridge(driver))
    signal.signal(signal.SIGTERM, driver.signal_handler)
    driver.start()
except Exception as e:
    logging.info('**** Could connect HAP Service: {0}'.format(e))
    os.kill(os.getpid(), signal.SIGKILL)
    
