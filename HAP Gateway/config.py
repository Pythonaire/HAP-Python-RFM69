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
    RFM69 = 'XXXX.home'
    RFM69_CONFIG = 'http://'+ RFM69 + ':8001/config'
    RFM69_CONTROL = 'http://'+ RFM69 + ':8001/setValue'
    RFM69_CACHE = url = 'http://' + RFM69 + ':8001/cached'
    NODES = {"XXXXX":11,"XXXXX":12}
    NODE_CACHE = {}
    #create empty cache
    for node in NODES.values(): 
        NODE_CACHE[str(node)] = None

    


