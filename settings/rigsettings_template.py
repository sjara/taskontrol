#!/usr/bin/env python

'''
Rig settings: servers name, data folders, etc.

This file is a template, do not modify it.

You should make a copy named 'settings.py' for each rig and change the
appropriate settings on that file.
'''

__version__ = '0.1.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2012-08-28'


STATE_MACHINE_TYPE = 'maple_dummy'
#SOUND_SERVER = STATE_MACHINE_SERVER

DATA_DIR = '/tmp/'

# -- The following must match the state machine settings --
INPUTS = {
    'Cin'  :0,
    'Cout' :1,
    'Lin'  :2,
    'Lout' :3,
    'Rin'  :4,
    'Rout' :5,
    'Tup'  :6,
}

DOUT = {
    'Center Water':1,
    'Center LED'  :2,
    'Left Water'  :4,
    'Left LED'    :8,
    'Right Water' :16,
    'Right LED'   :32,
    'Stim 1'      :64,
    'Stim 2'      :128,
}
