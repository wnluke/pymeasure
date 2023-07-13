#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2021 PyMeasure Developers
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

from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import truncated_range, strict_discrete_set


class XT981BL(Instrument):

    """
        All the commands are available in the "USER GUIDE XT Tuner: Connection and Control (XT981-557 Rev B 08/2022)"
        Chapter 8 TUNING COMMANDS

    """

    back_port = Instrument.control(
        "BACKport?;", "BACKport %s;",
        """ Query current backport file.
            Set backport S-parameter block to a .s2p file or directly writes S-parameters of a selected control frequency.
            Example: BACK atten.s2p
        This property can be set.
        """,
        dynamic=True
    )

    back_port_spar = Instrument.measurement(
        "BACKport:SPAR?;",
        """ Returns current backport S-parameters """,
        map_values=True,
    )

    calibration = Instrument.control(
        "CALIBration?;", "CALIBration %s;",
        """ Reads current calibration file.
            Defines calibration data file. Data is loaded into memory after sending FREQ command.
            Example: CALIB xt982a.tun
        This property can be set.
        """,
        dynamic=True
    )

    cal_info = Instrument.control(
        "CALINFO?;", "CALINFO? %s;",
        """ Reads contents of current cal or selected file [fname]
            Example: CALINFO? xt982a.tun
        This property can be set.
        """,
        dynamic=True
    )

    config_algo = Instrument.control(
        "CONFIGuration:ALGorithm?;", "CONFIGuration:ALGorithm %d;",
        """ Queries set algorithm.
            Sets the tuning algorithm.
            Example: CONFIGuration:ALGorithm 3
        This property can be set.
        """,
        validator=strict_discrete_set,
        values=(2, 3),
        dynamic=True
    )

    def __init__(self, resourceName, description="Maury Microwave XT981BL", **kwargs):
        super().__init__(
            resourceName,
            description,
            **kwargs
        )

    def clear(self):
        """ Clears all settings for calibration, frequencies, and fixture files """
        self.write("CLEAR;")
        self.complete
