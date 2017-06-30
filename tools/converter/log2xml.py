# -*- coding: latin-1 -*-
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

import sensors
import parser

import iso3166


################################################################################
logger = logging.getLogger('log2xml')


################################################################################
def setup():
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
            default='',
            metavar='AUS',
            help='Country Code, three characters, using ISO alpha-3 if unspecified')

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

    options.add_argument("-v", "--verbose", help="log verbose information to file",
                    action="store_true")

    return options.parse_args()


################################################################################
def isEmpty(line):
    text = line.strip()
    return not text


################################################################################
def toLatitude(value, line):
    text = str(value)
    pattern = re.compile(r'[+-]?(\d{2})(\d{2})((\d{2})(\.\d*)?)')
    ok = re.match(pattern, text)
    if ok:
        degree = float(ok.group(1))
        minute = float(ok.group(2))
        second = float(ok.group(3))
        number = degree + minute / 60.0 + second / 3600.0
        if float(value) < 0.0:
            text = "-" + str(number)
        else:
            text = "+" + str(number)
        return float(text)
    else:
        parser.errorMessage(line, text, "A latude value in format '[+-]ddmmss.s' (d:degree, m:minute, s:second) is expected")
        return 0.0


################################################################################
def toLongitude(value, line):
    text = str(value)
    pattern = re.compile(r'[+-]?(\d{3})(\d{2})((\d{2})(\.\d*)?)')
    ok = re.match(pattern, text)
    if ok:
        degree = float(int(ok.group(1)))
        minute = float(ok.group(2))
        second = float(ok.group(3))
        number = degree + minute / 60.0 + second / 3600.0
        if float(value) < 0.0:
            text = "-" + str(number)
        else:
            text = "+" + str(number)
        return float(text)
    else:
        parser.errorMessage(line, text, "A longitude value in format '[+-]dddmmss.s' (d:degree, m:minute, s:second) is expected")
        return 0.0


def countryFullname(name):
    CountryFullnames = {}
    CountryFullnames['ASCENSION ISLAND'] = "Saint Helena, Ascension and Tristan da Cunha"
    CountryFullnames['BRUNEI'] = "Brunei Darussalam"
    CountryFullnames['IRAN'] = "Iran, Islamic Republic of"
    CountryFullnames['ISLAMIC REPUBLIC OF IRAN'] = "Iran, Islamic Republic of"
    CountryFullnames['KOREA'] = "Korea, Republic of"
    CountryFullnames['KYRGHYZSTAN'] = "Kyrgyzstan"
    CountryFullnames['MICRONESIA'] = "Micronesia, Federated States of"
    CountryFullnames['FEDERATED STATES OF MICRONESIA'] = "Micronesia, Federated States of"
    CountryFullnames['NEGARA BRUNEI DARUSSALAM'] = "Brunei Darussalam"
    CountryFullnames['RUSSIA'] = "Russian Federation"
    CountryFullnames['REPUBLIC OF ARMENIA'] = "Armenia"
    CountryFullnames['REPUBLIC OF CAPE VERDE'] = "Cabo Verde"
    CountryFullnames['REPUBLIC OF CHINA'] = "China"
    CountryFullnames['REPUBLIC OF MALDIVES'] = "Maldives"
    CountryFullnames['REPUBLIC OF KOREA'] = "Korea, Republic of"
    CountryFullnames['SOUTH KOREA'] = "Korea, Republic of"
    CountryFullnames['KOREA'] = "Korea, Republic of"
    CountryFullnames['P.R.C.'] = "China"
    CountryFullnames['P.R. CHINA'] = "China"
    CountryFullnames['TAHITI'] = "French Polynesia"
    CountryFullnames['VIETNAM'] = "Viet Nam"
    CountryFullnames['DEPENDENT TERRITORY OF THE U.K.'] = "Saint Helena, Ascension and Tristan da Cunha"

    index = name.upper()
    if CountryFullnames.has_key(index):
        return CountryFullnames[index]
    else:
        return None
 
################################################################################
def parseCountryCodeType(target, field, pattern, text, line,
        space="urn:xml-gov-au:icsm:egeodesy:0.4",
        theCodeList="http://xml.gov.au/icsm/geodesyml/codelists/country-codes-codelist.xml#GeodesyML_CountryCode"):
    ok = re.match(pattern, text)
    if ok:
        country = ok.group('value').strip()

        # set the three letter code if not specified on the command line
        SiteLog.Country = country
        countryCode = SiteLog.CountryCode
        if not countryCode:
            fullname = countryFullname(country)
            if not fullname:
                fullname = country
            tuples = iso3166.countries.get(fullname)
            if tuples:
                code = tuples.alpha3
                if code and len(code) == 3:
                    countryCode = code
                    SiteLog.CountryCode = code
                else:
                    errorMessage(line, country, "No matching ISO 3166 alpha3 code")
            else:
                errorMessage(line, country, "Country name not matching ISO 3166")

        code = geo.countryCodeType(SiteLog.CountryCode, codeSpace=space, codeList=theCodeList, codeListValue=country)
        setattr(target, field, code)

        return True
    else:
        return False


################################################################################
def parseSatelliteSystem(target, field, pattern, text, line, space):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        allItems = value.split('+')
        for item in allItems:
            code = gml.CodeType(item, codeSpace=space)
            target.satelliteSystem.append(code)
        return True
    else:
        return False


################################################################################
def parseDataCenter(target, pattern, text, line):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        target.dataCenter.append(value)
        return True
    else:
        return False

################################################################################
def assignString(variable, pattern, text, line, isPrimary):
    ok = re.match(pattern, text)
    if ok:
        value = ok.group('value').strip()
        if isPrimary:
            variable[0] = value
        else:
            variable[1] = value
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


    PreparedBy = re.compile(r'^\s+(Prepared\s+by\s+\(full\s+name\)\s*:)(?P<value>.*)$', re.IGNORECASE)
    DatePrepared = re.compile(r'^\s+(Date\s+Prepared\s+:)(?P<value>.*)$', re.IGNORECASE)
    ReportType = re.compile(r'^\s+(Report\s+Type\s+:)(?P<value>.*)$', re.IGNORECASE)

    def __init__(self):
        self.formInformation = geo.formInformationType()

    def parse(self, text, line):
        if parser.parseText(self.formInformation, type(self).PreparedBy, text, line):
            return

        if parser.parseDateTime(self.formInformation, type(self).DatePrepared, text, line):
            return

        if parser.parseText(self.formInformation, type(self).ReportType, text, line):
            return

    def complete(self):
        return self.formInformation


################################################################################
class EpisodicEvent(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, eventSet):
        if cls.Current:
            event = cls.Current.complete()
            extra = geo.localEpisodicEffectPropertyType()
            extra.append(event)
            extra.append(event.validTime.AbstractTimePrimitive.beginPosition)
            eventSet.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = EpisodicEvent(cls.Index)

    Date = re.compile(r'^10\.\d+\s*(Date\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)
    Event = re.compile(r'^\s+(Event\s+:)(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "episodic-effect-" + str(sequence)
        self.episodicEffect = geo.localEpisodicEffectType(id=text)
        self.sequence = sequence

    def parse(self, text, line):
        if parser.parseTimePeriod(self.episodicEffect, type(self).Date, text, line, SiteLog, True):
            return

        if parser.parseText(self.episodicEffect, type(self).Event, text, line):
            return

    def complete(self):
        return self.episodicEffect


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

    Instrumentation = re.compile(r'^7\.\d+\s*(Instrumentation Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    Status = re.compile(r'^\s+(Status\s+:)(?P<value>.*)$', re.IGNORECASE)
    EffectiveDates = re.compile(r'^\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "instrumentation-type-" + str(sequence)
        self.collocation = geo.CollocationInformationType(id=text)

        self.notes = [""]
        self.notesAppended = False

    def parse(self, text, line):
        if parser.parseCodeType(self.collocation, "instrumentationType", type(self).Instrumentation, text, line, "urn:ga-gov-au:instrumentation-type"):
            return

        if parser.parseCodeType(self.collocation, "status", type(self).Status, text, line, "urn:ga-gov-au:status-type"):
            return

        if parser.setTimePeriodAttribute(self.collocation, "validTime", type(self).EffectiveDates, text, line, SiteLog, False):
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
            self.collocation.notes = self.notes[0]
            self.notesAppended = True
        return self.collocation


################################################################################
class OtherInstrumentation(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, allInstrumentations):
        if cls.Current:
            instrumentation = cls.Current.complete()
            extra = geo.otherInstrumentationPropertyType()
            extra.append(instrumentation)
            extra.dateInserted = gml.TimePositionType()
            allInstrumentations.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = OtherInstrumentation(cls.Index)

    OtherInstrumentation = re.compile(r'^8\.5\.\d+\s*(Other Instrumentation\s*:)(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "other-instrumentation-" + str(sequence)
        self.otherInstrumentation = geo.OtherInstrumentationType(id=text)
        validTime = gml.TimePrimitivePropertyType(nilReason="not applicable")
        setattr(self.otherInstrumentation, "validTime", validTime)
        self.sequence = sequence

    def parse(self, text, line):
        if parser.setTextAttribute(self.otherInstrumentation, "instrumentation", type(self).OtherInstrumentation, text, line):
            return

    def complete(self):
        return self.otherInstrumentation


class FrequencyStandard(object):
    Current = None
    Index = 0

    @classmethod
    def Append(cls, frequencyStandards):
        if cls.Current:
            standard = cls.Current.complete()
            wrapper = geo.frequencyStandardPropertyType()
            wrapper.append(standard)
            wrapper.dateInserted = standard.validTime.AbstractTimePrimitive.beginPosition
            frequencyStandards.append(wrapper)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = FrequencyStandard(cls.Index)


    StandardType = re.compile(r'^6\.(?P<version>\d+)\s*(Standard\s+Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    InputFrequency = re.compile(r'^\s+(Input Frequency\s+:)(?P<value>.*)$', re.IGNORECASE)
    EffectiveDates = re.compile(r'^\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Notes\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "frequency-standard-" + str(sequence)
        self.frequencyStandard = geo.FrequencyStandardType(id=text)

        self.version = [0]
        self.internal = False
        
        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence

    def parse(self, text, line):

        if parser.parseCodeTypeAndVersion(self.frequencyStandard, "standardType", type(self).StandardType,
                text, line, "urn:ga-gov-au:frequency-standard-type", self.version):
            pattern = re.compile(r'^.*INTERNAL\s*$', re.IGNORECASE)
            ok = re.match(pattern, text)
            if ok:
                self.internal = True
            else:
                self.internal = False
            return

        if parser.setNillableDoubleAttribute(self.frequencyStandard, "inputFrequency", type(self).InputFrequency, text, line, True, not self.internal):
            return

        if parser.setTimePeriodAttribute(self.frequencyStandard, "validTime", type(self).EffectiveDates, text, line, SiteLog, self.version[0] < SiteLog.FrequencyVersion):
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
            self.frequencyStandard.notes = self.notes[0]
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
            wrapper = geo.surveyedLocalTiePropertyType()
            wrapper.append(localTie)
            wrapper.append(localTie.dateMeasured)
            ties.append(wrapper)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = LocalTie(cls.Index)


    Name = re.compile(r'^5\.\d+\s*(Tied\s+Marker\s+Name\s+:)(?P<value>.*)$', re.IGNORECASE)
    Usage = re.compile(r'^\s+(Tied Marker Usage\s+:)(?P<value>.*)$', re.IGNORECASE)
    CDPNumber = re.compile(r'^\s+(Tied Marker CDP Number\s+:)(?P<value>.*)$', re.IGNORECASE)
    DOMESNumber = re.compile(r'^\s+(Tied Marker DOMES Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    DX = re.compile(r'^\s+(dx.*:)(?P<value>.*)$', re.IGNORECASE)
    DY = re.compile(r'^\s+(dy.*:)(?P<value>.*)$', re.IGNORECASE)
    DZ = re.compile(r'^\s+(dz.*:)(?P<value>.*)$', re.IGNORECASE)
    Accuracy = re.compile(r'^\s+(Accuracy.*:\s*[+]?[-]?)(?P<value>.*)$', re.IGNORECASE)

    Method = re.compile(r'^\s+(Survey method\s+:)(?P<value>.*)$', re.IGNORECASE)
    DateMeasured  = re.compile(r'^\s+(Date Measured\s+:)(?P<value>.*)$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "local-tie-" + str(sequence)
        self.localTie = geo.SurveyedLocalTieType(id=text)
        
        self.dx = [geo.NillableDouble()]
        self.dy = [geo.NillableDouble()]
        self.dz = [geo.NillableDouble()]

        self.notes = [""]
        self.notesAppended = False

    def parse(self, text, line):
        if parser.setTextAttribute(self.localTie, "tiedMarkerName", type(self).Name, text, line):
            return

        if parser.setTextAttribute(self.localTie, "tiedMarkerUsage", type(self).Usage, text, line):
            return

        if parser.setTextAttribute(self.localTie, "tiedMarkerCDPNumber", type(self).CDPNumber, text, line):
            return

        if parser.setTextAttribute(self.localTie, "tiedMarkerDOMESNumber", type(self).DOMESNumber, text, line):
            return

        if parser.assignNillableDouble(self.dx, type(self).DX, text, line):
            return

        if parser.assignNillableDouble(self.dy, type(self).DY, text, line):
            return

        if parser.assignNillableDouble(self.dz, type(self).DZ, text, line):
            return

        if parser.setDoubleAttribute(self.localTie, "localSiteTiesAccuracy", type(self).Accuracy, text, line, True, True):
            return

        if parser.setTextAttribute(self.localTie, "surveyMethod", type(self).Method, text, line):
            return

        if parser.setDateTimeAttribute(self.localTie, "dateMeasured", type(self).DateMeasured, text, line):
            return

        if parser.assignNotes(self.notes, type(self).Notes, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):

        differentialComponents = geo.differentialComponentsGNSSMarkerToTiedMonumentITRS()
        setattr(differentialComponents, "dx", self.dx[0])
        setattr(differentialComponents, "dy", self.dy[0])
        setattr(differentialComponents, "dz", self.dz[0])

        setattr(self.localTie, "differentialComponentsGNSSMarkerToTiedMonumentITRS", differentialComponents)

        if not self.notesAppended:
            self.notes[0] = parser.processingNotes(self.notes[0])
            self.localTie.notes = self.notes[0]
            self.notesAppended = True
        return self.localTie


################################################################################
class RadioInterference(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, sources):
        if cls.Current:
            radioInterference = cls.Current.complete()
            extra = geo.radioInterferencePropertyType()
            extra.append(radioInterference)
            extra.append(radioInterference.validTime.AbstractTimePrimitive.beginPosition)
            sources.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = RadioInterference(cls.Index)

    Radio = re.compile(r'^9\.1\.(?P<version>\d+)\s*(Radio Interferences\s+:)(?P<value>.*)$', re.IGNORECASE)
    Degradations = re.compile(r'^\s+(Observed Degr[a|e]dations\s+:)(?P<value>.*)$', re.IGNORECASE)
    EffectiveDates = re.compile(r'^\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Additional Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "radio-interference-" + str(sequence)
        self.radioInterference = geo.radioInterferenceType(id=text)
        super(RadioInterference, self).__init__()
        self.notes = [""]
        self.notesAppended = False
        self.sequence = sequence

    def parse(self, text, line):

        # TODO can't setattr on the parent's field ??
        if parser.parseText(self.radioInterference, type(self).Radio, text, line):
            return
        
        if parser.parseTimePeriod(self.radioInterference, type(self).EffectiveDates, text, line, SiteLog, False):
            return

        if parser.setTextAttribute(self.radioInterference, "observedDegradation", type(self).Degradations, text, line):
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
            self.radioInterference.notes = self.notes[0]
            self.notesAppended = True
        return self.radioInterference


################################################################################
class MultipathSource(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, sources):
        if cls.Current:
            multipath = cls.Current.complete()
            extra = geo.multipathSourcePropertyType()
            extra.append(multipath)
            extra.append(multipath.validTime.AbstractTimePrimitive.beginPosition)
            sources.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = MultipathSource(cls.Index)

    Multipath = re.compile(r'^9\.2\.(?P<version>\d+)\s*(Multipath Sources\s+:)(?P<value>.*)$', re.IGNORECASE)
    EffectiveDates = re.compile(r'^\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Additional Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "multipath-" + str(sequence)

        self.multipathSource = geo.multipathSourceType(id=text)

        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence

    def parse(self, text, line):

        if parser.parseText(self.multipathSource, type(self).Multipath, text, line):
            return

        if parser.parseTimePeriod(self.multipathSource, type(self).EffectiveDates, text, line, SiteLog, False):
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
            self.multipathSource.notes = self.notes[0]
            self.notesAppended = True
        return self.multipathSource


################################################################################
class SignalObstruction(object):
    Current = None
    Index = 0

    @classmethod
    def End(cls, sources):
        if cls.Current:
            signal = cls.Current.complete()
            extra = geo.signalObstructionPropertyType()
            extra.append(signal)
            extra.append(signal.validTime.AbstractTimePrimitive.beginPosition)
            sources.append(extra)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = SignalObstruction(cls.Index)

    Signal = re.compile(r'^9\.3\.(?P<version>\d+)\s*(Signal Obstructions\s+:)(?P<value>.*)$', re.IGNORECASE)
    EffectiveDates = re.compile(r'^\s+(Effective Dates\s+:)(((?P<begin>.*)\/(?P<end>.*))|(\s*)|((?P<start>.*)[\/]?))$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Additional Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "signal-obstruction-" + str(sequence)

        self.signalObstruction = geo.signalObstructionType(id=text)

        self.notes = [""]
        self.notesAppended = False

        self.sequence = sequence

    def parse(self, text, line):

        if parser.parseText(self.signalObstruction, type(self).Signal, text, line):
            return

        if parser.parseTimePeriod(self.signalObstruction, type(self).EffectiveDates, text, line, SiteLog, False):
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
            self.signalObstruction.notes = self.notes[0]
            self.notesAppended = True
        return self.signalObstruction


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


    City = re.compile(r'^\s+(City or Town\s+:)(?P<value>.*)$', re.IGNORECASE)
    State = re.compile(r'^\s+(State or Province\s+:)(?P<value>.*)$', re.IGNORECASE)
    Tectonic = re.compile(r'^\s+(Tectonic Plate\s+:)(?P<value>.*)$', re.IGNORECASE)
    Country = re.compile(r'^\s+(Country\s+:)(?P<value>.*)$', re.IGNORECASE)
    XCoordinate = re.compile(r'^\s+(X coordinate.*:)(?P<value>.*)$', re.IGNORECASE)
    YCoordinate = re.compile(r'^\s+(Y coordinate.*:)(?P<value>.*)$', re.IGNORECASE)
    ZCoordinate = re.compile(r'^\s+(Z coordinate.*:)(?P<value>.*)$', re.IGNORECASE)
    Latitude = re.compile(r'^\s+(Latitude.*:)(?P<value>.*)$', re.IGNORECASE)
    Longitude = re.compile(r'^\s+(Longitude.*:)(?P<value>.*)$', re.IGNORECASE)
    Elevation = re.compile(r'^\s+(Elevation.*:)(?P<value>.*)$', re.IGNORECASE)
    Notes = re.compile(r'^\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self):
        self.siteLocation = geo.siteLocationType()
        self.notes = [""]
        self.notesAppended = False
        self.x = [0.0]
        self.y = [0.0]
        self.z = [0.0]
        self.lat = [0.0]
        self.lng = [0.0]
        self.ele = [0.0]

    def parse(self, text, line):
        if parser.setTextAttribute(self.siteLocation, "city", type(self).City, text, line):
            return

        if parser.setTextAttribute(self.siteLocation, "state", type(self).State, text, line):
            return

        if parseCountryCodeType(self.siteLocation, "countryCodeISO", type(self).Country, text, line):                    
            return        
        
        if parser.parseCodeType(self.siteLocation, "tectonicPlate", type(self).Tectonic, text, line, "urn:ga-gov-au:plate-type"):
            return

        if parser.assignDouble(self.x, type(self).XCoordinate, text, line, True):
            return

        if parser.assignDouble(self.y, type(self).YCoordinate, text, line, True):
            return

        if parser.assignDouble(self.z, type(self).ZCoordinate, text, line, True):
            return

        if parser.assignText(self.lat, type(self).Latitude, text, line):
            self.lat[0] = toLatitude(self.lat[0], line)
            return

        if parser.assignText(self.lng, type(self).Longitude, text, line):
            self.lng[0] = toLongitude(self.lng[0], line)
            return

        if parser.assignDouble(self.ele, type(self).Elevation, text, line, True):
            return

        if parser.assignNotes(self.notes, type(self).Notes, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesExtra, text, line):
            return

        if parser.assignNotes(self.notes, type(self).NotesAddition, text, line):
            return

    def complete(self):
        
        self.siteLocation.approximatePositionITRF = geo.ApproximatePositionITRF()
        
        cartesianPositionPoint = gml.Point(id="itrf_cartesian")
        directPositionType = gml.DirectPositionType([self.x[0], self.y[0], self.z[0]])      
        cartesianPositionPoint.srsName = "EPSG:7789"
        cartesianPositionPoint.pos = directPositionType;
        cartesianPosition = geo.cartesianPosition()
        cartesianPosition.append(cartesianPositionPoint)
        
        self.siteLocation.approximatePositionITRF.append(cartesianPosition);
                
        geodeticPositionPoint = gml.Point(id="itrf_geodetic")
        directPositionType = gml.DirectPositionType([self.lat[0], self.lng[0], self.ele[0]])
        geodeticPositionPoint.srsName = "EPSG:7912" 
        geodeticPositionPoint.pos = directPositionType;
        geodeticPosition = geo.geodeticPosition()
        geodeticPosition.append(geodeticPositionPoint)
        
        self.siteLocation.approximatePositionITRF.append(geodeticPosition);
                                              
        if not self.notesAppended:
            self.notes[0] = parser.processingNotes(self.notes[0])
            self.siteLocation.notes = self.notes[0]            
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
            wrapper.dateInserted = gnssReceiver.dateInstalled
            receivers.append(wrapper)
            cls.Current = None

    @classmethod
    def Begin(cls):
        cls.Index += 1
        cls.Current = GNSSReceiver(cls.Index)

    ReceiverType = re.compile(r'^3\.(?P<version>\d+)\s*(Receiver\s+Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    SatelliteSystem = re.compile(r'^\s+(Satellite System\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber  = re.compile(r'^\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)
    FirmwareVersion  = re.compile(r'^\s+(Firmware Version\s+:)(?P<value>.*)$', re.IGNORECASE)
    Cutoff = re.compile(r'^\s+(Elevation Cutoff Setting\s*:)(?P<value>.*)$', re.IGNORECASE)
    DateInstalled  = re.compile(r'^\s+(Date Installed\s+:)(?P<value>.*)$', re.IGNORECASE)
    DateRemoved  = re.compile(r'^\s+(Date Removed\s+:)(?P<value>.*)$', re.IGNORECASE)
    Stabilizer = re.compile(r'^\s+(Temperature Stabiliz\.\s+:)(?P<value>.*)$', re.IGNORECASE)
    Notes = re.compile(r'^\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "gnss-receiver-" + str(sequence)
        self.gnssReceiver = geo.GnssReceiverType(id=text)
        self.notes = [""]
        self.notesAppended = False
        self.version = [0]

    def parse(self, text, line):
        if parser.parseReceiverModelCodeType(self.gnssReceiver, type(self).ReceiverType, text, line, self.version):
            return

        if parseSatelliteSystem(self.gnssReceiver, "satelliteSystem", type(self).SatelliteSystem, text, line, "urn:ga-gov-au:satellite-system-type"):
            return

        if parser.setTextAttribute(self.gnssReceiver, "manufacturerSerialNumber", type(self).SerialNumber, text, line):
            return

        if parser.setTextAttribute(self.gnssReceiver, 'firmwareVersion', type(self).FirmwareVersion, text, line):
            return

        if parser.setNillableDoubleAttribute(self.gnssReceiver, "elevationCutoffSetting", type(self).Cutoff, text, line, True, True):
            return
        
        if parser.setDateTimeAttribute(self.gnssReceiver, "dateInstalled", type(self).DateInstalled, text, line):
            return

        if parser.setDateTimeAttribute(self.gnssReceiver, "dateRemoved", type(self).DateRemoved, text, line, self.version[0] < SiteLog.ReceiverVersion):
            return

        if parser.setNillableDoubleAttribute(self.gnssReceiver, "temperatureStabilization", type(self).Stabilizer, text, line, True, False):
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
                self.gnssReceiver.notes = self.notes[0]
                self.notesAppended = True
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


    AntennaType = re.compile(r'^4\.(?P<version>\d+)\s*(Antenna\s+Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    SerialNumber  = re.compile(r'^\s+(Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    ReferencePoint = re.compile(r'^\s+(Antenna Reference Point\s+:)(?P<value>.*)$', re.IGNORECASE)
    
    Up = re.compile(r'^.*(ARP\s+Up.*:)(?P<value>.*)$', re.IGNORECASE)
    North = re.compile(r'^.*(ARP North.*:)(?P<value>.*)$', re.IGNORECASE)
    East = re.compile(r'^.*(ARP East.*:)(?P<value>.*)$', re.IGNORECASE)

    Alignment = re.compile(r'^\s+(Alignment from True N\s+:)(?P<value>.*)$', re.IGNORECASE)
    RadomeType = re.compile(r'^\s+(Antenna Radome Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    RadomeSerialNumber = re.compile(r'^\s+(Radome Serial Number\s+:)(?P<value>.*)$', re.IGNORECASE)

    CableType = re.compile(r'^\s+(Antenna Cable Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    CableLength = re.compile(r'^\s+(Antenna Cable Length.*:)(?P<value>.*)$', re.IGNORECASE)

    DateInstalled  = re.compile(r'^\s+(Date Installed\s+:)(?P<value>.*)$', re.IGNORECASE)
    DateRemoved  = re.compile(r'^\s+(Date Removed\s+:)(?P<value>.*)$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "gnss-antenna-" + str(sequence)
        self.gnssAntenna = geo.GnssAntennaType(id=text)      
        self.notes = [""]
        self.notesAppended = False
        self.version = [0]

    def parse(self, text, line):
        if parser.parseAntennaModelCodeType(self.gnssAntenna, type(self).AntennaType, text, line, self.version):
            return

        if parser.setTextAttribute(self.gnssAntenna, "manufacturerSerialNumber", type(self).SerialNumber, text, line):
            return

        if parser.parseCodeType(self.gnssAntenna, "antennaReferencePoint", type(self).ReferencePoint, text, line,
                "urn:ga-gov-au:antenna-reference-point-type"):
            return

        if parser.setNillableDoubleAttribute(self.gnssAntenna, "marker_arpUpEcc", type(self).Up, text, line, True, True):
            return
        
        if parser.setNillableDoubleAttribute(self.gnssAntenna, "marker_arpNorthEcc", type(self).North, text, line, True, True):
            return

        if parser.setNillableDoubleAttribute(self.gnssAntenna, "marker_arpEastEcc", type(self).East, text, line, True, True):
            return
        
        if parser.setNillableDoubleAttribute(self.gnssAntenna, "alignmentFromTrueNorth", type(self).Alignment, text, line, True, False):
            return

        if parser.parseRadomeModelCodeType(self.gnssAntenna, type(self).RadomeType, text, line):
            return

        if parser.setTextAttribute(self.gnssAntenna, "radomeSerialNumber", type(self).RadomeSerialNumber, text, line):
            return

        if parser.setTextAttribute(self.gnssAntenna, "antennaCableType", type(self).CableType, text, line):
            return

        if parser.setNillableDoubleAttribute(self.gnssAntenna, "antennaCableLength", type(self).CableLength, text, line, True):
            return
        
        if parser.setDateTimeAttribute(self.gnssAntenna, "dateInstalled", type(self).DateInstalled, text, line):
            return

        if parser.setDateTimeAttribute(self.gnssAntenna, "dateRemoved", type(self).DateRemoved, text, line, self.version[0] < SiteLog.AntennaVersion):
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
                self.gnssAntenna.notes = self.notes[0]
                self.notesAppended = True
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
    FourCharacterID = re.compile(r'^\s+(Four\s+Character\s+ID\s+:)(?P<value>.*)$', re.IGNORECASE)
    MonumentInscription = re.compile(r'^\s+(Monument\s+Inscription\s+:)(?P<value>.*)$', re.IGNORECASE)
    IersDOMESNumber = re.compile(r'^\s+(((IERS)|(APREF))\s+DOMES\s+Number\s+:)(?P<value>.*)$', re.IGNORECASE)
    CdpNumber = re.compile(r'^\s+(CDP\s+Number\s+:)(?P<value>.*)$', re.IGNORECASE)
    MonumentDescription = re.compile(r'^\s+(Monument\s+Description\s+:)(?P<value>.*)$', re.IGNORECASE)
    HeightOfTheMonument = re.compile(r'^\s+(Height\s+of\s+The\s+Monument\s+:)(?P<value>.*)$', re.IGNORECASE)
    MonumentFoundation = re.compile(r'^\s+(Monument\s+Foundation\s+:)(?P<value>.*)$', re.IGNORECASE)
    FoundationDepth = re.compile(r'^\s+(Foundation\s+Depth\s+:)(?P<value>.*)$', re.IGNORECASE)
    MarkerDescription = re.compile(r'^\s+(Marker\s+Description\s+:)(?P<value>.*)$', re.IGNORECASE)
    DateInstalled = re.compile(r'^\s+(Date\s+Installed\s+:)(?P<value>.*)$', re.IGNORECASE)
    GeologicCharacteristic = re.compile(r'^\s+(Geologic\s+Characteristic\s+:)(?P<value>.*)$', re.IGNORECASE)
    BedrockType = re.compile(r'^\s+(Bedrock\s+Type\s+:)(?P<value>.*)$', re.IGNORECASE)
    BedrockCondition = re.compile(r'^\s+(Bedrock\s+Condition\s+:)(?P<value>.*)$', re.IGNORECASE)
    FractureSpacing = re.compile(r'^\s+(Fracture\s+Spacing\s+:)(?P<value>.*)$', re.IGNORECASE)
    FaultZonesNearby = re.compile(r'^\s+(Fault\s+zones\s+nearby\s+:)(?P<value>.*)$', re.IGNORECASE)
    Distance_Activity = re.compile(r'^\s+(Distance\/activity\s+:)(?P<value>.*)$', re.IGNORECASE)
    Notes = re.compile(r'^\s+(Additional\s+Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self):
        self.siteIdentification = geo.siteIdentificationType()
        self.notes = [""]
        self.notesAppended = False

    def parse(self, text, line):
        if parser.setTextAttribute(self.siteIdentification, "siteName", type(self).SiteName, text, line):
            return

        if parser.setTextAttribute(self.siteIdentification, "fourCharacterID", type(self).FourCharacterID, text, line):
            return

        if parser.setTextAttribute(self.siteIdentification, "monumentInscription", type(self).MonumentInscription, text, line):
            return

        if parser.setTextAttribute(self.siteIdentification, "iersDOMESNumber", type(self).IersDOMESNumber, text, line):
            return

        if parser.setTextAttribute(self.siteIdentification, "cdpNumber", type(self).CdpNumber, text, line):
            return

        if parser.parseCodeType(self.siteIdentification, "monumentDescription", type(self).MonumentDescription,
                text, line, "urn:ga-gov-au:monument-description-type"):
            return

        if parser.setDoubleAttribute(self.siteIdentification, "heightOfTheMonument", type(self).HeightOfTheMonument, text, line, True, False):
            return

        if parser.setTextAttribute(self.siteIdentification, "monumentFoundation", type(self).MonumentFoundation, text, line):
            return

        if parser.setDoubleAttribute(self.siteIdentification, "foundationDepth", type(self).FoundationDepth, text, line, True, False):
            return

        if parser.setTextAttribute(self.siteIdentification, "markerDescription", type(self).MarkerDescription, text, line):
            return

        if parser.setDateTimeAttribute(self.siteIdentification, "dateInstalled", type(self).DateInstalled, text, line):
            return

        if parser.parseCodeType(self.siteIdentification, "geologicCharacteristic", type(self).GeologicCharacteristic,
                text, line, "urn:ga-gov-au:geologic-characteristic-type"):
            return

        if parser.setTextAttribute(self.siteIdentification, "bedrockType", type(self).BedrockType, text, line):
            return

        if parser.setTextAttribute(self.siteIdentification, "bedrockCondition", type(self).BedrockCondition, text, line):
            return

        if parser.setTextAttribute(self.siteIdentification, "fractureSpacing", type(self).FractureSpacing, text, line):
            return

        if parser.parseCodeType(self.siteIdentification, "faultZonesNearby", type(self).FaultZonesNearby,
                text, line, "urn:ga-gov-au:fault-zones-type"):
            return

        if parser.setTextAttribute(self.siteIdentification, "distance-Activity", type(self).Distance_Activity, text, line):
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
            self.siteIdentification.notes = self.notes[0]        
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

    PrimaryDataCenter = re.compile(r'^\s+(Primary Data Center\s+:)(?P<value>.*)$', re.IGNORECASE)
    SecondaryDataCenter = re.compile(r'^\s+(Secondary Data Center\s+:)(?P<value>.*)$', re.IGNORECASE)
    URL = re.compile(r'^\s+(URL for More Information\s*:)(?P<value>.*)$', re.IGNORECASE)
    SiteMap = re.compile(r'^\s+(Site Map\s+:)(?P<value>.*)$', re.IGNORECASE)
    SiteDiagram = re.compile(r'^\s+(Site Diagram\s+:)(?P<value>.*)$', re.IGNORECASE)
    HorizonMask = re.compile(r'^\s+(Horizon Mask\s+:)(?P<value>.*)$', re.IGNORECASE)
    MonumentDescription = re.compile(r'^\s+(Monument Description\s+:)(?P<value>.*)$', re.IGNORECASE)
    SitePictures = re.compile(r'^\s+(Site Pictures\s+:)(?P<value>.*)$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Additional Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    NotesExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    NotesAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    StopLine = re.compile(r'Antenna Graphics with Dimensions', re.IGNORECASE)

    def __init__(self, sequence):
        text = "more-information-" + str(sequence)
        self.moreInformation = geo.moreInformationType()

        self.done = False

        self.url = [""]

        self.notes = [""]
        self.sequence = sequence

        self.last = False
        self.stop = False

    def parse(self, text, line):
        if self.stop:
            return

        if parser.assignText(self.url, type(self).URL, text, line):
            return

        if parser.setTextAttribute(self.moreInformation, "siteMap", type(self).SiteMap, text, line):
            return

        if parser.setTextAttribute(self.moreInformation, "siteDiagram", type(self).SiteDiagram, text, line):
            return

        if parser.setTextAttribute(self.moreInformation, "horizonMask", type(self).HorizonMask, text, line):
            return

        if parser.setTextAttribute(self.moreInformation, "monumentDescription", type(self).MonumentDescription, text, line):
            return

        if parser.setTextAttribute(self.moreInformation, "sitePictures", type(self).SitePictures, text, line):
            return

        if parseDataCenter(self.moreInformation, type(self).PrimaryDataCenter, text, line):
            return

        if parseDataCenter(self.moreInformation, type(self).SecondaryDataCenter, text, line):
            return

        if parser.assignNotes(self.notes, type(self).Notes, text, line):
            self.last = True
            return

        if parser.assignNotes(self.notes, type(self).NotesExtra, text, line):
            self.last = True
            return

        if parser.assignNotes(self.notes, type(self).NotesAddition, text, line):
            self.last = True
            return

        ok = re.match(type(self).StopLine, text)
        if ok:
            self.stop = True
        elif self.last:
            self.stop = True


    def complete(self):
        if not self.done:
            self.done = True

            try:
# Actually prefer to revert back old copy log2xml in the future if possible
                if not len(self.moreInformation.dataCenter):
                    self.moreInformation.dataCenter.append("")
                    self.moreInformation.dataCenter.append("")
            except:
                pass

####            self.moreInformation.dataCenter.append(self.primaryDataCenter[0])
####            self.moreInformation.dataCenter.append(self.secondaryDataCenter[0])
            setattr(self.moreInformation, "antennaGraphicsWithDimensions", "")
            setattr(self.moreInformation, "insertTextGraphicFromAntenna", "")
            self.moreInformation.urlForMoreInformation = self.url[0]
            self.moreInformation.DOI = gml.CodeType("TODO", codeSpace="urn:ga-gov-au:self.moreInformation-type")
            self.notes[0] = parser.processingNotes(self.notes[0])
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
            agency =  cls.Current.second()
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

    Agency = re.compile(r'^\s+(Agency\s+:)(?P<value>.*)$', re.IGNORECASE)
    Address = re.compile(r'^\s+(Mailing Address\s+:)(?P<value>.*)$', re.IGNORECASE)
    Primary = re.compile(r'^\s+Primary Contact.*$', re.IGNORECASE)
    Name = re.compile(r'^\s+(Contact Name\s+:)(?P<value>.*)$', re.IGNORECASE)
    Telephone = re.compile(r'^\s+(Telephone \(primary\)\s+:)(?P<value>.*)$', re.IGNORECASE)
    Telephone2 = re.compile(r'\s+(Telephone \(secondary\)\s+:)(?P<value>.*)$', re.IGNORECASE)
    Fax = re.compile(r'^\s+(Fax\s+:)(?P<value>.*)$', re.IGNORECASE)
    Email = re.compile(r'^\s+(E-mail\s+:)(?P<value>.*)$', re.IGNORECASE)
    Secondary = re.compile(r'^\s+Secondary Contact.*$', re.IGNORECASE)

    Notes = re.compile(r'^\s+(Additional Information\s+:)(?P<value>.*)$', re.IGNORECASE)
    TextExtra = re.compile(r'^(\s{30}:)(?P<value>.*)$', re.IGNORECASE)
    TextAddition = re.compile(r'^(\s{31,})(?P<value>.*)$', re.IGNORECASE)

    def __init__(self, sequence):
        text = "agency-" + str(sequence)
        self.contactAgency = geo.agencyPropertyType(id=text)

        self.isPrimary = True
        self.isList = False

        self.done = False
        self.secondary = False

        self.previous = None

####        self.primary = True
####        self.ignore = True
####        self.store = False

        self.notes = [""]
        self.sequence = sequence

        self.agency =["", ""]
        self.address =["", ""]
        self.name =["", ""]
        self.telephone =["", ""]
        self.telephone2 =["", ""]
        self.fax =["", ""]
        self.email =["", ""]

    def setAsList(self, flag):
        self.isList = flag
        if self.isList:
            type(self).Index += 1
            sequence = type(self).Index
            text = "agency-" + str(sequence)
            self.secondAgency = geo.agencyPropertyType(id=text)

    def parse(self, text, line):
        ok = re.match(type(self).Name, text)
        if ok:
            if assignString(self.name, type(self).Name, text, line, self.isPrimary):
                pass
            return

        ok = re.match(type(self).Telephone, text)
        if ok:
            if assignString(self.telephone, type(self).Telephone, text, line, self.isPrimary):
                pass
            return

        ok = re.match(type(self).Telephone2, text)
        if ok:
            if assignString(self.telephone2, type(self).Telephone2, text, line, self.isPrimary):
                pass
            return

        ok = re.match(type(self).Fax, text)
        if ok:
            if assignString(self.fax, type(self).Fax, text, line, self.isPrimary):
                pass
            return

        ok = re.match(type(self).Email, text)
        if ok:
            if assignString(self.email, type(self).Email, text, line, self.isPrimary):
                pass
            return

        if parser.assignText(self.address, type(self).Address, text, line):
            return

        if parser.assignText(self.agency, type(self).Agency, text, line):
            return

        ok = re.match(type(self).Primary, text)
        if ok:
            self.isPrimary = True
            return

        ok = re.match(type(self).Secondary, text)
        if ok:
            self.isPrimary = False
            return

        if parser.assignNotes(self.notes, type(self).Notes, text, line):
            self.previous = self.notes
            return

        if parser.assignNotes(self.previous, type(self).TextExtra, text, line):
            return

        if parser.assignNotes(self.previous, type(self).TextAddition, text, line):
            return

    def complete(self):
        if not self.done:
            self.done = True

            constraints = gmd.MD_SecurityConstraints_Type()
            classification = gmd.MD_ClassificationCode_PropertyType(nilReason="missing")
###            code = gmd.MD_ClassificationCode("", codeList="codelist", codeListValue="")
###            classification.append(code)
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

            voice2 = gco.CharacterString_PropertyType()
            voice2.append(self.telephone2[0])

            telephone = pyxb.BIND(voice, voice2)
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

            pattern = re.compile(r'(?P<city>[a-zA-Z]+)([,]?\s+)(\w{2,3})([,]?\s+)(?P<code>\d{4})([,]?\s+)AUSTRALIA', 
                    re.MULTILINE | re.IGNORECASE)
            ok = re.search(pattern, self.address[0])
            if ok:
                city = gco.CharacterString_PropertyType()

                special = re.compile(r'Alice Springs', re.MULTILINE | re.IGNORECASE)
                found = re.search(special, self.address[0])
                if found:
                    city.append('Alice Springs')
                else:
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

        return self.contactAgency

    def second(self):
        if not self.secondary:
            self.secondary = True

            constraints = gmd.MD_SecurityConstraints_Type()
            classification = gmd.MD_ClassificationCode_PropertyType(nilReason="missing")
###            code = gmd.MD_ClassificationCode("", codeList="codelist", codeListValue="")
###            classification.append(code)
            constraints.append(classification)

            responsibleParty = gmd.CI_ResponsibleParty_Type()
            individualName = gco.CharacterString_PropertyType()
            individualName.append(self.name[1])

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
            voice.append(self.telephone[1])

            voice2 = gco.CharacterString_PropertyType()
            voice2.append(self.telephone2[0])

            telephone = pyxb.BIND(voice, voice2)
            phoneProperty.append(telephone)

            facsimile = gco.CharacterString_PropertyType()
            facsimile.append(self.fax[1])
            phoneProperty.CI_Telephone.facsimile.append(facsimile)

            addressProperty = gmd.CI_Address_PropertyType()
            SiteLog.AddressIndex += 1
            address = gmd.CI_Address_Type(id="address-" + str(SiteLog.AddressIndex))

            deliveryPoint = gco.CharacterString_PropertyType()
            deliveryPoint.append(self.address[0])

            address = pyxb.BIND(deliveryPoint)
            addressProperty.append(address)

            electronicMailAddress = gco.CharacterString_PropertyType()
            electronicMailAddress.append(self.email[1])

            pattern = re.compile(r'(?P<city>[a-zA-Z]+)([,]?\s+)(\w{2,3})([,]?\s+)(?P<code>\d{4})([,]?\s+)AUSTRALIA', re.MULTILINE | re.IGNORECASE)
            ok = re.search(pattern, self.address[0])
            if ok:
                city = gco.CharacterString_PropertyType()

                special = re.compile(r'Alice Springs', re.MULTILINE | re.IGNORECASE)
                found = re.search(special, self.address[0])
                if found:
                    city.append('Alice Springs')
                else:
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

            self.secondAgency.append(constraints)
            self.secondAgency.append(responsibleParty)

        return self.secondAgency



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
    FourLetters = ""

    SecondaryAgency = ""
    SecondaryAddress = ""
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
    ReceiverType = re.compile(r'^3\.(?P<version>\d+)\s*Receiver Type.*:')

    AntennaInfo = re.compile(r'^4\.\s+((GNSS)|(GPS)) Antenna Information')
    AntennaType = re.compile(r'^4\.(?P<version>\d+)\s*Antenna Type.*:')

    SurveyedLocalTies = re.compile(r'^5\.\s+Surveyed Local Ties')
    TiedMarker = re.compile(r'^5\.\d+\s*Tied Marker Name.*:')

    FrequencyStandard = re.compile(r'^6\.\s+Frequency Standard')
    StandardType = re.compile(r'^6\.(?P<version>\d+)\s*Standard Type.*:')

    CollocationInfo = re.compile(r'^7\.\s+Collocation Information')
    InstrumentationType = re.compile(r'^7\.\d+\s*Instrumentation Type.*:')

    Meteorological = re.compile(r'^8\.\s+Meteorological Instrumentation')

    Humidity = re.compile(r'^8\.1\.(?P<version>\d+)\s*Humidity Sensor Model.*:')
    Pressure = re.compile(r'^8\.2\.(?P<version>\d+)\s*Pressure Sensor Model.*:')
    Temperature = re.compile(r'^8\.3\.(?P<version>\d+)\s*Temp. Sensor Model.*:')
    WaterVapor = re.compile(r'^8\.4\.(?P<version>\d+)\s*Water Vapor Radiometer.*:')
    OtherInstrumentation = re.compile(r'^8\.5\.(\d+)\s*Other Instrumentation.*:')

    OngoingConditions = re.compile(r'^9\.\s+Local Ongoing Conditions Possibly Affecting Computed Position')
    Radio = re.compile(r'^9\.1\.\d+\s*Radio Interferences.*:')
    Multipath = re.compile(r'^9\.2\.\d+\s*Multipath Sources.*:')
    Signal = re.compile(r'^9\.3\.\d+\s*Signal Obstructions.*:')

    Episodic = re.compile(r'^10\.\s+Local Episodic Effects Possibly Affecting Data Quality')
    Event = re.compile(r'^10\.\d+\s*Date.*:')

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
    EmptySignal = re.compile(r'((Signal Obstructions\s+:\s*$)|(TREES\/BUILD([L]?)INGS\/etc))', re.IGNORECASE)

    EmptyEvent = re.compile(r'((Date\s+:\s*$)|(CCYY-MM-DD\/CCYY-MM-DD))', re.IGNORECASE)

    def __init__(self, filename):
        self.filename = filename
        diretory, nameOnly = os.path.split(filename)
        pattern = re.compile(r'^\d+\w+\_\d{8}\.log$', re.IGNORECASE)
        ok = re.match(pattern, nameOnly)
        if ok:
            nameOnly = "_" + nameOnly
        self.siteLog = geo.SiteLogType(id=nameOnly)


    def readFile(self, coding):
        with codecs.open(self.filename, 'r', encoding=coding) as infile:
            data = infile.read()
        infile.close()
        return data


    def parse(self):
        try:
            data = self.readFile("utf-8")
        except:
            parser.errorMessage("", self.filename, "There are special characters or symbols within site log file")
            try:
                data = self.readFile("iso-8859-1")
            except:
                parser.errorMessage("", self.filename, "Not sure the encoding? Not utf-8 nor iso-8859-1")
                sys.exit()

        textLines = data.splitlines()
        textLines = SiteLog.Preprocess(textLines)

        SiteLog.Update(textLines)

        flag = -8
        section = None

        lineNo = 0

        for line in textLines:
            lineNo += 1
            print(line)

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
                GNSSReceiver.Append(self.siteLog.gnssReceiver)

                if re.search(type(self).EmptyReceiver, line):
                    flag = -2
                    continue
                else:
                    flag = 3
                    GNSSReceiver.Begin()
                    section = GNSSReceiver.Current

            elif re.match(type(self).AntennaInfo, line):
                GNSSReceiver.Append(self.siteLog.gnssReceiver)

                flag = 4
                continue
            elif re.match(type(self).AntennaType, line):
                GNSSAntenna.Append(self.siteLog.gnssAntenna)

                if re.search(type(self).EmptyAntenna, line):
                    flag = -2
                    continue
                else:
                    flag = 4
                    GNSSAntenna.Begin()
                    section = GNSSAntenna.Current

            elif re.match(type(self).SurveyedLocalTies, line):
                GNSSAntenna.Append(self.siteLog.gnssAntenna)

                flag = 5
                continue
            elif re.search(type(self).TiedMarker, line):
                LocalTie.Append(self.siteLog.surveyedLocalTie)

                if re.search(type(self).EmptyTiedMarker, line):
                    flag = -2
                    continue
                else:
                    flag = 5
                    LocalTie.Begin()
                    section = LocalTie.Current
            elif re.match(type(self).FrequencyStandard, line):
                LocalTie.Append(self.siteLog.surveyedLocalTie)

                flag = 6
                continue
            elif re.match(type(self).StandardType, line):
                FrequencyStandard.Append(self.siteLog.frequencyStandard)

                if re.search(type(self).EmptyFrequency, line):
                    flag = -2
                    continue
                else:
                    flag = 6
                    FrequencyStandard.Begin()
                    section = FrequencyStandard.Current
            elif re.match(type(self).CollocationInfo, line):
                FrequencyStandard.Append(self.siteLog.frequencyStandard)

                flag = 7
                continue
            elif re.match(type(self).InstrumentationType, line):
                CollocationInformation.Append(self.siteLog.collocationInformation)

                if re.search(type(self).EmptyCollocation, line):
                    flag = -2
                    continue
                else:
                    flag = 7
                    CollocationInformation.Begin()
                    section = CollocationInformation.Current
            elif re.match(type(self).Meteorological, line):
                CollocationInformation.Append(self.siteLog.collocationInformation)

                flag = 8
                continue
            elif re.match(type(self).Humidity, line):
                sensors.HumiditySensor.End(self.siteLog.humiditySensor)
                if re.search(type(self).EmptyHumidity, line):
                    flag = -2
                    continue
                else:
                    flag = 81
                    sensors.HumiditySensor.Begin()
                    section = sensors.HumiditySensor.Current
            elif re.match(type(self).Pressure, line):
                sensors.HumiditySensor.End(self.siteLog.humiditySensor)
                sensors.PressureSensor.End(self.siteLog.pressureSensor)
                if re.search(type(self).EmptyPressure, line):
                    flag = -2
                    continue
                else:
                    flag = 82
                    sensors.PressureSensor.Begin()
                    section = sensors.PressureSensor.Current
            elif re.match(type(self).Temperature, line):
                sensors.PressureSensor.End(self.siteLog.pressureSensor)
                sensors.TemperatureSensor.End(self.siteLog.temperatureSensor)
                if re.search(type(self).EmptyTemperature, line):
                    flag = -2
                    continue
                else:
                    flag = 83
                    sensors.TemperatureSensor.Begin()
                    section = sensors.TemperatureSensor.Current
            elif re.match(type(self).WaterVapor, line):
                sensors.TemperatureSensor.End(self.siteLog.temperatureSensor)

                sensors.WaterVapor.End(self.siteLog.waterVaporSensor)
                if re.search(type(self).EmptyWaterVapor, line):
                    flag = -2
                    continue
                else:
                    flag = 84
                    sensors.WaterVapor.Begin()
                    section = sensors.WaterVapor.Current
            elif re.match(type(self).OtherInstrumentation, line):
                sensors.WaterVapor.End(self.siteLog.waterVaporSensor)
                OtherInstrumentation.End(self.siteLog.otherInstrumentation)

                if re.search(type(self).EmptyOtherInstrumentation, line):
                    flag = -2
                    continue
                else:
                    flag = 85
                    OtherInstrumentation.Begin()
                    section = OtherInstrumentation.Current
            elif re.match(type(self).OngoingConditions, line):
# Temporariely put here, in case very old log file format
# will move it later
                sensors.HumiditySensor.End(self.siteLog.humiditySensor)
                sensors.PressureSensor.End(self.siteLog.pressureSensor)
                sensors.TemperatureSensor.End(self.siteLog.temperatureSensor)
                sensors.WaterVapor.End(self.siteLog.waterVaporSensor)
                OtherInstrumentation.End(self.siteLog.otherInstrumentation)
                flag = -9
# not implemented yet
                continue
            elif re.match(type(self).Radio, line):
                RadioInterference.End(self.siteLog.radioInterference)
                if re.search(type(self).EmptyRadio, line):
                    flag = -2
                    continue
                else:
                    flag = 91
                    RadioInterference.Begin()
                    section = RadioInterference.Current
            elif re.match(type(self).Multipath, line):
                MultipathSource.End(self.siteLog.multipathSource)
                if re.search(type(self).EmptyMultipath, line):
                    flag = -2
                    continue
                else:
                    flag = 92
                    MultipathSource.Begin()
                    section = MultipathSource.Current
            elif re.match(type(self).Signal, line):
                SignalObstruction.End(self.siteLog.signalObstruction)
                if re.search(type(self).EmptySignal, line):
                    pattern = re.compile(r'BUILDLINGS', re.IGNORECASE)
                    yes = re.search(pattern, line)
                    if yes:
                        parser.errorMessage("", line, "Incorrect spelling as 'BUILDLINGS'")
                    flag = -2
                    continue
                else:
                    flag = 93
                    SignalObstruction.Begin()
                    section = SignalObstruction.Current
            elif re.match(type(self).Episodic, line):
                RadioInterference.End(self.siteLog.radioInterference)
                MultipathSource.End(self.siteLog.multipathSource)
                SignalObstruction.End(self.siteLog.signalObstruction)
                flag = 10
                continue
            elif re.match(type(self).Event, line):
                EpisodicEvent.End(self.siteLog.localEpisodicEffect)
                if re.search(type(self).EmptyEvent, line):
                    flag = -2
                    continue
                else:
                    flag = 10
                    EpisodicEvent.Begin()
                    section = EpisodicEvent.Current
            elif re.match(type(self).PointOfContact, line):
                EpisodicEvent.End(self.siteLog.localEpisodicEffect)
                flag = 11
                ContactAgency.Begin()
                section = ContactAgency.Current
                section.setAsList(True)
                continue
            elif re.match(type(self).ResponsibleAgency, line):
                ContactAgency.Append(self.siteLog.siteContact)
                flag = 12
                ContactAgency.Begin()
                section = ContactAgency.Current
                section.setAsList(False)
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
            if not re.search(cls.EmptyReceiver, text):
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
            if not re.search(cls.EmptyAntenna, text):
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
            if not re.search(cls.EmptyHumidity, text):
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
            if not re.search(cls.EmptyPressure, text):
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
            if not re.search(cls.EmptyTemperature, text):
                if version > cls.TemperatureVersion:
                    cls.TemperatureVersion = version
            return True
        else:
            return False


    @classmethod
    def ExtractWaterVaporVersion(cls, text):
        ok = re.match(cls.WaterVapor, text)
        if ok:
            version = int(ok.group('version').strip())
            if not re.search(cls.EmptyWaterVapor, text):
                if version > cls.WaterVaporVersion:
                    cls.WaterVaporVersion = version
            return True
        else:
            return False

    @classmethod
    def ExtractFrequencyVersion(cls, text):
        ok = re.match(cls.StandardType, text)
        if ok:
            version = int(ok.group('version').strip())
            if not re.search(cls.EmptyFrequency, text):
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
            elif cls.ExtractWaterVaporVersion(line):
                continue
            elif cls.ExtractFrequencyVersion(line):
                continue


    @classmethod
    def Preprocess(cls, textLines):
        MultipleLine = re.compile(r'^\s{30}:{0,1}(?P<value>.*)$', re.IGNORECASE)
        AntennaGraphicsLine = re.compile(r'^\s{0,}Antenna Graphics with Dimensions\s{0,}$', re.IGNORECASE)

        modified = []
        lineNo = 0
        limit = len(textLines)
        done = False

        while lineNo < limit:
            line = textLines[lineNo].rstrip()
            buffered = ""
            pending = lineNo + 1

            if not done:
                done = re.match(AntennaGraphicsLine, line)

            if not done:
                while pending < limit:
                    extra = textLines[pending].rstrip()
                    ok = re.match(MultipleLine, extra)
                    if ok:
                        segment = ok.group('value').strip()
                        buffered += " " + segment
                        pending += 1
                    else:
                        break

            line += buffered
            modified.append(line)
            lineNo = pending

        return modified


def logfile():
    #for batch script
    filename = "./xmlOutput/info/" + SiteLog.FourLetters.lower() + ".info"
    
    #for eclipse
    #filename = "./tools/converter/logs/xmlOutput/info/" + SiteLog.FourLetters.lower() + ".info"
    
    fh = logging.FileHandler(filename)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


################################################################################
def convert(logfile, xmlfile):
    # convert site log file silently
    logging.Logger.disabled = True

    setup()

    diretory, nameOnly = os.path.split(logfile)
    pattern = re.compile(r'^(?P<name>\w{4})_\d{8}\.log$', re.IGNORECASE)
    ok = re.match(pattern, nameOnly)
    if ok:
        SiteLog.FourLetters = ok.group('name').upper()
    else:
        return

    SiteLog.Reset()
    # probably unnecessary

    siteLog = SiteLog(logfile)

    siteLog.parse()
    element = siteLog.complete()

    nineLetters = SiteLog.FourLetters + "00" + SiteLog.CountryCode
    pattern = re.compile(r'^\d\w{8}$', re.IGNORECASE)
    ok = re.match(pattern, nineLetters)
    if ok:
        nineLetters = "_" + nineLetters
    gml = geo.GeodesyMLType(id=nineLetters)
    gml.append(element)

    contents = gml.toDOM(element_name="geo:GeodesyML").toprettyxml(indent='    ', encoding='utf-8')

    if xmlfile:
        open(xmlfile, 'w').write(contents)

    SiteLog.Reset()
    # probably unnecessary


################################################################################
def main():
    args = options()

    CountryCode = args.code
    SiteLogFile = args.sitelog

    logging.config.fileConfig(args.config)
    XML = args.xml

    setup()

    diretory, nameOnly = os.path.split(SiteLogFile)
    pattern = re.compile(r'^(?P<name>\w{4})_\d{8}\.log$', re.IGNORECASE)
    ok = re.match(pattern, nameOnly)
    if ok:
        SiteLog.FourLetters = ok.group('name').upper()
        if args.verbose:
            logfile()
    else:
        parser.errorMessage("", SiteLogFile, "Incorrect site log file naming")
        sys.exit()

    siteLog = SiteLog(SiteLogFile)
    SiteLog.CountryCode = CountryCode

    siteLog.parse()
    element = siteLog.complete()
        
    nineLetters = SiteLog.FourLetters + "00" + SiteLog.CountryCode
    pattern = re.compile(r'^\d\w{8}$', re.IGNORECASE)
    ok = re.match(pattern, nineLetters)
    if ok:
        nineLetters = "_" + nineLetters
    gml = geo.GeodesyMLType(id=nineLetters)
    gml.append(element)
    
    contents = gml.toDOM(element_name="geo:GeodesyML").toprettyxml(indent='    ', encoding='utf-8')
    
    if XML:
        open(XML, 'w').write(contents)
    else:
        sys.stdout.write(contents)


################################################################################
if __name__ == "__main__":

    main()

