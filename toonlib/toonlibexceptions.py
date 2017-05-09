#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# File: toonlibexceptions.py
#
"""
Main module Exceptions file

Put your exception classes here
"""

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = 'plaintext'
__date__ = '''13-03-2017'''


class InvalidCredentials(Exception):
    """The username and password combination was not accepted as valid"""


class UnableToGetSession(Exception):
    """Could not refresh session"""


class IncompleteResponse(Exception):
    """Vital information is missing from the response"""


class InvalidThermostatState(Exception):
    """Vital information is missing from the response"""
