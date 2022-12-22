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

RTC_CACHE = {
    'PanelCurrentConsumption': 0,
    'PanelHistory':0,
    'PanelTotalConsumption': 0,
    'FeedCurrentConsumption': 0,
    'FeedHistory': 0,
    'FeedTotalConsumption': 0,
    'GridCurrentConsumption': 0,
    'GridHistory': 0,
    'GridTotalConsumption': 0,
    'HouseholdCurrentConsumption': 0,
    'HouseholdHistory': 0,
    'HouseholdTotalConsumption': 0,
    'BatteryCurrentConsumption': 0,
    'BatteryHistory': 0,
    'BatteryTotalConsumption': 0,
    'BatteryPercentage': 0,
    'BatteryState': 0 
}

def call_repeatedly(interval, func):
        stopped = threading.Event()
        def loop():
            while not stopped.wait(stopped.wait(interval)): # the first call is in `interval` secs
                #func(*args)
                func()
        threading.Thread(target=loop, daemon=True).start()    
        return stopped.set


class RTCData():
    def __init__(self):
        self.syncCache() # initial

    @classmethod
    def connect(cls, db):
        try:
            #conn = sql.connect(db, uri=True, detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)
            conn = sql.connect(db, uri=True)
        except Error as e:
            logging.info('**** Failed to Connect to : {0} '.format(e))
        return conn

    @classmethod
    def fetchone(cls, cmd, value=None):
        with RTCData.connect(config.RTC_DBNAME) as conn:
            cursor = conn.cursor()
            if value == None: 
                records = cursor.execute(cmd).fetchone()
            else:
                records = cursor.execute(cmd, value).fetchone()
        cursor.close()
        return records[0]

    @classmethod
    def TotalWh(cls, column):
        cmd = "SELECT MAX({0}) FROM RTC WHERE date(time,'unixepoch') > date('now', 'start of year');".format(column)
        actualyear =round(RTCData.fetchone(cmd) / 1000, 2)
        cmd = "SELECT IFNULL(MAX({0}),0) FROM RTC WHERE date(time,'unixepoch') < date('now', 'start of year');".format(column)
        if RTCData.fetchone(cmd) == None:
            lastyear = 0
        else:
            lastyear =round(RTCData.fetchone(cmd) / 1000, 2)
        return round(actualyear - lastyear, 2)  # type: ignore

    @classmethod
    def ActualValue(cls, column):
        cmd = "SELECT {0} FROM RTC WHERE id = (SELECT MAX(id) FROM RTC);".format(column)
        return int(RTCData.fetchone(cmd))  # type: ignore

    @classmethod
    def AverageWh(cls, column):
        cmd = "SELECT ROUND(AVG({0}),2) FROM (SELECT {1} FROM RTC ORDER BY id DESC LIMIT 12);".format(column, column)
        '''
        The Eve App multiply the Power by 10. Eve.app will assume that the same power is drawn for all the sampling time (10 minutes), 
        so it will show a point with an energy consumption equal to this value divided by 60. Example. 
        Your appliance is consuming 1000W, which means a total energy of 1kWh if run for 1 hour. 
        The value reported is 1000 x 10. The value shown is 1000 x 10 / 60 = 166Wh, which is correct because this sample covers 10min, 
        i.e. 1/6 of an hour. At the end of the hour, Eve.app will show 6 samples at 166Wh, totalizing 1kWh.'''
        return int(RTCData.fetchone(cmd))

    @classmethod
    def syncCache(cls):
        cmd = 'SELECT MAX(id) FROM RTC;'
        try:
            maxId = RTCData.fetchone(cmd)
        except Exception as e:
            logging.info('sql error while writing: {0} \n'.format(e))
            maxId = 0
        if maxId > 11: # we want the last hour, the script runs every 10 minutes -> we need 6 values
            RTC_CACHE['PanelCurrentConsumption'] = RTCData.ActualValue('PanelCurrentConsumption')
            RTC_CACHE['PanelHistory'] = RTCData.AverageWh('PanelCurrentConsumption')
            RTC_CACHE['PanelTotalConsumption'] = RTCData.TotalWh('PanelTotalConsumption')
            RTC_CACHE['FeedCurrentConsumption'] = RTCData.ActualValue('FeedCurrentConsumption')
            RTC_CACHE['FeedHistory'] = RTCData.AverageWh('FeedCurrentConsumption')
            RTC_CACHE['FeedTotalConsumption'] =  RTCData.TotalWh('FeedTotalConsumption')
            RTC_CACHE['GridCurrentConsumption'] = RTCData.ActualValue('GridCurrentConsumption')
            RTC_CACHE['GridHistory'] = RTCData.AverageWh('GridCurrentConsumption')
            RTC_CACHE['GridTotalConsumption'] = RTCData.TotalWh('GridTotalConsumption')
            RTC_CACHE['HouseholdCurrentConsumption'] = RTCData.ActualValue('HouseholdCurrentConsumption')
            RTC_CACHE['HouseholdHistory'] = RTCData.AverageWh('HouseholdCurrentConsumption')
            RTC_CACHE['HouseholdTotalConsumption'] = RTCData.TotalWh('HouseholdTotalConsumption')
            RTC_CACHE['BatteryCurrentConsumption'] = RTCData.ActualValue('BatteryCurrentConsumption')
            RTC_CACHE['BatteryHistory'] = RTCData.AverageWh('BatteryCurrentConsumption')
            RTC_CACHE['BatteryTotalConsumption'] = RTCData.TotalWh('BatteryTotalConsumption')
            RTC_CACHE['BatteryPercentage'] = RTCData.ActualValue('BatteryPercentage')
            RTC_CACHE['BatteryState'] = RTCData.ActualValue('BatteryState')
        else:
            RTC_CACHE['PanelCurrentConsumption'] = RTCData.ActualValue('PanelCurrentConsumption')
            RTC_CACHE['PanelHistory'] = 0
            RTC_CACHE['PanelTotalConsumption'] = RTCData.TotalWh('PanelTotalConsumption')
            RTC_CACHE['FeedCurrentConsumption'] = RTCData.AverageWh('FeedCurrentConsumption')
            RTC_CACHE['FeedHistory'] = 0
            RTC_CACHE['FeedTotalConsumption'] =  RTCData.TotalWh('FeedTotalConsumption')
            RTC_CACHE['GridCurrentConsumption'] = RTCData.ActualValue('GridCurrentConsumption')
            RTC_CACHE['GridHistory'] = 0
            RTC_CACHE['GridTotalConsumption'] = RTCData.TotalWh('GridTotalConsumption')
            RTC_CACHE['HouseholdCurrentConsumption'] = RTCData.ActualValue('HouseholdCurrentConsumption')
            RTC_CACHE['HouseholdHistory'] = 0
            RTC_CACHE['HouseholdTotalConsumption'] = RTCData.TotalWh('HouseholdTotalConsumption')
            RTC_CACHE['BatteryCurrentConsumption'] = RTCData.ActualValue('BatteryCurrentConsumption')
            RTC_CACHE['BatteryHistory'] = 0
            RTC_CACHE['BatteryTotalConsumption'] = RTCData.TotalWh('BatteryTotalConsumption')
            RTC_CACHE['BatteryPercentage'] = RTCData.ActualValue('BatteryPercentage')
            RTC_CACHE['BatteryState'] = RTCData.ActualValue('BatteryState')

    @classmethod
    def stateValues(cls, val):
        state = RTC_CACHE.get(val)
        if state == None: state = 0
        return state
    

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

