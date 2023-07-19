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
from pymeasure.instruments.validators import strict_discrete_set
from math import atan2,degrees


class XT981BL18(Instrument):

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

    dump = Instrument.control(
        "DUMP?;", "DUMP? %d;",
        """ Dumps all tuner and fixture S-parameter data for one of all control frequencies.
        This property can be set with parameter [FreqIdx].
        """,
        dynamic=True
    )

    fixture = Instrument.control(
        "FIXTure?;", "FIXTure %s;",
        """ Used to query current fixture file.
            Sets fixture S-parameter block to a .s2p file or directly writes S-parameters of a selected control frequency.
            If .s2p file is loaded freq must be called afterwards to set S-parameters.
            If writing S-parameter data directly freq must be set first.
            Example: 
                FIXT atten.s2p
                FIXT <idx> <s11m> <s11p> <s12m> <s12p> <s21m> <s21p> <s22m> <s22p>
        This property can be set.
        """,
        dynamic=True
    )

    fixture_spar = Instrument.measurement(
        "FIXTure:SPAR?;",
        """ Returns current fixture S-parameters """,
    )

    gamma = Instrument.control(
        "GAMMA?;", "GAMMA? %d;",
        """ Reads current Gamma and Loss(dB) of one or all control frequencies.
            The Loss value is defined between DUT and Load (including FIXTURE, TUNER and BACK)
            Use IDX > 0 to report GAMMA at specific harmonic only. IDX=0 reports GAMMA for fundamental and all harmonics.
            Examples: GAMMA?
            Returns: <Freq>,<Mag,<Phase>,<Loss>
        This property can be set with parameter [FreqIdx].
        """,
        dynamic=True
    )

    loss = Instrument.control(
        "LOSS?;", "LOSS? %d;",
        """ Same as GAMMA?
        This property can be set with parameter [FreqIdx].
        """,
        dynamic=True
    )

    help = Instrument.measurement(
        "HELP?;",
        """ Display list of supported commands """,
    )

    setup = Instrument.measurement(
        "SETUP?;",
        """ Query current setup file """,
    )

    setup_all = Instrument.measurement(
        "SETUP:ALL?;",
        """ Query all files in current setup file.
            Returns: <Setup File> <Tuner File> <Fixture File> <Backport File> <Termination File> """,
    )

    spar = Instrument.measurement(
        "SPARameter?;",
        """ Reads current network S-Parameters and Loss(dB) of one or all control frequencies
            Example: SPAR? """,
    )

    frequency = Instrument.measurement(
        "FREQuency?;",
        """ Displays currently loaded frequency and number of harmonics. """,
    )

    status = Instrument.measurement(
        "STATus?;",
        """ Reports the move status of one or all motors
            Return value=0 ► Tuner is IDLE
            Return value>0 ► Tuner is busy (bit0=carriage, bit 1=probe1, etc…) """,
    )

    position = Instrument.measurement(
        "POSition?;",
        """ Query all files in current setup file.
            Returns: <Setup File> <Tuner File> <Fixture File> <Backport File> <Termination File> """,
    )

    init_status = Instrument.measurement(
        "STATus:INIT?",
        """ Indicates if one of all motors have been initialized. 1 indicates motor has been initialized """,
    )

    limit_status = Instrument.measurement(
        "STATus:INIT?",
        """ Indicates if one of all motors have been initialized. 1 indicates motor has been initialized """,
    )

    termination = Instrument.control(
        "TERMination?;", "TERMination %s;",
        """ Used to query current termination file.
            Sets termination S-parameter block to a .s1p file or directly writes S-parameters of a selected control frequency.
            If .s1p file is loaded freq must be called afterwards to set S-parameters.
            If writing S-parameter data directly freq must be set first.
            Example: term 7mm_term.s1p
        This property can be set.
        """,
        dynamic=True
    )

    termination_spar = Instrument.measurement(
        "TERMination:SPAR?;",
        """ Returns the current termination S-parameters """,
    )

    vswr = Instrument.control(
        "VSWR?;", "VSWR? %d;",
        """ Reports VSWR and Loss.
        Use IDX > 0 to report VSWR at specific control frequency. Blank IDX or IDX=0 reports VSWR for fundamental and all harmonics..
        """,
        dynamic=True
    )

    tune_weight = Instrument.measurement(
        "TUNE:WEIGHT?;",
        """ Reports current tuning weight
            Example: TUNE:WEIGHT 5 .003 1 """,
    )

    dir = Instrument.measurement(
        "DIR?;",
        """ List contents of working directory """,
    )

    def __init__(self, resourceName, description="Maury Microwave Corporation,XT981BL18", **kwargs):
        super().__init__(
            resourceName,
            description,
            **kwargs
        )

    def clear(self):
        """ Clears all settings for calibration, frequencies, and fixture files """
        self.write("CLEAR;")

    def initialize(self):
        """ Initializes individual motor, carriage, or entire tuner.
            Use complete or status command to detect when INIT procedure has finished. """
        self.write("INIT;")

    def set_position(self, motor, position):
        """ Moves motors to target position

            Mot=1 ► Carriage
            Mot=2 ► Low frequency probe
            Mot=3 ► High frequency probe

            Examples:
                POS 1 200 2 4500 3 2000
                POS 2 3000

            param:
                motor: integer that represents the motor
                position: integer that represents the position
        """
        self.write(f"POSition {motor} {position};")

    def set_frequency(self, f1, f2="", f3=""):
        """ Sets tuner control frequency(s).

            FREQ <freqGHz> [nHarm] [nTune] Format for algorithm 2.
            Where freqGHz, is the fundamental frequency, nHarm is the number of harmonics to observe, and nTune is number of harmonics to control.
            Frequency must be a characterized frequency.
            Example: FREQ 1.4 3 3

            FREQ <freqGHz_1> [freqGHz_2] [freqGHz_3] Format for algorithm 3.
            Where freqGHz is a control frequency.
            Example: FREQ 1.4 2.8 4.2

            param:
                f1: floating that represents the control frequency 1 in GHz
                f2: floating that represents the control frequency 2 in GHz
                f3: floating that represents the control frequency 3 in GHz
        """
        self.write(f"FREQuency {f1} {f2} {f3};")

    def stop(self):
        """ Immediately stops all motor operations """
        self.write("STOP;")

    def store_setup(self, filepath):
        """ Save tuner setup file """
        return self.write(f"SETUP:STORE {filepath}")

    def recall_setup(self, filepath):
        """ Load tuner setup file """
        return self.write(f"SETUP:RECALL {filepath}")

    def limit_status(self, carriage):
        """ Reads status of limit switches for selected carriage. 1 indicates limit switch is currently triggered """
        return self.ask(f"STATus:LIMIT? {carriage}")

    def tune(self, mag, phase, mag2="", phase2="", mag3="", phase3=""):
        """ Sets Gamma of FreqIdx (default 1) or of all control frequencies, and moves tuner """
        self.write(f"TUNE {mag} {phase} {mag2} {phase2} {mag3} {phase3}")

    def tune_vswr(self, vswr, phase, vswr2="", phase2="", vswr3="", phase3=""):
        """ Sets VSWR of FreqIdx (default 1) or of all control frequencies, and moves tuner
            Example: TUNE:VSWR 10 120 10 -120 10 0
        """
        self.write(f"TUNE:VSWR {vswr} {phase} {vswr2} {phase2} {vswr3} {phase3}")

    def set_zload(self, r, i, z0=50):
        """
            Set the desired load of the control frequency.
            Example: set_zload(22,-5) ► You should see in the smith chart @ control frequency a real part 22Ω and an imaginary -5Ω
            param:
                r: real part
                i: imaginary part
                z0: characteristic impedance of the line
        """
        z_load = complex(r, i)
        gamma = (z_load-z0)/(z_load+z0)
        mag = abs(gamma)
        phase_rad = atan2(gamma.imag, gamma.real)
        phase_deg = degrees(phase_rad)
        self.tune(mag, phase_deg)

    def tune_weight(self, weight, radius, freq_idx):
        """ Sets index for TUNE and TUNE:VSWR (default 1)
            Example: TUNE:WEIGHT 5 .003 1 """
        self.write(f"TUNE:WEIGHT {weight} {radius} {freq_idx}")

    def reboot(self):
        """Reboot Tuner"""
        self.write("REBOOT;")

