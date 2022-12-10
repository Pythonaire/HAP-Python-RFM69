#!/usr/bin/env python3
"""
RFM69XXXUrl : add the DNS Name or IP Adress of your 433MHz Bridge
RFM69XXX_CONTROL: flask interface to send and receive commands to the 433MHzBridge
RFM69XXX_SYNC flask interface to call sensor data, stored in the  433MHzBridge
NODES: give your nodes a name (this name must be equal to the class name of your HAP Python device)
"""

"""Set Flask configuration vars from .env file."""
RFM69GardenURL = 'XXXX.home' # name of RFM69 bridge or Ip Adresee
RFM69Garden_CONTROL = 'http://'+ RFM69GardenURL + ':8001/manageState' # Flask access point to control a device, here a switch
RFM69Garden_SYNC = 'http://' + RFM69GardenURL + ':8001/sync'  # Flask accesspoint to read data cached on the bridge. 
                                                                        # This is useful for devices in sleep mode, who send periodically values
NODES = {"XXXXX":1,"XXXXX":2} # node names and number on the RFM69 network
    

    


