#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# File: toonlib.py
"""A library overloading the api of the toon mobile app"""

import copy
import logging
import uuid

from requests import Session
from requests.exceptions import Timeout
from cachetools import cached, TTLCache

from .configuration import (STATES,
                            STATE_CACHING_SECONDS,
                            DEFAULT_STATE,
                            AUTHENTICATION_ERROR_STRINGS,
                            REQUEST_TIMEOUT)
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
from .toonlibexceptions import (InvalidCredentials,
                                UnableToGetSession,
                                IncompleteResponse,
                                InvalidThermostatState)

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = 'plaintext'
__date__ = '''13-03-2017'''

# This is the main prefix used for logging
LOGGER_BASENAME = '''toonlib'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())

state_cache = TTLCache(maxsize=1, ttl=STATE_CACHING_SECONDS)


class Toon(object):
    """Model of the toon smart meter from eneco."""

    def __init__(self, username, password, state_retrieval_retry=1):
        logger_name = u'{base}.{suffix}'.format(base=LOGGER_BASENAME,
                                                suffix=self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)
        self._session = Session()
        self.username = username
        self.password = password
        self.base_url = 'https://toonopafstand.eneco.nl/toonMobileBackendWeb'
        self.agreements = None
        self.agreement = None
        self.client = None
        self._state_ = DEFAULT_STATE
        self._state_retries = state_retrieval_retry
        self._uuid = None
        self.data = Data(self)
        self._login()

    def _reset(self):
        self.agreements = None
        self.agreement = None
        self.client = None
        self._state_ = DEFAULT_STATE
        self._uuid = None

    def _authenticate(self):
        """Authenticates to the api and sets up client information."""
        data = {'username': self.username,
                'password': self.password}
        url = '{base}/client/login'.format(base=self.base_url)
        response = self._session.get(url, params=data)
        data = response.json()
        if not data.get('success'):
            raise InvalidCredentials(data.get('reason', None))
        self._populate_info(data)

    def _populate_info(self, data):
        agreements = data.pop('agreements')
        self.agreements = [Agreement(agreement.get('agreementId'),
                                     agreement.get('agreementIdChecksum'),
                                     agreement.get('city'),
                                     agreement.get('displayCommonName'),
                                     agreement.get('displayHardwareVersion'),
                                     agreement.get('displaySoftwareVersion'),
                                     agreement.get('heatingType'),
                                     agreement.get('houseNumber'),
                                     agreement.get('isBoilerManagement'),
                                     agreement.get('isToonSolar'),
                                     agreement.get('isToonly'),
                                     agreement.get('postalCode'),
                                     agreement.get('street'))
                           for agreement in agreements]
        self.agreement = self.agreements[0]
        details = PersonalDetails(data.get('enecoClientNumber'),
                                  data.get('enecoClientEmailAddress'),
                                  data.get('enecoClientFirstName'),
                                  data.get('enecoClientLastName'),
                                  data.get('enecoClientMiddleName'),
                                  data.get('enecoClientMobileNumber'),
                                  data.get('enecoClientPhoneNumber'))
        self.client = Client(data.get('clientId'),
                             data.get('clientIdChecksum'),
                             data.get('passwordHash'),
                             data.get('sample'),
                             details)

    @property
    def _parameters(self):
        return {'clientId': self.client.id,
                'clientIdChecksum': self.client.checksum,
                'random': self._uuid or uuid.uuid4()}

    def _login(self):
        self._authenticate()
        self._get_session()

    def _logout(self, reset=True):
        """Log out of the API."""
        url = '{base}/client/auth/logout'.format(base=self.base_url)
        response = self._session.get(url, params=self._parameters)
        if response.ok:
            if reset:
                self._reset()
            return True
        else:
            return False

    def _get_session(self):
        data = copy.copy(self._parameters)
        data.update({'agreementId': self.agreement.id,
                     'agreementIdChecksum': self.agreement.checksum})
        url = '{base}/client/auth/start'.format(base=self.base_url)
        response = self._session.get(url, params=data)
        if not response.ok:
            self._logout()
            message = ('\n\tStatus Code :{}'
                       '\n\tText :{}').format(response.status_code,
                                              response.text)
            raise UnableToGetSession(message)
        else:
            uuid_kpi = response.json().get('displayUuidKpi', None)
            if uuid_kpi:
                self._uuid = uuid_kpi.get('uuid', None)
        return True

    def _clear_cache(self):
        self._logger.debug('Clearing state cache.')
        state_cache.clear()

    @property
    @cached(state_cache)
    def _state(self):
        """The internal state of the object.

        The api responses are not consistent so a retry is performed on every
        call with information updating the internally saved state refreshing
        the data. The info is cached for STATE_CACHING_SECONDS.

        :return: The current state of the toons' information state.
        """
        state = {}
        required_keys = ('deviceStatusInfo',
                         'gasUsage',
                         'powerUsage',
                         'thermostatInfo',
                         'thermostatStates')
        try:
            for _ in range(self._state_retries):
                state.update(self._get_data('/client/auth/retrieveToonState'))
        except TypeError:
            self._logger.exception('Could not get answer from service.')
        message = ('Updating internal state with retrieved '
                   'state:{state}').format(state=state)
        self._logger.debug(message)
        self._state_.update(state)
        if not all([key in self._state_.keys() for key in required_keys]):
            raise IncompleteResponse(state)
        return self._state_

    def _get_data(self, endpoint, params=None):
        url = '{base}{endpoint}'.format(base=self.base_url,
                                        endpoint=endpoint)
        try:
            response = self._session.get(url,
                                         params=params or self._parameters,
                                         timeout=REQUEST_TIMEOUT)
        except Timeout:
            self._logger.warning('Detected a timeout. '
                                 'Re-authenticating and retrying request.')
            self._logout(reset=False)
            self._login()
            return self._get_data(endpoint, params)
        if response.status_code == 500:
            error_message = response.json().get('reason', '')
            if any([message in error_message
                    for message in AUTHENTICATION_ERROR_STRINGS]):
                self._logger.warning('Detected an issue with authentication. '
                                     'Trying to reauthenticate.')
                self._login()
                return self._get_data(endpoint, params)
        elif not response.ok:
            self._logger.debug(('\n\tStatus Code :{}'
                                '\n\tText :{}').format(response.status_code,
                                                       response.text))
        else:
            try:
                return response.json()
            except (ValueError, TypeError):
                self._logger.debug(('\n\tStatus Code :{}'
                                    '\n\tText :{}').format(response.status_code,
                                                           response.text))
        return {}

    @property
    def smokedetectors(self):
        """:return: A list of smokedetector objects modeled as named tuples"""
        return [SmokeDetector(smokedetector.get('devUuid'),
                              smokedetector.get('name'),
                              smokedetector.get('lastConnectedChange'),
                              smokedetector.get('connected'),
                              smokedetector.get('batteryLevel'),
                              smokedetector.get('type'))
                for smokedetector in self._state.get('smokeDetectors',
                                                     {}).get('device', [])]

    def get_smokedetector_by_name(self, name):
        """Retrieves a smokedetector object by its name

        :param name: The name of the smokedetector to return
        :return: A smokedetector object
        """
        return next((smokedetector for smokedetector in self.smokedetectors
                     if smokedetector.name.lower() == name.lower()), None)

    @property
    def lights(self):
        """:return: A list of light objects"""
        return [Light(self, light.get('name'))
                for light in self._state.get('deviceStatusInfo',
                                             {}).get('device', [])
                if light.get('rgbColor')]

    def get_light_by_name(self, name):
        """Retrieves a light object by its name

        :param name: The name of the light to return
        :return: A light object
        """
        return next((light for light in self.lights
                     if light.name.lower() == name.lower()), None)

    @property
    def smartplugs(self):
        """:return: A list of smartplug objects."""
        return [SmartPlug(self, plug.get('name'))
                for plug in self._state.get('deviceStatusInfo',
                                            {}).get('device', [])
                if plug.get('networkHealthState')]

    def get_smartplug_by_name(self, name):
        """Retrieves a smartplug object by its name

        :param name: The name of the smartplug to return
        :return: A smartplug object
        """
        return next((plug for plug in self.smartplugs
                     if plug.name.lower() == name.lower()), None)

    @property
    def gas(self):
        """:return: A gas object modeled as a named tuple"""
        usage = self._state['gasUsage']
        return Usage(usage.get('avgDayValue'),
                     usage.get('avgValue'),
                     usage.get('dayCost'),
                     usage.get('dayUsage'),
                     usage.get('isSmart'),
                     usage.get('meterReading'),
                     usage.get('value'))

    @property
    def power(self):
        """:return: A power object modeled as a named tuple"""
        power = self._state['powerUsage']
        return PowerUsage(power.get('avgDayValue'),
                          power.get('avgValue'),
                          power.get('dayCost'),
                          power.get('dayUsage'),
                          power.get('isSmart'),
                          power.get('meterReading'),
                          power.get('value'),
                          power.get('meterReadingLow'),
                          power.get('dayLowUsage'))

    @property
    def solar(self):
        power = self._state['powerUsage']
        return Solar(power.get('maxSolar'),
                     power.get('valueProduced'),
                     power.get('valueSolar'),
                     power.get('avgProduValue'),
                     power.get('meterReadingLowProdu'),
                     power.get('meterReadingProdu'),
                     power.get('dayCostProduced'))

    @property
    def thermostat_info(self):
        """:return: A thermostatinfo object modeled as a named tuple"""
        info = self._state['thermostatInfo']
        return ThermostatInfo(info.get('activeState'),
                              info.get('boilerModuleConnected'),
                              info.get('burnerInfo'),
                              info.get('currentDisplayTemp'),
                              info.get('currentModulationLevel'),
                              info.get('currentSetpoint'),
                              info.get('currentTemp'),
                              info.get('errorFound'),
                              info.get('haveOTBoiler'),
                              info.get('nextProgram'),
                              info.get('nextSetpoint'),
                              info.get('nextState'),
                              info.get('nextTime'),
                              info.get('otCommError'),
                              info.get('programState'),
                              info.get('randomConfigId'),
                              info.get('realSetpoint'))

    @property
    def thermostat_states(self):
        """:return: A list of thermostatstate object modeled as named tuples"""
        return [ThermostatState(STATES[state.get('id')],
                                state.get('id'),
                                state.get('tempValue'),
                                state.get('dhw'))
                for state in self._state['thermostatStates']['state']]

    def get_thermostat_state_by_name(self, name):
        """Retrieves a thermostat state object by its assigned name

        :param name: The name of the thermostat state
        :return: The thermostat state object
        """
        self._validate_thermostat_state_name(name)
        return next((state for state in self.thermostat_states
                     if state.name.lower() == name.lower()), None)

    def get_thermostat_state_by_id(self, id_):
        """Retrieves a thermostat state object by its id

        :param id_: The id of the thermostat state
        :return: The thermostat state object
        """
        return next((state for state in self.thermostat_states
                     if state.id == id_), None)

    @property
    def burner_on(self):
        return True if int(self.thermostat_info.burner_info) else False

    @staticmethod
    def _validate_thermostat_state_name(name):
        if name.lower() not in [value.lower() for value in STATES.values()
                                if not value.lower() == 'unknown']:
            raise InvalidThermostatState(name)

    @property
    def thermostat_state(self):
        """The state of the thermostat programming

        :return: A thermostat state object of the current setting
        """
        current_state = self.thermostat_info.active_state
        state = self.get_thermostat_state_by_id(current_state)
        if not state:
            self._logger.debug('Manually set temperature, no Thermostat '
                               'State chosen!')
        return state

    @thermostat_state.setter
    def thermostat_state(self, name):
        """Changes the thermostat state to the one passed as an argument as name

        :param name: The name of the thermostat state to change to.
        """
        self._validate_thermostat_state_name(name)
        id_ = next((key for key in STATES.keys()
                    if STATES[key].lower() == name.lower()), None)
        data = copy.copy(self._parameters)
        data.update({'state': 2,
                     'temperatureState': id_})
        response = self._get_data('/client/auth/schemeState', data)
        self._logger.debug('Response received {}'.format(response))
        self._clear_cache()

    @property
    def thermostat(self):
        """The current setting of the thermostat as temperature

        :return: A float of the current setting of the temperature of the
        thermostat
        """
        return float(self.thermostat_info.current_set_point / 100)

    @thermostat.setter
    def thermostat(self, temperature):
        """A temperature to set the thermostat to. Requires a float.

        :param temperature: A float of the desired temperature to change to.
        """
        target = int(temperature * 100)
        data = copy.copy(self._parameters)
        data.update({'value': target})
        response = self._get_data('/client/auth/setPoint', data)
        self._logger.debug('Response received {}'.format(response))
        self._clear_cache()

    @property
    def temperature(self):
        """The current actual temperature as perceived by toon.

        :return: A float of the current temperature
        """
        return float(self.thermostat_info.current_temperature / 100)
