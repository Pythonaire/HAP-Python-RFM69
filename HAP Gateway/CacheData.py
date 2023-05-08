#!/usr/bin/env python3
import logging
import sqlite3 as sql
import threading
from sqlite3 import Error
import requests, json
from requests.exceptions import ConnectTimeout
import config

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
        self.syncCache() # inital

    @classmethod   
    def syncCache(cls):
        global RFM69_CACHE
        for link, dictNodes in config.RFMNETWORK.items():
            url = 'http://' + link + ':8001/sync'
            nodes = {k :str(v) for k, v in dictNodes.items()}
            try:
                dict = requests.get(url, timeout=2).json()
                for node in nodes.values():
                    if node in dict:
                        RFM69_CACHE[node] = dict[node]
                    else:
                        RFM69_CACHE[node] = None
                logging.info('**** Cache refreshed with data from {0} ****'.format(link))
            except ConnectionError as e:
                logging.info('**** request to {0} timed out: {1}'.format(url, e)) 
                for node in nodes.values():
                    RFM69_CACHE[node] = None   
       

    @classmethod
    def controlrfm(cls, node, cmd):
        global RFM69_CACHE
        url = None
        httpsend = {node: cmd}
        for key, value in config.RFMMANAGE.items():
                if node == str(value):
                    url = 'http://' + key + ':8001/manageState'
                    break
        if url == None:
            logging.info('**** Node number {0} not exists in RFMMNANAGE dictionary'.format(node)) 
        else:
            try:
                RFM69_CACHE[node] = requests.get(url, json=json.dumps(httpsend), timeout= 2).json()[node]
            #rfm return with json {'node':None} if request failed
            except ConnectionError as e:
                logging.info('**** request to {0} timed out: {1}'.format(url, e)) 
                RFM69_CACHE[node] = None
            return RFM69_CACHE[node]
    

    @classmethod
    def stateValues(cls, node, val):
        global RFM69_CACHE
        try:
            state = RFM69_CACHE[node].get(val)
            if state==None:
                state=0
        except Exception:
            state = 0
        return state

