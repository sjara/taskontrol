#!/usr/bin/env python

'''
Run a simple state matrix that alternates between two states.
A state change happens either from a 2 sec timer or from the center port in.
'''

__author__ = 'Santiago Jaramillo'
__created__ = '2010-12-11'

from taskontrol.core import smclient
import numpy as np

testSM = smclient.StateMachineClient('localhost')
testSM.VERBOSE = True

testSM.initialize()

#        Ci  Co  Li  Lo  Ri  Ro  Tout  t   CONTo  Sound
mat = [ [ 0,  0,  0,  0,  0,  0,  1,  0.1,   0,     0 ] ,
        [ 2,  1,  1,  1,  1,  1,  2,  4.0,  2**1,   0 ] ,
        [ 1,  2,  2,  2,  2,  2,  1,  4.0,  2**2,   0 ] ]

mat = np.array(mat)
testSM.setStateMatrix(mat)
testSM.run()

print('To stop type: testSM.halt()')
