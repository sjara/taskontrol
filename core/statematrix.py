#!/usr/bin/env python

'''
State transition matrix with assembler.

Input format:
sma.addState(name='STATENAME', selftimer=3,
             transitions={'EVENT':NEXTSTATE}, actions={'OUTPUT':VALUE})

Output:
#         Ci  Co  Li  Lo  Ri  Ro  Tup  t  CONTo TRIGo
mat = [ [  0,  0,  0,  0,  0,  0,  2,  1.2,  0,   0   ] ,\

'''

__version__ = '0.0.2'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-12-16'


# FIXME: what should be the SelfTimer period?
VERYLONGTIME  = 100    # Time period to stay in a state if nothing happens
VERYSHORTTIME = 0.0001 # Time period before jumping to next state "immediately"

class StateMatrix(object):
    '''
    State transition matrix.

    The default state transition matrix without schedule waves has the
    following columns:
    [ Cin  Cout  Lin  Lout  Rin  Rout  Tup  t  CONTo  TRIGo ]

    Where the first six are for center, left and right ports, the next
    two columns are for the timer transition and its interval, and the
    last two for digital outputs and sounds.

    FIXME: only one 'readystate' can be specified. It should accept many.
    '''
    def __init__(self,readystate=('ready_next_trial',1)):
        self.statesMat = []
        self.statesIndexToName = {}
        self.statesNameToIndex = {}
        self._nextStateInd = 0

        self.schedWavesMat = []
        self.schedWavesIndexToName = {}
        self.schedWavesNameToIndex = {}
        self._nextSchedWaveInd = 0

        # FIXME: These should depend on values from smclient
        # These dictionary is modified if SchedWaves are used.
        self.eventsDict = {'Cin':0,'Cout':1,'Lin':2,'Lout':3,
                           'Rin':4,'Rout':5,'Tup':6}
        self.actionNamesDict = {'Dout':0,'SoundOut':1}
        self.nInputEvents = len(self.eventsDict)-1   # Minus timer
        self.nOutputActions = 2
        self.readyForNextTrialStateName = readystate[0]
        self.readyForNextTrialStateInd = readystate[1]
        self._initMat()


    def _makeDefaultRow(self,stateInd):
        '''Create a transition row for a state.'''
        nSchedWaves = len(self.schedWavesNameToIndex)
        newrow = (self.nInputEvents+2*nSchedWaves)*[stateInd]    # Input events
        newrow.extend([stateInd, VERYLONGTIME])  # Self timer
        newrow.extend(self.nOutputActions*[0])   # Outputs
        if nSchedWaves>0:
            newrow.extend([0])   # One more column for SchedWaves
        return newrow


    def _initMat(self):
        '''Add row for state-zero and ready-next-trial jump state.

        A default state-zero is necessary because as of Dec 2010
        schedule waves cannot be triggered from the zeroth state. This
        was found empirically, and it may be a bug in the server.
        '''
        self._updateStateDict('_STATEZERO',0)
        self._nextStateInd = 1
        if self._nextStateInd==self.readyForNextTrialStateInd:
            self._nextStateInd += 1  # Skip readyForNextTrialState

        self.addState(name='_STATEZERO',selftimer=VERYSHORTTIME,transitions={'Tup':self._nextStateInd})
        self._updateStateDict(self.readyForNextTrialStateName,
                              self.readyForNextTrialStateInd)
        self.addState(name=self.readyForNextTrialStateName,selftimer=VERYLONGTIME)


    def _updateStateDict(self,stateName,stateInd):
        '''Add name and index of a state to the dicts keeping the states list.'''
        self.statesNameToIndex[stateName] = stateInd
        self.statesIndexToName[stateInd] = stateName


    #def _updateSchedWaveDict(self,stateName,stateInd):
    #    '''Add name and index of a schedule wave to the dicts keeping the waves list.'''
    #    self.schedWavesNameToIndex[schedWaveName] = self._nextSchedWaveInd
    #    self.schedWavesIndexToName[self._nextSchedWaveInd] = schedWaveName


    def _appendStateToList(self,stateName):
        '''Add state to the list of available states.'''        
        if self._nextStateInd==self.readyForNextTrialStateInd:
            self._nextStateInd += 1  # Skip readyForNextTrialState
        self._updateStateDict(stateName,self._nextStateInd)
        self._nextStateInd += 1
        

    def _appendSchedWaveToList(self,schedWaveName):
        '''Add schedule wave to the list of available schedule waves.'''        
        self.schedWavesNameToIndex[schedWaveName] = self._nextSchedWaveInd
        self.schedWavesIndexToName[self._nextSchedWaveInd] = schedWaveName
        self._nextSchedWaveInd += 1
        

    def addState(self,name='',selftimer=VERYLONGTIME,transitions={},actions={}):
        '''Add state to transition matrix.'''
        
        nSchedWaves = len(self.schedWavesNameToIndex)
        # -- Find index for this state (create if necessary) --
        if name not in self.statesNameToIndex:
            self._appendStateToList(name)
        thisStateInd = self.statesNameToIndex[name]

        # -- Add target states from specified events --
        NewRow = self._makeDefaultRow(thisStateInd)
        colTimer = self.nInputEvents+2*nSchedWaves+1
        NewRow[colTimer] = selftimer
        for (eventName,targetStateName) in transitions.iteritems():
            if targetStateName not in self.statesNameToIndex:
                self._appendStateToList(targetStateName)
            targetStateInd = self.statesNameToIndex[targetStateName]
            NewRow[self.eventsDict[eventName]] = targetStateInd

        # -- Add output actions --
        for (actionName,actionValue) in actions.iteritems():
            actionColumn = self.actionNamesDict[actionName]+self.nInputEvents+2*nSchedWaves+2
            if actionName=='Dout':
                NewRow[actionColumn] = actionValue
            elif actionName=='SoundOut':
                #NewRow[actionColumn] = actionValue
                print 'CODE FOR SOUND OUTPUT NOT WRITTEN YET (statematrix.addstate)'
            elif actionName=='SchedWaveTrig':
                NewRow[actionColumn] = 2**self.schedWavesNameToIndex[actionValue]
                

        # -- Add row to state transition matrix --
        # FIXME: this way to do it seems very inefficient
        while len(self.statesMat)<(thisStateInd+1):
            self.statesMat.append([])
        self.statesMat[thisStateInd] = NewRow


    def addScheduleWave(self, name='',preamble=0, sustain=0, refraction=0, DIOline=-1, soundTrig=0):
        '''Add a Scheduled Wave to this state machine.

        Example:
          addScheduleWave(self, name='mySW',preamble=1.2)
          self.sm.addState(name='first_state', selftimer=100,
                           transitions={'Cin':'second_state'},
                           actions={'Dout':LeftLED, 'SchedWaveTrig':'mySW'})
          self.sm.addState(name='second_state', selftimer=100,
                           transitions={'mySW_In':'first_state'})

        Note that as currently configured, you can have up to 32
        different scheduled waves defined per state machine, no more.

        From ExperPort/Modules/@StateMachineAssembler/add_scheduled_wave.m

        '''
        # -- Find index for this SW (create if necessary) --
        if name not in self.schedWavesNameToIndex:
            self._appendSchedWaveToList(name)
        swID = self.schedWavesNameToIndex[name]
        (inEventCol,outEventCol) = self._updateEventsDict(name)
        self.schedWavesMat.append([swID, inEventCol, outEventCol, DIOline,
                                   soundTrig, preamble, sustain, refraction])
        self._initMat() # Initialize again with different number of columns


    def _updateEventsDict(self,name):
        '''Add entries to the events dictionary according to the names of
        scheduled waves.'''
        # FIXME: the length of schedWavesNameToIndex may differ from swID+1
        inEventCol = 2*(len(self.schedWavesNameToIndex)-1) + self.nInputEvents
        outEventCol = inEventCol + 1
        self.eventsDict['%s_In'%name] = inEventCol
        self.eventsDict['%s_Out'%name] = outEventCol
        self.eventsDict['Tup'] = outEventCol+1
        if 'SchedWaveTrig' not in self.actionNamesDict:
            self.actionNamesDict['SchedWaveTrig']=2
        return (inEventCol,outEventCol)


    def getMatrix(self):
        # FIXME: check if there are orphan states or calls to nowhere
        return self.statesMat

    def getSchedWaves(self):
        # FIXME: check if there are orphan SW
        return self.schedWavesMat


    def getStatesDict(self,order='NameToIndex'):
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
            else:
                matstr += 'EMPTY ROW'
            matstr += '\n'
        return matstr


if __name__ == "__main__":
    
    sm = StateMatrix()
    sm.addScheduleWave(name='mySW',preamble=1.2)
    sm.addScheduleWave(name='my2SW',sustain=3.3)
    sm.addState(name='wait_for_cpoke', selftimer=10,
                transitions={'Cin':'play_target'})
    sm.addState(name='play_target', selftimer=0.5,
                transitions={'Cout':'wait_for_apoke','Tup':'wait_for_apoke'},
                actions={'Dout':5})
    print sm
    '''
    sm.addState(name='wait_for_apoke', selftimer=0.5,
                transitions={'Lout':'wait_for_cpoke','Rout':'wait_for_cpoke'})

    sm.addState(name='wait_for_cpoke', selftimer=10,
                    transitions={'Cin':'play_target'})
    print sm.statesMat
    sm.addState(name='play_target', selftimer=1,
                    transitions={'Cout':'wait_for_apoke','Tup':'wait_for_apoke'},
                    actions={'Dout':1})
    sm.addState(name='wait_for_apoke', selftimer=1,
                    transitions={'Lin':'reward','Rin':'punish','Tup':'end_of_trial'})
    sm.addState(name='reward', selftimer=1,
                    transitions={'Tup':'end_of_trial'},
                    actions={'Dout':2})
    sm.addState(name='punish', selftimer=1,
                    transitions={'Tup':'end_of_trial'},
                    actions={'Dout':4})
    sm.addState(name='end_of_trial')


    print(sm)
    '''

    ############# FIX THIS ##########

    # TO DO: make sure there are (empty) states until JumpState

'''

I have to add states to the list first, and then look for their
indices to fill up the matrix.


'''
