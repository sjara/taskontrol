#!/usr/bin/env python

'''
State transition matrix with assembler.

Input format:
sma.addState(name='STATENAME', selftimer=3,
             transitions={'EVENT':NEXTSTATE}, actions={'OUTPUT':VALUE})

Output:
#         Ci  Co  Li  Lo  Ri  Ro  Tout  t  CONTo TRIGo
mat = [ [  0,  0,  0,  0,  0,  0,  2,  1.2,  0,   0   ] ,\

'''

__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-12-16'


# FIXME: what should be the SelfTimer period?
VERYLONGTIME = 100   # Period to stay in a state if nothing happens

class StateMatrix(object):
    '''
    State transition matrix.

    The default state transition matrix without schedule waves has the
    following columns:
    [ Cin  Cout  Lin  Lout  Rin  Rout  Tout  t  CONTo  TRIGo ]

    Where the first six are for center, left and right ports, the next
    two columns are for the timer transition and its interval, and the
    last two for digital outputs and sounds.
    '''
    def __init__(self,readystate=('ready_next_trial',1)):
        self.pymat = [[]]
        self.statesIndexToName = {}
        self.statesNameToIndex = {}
        self._nextStateInd = 0
        # FIXME: These should depend on values from smclient
        self.eventsDict = {'Cin':0,'Cout':1,'Lin':2,'Lout':3,
                           'Rin':4,'Rout':5,'Tout':6}
        self.actionNamesDict = {'DOut':0,'SoundOut':1}
        self.nInputEvents = len(self.eventsDict)-1   # Minus timer
        self.nOutputActions = 2
        self.readyForNextTrialStateName = readystate[0]
        self.readyForNextTrialStateInd = readystate[1]
        self._initMat()


    def _makeDefaultRow(self,stateInd):
        '''Create a transition row for a state.'''
        newrow = self.nInputEvents*[stateInd]    # Input events
        newrow.extend([stateInd, VERYLONGTIME])  # Self timer
        newrow.extend(self.nOutputActions*[0])   # Outputs
        return newrow

    def _initMat(self):
        '''Add row for state zero and ready-next-trial jump state.'''
        #StateZeroRow = self._makeDefaultRow(self.readyForNextTrialState)
        #StateZeroRow[IndexOfTimer] = VERYSHORTTIME
        #self._updateStateDict('_STATEZERO',0)
        JumpStateRow = self._makeDefaultRow(self.readyForNextTrialStateInd)
        self._updateStateDict(self.readyForNextTrialStateName,
                              self.readyForNextTrialStateInd)
        self.pymat.insert(self.readyForNextTrialStateInd,JumpStateRow)


    def _updateStateDict(self,stateName,stateInd):
        '''Add name and index of a state to the dicts keeping the states list.'''
        self.statesNameToIndex[stateName] = stateInd
        self.statesIndexToName[stateInd] = stateName


    def _appendStateToList(self,stateName):
        '''Add state to the list of available states.'''        
        if self._nextStateInd==self.readyForNextTrialStateInd:
            self._nextStateInd += 1  # Skip readyForNextTrialState
        self._updateStateDict(stateName,self._nextStateInd)
        self._nextStateInd += 1
        

    def addState(self,name='',selftimer=VERYLONGTIME,transitions={},actions={}):
        '''Add state to transition matrix.'''
        
        # -- Find index for this state (create if necessary) --
        if name not in self.statesNameToIndex:
            self._appendStateToList(name)
        thisStateInd = self.statesNameToIndex[name]

        # -- Add target states from specified events --
        NewRow = self._makeDefaultRow(thisStateInd)
        NewRow[self.nInputEvents+1] = selftimer
        for (eventName,targetStateName) in transitions.iteritems():
            if targetStateName not in self.statesNameToIndex:
                self._appendStateToList(targetStateName)
            targetStateInd = self.statesNameToIndex[targetStateName]
            NewRow[self.eventsDict[eventName]] = targetStateInd

        # -- Add output actions --
        for (actionName,actionValue) in actions.iteritems():
            ActionColumn = self.actionNamesDict[actionName]+self.nInputEvents+2
            NewRow[ActionColumn] = actionValue

        # -- Add row to state transition matrix --
        # IMPROVE: seems very inefficient
        while len(self.pymat)<(thisStateInd+1):
            self.pymat.append([])
        self.pymat[thisStateInd] = NewRow


    def getMatrix(self):
        # FIXME: check if there are orphan states or calls to nowhere
        return self.pymat


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
        for (index,onerow) in enumerate(self.pymat):
            matstr += '%s [%d] \t'%(self.statesIndexToName[index].ljust(16),index)
            matstr += '\t'.join(str(e) for e in onerow)
            matstr += '\n'
        return matstr


if __name__ == "__main__":

    
    sm = StateMatrix()
    '''
    sm.addState(name='wait_for_cpoke', selftimer=10,
                transitions={'Cin':'play_target'})
    sm.addState(name='play_target', selftimer=0.5,
                transitions={'Cout':'wait_for_apoke','Tout':'wait_for_apoke'},
                actions={'DOut':5})
    sm.addState(name='wait_for_apoke', selftimer=0.5,
                transitions={'Lout':'wait_for_cpoke','Rout':'wait_for_cpoke'})
    '''
    sm.addState(name='wait_for_cpoke', selftimer=10,
                    transitions={'Cin':'play_target'})
    sm.addState(name='play_target', selftimer=1,
                    transitions={'Cout':'wait_for_apoke','Tout':'wait_for_apoke'},
                    actions={'DOut':1})
    sm.addState(name='wait_for_apoke', selftimer=1,
                    transitions={'Lin':'reward','Rin':'punish','Tout':'end_of_trial'})
    sm.addState(name='reward', selftimer=1,
                    transitions={'Tout':'end_of_trial'},
                    actions={'DOut':2})
    sm.addState(name='punish', selftimer=1,
                    transitions={'Tout':'end_of_trial'},
                    actions={'DOut':4})
    sm.addState(name='end_of_trial')


    print(sm)

    ############# FIX THIS ##########

    # TO DO: make sure there are (empty) states until JumpState

'''

I have to add states to the list first, and then look for their
indices to fill up the matrix.


'''
