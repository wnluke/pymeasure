#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2020 PyMeasure Developers
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

from pymeasure.instruments.rf_signal_generator import RFSignalGeneratorDM
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import truncated_range, strict_discrete_set, strict_range
import struct

class RS_SMIQ06B(RFSignalGeneratorDM):
    # Define instrument limits according to datasheet
    power_values = (-144.0, 16.0)
    frequency_values = (300e3, 6.4e9)

    ####################################################################
    # 3.5.14.5 SOURce:DM (Digital Modulation) Subsystem ([:SOURce]:DM)
    ####################################################################
    CUSTOM_MODULATION_DATA = {
        'Pattern0011' : None, # Not supported
        'Pattern0101' : "PATT;PATT ALT",
        'PatternPN9' :  "PRBS;PRBS 9",
        'DATA' : "DLIST",
    }

    CUSTOM_MODULATION_ENABLE_MAP = {
        1: "ON",
        0: "OFF"
    }

    custom_modulation_enable = Instrument.control(
        ":DM:STATE?", ":DM:STATE %s", 
        """ A boolean property that enables or disables the Custom modulation. 
        This property can be set. """,
        validator=strict_discrete_set,
        values=CUSTOM_MODULATION_ENABLE_MAP,
        map_values=True
    )

    custom_modulation = Instrument.control(
        ":DM:FORMat?", ":DM:FORMat %s", 
        """ A string property that allow to selects the modulation. QWCDma is only available with option SMIQB47.
        """,
        validator=strict_discrete_set,
        values=RFSignalGeneratorDM.MODULATION_TYPES
    )

    custom_modulation_filter = Instrument.setting(
        ":DM:FILTer:TYPE %s", 
        """ A string property that allow to set the type of filter.
        """,
        validator=strict_discrete_set,
        values=RFSignalGeneratorDM.MODULATION_FILTERS
    )

    custom_modulation_bbt = Instrument.setting(
        ":DM:FILTer:PARameter %f", 
        """ A  property that allow to set filter parameter (Roff Off or BxT rate).
        """,
        validator=strict_range,
        values=[0.1,1.0]
    )

    custom_modulation_symbol_rate = Instrument.setting(
        ":DM:SRATe %e", 
        """ A integer property that allow to set the transmission symbol rate
        This property can be set. """,
        validator=strict_range,
        values=[1000, 7e6]        
    )

    custom_modulation_ask_depth = Instrument.setting(
        ":DM:ASK:DEPTh %e", 
        """ An integer property that allow to set the depth for the amplitude shift keying (ASK) modulation.
        Depth is set as a percentage of the full power on level.
        """,
        validator=strict_range,
        values=[0, 100]
    )

    custom_modulation_fsk_deviation = Instrument.setting(
        ":DM:FSK:DEViation %e", 
        """ An integer property that allow to set the FSK frequency deviation value.
        Unit is Hz.
        """,
        validator=strict_range,
        values=[100, 2.5e6]
    )

    custom_modulation_data = Instrument.setting(
        ":DM:SOURce %s", 
        """ A string property that allow to set the data source.
        """,
        validator=strict_discrete_set,
        values=CUSTOM_MODULATION_DATA,
        map_values=True
    )

    memory = Instrument.measurement(
        ":DM:DLISt:FREE?",
        """ This property returns a list of data list names separated by commas.""",
        get_process=lambda v: int(v[0]),
    )

    def __init__(self, resourceName, **kwargs):
        super().__init__(
            resourceName,
            "Rohde & Schwarz SMIQ06B Signal Generator",
            **kwargs
        )

    def _get_symbol_length(self):
        modulation = self.custom_modulation
        symbol_length = 1
        if modulation in ["FSK4", "QPSK", "PSK4", "P4QPsk", "AFSK4"]:
            symbol_length = 2
        elif modulation == "USER":
            symbol_length = int(float(self.ask("DM:MLIST:DATA?").split(",")[1]))
        return symbol_length
            
    def data_load(self, bitsequences, spacings):
        """ Load data into signal generator for transmission, the parameters are:
        bitsequences: list of items. Each item is a string of '1' or '0' in transmission order
        spacings: integer list, gap to be inserted between each bitsequence  expressed in number of bit
        """
        # Check if bitsequences are compatible with bit per symbol
        
        # Switch line terminator to EOI to send data in packed format
        self.write(":SYST:COMM:GPIB:LTER EOI")
        # Select data list
        self.write("SOURce:DM:DLISt:DELete 'data2tx'")
        self.write("SOURce:DM:DLISt:SELect 'data2tx'")

        # Write data list and store positions when switch between sequence and spacing occurs
        # for bitseq, spacing in zip(bitsequences, spacings):
        sympos = 0
        ctrls = []
        val = ''
        symbol_length = self._get_symbol_length()
        for bitseq, spacing in zip(bitsequences, spacings):
            ctrls.append(sympos)
            val += bitseq + "0"*spacing
            sympos += (len(bitseq)//symbol_length)
            ctrls.append(sympos)
            sympos += (spacing//symbol_length)
        length = len(val)

        # Pad to have size multiple of 8
        if (length % 8):
            val = val + "0"*(8-(length % 8))
            length = len(val)
            
        values = []
        for i in range(0, length, 8):
            values.append(int(val[i:i+8], 2))
        
        self.adapter.write_binary_values("SOURce:DM:DLISt:DATA ", values, datatype='B')
        self.complete

        # Write control list
        # The control list is used to switch on the RF during sequence transmission and switch it off
        # during spacing
        self.write("SOURce:DM:CLISt:DELete 'datactrl'")
        self.write("SOURce:DM:CLISt:SELect 'datactrl'")
        self.complete

        values = []
        index_mask = (1 << 26) - 1 # 26 bits
        for i,v in enumerate(ctrls):
            # Switch on the power at the beginning of each sequence and switch it off at end of the sequences
            values.append( (((i+1)%2) << 31) + (v & index_mask))
        self.adapter.write_binary_values("SOURce:DM:CLISt:DATA ", values, datatype="I", is_big_endian=True)
        self.complete

        # Switch back to normal mode
        self.write(":SYST:COMM:GPIB:LTER STANDARD")

        self.write(":DM:CLISt:CONTrol ON")
        self.write(":DM:PRAMp:SOURce CLISt")
        self.write(":DM:PRAMp:STATe ON")
        self.complete

    def enable_modulation(self):
        # Do nothing since  each modulation type should be enable with relevant command
        pass

    def disable_modulation(self):
        """ Disables the signal modulation. """
        self.amplitude_modulation_enable = "OFF"
        self.pulse_modulation_enable = "OFF"
        self.custom_modulation_enable = 0
        self.write("SOUR:PDC:STAT OFF")

    def data_trigger_setup(self, mode='SINGLE'):
        """ Configure the trigger system for bitsequence transmission
        """
        self.write(":SOUR:DM:TRIGger:SOURce INT")
        self.write(":SOUR:DM:SEQ %s"%mode)

    def data_trigger(self):
        """ Trigger a bitsequence transmission
        """
        self.write(":TRIG:DM:IMM")

    def set_fsk_constellation(self, constellation, fsk_dev):
        """ For multi level FSK modulation, we need to define the constellation mapping.

        For R&S SMIQ06B, there is a dedicated user modulation to define FSK constellation.
        """
        self.bit_per_symbol = len(format(max(constellation.keys()), "b"))
        if (self.bit_per_symbol > 8):
            raise Exception("Multi level FSK is dupported up to 256 levels, i.e 8bit per symbol")

        cmd_params = "3,{},0,0,0,0".format(self.bit_per_symbol)
        for val in sorted(constellation.keys()):
            cmd_params += ",{:.3f},0".format(1/constellation[val])
        self.write("SOURce:DM:MLISt:DELete 'datamod'")
        self.write("SOURce:DM:MLISt:SELect 'datamod'")
        self.write(":SOUR:DM:MLIS:DATA {}".format(cmd_params))
        self.write(":DM:FORMat USER")