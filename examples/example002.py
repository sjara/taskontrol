#!/usr/bin/env python

'''
Use schedule waves to alternate between two states.
A state change also occurs on a center port in event.
'''

__author__ = 'Santiago Jaramillo'
__created__ = '2010-12-11'

from taskontrol.core import smclient

testSM = smclient.StateMachineClient('localhost')
testSM.VERBOSE = True

testSM.initialize()

# -- Define schedule waves --
# ID  InEventCol  OutEventCol    DIOline    SoundTrig  Preamble  Sustain  Refraction
# See smclient.setScheduledWavesDIO() for other options
schedwaves = [ [ 0, 6, 7,  4,   0,  0.5, 1.0,  0 ],
               [ 1, 8, 9,  5,   0,  1.0, 0.5,  0 ] ]

#        Ci  Co  Li  Lo  Ri  Ro  SW0u SW0d SW1u SW1d Tup   t   CONTo Sound  SW
mat = [ [ 0,  0,  0,  0,  0,  0,   0,  0,    0,  0,   1,  0.1,   0,    0,   0   ] ,
        [ 2,  1,  1,  1,  1,  1,   1,  2,    1,  1,   1,  100,  2**1,  0,  2**0 ] ,
        [ 1,  2,  2,  2,  2,  2,   2,  2,    2,  1,   2,  100,  2**2,  0,  2**1 ] ]

testSM.setScheduledWavesDIO(schedwaves)
testSM.setStateMatrix(mat)

testSM.run()

print('To stop type: testSM.halt()')
