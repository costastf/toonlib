# -*- coding: utf-8 -*-
"""toonlib package"""
from ._version import __version__
from .toonlibexceptions import (InvalidCredentials,
                                UnableToGetSession,
                                IncompleteResponse,
                                InvalidThermostatState)
from .configuration import (STATES,
                            STATE_CACHING_SECONDS,
                            DEFAULT_STATE,
                            AUTHENTICATION_ERROR_STRINGS)
from .helpers import (ThermostatState,
                      Client,
                      PersonalDetails,
                      Agreement,
                      SmokeDetector,
                      PowerUsage,
                      Solar,
                      Usage,
                      ThermostatInfo,
                      Light,
                      SmartPlug,
                      Data)
from .toonlib import Toon

__author__ = '''Costas Tyfoxylos'''
__email__ = '''costas.tyf@gmail.com'''

# This is to 'use' the module(s), so lint doesn't complain
assert __version__

# assert the exceptions
assert InvalidCredentials
assert UnableToGetSession
assert IncompleteResponse
assert InvalidThermostatState

# assert the objects
assert Toon
assert ThermostatState
assert Client
assert PersonalDetails
assert Agreement
assert SmokeDetector
assert PowerUsage
assert Solar
assert Usage
assert ThermostatInfo
assert Light
assert SmartPlug
assert Data

# assert configurations
assert STATES
assert STATE_CACHING_SECONDS
assert DEFAULT_STATE
assert AUTHENTICATION_ERROR_STRINGS
