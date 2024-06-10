#    Author: Carlos Pinzon
#    Date: 6/10/2024
#    ATS 545 command module
#   Note: managing stabilizing time externally, it may vary depending on the test to execute


import time
import numpy as np
import pandas as pd
import pyvisa
import serial

class ATS545:

    def __init__(self, com = None):
        self.COM = com
        self.temperature = 25
        self.commands = {
            'IDN' : '*IDN?',
            'RST' : '*RST',
            'SET_TEMP' : 'SETP',
            'FLOW_ON' : 'FLOW {}'.format(1),
            'FLOW_OFF': 'FLOW {}'.format(0),
            'MEAS_TEMP' : 'TEMP?'
        }

    def connect(self):
        self.rm = pyvisa.ResourceManager()
        self.thermostream = self.rm.open_resource(self.COM)
        print(self.thermostream.query(self.commands['IDN']))

    def sendRead_command(self,command):
        response = self.thermostream.query(command)

    def setTemperature(self, temperature = 25):
        self.temperature = temperature
        command = self.commands['SET_TEMP']+str(temperature)
        self.thermostream.write(command.encode())

    def readTemp(self):
        temperature = self.thermostream.query(self.commands['MEAS_TEMP'])
        return temperature

    def flowOn(self):
        self.thermostream.write(self.commands['FLOW_ON'])

    def flowOff(self):
        self.thermostream.write(self.commands['Flow_OFF'])
