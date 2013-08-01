#!/usr/bin/env python

'''
This example implements a simple two-alternative force choice paradigm.

TODO:
- Add subject/experimenter section
- Make container for results


'''

__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2013-07-17'

import sys
from PySide import QtCore 
from PySide import QtGui 
from taskontrol.settings import rigsettings
from taskontrol.core import dispatcher
from taskontrol.core import statematrix
from taskontrol.core import paramgui
from taskontrol.core import arraycontainer
from taskontrol.core import savedata
from taskontrol.core import messenger
from taskontrol.plugins import sidesplot
import signal
import numpy as np

reload(statematrix)
reload(savedata)
reload(paramgui)
reload(messenger)


class Paradigm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Paradigm, self).__init__(parent)

        # -- Read settings --
        smServerType = rigsettings.STATE_MACHINE_TYPE
        #smServerType = 'dummy'

        # -- Create dispatcher --
        self.dispatcherModel = dispatcher.Dispatcher(serverType=smServerType,interval=0.3)
        self.dispatcherView = dispatcher.DispatcherGUI(model=self.dispatcherModel)

        # -- Module for saving data --
        self.saveData = savedata.SaveData()

        # -- Sides plot --
        sidesplot.set_pg_colors(self)
        self.mySidesPlot = sidesplot.SidesPlot(nTrials=80)

        # -- Create an empty state matrix --
        ###self.sm = statematrix.StateMatrix()

        # -- Add parameters --
        self.params = paramgui.Container()
        self.params['stimulusDuration'] = paramgui.NumericParam('Stim duration',value=0.2,
                                                        group='Timing Parameters')
        self.params['rewardDuration'] = paramgui.NumericParam('Reward duration',value=0.05,
                                                        group='Timing Parameters')
        timingParams = self.params.layout_group('Timing Parameters')

        # -- Add graphical widgets to main window --
        centralWidget = QtGui.QWidget()
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
        layoutCol1.addWidget(self.dispatcherView)
        
        layoutCol2.addWidget(timingParams)

        centralWidget.setLayout(layoutMain)
        self.setCentralWidget(centralWidget)

        # -- Center in screen --
        self.center_in_screen()


        # -- Add variables storing results --
        # FIXME: put all these in one dict that can be easily saved
        self.results = arraycontainer.Container()
        maxNtrials = 4000
        self.results.labels['rewardSide'] = {'left':0,'right':1}
        self.results['rewardSide'] = np.random.randint(2,size=maxNtrials)
        self.results.labels['choice'] = {'left':0,'right':1}
        self.results['choice'] = np.empty(maxNtrials,dtype=int)
        self.results.labels['outcome'] = {'correct':1,'error':0}
        self.results['outcome'] = np.empty(maxNtrials,dtype=int)

        # --- Create state matrix ---
        #self.set_state_matrix() ################# ?????????????

        # -- Connect signals from dispatcher --
        self.dispatcherModel.prepareNextTrial.connect(self.prepare_next_trial)
        ###self.dispatcherModel.startNewTrial.connect(self.start_new_trial)
        self.dispatcherModel.timerTic.connect(self.timer_tic)

        # -- Connect messenger --
        self.messagebar = messenger.Messenger()
        self.messagebar.timedMessage.connect(self.show_message)
        #self.messagebar.timedMessage.emit('Created window')
        self.messagebar.collect('Created window')

        # -- Connect signals to messenger
        self.saveData.logMessage.connect(self.messagebar.collect)
        self.dispatcherModel.logMessage.connect(self.messagebar.collect)

        # -- Connect other signals --
        self.saveData.buttonSaveData.clicked.connect(self.save_to_file)

        # -- Prepare first trial --
        self.prepare_next_trial(0)

    def save_to_file(self):
        '''Triggered by button-clicked signal'''
        # Next line is needed to truncate data before saving
        ###self.results.currentTrial = self.dispatcherModel.currentTrial
        self.saveData.to_file([self.params, self.dispatcherModel,
                               self.sm, self.results],
                              self.dispatcherModel.currentTrial)

    def show_message(self,msg):
        self.statusBar().showMessage(str(msg))
        print msg

    def center_in_screen(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def set_state_matrix(self,nextCorrectChoice):
        self.sm = statematrix.StateMatrix(readystate='ready_next_trial')

        stimulusDuration = self.params['stimulusDuration'].get_value()
        rewardDuration = self.params['rewardDuration'].get_value()

        #possibleStimuli = ['LeftLED','RightLED']
        #nextStimulus = possibleStimuli[nextCorrectChoice]
        #possibleRewards = ['LeftWater','RightWater']
        ##possibleChoices = ['Lin','Rin']
        #correctChoice = possibleChoices[nextCorrectChoice]
        #incorrectChoice = possibleChoices[not nextCorrectChoice]
        ##nextReward = possibleRewards[nextCorrectChoice]
        if nextCorrectChoice==self.results.labels['rewardSide']['left']:
            stimOutput = 'LeftLED'
            fromChoiceL = 'reward'
            fromChoiceR = 'punish'
            rewardOutput = 'LeftWater'
        elif nextCorrectChoice==self.results.labels['rewardSide']['right']:
            stimOutput = 'RightLED'
            fromChoiceL = 'punish'
            fromChoiceR = 'reward'
            rewardOutput = 'RightWater'
        else:
            raise ValueError('Value of nextCorrectChoice is not appropriate')

        print stimOutput, fromChoiceL, rewardOutput ### DEBUG


        # -- Set state matrix --
        self.sm.add_state(name='wait_for_cpoke', statetimer=10,
                    transitions={'Cin':'play_stimulus'})
        self.sm.add_state(name='play_stimulus', statetimer=stimulusDuration,
                    transitions={'Cin':'wait_for_sidepoke'},
                    outputsOn=[stimOutput])
        self.sm.add_state(name='wait_for_sidepoke', statetimer=20,
                    transitions={'Lin':'choiceL', 'Rin':'choiceR',
                                 'Tup':'ready_next_trial'},
                    outputsOff=[stimOutput])
        self.sm.add_state(name='choiceL', statetimer=0,
                    transitions={'Tup':fromChoiceL})
        self.sm.add_state(name='choiceR', statetimer=0,
                    transitions={'Tup':fromChoiceR})
        self.sm.add_state(name='reward', statetimer=rewardDuration,
                    transitions={'Tup':'stopReward'},
                    outputsOn=[rewardOutput])
        self.sm.add_state(name='punish', statetimer=0,
                    transitions={'Tup':'ready_next_trial'})
        self.sm.add_state(name='stopReward', statetimer=0,
                    transitions={'Tup':'ready_next_trial'},
                    outputsOff=[rewardOutput])
        print self.sm ### DEBUG

        prepareNextTrialStates = ['ready_next_trial']
        self.dispatcherModel.set_prepare_next_trial_states(prepareNextTrialStates,
                                                  self.sm.get_states_dict())

        self.dispatcherModel.set_state_matrix(self.sm.get_matrix(),
                                              self.sm.get_outputs(),
                                              self.sm.get_state_timers())

    def prepare_next_trial(self, nextTrial):
        self.params.update_history()
        print '\nPreparing trial %d'%nextTrial
        '''
        lastTenEvents = self.dispatcherModel.eventsMat[-10:-1]
        print 'Last 10 events:'
        for oneEvent in lastTenEvents:
            print '%0.3f\t %d\t %d'%(oneEvent[0],oneEvent[1],oneEvent[2])
        '''
        # -- Prepare next trial --
        nextCorrectChoice = self.results['rewardSide'][nextTrial]
        #print '\nNext choice = {0}'.format(nextCorrectChoice) ### DEBUG
        self.set_state_matrix(nextCorrectChoice)
        #print self.sm ### DEBUG
        self.dispatcherModel.ready_to_start_trial()

        # -- Calculate results from last trial --
        outcome = self.results['outcome']
        outcomeLabels = self.results.labels['outcome']
        choice = self.results['choice']
        choiceLabels = self.results.labels['choice']
        if nextTrial>0:
            eventsThisTrial = self.dispatcherModel.events_one_trial(nextTrial-1)
            if self.sm.statesNameToIndex['reward'] in eventsThisTrial[:,2]:
                outcome[nextTrial-1] = outcomeLabels['correct']
            else:
                outcome[nextTrial-1] = outcomeLabels['error']
                
        #print outcome[:nextTrial] ### DEBUG




###### FIX THIS: self.sm.statesNameToIndex changes from trial to trial
#                so the outcome is not calculated properly.
# reset_transitions()
# when adding state, check if it exists and use it if it does.




        # -- Update sides plot --
        self.mySidesPlot.update(self.results['rewardSide'],outcome,nextTrial)


    def start_new_trial(self, currentTrial):
        '''OBSOLETE'''
        print '\n======== Started trial %d ======== '%currentTrial


    def timer_tic(self,etime,lastEvents):
        print '.',
        sys.stdout.flush() # Force printing on the screen at this point


    def closeEvent(self, event):
        '''
        Executed when closing the main window.
        This method is inherited from QtGui.QMainWindow, which explains
        its camelCase naming.
        '''
        ###print 'ENTERED closeEvent()' # DEBUG
        self.dispatcherModel.die()
        event.accept()


if __name__ == "__main__":
    #QtCore.pyqtRemoveInputHook() # To stop looping if error occurs (for PyQt not PySide)
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Enable Ctrl-C

    # -- A workaround to enable re-running the app in ipython after closing --
    #app = QtGui.QApplication(sys.argv)
    app=QtGui.QApplication.instance() # checks if QApplication already exists 
    if not app: # create QApplication if it doesnt exist 
        app = QtGui.QApplication(sys.argv)

    paradigm = Paradigm()
    paradigm.show()
    app.exec_()
