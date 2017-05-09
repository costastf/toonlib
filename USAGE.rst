=====
Usage
=====

To use toonlib in a project:

.. code-block:: python

    from toonlib import Toon

    eneco_username = 'USERNAME'
    eneco_password = 'PASSWORD'
    toon = Toon(eneco_username, eneco_password)


Print information about the agreement. Attributes are self explanatory.

.. code-block:: python

    print(toon.agreement.id)
    print(toon.agreement.checksum)
    print(toon.agreement.city)
    print(toon.agreement.display_common_name)
    print(toon.agreement.display_hardware_version)
    print(toon.agreement.display_software_version)
    print(toon.agreement.heating_type)
    print(toon.agreement.house_number)
    print(toon.agreement.boiler_management)
    print(toon.agreement.solar)
    print(toon.agreement.toonly)
    print(toon.agreement.post_code)
    print(toon.agreement.street_name)

Print information about the client. Attributes are self explanatory.

.. code-block:: python

    print(toon.client.id)
    print(toon.client.checksum)
    print(toon.client.hash)
    print(toon.client.sample)
    print(toon.client.personal_details.number)
    print(toon.client.personal_details.email)
    print(toon.client.personal_details.first_name)
    print(toon.client.personal_details.last_name)
    print(toon.client.personal_details.middle_name)
    print(toon.client.personal_details.mobile_number)
    print(toon.client.personal_details.phone_number)


Print information about the gas. Values are cached internally for 5 minutes
so as to not overwhelm the api. After the 5 minutes any access to any of the
attributes will refresh the information through a new call to the api.

.. code-block:: python

    print(toon.gas.average_daily)
    print(toon.gas.average)
    print(toon.gas.daily_cost)
    print(toon.gas.daily_usage)
    print(toon.gas.is_smart)
    print(toon.gas.meter_reading)
    print(toon.gas.value)

Print information about the electricity. Values are cached internally for 5 minutes so as to not overwhelm the api. After the 5 minutes any access to any of the attributes will refresh the information through a new call to the api.

.. code-block:: python

    print(toon.power.average_daily)
    print(toon.power.average)
    print(toon.power.daily_cost)
    print(toon.power.daily_usage)
    print(toon.power.is_smart)
    print(toon.power.meter_reading)
    print(toon.power.meter_reading_low)
    print(toon.power.daily_usage_low)
    print(toon.power.value)


Print information about the solar power production. Values are cached internally for 5 minutes so as to not overwhelm the api. After the 5 minutes
  any access to any of the attributes will refresh the information through a new call to the api.

.. code-block:: python

    print(toon.solar.maximum)
    print(toon.solar.produced)
    print(toon.solar.average_produced)
    print(toon.solar.meter_reading_low_produced)
    print(toon.solar.meter_reading_produced)
    print(toon.solar.daily_cost_produced)
    print(toon.solar.value)

Print information about connected hue lights.

.. code-block:: python

    # loop over all the lights
    for light in toon.lights:
        print(light.is_connected)
        print(light.device_uuid)
        print(light.rgb_color)
        print(light.name)
        print(light.current_state)
        print(light.device_type)
        print(light.in_switch_all_group)
        print(light.in_switch_schedule)
        print(light.is_locked)
        print(light.zwave_index)
        print(light.zwave_uuid)

    # or get a light by assigned name
    light = toon.get_light_by_name('Kitchen Ceiling')

    # print current status
    print(light.status)

    # checking whether the light can be toggled. For that to be able to
    # happen the light needs to be connected and not locked.
    # this state is checked internally from all the methods trying to toggle
    # the switch state of the light
    print(light.can_toggle)

    # lights can be turned on, off or toggled
    light.turn_on()
    light.turn_off()
    light.toggle()

Print information about connected fibaro smart plugs.

.. code-block:: python

    # get first smartplug
    plug = toon.smartplugs[0]

    # or get smartplug by assigned name
    plug = toon.get_smartplug_by_name('Dryer')

    # print all the information about the plug
    print(plug.current_usage)
    print(plug.current_state)
    print(plug.average_usage)
    print(plug.daily_usage)
    print(plug.device_uuid)
    print(plug.is_connected)
    print(plug.name)
    print(plug.network_health_state)
    print(plug.device_type)
    print(plug.in_switch_all_group)
    print(plug.in_switch_schedule)
    print(plug.is_locked)
    print(plug.usage_capable)
    print(plug.zwave_index)
    print(plug.zwave_uuid)
    print(plug.flow_graph_uuid)
    print(plug.quantity_graph_uuid)


    # print current status
    print(plug.status)

    # checking whether the plug can be toggled. For that to be able to
    # happen the plug needs to be connected and not locked.
    # this state is checked internally from all the methods trying to toggle
    # the switch state of the plug
    print(plug.can_toggle)

    # plugs can be turned on, off or toggled
    plug.turn_on()
    plug.turn_off()
    plug.toggle()

Print information about connected smokedetectors.

.. code-block:: python

    # loop over all the smokedetectors
    for smokedetector in toon.smokedetectors:
        print(smokedetector.device_uuid)
        print(smokedetector.name)
        print(smokedetector.last_connected_change)
        print(smokedetector.is_connected)
        print(smokedetector.battery_level)
        print(smokedetector.device_type)


    # or get a smokedetector by assigned name
    smokedetector = toon.get_smokedetector_by_name('Kitchen')


Get the current temperature

.. code-block:: python

    # show the current temperature
    print(toon.temperature)


Work with thermostat states

.. code-block:: python

    # show the information about the current state
    print(toon.thermostat_state.name)
    print(toon.thermostat_state.id)
    print(toon.thermostat_state.temperature)
    print(toon.thermostat_state.dhw)

    # set the current state by using a name out of ['comfort', 'home', 'sleep', away]
    toon.thermostat_state = 'comfort' # Case does not matter. The actual
                                      # values can be overwritten on the
                                      # configuration.py dictionary.


Check out all the thermostat states configured

.. code-block:: python

    for state in toon.thermostat_states:
        print(state.name)
        print(state.id)
        print(state.temperature)
        print(state.dhw)


Work with the thermostat

.. code-block:: python

    # show current value of thermostat
    print(toon.thermostat)

    # manually assign temperature to thermostat. This will override the thermostat state
    toon.thermostat = 20


The toon object exposes rrd measurement data in two forms, flow and graph and
 per interest item, gas, solar and for graph data type only, district_heat.

.. code-block:: python

    from pprint import pprint

    # print flow data for gas
    pprint(toon.data.flow.gas)

    # print graph data for gas
    pprint(toon.data.graph.gas)


    # print flow data for power
    pprint(toon.data.flow.power)

    # print graph data for power
    pprint(toon.data.graph.power)


    # print flow data for solar
    pprint(toon.data.flow.solar)

    # print graph data for solar
    pprint(toon.data.graph.solar)