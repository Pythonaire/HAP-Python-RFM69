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
            except ConnectTimeout as e:
                logging.info('**** request to {0} timed out: {1}'.format(url, e)) 
                for node in nodes.values():
                    RFM69_CACHE[node] = None   
        logging.info('**** Cache refreshed with data from Nodes {0} ****'.format(list(RFM69_CACHE.keys())))

    @classmethod
    def controlrfm(cls, node, cmd):
        global RFM69_CACHE
        httpsend = {node: cmd}
        try:
            for key, value in config.RFMMANAGE.items():
                if node == str(value):
                    url = 'http://' + key + ':8001/manageState'
                    break
            RFM69_CACHE[node] = requests.get(url, json=json.dumps(httpsend), timeout= 2).json()[node]
            #rfm return with json {'node':None} if request failed
        except ConnectTimeout as e:
            logging.info('**** request to {0} timed out: {1}'.format(url, e)) 
            RFM69_CACHE[node] = None
        return RFM69_CACHE[node]
    
    @classmethod
    def forwarder(cls, data):
        try:
            requests.post(config.RADIO_URL, json=json.dumps(data))
            logging.info('**** post Temp to Radio {0}'.format(data))
        except requests.exceptions.ConnectionError as e:
            logging.info('**** request.post to {0} got exception {1}'.format(config.RADIO_URL,e))

    @classmethod
    def stateValues(cls, node, val):
        global RFM69_CACHE
        state = RFM69_CACHE[node].get(val)
        if state == None: state = 0
        return state

