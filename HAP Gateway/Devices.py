#!/usr/bin/env python3
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_SPRINKLER
import logging, time
from threading import Timer
import config
import CacheData

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

NODES = config.NODES
RFM69Values = CacheData.RFM69_CACHE
RFM69Data= CacheData.RFM69Data()
cancel_future_calls =  CacheData.call_repeatedly(300,  RFM69Data.syncCache)


class Moisture(Accessory):
    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # Garden sensor nodeNumber 12
        super().__init__(*args, **kwargs)
        self.node = str(node) # node number of the 433MHz sensor
        self.set_info_service(firmware_revision='0.0.2', model='GardenSoil', manufacturer= 'Pythonaire', serial_number="7645-001")
        SoilHumidity = self.add_preload_service('HumiditySensor', chars=['Name', 'CurrentRelativeHumidity'])
        SoilHumidity.configure_char('Name', value= 'Soil Humidity')
        self.SoilHumidity = SoilHumidity.configure_char('CurrentRelativeHumidity') # initial

        Battery = self.add_preload_service("Battery", chars=['ChargingState','StatusLowBattery', 'BatteryLevel'])
        self.BattLevel = Battery.configure_char('BatteryLevel')
        self.BattStatus = Battery.configure_char('StatusLowBattery')
        Battery.configure_char('ChargingState', value = 0)
        self.getValue()

    def getValue(self):
        global RFM69Values
        dry = 800
        if RFM69Values[self.node] == None:
            self.SoilHumidity.set_value(0)
            self.BattStatus.set_value(0)
            self.BattLevel.set_value(0)
            self.MoisturePercent = 0
        else:
            relativeHumidity = int(RFM69Values[self.node]["SH"]) - 200
            if relativeHumidity < 0:
                relativeHumidity = 0
            dryPercent = relativeHumidity * 100 / dry # dry percent
            self.MoisturePercent = round(100 - dryPercent)  
            self.SoilHumidity.set_value(self.MoisturePercent)
            if RFM69Values[self.node]["B"]<=25:
                self.BattStatus.set_value(1)
            else:
                self.BattStatus.set_value(0)
            self.BattLevel.set_value(RFM69Values[self.node]["B"])

    @Accessory.run_at_interval(300)
    async def run(self):
        global RFM69Values
        self.getValue()
        
    def stop(self):
        logging.info('Stopping accessory.')

class Weather(Accessory):
    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # Garden sensor nodeNumber 12
        super().__init__(*args, **kwargs)
        global RFM69Values
        self.node = str(node) # node number of the 433MHz sensor
        self.set_info_service(firmware_revision='0.0.2', model='Gardener01', manufacturer= 'Pythonaire', serial_number="9328437-001")
        AirTemperature = self.add_preload_service('TemperatureSensor', chars=['Name', 'CurrentTemperature'])
        AirTemperature.configure_char('Name', value= 'Air Temperature')
        self.AirTemperature = AirTemperature.configure_char('CurrentTemperature') #initial
        AirHumidity = self.add_preload_service('HumiditySensor', chars=['Name', 'CurrentRelativeHumidity'])
        AirHumidity.configure_char('Name', value= 'Air Humidity')
        self.AirHumidity = AirHumidity.configure_char('CurrentRelativeHumidity') # initial
        AirPressure = self.add_preload_service('AtmosphericPressureSensor', chars=['Name', 'AtmosphericPressure'])
        AirPressure.configure_char('Name', value= 'Air Pressure')
        self.AirPressure = AirPressure.configure_char('AtmosphericPressure') # initial
        Battery = self.add_preload_service("Battery", chars=['ChargingState','StatusLowBattery', 'BatteryLevel'])
        self.BattLevel = Battery.configure_char('BatteryLevel')
        self.BattStatus = Battery.configure_char('StatusLowBattery')
        Battery.configure_char('ChargingState', value = 0)
        
        self.getValues()

    def getValues(self):
        global RFM69Values
        if RFM69Values[self.node] == None:
            self.AirTemperature.set_value(0)
            self.TempForRadio = 0
            self.AirHumidity.set_value(0)
            self.AirPressure.set_value(0)
            self.BattLevel.set_value(0)
            self.BattStatus.set_value(0)
        else:
            self.AirTemperature.set_value(RFM69Values[self.node]['AT'])
            self.TempForRadio = RFM69Values[self.node]['AT']
            self.AirHumidity.set_value(RFM69Values[self.node]['AH'])
            self.AirPressure.set_value(RFM69Values[self.node]['AP'])
            if RFM69Values[self.node]['B']<=25:
                self.BattStatus.set_value(1)
            else: 
                self.BattStatus.set_value(0)
            self.BattLevel.set_value(RFM69Values[self.node]['B'])

        
    @Accessory.run_at_interval(300)
    async def run(self):
        global RFM69Values
        self.getValues()
        
        
    def stop(self):
        logging.info('Stopping accessory.')


class Pumpe(Accessory):
    """Switch for immension pump, state request with ?, switch with 0 and 1 """
    category = CATEGORY_SPRINKLER
    def __init__(self, node, *args, **kwargs): # Pump sensor nodeNumber 11
        super().__init__(*args, **kwargs)
        self.node = str(node) # args[2] contained the device number given
        self.set_info_service(firmware_revision='0.0.2', model='Pump01', manufacturer= 'Pythonaire', serial_number="7867-001")
        Valve = self.add_preload_service('Valve',chars=['Active', 'ValveType', 'SetDuration', 'RemainingDuration', 'InUse', 'StatusFault'])
        # unfortunately case StatusFault not visible --> set to 0, to see nothing happend
        Valve.configure_char('ValveType', value = 1)
        self.duration = Valve.configure_char('SetDuration', value = 0) 
        self.rem_duration = Valve.configure_char('RemainingDuration', value = 0)
        self.StatusFault = Valve.configure_char('StatusFault', value = 0)
        self.ValveActive = Valve.configure_char('Active', value = self.get_state())
        self.ValveInUse = Valve.configure_char('InUse', value = 0)
        self.ValveActive.setter_callback = self.control

        '''
        Active=0, InUse=0 -> Off
        Active=1, InUse=0 -> Waiting [Starting, Activated but no water flowing (yet)]
        Active=1, InUse=1 -> Running
        Active=0, InUse=1 -> Stopping
        '''

    def close(self):
        global RFM69Values
        RFM69Data.controlrfm(config.RFM69Garden_CONTROL, self.node, 0) # switch the mcu off
        if RFM69Values[self.node] == 0:
             self.ValveInUse.set_value(0)
             self.ValveActive.set_value(0)
        else:
            self.StatusFault.set_value(1)
            self.ValveInUse(0)
        self.rem_duration.set_value(0)
        self.rem_duration.notify(0)
        self.duration.set_value(0)
        self.duration.notify() 
        #endTimer = round(time.monotonic() - self.MeasureWater)
        #1085,7 l/h = 0,30 l/s
        #self.WaterAmount = 0.30 * endTimer
        #self.HistoryValve.addEntry({'time':int(time.time()),'status':0,'waterAmount': self.WaterAmount})

    def control(self, state):
        global RFM69Values
        if state == 1: # open
            duration = self.duration.get_value()
            if duration == 0:
                RFM69Data.controlrfm(config.RFM69Garden_CONTROL, self.node, state) # switch the mcu on
                if RFM69Values[self.node] == state:
                    self.ValveActive.set_value(state)
                    self.ValveInUse.set_value(state)
                    self.MeasureWater = time.monotonic()
                    #self.HistoryValve.addEntry({'time':int(time.time()),'status':1,'waterAmount': 0})
                else:
                    self.StatusFault.set_value(1)
            else:
                RFM69Data.controlrfm(config.RFM69Garden_CONTROL, self.node, state) # switch the mcu on
                if RFM69Values[self.node] == state:
                    self.ValveActive.set_value(1)
                    self.ValveInUse.set_value(1)
                    self.rem_duration.set_value(duration)
                    #self.MeasureWater = time.monotonic()
                    #self.HistoryValve.addEntry({'time':int(time.time()),'status':1,'waterAmount': 0})
                    timer = Timer(duration, self.close)
                    timer.start()
                else:
                    self.StatusFault.set_value(1)
        else:
            self.close()
                
    def get_state(self):
        global RFM69Values
        RFM69Data.controlrfm(config.RFM69Garden_CONTROL, self.node, 2) # get the switch state
        if RFM69Values[self.node] != None:
            self.StatusFault.set_value(0)
            RFM69Values[self.node]
        else:
            self.StatusFault.set_value(1)
            RFM69Values[self.node] = 0
        return RFM69Values[self.node]


class RoomOne(Accessory):
    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # Room sensor nodeNumber 13
        super().__init__(*args, **kwargs)
        global RFM69Values
        self.node = str(node) # node number of the 433MHz sensor, because of json, it needs to be a string
        self.set_info_service(firmware_revision='0.0.2', model='Room01', manufacturer= 'Pythonaire', serial_number="11152022-001")
        AirTemperature = self.add_preload_service('TemperatureSensor', chars=['Name', 'CurrentTemperature'])
        AirTemperature.configure_char('Name', value= 'Temperature')
        self.AirTemperature = AirTemperature.configure_char('CurrentTemperature') #initial
        AirHumidity = self.add_preload_service('HumiditySensor', chars=['Name', 'CurrentRelativeHumidity'])
        AirHumidity.configure_char('Name', value='Humidity')
        self.AirHumidity = AirHumidity.configure_char('CurrentRelativeHumidity') # initial
        AirPressure = self.add_preload_service('AtmosphericPressureSensor', chars=['Name', 'AtmosphericPressure'])
        AirPressure.configure_char('Name', value= 'Pressure')
        self.AirPressure = AirPressure.configure_char('AtmosphericPressure') # initial
        Battery = self.add_preload_service("Battery", chars=['ChargingState','StatusLowBattery', 'BatteryLevel'])
        self.BattLevel = Battery.configure_char('BatteryLevel')
        self.BattStatus = Battery.configure_char('StatusLowBattery')
        Battery.configure_char('ChargingState', value = 0)
        self.HistoryRoomOne = FakeGatoHistory('weather', self)
        self.getValue()

    def getValue(self):
        global RFM69Values
        if RFM69Values[self.node] == None:
            self.AirHumidity.set_value(0)
            self.AirTemperature.set_value(0)
            self.AirPressure.set_value(0)
            self.BattLevel.set_value(0)
            self.BattStatus.set_value(0)
            self.HistoryRoomOne.addEntry({'time':int(time.time()),'temp':0,'humidity': 0, 'pressure':0})
        else:
            self.AirHumidity.set_value(RFM69Values[self.node]["AH"])
            self.AirTemperature.set_value(RFM69Values[self.node]["AT"])
            self.AirPressure.set_value(RFM69Values[self.node]["AP"])
            self.BattLevel.set_value(RFM69Values[self.node]["B"])
            if RFM69Values[self.node]["B"]<=25:
                self.BattStatus.set_value(1)
            else: 
                self.BattStatus.set_value(0)
            self.HistoryRoomOne.addEntry({'time':int(time.time()),'temp':RFM69Values[self.node]["AT"],'humidity': RFM69Values[self.node]["AH"], 'pressure':RFM69Values[self.node]["AP"]})

 
    @Accessory.run_at_interval(300)
    async def run(self):
        global RFM69Values
        self.getValue()
        
    def stop(self):
        logging.info('Stopping accessory.')