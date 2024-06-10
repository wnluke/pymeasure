<<<<<<< HEAD
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2023 PyMeasure Developers
=======
#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2016 PyMeasure Developers
>>>>>>> power_supplies
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import logging
<<<<<<< HEAD
import time
import numpy as np
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import truncated_range, strict_discrete_set

# Setup logging
=======
>>>>>>> power_supplies
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


<<<<<<< HEAD
class Keithley2600(Instrument):
    """Represents the Keithley 2600 series (channel A and B) SourceMeter"""

    def __init__(self, adapter, name="Keithley 2600 SourceMeter", **kwargs):
        super().__init__(
            adapter,
            name,
            **kwargs
        )
        self.ChA = Channel(self, 'a')
        self.ChB = Channel(self, 'b')

    @property
    def error(self):
        """ Returns a tuple of an error code and message from a
        single error. """
        err = self.ask('print(errorqueue.next())')
        err = err.split('\t')
        # Keithley Instruments Inc. sometimes on startup
        # if tab delimitated message is greater than one, grab first two as code, message
        # otherwise, assign code & message to returned error
        if len(err) > 1:
            err = (int(float(err[0])), err[1])
            code = err[0]
            message = err[1].replace('"', '')
        else:
            code = message = err[0]
        log.info(f"ERROR {str(code)},{str(message)} - len {str(len(err))}")
        return (code, message)

    def check_errors(self):
        """ Logs any system errors reported by the instrument.
        """
        code, message = self.error
        while code != 0:
            t = time.time()
            log.info("Keithley 2600 reported error: %d, %s" % (code, message))
            code, message = self.error
            if (time.time() - t) > 10:
                log.warning("Timed out for Keithley 2600 error retrieval.")


class Channel:

    def __init__(self, instrument, channel):
        self.instrument = instrument
        self.channel = channel

    def ask(self, cmd):
        return float(self.instrument.ask(f'print(smu{self.channel}.{cmd})'))

    def write(self, cmd):
        self.instrument.write(f'smu{self.channel}.{cmd}')

    def values(self, cmd, **kwargs):
        """ Reads a set of values from the instrument through the adapter,
        passing on any key-word arguments.
        """
        return self.instrument.values(f'print(smu{self.channel}.{cmd})')

    def binary_values(self, cmd, header_bytes=0, dtype=np.float32):
        return self.instrument.binary_values('print(smu%s.%s)' %
                                             (self.channel, cmd,), header_bytes, dtype)

    def check_errors(self):
        return self.instrument.check_errors()

    source_output = Instrument.control(
        'source.output', 'source.output=%d',
        """Property controlling the channel output state (ON of OFF)
        """,
        validator=strict_discrete_set,
        values={'OFF': 0, 'ON': 1},
        map_values=True
    )

    source_mode = Instrument.control(
        'source.func', 'source.func=%d',
        """Property controlling the channel soource function (Voltage or Current)
        """,
        validator=strict_discrete_set,
        values={'voltage': 1, 'current': 0},
        map_values=True
    )

    measure_nplc = Instrument.control(
        'measure.nplc', 'measure.nplc=%f',
        """ Property controlling the nplc value """,
        validator=truncated_range,
        values=[0.001, 25],
        map_values=True
    )

    ###############
    # Current (A) #
    ###############
    current = Instrument.measurement(
        'measure.i()',
        """ Reads the current in Amps """
    )

    source_current = Instrument.control(
        'source.leveli', 'source.leveli=%f',
        """ Property controlling the applied source current """,
        validator=truncated_range,
        values=[-1.5, 1.5]
    )

    compliance_current = Instrument.control(
        'source.limiti', 'source.limiti=%f',
        """ Property controlling the source compliance current """,
        validator=truncated_range,
        values=[-1.5, 1.5]
    )

    source_current_range = Instrument.control(
        'source.rangei', 'source.rangei=%f',
        """Property controlling the source current range """,
        validator=truncated_range,
        values=[-1.5, 1.5]
    )

    current_range = Instrument.control(
        'measure.rangei', 'measure.rangei=%f',
        """Property controlling the measurement current range """,
        validator=truncated_range,
        values=[-1.5, 1.5]
    )

    ###############
    # Voltage (V) #
    ###############
    voltage = Instrument.measurement(
        'measure.v()',
        """ Reads the voltage in Volts """
    )

    source_voltage = Instrument.control(
        'source.levelv', 'source.levelv=%f',
        """ Property controlling the applied source voltage """,
        validator=truncated_range,
        values=[-200, 200]
    )

    compliance_voltage = Instrument.control(
        'source.limitv', 'source.limitv=%f',
        """ Property controlling the source compliance voltage """,
        validator=truncated_range,
        values=[-200, 200]
    )

    source_voltage_range = Instrument.control(
        'source.rangev', 'source.rangev=%f',
        """Property controlling the source current range """,
        validator=truncated_range,
        values=[-200, 200]
    )

    voltage_range = Instrument.control(
        'measure.rangev', 'measure.rangev=%f',
        """Property controlling the measurement voltage range """,
        validator=truncated_range,
        values=[-200, 200]
    )

    ####################
    # Resistance (Ohm) #
    ####################
    resistance = Instrument.measurement(
        'measure.r()',
        """ Reads the resistance in Ohms """
    )

    wires_mode = Instrument.control(
        'sense', 'sense=%d',
        """Property controlling the resistance measurement mode: 4 wires or 2 wires""",
        validator=strict_discrete_set,
        values={'4': 1, '2': 0},
        map_values=True
    )

    #######################
    # Measurement Methods #
    #######################

    def measure_voltage(self, nplc=1, voltage=21.0, auto_range=True):
        """ Configures the measurement of voltage.
        :param nplc: Number of power line cycles (NPLC) from 0.001 to 25
        :param voltage: Upper limit of voltage in Volts, from -200 V to 200 V
        :param auto_range: Enables auto_range if True, else uses the set voltage
        """
        log.info("%s is measuring voltage." % self.channel)
        self.write('measure.v()')
        self.write('measure.nplc=%f' % nplc)
        if auto_range:
            self.write('measure.autorangev=1')
        else:
            self.voltage_range = voltage
        self.check_errors()

    def measure_current(self, nplc=1, current=1.05e-4, auto_range=True):
        """ Configures the measurement of current.
        :param nplc: Number of power line cycles (NPLC) from 0.001 to 25
        :param current: Upper limit of current in Amps, from -1.5 A to 1.5 A
        :param auto_range: Enables auto_range if True, else uses the set current
        """
        log.info("%s is measuring current." % self.channel)
        self.write('measure.i()')
        self.write('measure.nplc=%f' % nplc)
        if auto_range:
            self.write('measure.autorangei=1')
        else:
            self.current_range = current
        self.check_errors()

    def auto_range_source(self):
        """ Configures the source to use an automatic range.
        """
        if self.source_mode == 'current':
            self.write('source.autorangei=1')
        else:
            self.write('source.autorangev=1')

    def apply_current(self, current_range=None, compliance_voltage=0.1):
        """ Configures the instrument to apply a source current, and
        uses an auto range unless a current range is specified.
        The compliance voltage is also set.
        :param compliance_voltage: A float in the correct range for a
                                   :attr:`~.Keithley2600.compliance_voltage`
        :param current_range: A :attr:`~.Keithley2600.current_range` value or None
        """
        log.info("%s is sourcing current." % self.channel)
        self.source_mode = 'current'
        if current_range is None:
            self.auto_range_source()
        else:
            self.source_current_range = current_range
        self.compliance_voltage = compliance_voltage
        self.check_errors()

    def apply_voltage(self, voltage_range=None,
                      compliance_current=0.1):
        """ Configures the instrument to apply a source voltage, and
        uses an auto range unless a voltage range is specified.
        The compliance current is also set.
        :param compliance_current: A float in the correct range for a
                                   :attr:`~.Keithley2600.compliance_current`
        :param voltage_range: A :attr:`~.Keithley2600.voltage_range` value or None
        """
        log.info("%s is sourcing voltage." % self.channel)
        self.source_mode = 'voltage'
        if voltage_range is None:
            self.auto_range_source()
        else:
            self.source_voltage_range = voltage_range
        self.compliance_current = compliance_current
        self.check_errors()

    def ramp_to_voltage(self, target_voltage, steps=30, pause=0.1):
        """ Ramps to a target voltage from the set voltage value over
        a certain number of linear steps, each separated by a pause duration.
        :param target_voltage: A voltage in Amps
        :param steps: An integer number of steps
        :param pause: A pause duration in seconds to wait between steps """
        voltages = np.linspace(self.source_voltage, target_voltage, steps)
        for voltage in voltages:
            self.source_voltage = voltage
            time.sleep(pause)

    def ramp_to_current(self, target_current, steps=30, pause=0.1):
        """ Ramps to a target current from the set current value over
        a certain number of linear steps, each separated by a pause duration.
        :param target_current: A current in Amps
        :param steps: An integer number of steps
        :param pause: A pause duration in seconds to wait between steps """
        currents = np.linspace(self.source_current, target_current, steps)
        for current in currents:
            self.source_current = current
            time.sleep(pause)

    def shutdown(self):
        """ Ensures that the current or voltage is turned to zero
        and disables the output. """
        log.info("Shutting down channel %s." % self.channel)
        if self.source_mode == 'current':
            self.ramp_to_current(0.0)
        else:
            self.ramp_to_voltage(0.0)
        self.source_output = 'OFF'
=======
import visa
import numpy as np
import time
from io import BytesIO


class Keithley2600(Instrument):
    """This is the class for the Keithley 2600-series instruments"""

    def __init__(self, resourceName, **kwargs):
        super(Keithley2600, self).__init__(
            resourceName,
            "Keithley 2600 Sourcemeter",
            includeSCPI=False,
            **kwargs
        )
        self.adapter.connection.read_termination = '\n'

    def get_currentA(self):
        '''Get the current reading for channel A.'''
        return float(self.ask('print(smua.measure.i())'))

    @property
    def currentA(self):
        '''Get the current reading for channel A.'''
        return float(self.ask('print(smua.measure.i())'))
    @property
    def currentB(self):
        '''Get the current reading for channel B.'''
        return float(self.ask('print(smub.measure.i())'))
    @currentA.setter
    def currentA(self, value):
        '''Set the source current for channel A.'''
        self.write('smua.source.func=smua.OUTPUT_DCAMPS;smua.source.leveli=%s' % value)
    @currentB.setter
    def currentB(self, value):
        '''Set the source current for channel B.'''
        self.write('smub.source.func=smub.OUTPUT_DCAMPS;smub.source.leveli=%s' % value)

    @property
    def voltageA(self):
        '''Get the voltage reading for channel A'''
        return float(self.ask('print(smua.measure.v())'))
    @property
    def voltageB(self):
        '''Get the voltage reading for channel B'''
        return float(self.ask('print(smub.measure.v())'))
    @voltageA.setter
    def voltageA(self, value):
        '''Set the source voltage for channel A.'''
        self.write('smua.source.func=smua.OUTPUT_DCVOLTS;smua.source.levelv=%s' % value)
    @voltageB.setter
    def voltageB(self, value):
        '''Set the source voltage for channel B.'''
        self.write('smub.source.func=smub.OUTPUT_DCVOLTS;smub.source.levelv=%s' % value)

    @property
    def modeA(self):
        '''Get the source function for channel A.'''
        return self.ask('print(smuA.source.func())')
    @property
    def modeB(self):
        '''Get the source function for channel B.'''
        return self.ask('print(smuB.source.func())')
    @modeA.setter
    def modeA(self, value):
        '''Set the source function ('voltage' or 'current') for channel A'''
        value={'voltage':'OUTPUT_DCVOLTS','current':'OUTPUT_DCAMPS'}[value]
        self.write('smua.source.func=smua.%s' % value)
    @modeB.setter
    def modeB(self, value):
        '''Set the source function ('voltage' or 'current') for channel B'''
        value={'voltage':'OUTPUT_DCVOLTS','current':'OUTPUT_DCAMPS'}[value]
        self.write('smub.source.func=smub.%s' % value)


    @property
    def outputA(self):
        '''Gets the source output ('on'/'off'/'highz') for channel A'''
        return {0: 'off', 1:'on', 2: 'highz'}[int(float(self.ask('print(smua.source.output)')))]
    @property
    def outputB(self):
        '''Gets the source output ('on'/'off'/'highz')  for channel B'''
        return {0: 'off', 1:'on', 2: 'highz'}[int(float(self.ask('print(smub.source.output)')))]
    @outputA.setter
    def outputA(self, value):
        '''Sets the source output ('on'/'off'/'highz') for channel A'''
        status = 'ON' if ((value==True) or (value==1) or (value=='on')) else 'OFF'
        self.write('smua.source.output= smua.OUTPUT_%s' %status)
    @outputB.setter
    def outputB(self, value):
        '''Sets the source output ('on'/'off'/'highz') for channel B'''
        status = 'ON' if ((value==True) or (value==1) or (value=='on')) else 'OFF'
        self.write('smub.source.output= smub.OUTPUT_%s' %status)

    @property
    def voltagelimitA(self,value):
        '''Get the output voltage compliance limit for channel A'''
        return float(self.ask('print(smua.source.limitv'))
    @property
    def voltagelimitB(self,value):
        '''Get the output voltage compliance limit for channel B'''
        return float(self.ask('print(smub.source.limitv'))
    @voltagelimitA.setter
    def voltagelimitA(self,value):
        '''Get the output voltage compliance limit for channel A'''
        return self.write('smua.source.limitv=%s' %value)
    @voltagelimitB.setter
    def voltagelimitB(self,value):
        '''Get the output voltage compliance limit for channel B'''
        return self.write('smub.source.limitv=%s' %value)


    @property
    def currentlimitA(self,value):
        '''Get the output current compliance limit for channel A'''
        return float(self.ask('print(smua.source.limiti'))
    @property
    def currentlimitB(self,value):
        '''Get the output current compliance limit for channel B'''
        return float(self.ask('print(smub.source.limiti'))
    @currentlimitA.setter
    def currentlimitA(self,value):
        '''Get the output current compliance limit for channel A'''
        return self.write('smua.source.limiti=%s' %value)
    @currentlimitB.setter
    def currentlimitB(self,value):
        '''Get the output current compliance limit for channel B'''
        return self.write('smub.source.limiti=%s' %value)

    def resetA(self):
        '''Resets the A channel'''
        self.write('smua.reset()')
    def resetB(self):
        '''Resets the B channel'''
        self.write('smub.reset()')
>>>>>>> power_supplies
