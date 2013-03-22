#!/usr/bin/env python

'''
Assemble a state transition matrix as well as timers and outputs.

Input format:
sma.add_state(name='STATENAME', statetimer=3,
             transitions={'EVENT':NEXTSTATE},
             outputs={'OUTPUT':VALUE})


  OUTPUT WILL CHANGE TO SEPARATE TRANSITION MATRIX AND TIMERS

Output:
#       Ci  Co  Li  Lo  Ri  Ro  Tup
mat = [  0,  0,  0,  0,  0,  0,  2  ]
      
'''

from taskontrol.settings import rigsettings

__version__ = '0.1.0'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2012-09-03'


# FIXME: what should be the Statetimer period?
VERYLONGTIME  = 100    # Time period to stay in a state if nothing happens
VERYSHORTTIME = 0.0001 # Time period before jumping to next state "immediately"

class StateMatrix(object):
    '''
    State transition matrix.

    The default state transition matrix without extra timers has the
    following columns:
    [ Cin  Cout  Lin  Lout  Rin  Rout  Tup]

    Where the first six are for center, left and right ports, and the
    next column for the state timer.

    FIXME: only one 'readystate' can be specified. It should accept many.
    '''
    #def __init__(self,readystate=('ready_next_trial',1)):
    #def __init__(self):
    def __init__(self,readystate='ready_next_trial'):
        self.statesMat = []
        self.statesTimers = []
        self.statesOutputs = []

        self.statesIndexToName = {}
        self.statesNameToIndex = {}

        self._nextStateInd = 0

        self.schedWavesMat = []
        self.schedWavesIndexToName = {}
        self.schedWavesNameToIndex = {}
        self._nextSchedWaveInd = 0

        # FIXME: These should depend on values from smclient
        # These dictionary is modified if SchedWaves are used.
        self.eventsDict = rigsettings.INPUTS
        self.nInputEvents = len(self.eventsDict)

        #self.outputNamesDict = {'Dout':0,'SoundOut':1}
        #self.nOutputs = 2

        #self.readyForNextTrialStateName = readystate[0]
        #self.readyForNextTrialStateInd = readystate[1]
        self.readyForNextTrialStateName = readystate
        self._initMat()


    def _make_default_row(self,stateInd):
        '''Create a transition row for a state.'''
        #nSchedWaves = len(self.schedWavesNameToIndex)
        #newrow = (self.nInputEvents+2*nSchedWaves)*[stateInd]    # Input events
        newrow = (self.nInputEvents)*[stateInd]    # Input events
        #newrow.extend([stateInd, VERYLONGTIME])  # Self timer
        #newrow.extend(self.nOutputs*[0])   # Outputs
        #if nSchedWaves>0:
        #    newrow.extend([0])   # One more column for SchedWaves
        return newrow


    def _init_mat(self):
        '''Add row for state-zero and ready-next-trial jump state.

        A default state-zero is necessary because as of Dec 2010
        schedule waves cannot be triggered from the zeroth state. This
        was found empirically, and it may be a bug in the server.
        '''
        '''
        self._update_state_dict('_STATEZERO',0)
        self._nextStateInd = 1
        if self._nextStateInd==self.readyForNextTrialStateInd:
            self._nextStateInd += 1  # Skip readyForNextTrialState
        '''
        #self.add_state(name='_STATEZERO',statetimer=VERYSHORTTIME,
        #              transitions={'Tup':self._nextStateInd})
        #self.add_state(name='STATEZERO',statetimer=VERYLONGTIME)
        #self._force_transition(self.statesNameToIndex['_STATEZERO'],self._nextStateInd)
        #self._update_state_dict(self.readyForNextTrialStateName,
        #                      self.readyForNextTrialStateInd)
        self.add_state(name=self.readyForNextTrialStateName,statetimer=VERYLONGTIME)


    def _force_transition(self,originStateID,destinationStateID):
        '''Set Tup transition from one state to another give state numbers
        instead of state names'''
        self.statesMat[originStateID][self.eventsDict['Tup']] = destinationStateID
        
        
    def _update_state_dict(self,stateName,stateInd):
        '''Add name and index of a state to the dicts keeping the states list.'''
        self.statesNameToIndex[stateName] = stateInd
        self.statesIndexToName[stateInd] = stateName


    #def _updateSchedWaveDict(self,stateName,stateInd):
    #    '''Add name and index of a schedule wave to the dicts keeping the waves list.'''
    #    self.schedWavesNameToIndex[schedWaveName] = self._nextSchedWaveInd
    #    self.schedWavesIndexToName[self._nextSchedWaveInd] = schedWaveName


    def _append_state_to_list(self,stateName):
        '''Add state to the list of available states.'''        
        #if self._nextStateInd==self.readyForNextTrialStateInd:
        #    self._nextStateInd += 1  # Skip readyForNextTrialState
        self._update_state_dict(stateName,self._nextStateInd)
        self._nextStateInd += 1
        

    def _append_sched_wave_to_list(self,schedWaveName):
        '''Add schedule wave to the list of available schedule waves.'''        
        self.schedWavesNameToIndex[schedWaveName] = self._nextSchedWaveInd
        self.schedWavesIndexToName[self._nextSchedWaveInd] = schedWaveName
        self._nextSchedWaveInd += 1
        

    def add_state(self,name='',statetimer=VERYLONGTIME,transitions={},outputs={}):
        '''Add state to transition matrix.'''
        
        nSchedWaves = len(self.schedWavesNameToIndex)

        # -- Find index for this state (create if necessary) --
        if name not in self.statesNameToIndex:
            self._append_state_to_list(name)
        thisStateInd = self.statesNameToIndex[name]

        # -- Add target states from specified events --
        newRow = self._make_default_row(thisStateInd)
        colTimer = self.nInputEvents+2*nSchedWaves+1
        #NewRow[colTimer] = statetimer
        for (eventName,targetStateName) in transitions.iteritems():
            if targetStateName not in self.statesNameToIndex:
                self._append_state_to_list(targetStateName)
            targetStateInd = self.statesNameToIndex[targetStateName]
            newRow[self.eventsDict[eventName]] = targetStateInd

        # -- Add output actions --
        '''
        for (actionName,actionValue) in actions.iteritems():
            actionColumn = self.actionNamesDict[actionName]+self.nInputEvents+2*nSchedWaves+2
            if actionName=='Dout':
                NewRow[actionColumn] = actionValue
            elif actionName=='SoundOut':
                #NewRow[actionColumn] = actionValue
                print 'CODE FOR SOUND OUTPUT NOT WRITTEN YET (statematrix.addstate)'
            elif actionName=='SchedWaveTrig':
                NewRow[actionColumn] = 2**self.schedWavesNameToIndex[actionValue]
        '''     

        # -- Add row to state transition matrix --
        # FIXME: this way to do it seems very inefficient
        while len(self.statesMat)<(thisStateInd+1):
            self.statesMat.append([])
            self.statesTimers.append([])
            self.statesOutputs.append([])
        self.statesMat[thisStateInd] = newRow
        self.statesTimers[thisStateInd] = statetimer
        if outputs.has_key('Dout'):
            self.statesOutputs[thisStateInd] = outputs['Dout']
        else:
            self.statesOutputs[thisStateInd] = 0


    def add_schedule_wave(self, name='',preamble=0, sustain=0, refraction=0, DIOline=-1, soundTrig=0):
        '''Add a Scheduled Wave to this state machine.

        Example:
          add_schedule_wave(self, name='mySW',preamble=1.2)
          self.sm.add_state(name='first_state', statetimer=100,
                           transitions={'Cin':'second_state'},
                           actions={'Dout':LeftLED, 'SchedWaveTrig':'mySW'})
          self.sm.add_state(name='second_state', statetimer=100,
                           transitions={'mySW_In':'first_state'})

        Note that as currently configured, you can have up to 32
        different scheduled waves defined per state machine, no more.

        From ExperPort/Modules/@StateMachineAssembler/add_scheduled_wave.m

        '''
        print 'NOT IMPLEMENTED YET'
        return
        # -- Find index for this SW (create if necessary) --
        if name not in self.schedWavesNameToIndex:
            self._append_schedwave_to_list(name)
        swID = self.schedWavesNameToIndex[name]
        (inEventCol,outEventCol) = self._update_events_dict(name)
        self.schedWavesMat.append([swID, inEventCol, outEventCol, DIOline,
                                   soundTrig, preamble, sustain, refraction])
        self._init_mat() # Initialize again with different number of columns


    def _update_events_dict(self,name):
        '''Add entries to the events dictionary according to the names of
        scheduled waves.'''
        # FIXME: the length of schedWavesNameToIndex may differ from swID+1
        inEventCol = 2*(len(self.schedWavesNameToIndex)-1) + self.nInputEvents
        outEventCol = inEventCol + 1
        self.eventsDict['%s_In'%name] = inEventCol
        self.eventsDict['%s_Out'%name] = outEventCol
        self.eventsDict['Tup'] = outEventCol+1
        if 'SchedWaveTrig' not in self.outputNamesDict:
            self.outputNamesDict['SchedWaveTrig']=2
        return (inEventCol,outEventCol)


    def get_matrix(self):
        # FIXME: check if there are orphan states or calls to nowhere
        return self.statesMat

    def get_sched_waves(self):
        # FIXME: check if there are orphan SW
        return self.schedWavesMat


    def get_states_dict(self,order='NameToIndex'):
        '''
        Return mapping between states names and indices.

        'order' can be 'NameToIndex' or 'IndexToName'.
        '''
        if order=='NameToIndex':
            return self.statesNameToIndex
        elif order=='NameToIndex':
            return self.statesIndexToName
        else:
            raise ValueError('Order not valid.')


    def __str__(self):
        '''String representation of transition matrix.'''
        matstr = ''
        revEventsDict = {}
        for key in self.eventsDict:
            revEventsDict[self.eventsDict[key]] = key
        matstr += '\t\t\t'
        matstr += '\t'.join([revEventsDict[k][0:4] for k in sorted(revEventsDict.keys())])
        matstr += '\n'
        for (index,onerow) in enumerate(self.statesMat):
            if len(onerow):
                matstr += '%s [%d] \t'%(self.statesIndexToName[index].ljust(16),index)
                matstr += '\t'.join(str(e) for e in onerow)
                matstr += '\t|\t%0.2f'%self.statesTimers[index]
                matstr += '\t%d'%self.statesOutputs[index]
            else:
                matstr += 'EMPTY ROW'
            matstr += '\n'
        return matstr


if __name__ == "__main__":
    CASE = 1
    if CASE==1:
        sm = StateMatrix()
        #elif CASE==100:
        sm.add_state(name='wait_for_cpoke', statetimer=12,
                    transitions={'Cin':'play_target'})
        sm.add_state(name='play_target', statetimer=0.5,
                    transitions={'Cout':'wait_for_apoke','Tup':'wait_for_cpoke'},
                    outputs={'Dout':rigsettings.OUTPUTS['Center LED']})
        print sm
    elif CASE==2:
        sm = StateMatrix()
        sm.add_schedule_wave(name='mySW',preamble=1.2)
        sm.add_schedule_wave(name='my2SW',sustain=3.3)
        sm.add_state(name='wait_for_cpoke', statetimer=10,
                    transitions={'Cin':'play_target'})
        sm.add_state(name='play_target', statetimer=0.5,
                    transitions={'Cout':'wait_for_apoke','Tup':'wait_for_apoke'},
                    outputs={'Dout':5})
        print sm
    '''
    sm.add_state(name='wait_for_apoke', statetimer=0.5,
                transitions={'Lout':'wait_for_cpoke','Rout':'wait_for_cpoke'})

    sm.add_state(name='wait_for_cpoke', statetimer=10,
                    transitions={'Cin':'play_target'})
    print sm.statesMat
    sm.add_state(name='play_target', statetimer=1,
                    transitions={'Cout':'wait_for_apoke','Tup':'wait_for_apoke'},
                    outputs={'Dout':1})
    sm.add_state(name='wait_for_apoke', statetimer=1,
                    transitions={'Lin':'reward','Rin':'punish','Tup':'end_of_trial'})
    sm.add_state(name='reward', statetimer=1,
                    transitions={'Tup':'end_of_trial'},
                    outputs={'Dout':2})
    sm.add_state(name='punish', statetimer=1,
                    transitions={'Tup':'end_of_trial'},
                    outputs={'Dout':4})
    sm.add_state(name='end_of_trial')


    print(sm)
    '''

    ############# FIX THIS ##########

    # TO DO: make sure there are (empty) states until JumpState

'''

I have to add states to the list first, and then look for their
indices to fill up the matrix.


'''
