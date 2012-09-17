#!/usr/bin/env python

'''
State machine client dummy.

TO DO:
'''


__version__ = '0.1.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2012-08-20'

import time
import numpy as np
import datetime


class StateMachineClient(object):

    def __init__(self, connectnow=True, verbose=False):
        self.timeOfCreation = time.time()
        self.timeOfLastEvents = self.timeOfCreation
        self.lastTimeOfEvents = 0
        self.serverTime = 0
        self.state = 0
        self.lastEvents = []
    def send_reset(self):
        pass
    def connect(self):
        print 'DUMMY: Connect.'
        pass
    def set_output(self,output,value):
        pass
    def get_version(self):
        pass
    def get_inputs(self):
        pass
    def get_time(self):
        self.serverTime = datetime.datetime.now().second  ######## DEBUG ##########
        return self.serverTime
    def run(self):
        print 'DUMMY: Run.'
    def stop(self):
        print 'DUMMY: Stop.'
    def get_events(self):
        self.serverTime = datetime.datetime.now().second  ######## DEBUG ##########
        self.state = int(not self.state)
        self.lastEvents = [self.serverTime,1234,self.state]
        return self.lastEvents
    def write(self,value):
        pass
    def set_state_matrix(self,stateMatrix):
        print 'DUMMY: Set state matrix.'
    def set_state_outputs(self,stateOutputs):
        print 'DUMMY: Set state outputs.'
    def set_state_outputs(self,stateTimers):
        print 'DUMMY: Set state timers.'
    def send_matrix(self,someMatrix):
        pass
    def set_state_timers(self,timerValues):
        pass
    def set_state_outputs(self,stateOutputs):
        pass
    def report_state_matrix(self):
        pass
    def get_current_state(self):
        pass
    def force_state(self,stateID):
        print 'DUMMY: Force state %d.'%stateID
    def report_state_timers(self):
        pass
    def readlines(self):
        pass
    def read(self):
        pass
    def close(self):
        print 'DUMMY: Close.'




'''
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

    def bypassDout(self,dout):
        pass

    def run(self):
        print 'DUMMY: Run.'

    def halt(self):
        print 'DUMMY: Halt.'

    def forceState(self, state):
        print 'DUMMY: Force state %d.'%state

    def close(self):
        print 'DUMMY: Close.'
'''
