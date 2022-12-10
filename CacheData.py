#!/usr/bin/env python3
import logging
import threading
import requests, json
from requests.exceptions import ConnectTimeout
import config
RTC_DBNAME = config.RTC_DBNAME
logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")


RFM69_CACHE = {}

def call_repeatedly(interval, func):
        stopped = threading.Event()
        def loop():
            while not stopped.wait(stopped.wait(interval)): # the first call is in `interval` secs
                #func(*args)
                func()
        threading.Thread(target=loop, daemon=True).start()    
        return stopped.set



class RFM69Data():
    def __init__(self):
        self.GardenNodes = {k :str(v) for k, v in config.NODES_GARDEN.items()} # switch node number to string, because of easier json handling
        self.GardenUrl = config.RFM69Garden_SYNC
        self.GardenControlUrl = config.RFM69Garden_CONTROL
        self.syncCache() # inital

    def syncCache(self):
        global RFM69_CACHE
        #my_dictionary = {k :str(v) for k, v in self.HouseNodes.items()}
        #logging.info("dict: {0}".format(my_dictionary))
        try:
            dict = requests.get(self.GardenUrl, timeout = 2).json()
            for node in self.GardenNodes.values():
                if node in dict:
                    RFM69_CACHE[node] = dict[node]
                else:
                    RFM69_CACHE[node] = None
        except ConnectTimeout as e:
            logging.info('**** request to {0} timed out: {1}'.format(self.GardenUrl, e))
            for node in self.GardenNodes.values():
                RFM69_CACHE[node] = None
        logging.info('**** Cache refreshed with data from Nodes {0} ****'.format(list(RFM69_CACHE.keys())))

    def controlrfm(self, bridge, node, cmd):
        global RFM69_CACHE
        httpsend = {node: cmd}
        try:
            RFM69_CACHE[node] = requests.get(bridge, json=json.dumps(httpsend), timeout= 2).json()[node]
            #rfm return with json {'node':None} if request failed
            #NODE_CACHE[node] = answer[node]
        except ConnectTimeout as e:
            logging.info('**** request to {0} timed out: {1}'.format(bridge, e)) 
            RFM69_CACHE[node] = None

