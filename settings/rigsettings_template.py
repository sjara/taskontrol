#!/usr/bin/env python

'''
Rig settings: servers name, data folders, etc.

This file is a template, do not modify it.

You should make a copy named 'settings.py' for each rig and change the
appropriate settings on that file.
'''

__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-26'


STATE_MACHINE_SERVER = 'localhost'
SOUND_SERVER = STATE_MACHINE_SERVER

DATA_DIR = '/tmp/'

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
