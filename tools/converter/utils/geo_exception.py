""" 
Module: Geo defined exceptions
""" 


class GeoException(Exception):
    pass


class FileNotFound(GeoException): 
    pass


class NilValue(GeoException):
    pass


