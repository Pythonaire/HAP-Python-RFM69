#!/usr/bin/env python3
"""App configuration."""
"""Set configuration vars from .env file."""
RFM69GardenURL = 'XXXXXX.local'
RFM69HouseURL = 'XXXXXX.local'
RFMNETWORK ={RFM69GardenURL: {"Pump": 11, "Weather": 12 , "RoomTwo": 14}, 
            RFM69HouseURL: {"RoomOne": 13}}
RFMMANAGE = {RFM69GardenURL: 11}

