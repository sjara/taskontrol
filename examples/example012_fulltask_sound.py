'''
Create a frequency discrimination 2AFC paradigm.


* TO DO:
- Check that all parameters are saved
- Check that all times are saved
- Note that outcomeMode (menu) is saved different from labels (e.g., outcome)
- Verify that the choice of last trial is saved properly

'''

import numpy as np
from taskontrol.settings import rigsettings
from taskontrol.core import paramgui
from PySide import QtGui 
from taskontrol.core import arraycontainer

from taskontrol.plugins import templates
reload(templates)
from taskontrol.plugins import performancedynamicsplot

from taskontrol.plugins import soundclient
from taskontrol.plugins import speakercalibration
import time

LONGTIME = 100

class Paradigm(templates.Paradigm2AFC):
    def __init__(self,parent=None, paramfile=None, paramdictname=None):
        super(Paradigm, self).__init__(parent)

        # -- Performance dynamics plot --
        performancedynamicsplot.set_pg_colors(self)
        self.myPerformancePlot = performancedynamicsplot.PerformanceDynamicsPlot(nTrials=400,winsize=10)

         # -- Add parameters --
        self.params['timeWaterValveL'] = paramgui.NumericParam('Time valve left',value=0.04,
                                                               units='s',group='Water delivery')
        self.params['timeWaterValveC'] = paramgui.NumericParam('Time valve center',value=0.04,
                                                               units='s',group='Water delivery')
        self.params['timeWaterValveR'] = paramgui.NumericParam('Time valve right',value=0.04,
                                                               units='s',group='Water delivery')
        waterDelivery = self.params.layout_group('Water delivery')
        
        self.params['outcomeMode'] = paramgui.MenuParam('Outcome mode',
                                                        ['sides_direct','direct','on_next_correct',
                                                         'only_if_correct','simulated'],
                                                         value=3,group='Choice parameters')
        self.params['antibiasMode'] = paramgui.MenuParam('Anti-bias mode',
                                                        ['off','repeat_mistake'],
                                                        value=0,group='Choice parameters')
        choiceParams = self.params.layout_group('Choice parameters')

        self.params['delayToTarget'] = paramgui.NumericParam('Delay to Target',value=0.2,
                                                        units='s',group='Timing Parameters')
        self.params['targetDuration'] = paramgui.NumericParam('Target Duration',value=0.1,
                                                        units='s',group='Timing Parameters')
        self.params['rewardAvailability'] = paramgui.NumericParam('Reward Availability',value=4,
                                                        units='s',group='Timing Parameters')
        self.params['punishTimeError'] = paramgui.NumericParam('Punishment (error)',value=0,
                                                        units='s',group='Timing Parameters')
        self.params['punishTimeEarly'] = paramgui.NumericParam('Punishment (early)',value=0,
                                                        units='s',group='Timing Parameters')
        timingParams = self.params.layout_group('Timing Parameters')

        self.params['nValid'] = paramgui.NumericParam('N valid',value=0,
                                                      units='',enabled=False,
                                                      group='Report')
        self.params['nRewarded'] = paramgui.NumericParam('N rewarded',value=0,
                                                         units='',enabled=False,
                                                         group='Report')
        reportParams = self.params.layout_group('Report')

        # 5000, 7000, 9800 (until 2014-03-19)
        self.params['highFreq'] = paramgui.NumericParam('High freq',value=16000,
                                                        units='Hz',group='Sound Parameters')
        self.params['midFreq'] = paramgui.NumericParam('Middle freq',value=7000,
                                                        units='Hz',group='Sound Parameters')
        self.params['lowFreq'] = paramgui.NumericParam('Low freq',value=3000,
                                                        units='Hz',group='Sound Parameters')
        #self.params['soundMaxAmplitude'] = paramgui.NumericParam('Max amplitude',value=0.01,
        #                                                units='[0-1]',group='Sound Parameters')
        self.params['soundIntensityMode'] = paramgui.MenuParam('Intensity mode',
                                                        ['fixed','randMinus20'],
                                                        value=1,group='Sound Parameters')
        self.params['soundMaxIntensity'] = paramgui.NumericParam('Max intensity',value=60,
                                                        units='dB-SPL',group='Sound Parameters')
        self.params['soundIntensity'] = paramgui.NumericParam('Intensity',value=0.0,units='db-SPL',
                                                        enabled=False,group='Sound Parameters')
        self.params['soundAmplitudeHigh'] = paramgui.NumericParam('AmplitudeHigh',value=0.0,units='[0-1]',
                                                        enabled=False,group='Sound Parameters')
        self.params['soundAmplitudeMid'] = paramgui.NumericParam('AmplitudeMid',value=0.0,units='[0-1]',
                                                        enabled=False,group='Sound Parameters')
        self.params['soundAmplitudeLow'] = paramgui.NumericParam('AmplitudeLow',value=0.0,units='[0-1]',
                                                        enabled=False,group='Sound Parameters')
        self.params['punishSoundAmplitude'] = paramgui.NumericParam('Punish amplitude',value=0.01,
                                                              units='[0-1]',
                                                              group='Sound Parameters')
        
        '''
        self.params['highFreq'] = paramgui.NumericParam('High freq',value=500,
                                                        units='Hz',group='Sound Parameters')
        self.params['midFreq'] = paramgui.NumericParam('Middle freq',value=440,
                                                        units='Hz',group='Sound Parameters')
        self.params['lowFreq'] = paramgui.NumericParam('Low freq',value=400,
                                                        units='Hz',group='Sound Parameters')
        #4200, 9200, 20200
        '''
        soundParams = self.params.layout_group('Sound Parameters')


        # 
        self.params['experimenter'].set_value('santiago')
        self.params['subject'].set_value('test')

        # -- Add graphical widgets to main window --
        self.centralWidget = QtGui.QWidget()
        layoutMain = QtGui.QVBoxLayout()
        layoutTop = QtGui.QVBoxLayout()
        layoutBottom = QtGui.QHBoxLayout()
        layoutCol1 = QtGui.QVBoxLayout()
        layoutCol2 = QtGui.QVBoxLayout()
        layoutCol3 = QtGui.QVBoxLayout()
        layoutCol4 = QtGui.QVBoxLayout()
        
        layoutMain.addLayout(layoutTop)
        #layoutMain.addStretch()
        layoutMain.addSpacing(0)
        layoutMain.addLayout(layoutBottom)

        layoutTop.addWidget(self.mySidesPlot)
        layoutTop.addWidget(self.myPerformancePlot)

        layoutBottom.addLayout(layoutCol1)
        layoutBottom.addLayout(layoutCol2)
        layoutBottom.addLayout(layoutCol3)
        layoutBottom.addLayout(layoutCol4)

        layoutCol1.addWidget(self.saveData)
        layoutCol1.addWidget(self.sessionInfo)
        layoutCol1.addWidget(self.dispatcherView)
        
        layoutCol2.addWidget(self.manualControl)
        layoutCol2.addWidget(waterDelivery)
        layoutCol2.addWidget(choiceParams)
        layoutCol2.addStretch()

        layoutCol3.addWidget(timingParams)
        layoutCol4.addWidget(soundParams)
        layoutCol3.addWidget(reportParams)
        layoutCol3.addStretch()

        layoutCol4.addStretch()

        self.centralWidget.setLayout(layoutMain)
        self.setCentralWidget(self.centralWidget)

        # -- Add variables for storing results --
        maxNtrials = 4000 # Preallocating space for each vector makes things easier
        self.results = arraycontainer.Container()
        self.results.labels['rewardSide'] = {'left':0,'right':1}
        self.results['rewardSide'] = np.random.randint(2,size=maxNtrials)
        self.results.labels['choice'] = {'left':0,'right':1,'none':2}
        self.results['choice'] = np.empty(maxNtrials,dtype=int)
        self.results.labels['outcome'] = {'correct':1,'error':0,'invalid':2,
                                          'free':3,'nochoice':4,'aftererror':5,'aborted':6}
        self.results['outcome'] = np.empty(maxNtrials,dtype=int)
        self.results['timeTrialStart'] = np.empty(maxNtrials,dtype=float)
        self.results['timeCenterIn'] = np.empty(maxNtrials,dtype=float)
        self.results['timeCenterOut'] = np.empty(maxNtrials,dtype=float)
        self.results['timeSideIn'] = np.empty(maxNtrials,dtype=float)

        # -- Load parameters from a file --
        self.params.from_file(paramfile,paramdictname)

        # -- Connect to sound server and define sounds --
        print 'Conecting to soundserver...'
        print '***** FIXME: HARDCODED TIME DELAY TO WAIT FOR SERIAL PORT! *****'
        time.sleep(0.2)
        self.soundClient = soundclient.SoundClient()
        '''
        highFreq = self.params['highFreq'].get_value()
        lowFreq = self.params['lowFreq'].get_value()
        stimDur = self.params['targetDuration'].get_value()
        s1 = {'type':'tone', 'frequency':lowFreq, 'duration':stimDur, 'amplitude':0.01}
        s2 = {'type':'tone', 'frequency':highFreq, 'duration':stimDur, 'amplitude':0.01}
        self.soundClient.set_sound(1,s1)
        self.soundClient.set_sound(2,s2)
        '''

        punishSoundAmplitude = self.params['punishSoundAmplitude'].get_value()
        sNoise = {'type':'noise', 'duration':0.5, 'amplitude':punishSoundAmplitude}
        self.punishSoundID = 127
        self.soundClient.set_sound(self.punishSoundID,sNoise)
        self.soundClient.start()

        # -- Prepare first trial --
        #self.prepare_next_trial(0)
       
    def define_sounds(self):
        if self.params['soundIntensityMode'].get_string() == 'randMinus20':
            possibleIntensities = self.params['soundMaxIntensity'].get_value()+\
                                  np.array([-20,-15,-10,-5,0])
            soundIntensity = possibleIntensities[np.random.randint(len(possibleIntensities))]
        else:
            soundIntensity = self.params['soundMaxIntensity'].get_value()
        self.params['soundIntensity'].set_value(soundIntensity)
                
            
        #amplitudeFactor = [0.25,0.5,1]
        #possibleAmplitudes = self.params['soundMaxAmplitude'].get_value()*np.array(amplitudeFactor)
        #soundAmplitude = possibleAmplitudes[np.random.randint(len(possibleAmplitudes))]

        #soundAmplitude = 0.01
        #self.params['soundAmplitude'].set_value(soundAmplitude)

        highFreq = self.params['highFreq'].get_value()
        midFreq = self.params['midFreq'].get_value()
        lowFreq = self.params['lowFreq'].get_value()
        stimDur = self.params['targetDuration'].get_value()
        
        spkCal = speakercalibration.Calibration(rigsettings.SPEAKER_CALIBRATION)
        ampLow = spkCal.find_amplitude(lowFreq,soundIntensity).mean()
        ampMid = spkCal.find_amplitude(midFreq,soundIntensity).mean()
        ampHigh = spkCal.find_amplitude(highFreq,soundIntensity).mean()
        
        self.params['soundAmplitudeLow'].set_value(ampLow)
        self.params['soundAmplitudeMid'].set_value(ampMid)
        self.params['soundAmplitudeHigh'].set_value(ampHigh)
        
        #s1 = {'type':'tone', 'frequency':lowFreq, 'duration':stimDur, 'amplitude':ampLow}
        #s2 = {'type':'tone', 'frequency':highFreq, 'duration':stimDur, 'amplitude':ampHigh}
        s1 = {'type':'chord', 'frequency':lowFreq, 'duration':stimDur,
              'amplitude':ampLow, 'ntones':12, 'factor':1.2}
        s2 = {'type':'chord', 'frequency':highFreq, 'duration':stimDur,
              'amplitude':ampHigh, 'ntones':12, 'factor':1.2}
        self.soundClient.set_sound(1,s1)
        self.soundClient.set_sound(2,s2)

    def prepare_next_trial(self, nextTrial):
        import time
        TicTime = time.time()

        self.params.update_history()

        # -- Calculate results from last trial (update outcome, choice, etc) --
        if nextTrial>0:
            self.calculate_results(nextTrial-1)
            # -- Apply anti-bias --
            if self.params['antibiasMode'].get_string()=='repeat_mistake':
                if self.results['outcome'][nextTrial-1]==self.results.labels['outcome']['error']:
                    self.results['rewardSide'][nextTrial] = self.results['rewardSide'][nextTrial-1]

        # -- Prepare next trial --
        self.define_sounds()
        nextCorrectChoice = self.results['rewardSide'][nextTrial]
        self.set_state_matrix(nextCorrectChoice)
        self.dispatcherModel.ready_to_start_trial()
        print 'Elapsed Time (preparing next trial): ' + str(time.time()-TicTime)

        # -- Update sides plot --
        self.mySidesPlot.update(self.results['rewardSide'],self.results['outcome'],nextTrial)

        # -- Update performance plot --
        self.myPerformancePlot.update(self.results['rewardSide'],self.results.labels['rewardSide'],
                                      self.results['outcome'],self.results.labels['outcome'],
                                      nextTrial)

    def set_state_matrix(self,nextCorrectChoice):
        self.sm.reset_transitions()

        targetDuration = self.params['targetDuration'].get_value()
        if nextCorrectChoice==self.results.labels['rewardSide']['left']:
            rewardDuration = self.params['timeWaterValveL'].get_value()
            stimOutput = 'leftLED'
            fromChoiceL = 'reward'
            fromChoiceR = 'punish'
            rewardOutput = 'leftWater'
            correctSidePort = 'Lin'
            soundID = 1
        elif nextCorrectChoice==self.results.labels['rewardSide']['right']:
            rewardDuration = self.params['timeWaterValveR'].get_value()
            stimOutput = 'rightLED'
            fromChoiceL = 'punish'
            fromChoiceR = 'reward'
            rewardOutput = 'rightWater'
            correctSidePort = 'Rin'
            soundID = 2
        else:
            raise ValueError('Value of nextCorrectChoice is not appropriate')

        delayToTarget = self.params['delayToTarget'].get_value()
        rewardAvailability = self.params['rewardAvailability'].get_value()
        punishTimeError = self.params['punishTimeError'].get_value()
        punishTimeEarly = self.params['punishTimeEarly'].get_value()

        # -- Set state matrix --
        outcomeMode = self.params['outcomeMode'].get_string()
        if outcomeMode=='simulated':
            self.sm.add_state(name='startTrial', statetimer=0,
                              transitions={'Tup':'waitForCenterPoke'})
            self.sm.add_state(name='waitForCenterPoke', statetimer=1,
                              transitions={'Tup':'playStimulus'})
            self.sm.add_state(name='playStimulus', statetimer=targetDuration,
                              transitions={'Tup':'reward'},
                              outputsOn=[stimOutput],serialOut=soundID)
            self.sm.add_state(name='reward', statetimer=rewardDuration,
                              transitions={'Tup':'stopReward'},
                              outputsOn=[rewardOutput],
                              outputsOff=[stimOutput])
            self.sm.add_state(name='stopReward', statetimer=0,
                              transitions={'Tup':'readyForNextTrial'},
                              outputsOff=[rewardOutput])
        elif outcomeMode=='sides_direct':
            self.sm.add_state(name='startTrial', statetimer=0,
                              transitions={'Tup':'waitForCenterPoke'})
            self.sm.add_state(name='waitForCenterPoke', statetimer=LONGTIME,
                              transitions={'Cin':'playStimulus',correctSidePort:'playStimulus'})
            self.sm.add_state(name='playStimulus', statetimer=targetDuration,
                              transitions={'Tup':'reward'},
                              outputsOn=[stimOutput],serialOut=soundID)
            self.sm.add_state(name='reward', statetimer=rewardDuration,
                              transitions={'Tup':'stopReward'},
                              outputsOn=[rewardOutput],
                              outputsOff=[stimOutput])
            self.sm.add_state(name='stopReward', statetimer=0,
                              transitions={'Tup':'readyForNextTrial'},
                              outputsOff=[rewardOutput])
        elif outcomeMode=='direct':
            self.sm.add_state(name='startTrial', statetimer=0,
                              transitions={'Tup':'waitForCenterPoke'})
            self.sm.add_state(name='waitForCenterPoke', statetimer=LONGTIME,
                              transitions={'Cin':'playStimulus'})
            self.sm.add_state(name='playStimulus', statetimer=targetDuration,
                              transitions={'Tup':'reward'},
                              outputsOn=[stimOutput],serialOut=soundID)
            self.sm.add_state(name='reward', statetimer=rewardDuration,
                              transitions={'Tup':'stopReward'},
                              outputsOn=[rewardOutput],
                              outputsOff=[stimOutput])
            self.sm.add_state(name='stopReward', statetimer=0,
                              transitions={'Tup':'readyForNextTrial'},
                              outputsOff=[rewardOutput])
        elif outcomeMode=='on_next_correct':
            self.sm.add_state(name='startTrial', statetimer=0,
                              transitions={'Tup':'waitForCenterPoke'})
            self.sm.add_state(name='waitForCenterPoke', statetimer=LONGTIME,
                              transitions={'Cin':'delayPeriod'})
            self.sm.add_state(name='delayPeriod', statetimer=delayToTarget,
                              transitions={'Tup':'playStimulus','Cout':'waitForCenterPoke'})
            self.sm.add_state(name='playStimulus', statetimer=targetDuration,
                              transitions={'Tup':'waitForSidePoke','Cout':'earlyWithdrawal'},
                              serialOut=soundID) #outputsOn=[stimOutput],
            self.sm.add_state(name='waitForSidePoke', statetimer=rewardAvailability,
                              transitions={'Lin':'choiceLeft','Rin':'choiceRight',
                                           'Tup':'noChoice'},
                              outputsOff=[stimOutput])
            self.sm.add_state(name='keepWaitForSide', statetimer=rewardAvailability,
                              transitions={'Lin':'choiceLeft','Rin':'choiceRight',
                                           'Tup':'noChoice'},
                              outputsOff=[stimOutput])
            if correctSidePort=='Lin':
                self.sm.add_state(name='choiceLeft', statetimer=0,
                                  transitions={'Tup':'reward'})
                self.sm.add_state(name='choiceRight', statetimer=0,
                                  transitions={'Tup':'keepWaitForSide'})
            elif correctSidePort=='Rin':
                self.sm.add_state(name='choiceLeft', statetimer=0,
                                  transitions={'Tup':'keepWaitForSide'})
                self.sm.add_state(name='choiceRight', statetimer=0,
                                  transitions={'Tup':'reward'})
            self.sm.add_state(name='earlyWithdrawal', statetimer=punishTimeEarly,
                              transitions={'Tup':'readyForNextTrial'},
                              outputsOff=[stimOutput],serialOut=self.punishSoundID)
            self.sm.add_state(name='reward', statetimer=rewardDuration,
                              transitions={'Tup':'stopReward'},
                              outputsOn=[rewardOutput])
            self.sm.add_state(name='stopReward', statetimer=0,
                              transitions={'Tup':'readyForNextTrial'},
                              outputsOff=[rewardOutput])
            self.sm.add_state(name='punish', statetimer=punishTimeError,
                              transitions={'Tup':'readyForNextTrial'})
            self.sm.add_state(name='noChoice', statetimer=0,
                              transitions={'Tup':'readyForNextTrial'})

        elif outcomeMode=='only_if_correct':
            self.sm.add_state(name='startTrial', statetimer=0,
                              transitions={'Tup':'waitForCenterPoke'})
            self.sm.add_state(name='waitForCenterPoke', statetimer=LONGTIME,
                              transitions={'Cin':'delayPeriod'})
            self.sm.add_state(name='delayPeriod', statetimer=delayToTarget,
                              transitions={'Tup':'playStimulus','Cout':'waitForCenterPoke'})
            self.sm.add_state(name='playStimulus', statetimer=targetDuration,
                              transitions={'Tup':'waitForSidePoke','Cout':'earlyWithdrawal'},
                              serialOut=soundID) #outputsOn=[stimOutput],
            self.sm.add_state(name='waitForSidePoke', statetimer=rewardAvailability,
                              transitions={'Lin':'choiceLeft','Rin':'choiceRight',
                                           'Tup':'noChoice'},
                              outputsOff=[stimOutput])
            if correctSidePort=='Lin':
                self.sm.add_state(name='choiceLeft', statetimer=0,
                                  transitions={'Tup':'reward'})
                self.sm.add_state(name='choiceRight', statetimer=0,
                                  transitions={'Tup':'punish'})
            elif correctSidePort=='Rin':
                self.sm.add_state(name='choiceLeft', statetimer=0,
                                  transitions={'Tup':'punish'})
                self.sm.add_state(name='choiceRight', statetimer=0,
                                  transitions={'Tup':'reward'})
            self.sm.add_state(name='earlyWithdrawal', statetimer=punishTimeEarly,
                              transitions={'Tup':'readyForNextTrial'},
                              outputsOff=[stimOutput],serialOut=self.punishSoundID)
            self.sm.add_state(name='reward', statetimer=rewardDuration,
                              transitions={'Tup':'stopReward'},
                              outputsOn=[rewardOutput])
            self.sm.add_state(name='stopReward', statetimer=0,
                              transitions={'Tup':'readyForNextTrial'},
                              outputsOff=[rewardOutput,stimOutput])
            self.sm.add_state(name='punish', statetimer=punishTimeError,
                              transitions={'Tup':'readyForNextTrial'})
            self.sm.add_state(name='noChoice', statetimer=0,
                              transitions={'Tup':'readyForNextTrial'})

        else:
            raise TypeError('outcomeMode={0} has not been implemented'.format(outcomeMode))
        print self.sm ### DEBUG
        self.dispatcherModel.set_state_matrix(self.sm)


    def calculate_results(self,trialIndex):
        eventsThisTrial = self.dispatcherModel.events_one_trial(trialIndex)
        #print '===== Trial {0} ====='.format(trialIndex)
        #print eventsThisTrial

        # -- Find beginning of trial --
        startTrialStateID = self.sm.statesNameToIndex['startTrial']
        # FIXME: Next line seems inefficient. Is there a better way?
        startTrialInd = np.flatnonzero(eventsThisTrial[:,2]==startTrialStateID)[0]
        self.results['timeTrialStart'][trialIndex] = eventsThisTrial[startTrialInd,0]

        # -- Find outcomeMode for that trial --
        outcomeModeID = self.params.history['outcomeMode'][trialIndex]
        outcomeModeString = self.params['outcomeMode'].get_items()[outcomeModeID]

        # -- Check if it's an aborted trial --
        lastEvent = eventsThisTrial[-1,:]
        if lastEvent[1]==-1 and lastEvent[2]==0:
            self.results['outcome'][trialIndex] = self.results.labels['outcome']['aborted']
            self.results['choice'][trialIndex] = self.results.labels['choice']['none']
        # -- Otherwise evaluate 'choice' and 'outcome' --
        else:
            if outcomeModeString in ['simulated','sides_direct','direct']:
                self.results['outcome'][trialIndex] = self.results.labels['outcome']['free']
                self.results['choice'][trialIndex] = self.results.labels['choice']['none']
                self.params['nValid'].add(1)
                self.params['nRewarded'].add(1)
            if outcomeModeString=='on_next_correct' or outcomeModeString=='only_if_correct':
                if self.sm.statesNameToIndex['choiceLeft'] in eventsThisTrial[:,2]:
                    self.results['choice'][trialIndex] = self.results.labels['choice']['left']
                elif self.sm.statesNameToIndex['choiceRight'] in eventsThisTrial[:,2]:
                    self.results['choice'][trialIndex] = self.results.labels['choice']['right']
                else:
                    self.results['choice'][trialIndex] = self.results.labels['choice']['none']
                    self.results['outcome'][trialIndex] = \
                        self.results.labels['outcome']['nochoice']
                if self.sm.statesNameToIndex['reward'] in eventsThisTrial[:,2]:
                   self.results['outcome'][trialIndex] = \
                        self.results.labels['outcome']['correct']
                   self.params['nRewarded'].add(1)
                   if outcomeModeString=='on_next_correct' and \
                           self.sm.statesNameToIndex['keepWaitForSide'] in eventsThisTrial[:,2]:
                       self.results['outcome'][trialIndex] = \
                           self.results.labels['outcome']['aftererror']
                else:
                    if self.sm.statesNameToIndex['earlyWithdrawal'] in eventsThisTrial[:,2]:
                        self.results['outcome'][trialIndex] = \
                            self.results.labels['outcome']['invalid']
                    elif self.sm.statesNameToIndex['punish'] in eventsThisTrial[:,2]:
                        self.results['outcome'][trialIndex] = \
                            self.results.labels['outcome']['error']
            	# -- Check if it was a valid trial --
            	if self.sm.statesNameToIndex['waitForSidePoke'] in eventsThisTrial[:,2]:
                	self.params['nValid'].add(1)


if __name__ == "__main__":
    (app,paradigm) = paramgui.create_app(Paradigm)


