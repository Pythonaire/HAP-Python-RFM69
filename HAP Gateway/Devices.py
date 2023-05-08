#!/usr/bin/env python3
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_SPRINKLER
import CacheData
import logging, time
from threading import Timer
#import atexit
logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")
''' 
copy const.py to to /usr/local/lib/python3.x/dist-packages/pyhap to use newer CATEGORY and PERMISSIONS
'''

EPOCH_OFFSET = 978307200

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
        self.SoilHumidity = SoilHumidity.configure_char('CurrentRelativeHumidity', setter_callback = self.getState('SH')) # initial
        self.HistorySoil = FakeGatoHistory('room', self)

    def CalcPercentage(self, measured):
        AirValue= 840
        WaterValue= 140
        measured = measured + WaterValue
        if measured > AirValue: measured = AirValue
        reverse = -measured + AirValue
        return int(round(reverse * 100/AirValue, 2))

    def getState(self, value):
        """Get the state
        """
        value = RFM69Data.stateValues(self.node, value)
        return self.CalcPercentage(value)

    @Accessory.run_at_interval(300)
    async def run(self):
        self.SoilHumidity.set_value(self.getState('SH'))

    def stop(self):
        logging.info('Stopping accessory.')

class Weather(Accessory):
    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # Garden sensor nodeNumber 12
        super().__init__(*args, **kwargs)
        self.node = str(node) # node number of the 433MHz sensor
        self.set_info_service(firmware_revision='0.0.2', model='Gardener01', manufacturer= 'Pythonaire', serial_number="9328437-001")
        AirTemperature = self.add_preload_service('TemperatureSensor', chars=['Name', 'CurrentTemperature'])
        AirTemperature.configure_char('Name', value= 'Air Temperature')
        self.AirTemperature = AirTemperature.configure_char('CurrentTemperature', setter_callback = self.getState('AT')) #initial
        AirHumidity = self.add_preload_service('HumiditySensor', chars=['Name', 'CurrentRelativeHumidity'])
        AirHumidity.configure_char('Name', value= 'Air Humidity')
        self.AirHumidity = AirHumidity.configure_char('CurrentRelativeHumidity', setter_callback = self.getState('AH')) # initial
        AirPressure = self.add_preload_service('AtmosphericPressureSensor', chars=['Name', 'AtmosphericPressure'])
        AirPressure.configure_char('Name', value= 'Air Pressure')
        self.AirPressure = AirPressure.configure_char('AtmosphericPressure', setter_callback = self.getState('AP')) # initial
        Battery = self.add_preload_service("Battery", chars=['ChargingState','StatusLowBattery', 'BatteryLevel'])
        self.BattLevel = Battery.configure_char('BatteryLevel', setter_callback = self.getState('B'))
        self.BattStatus = Battery.configure_char('StatusLowBattery')
        Battery.configure_char('ChargingState', value = 0)

    def getState(self, value):
        """Get the state
        """
        return RFM69Data.stateValues(self.node, value)

    @Accessory.run_at_interval(300)
    async def run(self):
        self.AirTemperature.set_value(self.getState('AT'))
        self.AirHumidity.set_value(self.getState('AH'))
        self.AirPressure.set_value(self.getState('AP'))
        Level = self.getState('B')
        self.BattLevel.set_value(Level)
        self.BattStatus.set_value(1) if Level <=25 else self.BattStatus.set_value(0)
        self.HistoryTerrace.addEntry({'time':int(time.time()),'temp':self.getState('AT'),'humidity': self.getState('AH'), 'pressure':self.getState('AP')})
        
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
        self.ValveInUse = Valve.configure_char('InUse', value = 0)
        self.ValveActive = Valve.configure_char('Active', value = self.initialState(2))
        
        self.ValveActive.setter_callback = self.control

        '''
        Active=0, InUse=0 -> Off
        Active=1, InUse=0 -> Waiting [Starting, Activated but no water flowing (yet)]
        Active=1, InUse=1 -> Running
        Active=0, InUse=1 -> Stopping
        '''
    def initialState(self, val):
        """Get the initial state
        """
        answer = RFM69Data.controlrfm(self.node, val) # get the switch state
        if answer != None:
            self.StatusFault.set_value(0)
            self.ValveInUse.set_value(answer)
        else:
            self.StatusFault.set_value(1)
        return answer
    
    def getState(self,val):
        """Get the running state
        """
        answer = RFM69Data.controlrfm(self.node, val) # get the switch state
        if answer != None:
            self.StatusFault.set_value(0)
            self.ValveActive.set_value(answer)
            self.ValveInUse.set_value(answer)
        else:
            self.StatusFault.set_value(1)

    def close(self):
        self.ValveActive.set_value(0)
        self.getState(0)
        self.rem_duration.set_value(0)
        self.rem_duration.notify(0)
        self.duration.set_value(0)
        self.duration.notify()

    def control(self, state):
        if state == 1: # open
            duration = self.duration.get_value()
            if duration == 0:
                self.ValveActive.set_value(1)
                self.getState(1)
            else:
                self.rem_duration.set_value(duration)
                self.ValveActive.set_value(1)
                self.getState(1)
                timer = Timer(duration, self.close)
                timer.start()
        else:
            self.close()
                

class RoomOne(Accessory):
    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # Room sensor nodeNumber 13
        super().__init__(*args, **kwargs)
        self.node = str(node) # node number of the 433MHz sensor, because of json, it needs to be a string
        self.set_info_service(firmware_revision='0.0.2', model='Room01', manufacturer= 'Pythonaire', serial_number="11152022-001")
        AirTemperature = self.add_preload_service('TemperatureSensor', chars=['Name', 'CurrentTemperature'])
        AirTemperature.configure_char('Name', value= 'Temperature')
        self.AirTemperature = AirTemperature.configure_char('CurrentTemperature', setter_callback = self.getState('AT')) #initial
        AirHumidity = self.add_preload_service('HumiditySensor', chars=['Name', 'CurrentRelativeHumidity'])
        AirHumidity.configure_char('Name', value='Humidity')
        self.AirHumidity = AirHumidity.configure_char('CurrentRelativeHumidity', setter_callback = self.getState('AH')) # initial
        AirPressure = self.add_preload_service('AtmosphericPressureSensor', chars=['Name', 'AtmosphericPressure'])
        AirPressure.configure_char('Name', value= 'Pressure')
        self.AirPressure = AirPressure.configure_char('AtmosphericPressure', setter_callback = self.getState('AP')) # initial
        Battery = self.add_preload_service("Battery", chars=['ChargingState','StatusLowBattery', 'BatteryLevel'])
        self.BattLevel = Battery.configure_char('BatteryLevel', setter_callback = self.getState('B'))
        self.BattStatus = Battery.configure_char('StatusLowBattery')
        Battery.configure_char('ChargingState', value = 0)

    def getState(self, value):
        """Get the state
        """
        return RFM69Data.stateValues(self.node, value)
 
    @Accessory.run_at_interval(300)
    async def run(self):
        self.AirTemperature.set_value(self.getState('AT'))
        self.AirHumidity.set_value(self.getState('AH'))
        self.AirPressure.set_value(self.getState('AP'))
        Level = self.getState('B')
        self.BattLevel.set_value(Level)
        if Level <=25:
            self.BattStatus.set_value(1)
        else:
            self.BattStatus.set_value(0)
        
    def stop(self):
        logging.info('Stopping accessory.')

class RoomTwo(Accessory):
    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # Garden sensor nodeNumber 14
        super().__init__(*args, **kwargs)
        self.node = str(node) # node number of the 433MHz sensor
        self.set_info_service(firmware_revision='0.0.2', model='Room02', manufacturer= 'Pythonaire', serial_number="11152022-002")
        AirTemperature = self.add_preload_service('TemperatureSensor', chars=['Name', 'CurrentTemperature'])
        AirTemperature.configure_char('Name', value= 'Air Temperature')
        self.AirTemperature = AirTemperature.configure_char('CurrentTemperature', setter_callback = self.getState('AT')) #initial
        AirHumidity = self.add_preload_service('HumiditySensor', chars=['Name', 'CurrentRelativeHumidity'])
        AirHumidity.configure_char('Name', value= 'Air Humidity')
        self.AirHumidity = AirHumidity.configure_char('CurrentRelativeHumidity', setter_callback = self.getState('AH')) # initial
        AirPressure = self.add_preload_service('AtmosphericPressureSensor', chars=['Name', 'AtmosphericPressure'])
        AirPressure.configure_char('Name', value= 'Air Pressure')
        self.AirPressure = AirPressure.configure_char('AtmosphericPressure', setter_callback = self.getState('AP')) # initial
        Battery = self.add_preload_service("Battery", chars=['ChargingState','StatusLowBattery', 'BatteryLevel'])
        self.BattLevel = Battery.configure_char('BatteryLevel', setter_callback = self.getState('B'))
        self.BattStatus = Battery.configure_char('StatusLowBattery')
        Battery.configure_char('ChargingState', value = 0)
        self.HistoryRoomTwo = FakeGatoHistory('weather', self)
        
    def getState(self, value):
        """Get the state
        """
        return RFM69Data.stateValues(self.node, value)
        
    @Accessory.run_at_interval(300)
    async def run(self):
        self.AirTemperature.set_value(self.getState('AT'))
        self.AirHumidity.set_value(self.getState('AH'))
        self.AirPressure.set_value(self.getState('AP'))
        Level = self.getState('B')
        self.BattStatus.set_value(1) if Level <=25 else self.BattStatus.set_value(0)
        self.BattLevel.set_value(Level)
        
    def stop(self):
        logging.info('Stopping accessory.')
