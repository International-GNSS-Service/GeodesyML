"""
Module: Geo wrapper
"""

import math

################################################################################
def is_equal(first_float, second_float, epsilon = 0.0000000001):
    return True if math.abs(first_float - second_float) < epsilon else False


