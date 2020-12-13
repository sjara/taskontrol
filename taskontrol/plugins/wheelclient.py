"""
Client for the rotary encoder server running on an Arduino Uno.

TO DO:
- GET_POSITION waits until the wheel stops
"""

import serial
import struct
import time
import threading
import numpy as np
from taskontrol import rigsettings

SERIAL_PORT_PATH = rigsettings.WHEEL_SENSOR_PORT
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 0.2 #None

DEFAULT_SAMPLING_PERIOD = 0.1

opcode = {
    'OK'                  : 0xaa,
    'RESET'               : 0x01,  # NOT IMPLEMENTED
    'TEST_CONNECTION'     : 0x02,
    'GET_VERSION'         : 0x03,
    'GET_POSITION'        : 0x04,
    'SET_THRESHOLD_MOVE'  : 0x05,
    'GET_THRESHOLD_MOVE'  : 0x06,
    'SET_THRESHOLD_STOP'  : 0x07,
    'GET_THRESHOLD_STOP'  : 0x08,
    'SET_SAMPLING_FACTOR' : 0x09,
    'GET_SAMPLING_FACTOR' : 0x0a,
    'ERROR'               : 0xff,
}
for k,v in opcode.items():
    opcode[k]=bytes([v])


class WheelClient(threading.Thread):
    def __init__(self, samplingPeriod=DEFAULT_SAMPLING_PERIOD):
        """
        Args:
            samplingPeriod (float): how often (in sec) to request position from wheel sensor.
        """
        super().__init__()
        self.running = True
        self.timestamp = []
        self.position = []
        self.samplingPeriod = samplingPeriod
        self.daemon = True  # The program exits when only daemon threads are left.
        self.ser = serial.Serial(SERIAL_PORT_PATH, SERIAL_BAUD, timeout=SERIAL_TIMEOUT)

    def run(self):
        while(self.running):
            (ts, pos) = self.get_position()
            self.timestamp.append(ts)
            self.position.append(pos)
            time.sleep(self.samplingPeriod)

    def append_to_file(self, h5file, currentTrial):
        """
        Create a group in the specified HDF5 file, and store
        timestamps and position.
        """
        (timestamp, position) = self.get_data()
        wheelGroup = h5file.create_group('/wheelSensor')
        dset1 = wheelGroup.create_dataset('timestamp', data=timestamp)
        dset2 = wheelGroup.create_dataset('position', data=position)

    def get_data(self):
        """
        Returns:
            timestamps (np.array): timestamps in seconds (float)
            position (list): position (int64)
        """
        return (np.array(self.timestamp)/1000, np.array(self.position))

    def get_last_sample(self):
        """
        Returns:
            timestamps (np.array): timestamps in seconds (float)
            position (list): position (int64)
        """
        return (self.timestamp[-1]/1000, self.position[-1])
        
    def get_raw_data(self):
        """
        Returns:
            timestamps (list): in milliseconds as int64
            position (list): as int64
        """
        return (self.timestamp, self.position)

    def get_position(self):
        """
        Returns one sample of raw data (timestamp, position) from the wheel sensor.
        Both numbers are int64. Timestamp in milliseconds.
        """
        self.ser.write(opcode['GET_POSITION'])
        oneline = self.ser.readline()
        ts, pos = [int(x) for x in oneline.strip().split(b' ')]
        return (ts, pos)

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
        raise IOError('Connection to the wheel sensor Arduino was lost.')

    def print_serial(self):
        oneline = 'not-empty'
        while oneline:
            oneline = self.ser.readline()
            print(oneline,end='')

    def get_version(self):
        self.running = False
        self.ser.write(opcode['GET_VERSION'])
        valueStr = self.ser.readline()
        self.running = True
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

    def shutdown(self):
        self.running = False
        while(self.is_alive()):
            time.sleep(0.001)
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
