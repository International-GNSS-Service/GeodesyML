from __future__ import print_function

import sys
import os
import re
import logging
import logging.config
import argparse
import codecs
from pyxb import BIND
import pyxb.utils.domutils as domutils
import pyxb.binding.datatypes as xsd
import pyxb.bundles.opengis.gml_3_2 as gml
import pyxb.bundles.opengis.iso19139.v20070417.gmd as gmd
import pyxb.binding.datatypes
import pyxb.bundles.opengis.om_2_0 as om
import pyxb.bundles.opengis.iso19139.v20070417.gco as gco
import pyxb.bundles.common.xlink as xlink
import pyxb.bundles.opengis as opengis
import eGeodesy as geo


################################################################################
logger = logging.getLogger('log2xml')


################################################################################
def setup():
    logging.config.fileConfig('logging.conf')
    pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(gml.Namespace, 'gml')
    pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(xlink.Namespace, 'xlink')
    pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(gmd.Namespace, 'gmd')
    pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(gco.Namespace, 'gco')
    pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(geo.Namespace, 'geo')
    pyxb.RequireValidWhenGenerating(True)

################################################################################
def options():
    options = argparse.ArgumentParser(prog='log2xml',
            description="Convert site log file to GeodesyML file")

    options.add_argument('--version', action='version',
            version='%(prog)s 1.0, Copyright (c) 2016 by Geodesy, Geoscience Australia')

    options.add_argument('-c', '--code',
            default='AUS',
            metavar='AUS',
            help='Country Code, three characters (defaul: %(default)s)')

    options.add_argument("-l", "--sitelog",
            metavar='ssss_yyyydoy.log',
            required=True,
            help='GNSS site log file')

    options.add_argument("-x", "--xml",
            metavar='SSSS.xml',
            help='Output GeodesyML file (defaul: sys.stdout)')

    options.add_argument("-g", "--config",
            type=argparse.FileType('r'),
            metavar='logging.conf',
            default='logging.conf',
            help='Configuration file for logging (defaul: %(default)s)')

    return options.parse_args()

################################################################################
def isEmpty(line):
    text = line.strip()
    return not text

################################################################################
def validateDate(text, reference):
    pattern = re.compile(r'^(\d{4})-(\d{2})-(\d{2})T*$', re.IGNORECASE)
    ok = re.match(pattern, text)
    if ok:
        year = int(ok.group(1))
        month = int(ok.group(2))
        date = int(ok.group(3))
        try:
            theDate = xsd.dateTime(year, month, date)
        except pyxb.PyXBException:
            e = pyxb.PyXBException("incorrect date format")
            raise e
        except:
            e = pyxb.PyXBException("incorrect date format")
            raise e
        reference[0] = ok.group(1) + "-" + ok.group(2) + "-" + ok.group(3)
    else:
        e = pyxb.PyXBException("incorrect date format")
        raise e


################################################################################
def validateDateTime(text, reference):
    pattern = re.compile(r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})Z$', re.IGNORECASE)
    ok = re.match(pattern, text)
    if ok:
        year = int(ok.group(1))
        month = int(ok.group(2))
        date = int(ok.group(3))
        hour = int(ok.group(4))
        minute = int(ok.group(5))
        try:
            theDate = xsd.dateTime(year, month, date, hour, minute)
        except pyxb.PyXBException:
            e = pyxb.PyXBException("incorrect date format")
            raise e
        except:
            e = pyxb.PyXBException("incorrect date format")
            raise e

        reference[0] = ok.group(1)+"-"+ok.group(2)+"-"+ok.group(3)+"T"+ok.group(4)+":"+ok.group(5)+":00Z"

    else:
        return validateDate(text, reference)


################################################################################
def parseText(variable, pattern, text, line):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        variable.append(value)
        return True
    else:
        return False


################################################################################
def assignNotes(variable, pattern, text, line):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        if value:
            if variable[0]:
                variable[0] += "\n"
            variable[0] += value
        return True
    else:
        return False


################################################################################
def parseNillableDouble(variable, pattern, text, line, mandatory=True, output=True):
    floatPattern = re.compile(r'(?P<float>[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)', re.IGNORECASE)
    nonePattern = re.compile(r'none', re.IGNORECASE)
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        if value:
            ok = re.match(floatPattern, value)
            if ok:
                floatValue = ok.group('float')
                nilDouble = geo.NillableDouble(float(floatValue))
                variable.append(nilDouble)
            else:
                if mandatory:
                    nilDouble = geo.NillableDouble()
                    nilDouble._setIsNil()
                    variable.append(nilDouble)
                    if output:
                        logger.info("line %s: a double is expected", line)
                else:
                    ok = re.match(nonePattern, value)
                    if not ok:
                        if output:
                            logger.info("line %s: invalid value as %s", line, value)
        else:
            if mandatory:
                nilDouble = geo.NillableDouble()
                nilDouble._setIsNil()
                variable.append(nilDouble)
                if output:
                    logger.info("line %s: a double is expected", line)
        return True
    else:
        return False


################################################################################
def parseDouble(variable, pattern, text, line, mandatory=False, output=True):
    floatPattern = re.compile(r'(?P<float>[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)', re.IGNORECASE)
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        if value:
            ok = re.match(floatPattern, value)
            if ok:
                floatValue = ok.group('float').strip()
                variable.append(float(floatValue))
            else:
                logger.info("line %s: invalid value as %s", line, value)
                if mandatory:
                    variable.append(0.0)
        else:
            if output:
                logger.info("line %s: missing value", line)
            if mandatory:
                variable.append(0.0)
        return True
    else:
        return False


################################################################################
def parseInt(variable, pattern, text, line, mandatory=False):
    intPattern = re.compile(r'(?P<number>[+-]?(?<!\.)\b[0-9]+\b(?!\.[0-9]))', re.IGNORECASE)
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        if value:
            ok = re.match(intPattern, value)
            if ok:
                number = ok.group('number').strip()
                variable.append(int(number))
            else:
                logger.info("line %s: invalid number as %s", line, value)
                if mandatory:
                    variable.append(0)
        else:
            logger.info("line %s: missing number", line)
            if mandatory:
                variable.append(0)
        return True
    else:
        return False


################################################################################
def parseCodeTypeAndVersion(variable, pattern, text, line, space, versionRef):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        versionRef[0] = int(ok.group('version').strip())
        code = gml.CodeType(value, codeSpace=space)
        variable.append(code)
        return True
    else:
        return False


################################################################################
def parseCodeType(variable, pattern, text, line, space):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        code = gml.CodeType(value, codeSpace=space)
        variable.append(code)
        return True
    else:
        return False


################################################################################
def parseRadomeModelCodeType(variable, pattern, text, line,
        space="urn:igs-org:gnss-radome-model-code"):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        code = geo.igsRadomeModelCodeType(value, codeSpace=space)
        variable.append(code)
        return True
    else:
        return False


################################################################################
def parseAntennaModelCodeType(variable, pattern, text, line, versionRef,
        space="urn:igs-org:gnss-antenna-model-code",
        theCodeList="http://xml.gov.au/icsm/geodesyml/codelists/antenna-receiver-codelists.xml#GeodesyML_GNSSAntennaTypeCode"):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        versionRef[0] = int(ok.group('version').strip())
        code = geo.igsAntennaModelCodeType(value, codeSpace=space, codeList=theCodeList, codeListValue=value)
        variable.append(code)
        return True
    else:
        return False


################################################################################
def parseReceiverModelCodeType(variable, pattern, text, line, versionRef,
        space="urn:igs-org:gnss-receiver-model-code",
        theCodeList="http://xml.gov.au/icsm/geodesyml/codelists/antenna-receiver-codelists.xml#GeodesyML_GNSSReceiverTypeCode"):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        versionRef[0] = int(ok.group('version').strip())
        code = geo.igsReceiverModelCodeType(value, codeSpace=space, codeList=theCodeList, codeListValue=value)
        variable.append(code)
        return True
    else:
        return False


################################################################################
def parseDateTime(variable, pattern, text, line, mandatory=True):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        try:
            replacement = [""]
            validateDateTime(value, replacement)
            dateTime = gml.TimePositionType(replacement[0])
            variable.append(dateTime)
        except pyxb.PyXBException as e:
            if mandatory:
                logger.info("line %s: %s", line, e.message)
            else:
                digit = re.compile(r'\d+')
                if re.match(digit, value):
                    logger.info("line %s: %s", line, e.message)
            variable.append(gml.TimePositionType())
        except:
            pass
        return True
    else:
        return False


################################################################################
def textToDateTime(text, line, mandatory = False):
    pattern = re.compile(r'[\(]?CCYY-MM-DD[\)]?', re.IGNORECASE)
    matched = re.match(pattern, text)
    if matched:
        if mandatory:
            logger.info("line %s: not a valid date time format", line)
# not a valid date time
        return gml.TimePositionType()
    else:
        try:
            replacement = [""]
            validateDateTime(text, replacement)
            dateTime = gml.TimePositionType(replacement[0])
        except pyxb.PyXBException as e:
            logger.info("line %s: not a valid date time format", line)
            dateTime = gml.TimePositionType()
        except:
            dateTime = gml.TimePositionType()

        return dateTime


################################################################################
def parseTimePeriod(variable, pattern, text, line, mandatory = True):
    ok = re.match(pattern, text)
    if ok:
        beginText = ""
        endText = ""
        if ok.group('begin'):
            beginText = ok.group('begin').strip()
        if ok.group('end'):
            endText = ok.group('end').strip()

        begin = textToDateTime(beginText, line, True)
        end = textToDateTime(endText, line, mandatory)

        try:
            validTime = gml.TimePrimitivePropertyType()
            SiteLog.TimePeriodIndex += 1
            timePeriod = gml.TimePeriod(id="time-period-" + str(SiteLog.TimePeriodIndex))
            timePeriod.append(begin)
            timePeriod.append(end)
            validTime.append(timePeriod)
            variable.append(validTime)
        except pyxb.PyXBException as e:
            logger.info("line %s: %s", line, e.message)
            validTime = gml.TimePrimitivePropertyType(nilReason="inapplicable")
            variable.append(validTime)
        except:
            pass

        return True
    else:
        return False


################################################################################
def parseTimeInstant(variable, pattern, text, line, sequence):
    ok = re.match(pattern, text)
    if ok:
        beginText = ok.group('begin').strip()
        begin = textToDateTime(beginText, line, True)
        endText = ok.group('end').strip()
        end = textToDateTime(endText, line, False)

        try:
            validTime = gml.TimePrimitivePropertyType()
            SiteLog.TimeInstantIndex
            timeInstant = gml.TimeInstant(id="time-instant-" + str(SiteLog.TimeInstantIndex))
            timeInstant.append(begin)
            validTime.append(timeInstant)
            variable.append(validTime)
        except pyxb.PyXBException as e:
            logger.info("line %s: %s", line, e.message)
            validTime = gml.TimePrimitivePropertyType(nilReason="inapplicable")
            variable.append(validTime)
        except:
            pass

        return True
    else:
        return False


################################################################################
def toLatitude(value):
    text = str(value)
    pattern = re.compile(r'[+-]?(\d{2})(\d{2})((\d{2})(\.\d*)?)')
    ok = re.match(pattern, text)
    if ok:
        degree = float(ok.group(1))
        minute = float(ok.group(2))
        second = float(ok.group(3))
        number = degree + minute / 60.0 + second / 3600.0
        if value < 0.0:
            text = "-" + str(number)
        else:
            text = "+" + str(number)
        return float(text)
    else:
        logger.error("incorrect latitude format")
        return 0.0


################################################################################
def toLongitude(value):
    text = str(value)
    pattern = re.compile(r'[+-]?(\d{3})(\d{2})((\d{2})(\.\d*)?)')
    ok = re.match(pattern, text)
    if ok:
        degree = float(int(ok.group(1)))
        minute = float(ok.group(2))
        second = float(ok.group(3))
        number = degree + minute / 60.0 + second / 3600.0
        if value < 0.0:
            text = "-" + str(number)
        else:
            text = "+" + str(number)
        return float(text)
    else:
        logger.error("incorrect longitude format")
        return 0.0


################################################################################
def assignText(variable, pattern, text, line):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        variable[0] = value
        return True
    else:
        return False


################################################################################
def assignNillableDouble(variable, pattern, text, line, mandatory=False):
    floatPattern = re.compile(r'(?P<float>[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)', re.IGNORECASE)
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        if value:
            ok = re.match(floatPattern, value)
            if ok:
                floatValue = ok.group('float')
                variable[0] = geo.NillableDouble(float(floatValue))
            else:
                logger.info("line %s: invalid value as %s", line, value)
                variable[0] = geo.NillableDouble()
                variable[0]._setIsNil()
        else:
            variable[0] = geo.NillableDouble()
            variable[0]._setIsNil()
            logger.info("line %s: missing value", line)
        return True
    else:
        return False


################################################################################
def assignDouble(variable, pattern, text, line, mandatory=False):
    floatPattern = re.compile(r'(?P<float>[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)', re.IGNORECASE)
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        if value:
            ok = re.match(floatPattern, value)
            if ok:
                floatValue = ok.group('float').strip()
                variable[0] = float(floatValue)
            else:
                logger.info("line %s: invalid value as %s", line, value)
                if mandatory:
                    variable[0] = 0.0
        else:
            logger.info("line %s: missing value", line)
            if mandatory:
                variable[0] = 0.0
        return True
    else:
        return False


################################################################################
class FormInformation(object):
    Current = None
    Index = 0

    @classmethod
    def Detach(cls):
        if cls.Current:
            information = cls.Current.complete()
            cls.Current = None
            return information

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = FormInformation()


    PreparedBy = re.compile(r'^\s+(Prepared\s+by\s+.*:)(?P<value>.*)$', re.IGNORECASE)
    DatePrepared = re.compile(r'\s+(Date\s+Prepared\s+:)(?P<value>.*)$', re.IGNORECASE)
    ReportType = re.compile(r'\s+(Report\s+Type\s+:)(?P<value>.*)$', re.IGNORECASE)

    def __init__(self):
        self.formInformation = geo.formInformationType()

    def parse(self, text, line):
        if parseText(self.formInformation, type(self).PreparedBy, text, line):
            return

        if parseDateTime(self.formInformation, type(self).DatePrepared, text, line):
            return

        if parseText(self.formInformation, type(self).ReportType, text, line):
            return

    def complete(self):
        # if notes, then added notes
        return self.formInformation


################################################################################
class EpisodicEvent(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, eventSet):
        if cls.Current:
            event = cls.Current.complete()
            extra = geo.localEpisodicEventsPropertyType()
            extra.append(event)
            extra.append(event.validTime.AbstractTimePrimitive.beginPosition)
            eventSet.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = EpisodicEvent(cls.Index)

    Date = re.compile(r'^10\.\d+\s*(Date.*:)(((?P<begin>.*)\/(?P<end>.*))|(\s*))$', re.IGNORECASE)
    Event = re.compile(r'\s+(Event\s+:)(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "episodic-event-" + str(sequence)
        self.episodicEvent = geo.localEpisodicEventsType(id=text)
# will fixed it lated, passed in by constructor
        self.sequence = sequence 

    def parse(self, text, line):
        if parseTimePeriod(self.episodicEvent, type(self).Date, text, line, True):
            return

        if parseText(self.episodicEvent, type(self).Event, text, line):
            return

    def complete(self):
        return self.episodicEvent


################################################################################
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

    Model = re.compile(r'^8\.3\.(?P<version>\d+)\s*(Temp.*:)(?P<value>.*)$', re.IGNORECASE)
    Manufacturer = re.compile(r'\s+(Manufacturer\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber = re.compile(r'\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    Interval = re.compile(r'\s+(Data Sampling Interval\s+:)(?P<value>.*)$', re.IGNORECASE)
    Accuracy = re.compile(r'\s+(Accuracy.*:)(?P<value>.*)$', re.IGNORECASE)
    Aspiration = re.compile(r'\s+(Aspiration.*:)(?P<value>.*)$', re.IGNORECASE)
    DiffToAnt = re.compile(r'\s+(Height Diff to Ant.*:)(?P<value>.*)$', re.IGNORECASE)
    CalibrationDate = re.compile(r'\s+(Calibration date.*:)(?P<value>.*)$', re.IGNORECASE)

    EffectiveDates = re.compile(r'\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*))$', re.IGNORECASE)

    Notes = re.compile(r'\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "temperature-sensor-" + str(sequence)
        self.temperatureSensor = geo.temperatureSensorType(id=text)

        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence

        self.interval = [geo.NillableDouble()]
        self.accuracy = [geo.NillableDouble()]

        self.aspiration = [""]

        self.version = [0]


    def parse(self, text, line):

        if parseCodeTypeAndVersion(self.temperatureSensor, type(self).Model, 
                text, line, "urn:ga-gov-au:temperature-sensor-type", self.version):
            return

        if parseText(self.temperatureSensor, type(self).Manufacturer, text, line):
            return

        if parseText(self.temperatureSensor, type(self).SerialNumber, text, line):
            return

        if assignNillableDouble(self.interval, type(self).Interval, text, line, True):
            return

        if assignNillableDouble(self.accuracy, type(self).Accuracy, text, line, True):
            return

        if assignText(self.aspiration, type(self).Aspiration, text, line):
            return

        if parseNillableDouble(self.temperatureSensor, type(self).DiffToAnt, text, line, True):
            return

        if parseDateTime(self.temperatureSensor, type(self).CalibrationDate, text, line):
            return

        if parseTimePeriod(self.temperatureSensor, type(self).EffectiveDates, text, line, self.version[0] < SiteLog.TemperatureVersion):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.temperatureSensor.append(self.interval[0])
            self.temperatureSensor.append(self.accuracy[0])
            self.temperatureSensor.append(self.aspiration[0])
            self.temperatureSensor.append(self.notes[0])
            self.notesAppended = True
        return self.temperatureSensor


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

    Model = re.compile(r'^8\.2\.(?P<version>\d+)\s*(Pressure.*:)(?P<value>.*)$', re.IGNORECASE)
    Manufacturer = re.compile(r'\s+(Manufacturer\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber = re.compile(r'\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    Interval = re.compile(r'\s+(Data Sampling Interval\s+:)(?P<value>.*)$', re.IGNORECASE)
    Accuracy = re.compile(r'\s+(Accuracy.*:)(?P<value>.*)$', re.IGNORECASE)
    DiffToAnt = re.compile(r'\s+(Height Diff to Ant.*:)(?P<value>.*)$', re.IGNORECASE)
    CalibrationDate = re.compile(r'\s+(Calibration date.*:)(?P<value>.*)$', re.IGNORECASE)

    EffectiveDates = re.compile(r'\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*))$', re.IGNORECASE)

    Notes = re.compile(r'\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "pressure-sensor-" + str(sequence)
        self.pressureSensor = geo.pressureSensorType(id=text)

        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence

        self.interval = [geo.NillableDouble()]
        self.accuracy = [geo.NillableDouble()]

        self.version = [0]

    def parse(self, text, line):

        if parseCodeTypeAndVersion(self.pressureSensor, type(self).Model,
                text, line, "urn:ga-gov-au:pressure-sensor-type", self.version):
            return

        if parseText(self.pressureSensor, type(self).Manufacturer, text, line):
            return

        if parseText(self.pressureSensor, type(self).SerialNumber, text, line):
            return

        if assignNillableDouble(self.interval, type(self).Interval, text, line, True):
            return

        if assignNillableDouble(self.accuracy, type(self).Accuracy, text, line, True):
            return

        if parseNillableDouble(self.pressureSensor, type(self).DiffToAnt, text, line, True):
            return

        if parseDateTime(self.pressureSensor, type(self).CalibrationDate, text, line):
            return

        if parseTimePeriod(self.pressureSensor, type(self).EffectiveDates, text, line, self.version[0] < SiteLog.PressureVersion):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.pressureSensor.append(self.interval[0])
            self.pressureSensor.append(self.accuracy[0])
            self.pressureSensor.append(self.notes[0])
            self.notesAppended = True
        return self.pressureSensor


################################################################################
class CollocationInformation(object):
    Current = None
    Index = 0

    @classmethod
    def Append(cls, information):
        if cls.Current:
            collocation = cls.Current.complete()
            wrapper = geo.collocationInformationPropertyType()
            wrapper.append(collocation)
            wrapper.append(collocation.validTime.AbstractTimePrimitive.beginPosition)
            information.append(wrapper)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = CollocationInformation(cls.Index)

    Instrumentation = re.compile(r'^7\.\d+\s*(Instrumentation Type.*:)(?P<value>.*)$', re.IGNORECASE)
    Status = re.compile(r'\s+(Status\s+:)(?P<value>.*)$', re.IGNORECASE)
    EffectiveDates = re.compile(r'\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*))$', re.IGNORECASE)

    Notes = re.compile(r'\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "instrumentation-type-" + str(sequence)
        self.collocation = geo.collocationInformationType(id=text)

        self.notes = [""]
        self.notesAppended = False

    def parse(self, text, line):
        if parseCodeType(self.collocation, type(self).Instrumentation, text, line, "urn:ga-gov-au:instrumentation-type"):
            return

        if parseCodeType(self.collocation, type(self).Status, text, line, "urn:ga-gov-au:status-type"):
            return

        if parseTimePeriod(self.collocation, type(self).EffectiveDates, text, line, False):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.collocation.append(self.notes[0])
            self.notesAppended = True
        return self.collocation


################################################################################
class HumiditySensor(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, sensors):
        if cls.Current:
            humidity = cls.Current.complete()
            extra = geo.humiditySensorPropertyType()
            extra.append(humidity)
            extra.append(humidity.validTime.AbstractTimePrimitive.beginPosition)
            sensors.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = HumiditySensor(cls.Index)

    Model = re.compile(r'^8\.1\.(?P<version>\d+)\s*(Humidity.*:)(?P<value>.*)$', re.IGNORECASE)
    Manufacturer = re.compile(r'\s+(Manufacturer\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber = re.compile(r'\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    Interval = re.compile(r'\s+(Data Sampling Interval\s+:)(?P<value>.*)$', re.IGNORECASE)
    Accuracy = re.compile(r'\s+(Accuracy.*:)(?P<value>.*)$', re.IGNORECASE)
    Aspiration = re.compile(r'\s+(Aspiration.*:)(?P<value>.*)$', re.IGNORECASE)
    DiffToAnt = re.compile(r'\s+(Height Diff to Ant.*:)(?P<value>.*)$', re.IGNORECASE)
    CalibrationDate = re.compile(r'\s+(Calibration date.*:)(?P<value>.*)$', re.IGNORECASE)

    EffectiveDates = re.compile(r'\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*))$', re.IGNORECASE)

    Notes = re.compile(r'\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "humidity-sensor-" + str(sequence)
        self.humiditySensor = geo.humiditySensorType(id=text)

        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence

        self.interval = [geo.NillableDouble()]
        self.accuracy = [geo.NillableDouble()]
        self.aspiration = [""]

        self.version = [0]


    def parse(self, text, line):

        if parseCodeTypeAndVersion(self.humiditySensor, type(self).Model,
                text, line, "urn:ga-gov-au:humidity-sensor-type", self.version):
            return

        if parseText(self.humiditySensor, type(self).Manufacturer, text, line):
            return

        if parseText(self.humiditySensor, type(self).SerialNumber, text, line):
            return

        if assignNillableDouble(self.interval, type(self).Interval, text, line, True):
            return

        if assignNillableDouble(self.accuracy, type(self).Accuracy, text, line, True):
            return

        if assignText(self.aspiration, type(self).Aspiration, text, line):
            return

        if parseNillableDouble(self.humiditySensor, type(self).DiffToAnt, text, line, True):
            return

        if parseDateTime(self.humiditySensor, type(self).CalibrationDate, text, line):
            return

        if parseTimePeriod(self.humiditySensor, type(self).EffectiveDates, text, line, self.version[0] < SiteLog.HumidityVersion):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.humiditySensor.append(self.interval[0])
            self.humiditySensor.append(self.accuracy[0])
            self.humiditySensor.append(self.aspiration[0])
            self.humiditySensor.append(self.notes[0])
            self.notesAppended = True
        return self.humiditySensor


################################################################################
class FrequencyStandard(object):
    Current = None
    Index = 0

    @classmethod
    def Append(cls, frequencyStandards):
        if cls.Current:
            standard = cls.Current.complete()
            wrapper = geo.frequencyStandardPropertyType()
            wrapper.append(standard)
            wrapper.append(standard.validTime.AbstractTimePrimitive.beginPosition)
            frequencyStandards.append(wrapper)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = FrequencyStandard(cls.Index)


    StandardType = re.compile(r'^6\.(?P<version>\d+)\s*(Standard\s+Type.*:)(?P<value>.*)$', re.IGNORECASE)
    InputFrequency = re.compile(r'\s+(Input Frequency\s+:)(?P<value>.*)$', re.IGNORECASE)
    EffectiveDates = re.compile(r'\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*))$', re.IGNORECASE)

    Notes = re.compile(r'\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "frequency-standard-" + str(sequence)
        self.frequencyStandard = geo.frequencyStandardType(id=text)

        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence

        self.version = [0]
        self.internal = False 

    def parse(self, text, line):

        if parseCodeTypeAndVersion(self.frequencyStandard, type(self).StandardType, 
                text, line, "urn:ga-gov-au:frequencty-standard-type", self.version):
            pattern = re.compile(r'^.*INTERNAL\s*$', re.IGNORECASE)
            ok = re.match(pattern, text)
            if ok:
                self.internal = True
            else:
                self.internal = False
            return

        if parseNillableDouble(self.frequencyStandard, type(self).InputFrequency, text, line, True, not self.internal):
            return

        if parseTimePeriod(self.frequencyStandard, type(self).EffectiveDates, text, line, self.version[0] < SiteLog.FrequencyVersion):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.frequencyStandard.append(self.notes[0])
            self.notesAppended = True
        return self.frequencyStandard


################################################################################
class LocalTie(object):
    Current = None
    Index = 0

    @classmethod
    def Append(cls, ties):
        if cls.Current:
            localTie = cls.Current.complete()
            wrapper = geo.surveyedLocalTiesPropertyType()
            wrapper.append(localTie)
            wrapper.append(localTie.dateMeasured)
            ties.append(wrapper)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = LocalTie(cls.Index)


    Name = re.compile(r'^5\.\d+\s*(Tied\s+Marker\s+Name.*:)(?P<value>.*)$', re.IGNORECASE)
    Usage = re.compile(r'\s+(Tied Marker Usage\s+:)(?P<value>.*)$', re.IGNORECASE)
    CDPNumber = re.compile(r'\s+(Tied Marker CDP Number\s+:)(?P<value>.*)$', re.IGNORECASE)
    DOMESNumber = re.compile(r'\s+(Tied Marker DOMES Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    DX = re.compile(r'\s+(dx.*:)(?P<value>.*)$', re.IGNORECASE)
    DY = re.compile(r'\s+(dy.*:)(?P<value>.*)$', re.IGNORECASE)
    DZ = re.compile(r'\s+(dz.*:)(?P<value>.*)$', re.IGNORECASE)
    Accuracy = re.compile(r'\s+(Accuracy.*:\s*[+]?[-]?)(?P<value>.*)$', re.IGNORECASE)

    Method = re.compile(r'\s+(Survey method\s+:)(?P<value>.*)$', re.IGNORECASE)
    DateMeasured  = re.compile(r'\s+(Date Measured\s+:)(?P<value>.*)$', re.IGNORECASE)

    Notes = re.compile(r'\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "local-tie-" + str(sequence)
        self.localTie = geo.surveyedLocalTiesType(id=text)

        self.dx = [geo.NillableDouble()]
        self.dy = [geo.NillableDouble()]
        self.dz = [geo.NillableDouble()]

        self.notes = [""]
        self.notesAppended = False

    def parse(self, text, line):
        if parseText(self.localTie, type(self).Name, text, line):
            return

        if parseText(self.localTie, type(self).Usage, text, line):
            return

        if parseText(self.localTie, type(self).CDPNumber, text, line):
            return

        if parseText(self.localTie, type(self).DOMESNumber, text, line):
            return

        if assignNillableDouble(self.dx, type(self).DX, text, line):
            return

        if assignNillableDouble(self.dy, type(self).DY, text, line):
            return

        if assignNillableDouble(self.dz, type(self).DZ, text, line):
            self.localTie.append(pyxb.BIND(self.dx[0], self.dy[0], self.dz[0]))
            return

        if parseNillableDouble(self.localTie, type(self).Accuracy, text, line, True):
            return

        if parseText(self.localTie, type(self).Method, text, line):
            return

        if parseDateTime(self.localTie, type(self).DateMeasured, text, line):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.localTie.append(self.notes[0])
            self.notesAppended = True
        return self.localTie


################################################################################
class SiteLocation(object):
    Current = None
    Index = 0

    @classmethod
    def Detach(cls):
        if cls.Current:
            location = cls.Current.complete()
            cls.Current = None
            return location

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = SiteLocation()


    City = re.compile(r'\s+(City or Town\s+:)(?P<value>.*)$', re.IGNORECASE)
    State = re.compile(r'\s+(State or Province\s+:)(?P<value>.*)$', re.IGNORECASE)
    Tectonic = re.compile(r'\s+(Tectonic Plate\s+:)(?P<value>.*)$', re.IGNORECASE)
    Country = re.compile(r'\s+(Country\s+:)(?P<value>.*)$', re.IGNORECASE)
    XCoordinate = re.compile(r'\s+(X coordinate.*:)(?P<value>.*)$', re.IGNORECASE)
    YCoordinate = re.compile(r'\s+(Y coordinate.*:)(?P<value>.*)$', re.IGNORECASE)
    ZCoordinate = re.compile(r'\s+(Z coordinate.*:)(?P<value>.*)$', re.IGNORECASE)
    Latitude = re.compile(r'\s+(Latitude.*:)(?P<value>.*)$', re.IGNORECASE)
    Longitude = re.compile(r'\s+(Longitude.*:)(?P<value>.*)$', re.IGNORECASE)
    Elevation = re.compile(r'\s+(Elevation.*:)(?P<value>.*)$', re.IGNORECASE)
    Notes = re.compile(r'\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self):
        self.siteLocation = geo.siteLocationType()
        self.notes = [""]
        self.notesAppended = False
        self.x = [""]
        self.y = [""]
        self.z = [""]
        self.lat = [""]
        self.lng = [""]
        self.ele = [""]

    def parse(self, text, line):
        if parseText(self.siteLocation, type(self).City, text, line):
            return

        if parseText(self.siteLocation, type(self).State, text, line):
            return

        if parseCodeType(self.siteLocation, type(self).Tectonic, text, line, "urn:ga-gov-au:plate-type"):
            return

        if assignText(self.x, type(self).XCoordinate, text, line):
            return

        if assignText(self.y, type(self).YCoordinate, text, line):
            return

        if assignText(self.z, type(self).ZCoordinate, text, line):
            return

        if assignText(self.lat, type(self).Latitude, text, line):
            return

        if assignText(self.lng, type(self).Longitude, text, line):
            return

        if assignText(self.ele, type(self).Elevation, text, line):

            self.siteLocation.append(pyxb.BIND(
                self.x[0],
                self.y[0],
                self.z[0],
                toLatitude(self.lat[0]),
                toLongitude(self.lng[0]),
                self.ele[0]))

            return

        ok = re.match(type(self).Country, text)
        if ok:
            country = ok.group('value').strip()
            SiteLog.Country = country
            countryCode = SiteLog.CountryCode 
            self.siteLocation.append(countryCode)
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.siteLocation.append(self.notes[0])
            self.notesAppended = True
        return self.siteLocation


################################################################################
class GNSSReceiver(object):
    Current = None
    Index = 0

    @classmethod
    def Append(cls, receivers):
        if cls.Current:
            gnssReceiver = cls.Current.complete()
            wrapper = geo.gnssReceiverPropertyType()
            wrapper.append(gnssReceiver)
            wrapper.append(gnssReceiver.dateInstalled)
            receivers.append(wrapper)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = GNSSReceiver(cls.Index)


    ReceiverType = re.compile(r'^3\.(?P<version>\d+)\s*(Receiver\s+Type.*:)(?P<value>.*)$', re.IGNORECASE)
    SatelliteSystem = re.compile(r'\s+(Satellite System\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber  = re.compile(r'\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)
    FirmwareVersion  = re.compile(r'\s+(Firmware Version\s+:)(?P<value>.*)$', re.IGNORECASE)
    Cutoff = re.compile(r'\s+(Elevation Cutoff Setting\s+:)(?P<value>.*)$', re.IGNORECASE)
    DateInstalled  = re.compile(r'\s+(Date Installed\s+:)(?P<value>.*)$', re.IGNORECASE)
    DateRemoved  = re.compile(r'\s+(Date Removed\s+:)(?P<value>.*)$', re.IGNORECASE)
    Stabilizer = re.compile(r'\s+(Temperature Stabiliz\.\s+:)(?P<value>.*)$', re.IGNORECASE)
    Notes = re.compile(r'\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "gnss-receiver-" + str(sequence)
        manufacturerSerialNumber = "unknown"
        self.gnssReceiver = geo.gnssReceiverType(id=text)
        self.gnssReceiver.append(manufacturerSerialNumber)
        self.notes = [""]
        self.notesAppended = False
        self.version = [0]

    def parse(self, text, line):
        if parseReceiverModelCodeType(self.gnssReceiver, type(self).ReceiverType, text, line, self.version):
            return

        if parseCodeType(self.gnssReceiver, type(self).SatelliteSystem, text, line, "urn:ga-gov-au:satellite-system-type"):
            return

        if parseText(self.gnssReceiver, type(self).SerialNumber, text, line):
            return

        if parseText(self.gnssReceiver, type(self).FirmwareVersion, text, line):
            return

        if parseNillableDouble(self.gnssReceiver, type(self).Cutoff, text, line, True):
            return

        if parseDateTime(self.gnssReceiver, type(self).DateInstalled, text, line):
            return

        if parseDateTime(self.gnssReceiver, type(self).DateRemoved, text, line, self.version[0] < SiteLog.ReceiverVersion):
            return

        if parseNillableDouble(self.gnssReceiver, type(self).Stabilizer, text, line, False):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.gnssReceiver.append(self.notes[0])
            self.notesAppended = True
            self.gnssReceiver.manufacturerSerialNumber = self.gnssReceiver.serialNumber
        return self.gnssReceiver


################################################################################
class GNSSAntenna(object):
    Current = None
    Index = 0

    @classmethod
    def Append(cls, antennas):
        if cls.Current:
            gnssAntenna = cls.Current.complete()
            wrapper = geo.gnssAntennaPropertyType()
            wrapper.append(gnssAntenna)
            wrapper.append(gnssAntenna.dateInstalled)
            antennas.append(wrapper)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = GNSSAntenna(cls.Index)


    AntennaType = re.compile(r'^4\.(?P<version>\d+)\s*(Antenna\s+Type.*:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber  = re.compile(r'\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    ReferencePoint = re.compile(r'\s+(Antenna Reference Point\s+:)(?P<value>.*)$', re.IGNORECASE)
    Up = re.compile(r'^.*(ARP\s+Up.*:)(?P<value>.*)$', re.IGNORECASE)
    North = re.compile(r'^.*(ARP\s+North.*:)(?P<value>.*)$', re.IGNORECASE)
    East = re.compile(r'^.*(ARP\s+East.*:)(?P<value>.*)$', re.IGNORECASE)

    Alignment = re.compile(r'\s+(Alignment from True N\s+:)(?P<value>.*)$', re.IGNORECASE)
    RadomeType = re.compile(r'\s+(Antenna Radome Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    RadomeSerialNumber = re.compile(r'\s+(Radome Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    CableType = re.compile(r'\s+(Antenna Cable Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    CableLength = re.compile(r'\s+(Antenna Cable Length\s+:)(?P<value>.*)$', re.IGNORECASE)

    DateInstalled  = re.compile(r'\s+(Date Installed\s+:)(?P<value>.*)$', re.IGNORECASE)
    DateRemoved  = re.compile(r'\s+(Date Removed\s+:)(?P<value>.*)$', re.IGNORECASE)

    Notes = re.compile(r'\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "gnss-antenna-" + str(sequence)
        manufacturerSerialNumber = "unknown"
        self.gnssAntenna = geo.gnssAntennaType(id=text)
        self.gnssAntenna.append(manufacturerSerialNumber)
        self.notes = [""]
        self.notesAppended = False
        self.version = [0]

    def parse(self, text, line):
        if parseAntennaModelCodeType(self.gnssAntenna, type(self).AntennaType, text, line, self.version):
            return

        if parseText(self.gnssAntenna, type(self).SerialNumber, text, line):
            return

        if parseCodeType(self.gnssAntenna, type(self).ReferencePoint, text, line,
                "urn:ga-gov-au:antenna-reference-point-type"):
            return

        if parseNillableDouble(self.gnssAntenna, type(self).Up, text, line):
            return

        if parseNillableDouble(self.gnssAntenna, type(self).North, text, line):
            return

        if parseNillableDouble(self.gnssAntenna, type(self).East, text, line):
            return

        if parseNillableDouble(self.gnssAntenna, type(self).Alignment, text, line):
            return

        if parseRadomeModelCodeType(self.gnssAntenna, type(self).RadomeType, text, line):
            return

        if parseText(self.gnssAntenna, type(self).RadomeSerialNumber, text, line):
            return

        if parseText(self.gnssAntenna, type(self).CableType, text, line):
            return

        if parseNillableDouble(self.gnssAntenna, type(self).CableLength, text, line, True):
            return

        if parseDateTime(self.gnssAntenna, type(self).DateInstalled, text, line):
            return

        if parseDateTime(self.gnssAntenna, type(self).DateRemoved, text, line, self.version[0] < SiteLog.AntennaVersion):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.gnssAntenna.append(self.notes[0])
            self.notesAppended = True
            self.gnssAntenna.manufacturerSerialNumber = self.gnssAntenna.serialNumber
        return self.gnssAntenna


################################################################################
class SiteIdentification(object):
    Current = None
    Index = 0

    @classmethod
    def Detach(cls):
        if cls.Current:
            identification = cls.Current.complete()
            cls.Current = None
            return identification

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = SiteIdentification()


    SiteName = re.compile(r'^\s+(Site\s+Name\s+:)(?P<value>.*)$', re.IGNORECASE)
    FourCharacterID = re.compile(r'\s+(Four\s+Character\s+ID\s+:)(?P<value>.*)$', re.IGNORECASE)
    MonumentInscription = re.compile(r'\s+(Monument\s+Inscription\s+:)(?P<value>.*)$', re.IGNORECASE)
    IersDOMESNumber = re.compile(r'\s+(IERS\s+DOMES\s+Number\s+:)(?P<value>.*)$', re.IGNORECASE)
    CdpNumber = re.compile(r'\s+(CDP\s+Number\s+:)(?P<value>.*)$', re.IGNORECASE)
    MonumentDescription = re.compile(r'\s+(Monument\s+Description\s+:)(?P<value>.*)$', re.IGNORECASE)
    HeightOfTheMonument = re.compile(r'\s+(Height\s+of\s+The\s+Monument\s+:)(?P<value>.*)$', re.IGNORECASE)
    MonumentFoundation = re.compile(r'\s+(Monument\s+Foundation\s+:)(?P<value>.*)$', re.IGNORECASE)
    FoundationDepth = re.compile(r'\s+(Foundation\s+Depth\s+:)(?P<value>.*)$', re.IGNORECASE)
    MarkerDescription = re.compile(r'\s+(Marker\s+Description\s+:)(?P<value>.*)$', re.IGNORECASE)
    DateInstalled = re.compile(r'\s+(Date\s+Installed\s+:)(?P<value>.*)$', re.IGNORECASE)
    GeologicCharacteristic = re.compile(r'\s+(Geologic\s+Characteristic\s+:)(?P<value>.*)$', re.IGNORECASE)
    BedrockType = re.compile(r'\s+(Bedrock\s+Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    BedrockCondition = re.compile(r'\s+(Bedrock\s+Condition\s+:)(?P<value>.*)$', re.IGNORECASE)
    FractureSpacing = re.compile(r'\s+(Fracture\s+Spacing\s+:)(?P<value>.*)$', re.IGNORECASE)
    FaultZonesNearby = re.compile(r'\s+(Fault\s+zones\s+nearby\s+:)(?P<value>.*)$', re.IGNORECASE)
    Distance_Activity = re.compile(r'\s+(Distance\/activity\s+:)(?P<value>.*)$', re.IGNORECASE)
    Notes = re.compile(r'\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self):
        self.siteIdentification = geo.siteIdentificationType()
        self.notes = [""]
        self.notesAppended = False

    def parse(self, text, line):
        if parseText(self.siteIdentification, type(self).SiteName, text, line):
            return

        if parseText(self.siteIdentification, type(self).FourCharacterID, text, line):
            return

        if parseText(self.siteIdentification, type(self).MonumentInscription, text, line):
            return

        if parseText(self.siteIdentification, type(self).IersDOMESNumber, text, line):
            return

        if parseText(self.siteIdentification, type(self).CdpNumber, text, line):
            return

        if parseCodeType(self.siteIdentification, type(self).MonumentDescription,
                text, line, "urn:ga-gov-au:monument-description-type"):
            return

        if parseNillableDouble(self.siteIdentification, type(self).HeightOfTheMonument, text, line, False):
            return

        if parseText(self.siteIdentification, type(self).MonumentFoundation, text, line):
            return

        if parseNillableDouble(self.siteIdentification, type(self).FoundationDepth, text, line, False):
            return

        if parseText(self.siteIdentification, type(self).MarkerDescription, text, line):
            return

        if parseDateTime(self.siteIdentification, type(self).DateInstalled, text, line):
            return

        if parseCodeType(self.siteIdentification, type(self).GeologicCharacteristic,
                text, line, "urn:ga-gov-au:geologic-characteristic-type"):
            return

        if parseText(self.siteIdentification, type(self).BedrockType, text, line):
            return

        if parseText(self.siteIdentification, type(self).BedrockCondition, text, line):
            return

        if parseText(self.siteIdentification, type(self).FractureSpacing, text, line):
            return

        if parseCodeType(self.siteIdentification, type(self).FaultZonesNearby,
                text, line, "urn:ga-gov-au:fault-zones-type"):
            return

        if parseText(self.siteIdentification, type(self).Distance_Activity, text, line):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.notesAppended:
            self.siteIdentification.append(self.notes[0])
            self.notesAppended = True
        return self.siteIdentification


################################################################################
class MoreInformation(object):
    Current = None
    Index = 0

    @classmethod
    def Detach(cls):
        if cls.Current:
            information = cls.Current.complete()
            cls.Current = None
            return information

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = MoreInformation(cls.Index)

    PrimaryDataCenter = re.compile(r'\s+(Primary Data Center\s+:)(?P<value>.*)$', re.IGNORECASE)
    SecondaryDataCenter = re.compile(r'\s+(Secondary Data Center\s+:)(?P<value>.*)$', re.IGNORECASE)
    URL = re.compile(r'\s+(URL for More Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    SiteMap = re.compile(r'\s+(Site Map\s+:)(?P<value>.*)$', re.IGNORECASE)
    SiteDiagram = re.compile(r'\s+(Site Diagram\s+:)(?P<value>.*)$', re.IGNORECASE)
    HorizonMask = re.compile(r'\s+(Horizon Mask\s+:)(?P<value>.*)$', re.IGNORECASE)
    MonumentDescription = re.compile(r'\s+(Monument Description\s+:)(?P<value>.*)$', re.IGNORECASE)
    SitePictures = re.compile(r'\s+(Site Pictures\s+:)(?P<value>.*)$', re.IGNORECASE)

    Notes = re.compile(r'\s+(Additional Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "more-information-" + str(sequence)
        self.moreInformation = geo.moreInformationType()

        self.done = False

        self.primaryDataCenter = [""]
        self.secondaryDataCenter = [""]

        self.notes = [""]
        self.sequence = sequence

        self.url =[""]
        self.siteMap =[""]
        self.siteDiagram =[""]
        self.horizonMask =[""]
        self.monumentDescription =[""]
        self.sitePictures =[""]

    def parse(self, text, line):
        if assignText(self.url, type(self).URL, text, line):
            return

        if assignText(self.siteMap, type(self).SiteMap, text, line):
            return

        if assignText(self.siteDiagram, type(self).SiteDiagram, text, line):
            return

        if assignText(self.horizonMask, type(self).HorizonMask, text, line):
            return

        if assignText(self.monumentDescription, type(self).MonumentDescription, text, line):
            return

        if assignText(self.sitePictures, type(self).SitePictures, text, line):
            return

        if assignText(self.primaryDataCenter, type(self).PrimaryDataCenter, text, line):
            return

        if assignText(self.secondaryDataCenter, type(self).SecondaryDataCenter, text, line):
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            return

        if assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        if not self.done:
            self.done = True
            self.moreInformation.dataCenter.append(self.primaryDataCenter[0])
            self.moreInformation.dataCenter.append(self.secondaryDataCenter[0])
            self.moreInformation.urlForMoreInformation = self.url[0]
            self.moreInformation.siteMap = self.siteMap[0]
            self.moreInformation.siteDiagram = self.siteDiagram[0]
            self.moreInformation.horizonMask = self.horizonMask[0]
            self.moreInformation.monumentDescription = self.monumentDescription[0]
            self.moreInformation.sitePictures= self.sitePictures[0]
            self.moreInformation.antennaGraphicsWithDimensions= ""
            self.moreInformation.insertTextGraphicFromAntenna= ""
            self.moreInformation.DOI = gml.CodeType("TODO", codeSpace="urn:ga-gov-au:self.moreInformation-type")
            self.moreInformation.notes = self.notes[0]

        return self.moreInformation


################################################################################
class ContactAgency(object):
    Current = None
    Index = 0

    @classmethod
    def Append(cls, contact):
        if cls.Current:
            agency = cls.Current.complete()
            contact.append(agency)
            cls.Current = None

    @classmethod
    def Detach(cls):
        if cls.Current:
            agency = cls.Current.complete()
            cls.Current = None
            return agency

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = ContactAgency(cls.Index)

    Agency = re.compile(r'\s+(Agency\s+:)(?P<value>.*)$', re.IGNORECASE)
    Address = re.compile(r'\s+(Mailing Address\s+:)(?P<value>.*)$', re.IGNORECASE)
    Primary = re.compile(r'\s+Primary Contact.*$', re.IGNORECASE)
    Name = re.compile(r'\s+(Contact Name\s+:)(?P<value>.*)$', re.IGNORECASE)
    Telephone = re.compile(r'\s+(Telephone \(primary\)\s+:)(?P<value>.*)$', re.IGNORECASE)
#    Telephone2 = re.compile(r'\s+(Telephone \(secondary\)\s+:)(?P<value>.*)$', re.IGNORECASE)
    Fax = re.compile(r'\s+(Fax\s+:)(?P<value>.*)$', re.IGNORECASE)
    Email = re.compile(r'\s+(E-mail\s+:)(?P<value>.*)$', re.IGNORECASE)
    Secondary = re.compile(r'\s+Secondary Contact.*$', re.IGNORECASE)

    Notes = re.compile(r'\s+(Additional Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    TextExtra = re.compile(r'(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    TextAddition = re.compile(r'(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "agency-" + str(sequence)
        self.contactAgency = geo.agencyPropertyType(id=text)

        self.done = False
        self.previous = None

        self.primary = True
        self.ignore = True
        self.store = False

        self.notes = [""]
        self.sequence = sequence

        self.agency =[""]
        self.address =[""]
        self.name =[""]
        self.telephone =[""]
        self.fax =[""]
        self.email =[""]

    def setPrimary(self, flag):
        self.primary = flag

    def parse(self, text, line):
        ok = re.match(type(self).Name, text)
        if ok:
            if self.ignore and self.store:
                if assignText(SiteLog.SecondaryName, type(self).Name, text, line):
                    pass
            else:
                if assignText(self.name, type(self).Name, text, line):
                    pass
            self.previous = None 
            return

        ok = re.match(type(self).Telephone, text)
        if ok:
            if self.ignore and self.store:
                if assignText(SiteLog.SecondaryTelephone, type(self).Telephone, text, line):
                    pass
            else:
                if assignText(self.telephone, type(self).Telephone, text, line):
                    pass
            self.previous = None 
            return

        ok = re.match(type(self).Fax, text)
        if ok:
            if self.ignore and self.store:
                if assignText(SiteLog.SecondaryFax, type(self).Fax, text, line):
                    pass
            else:
                if assignText(self.fax, type(self).Fax, text, line):
                    pass
            self.previous = None 
            return

        ok = re.match(type(self).Email, text)
        if ok:
            if self.ignore and self.store:
                if assignText(SiteLog.SecondaryEmail, type(self).Email, text, line):
                    pass
            else:
                if assignText(self.email, type(self).Email, text, line):
                    pass
            self.previous = None 
            return

        if assignText(self.address, type(self).Address, text, line):
            self.previous = self.address
            return

        if assignText(self.agency, type(self).Agency, text, line):
            self.previous = self.agency
            return

        ok = re.match(type(self).Primary, text)
        if ok:
            self.store = False
            if self.primary:
                self.ignore = False
            else:
                self.ignore = True
            self.previous = None 
            return

        ok = re.match(type(self).Secondary, text)
        if ok:
            self.store = True
            if self.primary:
                self.ignore = True
            else:
                self.ignore = False
            self.previous = None 
            return

        if assignNotes(self.notes, type(self).Notes, text, line):
            self.previous = self.notes 
            return

        if assignNotes(self.previous, type(self).TextExtra, text, line):
            return

        if assignNotes(self.previous, type(self).TextAddition, text, line):
            return

    def complete(self):
        if not self.done:
            self.done = True

            if isEmpty(self.name[0]) and isEmpty(self.email[0]):
                self.agency[0] = SiteLog.SecondaryAgency
                self.address[0] = SiteLog.SecondaryAddress
                self.name[0] = SiteLog.SecondaryName[0]
                self.telephone[0] = SiteLog.SecondaryTelephone[0]
                self.fax[0] = SiteLog.SecondaryFax[0]
                self.email[0] = SiteLog.SecondaryEmail[0]

            constraints = gmd.MD_SecurityConstraints_Type()
            classification = gmd.MD_ClassificationCode_PropertyType(nilReason="missing")
            code = gmd.MD_ClassificationCode("", codeList="codelist", codeListValue="")
            classification.append(code)
            constraints.append(classification)

            responsibleParty = gmd.CI_ResponsibleParty_Type()
            individualName = gco.CharacterString_PropertyType()
            individualName.append(self.name[0])

            organisationName = gco.CharacterString_PropertyType()
            organisationName.append(self.agency[0])

            positionName = gco.CharacterString_PropertyType()
            positionName.append("")

            contactInfo = gmd.CI_Contact_PropertyType()
            contact = gmd.CI_Contact_Type()

            phoneProperty = gmd.CI_Telephone_PropertyType()
            SiteLog.TelephoneIndex += 1
            telephone = gmd.CI_Telephone_Type(id="telephone-" + str(SiteLog.TelephoneIndex))
            voice = gco.CharacterString_PropertyType()
            voice.append(self.telephone[0])

            telephone = pyxb.BIND(voice)
            phoneProperty.append(telephone)

            facsimile = gco.CharacterString_PropertyType()
            facsimile.append(self.fax[0])
            phoneProperty.CI_Telephone.facsimile.append(facsimile)

            addressProperty = gmd.CI_Address_PropertyType()
            SiteLog.AddressIndex += 1 
            address = gmd.CI_Address_Type(id="address-" + str(SiteLog.AddressIndex))

            deliveryPoint = gco.CharacterString_PropertyType()
            deliveryPoint.append(self.address[0])

            address = pyxb.BIND(deliveryPoint)
            addressProperty.append(address)

            electronicMailAddress = gco.CharacterString_PropertyType()
            electronicMailAddress.append(self.email[0])

            pattern = re.compile(r'(?P<city>\w+)([,]?\s*)(\w{2,3})([,]?\s*)(?P<code>\d{4})([,]?\s*)AUSTRALIA', re.MULTILINE | re.IGNORECASE)
            ok = re.search(pattern, self.address[0])
            if ok:
                city = gco.CharacterString_PropertyType()
                city.append(ok.group('city'))

                country = gco.CharacterString_PropertyType()
                country.append("Australia")

                postalCode = gco.CharacterString_PropertyType()
                postalCode.append(ok.group('code'))
            else:
                city = gco.CharacterString_PropertyType()
                city.append("")

                country = gco.CharacterString_PropertyType()
                country.append("")

                postalCode = gco.CharacterString_PropertyType()
                postalCode.append("")

            addressProperty.CI_Address.city = city
            addressProperty.CI_Address.postalCode = postalCode
            addressProperty.CI_Address.country = country
            addressProperty.CI_Address.electronicMailAddress.append(electronicMailAddress)

            contact = pyxb.BIND(phoneProperty, addressProperty)
            contactInfo.append(contact)

            role = gmd.CI_RoleCode_PropertyType()
            roleCode = gmd.CI_RoleCode("", codeList="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode", codeListValue="pointOfContact")
            role.append(roleCode)

            responsibleParty = pyxb.BIND(individualName, organisationName, contactInfo, role)

            self.contactAgency.append(constraints)
            self.contactAgency.append(responsibleParty)

            if self.agency[0] and self.address[0]:
                SiteLog.SecondaryAgency = self.agency[0]
                SiteLog.SecondaryAddress = self.address[0]

        return self.contactAgency


################################################################################
class SiteLog(object):
    TimePeriodIndex = 0
    TimeInstantIndex = 0
    TelephoneIndex = 0
    AddressIndex = 0

    ReceiverVersion = 0
    AntennaVersion = 0
    HumidityVersion = 0
    PressureVersion = 0
    TemperatureVersion = 0
    WaterVaporVersion = 0
    FrequencyVersion = 0

    CountryCode = ""

    SecondaryAgency = ""
    SecondaryAddess = ""
    SecondaryName = [""]
    SecondaryTelephone = [""]
    SecondaryFax = [""]
    SecondaryEmail = [""]

    @classmethod
    def Reset(cls):
        cls.TimePeriodIndex = 0
        cls.TimeInstantIndex = 0
        cls.TelephoneIndex = 0
        cls.AddressIndex = 0

        cls.ReceiverVersion = 0
        cls.AntennaVersion = 0
        cls.HumidityVersion = 0
        cls.PressureVersion = 0
        cls.TemperatureVersion = 0
        cls.WaterVaporVersion = 0
        cls.FrequencyVersion = 0

        cls.CountryCode = ""

        SecondaryAgency = ""
        SecondaryAddess = ""
        SecondaryName = [""]
        SecondaryTelephone = [""]
        SecondaryFax = [""]
        SecondaryEmail = [""]



    Template1 = re.compile(r'^\d+\.x')
    Template2 = re.compile(r'^\d+\.\d+\.x')

    Form = re.compile(r'^0\.\s+Form')
    Identification = re.compile(r'^1\.\s+Site Identification of the ((GNSS)|(GPS)) Monument')
    Location = re.compile(r'^2\.\s+Site Location Information')

    ReceiverInfo = re.compile(r'^3\.\s+((GNSS)|(GPS)) Receiver Information')
    ReceiverType = re.compile(r'^3\.(?P<version>\d+)\s*Receiver Type            :')

    AntennaInfo = re.compile(r'^4\.\s+((GNSS)|(GPS)) Antenna Information')
    AntennaType = re.compile(r'^4\.(?P<version>\d+)\s*Antenna Type             :')

    SurveyedLocalTies = re.compile(r'^5\.\s+Surveyed Local Ties')
    TiedMarker = re.compile(r'^5\.\d+\s*Tied Marker Name         :')

    FrequencyStandard = re.compile(r'^6\.\s+Frequency Standard')
    StandardType = re.compile(r'^6\.(?P<version>\d+)\s*Standard Type            :')

    CollocationInfo = re.compile(r'^7\.\s+Collocation Information')
    InstrumentationType = re.compile(r'^7\.\d+\s*Instrumentation Type     :')

    Meteorological = re.compile(r'^8\.\s+Meteorological Instrumentation')

    Humidity = re.compile(r'^8\.1\.(?P<version>\d+)\s*Humidity Sensor Model  :')
    Pressure = re.compile(r'^8\.2\.(?P<version>\d+)\s*Pressure Sensor Model  :')
    Temperature = re.compile(r'^8\.3\.(?P<version>\d+)\s*Temp. Sensor Model     :')
    WaterVapor = re.compile(r'^8\.4\.(?P<version>\d+)\s*Water Vapor Radiometer :')
    OtherInstrumentation = re.compile(r'^8\.5\.(\d+)\s*Other Instrumentation  :')

    OngoingConditions = re.compile(r'^9\.\s+Local Ongoing Conditions Possibly Affecting Computed Position')
    Radio = re.compile(r'^9\.1\.\d+\s*Radio Interferences    :')
    Multipath = re.compile(r'^9\.2\.\d+\s*Multipath Sources      :')
    Signal = re.compile(r'^9\.3\.\d+\s*Signal Obstructions    :')

    Episodic = re.compile(r'^10\.\s+Local Episodic Effects Possibly Affecting Data Quality')
    Event = re.compile(r'^10\.\d+\s*Date                     :')

    PointOfContact = re.compile(r'^11\.\s+On-Site, Point of Contact Agency Information')
    ResponsibleAgency = re.compile(r'^12\.\s+Responsible Agency')
    MoreInformation = re.compile(r'^13\.\s+More Information')

    EmptyReceiver = re.compile(r'((Receiver Type\s+:\s*$)|(from rcvr_ant\.tab)|(see instructions))', re.IGNORECASE)
    EmptyAntenna = re.compile(r'((Antenna Type\s+:\s*$)|(from rcvr_ant\.tab)|(see instructions))', re.IGNORECASE)
    EmptyTiedMarker = re.compile(r'Tied Marker Name\s+:\s*$', re.IGNORECASE)
    EmptyFrequency = re.compile(r'((Standard Type\s+:\s*$)|(INTERNAL or EXTERNAL H-MASER\/CESIUM\/etc))', re.IGNORECASE)
    EmptyCollocation = re.compile(r'((Instrumentation Type\s+:\s*$)|(GPS\/GLONASS\/DORIS\/PRARE\/SLR\/VLBI\/TIME\/etc))', re.IGNORECASE)

    EmptyHumidity = re.compile(r'Humidity Sensor Model\s+:\s*$', re.IGNORECASE)
    EmptyPressure = re.compile(r'Pressure Sensor Model\s+:\s*$', re.IGNORECASE)
    EmptyTemperature = re.compile(r'Temp. Sensor Model\s+:\s*$', re.IGNORECASE)
    EmptyWaterVapor = re.compile(r'Water Vapor Radiometer\s+:\s*$', re.IGNORECASE)
    EmptyOtherInstrumentation = re.compile(r'((Other Instrumentation\s+:\s*$)|(multiple lines))', re.IGNORECASE)

    EmptyRadio = re.compile(r'((Radio Interferences\s+:\s*$)|(TV\/CELL PHONE ANTENNA\/RADAR\/etc))', re.IGNORECASE)
    EmptyMultipath = re.compile(r'((Multipath Sources\s+:\s*$)|(METAL ROOF\/DOME\/VLBI ANTENNA\/etc))', re.IGNORECASE)
    EmptySignal = re.compile(r'((Signal Obstructions\s+:\s*$)|(TREES\/BUILDINGS\/etc))', re.IGNORECASE)

    EmptyEvent = re.compile(r'((Date\s+:\s*$)|(CCYY-MM-DD\/CCYY-MM-DD))', re.IGNORECASE)

    def __init__(self, filename):
        self.filename = filename
        self.siteLog = geo.SiteLogType(id=os.path.basename(filename))

    def parse(self):

        with codecs.open(self.filename, 'r', encoding="iso-8859-15") as infile:
            data = infile.read()
        infile.close()

        textLines = data.splitlines()

        SiteLog.Update(textLines)

        flag = -8
        section = None

        lineNo = 0

        for line in textLines:
            lineNo += 1
#            print(line)

            if isEmpty(line):
                continue

            line = line.encode('ascii', 'xmlcharrefreplace')

            if re.match(type(self).Template1, line):
                flag = -2
                continue
            elif re.match(type(self).Template2, line):
                flag = -4
                continue
            elif re.match(type(self).Form, line):
                flag = 0
                FormInformation.Begin()
                section = FormInformation.Current
                continue
            elif re.match(type(self).Identification, line):
                self.siteLog.formInformation = FormInformation.Detach()

                SiteIdentification.Begin()
                section = SiteIdentification.Current
                flag = 1
                continue
            elif re.match(type(self).Location, line):
                self.siteLog.siteIdentification = SiteIdentification.Detach()

                SiteLocation.Begin()
                section = SiteLocation.Current
                flag = 2
                continue
            elif re.match(type(self).ReceiverInfo, line):
                self.siteLog.siteLocation = SiteLocation.Detach()

                flag = 3
                continue
            elif re.match(type(self).ReceiverType, line):
                GNSSReceiver.Append(self.siteLog.gnssReceivers)

                if re.match(type(self).EmptyReceiver, line):
                    flag = -2
                    continue
                else:
                    flag = 3
                    GNSSReceiver.Begin()
                    section = GNSSReceiver.Current

            elif re.match(type(self).AntennaInfo, line):
                GNSSReceiver.Append(self.siteLog.gnssReceivers)

                flag = 4
                continue
            elif re.match(type(self).AntennaType, line):
                GNSSAntenna.Append(self.siteLog.gnssAntennas)

                if re.match(type(self).EmptyAntenna, line):
                    flag = -2
                    continue
                else:
                    flag = 4
                    GNSSAntenna.Begin()
                    section = GNSSAntenna.Current

            elif re.match(type(self).SurveyedLocalTies, line):
                GNSSAntenna.Append(self.siteLog.gnssAntennas)

                flag = 5
                continue
            elif re.match(type(self).TiedMarker, line):
                LocalTie.Append(self.siteLog.surveyedLocalTies)

                if re.match(type(self).EmptyTiedMarker, line):
                    flag = -2
                    continue
                else:
                    flag = 5
                    LocalTie.Begin()
                    section = LocalTie.Current
            elif re.match(type(self).FrequencyStandard, line):
                LocalTie.Append(self.siteLog.surveyedLocalTies)

                flag = 6
                continue
            elif re.match(type(self).StandardType, line):
                FrequencyStandard.Append(self.siteLog.frequencyStandards)

                if re.match(type(self).EmptyFrequency, line):
                    flag = -2
                    continue
                else:
                    flag = 6
                    FrequencyStandard.Begin()
                    section = FrequencyStandard.Current
            elif re.match(type(self).CollocationInfo, line):
                FrequencyStandard.Append(self.siteLog.frequencyStandards)

                flag = 7
                continue
            elif re.match(type(self).InstrumentationType, line):
                CollocationInformation.Append(self.siteLog.collocationInformations)

                if re.match(type(self).EmptyCollocation, line):
                    flag = -2
                    continue
                else:
                    flag = 7
                    CollocationInformation.Begin()
                    section = CollocationInformation.Current
            elif re.match(type(self).Meteorological, line):
                CollocationInformation.Append(self.siteLog.collocationInformations)

                flag = 8
                continue
            elif re.match(type(self).Humidity, line):
                HumiditySensor.End(self.siteLog.humiditySensors)
                if re.match(type(self).EmptyHumidity, line):
                    flag = -2
                    continue
                else:
                    flag = 81
                    HumiditySensor.Begin()
                    section = HumiditySensor.Current
            elif re.match(type(self).Pressure, line):
                HumiditySensor.End(self.siteLog.humiditySensors)
                PressureSensor.End(self.siteLog.pressureSensors)
                if re.match(type(self).EmptyPressure, line):
                    flag = -2
                    continue
                else:
                    flag = 82
                    PressureSensor.Begin()
                    section = PressureSensor.Current
            elif re.match(type(self).Temperature, line):
                PressureSensor.End(self.siteLog.pressureSensors)
                TemperatureSensor.End(self.siteLog.temperatureSensors)
                if re.match(type(self).EmptyTemperature, line):
                    flag = -2
                    continue
                else:
                    flag = 83
                    TemperatureSensor.Begin()
                    section = TemperatureSensor.Current
            elif re.match(type(self).WaterVapor, line):
                TemperatureSensor.End(self.siteLog.temperatureSensors)
                flag = -84
# not implemented yet
                continue
            elif re.match(type(self).OtherInstrumentation, line):
                flag = -85
# not implemented yet
                continue
            elif re.match(type(self).OngoingConditions, line):
# Temporariely put here, in case very old log file format
# will move it later
                TemperatureSensor.End(self.siteLog.temperatureSensors)
                flag = -9
# not implemented yet
                continue
            elif re.match(type(self).Radio, line):
# not implemented yet
                flag = -91
                continue
            elif re.match(type(self).Multipath, line):
# not implemented yet
                flag = -92
                continue
            elif re.match(type(self).Signal, line):
# not implemented yet
                flag = -93
                continue
            elif re.match(type(self).Episodic, line):
                flag = 10
                continue
            elif re.match(type(self).Event, line):
                EpisodicEvent.End(self.siteLog.localEpisodicEventsSet)
                if re.match(type(self).EmptyEvent, line):
                    flag = -2
                    continue
                else:
                    flag = 10
                    EpisodicEvent.Begin()
                    section = EpisodicEvent.Current
            elif re.match(type(self).PointOfContact, line):
                EpisodicEvent.End(self.siteLog.localEpisodicEventsSet)
                flag = 11
                ContactAgency.Begin()
                section = ContactAgency.Current
                section.setPrimary(True)
                continue
            elif re.match(type(self).ResponsibleAgency, line):
                ContactAgency.Append(self.siteLog.siteContact)
                flag = 12
                ContactAgency.Begin()
                section = ContactAgency.Current
                section.setPrimary(False)
                continue
            elif re.match(type(self).MoreInformation, line):
                self.siteLog.siteMetadataCustodian = ContactAgency.Detach()

                flag = 13
                MoreInformation.Begin()
                section = MoreInformation.Current
                continue

            if flag >= 0:
                section.parse(line, lineNo)
                continue

        self.siteLog.moreInformation = MoreInformation.Detach()

        return

    def complete(self):
        return self.siteLog

    @classmethod
    def ExtractReceiverVersion(cls, text):
        ok = re.match(cls.ReceiverType, text)
        if ok:
            version = int(ok.group('version').strip())
            if not re.match(cls.EmptyReceiver, text):
                if version > cls.ReceiverVersion:
                    cls.ReceiverVersion = version
            return True
        else:
            return False


    @classmethod
    def ExtractAntennaVersion(cls, text):
        ok = re.match(cls.AntennaType, text)
        if ok:
            version = int(ok.group('version').strip())
            if not re.match(cls.EmptyAntenna, text):
                if version > cls.AntennaVersion:
                    cls.AntennaVersion = version
            return True
        else:
            return False


    @classmethod
    def ExtractHumidityVersion(cls, text):
        ok = re.match(cls.Humidity, text)
        if ok:
            version = int(ok.group('version').strip())
            if not re.match(cls.EmptyHumidity, text):
                if version > cls.HumidityVersion:
                    cls.HumidityVersion = version
            return True
        else:
            return False


    @classmethod
    def ExtractPressureVersion(cls, text):
        ok = re.match(cls.Pressure, text)
        if ok:
            version = int(ok.group('version').strip())
            if not re.match(cls.EmptyPressure, text):
                if version > cls.PressureVersion:
                    cls.PressureVersion = version
            return True
        else:
            return False


    @classmethod
    def ExtractTemperatureVersion(cls, text):
        ok = re.match(cls.Temperature, text)
        if ok:
            version = int(ok.group('version').strip())
            if not re.match(cls.EmptyTemperature, text):
                if version > cls.TemperatureVersion:
                    cls.TemperatureVersion = version
            return True
        else:
            return False


    @classmethod
    def ExtractFrequencyVersion(cls, text):
        ok = re.match(cls.StandardType, text)
        if ok:
            version = int(ok.group('version').strip())
            if not re.match(cls.EmptyFrequency, text):
                if version > cls.FrequencyVersion:
                    cls.FrequencyVersion = version
            return True
        else:
            return False


    @classmethod
    def Update(cls, textLines):
        for line in textLines:
            if isEmpty(line):
                continue
            elif cls.ExtractReceiverVersion(line):
                continue
            elif cls.ExtractAntennaVersion(line):
                continue
            elif cls.ExtractHumidityVersion(line):
                continue
            elif cls.ExtractPressureVersion(line):
                continue
            elif cls.ExtractTemperatureVersion(line):
                continue
            elif cls.ExtractFrequencyVersion(line):
                continue


################################################################################
def main():
    args = options()

    CountryCode = args.code
    SiteLogFile = args.sitelog
    XML = args.xml

    setup()

    siteLog = SiteLog(SiteLogFile)
    SiteLog.CountryCode = CountryCode
    siteLog.parse()
    element = siteLog.complete()
###    contents = element.toDOM(element_name="geo:siteLog").toprettyxml(indent='    ', encoding='utf-8')

    gml = geo.GeodesyMLType(id="geodesy")
# id will be replaced by 11 character id
    gml.append(element) 

    contents = gml.toDOM(element_name="geo:GeodesyML").toprettyxml(indent='    ', encoding='utf-8')

    if XML:
        open(XML, 'w').write(contents)
    else:
        sys.stdout.write(contents)


################################################################################
if __name__ == "__main__":

    main()

