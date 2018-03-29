#!/usr/bin/env python

'''
Classes for assembling a state transition matrix, timers and outputs.

NOTES:

* The state matrix is represented by a python list (of lists), in which
  each element (row) corresponds to the transitions from one state.
* The state timers are represented as a list of floats.
  One element per state.
* The outputs are represented as a list (of lists). Each element contains
  the outputs for each state as a list of 0 (off), 1 (on) or another integer
  which indicates the output should not be changed from its previous value.


Input format:
sma.add_state(name='STATENAME', statetimer=3,
             transitions={'EVENT':NEXTSTATE},
             outputsOn=[], outputsOff=[])


  OUTPUT WILL CHANGE TO SEPARATE TRANSITION MATRIX AND TIMERS
Output:
#       Ci  Co  Li  Lo  Ri  Ro  Tup
mat = [  0,  0,  0,  0,  0,  0,  2  ]


WRITE DOCUMENTATION ABOUT:
sm.statesNameToIndex
self.eventsDict
 ...

'''


from __future__ import print_function
from taskontrol.core import utils
#from taskontrol.settings import rigsettings
#reload(rigsettings)

__version__ = '0.3'
__author__ = 'Santiago Jaramillo <sjara@uoregon.edu>'

# FIXME: what should be the Statetimer period?
VERYLONGTIME  = 100    # Time period to stay in a state if nothing happens
#VERYSHORTTIME = 0.0001 # Time period before jumping to next state "immediately" OBSOLETE, use 0.
SAMEOUTPUT = 7

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
    def __init__(self,inputs={},outputs={},readystate='readyForNextTrial',extratimers=[]):
        '''
        Args:
            inputs (dict): Labels for inputs. Elements should be of type str:int.
            outputs (dict): Labels for outputs. Elements should be of type str:int.
            readystate (str): name of ready-for-next-trial state.
            extratimers (list): names of extratimers.

        A common use is:
        self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                          outputs=rigsettings.OUTPUTS,
                                          readystate='readyForNextTrial'
                                          extratimers=['mytimer'])
        '''
        self.inputsDict = inputs
        self.outputsDict = outputs

        self.stateMatrix = []
        self.stateTimers = []
        self.stateOutputs = []
        self.serialOutputs = []

        self.statesIndexToName = {}
        self.statesNameToIndex = {}

        self._nextStateInd = 0

        #self.extraTimersIndexToName = {}
        #self.extraTimersNameToIndex = {}
        self.extraTimersNames = []
        #self._nextExtraTimerInd = 0
        self.extraTimersDuration = []
        self.extraTimersTriggers = []

        # This dictionary is modified if ExtraTimers are used.
        self.eventsDict = {}
        for key,val in self.inputsDict.items():
            self.eventsDict[key+'in'] = 2*val
            self.eventsDict[key+'out'] = 2*val+1
        self.eventsDict['Tup'] = len(self.eventsDict)

        self.nInputEvents = len(self.eventsDict)
        self.eventsDict['Forced'] = -1
        self.nOutputs = len(self.outputsDict)

        for onetimer in extratimers:
            self._add_extratimer(onetimer)

        #self.readyForNextTrialStateName = readystate[0]
        #self.readyForNextTrialStateInd = readystate[1]
        self.readyForNextTrialStateName = readystate
        self._init_mat()

    def append_to_file(self,h5file,currentTrial):
        '''Append states definitions to open HDF5 file
        It ignores currentTrial'''
        statematGroup = h5file.create_group('/stateMatrix')
        utils.append_dict_to_HDF5(statematGroup,'eventsNames',self.eventsDict)
        utils.append_dict_to_HDF5(statematGroup,'outputsNames',self.outputsDict)
        utils.append_dict_to_HDF5(statematGroup,'statesNames',self.statesNameToIndex)

        #TODO: save names of extratimers and index corresponding to the event for each.
        #      note that you have to add nInputEvents to the index of each timer.
        #utils.append_dict_to_HDF5(statematGroup,'extraTimersNames',self.extraTimersNameToIndex)

    def _make_default_row(self,stateInd):
        '''Create a transition row for a state.'''
        nExtraTimers = len(self.extraTimersNames)
        newrow = (self.nInputEvents+nExtraTimers)*[stateInd]    # Input events
        return newrow


    def _init_mat(self):
        '''
        Initialize state transition matrix with a row for the readystate.
        '''
        if len(self.stateMatrix)>1:
            raise Exception('You need to create all extra timers before creating any state.')
        self.add_state(name=self.readyForNextTrialStateName,statetimer=VERYLONGTIME)
        # -- Setting outputs off here is not a good idea. Instead we do it in dispatcher --
        #self.add_state(name=self.readyForNextTrialStateName,statetimer=VERYLONGTIME,
        #               outputsOff=self.outputsDict.keys())


    def _force_transition(self,originStateID,destinationStateID):
        '''Set Tup transition from one state to another give state numbers
        instead of state names'''
        self.stateMatrix[originStateID][self.eventsDict['Tup']] = destinationStateID


    def _update_state_dict(self,stateName,stateInd):
        '''Add name and index of a state to the dicts keeping the states list.'''
        self.statesNameToIndex[stateName] = stateInd
        self.statesIndexToName[stateInd] = stateName


    def _append_state_to_list(self,stateName):
        '''Add state to the list of available states.'''
        #if self._nextStateInd==self.readyForNextTrialStateInd:
        #    self._nextStateInd += 1  # Skip readyForNextTrialState
        self._update_state_dict(stateName,self._nextStateInd)
        self._nextStateInd += 1


    def add_state(self, name='', statetimer=VERYLONGTIME, transitions={},
                  outputsOn=[], outputsOff=[], trigger=[], serialOut=0):
        '''Add state to transition matrix.
        outputsOn:
        outputsOff
        trigger: extra-timers trigger when entering this state
        serialOut: integer (1-255) to send through serial port on entering
                      state. A value of zero means no serial output.
        '''

        nExtraTimers = len(self.extraTimersNames)

        # -- Find index for this state (create if necessary) --
        if name not in self.statesNameToIndex:
            self._append_state_to_list(name)
        thisStateInd = self.statesNameToIndex[name]

        # -- Add target states from specified events --
        newRow = self._make_default_row(thisStateInd)
        for (eventName,targetStateName) in transitions.items():
            if targetStateName not in self.statesNameToIndex:
                self._append_state_to_list(targetStateName)
            targetStateInd = self.statesNameToIndex[targetStateName]
            newRow[self.eventsDict[eventName]] = targetStateInd

        # -- Add row to state transition matrix --
        # FIXME: this way to do it seems very inefficient
        while len(self.stateMatrix)<(thisStateInd+1):
            self.stateMatrix.append([])
            self.stateTimers.append([])
            self.stateOutputs.append(self.nOutputs*[SAMEOUTPUT])
            self.serialOutputs.append(0)
        self.stateMatrix[thisStateInd] = newRow
        self.stateTimers[thisStateInd] = statetimer
        for oneOutput in outputsOn:
            outputInd = self.outputsDict[oneOutput]
            self.stateOutputs[thisStateInd][outputInd] = 1
        for oneOutput in outputsOff:
            outputInd = self.outputsDict[oneOutput]
            self.stateOutputs[thisStateInd][outputInd] = 0
        self.serialOutputs[thisStateInd] = serialOut

        # -- Add this state to the list of triggers for extra timers --
        for oneExtraTimer in trigger:
            extraTimerInd = self.extraTimersNames.index(oneExtraTimer)
            self.extraTimersTriggers[extraTimerInd] = thisStateInd
        pass


    def _add_extratimer(self, name, duration=0):
        '''
        Add an extra timer that will be trigger when entering a defined state,
        but can continue after state transitions.
        '''
        if name not in self.extraTimersNames:
            self.extraTimersNames.append(name)
        else:
            raise Exception('Extra timer ({0}) has already been defined.'.format(name))
        extraTimerEventCol = self.nInputEvents + len(self.extraTimersNames)-1
        self.eventsDict[name] = extraTimerEventCol
        #self._init_mat() # Initialize again with different number of columns
        self.extraTimersDuration.append(duration)
        #self.extraTimersTriggers.append(None) # This will be filled by add_state
        # The default trigger for extratimers is state 0. The state machine requires a trigger.
        self.extraTimersTriggers.append(0) # This will be updated by add_state


    def set_extratimer(self, name, duration):
        '''
        Set the duration of an extratimer.
        '''
        if name not in self.extraTimersNames:
            raise Exception('The state matrix has no extratimer called {0}.'.format(name))
        self.extraTimersDuration[self.extraTimersNames.index(name)] = duration

    def get_matrix(self):
        # -- Check if there are orphan states or calls to nowhere --
        maxStateIDdefined = len(self.stateMatrix)-1
        for (stateName,stateID) in self.statesNameToIndex.items():
            if (stateID>maxStateIDdefined) or not len(self.stateMatrix[stateID]):
                raise ValueError('State "{0}" was not defined.'.format(stateName))
        return self.stateMatrix

    def reset_transitions(self):
        #defaultTransitions = self._make_default_row(0) # Default row of the matrix
        for stateind in self.statesIndexToName.keys():
            self.stateMatrix[stateind] = self._make_default_row(stateind)
            self.stateTimers[stateind] = VERYLONGTIME
            self.stateOutputs[stateind] = self.nOutputs*[SAMEOUTPUT]

    def get_outputs(self):
        return self.stateOutputs

    def get_serial_outputs(self):
        return self.serialOutputs

    def get_ready_states(self):
        '''Return names of state that indicate the machine is
        ready to start a new trial '''
        return [self.readyForNextTrialStateName]

    def get_state_timers(self):
        return self.stateTimers

    def get_extra_timers(self):
        return self.extraTimersDuration

    def get_extra_triggers(self):
        return self.extraTimersTriggers

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
        matstr = '\n'
        revEventsDict = {}
        matstr += self._extratimers_as_str()
        for key in self.eventsDict:
            if key!='Forced':
                revEventsDict[self.eventsDict[key]] = key
        matstr += '\t\t\t'
        matstr += '\t'.join([revEventsDict[k][0:4] for k in sorted(revEventsDict.keys())])
        matstr += '\t\tTimers\tOutputs\tSerialOut'
        matstr += '\n'
        for (index,onerow) in enumerate(self.stateMatrix):
            if len(onerow):
                matstr += '{0} [{1}] \t'.format(self.statesIndexToName[index].ljust(16),index)
                matstr += '\t'.join(str(e) for e in onerow)
                matstr += '\t|\t{0:0.2f}'.format(self.stateTimers[index])
                matstr += '\t{0}'.format(self._output_as_str(self.stateOutputs[index]))
                matstr += '\t{0}'.format(self.serialOutputs[index])
            else:
                matstr += 'EMPTY ROW'
            matstr += '\n'
        return matstr

    def _extratimers_as_str(self):
        etstr = ''
        for indt, oneExtratimer in enumerate(self.extraTimersNames):
            if self.extraTimersTriggers[indt] is not None:
                thisTrigger = self.statesIndexToName[self.extraTimersTriggers[indt]]
            else:
                thisTrigger = '[nothing]'
            etstr += '{0}:\t{1:0.2f} triggered by {2}\n'.format(oneExtratimer,
                                                                self.extraTimersDuration[indt],
                                                                thisTrigger)
        return etstr

    def _output_as_str(self,outputVec):
        #outputStr = '-'*len(outputVec)
        outputStr = ''
        for indo,outputValue in enumerate(outputVec):
            if outputValue==1:
                outputStr += '1'
            elif outputValue==0:
                outputStr += '0'
            else:
                outputStr += '-'
        return outputStr

if __name__ == "__main__":
    CASE = 3
    if CASE==1:
        sm = StateMatrix(inputs={'C':0, 'L':1, 'R':2},
                         outputs={'centerWater':0, 'centerLED':1})
        #elif CASE==100:
        sm.add_state(name='wait_for_cpoke', statetimer=12,
                    transitions={'Cin':'play_target'},
                    outputsOff=['centerLED'])
        sm.add_state(name='play_target', statetimer=0.5,
                    transitions={'Cout':'wait_for_apoke','Tup':'wait_for_cpoke'},
                    outputsOn=['centerLED'])
        print(sm)
    elif CASE==2:
        sm = StateMatrix()
        sm.add_schedule_wave(name='mySW',preamble=1.2)
        sm.add_schedule_wave(name='my2SW',sustain=3.3)
        sm.add_state(name='wait_for_cpoke', statetimer=10,
                    transitions={'Cin':'play_target'})
        sm.add_state(name='play_target', statetimer=0.5,
                    transitions={'Cout':'wait_for_apoke','Tup':'wait_for_apoke'},
                    outputs={'Dout':5})
        print(sm)
    elif CASE==3:
        sm = StateMatrix(inputs={'C':0, 'L':1, 'R':2},
                         outputs={'centerWater':0, 'centerLED':1},
                         extratimers=['mytimer','secondtimer'])
        sm.set_extratimer('mytimer', 0.6)
        sm.set_extratimer('secondtimer', 0.3)
        sm.add_state(name='wait_for_cpoke', statetimer=12,
                     transitions={'Cin':'play_target', 'mytimer':'third_state'},
                     outputsOff=['centerLED'],  trigger=['mytimer'])
        print(sm)
    elif CASE==3.5:
        sm = StateMatrix(inputs={'C':0, 'L':1, 'R':2},
                         outputs={'centerWater':0, 'centerLED':1})
        sm.add_extratimer('mytimer', duration=0.6)
        sm.add_extratimer('secondtimer', duration=0.3)
        sm.add_state(name='wait_for_cpoke', statetimer=12,
                     transitions={'Cin':'play_target', 'mytimer':'third_state'},
                     outputsOff=['centerLED'],  trigger=['mytimer'])
        print(sm)
    elif CASE==4:
        sm = StateMatrix()
        sm.add_state(name='wait_for_cpoke', statetimer=12,
                    transitions={'Cin':'play_target','Tup':'play_target'},
                    outputsOff=['CenterLED'])
        sm.add_state(name='play_target', statetimer=0.5,
                    transitions={'Cout':'wait_for_apoke','Tup':'wait_for_cpoke'},
                    outputsOn=['CenterLED'])
        sm.add_state(name='wait_for_apoke', statetimer=0.5,
                    transitions={'Tup':'wait_for_cpoke'},
                    outputsOff=['CenterLED'])
        print(sm)
        sm.get_matrix()
        sm.reset_transitions()
        sm.add_state(name='wait_for_cpoke', statetimer=12,
                    transitions={'Cin':'play_target','Tup':'play_target'},
                    outputsOff=['CenterLED'])
        print(sm)
        sm.get_matrix()
    if CASE==5:
        sm = StateMatrix()
        sm.add_state(name='wait_for_cpoke', statetimer=12,
                    transitions={'Cin':'play_target'},
                    outputsOff=['CenterLED'])
        sm.add_state(name='play_target', statetimer=0.5,
                    transitions={'Cout':'wait_for_apoke','Tup':'wait_for_cpoke'},
                    outputsOn=['CenterLED'], serialOut=1)
        print(sm)

