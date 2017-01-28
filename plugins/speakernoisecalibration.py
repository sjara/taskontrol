import sys
from PySide import QtCore
from PySide import QtGui
from taskontrol.core import messenger
from taskontrol.settings import rigsettings
import pyo
import signal
import time
import os
import numpy as np
import h5py

DEFAULT_AMPLITUDE = 0.1
AMPLITUDE_STEP = 0.0005
MAX_AMPLITUDE = 0.5

DEFAULT_INTENSITY = 60 # white noise overall intensity (dB-SPL)
DEFAULT_POWER = 40 # white noise spectral power (dB-SPL)

DATADIR = '/var/tmp/'

BUTTON_COLORS = {'on':'red','off':'black'}

class OutputButton(QtGui.QPushButton):
    '''Single button for manual output'''
    def __init__(self, soundServer, title, channel=1, parent=None):
        super(OutputButton, self).__init__(title, parent)

        self.soundServer = soundServer
        self.soundAmplitude = DEFAULT_AMPLITUDE
        self.channel = channel
        self.setCheckable(True)
        self.clicked.connect(self.toggleOutput)
        self.soundObj = pyo.Noise(mul=DEFAULT_AMPLITUDE)

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
        self.soundObj.out(chnl=self.channel)

    def change_amplitude(self,amplitude):
        self.soundAmplitude = amplitude
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
        self.channel=channel

        # -- Create graphical objects --
        layout = QtGui.QGridLayout()
        self.outputButtons = []
        self.amplitudeControl=[]

        self.outputButtons.append(OutputButton(self.soundServer, 'Noise Intensity', channel=self.channel))
        self.outputButtons.append(OutputButton(self.soundServer, 'Spectral Power', channel=self.channel))

        for indButton, outputButton in enumerate(self.outputButtons):
            self.amplitudeControl.append(AmplitudeControl(outputButton))
            layout.addWidget(self.outputButtons[indButton], indButton+1, 0)
            layout.addWidget(self.amplitudeControl[indButton], indButton+1, 1)

        self.setLayout(layout)
        self.setTitle('Speaker '+channelName)

    # If multiple amplitude controls
    def amplitude_array(self):
        amplitudeEach = np.empty(len(self.amplitudeControl))
        for indf,oneAmplitude in enumerate(self.amplitudeControl):
            amplitudeEach[indf] = oneAmplitude.value()
        return amplitudeEach

    #If single button
    # def amplitude_array(self):
    #     return np.array([self.amplitudeControl.value()])

class VerticalLine(QtGui.QFrame):
    def __init__(self,parent=None):
        super(VerticalLine, self).__init__(parent)
        self.setFrameStyle(QtGui.QFrame.VLine)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum,
                           QtGui.QSizePolicy.Expanding)

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
            fileNameOnly = 'speaker_noise_calibration_{0}.{1}'.format(date,fileExt)
            defaultFileName = os.path.join(dataDir,fileNameOnly)

        self.logMessage.emit('Saving data...')

        if self.interactive:
            fname,ffilter = QtGui.QFileDialog.getSaveFileName(self,'CHOOSE',DATADIR,'*.*')
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
            # dsetFreq = h5file.create_dataset('frequency',data=SOUND_FREQUENCIES)
            # dsetFreq.attrs['Units'] = 'Hz' # FIXME: hardcoded
            dsetRef = h5file.create_dataset('intensity',data=DEFAULT_INTENSITY)
            dsetRef.attrs['Units'] = 'dB-SPL' # FIXME: hardcoded
            dsetRef = h5file.create_dataset('power',data=DEFAULT_POWER)
            dsetRef.attrs['Units'] = 'dB-SPL' # FIXME: hardcoded
            dsetRef = h5file.create_dataset('computerSoundLevel',
                                            data=rigsettings.SOUND_VOLUME_LEVEL)
            dsetRef.attrs['Units'] = '%' # FIXME: hardcoded
        except UserWarning as uwarn:
            self.logMessage.emit(uwarn.message)
            print uwarn.message
        except:
            h5file.close()
            raise
        h5file.close()

        self.filename = fname
        self.logMessage.emit('Saved data to {0}'.format(fname))

class NoiseCalibration(QtGui.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(NoiseCalibration, self).__init__(parent)

        self.name = 'noisecalibration'
        self.soundServer = self.initialize_sound()

        # -- Add graphical widgets to main window --
        self.centralWidget = QtGui.QWidget()
        layoutMain = QtGui.QHBoxLayout()
        layoutRight = QtGui.QVBoxLayout()

        self.soundControlL = SoundControl(self.soundServer, channel=0, channelName='left')
        self.soundControlR = SoundControl(self.soundServer, channel=1, channelName='right')

        self.saveButton = SaveButton([self.soundControlL,self.soundControlR])

        noiseTargetIntensityLabel = QtGui.QLabel('Target noise intensity [dB-SPL]')
        self.noiseTargetIntensity = QtGui.QLineEdit()
        self.noiseTargetIntensity.setText(str(DEFAULT_INTENSITY))
        self.noiseTargetIntensity.setEnabled(False)
        powerTargetIntensityLabel = QtGui.QLabel('Target spectral power [dB-SPL]')
        self.powerTargetIntensity = QtGui.QLineEdit()
        self.powerTargetIntensity.setText(str(DEFAULT_POWER))
        self.powerTargetIntensity.setEnabled(False)
        computerSoundLevelLabel = QtGui.QLabel('Computer sound level [%]')
        self.computerSoundLevel = QtGui.QLineEdit()
        self.computerSoundLevel.setText(str(rigsettings.SOUND_VOLUME_LEVEL))
        self.computerSoundLevel.setEnabled(False)

        #TODO: Implement loading, probably not plotting though
        # self.loadButton = LoadButton([self.soundControlL,self.soundControlR])
        # self.plotButton = PlotButton([self.soundControlL,self.soundControlR])

        layoutRight.addWidget(self.saveButton)

        layoutRight.addWidget(noiseTargetIntensityLabel)
        layoutRight.addWidget(self.noiseTargetIntensity)
        layoutRight.addWidget(powerTargetIntensityLabel)
        layoutRight.addWidget(self.powerTargetIntensity)
        layoutRight.addWidget(computerSoundLevelLabel)
        layoutRight.addWidget(self.computerSoundLevel)

        # layoutRight.addWidget(self.loadButton)
        # layoutRight.addWidget(self.plotButton)
        layoutRight.addStretch()

        layoutMain.addWidget(self.soundControlL)
        layoutMain.addWidget(VerticalLine())
        layoutMain.addWidget(self.soundControlR)
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
        #TODO: enable saving and uncomment below
        self.saveButton.logMessage.connect(self.messagebar.collect)

        # -- Connect other signals --
        #self.saveData.buttonSaveData.clicked.connect(self.save_to_file)

    # def change_sound_type(self,soundTypeInd):
    #     for oneOutputButton in self.soundControlL.outputButtons:
    #         #oneOutputButton.create_sound(self.soundTypeList[soundTypeInd])
    #         oneOutputButton.soundType = self.soundTypeList[soundTypeInd]
    #     for oneOutputButton in self.soundControlR.outputButtons:
    #         #oneOutputButton.create_sound(self.soundTypeList[soundTypeInd])
    #         oneOutputButton.soundType = self.soundTypeList[soundTypeInd]

    def initialize_sound(self):
        s = pyo.Server(audio='jack').boot()
        #s = pyo.Server().boot()
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
        self.soundServer.shutdown()
        #self.pyoServer.shutdown()
        event.accept()
        
class Calibration(object):
    '''
    Reads data from file and finds appropriate amplitude for a desired
    sound intensity at a particular frequency.
    This class assumes two channels (left,right)
    '''
    def __init__(self,filename=None):
        if filename is not None:
            h5file = h5py.File(filename,'r')
            self.amplitude = h5file['amplitude'][...]
            self.intensity = h5file['intensity'][...]
            self.power = h5file['power'][...]
            h5file.close()
        else:
            self.amplitude = 0.1*np.ones((2,2))
            self.intensity = 60
            self.power = 40
        self.nChannels = self.amplitude.shape[0]
            
    def find_amplitude(self, type, intensity):
        '''
        Type: 0 for dB SPL, 1 for spectral power
        Returns an array with the amplitude for each channel.
        '''
        ampAtRef = self.amplitude[:,type]
        if type == 0:
            dBdiff = intensity-self.intensity
        elif type == 1:
            dBdiff = intensity-self.power
        ampFactor = 10**(dBdiff/20.0)
        return np.array(ampAtRef)*ampFactor

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Enable Ctrl-C
    app=QtGui.QApplication.instance() # checks if QApplication already exists
    if not app: # create QApplication if it doesnt exist
        app = QtGui.QApplication(sys.argv)
    spkcal = NoiseCalibration()
    spkcal.show()
    sys.exit(app.exec_())
    '''
    if 1:
        cal=Calibration('/tmp/speaker_calibration_20140322175816.h5')
        print cal.find_amplitude(1200,60)
        print cal.find_amplitude(1200,40)
    '''
