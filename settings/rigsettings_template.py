#!/usr/bin/env python

'''
This script defines the names of inputs and outputs, the type of state
machine and sound server, the data directories, and other parameters.

*This file is a template, do not modify it.* Make a copy of this file
and name it 'rigsettings.py'. Modify this new file to define the
appropriate settings for the rig.

'''

__version__ = '0.2'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2013-03-18'


#: Type of state machine. Either 'arduino_due' or 'dummy'
#STATE_MACHINE_TYPE = 'arduino_due'
#STATE_MACHINE_TYPE = 'dummy'
STATE_MACHINE_TYPE = 'emulator'

#: Serial port for the state machine.
STATE_MACHINE_PORT = '/dev/ttyACM0'

#: Parameters for the sound server.
SOUND_SERVER = {'port':'/dev/ttyACM1',
                'baudRate':115200,
                'soundCard':'hw:0',
                'samplingRate':96000, 
                'nChannels':2,
                'bufferSize':128,
                'realtime':True}

_ignore=0
'''
Testing

SOUND_SERVER_SERIAL_PORT = '/dev/ttyACM1'
#SOUND_SERVER_PYRO_PORT = 9124

SOUND_CARD = 'hw:0'
SAMPLING_RATE = 41000
N_CHANNELS = 2
BUFFER_SIZE = 128
REALTIME = False
'''



DATA_DIR = '/tmp/'
REMOTE_DIR = 'localhost://tmp/remote'

DEFAULT_PARAMSFILE = './params.py'

#: Name for each input line.
# -- The following must match the state machine settings --
INPUTS = {
    'C'  :0,
    'L'  :1,
    'R'  :2,
}

#: Name for each output line.
OUTPUTS = {
    'centerWater':0,
    'centerLED'  :1,
    'leftWater'  :2,
    'leftLED'    :3,
    'rightWater' :4,
    'rightLED'   :5,
    'stim1'      :6,
    'stim2'      :7,
}

'''
OUTPUTS = {
    'CenterWater':0,
    'CenterLED'  :1,
    'LeftWater'  :2,
    'LeftLED'    :3,
    'RightWater' :4,
    'RightLED'   :5,
#    'Stim1'      :6,
#    'Stim2'      :7,
    'Stim3'      :8,
}
'''

