import serial
import numpy as np
import pyvisa

def findPorts(): # function to find ports
    portList = []
    for i in range(100):
        try:
            comT = 'COM' + str(i)
            ser = serial.Serial(comT, 9600)
            ser.close()
            portList.append(comT)
        except:
            pass
    rm = pyvisa.ResourceManager()
    visa_ad = rm.list_resources()
    ports = np.concatenate((portList, visa_ad), axis=0)
    return ports

class keysightE60102B:

    def __init__(self, com = None):
        self.functions = {
            'IDN': '*IDN?',
            'RST': '*RST',
            'OUTP_ON': ':OUTP ON',
            'OUTP_OFF': ':OUTP OFF',
            'SET_VOLT': ':VOLT {:.2f}',
            'SET_CURR': ':CURR {:.2f}',
            'GET_VOLT': ':VOLT?',
            'GET_CURR': ':CURR?',
            'MEAS_VOLT': ':MEAS:VOLT?',
            'MEAS_CURR': ':MEAS:CURR?',
            'SYS_ERR': ':SYST:ERR?'
        }

        self.ser = None
        self.COM = com
        self.response = ""
        self.voltage = 0
        self.current = 0
        self.state = 'OFF'




    def connect(self):
        rm = pyvisa.ResourceManager()
        self.ser = rm.open_resource(self.COM)
        self.voltage = self.sendRead_command(self.functions['GET_VOLT'])
        self.current = self.sendRead_command(self.functions['GET_CURR'])

    def sendRead_command(self, command):
        response = self.ser.query(command)
        self.response = response
        return response
    def send_command(self, command):
        self.ser.write(command)


    def setVoltage(self,voltage):
        self.send_command(self.functions['SET_VOLT'].format(float(voltage)))
        self.voltage = self.sendRead_command(self.functions['GET_VOLT'])
        self.current = self.sendRead_command(self.functions['GET_CURR'])

    def setCurrent(self,current):
        self.send_command(self.functions['SET_CURR'].format(float(current)))
        self.voltage = self.sendRead_command(self.functions['GET_VOLT'])
        self.current = self.sendRead_command(self.functions['GET_CURR'])

    def reset(self):
        self.send_command(self.functions['IDN'])

    def outputOn(self):
        self.send_command(self.functions['OUTP_ON'])
        self.voltage = self.sendRead_command(self.functions['GET_VOLT'])
        self.current = self.sendRead_command(self.functions['GET_CURR'])
        self.state = 'ON'

    def outputOff(self):
        self.send_command(self.functions['OUTP_OFF'])
        self.voltage = 0#self.sendRead_command(self.functions['GET_VOLT'])
        self.current = 0#self.sendRead_command(self.functions['GET_CURR'])
        self.state = 'OFF'









# COM = 'USB0::0x2A8D::0x1502::MY61002508::0::INSTR'
#
# ports = findPorts()
# # ser = connect('USB0::0x2A8D::0x1502::MY61002508::0::INSTR')
# # response = send_command(ser, '*IDN?')
#
# ps = keysightE60102B(com = COM)
# ps.connect()
# message = ps.sendRead_command('*IDN?')
#
#
# ps.setVoltage(voltage= 3.3)
# ps.setCurrent(current= 0.2)
# # ps.outputOn()
# print(ps.voltage)
# print(ps.current)
# print(response)
