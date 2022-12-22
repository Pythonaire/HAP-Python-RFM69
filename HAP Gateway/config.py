#!/usr/bin/env python3
"""App configuration."""
"""Set configuration vars from .env file."""
RFM69GardenURL = 'RFMGarden.local'
RFM69HouseURL = 'RFMHouse.local'
RFMNETWORK ={RFM69GardenURL: {"Pumpe": 11, "Weather": 12 , "RoomTwo": 14}, 
            RFM69HouseURL: {"RoomOne": 13}}
RFMMANAGE = {RFM69GardenURL: 11}

