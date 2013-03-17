#!/usr/bin/env python

'''
Client for the state machine server running on an Arduino Due.

TO DO:
- Change welcome message to opcode,size,msg
- The welcome message includes a cut message a the beginning
  but when arduino is reset manually it sends only the right thing.
- Send time (for a schedule wave)
- Send actions

'''

__version__ = '0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2012-10-09'


import serial
import glob
import os
import sys
import time
import struct

SERIAL_PORT_PATH = '/dev/ttyACM0'
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 0.1

# -- COMMANDS --
opcode = {
    'RESET'              : 0x01,     #OBSOLETE
    'OK'                 : 0xaa,
    'CONNECT'            : 0x64,
    'TEST_CONNECTION'    : 0x65,
    'GET_SERVER_VERSION' : 0x09,
    'GET_TIME'           : 0x0a,
    'GET_INPUTS'         : 0x0c,
    'FORCE_OUTPUT'       : 0x16,
    'SET_STATE_MATRIX'   : 0x0d,
    'RUN'                : 0x0b,
    'STOP'               : 0x0e,
    'GET_EVENTS'         : 0x0f,
    'REPORT_STATE_MATRIX': 0x10,
    'GET_CURRENT_STATE'  : 0x11,
    'FORCE_STATE'        : 0x12,
    'SET_STATE_TIMERS'   : 0x13,
    'REPORT_STATE_TIMERS': 0x14,
    'SET_STATE_OUTPUTS'  : 0x15,
    'ERROR'              : 0xff,
}
for k,v in opcode.iteritems():
    opcode[k]=chr(v)

class StateMachineClient(object):
    def __init__(self,connectnow=True):
        '''
        # -- Check if there are multiple serial USB ports --
        allSerialPorts = glob.glob(SERIAL_PORT_PATH)
        if len(allSerialPorts)>1:
            raise
        self.port = allSerialPorts[0]
        '''
        self.port = SERIAL_PORT_PATH
        self.ser = None  # To be created on self.connect()
        if connectnow:
            self.connect()
    def send_reset(self):
        '''Old function necessary for Maple. Obsolete for Arduino'''
        pass
    def connect(self):
        ###self.ser.flushInput()  # FIXME: Why would I need this?
        portReady = False
        fsmReady = False
        while not portReady:  #os.path.exists(self.port):
            try:
                self.ser = serial.Serial(self.port, SERIAL_BAUD,
                                         timeout=SERIAL_TIMEOUT)
                portReady = True
            except serial.SerialException:
                print 'Waiting for Arduino to be ready...'
                time.sleep(1)
        self.ser.setTimeout(1)
        #self.ser.flushOutput()  # FIXME: Discard anything in output buffer?
        #self.ser.flushInput()   # FIXME: Discard anything in input buffer?
        time.sleep(0.2)  # FIXME: why does it need extra time? 0.1 does not work!
        self.ser.write(opcode['CONNECT'])
        while not fsmReady:
            fsmReady = (self.ser.read(1)==opcode['OK'])
            print 'Establishing connection...'
        self.ser.setTimeout(SERIAL_TIMEOUT)
        print 'Connected!'
        #self.ser.flushOutput()
    def test_connection(self):
        self.ser.write(opcode['TEST_CONNECTION'])
        connectionStatus = self.ser.read()
        if connectionStatus==opcode['OK']:
            return 'OK'
        else:
            raise IOError('Connection to state machine was lost.')
            #print 'Connection lost'
    def force_output(self,outputIndex,outputValue):
        self.ser.write(opcode['FORCE_OUTPUT']+chr(outputIndex)+chr(outputValue))
    def get_version(self):
        '''Request version number from server.
        Returns: string
        '''
        self.ser.write(opcode['GET_SERVER_VERSION'])
        versionString = self.ser.readline()
        return versionString.strip()
    def get_inputs(self):
        '''Request values of inputs.
        Returns: string
        '''
        self.ser.flushInput()  ## WHY
        self.ser.write(opcode['GET_INPUTS'])
        #inputValues = self.ser.readlines()
        nInputs = ord(self.ser.read(1))
        inputValuesChr = self.ser.read(nInputs)
        inputValues = [ord(x) for x in inputValuesChr]
        return inputValues
    def get_time(self):
        '''Request server time.
        Returns: string
        '''
        self.ser.write(opcode['GET_TIME'])
        serverTime = self.ser.readline()
        return serverTime.strip()
    def run(self):
        self.ser.write(opcode['RUN'])
    def stop(self):
        self.ser.write(opcode['STOP'])
    def get_events(self):
        '''Request list of events
        Returns: strings (NEEDS MORE DETAIL)
        '''
        self.ser.write(opcode['GET_EVENTS'])
        nEvents = ord(self.ser.read())
        eventsList = []
        for inde in range(nEvents):
            eventsList.append(self.ser.readline())
        return eventsList
    def write(self,value):
        self.ser.write(value)
    def set_state_matrix(self,stateMatrix):
        self.ser.write(opcode['SET_STATE_MATRIX'])
        self.send_matrix(stateMatrix)
    def send_matrix(self,someMatrix):
        nRows = len(someMatrix)
        nCols = len(someMatrix[0])
        self.ser.write(chr(nRows))
        self.ser.write(chr(nCols))
        #print repr(chr(nRows)) ### DEBUG
        #print repr(chr(nCols)) ### DEBUG
        for oneRow in someMatrix:
            for oneItem in oneRow:
                #print repr(chr(oneItem)) ### DEBUG
                self.ser.write(chr(oneItem))
    def set_state_timers(self,timerValues):
        self.ser.write(opcode['SET_STATE_TIMERS'])
        # Send unsigned long ints (4bytes) little endian
        for oneTimerValue in timerValues:
            packedValue = struct.pack('<L',oneTimerValue)
            self.ser.write(packedValue)
    def set_state_outputs(self,stateOutputs):
        '''Each element of stateOutputs must be one byte.
        A future version may include a 'mask' so that the output
        is not changed when entering that state.'''
        self.ser.write(opcode['SET_STATE_OUTPUTS'])
        for outputsOneState in stateOutputs:
            self.ser.write(outputsOneState)
    def report_state_matrix(self):
        self.ser.write(opcode['REPORT_STATE_MATRIX'])
        sm = self.ser.readlines()
        for line in sm:
            print line,
    def get_current_state(self):
        self.ser.write(opcode['GET_CURRENT_STATE'])
        currentState = self.ser.read()
        return ord(currentState)
    def force_state(self,stateID):
        self.ser.write(opcode['FORCE_STATE'])
        self.ser.write(chr(stateID))        
    def report_state_timers(self):
        self.ser.write(opcode['REPORT_STATE_TIMERS'])
        return self.ser.readlines()
    def readlines(self):
        return self.ser.readlines()
    def read(self):
        oneline = self.ser.readlines()
        #print ''.join(oneline)
        print oneline
    def close(self):
        self.stop()
        #for ... force_output() # Force every output to zero
        self.ser.close()
'''
    def send_timers(self,oneTime):
        self.ser.write(chr(SEND_TIMERS))
        self.ser.write('%d\n'%oneTime) # in milliseconds
        
'''


if __name__ == "__main__":
    c = ToyClient()
    #c.set_output(1,1)

    #import time; time.sleep(0.5)
    stateMatrix = [[1,0, 0,0, 0,0, 1] , [0,1, 1,1, 1,1, 0]]
    c.set_state_matrix(stateMatrix)
    c.set_state_timers([1000,500])
    stateOutputs = ['\x00','\xff']
    c.set_state_outputs(stateOutputs)
    c.run()

    sys.exit()

    '''
    # -- Test with a large matrix --
    m=reshape(arange(400)%10,(20,20))
    c.set_state_matrix(m)
    c.report_state_matrix()
    '''

    stateMatrix=[]
    # INPUTS          i1 i2
    #stateMatrix.append([ 1 , 2 ])
    #stateMatrix.append([ 2 , 0 ])
    #stateMatrix.append([ 0 , 1 ])

    # FIXME: there is a limit on the size of the matrix
    #        one due to the number of rows or cols (has to be <128)
    #        another probably due to the serial buffer size

    #stateMatrix.append(range(0,4))
    #stateMatrix.append(range(100,104))
    stateMatrix = [[1,0, 0,0, 0,0, 1] , [0,1, 1,1, 1,1, 0]]
    stateTimers = [200000,1000000] # in microseconds
    #stateMatrix = [[1,0, 1] , [0,1, 0]]
    #stateTimers = [0,0] # in microseconds
    stateOutputs = ['\x00','\xff']

    import time
    time.sleep(0.5)
    c.set_state_matrix(stateMatrix)
    #time.sleep(0.1)
    #print c.readlines()
    c.set_state_timers(stateTimers)
    #time.sleep(0.1)
    #print c.readlines()
    c.set_state_outputs(stateOutputs)
    #time.sleep(0.1)
    unwantedData = c.readlines()
    if unwantedData:
        print unwantedData
    c.run()
    '''
    '''
    #c.send_timers(200)

'''
nRows = len(stateMatrix)
nCols = len(stateMatrix[0])

ser.write(chr(SEND_STATE_MATRIX))
ser.write(chr(nRows))
ser.write(chr(nCols))
for oneRow in stateMatrix:
    for oneItem in oneRow:
        ser.write(chr(oneItem))

ser.write(chr(SEND_STATE_MATRIX))
while not fsmReady:
    oneline = ser.readlines()
    print ''.join(oneline)
    #print oneline
    if oneline[-1]=='STA:READY\r\n':
        break
'''

'''
for ind in range(100):
    oneItem = ser.read()
    print oneItem,
'''



