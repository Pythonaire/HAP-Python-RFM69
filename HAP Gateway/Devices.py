#!/usr/bin/env python3
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_SPRINKLER
import sqlite3 as sql
import logging, requests, asyncio, json, socket, threading, time
from history import FakeGatoHistory
import config

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

''' 
add additional service and characteristics to /usr/local/lib/python3.x/dist-packages/pyhap/ressources
'''

NODES = config.Config.NODES
NODE_CACHE = config.Config.NODE_CACHE

def send_config(): # send defined nodes to the 433MHz brigde
    ret = None
    while ret != '200':
        try:
            ret = requests.post(config.Config.RFM69_CONFIG, json=json.dumps(NODE_CACHE))
        except Exception as e:
            logging.info('**** request to {0} timed out: {1}'.format(config.Config.RFM69_CONFIG, e))
            time.sleep(10)

def controlrfm(node, cmd):
    httpsend = {node: cmd}
    NODE_CACHE[node] = "None" # set to None, wait for answer
    ret = {}
    try:
        ret = requests.get(config.Config.RFM69_CONTROL, json=json.dumps(httpsend)).json()
        #rfm return with {'node': "None"} if request failed
        #if ret[node] == "None":
        #    ret[node] = 2 # set to 2
        NODE_CACHE[node] = ret[node]
        return ret
    except Exception as e:
        logging.info('**** request to {0} timed out: {1}'.format(config.Config.RFM69_CONTROL, e))

def getCache(node):
    httpsend = {'node':node} # "?" useless, but needed for dict/json handling
    ret = {}
    while not node in ret:
        try:
            ret = requests.get(config.Config.RFM69_CACHE, json=json.dumps(httpsend)).json()
            NODE_CACHE[node] = ret[node]
        except socket.error as e:
            logging.info('**** request to  {0} timed out: {1}'.format(config.Config.RFM69_CACHE, e))
            time.sleep(10)
    return ret

async def forwarder(data):
    try:
        requests.post(config.Config.RADIO_URL, json=json.dumps(data))
        logging.info('**** post Temp to Radio {0}'.format(data))
    except socket.error as e:
        logging.info('**** request.post to {0} got exception {1}'.format(config.Config.RADIO_URL,e))
    finally:
        return '', 200 # make shure, do not produce additional error on sender side

class PhotoVoltaic(Accessory):
    category = CATEGORY_SENSOR
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.displayName = args[1] # args[1] contained the device/class Name given
        self.dbFile = '/home/pwiechmann/smadata/SBFspot.db'
        self.thisDay = "SELECT max(round(TotalYield, 1)) - min(round(TotalYield,1)) AS power FROM DayData WHERE date(TimeStamp, 'unixepoch') = CURRENT_DATE"
        self.thisYear = "SELECT max(round(TotalYield, 1)) - min(round(TotalYield,1)) AS power FROM DayData WHERE datetime(TimeStamp, 'unixepoch') > date('now','start of year')"
        self.set_info_service(firmware_revision='0.0.1', manufacturer=None, model='MacServer SMAInverter', serial_number="MSSMA01")
        self.Outlet=self.add_preload_service('Outlet', chars = ['Name', 'On','OutletInUse']) 
        self.PhotoVoltaic = self.add_preload_service('PowerMeter', chars = ['Name', 'CurrentConsumption','TotalConsumption']) 
        self.Outlet.configure_char('Name', value = 'PhotoVoltaic')
        self.Outlet.configure_char('On', value=False)
        self.Outlet.configure_char('OutletInUse', value=False)
        self.PhotoVoltaic.configure_char('Name', value = 'PhotoVoltaic')
        self.CurrentConsumption = self.PhotoVoltaic.configure_char('CurrentConsumption', value = self.select_power(self.thisDay))
        self.TotalConsumption = self.PhotoVoltaic.configure_char('TotalConsumption', value = self.select_power(self.thisYear)/1000)
        self.HistoryPower = FakeGatoHistory('energy', self)

    def create_connection(self, dbFile):
        conn = None
        try:
            conn = sql.connect(dbFile)
        except Exception as e:
            logging.info('** Could not open {0} , err: {1}'.format(dbFile, e))
        return conn

    def select_power(self, command):
        conn = self.create_connection(self.dbFile)
        cur = conn.cursor()
        cur.execute(command)
        value = cur.fetchall() # return tuple
        logging.info('*** get value from SBFSpot : {0} '.format(value[0][0]))
        cur.close()
        if value[0][0] == None:
            power = 0
        else:
            power = value[0][0]
        return power

    @Accessory.run_at_interval(300)
    def run(self):
        self.CurrentConsumption.set_value(self.select_power(self.thisDay))
        self.TotalConsumption.set_value(self.select_power(self.thisYear)/1000)


    def stop(self):
        logging.info('Stopping accessory.')

class Moisture(Accessory):
    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # Garden sensor nodeNumber 12
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        self.node = node # node number of the 433MHz sensor
        self.set_info_service(firmware_revision='0.0.2', model='GardenSoil', manufacturer= 'Pythonaire', serial_number="Soil-001")

        SoilHumidity = self.add_preload_service('HumiditySensor', chars=['Name', 'CurrentRelativeHumidity'])
        SoilHumidity.configure_char('Name', value= 'Soil Humidity')
        self.SoilHumidity = SoilHumidity.configure_char('CurrentRelativeHumidity', value = 0) # initial

        Battery = self.add_preload_service("Battery", chars=['ChargingState','StatusLowBattery', 'BatteryLevel'])
        self.BattLevel = Battery.configure_char('BatteryLevel', value = 0)
        self.BattStatus = Battery.configure_char('StatusLowBattery', value = 1)
        Battery.configure_char('ChargingState', value = 2)

        self.HistorySoil = FakeGatoHistory('room', self)

    @Accessory.run_at_interval(300)
    def run(self):
        global NODE_CACHE
        dry = 800
        if NODE_CACHE[str(self.node)] == None: #the full data will be received by the weather class and stored, no need of extra calling
            self.SoilHumidity.set_value(0)
            self.BattStatus.set_value(0)
            self.BattLevel.set_value(0)
            MoisturePercent = 0
        else:
            NodeData = NODE_CACHE[str(self.node)]
            relativeHumidity = int(NodeData["SH"]) - 200
            if relativeHumidity < 0:
                relativeHumidity = 0
            dryPercent = relativeHumidity * 100 / dry # dry percent
            MoisturePercent = round(100 - dryPercent)  
            self.SoilHumidity.set_value(MoisturePercent)
            if NodeData["B"]<=25:
                self.BattStatus.set_value(1)
            else:
                self.BattStatus.set_value(0)
            self.BattLevel.set_value(NodeData["B"])
        
        self.HistorySoil.addEntry({'time':int(round(time.time())),'humidity': MoisturePercent, 'temp':0,'ppm':0})
        
    def stop(self):
        logging.info('Stopping accessory.')

class Weather(Accessory):
    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # Garden sensor nodeNumber 12
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        self.node = node # node number of the 433MHz sensor
        self.set_info_service(firmware_revision='0.0.2', model='Gardener01', manufacturer= 'Pythonaire', serial_number="Weather-001")
        
        AirTemperature = self.add_preload_service('TemperatureSensor', chars=['Name', 'CurrentTemperature'])
        AirTemperature.configure_char('Name', value= 'Air Temperature')
        self.AirTemperature = AirTemperature.configure_char('CurrentTemperature', value= 0) #initial

        AirHumidity = self.add_preload_service('HumiditySensor', chars=['Name', 'CurrentRelativeHumidity'])
        AirHumidity.configure_char('Name', value= 'Air Humidity')
        self.AirHumidity = AirHumidity.configure_char('CurrentRelativeHumidity', value = 0) # initial

        AirPressure = self.add_preload_service('AtmosphericPressureSensor', chars=['Name', 'AtmosphericPressure'])
        AirPressure.configure_char('Name', value= 'Air Pressure')
        self.AirPressure = AirPressure.configure_char('AtmosphericPressure', value = 0) # initial

        Battery = self.add_preload_service("Battery", chars=['ChargingState','StatusLowBattery', 'BatteryLevel'])
        self.BattLevel = Battery.configure_char('BatteryLevel', value = 0)
        self.BattStatus = Battery.configure_char('StatusLowBattery', value = 1)
        Battery.configure_char('ChargingState', value = 2)

        self.HistoryTerrace = FakeGatoHistory('weather', self)
        
    @Accessory.run_at_interval(300)
    def run(self):
        recv = getCache(str(self.node))
        #{'B':Battery,'AT':AirTemperature,'AH':AirHumidity,'AP':AirPressure,SH':SoilHumidity}         
        if recv[str(self.node)] == None:
            NodeData = {"B": 0, "AT":0, "AH": 0, "AP": 0, "SH":0}
        else: 
            NodeData = recv[str(self.node)]
        if NodeData["B"]<=25:
            self.BattStatus.set_value(1) 
        else: 
            self.BattStatus.set_value(0)
        self.AirHumidity.set_value(NodeData["AH"])
        self.AirTemperature.set_value(NodeData["AT"])
        self.AirPressure.set_value(NodeData["AP"])
        self.BattLevel.set_value(NodeData["B"])
        self.HistoryTerrace.addEntry({'time':int(round(time.time())),'temp':NodeData["AT"],'humidity': NodeData["AH"], 'pressure':NodeData["AP"]})
        forward = {'Temp': NodeData["AT"]} 
        asyncio.run(forwarder(forward))
        
    def stop(self):
        logging.info('Stopping accessory.')

class Pumpe(Accessory):
    """Switch for immension pump, state request with ?, switch with 0 and 1 """
    category = CATEGORY_SPRINKLER
    def __init__(self, node, *args, **kwargs): # Pump sensor nodeNumber 11
        super().__init__(*args, **kwargs)
        global NODE_CACHE
        self.name = args[1] # args[1] contained the device/class Name given
        self.node = str(node) # args[2] contained the device number given
        Valve = self.add_preload_service('Valve',['Active','ValveType', 'SetDuration', 'RemainingDuration', 'IsConfigured', 'InUse', 'StatusFault'])
        # unfortunately case StatusFault not visible --> set to 0, to see nothing happend
        Valve.configure_char('ValveType', value = 1)
        Valve.configure_char('IsConfigured', value = 1)
        self.duration = Valve.configure_char('SetDuration', value = 0) 
        self.rem_duration = Valve.configure_char('RemainingDuration')
        NODE_CACHE[self.node] = controlrfm(self.node, 2)[self.node]
        if NODE_CACHE[self.node] !=None:
            self.StatusFault = Valve.configure_char('StatusFault', value = 0) # sensor react
            self.ValveActive = Valve.configure_char('Active', value = 0)
            self.ValveInUse = Valve.configure_char('InUse', value = 0)
        else:
            self.StatusFault = Valve.configure_char('StatusFault', value = 1) # somethings goes wrong
            self.ValveActive = Valve.configure_char('Active', value = 0)
            self.ValveInUse = Valve.configure_char('InUse', value = 0)
        self.ValveActive.setter_callback = self.set_state
        self.ValveActive.getter_callback = self.get_state

    def fault_state(self, state):
        if state != None:
            self.ValveActive.set_value(state)
            self.ValveInUse.set_value(state)
            self.StatusFault.set_value(0)
        else:
            self.ValveActive.set_value(0)
            self.ValveInUse.set_value(0)
            self.StatusFault.set_value(1)
        self.ValveInUse.notify()
        self.StatusFault.notify()

        
    def duration_off(self):
        global NODE_CACHE
        NODE_CACHE[self.node] = controlrfm(self.node, 0)[self.node] # switch the mcu off, should be 0
        self.fault_state(NODE_CACHE[self.node])
        self.rem_duration.set_value(0)
        self.duration.set_value(0)

    def set_state(self, value):
        global NODE_CACHE
        duration = self.duration.get_value()
        self.rem_duration.set_value(duration)
        if value ==1 and duration > 0:
            NODE_CACHE[self.node]= controlrfm(self.node, value)[self.node] # switch on with time
            if NODE_CACHE[self.node] != None:
                self.fault_state(NODE_CACHE[self.node])
                timer = threading.Timer(duration, self.duration_off)
                timer.start()
            else:
                self.fault_state(NODE_CACHE[self.node])
        else:
            self.rem_duration.set_value(0)
            NODE_CACHE[self.node] = controlrfm(self.node, value)[self.node] # switch on/off
            self.fault_state(NODE_CACHE[self.node])
        return value

    def get_state(self):
        if NODE_CACHE[self.node] == None:
            NODE_CACHE[self.node] = controlrfm(self.node, 2)[self.node] # switch state
            self.fault_state(NODE_CACHE[self.node])
        return NODE_CACHE[self.node]