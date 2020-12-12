'''
Client for the rotary encoder server running on an Arduino Uno.
'''

import sys
import serial
import struct
import time
import numpy as np

SERIAL_PORT_PATH = '/dev/ttyACM0'
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 0.2 #None

opcode = {
    'OK'                  : 0xaa,
    'RESET'               : 0x01,  # NOT IMPLEMENTED
    'TEST_CONNECTION'     : 0x02,
    'GET_POSITION'        : 0x03,
    'GET_INTERVAL'        : 0x04,
    'GET_SPEED'           : 0x05,
    'SET_THRESHOLD_MOVE'  : 0x06,
    'GET_THRESHOLD_MOVE'  : 0x07,
    'SET_THRESHOLD_STOP'  : 0x08,
    'GET_THRESHOLD_STOP'  : 0x09,
    'SET_SAMPLING_FACTOR' : 0x0a,
    'GET_SAMPLING_FACTOR' : 0x0b,
    'SET_N_PERIODS'       : 0x0c,
    'GET_N_PERIODS'       : 0x0d,
    'GET_VERSION'         : 0x0e,
    'GET_TICK_TIMES'      : 0x0f,
    'RUN'                 : 0xee,
    'SET_DEBUG_MODE'      : 0xf0,
    'ERROR'               : 0xff,
}
for k,v in opcode.items():
    opcode[k]=bytes([v])


class WheelClient(object):
    def __init__(self, connectnow=True):
        '''Wheel sensor client for the Arduino Due.'''
        self.ser = serial.Serial(SERIAL_PORT_PATH, SERIAL_BAUD, timeout=SERIAL_TIMEOUT)
        #self.tickTimes = np.array([],dtype=int)
        
    def test_connection(self):
        """
        Clear serial buffer and test whether connection to wheel sensor is alive.
        Returns 'OK' if connection is alive.
        """
        print('Testing connection to wheelsensor...', end='', flush=True)
        self.ser.readlines()
        for attempt in range(10):
            self.ser.write(opcode['TEST_CONNECTION'])
            connectionStatus = self.ser.read()
            if connectionStatus==opcode['OK']:
                print(' Ready.')
                return 'OK'
            time.sleep(0.01)
            print('.', end='', flush=True)
            #print(f'{attempt}: {connectionStatus}')
        raise IOError('Connection to the wheel sensor Arduino was lost.')
            

    def print_serial(self):
        oneline = 'not-empty'
        while oneline:
            oneline = self.ser.readline()
            print(oneline,end='')
            
    def get_version(self):
        self.ser.write(opcode['GET_VERSION'])
        valueStr = self.ser.readline()
        return valueStr.strip()
    
    def set_threshold_move(self, value):
        self.ser.write(opcode['SET_THRESHOLD_MOVE'])
        packedValue = struct.pack('<B',value)
        self.ser.write(packedValue)
    def get_threshold_move(self):
        self.ser.write(opcode['GET_THRESHOLD_MOVE'])
        valueStr = self.ser.readline()
        return int(valueStr.strip())
    def set_threshold_stop(self, value):
        self.ser.write(opcode['SET_THRESHOLD_STOP'])
        packedValue = struct.pack('<B',value)
        self.ser.write(packedValue)
    def get_threshold_stop(self):
        self.ser.write(opcode['GET_THRESHOLD_STOP'])
        valueStr = self.ser.readline()
        return int(valueStr.strip())
    def set_sampling_factor(self, value):
        self.ser.write(opcode['SET_SAMPLING_FACTOR'])
        packedValue = struct.pack('<B',value)
        self.ser.write(packedValue)
    def set_n_periods(self, value):
        self.ser.write(opcode['SET_N_PERIODS'])
        packedValue = struct.pack('<B',value)
        self.ser.write(packedValue)
    def set_debug_mode(self, value):
        self.ser.write(opcode['SET_DEBUG_MODE'])
        packedValue = struct.pack('<B',value)
        self.ser.write(packedValue)

    def run(self):
        self.ser.write(opcode['RUN'])
        
    def close(self):
        self.ser.close()
        

if __name__ == '__main__':
    #samplingPeriod = 20   # In milliseconds
    #nPeriods = 5          # WINDOW = samplingPeriod*nPeriods
    #thresholdMove = int(0.15 * nPeriods*samplingPeriod)
    #print('thresholdMove = {}'.format(thresholdMove))
    
    wheelclient = WheelClient()
    #wheelclient.print_serial()
    time.sleep(0.4)
    wheelclient.set_threshold_move(10)
    wheelclient.set_threshold_stop(2)
    wheelclient.set_n_periods(1)
    wheelclient.set_sampling_factor(2)
    wheelclient.set_debug_mode(0)
    wheelclient.run()
    while(1):
        oneline = wheelclient.ser.readline()
        #if oneline:
        #    print(oneline,end='')
        if oneline.strip():
            ts, val = [int(x) for x in oneline.strip().split(b' ')]
            if 1:
                print(f'{ts}:\t {val}')
            else:
                if val>0:
                    print(val*'+')
                else:
                    print(abs(val)*'-')
