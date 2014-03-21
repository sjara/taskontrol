'''
Generate sounds at different frequencies to calibrate speakers.

What I want:
- Play sound until press stop
  . To enable enough time to measure amplitude in oscilloscope
- GUI: 
  . array of frequencies
  . one button each freq to start/stop
  . a box to enter amplitude
  . a button to plot results
  . a button to save results

[0.03,0.014,0.013,0.004,0.005,0.006,0.01,0.01,0.03,0.017,0.03,0.028,0.03,0.03,0.03,0.03]
'''

import sys
from PySide import QtCore 
from PySide import QtGui 
from taskontrol.core import messenger

import pyo
import time
import signal
import numpy as np

SOUND_FREQUENCIES = np.logspace(np.log10(1000), np.log10(40000), 16)
DEFAULT_AMPLITUDE = 0.01
MAX_AMPLITUDE = 0.03

BUTTON_COLORS = {'on':'red','off':'black'}


'''
s = pyo.Server(audio='jack').boot()
s.start()
soundObj = pyo.Sine(freq=3000,mul=0.02).mix(2).out(dur=4)
time.sleep(4)
'''

class OutputButton(QtGui.QPushButton):
    '''Single button for manual output'''
    def __init__(self, soundServer, soundFreq, parent=None):
        super(OutputButton, self).__init__(str(int(np.round(soundFreq))), parent)

        self.soundServer = soundServer
        self.soundFreq = soundFreq
        self.setCheckable(True)
        self.connect(self,QtCore.SIGNAL('clicked()'),self.toggleOutput)
        #self.soundObj = pyo.Sine(freq=self.soundFreq,mul=0.02).mix(2)
        self.soundObj = pyo.Sine(freq=self.soundFreq,mul=DEFAULT_AMPLITUDE)
        
    def toggleOutput(self):
        if self.isChecked():
            self.start()
        else:
            self.stop()

    def start(self):
        '''Start action.'''
        stylestr = 'QPushButton {{color: {0}; font: bold}}'.format(BUTTON_COLORS['on'])
        self.setStyleSheet(stylestr)
        self.play_sound(self.soundFreq)

    def stop(self):
        '''Stop action.'''
        stylestr = ''
        self.setStyleSheet(stylestr)
        self.stop_sound()
        
    def play_sound(self,soundfreq):
        #self.soundObj = pyo.Sine(freq=soundfreq,mul=0.02).mix(2).out()
        #self.soundObj.setMul(0.01)  
        self.soundObj.out()

    def change_amplitude(self,amplitude):
        self.soundObj.setMul(amplitude)

    def stop_sound(self):
        self.soundObj.stop()

class AmplitudeControl(QtGui.QDoubleSpinBox):
    def __init__(self,soundButton,parent=None):
        super(AmplitudeControl,self).__init__(parent)
        self.setRange(0,MAX_AMPLITUDE)
        self.setSingleStep(0.001)
        self.setDecimals(3)
        self.setValue(DEFAULT_AMPLITUDE)
        self.soundButton = soundButton
        self.valueChanged.connect(self.change_amplitude)
    def change_amplitude(self,value):
        self.soundButton.change_amplitude(value)

class SoundControl(QtGui.QGroupBox):
    def __init__(self, parent=None):
        super(SoundControl, self).__init__(parent)
        self.soundServer = self.initializeSound()
        
        # -- Create graphical objects --
        layout = QtGui.QGridLayout()
        soundFreqs = SOUND_FREQUENCIES
        nFreq = len(soundFreqs)
        self.outputButtons = nFreq*[None]
        self.amplitudeControl = nFreq*[None]
        #nButtons = 0
        #nCols = 1
        for indf,onefreq in enumerate(soundFreqs):
            self.outputButtons[indf] = OutputButton(self.soundServer,onefreq)
            self.amplitudeControl[indf] = AmplitudeControl(self.outputButtons[indf])
            #self.outputButtons[indf].setObjectName('ManualControlButton')
            #row = nButtons//nCols # Integer division
            #col = nButtons%nCols  # Modulo
            layout.addWidget(self.outputButtons[indf], indf, 0)
            layout.addWidget(self.amplitudeControl[indf], indf, 1)
            #nButtons += 1

        #layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setTitle('Sound freqs')
        

    def initializeSound(self):
        s = pyo.Server(audio='jack').boot()
        s.start()
        return s



class SpeakerCalibration(QtGui.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(SpeakerCalibration, self).__init__(parent)

        self.name = 'speakercalibration'

        # -- Module for saving data --
        #self.saveData = savedata.SaveData(rigsettings.DATA_DIR)

        # -- Add parameters --
        '''
        self.params = paramgui.Container()
        self.params['experimenter'] = paramgui.StringParam('Experimenter',
                                                           value='experimenter',
                                                           group='Session info')
        self.params['subject'] = paramgui.StringParam('Subject',value='subject',
                                                      group='Session info')
        self.sessionInfo = self.params.layout_group('Session info')
        '''

        # -- Connect to sound server and define sounds --
        # FINISH

        # -- Add graphical widgets to main window --
        self.centralWidget = QtGui.QWidget()
        layoutMain = QtGui.QVBoxLayout()

        soundControl = SoundControl()        
        layoutMain.addWidget(soundControl)

        self.centralWidget.setLayout(layoutMain)
        self.setCentralWidget(self.centralWidget)

        # -- Center in screen --
        self._center_in_screen()

        # -- Add variables storing results --
        #self.results = arraycontainer.Container()

        # -- Connect messenger --
        self.messagebar = messenger.Messenger()
        self.messagebar.timedMessage.connect(self._show_message)
        self.messagebar.collect('Created window')

        # -- Connect signals to messenger
        #self.saveData.logMessage.connect(self.messagebar.collect)
        
        # -- Connect other signals --
        #self.saveData.buttonSaveData.clicked.connect(self.save_to_file)

    def _show_message(self,msg):
        self.statusBar().showMessage(str(msg))
        print msg

    def _center_in_screen(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    '''
    def save_to_file(self):
        ' ''Triggered by button-clicked signal'' '
        self.saveData.to_file([self.params, self.dispatcherModel,
                               self.sm, self.results],
                              self.dispatcherModel.currentTrial,
                              experimenter=self.params['experimenter'].get_value(),
                              subject=self.params['subject'].get_value(),
                              paradigm=self.name)
    '''


    def closeEvent(self, event):
        '''
        Executed when closing the main window.
        This method is inherited from QtGui.QMainWindow, which explains
        its camelCase naming.
        '''
        #print 'ENTERED closeEvent()' # DEBUG
        #print 'Closing all connections.' # DEBUG
        #self.soundClient.shutdown()
        event.accept()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Enable Ctrl-C
    app=QtGui.QApplication.instance() # checks if QApplication already exists 
    if not app: # create QApplication if it doesnt exist 
        app = QtGui.QApplication(sys.argv)
    spkcal = SpeakerCalibration()
    spkcal.show()
    sys.exit(app.exec_())


