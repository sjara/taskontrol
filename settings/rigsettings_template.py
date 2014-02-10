#!/usr/bin/env python

'''
Rig settings: servers name, data folders, etc.

This file is a template, do not modify it.

You should make a copy named 'settings.py' for each rig and change the
appropriate settings on that file.
'''

__version__ = '0.2'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2013-03-18'


#STATE_MACHINE_TYPE = 'dummy'
STATE_MACHINE_TYPE = 'arduino_due'

#SOUND_SERVER = STATE_MACHINE_SERVER

DATA_DIR = '/tmp/'

# -- The following must match the state machine settings --
INPUTS = {
    'C'  :0,
    'L'  :1,
    'R'  :2,
}

OUTPUTS = {
    'CenterWater':0,
    'CenterLED'  :1,
    'LeftWater'  :2,
    'LeftLED'    :3,
    'RightWater' :4,
    'RightLED'   :5,
    'Stim1'      :6,
    'Stim2'      :7,
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

