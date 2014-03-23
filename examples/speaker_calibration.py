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
import signal
import time
import os
import numpy as np
import h5py

SOUND_FREQUENCIES = np.logspace(np.log10(1000), np.log10(40000), 16)
DEFAULT_AMPLITUDE = 0.01
AMPLITUDE_STEP = 0.0005
MAX_AMPLITUDE = 0.05

DATADIR = '/tmp/'

BUTTON_COLORS = {'on':'red','off':'black'}

class OutputButton(QtGui.QPushButton):
    '''Single button for manual output'''
    def __init__(self, soundServer, soundFreq, channel=1, parent=None):
        super(OutputButton, self).__init__(str(int(np.round(soundFreq))), parent)

        self.soundServer = soundServer
        self.soundFreq = soundFreq
        self.channel = channel
        self.setCheckable(True)
        #self.connect(self,QtCore.SIGNAL('clicked()'),self.toggleOutput)
        self.clicked.connect(self.toggleOutput)
        #self.soundObj = pyo.Sine(freq=self.soundFreq,mul=0.02).mix(2)
        self.soundObj = pyo.Sine(freq=self.soundFreq,mul=DEFAULT_AMPLITUDE)
        
    def toggleOutput(self):
        if self.isChecked():
            self.start()
        else:
            self.stop()

    def start(self):
        '''Start action.'''
        self.setChecked(True)
        stylestr = 'QPushButton {{color: {0}; font: bold}}'.format(BUTTON_COLORS['on'])
        self.setStyleSheet(stylestr)
        self.play_sound()

    def stop(self):
        '''Stop action.'''
        self.setChecked(False)
        stylestr = ''
        self.setStyleSheet(stylestr)
        self.stop_sound()
        
    def play_sound(self):
        #self.soundObj = pyo.Sine(freq=soundfreq,mul=0.02).mix(2).out()
        #self.soundObj.setMul(0.01)  
        self.soundObj.out(chnl=self.channel)

    def change_amplitude(self,amplitude):
        self.soundObj.setMul(amplitude)

    def stop_sound(self):
        self.soundObj.stop()

class AmplitudeControl(QtGui.QDoubleSpinBox):
    def __init__(self,soundButton,parent=None):
        super(AmplitudeControl,self).__init__(parent)
        self.setRange(0,MAX_AMPLITUDE)
        self.setSingleStep(AMPLITUDE_STEP)
        self.setDecimals(4)
        self.setValue(DEFAULT_AMPLITUDE)
        self.soundButton = soundButton
        self.valueChanged.connect(self.change_amplitude)
    def change_amplitude(self,value):
        self.soundButton.change_amplitude(value)

class SoundControl(QtGui.QGroupBox):
    def __init__(self, soundServer, channel=0, channelName='left', parent=None):
        super(SoundControl, self).__init__(parent)
        self.soundServer = soundServer
        self.soundFreqs = SOUND_FREQUENCIES
        # -- Create graphical objects --
        layout = QtGui.QGridLayout()
        nFreq = len(self.soundFreqs)
        self.outputButtons = nFreq*[None]
        self.amplitudeControl = nFreq*[None]
        self.channel = channel
        
        stopAllButton = QtGui.QPushButton('STOP ALL')
        layout.addWidget(stopAllButton, 0, 1)
        stopAllButton.clicked.connect(self.stop_all)
        playAllButton = QtGui.QPushButton('PLAY ALL')
        layout.addWidget(playAllButton, 0, 0)
        playAllButton.clicked.connect(self.play_all)

        for indf,onefreq in enumerate(self.soundFreqs):
            self.outputButtons[indf] = OutputButton(self.soundServer,onefreq,
                                                    channel=self.channel)
            self.amplitudeControl[indf] = AmplitudeControl(self.outputButtons[indf])
            layout.addWidget(self.outputButtons[indf], indf+1, 0)
            layout.addWidget(self.amplitudeControl[indf], indf+1, 1)
            
        self.setLayout(layout)
        self.setTitle('Speaker '+channelName)
    
    def play_all(self):
        for oneButton in self.outputButtons:
            oneButton.start()

    def stop_all(self):
        for oneButton in self.outputButtons:
            oneButton.stop()

    def amplitude_array(self):
        amplitudeEach = np.empty(len(self.amplitudeControl))
        for indf,oneAmplitude in enumerate(self.amplitudeControl):
            amplitudeEach[indf] = oneAmplitude.value()
        return amplitudeEach


class SaveButton(QtGui.QPushButton):
    '''
    '''
    logMessage = QtCore.Signal(str)
    def __init__(self, soundControlArray, parent=None):
        super(SaveButton, self).__init__('Save calibration', parent)
        self.soundControlArray = soundControlArray       
        self.clicked.connect(self.save_data)
        self.filename = None
        self.datadir = DATADIR
        self.interactive = False
    def save_data(self, date=None, filename=None):
        if filename is not None:
            defaultFileName = filename
        else:
            if date is None:
                date = time.strftime('%Y%m%d%H%M%S',time.localtime())
            dataRootDir = self.datadir
            fileExt = 'h5'
            dataDir = dataRootDir #os.path.join(dataRootDir)
            if not os.path.exists(dataDir):
                os.makedirs(dataDir)
            fileNameOnly = 'speaker_calibration_{0}.{1}'.format(date,fileExt)
            defaultFileName = os.path.join(dataDir,fileNameOnly)

        self.logMessage.emit('Saving data...')

        if self.interactive:
            fname,ffilter = QtGui.QFileDialog.getSaveFileName(self,'CHOOSE','/tmp/','*.*')
            if not fname:
                self.logMessage.emit('Saving cancelled.')
                return
        else:
            fname = defaultFileName
        
        # Create array with amplitudes from all channels
        amplitudeData = []
        for soundControl in self.soundControlArray:
            amplitudeData.append(soundControl.amplitude_array())
        amplitudeData = np.array(amplitudeData)

        ###print amplitudeData ###DEBUG

        # -- Create data file --
        # FIXME: check that the file opened correctly
        if os.path.exists(fname):
            self.logMessage.emit('File exists. I will rewrite {0}'.format(fname))
        h5file = h5py.File(fname,'w')

        try:
            dsetAmp = h5file.create_dataset('amplitude',data=amplitudeData)
            dsetAmp.attrs['Channels'] = 'left,right' # FIXME: hardcoded
            dsetAmp.attrs['Units'] = '(none)' # FIXME: hardcoded
            dsetFreq = h5file.create_dataset('frequency',data=SOUND_FREQUENCIES)
            dsetFreq.attrs['Units'] = 'Hz' # FIXME: hardcoded
            dsetRef = h5file.create_dataset('reference',data=[60])
            dsetRef.attrs['Units'] = 'dB-SPL' # FIXME: hardcoded
        except UserWarning as uwarn:
            self.logMessage.emit(uwarn.message)
            print uwarn.message
        except:
            h5file.close()
            raise
        h5file.close()
 
        self.filename = fname
        self.logMessage.emit('Saved data to {0}'.format(fname))
    
class VerticalLine(QtGui.QFrame):
    def __init__(self,parent=None):
        super(VerticalLine, self).__init__(parent)
        self.setFrameStyle(QtGui.QFrame.VLine)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum,
                           QtGui.QSizePolicy.Expanding)
     
    
class SpeakerCalibration(QtGui.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(SpeakerCalibration, self).__init__(parent)

        self.name = 'speakercalibration'
        self.soundServer = self.initializeSound()

        # -- Add graphical widgets to main window --
        self.centralWidget = QtGui.QWidget()
        layoutMain = QtGui.QHBoxLayout()
        layoutRight = QtGui.QVBoxLayout()
               
        soundControlL = SoundControl(self.soundServer, channel=0, channelName='left')
        soundControlR = SoundControl(self.soundServer, channel=1, channelName='right')        

        self.saveButton = SaveButton([soundControlL,soundControlR])
        
        layoutRight.addWidget(self.saveButton)
        layoutRight.addStretch()

        layoutMain.addWidget(soundControlL)
        layoutMain.addWidget(VerticalLine())
        layoutMain.addWidget(soundControlR)
        layoutMain.addWidget(VerticalLine())
        layoutMain.addLayout(layoutRight)
        

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
        self.saveButton.logMessage.connect(self.messagebar.collect)
        
        # -- Connect other signals --
        #self.saveData.buttonSaveData.clicked.connect(self.save_to_file)

    def initializeSound(self):
        s = pyo.Server(audio='jack').boot()
        s.start()
        return s

    def _show_message(self,msg):
        self.statusBar().showMessage(str(msg))
        print msg

    def _center_in_screen(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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


