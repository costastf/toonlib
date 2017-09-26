#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# File: toonlib.py
"""All helper objects will live here"""

import logging
import copy
from collections import namedtuple

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = 'plaintext'
__date__ = '''13-03-2017'''

LOGGER_BASENAME = '''helpers'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


ThermostatState = namedtuple('ThermostatState', ('name',
                                                 'id',
                                                 'temperature',
                                                 'dhw'))

ThermostatInfo = namedtuple('ThermostatInfo', ('active_state',
                                               'boiler_connected',
                                               'burner_info',
                                               'current_displayed_temperature',
                                               'current_modulation_level',
                                               'current_set_point',
                                               'current_temperature',
                                               'error_found',
                                               'have_ot_boiler',
                                               'next_program',
                                               'next_set_point',
                                               'next_state',
                                               'next_time',
                                               'ot_communication_error',
                                               'program_state',
                                               'random_configuration_id',
                                               'real_set_point'))

Usage = namedtuple('Usage', ('average_daily',
                             'average',
                             'daily_cost',
                             'daily_usage',
                             'is_smart',
                             'meter_reading',
                             'value'))

Low = namedtuple('Low', ('meter_reading_low', 'daily_usage_low'))

Solar = namedtuple('Solar', ('maximum',
                             'produced',
                             'value',
                             'average_produced',
                             'meter_reading_low_produced',
                             'meter_reading_produced',
                             'daily_cost_produced'))

PowerUsage = namedtuple('PowerUsage',
                        Usage._fields + Low._fields)

Agreement = namedtuple('Agreement', ('id',
                                     'checksum',
                                     'city',
                                     'display_common_name',
                                     'display_hardware_version',
                                     'display_software_version',
                                     'heating_type',
                                     'house_number',
                                     'boiler_management',
                                     'solar',
                                     'toonly',
                                     'post_code',
                                     'street_name'))

PersonalDetails = namedtuple('PersonalDetails', ('number',
                                                 'email',
                                                 'first_name',
                                                 'last_name',
                                                 'middle_name',
                                                 'mobile_number',
                                                 'phone_number'))

Client = namedtuple('Client', ('id',
                               'checksum',
                               'hash',
                               'sample',
                               'personal_details'))

SmokeDetector = namedtuple('SmokeDetector', ('device_uuid',
                                             'name',
                                             'last_connected_change',
                                             'is_connected',
                                             'battery_level',
                                             'device_type'))


class Data(object):
    """Data object exposing flow and graph attributes."""

    class Flow(object):
        """The object that exposes the flow information of categories in toon

        The information is rrd metrics and the object dynamically handles the
        accessing of attributes matching with the corresponding api endpoint
        if they are know, raises an exception if not.
        """

        def __init__(self, toon_instance):
            self.toon = toon_instance
            self._endpoint = {'power': '/client/auth/getElecFlowData',
                              'gas': '/client/auth/getGasFlowData',
                              'solar': '/client/auth/getSolarFlowData'}

        def __getattr__(self, name):
            """Implements dynamic atributes on the Flow object"""
            endpoint = self._endpoint.get(name)
            if not endpoint:
                raise AttributeError(name)
            data = self.toon._get_data(endpoint)
            return data.get('graphData') if data.get('success') else None

    class Graph(object):
        """The object that exposes the graph information of categories in toon

        The information is rrd metrics and the object dynamically handles the
        accessing of attributes matching with the corresponding api endpoint
        if they are know, raises an exception if not.
        """

        def __init__(self, toon_instance):
            self.toon = toon_instance
            self._endpoint = {'power': '/client/auth/getElecGraphData',
                              'gas': '/client/auth/getGasGraphData',
                              'solar': '/client/auth/getSolarGraphData',
                              'district_heat':
                                  '/client/auth/getDistrictHeatGraphData'}

        def __getattr__(self, name):
            """Implements dynamic atributes on the Graph object"""
            endpoint = self._endpoint.get(name)
            if not endpoint:
                raise AttributeError(name)
            data = self.toon._get_data(endpoint)
            return data.get('graphData') if data.get('success') else None

    def __init__(self, toon_instance):
        logger_name = u'{base}.{suffix}'.format(base=LOGGER_BASENAME,
                                                suffix=self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)
        self.flow = self.Flow(toon_instance)
        self.graph = self.Graph(toon_instance)


class Switch(object):
    """Core object to implement the turning on, off or toggle

    Both hue lamps and fibaro plugs have a switch component that is shared.
    This implements that usage.
    """

    def __init__(self, toon_instance, name):
        logger_name = u'{base}.{suffix}'.format(base=LOGGER_BASENAME,
                                                suffix=self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)
        self.toon = toon_instance
        self._name = name

    @property
    def name(self):
        return self._name

    def _get_value(self, name, config=False):
        key = 'deviceConfigInfo' if config else 'deviceStatusInfo'
        return next((item.get(name) for item in
                     self.toon._state.get(key).get('device')  # noqa
                     if item.get('name') == self.name), None)

    def toggle(self):
        return self._change_state(not self.current_state)

    def turn_on(self):
        return self._change_state(1)

    @property
    def status(self):
        return 'on' if self.current_state else 'off'

    def _change_state(self, state):
        if not self.can_toggle:
            self._logger.warning('The item is not connected or locked, cannot '
                                 'change state.')
            return False
        else:
            data = copy.copy(self.toon._parameters)  # noqa
            data.update({'state': int(state),
                         'devUuid': self.device_uuid})
            response = self.toon._get_data('/client/auth/smartplug/setTarget',  # noqa
                                           data)
            self._logger.debug('Response received {}'.format(response))
            self.toon._clear_cache()  # noqa
            return True

    @property
    def can_toggle(self):
        if not self.is_connected or self.is_locked:
            return False
        else:
            return True

    def turn_off(self):
        return self._change_state(0)

    @property
    def device_uuid(self):
        return self._get_value('devUUID')

    @property
    def is_connected(self):
        value = self._get_value('isConnected')
        return True if value else False

    @property
    def current_state(self):
        return self._get_value('currentState')

    @property
    def device_type(self):
        return self._get_value('devType', config=True)

    @property
    def in_switch_all_group(self):
        value = self._get_value('inSwitchAll', config=True)
        return True if value else False

    @property
    def in_switch_schedule(self):
        value = self._get_value('inSwitchSchedule', config=True)
        return True if value else False

    @property
    def zwave_index(self):
        return self._get_value('position', config=True)

    @property
    def is_locked(self):
        value = self._get_value('switchLocked', config=True)
        return True if value else False

    @property
    def zwave_uuid(self):
        return self._get_value('zwUuid', config=True)


class SmartPlug(Switch):
    """Object modeling the fibaro smart plugs the toon can interact with.

    It inherits from switch which is the common interface with the hue
    lamps to turn on, off or toggle
    """

    def __init__(self, toon_instance, name):
        super(SmartPlug, self).__init__(toon_instance, name)
        self._usage_capable = None

    @property
    def average_usage(self):
        return self._get_value('avgUsage') if self.usage_capable else 0

    @property
    def current_usage(self):
        return self._get_value('currentUsage') if self.usage_capable else 0

    @property
    def daily_usage(self):
        return self._get_value('dayUsage') if self.usage_capable else 0

    @property
    def network_health_state(self):
        return self._get_value('networkHealthState')

    @property
    def usage_capable(self):
        if self._usage_capable is None:
            value = self._get_value('usageCapable', config=True)
            self._usage_capable = True if value else False
        return self._usage_capable

    @property
    def quantity_graph_uuid(self):
        return self._get_value('quantityGraphUuid', config=True)

    @property
    def flow_graph_uuid(self):
        return self._get_value('flowGraphUuid', config=True)


class Light(Switch):
    """Object modeling the hue light bulbs that toon can interact with.

    It inherits from switch which is the common interface with the hue
    lamps to turn on, off or toggle
    """

    def __init__(self, toon_instance, name):
        super(Light, self).__init__(toon_instance, name)

    @property
    def rgb_color(self):
        return self._get_value('rgbColor')
