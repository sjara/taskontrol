'''
Create a test to see how we can stop the sound from playing during a trial.

'''

import numpy as np
from taskontrol.core import paramgui
from PySide import QtGui 
from taskontrol.core import arraycontainer

from taskontrol.plugins import templates
reload(templates)
from taskontrol.plugins import speakercalibration
from taskontrol.settings import rigsettings
from taskontrol.plugins import soundclient

LONGTIME = 100

class Paradigm(templates.Paradigm2AFC):
    def __init__(self,parent=None, paramfile=None, paramdictname=None):
        super(Paradigm, self).__init__(parent)

         # -- Add parameters --
        self.params['targetDuration'] = paramgui.NumericParam('Target Duration',value=1,
                                                        units='s',group='Timing Parameters')
        timingParams = self.params.layout_group('Timing Parameters')
        
        self.params['targetFrequency'] = paramgui.NumericParam('Target freq',value=2000,decimals=0,
                                                        units='Hz',enabled=True,group='Sound Parameters')
        self.params['targetIntensity'] = paramgui.NumericParam('Intensity',value=50.0,units='dB-SPL',
                                                        enabled=True,group='Sound Parameters')
        soundParams = self.params.layout_group('Sound Parameters')

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

        layoutBottom.addLayout(layoutCol1)
        layoutBottom.addLayout(layoutCol2)

        layoutCol1.addWidget(self.saveData)
        layoutCol1.addWidget(self.sessionInfo)
        layoutCol1.addWidget(self.dispatcherView)
        
        layoutCol2.addWidget(timingParams)
        layoutCol2.addWidget(soundParams)
        layoutCol2.addStretch()


        self.centralWidget.setLayout(layoutMain)
        self.setCentralWidget(self.centralWidget)

        '''# -- Add variables for storing results --
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
        self.results['timeSideIn'] = np.empty(maxNtrials,dtype=float)'''

        # -- Load parameters from a file --
        self.params.from_file(paramfile,paramdictname)
        
        # -- Create sound client --
        self.soundClient = soundclient.SoundClient()
        self.soundClient.start()

        # -- Prepare first trial --
        #self.prepare_next_trial(0)
       

    def prepare_next_trial(self, nextTrial):
        #print '---------- ENTERING PREPARE TRIAL {0} --------------'.format(nextTrial) ###DEBUG
        self.params.update_history()
        self.prepare_target_sound()
        self.set_state_matrix()
        self.dispatcherModel.ready_to_start_trial()


    def prepare_target_sound(self):
        targetFrequency = self.params['targetFrequency'].get_value()
        targetIntensity = self.params['targetIntensity'].get_value()
        spkCal = speakercalibration.Calibration(rigsettings.SPEAKER_CALIBRATION)

        # FIXME: currently I am averaging calibration from both speakers (not good)
        targetAmp = spkCal.find_amplitude(targetFrequency,targetIntensity).mean()

        stimDur = self.params['targetDuration'].get_value()
        s1 = {'type':'chord', 'frequency':targetFrequency, 'duration':stimDur,
              'amplitude':targetAmp, 'ntones':12, 'factor':1.2}
        self.soundClient.set_sound(1,s1)

    def set_state_matrix(self):
        self.sm.reset_transitions()

        targetDuration = self.params['targetDuration'].get_value()

        # -- Set state matrix --
        self.sm.add_state(name='startTrial', statetimer=0,
                          transitions={'Tup':'waitForCenterPoke'})
        self.sm.add_state(name='waitForCenterPoke', statetimer=LONGTIME,
                          transitions={'Cin':'playStimulus'})
        self.sm.add_state(name='playStimulus', statetimer=targetDuration,
                          transitions={'Tup':'stopStimulus', 'Cout':'stopStimulus'},
                          outputsOn=['centerLED'],serialOut=1)
        self.sm.add_state(name='stopStimulus', statetimer=0,
                          transitions={'Tup':'waitForSidePoke'},
                          outputsOff=['centerLED'],serialOut=soundclient.STOP_ALL_SOUNDS)
        self.sm.add_state(name='waitForSidePoke', statetimer=LONGTIME,
                          transitions={'Lin':'readyForNextTrial', 'Rin':'readyForNextTrial'})

        self.dispatcherModel.set_state_matrix(self.sm)

if __name__ == "__main__":
    (app,paradigm) = paramgui.create_app(Paradigm)


