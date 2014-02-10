'''
Create a frequency discrimination 2AFC paradigm.
'''

import numpy as np
from taskontrol.core import paramgui
from PySide import QtGui 
from taskontrol.core import arraycontainer

from taskontrol.plugins import templates
reload(templates)

class Paradigm(templates.Paradigm2AFC):
    def __init__(self,parent=None):
        super(Paradigm, self).__init__(parent,dummy=0)

         # -- Add parameters --
        self.params['timeWaterValveL'] = paramgui.NumericParam('Time valve left',value=0.02,
                                                               group='Water delivery')
        self.params['timeWaterValveC'] = paramgui.NumericParam('Time valve center',value=0.02,
                                                               group='Water delivery')
        self.params['timeWaterValveR'] = paramgui.NumericParam('Time valve right',value=0.02,
                                                               group='Water delivery')
        waterDelivery = self.params.layout_group('Water delivery')
        
        self.params['outcomeMode'] = paramgui.MenuParam('Outcome mode',
                                                        ['sides direct','direct','on next correct',
                                                         'only if correct'],
                                                        value=1,group='Choice parameters')
        choiceParams = self.params.layout_group('Choice parameters')

        self.params['targetDuration'] = paramgui.NumericParam('Target Duration',value=0.5,
                                                        group='Timing Parameters')
        timingParams = self.params.layout_group('Timing Parameters')

        # -- Add graphical widgets to main window --
        self.centralWidget = QtGui.QWidget()
        layoutMain = QtGui.QVBoxLayout()
        layoutTop = QtGui.QVBoxLayout()
        layoutBottom = QtGui.QHBoxLayout()
        layoutCol1 = QtGui.QVBoxLayout()
        layoutCol2 = QtGui.QVBoxLayout()

        
        layoutMain.addLayout(layoutTop)
        #layoutMain.addStretch()
        layoutMain.addSpacing(0)
        layoutMain.addLayout(layoutBottom)

        layoutTop.addWidget(self.mySidesPlot)

        layoutBottom.addLayout(layoutCol1)
        layoutBottom.addLayout(layoutCol2)

        layoutCol1.addWidget(self.saveData)
        layoutCol1.addWidget(self.sessionInfo)
        layoutCol1.addWidget(self.dispatcherView)
        
        layoutCol2.addWidget(self.manualControl)
        layoutCol2.addWidget(waterDelivery)
        layoutCol2.addWidget(choiceParams)
        layoutCol2.addWidget(timingParams)
        layoutCol2.addStretch()

        self.centralWidget.setLayout(layoutMain)
        self.setCentralWidget(self.centralWidget)

        # -- Add variables for storing results --
        maxNtrials = 4000 # Preallocating space for each vector makes things easier
        self.results = arraycontainer.Container()
        self.results.labels['rewardSide'] = {'left':0,'right':1}
        self.results['rewardSide'] = np.random.randint(2,size=maxNtrials)
        self.results.labels['choice'] = {'left':0,'right':1,'none':2}
        self.results['choice'] = np.empty(maxNtrials,dtype=int)
        self.results.labels['outcome'] = {'correct':1,'error':0,'invalid':2,'free':3,'aborted':4}
        self.results['outcome'] = np.empty(maxNtrials,dtype=int)
        self.results['timeTrialStart'] = np.empty(maxNtrials,dtype=float)
        self.results['timeCenterIn'] = np.empty(maxNtrials,dtype=float)
        self.results['timeCenterOut'] = np.empty(maxNtrials,dtype=float)
        self.results['timeSideIn'] = np.empty(maxNtrials,dtype=float)

         # -- Prepare first trial --
        self.prepare_next_trial(0)
       

    def prepare_next_trial(self, nextTrial):
        self.params.update_history()

        # -- Prepare next trial --
        nextCorrectChoice = self.results['rewardSide'][nextTrial]
        self.set_state_matrix(nextCorrectChoice)
        self.dispatcherModel.ready_to_start_trial()

        # -- Calculate results from last trial (update outcome, choice, etc) --
        if nextTrial>0:
            self.calculate_results(nextTrial-1)

        # -- Update sides plot --
        self.mySidesPlot.update(self.results['rewardSide'],self.results['outcome'],nextTrial)


    def set_state_matrix(self,nextCorrectChoice):
        self.sm.reset_transitions()

        targetDuration = self.params['targetDuration'].get_value()
        if nextCorrectChoice==self.results.labels['rewardSide']['left']:
            rewardDuration = self.params['timeWaterValveL'].get_value()
            stimOutput = 'LeftLED'
            fromChoiceL = 'reward'
            fromChoiceR = 'punish'
            rewardOutput = 'LeftWater'
            sideIn = 'Lin'
        elif nextCorrectChoice==self.results.labels['rewardSide']['right']:
            rewardDuration = self.params['timeWaterValveR'].get_value()
            stimOutput = 'RightLED'
            fromChoiceL = 'punish'
            fromChoiceR = 'reward'
            rewardOutput = 'RightWater'
            sideIn = 'Rin'
        else:
            raise ValueError('Value of nextCorrectChoice is not appropriate')

        # -- Set state matrix --
        outcomeMode = self.params['outcomeMode'].get_string()
        if outcomeMode=='sides direct':
            self.sm.add_state(name='start_trial', statetimer=0,
                              transitions={'Tup':'wait_for_cpoke'})
            self.sm.add_state(name='wait_for_cpoke', statetimer=10,
                              transitions={'Cin':'play_stimulus',sideIn:'play_stimulus'})
            self.sm.add_state(name='play_stimulus', statetimer=targetDuration,
                              transitions={'Tup':'reward'},
                              outputsOn=[stimOutput])
            self.sm.add_state(name='reward', statetimer=rewardDuration,
                              transitions={'Tup':'stopReward'},
                              outputsOn=[rewardOutput],
                              outputsOff=[stimOutput])
            self.sm.add_state(name='stopReward', statetimer=0,
                              transitions={'Tup':'ready_next_trial'},
                              outputsOff=[rewardOutput])
        elif outcomeMode=='direct':
            self.sm.add_state(name='start_trial', statetimer=0,
                              transitions={'Tup':'wait_for_cpoke'})
            self.sm.add_state(name='wait_for_cpoke', statetimer=2,
                              transitions={'Cin':'play_stimulus'})
            self.sm.add_state(name='play_stimulus', statetimer=targetDuration,
                              transitions={'Tup':'reward'},
                              outputsOn=[stimOutput])
            self.sm.add_state(name='reward', statetimer=rewardDuration,
                              transitions={'Tup':'stopReward'},
                              outputsOn=[rewardOutput],
                              outputsOff=[stimOutput])
            self.sm.add_state(name='stopReward', statetimer=0,
                              transitions={'Tup':'ready_next_trial'},
                              outputsOff=[rewardOutput])
        elif outcomeMode=='on next correct':
            self.sm.add_state(name='start_trial', statetimer=1,
                              transitions={'Tup':'ready_next_trial'})


            ########### CONTINUE HERE ############


        elif outcomeMode=='only if correct':
            self.sm.add_state(name='start_trial', statetimer=1,
                              transitions={'Tup':'ready_next_trial'})
        else:
            raise TypeError('outcomeMode={0} has not been implemented'.format(outcomeMode))
        print self.sm ### DEBUG
        self.dispatcherModel.set_state_matrix(self.sm)


    def calculate_results(self,trialIndex):
        eventsThisTrial = self.dispatcherModel.events_one_trial(trialIndex)
        print '===== Trial {0} ====='.format(trialIndex)
        print eventsThisTrial

        '''
        # -- Find beginning of trial --
        startTrialStateID = self.sm.statesNameToIndex['start_trial']
        startTrialInd = np.flatnonzero(eventsThisTrial[:,2]==startTrialStateID)[0]
        self.results['timeTrialStart'][trialIndex] = eventsThisTrial[startTrialInd,0]
        '''

        # -- Store choice and outcome --
        outcomeMode = self.params['outcomeMode'].get_string()


        ####### FIXME: what happens to 'choice' in the trials without one? ########

        # -- Check if it's an aborted trial --
        lastEvent = eventsThisTrial[-1,:]
        if lastEvent[1]==-1 and lastEvent[2]==0:
            self.results['outcome'][trialIndex] = self.results.labels['outcome']['aborted']
        # -- Otherwise evaluate 'choice' and 'outcome' --
        else:
            if outcomeMode=='sides direct' or outcomeMode=='direct':
                self.results['outcome'][trialIndex] = self.results.labels['outcome']['free']
            else:
                if self.sm.statesNameToIndex['choiceL'] in eventsThisTrial[:,2]:
                    self.results['choice'][trialIndex] = self.results.labels['choice']['left']
                elif self.sm.statesNameToIndex['choiceR'] in eventsThisTrial[:,2]:
                    self.results['choice'][trialIndex] = self.results.labels['choice']['right']
                else:
                    self.results['choice'][trialIndex] = self.results.labels['choice']['none']

                if self.sm.statesNameToIndex['reward'] in eventsThisTrial[:,2]:
                    self.results['outcome'][trialIndex] = self.results.labels['outcome']['correct']
                else:
                    self.results['outcome'][trialIndex] = self.results.labels['outcome']['error']
         


if __name__ == "__main__":
    (app,paradigm) = templates.create_app(Paradigm)


