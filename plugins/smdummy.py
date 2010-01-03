#!/usr/bin/env python

'''
State machine client dummy.

TO DO:
- Do I need to define smclient.baseclient.AckError?

'''


__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-12-30'

import time
import random
import numpy as np

class Dummy(object):
    def __init__(self):
        state=0
        

class StateMachineClient(object):

    def __init__(self, host='localhost', port=3333, fsmID=0, 
                                         connectnow=True, verbose=False):
        self.timeOfCreation = time.time()
        self.timeOfLastEvents = self.timeOfCreation
        self.lastTimeOfEvents = 0

    def connect(self):
        print 'DUMMY: Connect state machine client.'

    def initialize(self):
        print 'DUMMY: Initialize state machine.'

    def setStateMatrix(statematrix, pend_sm_swap=False):       
        #print statematrix
        print 'DUMMY: Set state matrix.'

    def readyToStartTrial(self):
        print 'DUMMY: Ready to start trial.'
        
    def getTimeEventsAndState(self,firstEvent):
        #print 'DUMMY: Get time events and state.'
        timeThisTic = time.time()
        etime = timeThisTic-self.timeOfCreation
        state = 0
        if (timeThisTic-self.lastTimeOfEvents)>2:
            self.lastTimeOfEvents = timeThisTic
            mat = np.array([[0,0,etime-0.7,2,0],
                            [2,1,etime-0.6,3,0],
                            [3,-1,etime-0.150,1,0],
                            [1,-1,etime-0.05,0,0]])
        else:
            mat = np.empty((0,5))
        eventcountsince = mat.shape[0]
        allresults = {'etime':etime,'state':state,
                      'eventcount':eventcountsince+firstEvent-1,'events':mat}
        return allresults

    def run(self):
        print 'DUMMY: Run.'

    def halt(self):
        print 'DUMMY: Halt.'

    def forceState(self, state):
        print 'DUMMY: Force state %d.'%state

    def close(self):
        print 'DUMMY: Close.'
