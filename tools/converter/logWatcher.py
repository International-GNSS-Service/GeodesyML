import os
import re
import argparse
import logging
import logging.config
import requests

import pyinotify
import log2xml

from multiprocessing import Process


################################################################################
class Shared(object):

    Proxy = ""
    LogFolder = ""
    URL = ""
    Verbose = ""
    Logger = None

    @classmethod
    def Settings(cls, args):
        """Global Settings from arguments"""

        cls.Proxy = args.proxy
        cls.LogFolder = args.logFolder
        cls.URL = args.url
        cls.Verbose = args.verbose

        if args.config:
            cls.Logger = logging.getLogger('logWatcher')
            logging.config.fileConfig(args.config)
        else:
            logging.Logger.disabled = True


################################################################################
def options():
    """Design the arguments"""

    options = argparse.ArgumentParser(prog='logWatcher',
            description="Watch for new or updated site log files for eGeodesy database")

    options.add_argument('--version', action='version',
            version='%(prog)s 1.0, Copyright (c) 2016 by Geodesy, Geoscience Australia')

    options.add_argument('-d', '--logFolder',
            default='/nas/gemd/geodesy_data/gnss/logs',
            help='The directory, where site log files to be watched, reside')

    options.add_argument("-l", "--url",
            metavar='https://testgeodesy-webservices.geodesy.ga.gov.au/siteLogs/upload',
            required=True,
            help='The address for eGeodesy web services to upload XML files')

    options.add_argument("-x", "--proxy",
            metavar='http://proxy.inno.lan:3128',
            help='Proxy for http(s) connections')

    options.add_argument("-g", "--config",
            type=argparse.FileType('r'),
            metavar='logging.conf',
            default='logging.conf',
            help='Configuration file for logging (defaul: %(default)s)')

    options.add_argument("-v", "--verbose", help="log verbose information to file",
            action="store_true")

    return options.parse_args()


################################################################################
def doPost(xmlfile, url): 
    """Post XML file to eGeodesy database through web services"""

    session = requests.Session()
    session.proxies = {"http": Shared.Proxy, "https": Shared.Proxy}

    try:
        headers = {'content-type': 'application/xml'}

        with open(xmlfile, 'rb') as block:
            response = session.post(url, data=block, headers=headers)
            response.raise_for_status()
            Shared.Logger.info("%s added into Database", xmlfile)

    except requests.exceptions.Timeout as e:
        Shared.Logger.error("Session timeout: " + e)
    except requests.exceptions.URLRequired as e:
        Shared.Logger.error("URL is required: " + e)
    except requests.exceptions.TooManyRedirects as e:
        Shared.Logger.error("Too may redirects: " + e)
    except requests.exceptions.HTTPError as err:
        Shared.Logger.error("HTTP error: " + str(err))
    except requests.exceptions.ConnectionError as err:
        Shared.Logger.error("Connection error: " + str(err))
    except requests.exceptions.ProxyError as err:
        Shared.Logger.error("Proxy error: " + str(err))
    except requests.exceptions.SSLError as err:
        Shared.Logger.error("SSL error: " + str(err))
    except requests.exceptions.RequestException as e:
        Shared.Logger.error("Exception: " + e)


################################################################################
def doConvert(logfile):
    """Convert site log to XML and post XML to eGeodesy database"""

    directory, nameOnly = os.path.split(logfile)
    pattern = re.compile(r'^(?P<name>\w{4})_\d{8}\.log$', re.IGNORECASE)

    ok = re.match(pattern, nameOnly)
    if ok:
        fourLetters = ok.group('name').upper()
        xmlfile = os.path.join(directory, "gml", fourLetters + ".xml")

        try:
            log2xml.convert(logfile, xmlfile)
            fileSize = os.stat(xmlfile)
            if fileSize > 1000:
                doPost(xmlfile, Shared.URL)
            else:
                Shared.Logger.error("Failed to convert %s to XML", logfile)
        except: 
            Shared.Logger.error("Failed to process %s for %s", logfile, Shared.URL)


################################################################################
class EventHandler(pyinotify.ProcessEvent):
    """Event handling"""

    def process_IN_ACCESS(self, event):
        print "ACCESS event:", event.pathname

    def process_IN_ATTRIB(self, event):
        print "ATTRIB event:", event.pathname

    def process_IN_CLOSE_NOWRITE(self, event):
        print "CLOSE_NOWRITE event:", event.pathname

    def process_IN_CLOSE_WRITE(self, event):
        p = Process(target=doConvert, args=(event.pathname,))
        p.start()
        p.join()

    def process_IN_CREATE(self, event):
        print "CREATE event:", event.pathname

    def process_IN_DELETE(self, event):
        print "DELETE event:", event.pathname

    def process_IN_MODIFY(self, event):
        print "MODIFY event:", event.pathname

    def process_IN_OPEN(self, event):
        print "OPEN event:", event.pathname


################################################################################
def main():
    """Start event watching and event handling"""

    args = options()

    Shared.Settings(args)

    # watch manager
    watchManager = pyinotify.WatchManager()
    watchManager.add_watch(Shared.LogFolder, pyinotify.IN_CLOSE_WRITE, rec=False)

    # event handler
    handler = EventHandler()

    # notifier
    notifier = pyinotify.Notifier(watchManager, handler)
    notifier.loop()


################################################################################
if __name__ == '__main__':
    main()

