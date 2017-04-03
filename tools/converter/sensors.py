################################################################################
#
# This module contains sensor classes
#
################################################################################

import re
import eGeodesy as geo
import parser
from log2xml import SiteLog

class HumiditySensor(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, sensors):
        if cls.Current:
            humidity = cls.Current.complete()
            extra = geo.humiditySensorPropertyType()
            extra.append(humidity)
            extra.dateInserted = humidity.validTime.AbstractTimePrimitive.beginPosition
            sensors.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = HumiditySensor(cls.Index)

    Model = re.compile(r'^8\.1\.(?P<version>\d+)\s*(Humidity\s+Sensor\s+Model\s+:)(?P<value>.*)$', re.IGNORECASE)
    Manufacturer = re.compile(r'^\s+(Manufacturer\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber = re.compile(r'^\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    Interval = re.compile(r'^\s+(Data Sampling Interval\s+:)(?P<value>.*)$', re.IGNORECASE)
    Accuracy = re.compile(r'^\s+(Accuracy.*:)(?P<value>.*)$', re.IGNORECASE)
    Aspiration = re.compile(r'^\s+(Aspiration\s+:)(?P<value>.*)$', re.IGNORECASE)
    DiffToAnt = re.compile(r'^\s+(Height Diff to Ant\s+:)(?P<value>.*)$', re.IGNORECASE)
    CalibrationDate = re.compile(r'^\s+(Calibration date\s+:)(?P<value>.*)$', re.IGNORECASE)

    EffectiveDates = re.compile(r'^\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "humidity-sensor-" + str(sequence)
        self.humiditySensor = geo.HumiditySensorType(id=text)

        self.notes = [""]
        self.notesAppended = False
        self.sequence = sequence
        self.version = [0]


    def parse(self, text, line):

        if parser.parseCodeTypeAndVersion(self.humiditySensor, "type", type(self).Model,
                text, line, "urn:ga-gov-au:humidity-sensor-type", self.version):
            return

        if parser.assignNotes(self.notes, type(self).Notes, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesAddition, text, line):
            return
        
        if parser.setTextAttribute(self.humiditySensor, "manufacturer", type(self).Manufacturer, text, line):
            return

        if parser.setTextAttribute(self.humiditySensor, "serialNumber", type(self).SerialNumber, text, line):
            return

        if parser.setDoubleAttribute(self.humiditySensor, "dataSamplingInterval", type(self).Interval, text, line, True, True):
            return

        if parser.setDoubleAttribute(self.humiditySensor, "accuracy_percentRelativeHumidity", type(self).Accuracy, text, line, True, True):
            return

        if parser.setTextAttribute(self.humiditySensor, "aspiration", type(self).Aspiration, text, line):
            return

        if parser.setDoubleAttribute(self.humiditySensor, "heightDiffToAntenna", type(self).DiffToAnt, text, line, True, True):
            return

        if parser.setDateTimeAttribute(self.humiditySensor, "calibrationDate", type(self).CalibrationDate, text, line):
            return

        if parser.setTimePeriodAttribute(self.humiditySensor, "validTime", type(self).EffectiveDates, text, line, SiteLog, self.version[0] < SiteLog.HumidityVersion):
            return



    def complete(self): 
                
        if not self.notesAppended:
            if len(self.notes[0]) > 0:
                self.humiditySensor.notes = self.notes[0]
                self.notesAppended = True
        return self.humiditySensor


################################################################################
class WaterVapor(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, sensors):
        if cls.Current:
            waterVapor = cls.Current.complete()
            extra = geo.waterVaporSensorPropertyType()
            extra.append(waterVapor)
            extra.append(waterVapor.validTime.AbstractTimePrimitive.beginPosition)
            sensors.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = WaterVapor(cls.Index)

    Radiometer = re.compile(r'^8\.4\.(?P<version>\d+)\s*(Water\s+Vapor\s+Radiometer\s+:)(?P<value>.*)$', re.IGNORECASE)
    Manufacturer = re.compile(r'^\s+(Manufacturer\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber = re.compile(r'^\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    Distance = re.compile(r'^\s+(Distance to Antenna\s+:)(?P<value>.*)$', re.IGNORECASE)
    DiffToAnt = re.compile(r'^\s+(Height Diff to Ant\s+:)(?P<value>.*)$', re.IGNORECASE)
    CalibrationDate = re.compile(r'^\s+(Calibration date\s+:)(?P<value>.*)$', re.IGNORECASE)

    EffectiveDates = re.compile(r'^\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "water-vapor-" + str(sequence)
        self.waterVaporSensor = geo.WaterVaporSensorType(id=text)

        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence
        self.version = [0]


    def parse(self, text, line):

        if  parser.parseCodeTypeAndVersion(self.waterVaporSensor, "type", type(self).Radiometer,
                text, line, "urn:ga-gov-au:water-vapor-sensor-type", self.version):
            return

        if parser.setTextAttribute(self.waterVaporSensor, "manufacturer", type(self).Manufacturer, text, line):
            return

        if parser.setTextAttribute(self.waterVaporSensor, "serialNumber", type(self).SerialNumber, text, line):
            return

        if parser.setDoubleAttribute(self.waterVaporSensor, "distanceToAntenna", type(self).Distance, text, line, True, True):
            return

        if parser.setDoubleAttribute(self.waterVaporSensor, "heightDiffToAntenna", type(self).DiffToAnt, text, line, True, True):
            return

        if parser.setDateTimeAttribute(self.waterVaporSensor, "calibrationDate", type(self).CalibrationDate, text, line):
            return

        if parser.setTimePeriodAttribute(self.waterVaporSensor, "validTime", type(self).EffectiveDates, text, line, SiteLog, self.version[0] < SiteLog.WaterVaporVersion):
            return

        if parser.assignNotes(self.notes, type(self).Notes, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.notes[0] = parser.processingNotes(self.notes[0])
            if len(self.notes[0]) > 0:
                self.waterVaporSensor.notes = self.notes[0]
                self.notesAppended = True
        
        return self.waterVaporSensor


################################################################################
class PressureSensor(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, sensors):
        if cls.Current:
            pressure = cls.Current.complete()
            extra = geo.pressureSensorPropertyType()
            extra.append(pressure)
            extra.append(pressure.validTime.AbstractTimePrimitive.beginPosition)
            sensors.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = PressureSensor(cls.Index)

    Model = re.compile(r'^8\.2\.(?P<version>\d+)\s*(Pressure\s+Sensor\s+Model\s*:)(?P<value>.*)$', re.IGNORECASE)
    Manufacturer = re.compile(r'^\s+(Manufacturer\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber = re.compile(r'^\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    Interval = re.compile(r'^\s+(Data Sampling Interval\s+:)(?P<value>.*)$', re.IGNORECASE)
    Accuracy = re.compile(r'^\s+(Accuracy.*:)(?P<value>.*)$', re.IGNORECASE)
    DiffToAnt = re.compile(r'^\s+(Height Diff to Ant\s+:)(?P<value>.*)$', re.IGNORECASE)
    CalibrationDate = re.compile(r'^\s+(Calibration date\s+:)(?P<value>.*)$', re.IGNORECASE)

    EffectiveDates = re.compile(r'^\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "pressure-sensor-" + str(sequence)
        self.pressureSensor = geo.PressureSensorType(id=text)

        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence

        self.version = [0]

    def parse(self, text, line):

        if  parser.parseCodeTypeAndVersion(self.pressureSensor, "type", type(self).Model,
                text, line, "urn:ga-gov-au:pressure-sensor-type", self.version):
            return

        if parser.setTextAttribute(self.pressureSensor, "manufacturer", type(self).Manufacturer, text, line):
            return

        if parser.setTextAttribute(self.pressureSensor, "serialNumber", type(self).SerialNumber, text, line):
            return

        if parser.setDoubleAttribute(self.pressureSensor, "dataSamplingInterval", type(self).Interval, text, line, True, True):
            return

        if parser.setDoubleAttribute(self.pressureSensor, "accuracy_hPa", type(self).Accuracy, text, line, True, True):
            return

        if parser.setDoubleAttribute(self.pressureSensor, "heightDiffToAntenna", type(self).DiffToAnt, text, line, True, True):
            return

        if parser.setDateTimeAttribute(self.pressureSensor, "calibrationDate", type(self).CalibrationDate, text, line):
            return

        if parser.setTimePeriodAttribute(self.pressureSensor, "validTime", type(self).EffectiveDates, text, line, SiteLog, self.version[0] < SiteLog.PressureVersion):
            return
        
        if parser.assignNotes(self.notes, type(self).Notes, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.notes[0] = parser.processingNotes(self.notes[0])  
            if len(self.notes[0]) > 0:      
                self.pressureSensor.notes = self.notes[0]    
                self.notesAppended = True
        return self.pressureSensor
    
class TemperatureSensor(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, sensors):
        if cls.Current:
            temperature = cls.Current.complete()
            extra = geo.temperatureSensorPropertyType()
            extra.append(temperature)
            extra.append(temperature.validTime.AbstractTimePrimitive.beginPosition)
            sensors.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = TemperatureSensor(cls.Index)

    Model = re.compile(r'^8\.3\.(?P<version>\d+)\s*(Temp\.\s+Sensor\s+Model\s+:)(?P<value>.*)$', re.IGNORECASE)
    Manufacturer = re.compile(r'^\s+(Manufacturer\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber = re.compile(r'^\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    Interval = re.compile(r'^\s+(Data Sampling Interval\s+:)(?P<value>.*)$', re.IGNORECASE)
    Accuracy = re.compile(r'^\s+(Accuracy.*:)(?P<value>.*)$', re.IGNORECASE)
    Aspiration = re.compile(r'^\s+(Aspiration\s+:)(?P<value>.*)$', re.IGNORECASE)
    DiffToAnt = re.compile(r'^\s+(Height Diff to Ant\s+:)(?P<value>.*)$', re.IGNORECASE)
    CalibrationDate = re.compile(r'^\s+(Calibration date\s+:)(?P<value>.*)$', re.IGNORECASE)

    EffectiveDates = re.compile(r'^\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "temperature-sensor-" + str(sequence)
        self.temperatureSensor = geo.TemperatureSensorType(id=text)

        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence
        self.version = [0]


    def parse(self, text, line):

        if  parser.parseCodeTypeAndVersion(self.temperatureSensor, "type", type(self).Model,
                text, line, "urn:ga-gov-au:temperature-sensor-type", self.version):
            return

        if parser.setTextAttribute(self.temperatureSensor, "manufacturer", type(self).Manufacturer, text, line):
            return

        if parser.setTextAttribute(self.temperatureSensor, "serialNumber", type(self).SerialNumber, text, line):
            return

        if parser.setDoubleAttribute(self.temperatureSensor, "dataSamplingInterval", type(self).Interval, text, line, True, True):
            return

        if parser.setDoubleAttribute(self.temperatureSensor, "accuracy_degreesCelcius", type(self).Accuracy, text, line, True, True):
            return

        if parser.setTextAttribute(self.temperatureSensor, "aspiration", type(self).Aspiration, text, line):
            return

        if parser.setDoubleAttribute(self.temperatureSensor, "heightDiffToAntenna", type(self).DiffToAnt, text, line, True, True):
            return

        if parser.setDateTimeAttribute(self.temperatureSensor, "calibrationDate", type(self).CalibrationDate, text, line):
            return

        if parser.setTimePeriodAttribute(self.temperatureSensor, "validTime", type(self).EffectiveDates, text, line, SiteLog, self.version[0] < SiteLog.TemperatureVersion):
            return

        if parser.assignNotes(self.notes, type(self).Notes, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):    
        if not self.notesAppended:
            self.notes[0] = parser.processingNotes(self.notes[0])
            if len(self.notes[0]) > 0:                     
                self.temperatureSensor.notes = self.notes[0]
                self.notesAppended = True
        return self.temperatureSensor

################################################################################