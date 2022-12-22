#!/usr/bin/env python3
"""App configuration."""
"""Set configuration vars from .env file."""
RFM69GardenURL = 'RFMGarden.local'
RFM69HouseURL = 'RFMHouse.local'
RADIO_URL = 'http://PiRadio.local:8001/postjson'
RFMNETWORK ={RFM69GardenURL: {"Pumpe": 11, "Weather": 12 , "RoomTwo": 14}, 
            RFM69HouseURL: {"RoomOne": 13}}
RFMMANAGE = {RFM69GardenURL: 11}
#conf for RTC Access
RTCDEVICE = '192.168.0.143'
RTC_DBNAME = '/home/pwiechmann/database/Photovoltaic.db'
