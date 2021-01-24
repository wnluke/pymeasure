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

from pymeasure.instruments.spectrum_analyzer import SpectrumAnalyzer
from pymeasure.instruments.validators import truncated_range, strict_discrete_set

class RS_FSW13(SpectrumAnalyzer):
    """ Rohde&Schwarz FSW13 spectrum analyzer """

    # Customize parameters with values taken from datasheet/user manual 
    reference_level_values = (-40, 27)

    frequency_span_values = (0, 13.6e9)

    resolution_bw_values = (10, 10e6)

    input_attenuation_values = (0, 70) # This limit is not clear in the datasheet

    frequency_points_values = (101, 100001)

    detector_values = ("APE", "NEG", "POS", "QPE", "SAMP", "RMS", "AVER", "CAV", "CRMS"),

    trace_mode_get_command = "DISPLAY:TRACe:MODE?;"
    trace_mode_set_command = "DISPLAY:TRACe:MODE %s;"

    input_attenuation_get_command = ":INPut:ATTenuation?;"
    input_attenuation_set_command = ":INPut:ATTenuation %d;"


    def __init__(self, resourceName, **kwargs):
        super().__init__(
            resourceName,
            "R&S FSW Spectrum Analyzer FSW-13",
            **kwargs
        )
