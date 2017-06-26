"""
Module: Geo Logger 
"""

import logging
import logging.config

################################################################################
class GeoLogger(object):
    Logger = None
    ConfigFile = "geoLogger.conf"
    LoggingName = "geoLogger"

    @classmethod
    def setup(cls, configFile = None, loggingName = None):
        theConfigFile = cls.ConfigFile if configFile is None else configFile
        theLoggingName = cls.LoggingName if loggingName is None else loggingName
        logging.config.fileConfig(theConfigFile)
        if cls.Logger is None:
            cls.Logger = logging.getLogger(theLoggingName)

