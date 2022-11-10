#!/usr/bin/env python3
"""
RFM69 : add the DNS Name or IP Adress of your 433MHz Bridge
RFM69_CONFIG: flask interface for later use, to hand over device definitions (not used yet)
RFM69_CONTROL: flask interface to send and receive commands to the 433MHzBridge
RFM69_CACHE: flask interface to call sensor data, stored in the  433MHzBridge
NODES: give your nodes a name (this name must be equal to the class name of your HAP Python device)
NODE_CACHE: local cache, hold data received from the 433MHzBridge
"""


class Config:
    """Set Flask configuration vars from .env file."""
    RFM69Garden = 'XXXX.home' # name of RFM69 bridge or Ip Adresee
    RFM69Garden_CONTROL = 'http://'+ RFM69Garden + ':8001/setValue' # Flask access point to control a device, here a switch
    RFM69Garden_CACHE = url = 'http://' + RFM69Garden + ':8001/cached'  # Flask accesspoint to read data cached on the bridge. 
                                                                        # This is useful for devices in sleep mode, who send periodically values
    NODES = {"XXXXX":1,"XXXXX":2} # node names and number on the RFM69 network
    NODE_CACHE = {} # prepare a emty cache
    #create empty cache
    for node in NODES.values(): 
        NODE_CACHE[str(node)] = None

    


