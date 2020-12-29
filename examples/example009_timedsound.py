"""
Simple paradigm that presents a sound on every trial.
"""

from qtpy import QtCore 
from qtpy import QtWidgets 
from taskontrol import rigsettings
from taskontrol import paramgui
from taskontrol import savedata
from taskontrol import statematrix
from taskontrol import dispatcher
from taskontrol.plugins import manualcontrol
from taskontrol.plugins import soundclient
from taskontrol.plugins import speakercalibration
import time


class Paradigm(QtWidgets.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super().__init__(parent)

        self.name = 'timedsound'

        smServerType = rigsettings.STATE_MACHINE_TYPE

        # -- Module for saving data --
        self.saveData = savedata.SaveData(rigsettings.DATA_DIR, remotedir=rigsettings.REMOTE_DIR)

        # -- Create an empty state matrix --
        self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                          outputs=rigsettings.OUTPUTS,
                                          readystate='readyForNextTrial')

        # -- Add parameters --
        self.params = paramgui.Container()
        self.params['trainer'] = paramgui.StringParam('Trainer (initials)',
                                                      value='',
                                                      group='Session info')
        self.params['experimenter'] = paramgui.StringParam('Experimenter',
                                                           value='experimenter',
                                                           group='Session info')
        self.params['subject'] = paramgui.StringParam('Subject',value='subject',
                                                      group='Session info')
        self.sessionInfo = self.params.layout_group('Session info')

        # -- Trial timing parameters --
        self.params['interTrialInterval'] = paramgui.NumericParam('Inter trial interval (ITI)',value=1.0,
                                                                  units='s',group='Timing parameters')
        timingParams = self.params.layout_group('Timing parameters')

        # -- Sound parameters --
        self.params['soundFrequency'] = paramgui.NumericParam('Sound frequency', value=1000,
                                                               decimals=0, units='Hz',
                                                               group='Sound parameters')
        self.params['soundDuration'] = paramgui.NumericParam('Sound duration', value=0.1, units='s',
                                                              group='Sound parameters')
        self.params['soundIntensity'] = paramgui.NumericParam('Sound intensity', value=60, units='dB-SPL',
                                                        enabled=True, group='Sound parameters')
        self.params['soundAmplitude'] = paramgui.NumericParam('Sound amplitude',value=0.0,units='[0-1]',
                                                        enabled=False, decimals=4, group='Sound parameters')
        soundParams = self.params.layout_group('Sound parameters')
        
        # -- Create dispatcher --
        self.dispatcher = dispatcher.Dispatcher(serverType=smServerType,interval=0.1)

        # -- Manual control of outputs --
        self.manualControl = manualcontrol.ManualControl(self.dispatcher.statemachine)

        # -- Add graphical widgets to main window --
        self.centralWidget = QtWidgets.QWidget()
        layoutMain = QtWidgets.QHBoxLayout()
        layoutCol1 = QtWidgets.QVBoxLayout()
        layoutCol2 = QtWidgets.QVBoxLayout()

        layoutMain.addLayout(layoutCol1)
        layoutMain.addLayout(layoutCol2)

        layoutCol1.addWidget(self.saveData)
        layoutCol1.addWidget(self.sessionInfo)
        layoutCol1.addWidget(self.dispatcher.widget)
        
        layoutCol2.addWidget(self.manualControl)
        layoutCol2.addStretch()
        layoutCol2.addWidget(timingParams)
        layoutCol2.addStretch()
        layoutCol2.addWidget(soundParams)

        self.centralWidget.setLayout(layoutMain)
        self.setCentralWidget(self.centralWidget)

        # -- Center in screen --
        paramgui.center_on_screen(self)

        # -- Load speaker calibration --
        self.spkCal = speakercalibration.Calibration(rigsettings.SPEAKER_CALIBRATION_CHORD)
        self.noiseCal = speakercalibration.NoiseCalibration(rigsettings.SPEAKER_CALIBRATION_NOISE)

        # -- Connect to sound server and define sounds --
        self.soundClient = soundclient.SoundClient()
        self.soundID = 1
        self.soundClient.start()
        
        # -- Connect signals from dispatcher --
        self.dispatcher.prepareNextTrial.connect(self.prepare_next_trial)

        # -- Connect messenger --
        self.messagebar = paramgui.Messenger()
        self.messagebar.timedMessage.connect(self._show_message)
        self.messagebar.collect('Created window')

        # -- Connect signals to messenger
        self.saveData.logMessage.connect(self.messagebar.collect)
        self.dispatcher.logMessage.connect(self.messagebar.collect)

        # -- Connect other signals --
        self.saveData.buttonSaveData.clicked.connect(self.save_to_file)

    def _show_message(self,msg):
        self.statusBar().showMessage(str(msg))
        print(msg)

    '''
    def _center_in_screen(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    '''
    
    def save_to_file(self):
        '''Triggered by button-clicked signal'''
        self.saveData.to_file([self.params, self.dispatcher, self.sm],
                              self.dispatcher.currentTrial,
                              subject=self.params['subject'].get_value(),
                              paradigm=self.name)

    def prepare_sound(self):
        soundIntensity = self.params['soundIntensity'].get_value()
        soundDuration = self.params['soundDuration'].get_value()
        # FIXME: currently I am averaging calibration from both speakers (not good)
        soundFrequency = self.params['soundFrequency'].get_value()
        soundAmp = self.spkCal.find_amplitude(soundFrequency,soundIntensity).mean()
        s1 = {'type':'tone', 'frequency':soundFrequency, 'duration':soundDuration,
              'amplitude':soundAmp}
        self.params['soundAmplitude'].set_value(soundAmp)
        self.soundClient.set_sound(self.soundID, s1)
        
    def prepare_next_trial(self, nextTrial):
        if nextTrial>0:
            self.params.update_history(nextTrial-1)
        soundDuration = self.params['soundDuration'].get_value()
        interTrialInterval = self.params['interTrialInterval'].get_value()
        self.prepare_sound()
        self.sm.reset_transitions()
        self.sm.add_state(name='startTrial', statetimer=0,
                          transitions={'Tup':'playSound'},
                          outputsOff=['centerLED'])
        self.sm.add_state(name='playSound', statetimer=soundDuration,
                          transitions={'Tup':'ITI', 'Cin':'ITI',
                                       'Lin':'ITI', 'Rin':'ITI'},
                          outputsOn=['centerLED'],
                          serialOut=self.soundID)
        self.sm.add_state(name='ITI', statetimer=interTrialInterval,
                          transitions={'Tup':'readyForNextTrial'},
                          outputsOff=['centerLED'],
                          serialOut=soundclient.STOP_ALL_SOUNDS)
        '''
        self.sm.add_state(name='stopSound', statetimer=0,
                          transitions={'Tup':'readyForNextTrial'},
                          outputsOff=['centerLED'],
                          serialOut=soundclient.STOP_ALL_SOUNDS)
        '''
        self.dispatcher.set_state_matrix(self.sm)
        self.dispatcher.ready_to_start_trial()

    def closeEvent(self, event):
        '''
        Executed when closing the main window.
        This method is inherited from QtWidgets.QMainWindow, which explains
        its camelCase naming.
        '''
        self.soundClient.shutdown()
        self.dispatcher.die()
        event.accept()


if __name__ == "__main__":
    (app, paradigm) = paramgui.create_app(Paradigm)

