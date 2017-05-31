import os
import re
import time
import argparse
import logging
import logging.config
import json
import requests
from multiprocessing import Process

from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

import sensors
import parser

import log2xml


################################################################################
class Shared(object):

    Proxy = ""
    LogFolder = ""
    URL = ""
    Verbose = ""
    Logger = None

    OpenAM = ""

    Manager = ""
    Id = ""

    Username = ""
    password = ""

    @classmethod
    def Settings(cls, args):
        """Global Settings from arguments"""

        cls.Proxy = args.proxy
        cls.LogFolder = args.logFolder
        cls.URL = args.url
        cls.Verbose = args.verbose

        cls.OpenAM = args.openam

        cls.Manager = args.manager
        cls.Id = args.identifier

        cls.Username = args.user
        cls.Password = args.password

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
            metavar='/nas/gemd/geodesy_data/gnss/logs',
            help='The directory, where site log files to be watched, reside')

    options.add_argument('-e', '--openam',
            default='https://prodgeodesy-openam.geodesy.ga.gov.au/openam/oauth2/access_token?realm=/',
            metavar='https://prodgeodesy-openam.geodesy.ga.gov.au/openam/oauth2/access_token?realm=/',
            help='OpenAM address')

    options.add_argument('-m', '--manager',
            default='GnssSiteManager',
            metavar='GnssSiteManager',
            help='Site manager')

    options.add_argument('-w', '--identifier',
            default='G2dioga12',
            metavar='G2dioga12',
            help='The password for site manager')

    options.add_argument('-u', '--user',
            required=True,
            help='username')

    options.add_argument("-p", "--password",
            required=True,
            help='The password for specific user')

    options.add_argument("-l", "--url",
            default='https://gws.geodesy.ga.gov.au/siteLogs/upload',
            metavar='https://gws.geodesy.ga.gov.au/siteLogs/upload',
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
        response = requests.post(Shared.OpenAM, 
                                 auth = (Shared.Manager, Shared.Id), 
                                 data = {'grant_type':'password', 
                                         'username':Shared.Username, 
                                         'password':Shared.Password, 
                                         'scope':'openid profile'}) 
        response.raise_for_status()
        token = json.loads(response.content)['id_token']
 
        headers = {'content-type': 'application/xml', 'Authorization':'Bearer ' + token}

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
    except:
        Shared.Logger.error("Failed with posting XML file")



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
class EventHandler(FileSystemEventHandler):
    """Fvent handling"""

    def on_moved(self, event):
        # Users not expected to do so
        return

    def on_created(self, event):
        self.handle(event)

    def on_modified(self, event):
        self.handle(event)

    def handle(self, event):
        # event handling
        if event.is_directory:
            return

        if not os.path.exists(event.src_path):
            return

        if os.path.getsize(event.src_path) < 1000:
            # reasonable site log file size
            return

        p = Process(target=doConvert, args=(event.src_path,))
        p.start()
        # enough to convert to XML and connect to remote end
        p.join(300)

        return


################################################################################
def main():
    """Start event watching and event handling"""

    args = options()

    Shared.Settings(args)

    observer = Observer()
    observer.schedule(EventHandler(), path = Shared.LogFolder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


################################################################################
if __name__ == '__main__':
    main()

