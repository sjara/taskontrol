"""
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

TO DO:
- Fix one speaker at a time (currently all sounds come out of both speakers)
- Add SpeakerNoiseCalibration class (GUI to calibrate)
- Fix NoiseCalibration.find_amplitude types (it should not be just a number)
"""


import sys
#import pyo
import signal
import time
import os
import numpy as np
import h5py
import scipy.signal
import matplotlib.pyplot as plt
from qtpy import QtWidgets as QtGui
from qtpy import QtCore
from taskontrol import paramgui
from taskontrol import rigsettings
from taskontrol.plugins import soundclient

SOUND_FREQUENCIES = np.logspace(np.log10(1000), np.log10(40000), 16)
SOUND_FREQUENCIES = np.sort(np.concatenate((SOUND_FREQUENCIES,[3000,5000,7000,11000,16000,24000])))
DEFAULT_AMPLITUDE = 0.01
AMPLITUDE_STEP = 0.0005
MAX_AMPLITUDE = 0.5

DEFAULT_INTENSITY = 60 # intensity used for tone and chord calibration (dB-SPL)
DEFAULT_POWER_RMS = 60 # RMS power in time domain (dB-SPL)
DEFAULT_POWER_NARROWBAND = 40 # average power of narrowband sound (dB-SPL)

DATADIR = '/var/tmp/'

BUTTON_COLORS = {'on':'red','off':'black'}

'''
# -- Set computer's sound level --
if hasattr(rigsettings,'SOUND_VOLUME_LEVEL'):
    baseVol = rigsettings.SOUND_VOLUME_LEVEL
    if baseVol is not None:
        os.system('amixer set Master {0}% > /dev/null'.format(baseVol))
        print('Set sound volume to {0}%'.format(baseVol))
'''

'''
def OLD_create_sound(soundParams):
    amplitude = soundParams['amplitude']
    if soundParams['type']=='sine':
        soundObjList = [pyo.Sine(freq=soundParams['frequency'],mul=amplitude)]
    if soundParams['type']=='chord':
        nTones = soundParams['ntones']  # Number of components in chord
        factor = soundParams['factor']  # Components will be in range [f/factor, f*factor]
        centerFreq = soundParams['frequency']
        freqEachComp = np.logspace(np.log10(centerFreq/factor),np.log10(centerFreq*factor),nTones)
        soundObjList = []
        for indcomp in range(nTones):
            soundObjList.append(pyo.Sine(freq=float(freqEachComp[indcomp]),mul=amplitude))
    if soundParams['type']=='noise':
        soundObjList = [pyo.Noise(mul=amplitude)]
    return soundObjList
'''

class OutputButton(QtGui.QPushButton):
    '''Single button for manual output'''
    def __init__(self, buttonID, soundClient, title, soundType='sine', channel=0, parent=None):
        super().__init__(title, parent)

        self.buttonID = buttonID
        self.soundClient = soundClient
        self.soundTitle = title
        self.soundAmplitude = DEFAULT_AMPLITUDE
        self.channel = channel
        self.soundType = soundType
        self.setCheckable(True)
        self.clicked.connect(self.toggleOutput)
        self.create_sound(soundType=soundType)
        '''
        self.soundObj = pyo.Sine(freq=self.soundFreq,mul=DEFAULT_AMPLITUDE)
        if soundFreq<40000:
            self.soundObj = pyo.Sine(freq=self.soundFreq,mul=DEFAULT_AMPLITUDE)
        else:
            self.soundObj = pyo.Noise(mul=DEFAULT_AMPLITUDE)
        '''
    def create_sound(self,soundType):
        duration = 3
        fade = 0.01
        if soundType=='sine':
            soundParams = {'type':'tone', 'frequency':int(self.soundTitle)}
        elif soundType=='chord':
            soundParams = {'type':'chord', 'frequency':int(self.soundTitle), 'ntones':12, 'factor':1.2}
        elif soundType=='noise':
            soundParams = {'type':'noise'}
        amplitude = [0, 0]
        amplitude[self.channel] = self.soundAmplitude
        soundParams.update({'amplitude':amplitude, 'duration':duration,
                            'fadein':fade, 'fadeout':fade})
        self.soundClient.set_sound(self.buttonID, soundParams)

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
        self.create_sound(soundType=self.soundType)
        #self.soundClient.play_sound(self.buttonID)
        self.soundClient.loop_sound(self.buttonID)

    def stop(self):
        '''Stop action.'''
        self.setChecked(False)
        stylestr = ''
        self.setStyleSheet(stylestr)
        self.soundClient.stop_sound(self.buttonID)

    '''
    def play_sound(self):
        for soundObj in self.soundObjList:
            soundObj.out(chnl=self.channel)
    '''
    
    def change_amplitude(self,amplitude):
        self.soundAmplitude = amplitude
        #for soundObj in self.soundObjList:
        #    soundObj.setMul(amplitude)

    '''
    def stop_sound(self):
        for soundObj in self.soundObjList:
            soundObj.stop()
    '''

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
        self.setValue(value)
        self.soundButton.change_amplitude(value)


class SoundControlGUI(QtGui.QGroupBox):
    def __init__(self, soundClient, channel=0, channelName='left', parent=None):
        super(SoundControlGUI, self).__init__(parent)
        self.soundClient = soundClient
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
            self.outputButtons[indf] = OutputButton(indf, self.soundClient, str(int(np.round(onefreq))),
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

    def smooth_amplitude(self):
        self.polyOrder = 4
        self.windowSize = 61
        self.nSamples = 100
        frequencies = self.soundFreqs
        logFreq = np.log10(frequencies)
        amplitudeData = []
        smoothAmplitude = []
        newLogFreq = np.linspace(np.log10(frequencies[0]),np.log10(frequencies[-1]),
                                 self.nSamples)
        newFreq = 10**newLogFreq
        thisAmpArray = self.amplitude_array()
        interpAmp = np.interp(newLogFreq, logFreq, thisAmpArray)
        smoothAmplitude = scipy.signal.savgol_filter(interpAmp, self.windowSize,
                                                     polyorder=self.polyOrder)
        return (newFreq, smoothAmplitude)


class NoiseSoundControlGUI(QtGui.QGroupBox):
    def __init__(self, soundClient, channel=0, channelName='left', parent=None):
        super(NoiseSoundControlGUI, self).__init__(parent)
        self.soundClient = soundClient
        self.channel=channel

        # -- Create graphical objects --
        layout = QtGui.QGridLayout()
        self.outputButtons = []
        self.amplitudeControl=[]

        self.outputButtons.append(OutputButton(1, self.soundClient, 'RMS Power', soundType='noise', channel=self.channel))
        self.outputButtons.append(OutputButton(2, self.soundClient, 'Narrowband Power', soundType='noise', channel=self.channel))

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


class LoadButton(QtGui.QPushButton):
    '''
    Note: this class does not change target intensity value.
          It loads data for the saved target intensity.
    '''
    logMessage = QtCore.Signal(str)
    def __init__(self, soundControlArray, parent=None):
        super(LoadButton, self).__init__('Load data', parent)
        self.soundControlArray = soundControlArray
        self.calData = None # Object to contain loaded data
        self.clicked.connect(self.load_data)
    def load_data(self):
        fname,ffilter = QtGui.QFileDialog.getOpenFileName(self,'Open calibration file',DATADIR,'*.h5')
        self.calData = Calibration(fname)
        self.update_values()
    def update_values(self):
        nChannels = 2 # FIXME: hardcoded
        for indch in range(nChannels):
            for indf, oneoutputButton in enumerate(self.soundControlArray[indch].outputButtons):
                oneAmplitudeControl = self.soundControlArray[indch].amplitudeControl[indf]
                thisAmp = self.calData.amplitude[indch, indf]
                #thisFreq = self.soundControlArray[indch]
                oneAmplitudeControl.change_amplitude(thisAmp)
                '''
                thisAmp = self.calData.find_amplitude(oneOutputButton.soundFreq,
                                                      self.calData.intensity)
                # NOTE: We are calculating values twice.1
                #       find_amplitude() finds value for both channels
                oneAmplitudeControl.setValue(thisAmp[indch])
                oneOutputButton.change_amplitude(thisAmp[indch])
                '''

class PlotButton(QtGui.QPushButton):
    '''
    '''
    def __init__(self, soundControlArray, parent=None):
        super(PlotButton, self).__init__('Plot results', parent)
        self.soundControlArray = soundControlArray
        self.clicked.connect(self.plot_data)
    def plot_data(self):
        frequencies = self.soundControlArray[0].soundFreqs
        amplitudeData = []
        for soundControl in self.soundControlArray:
            amplitudeData.append(soundControl.amplitude_array())
        amplitudeData = np.array(amplitudeData)
        import matplotlib.pyplot as plt
        plt.plot(frequencies,np.array(amplitudeData).T,'o-')
        plt.gca().set_xscale('log')
        plt.ylabel('Amplitude')
        plt.xlabel('Frequency (Hz)')
        plt.draw()
        plt.show()

#def smooth()
        
class PlotSmoothButton(QtGui.QPushButton):
    '''
    '''
    def __init__(self, soundControlArray, parent=None):
        super(PlotSmoothButton, self).__init__('Plot smooth', parent)
        self.soundControlArray = soundControlArray
        self.clicked.connect(self.plot_smooth_data)
    def plot_smooth_data(self):
        frequencies = self.soundControlArray[0].soundFreqs
        logFreq = np.log10(frequencies)
        amplitudeData = []
        smoothAmplitude = []
        for soundControl in self.soundControlArray:
            thisAmpArray = soundControl.amplitude_array()
            amplitudeData.append(thisAmpArray)
            (newFreq, thisSmoothAmp) = soundControl.smooth_amplitude()
            smoothAmplitude.append(thisSmoothAmp)
        plt.plot(frequencies, np.array(amplitudeData).T, 'o-')
        plt.plot(newFreq, np.array(smoothAmplitude).T, '-', lw=2)
        plt.gca().set_xscale('log')
        plt.ylabel('Amplitude')
        plt.xlabel('Frequency (Hz)')
        plt.draw()
        plt.show()

class ApplySmoothButton(QtGui.QPushButton):
    '''
    '''
    def __init__(self, soundControlArray, parent=None):
        super(ApplySmoothButton, self).__init__('Apply smoothing', parent)
        self.soundControlArray = soundControlArray
        self.clicked.connect(self.apply_smoothing)
    def apply_smoothing(self):
        for soundControl in self.soundControlArray:
            frequency = soundControl.soundFreqs
            (newFreq, thisSmoothAmp) = soundControl.smooth_amplitude()
            newAmps = np.interp(np.log10(frequency), np.log10(newFreq),
                                thisSmoothAmp)
            for indf, thisNewAmp in enumerate(newAmps):
                soundControl.amplitudeControl[indf].change_amplitude(thisNewAmp)

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
            # FIXME: on 2020-02-02 date appeared to be False instead of None, why?
            if date is None or date==False:
                date = time.strftime('%Y%m%d%H%M%S',time.localtime())
            soundType = self.soundControlArray[0].outputButtons[0].soundType
            dataRootDir = self.datadir
            fileExt = 'h5'
            dataDir = dataRootDir #os.path.join(dataRootDir)
            if not os.path.exists(dataDir):
                os.makedirs(dataDir)
            fileNameOnly = 'speaker_calibration_{0}_{1}.{2}'.format(soundType,date,fileExt)
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

        ###print(amplitudeData) # DEBUG

        # -- Create data file --
        # FIXME: check that the file opened correctly
        if os.path.exists(fname):
            self.logMessage.emit('File exists. I will rewrite {0}'.format(fname))
        h5file = h5py.File(fname,'w')

        try:
            if soundType=='noise':
                dsetAmp = h5file.create_dataset('amplitudeRMS',data=amplitudeData[:,0]) # FIXME: hardcoded method of separating amplitudes
                dsetAmp.attrs['Channels'] = 'left,right' # FIXME: hardcoded
                dsetAmp.attrs['Units'] = '(none)' # FIXME: hardcoded
                dsetAmp = h5file.create_dataset('amplitudeNarrowband',data=amplitudeData[:,1])
                dsetAmp.attrs['Channels'] = 'left,right' # FIXME: hardcoded
                dsetAmp.attrs['Units'] = '(none)' # FIXME: hardcoded
                dsetRef = h5file.create_dataset('powerRMS',data=DEFAULT_POWER_RMS)
                dsetRef.attrs['Units'] = 'dB-SPL' # FIXME: hardcoded
                dsetRef = h5file.create_dataset('powerNarrowband',data=DEFAULT_POWER_NARROWBAND)
                dsetRef.attrs['Units'] = 'dB-SPL' # FIXME: hardcoded
            else:
                dsetAmp = h5file.create_dataset('amplitude',data=amplitudeData)
                dsetAmp.attrs['Channels'] = 'left,right' # FIXME: hardcoded
                dsetAmp.attrs['Units'] = '(none)' # FIXME: hardcoded
                dsetFreq = h5file.create_dataset('frequency',data=SOUND_FREQUENCIES)
                dsetFreq.attrs['Units'] = 'Hz' # FIXME: hardcoded
                dsetRef = h5file.create_dataset('intensity',data=DEFAULT_INTENSITY)
                dsetRef.attrs['Units'] = 'dB-SPL' # FIXME: hardcoded
                
            if rigsettings.SOUND_VOLUME_LEVEL is None:
                computerSoundLevel = np.nan
            else:
                computerSoundLevel = rigsettings.SOUND_VOLUME_LEVEL
            dsetRef = h5file.create_dataset('computerSoundLevel',
                                            data=computerSoundLevel)
            dsetRef.attrs['Units'] = '%' # FIXME: hardcoded
        except UserWarning as uwarn:
            self.logMessage.emit(uwarn.message)
            print(uwarn.message)
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


class SpeakerCalibrationGUI(QtGui.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(SpeakerCalibrationGUI, self).__init__(parent)

        self.name = 'speakercalibration'
        #self.soundClient = self.initialize_sound()
        self.soundClient = soundclient.SoundClient()

        # -- Add graphical widgets to main window --
        self.centralWidget = QtGui.QWidget()
        layoutMain = QtGui.QHBoxLayout()
        layoutRight = QtGui.QVBoxLayout()

        self.soundControlL = SoundControlGUI(self.soundClient, channel=0, channelName='left')
        self.soundControlR = SoundControlGUI(self.soundClient, channel=1, channelName='right')

        self.saveButton = SaveButton([self.soundControlL, self.soundControlR])
        soundTypeLabel = QtGui.QLabel('Sound type')
        self.soundTypeMenu = QtGui.QComboBox()
        self.soundTypeList = ['sine','chord']
        self.soundTypeMenu.addItems(self.soundTypeList)
        self.soundTypeMenu.activated.connect(self.change_sound_type)
        soundTargetIntensityLabel = QtGui.QLabel('Target intensity [dB-SPL]')
        self.soundTargetIntensity = QtGui.QLineEdit()
        self.soundTargetIntensity.setText(str(DEFAULT_INTENSITY))
        #self.soundTargetIntensity.setEnabled(False)
        computerSoundLevelLabel = QtGui.QLabel('Computer sound level [%]')
        self.computerSoundLevel = QtGui.QLineEdit()
        self.computerSoundLevel.setText(str(rigsettings.SOUND_VOLUME_LEVEL))
        self.computerSoundLevel.setEnabled(False)
        self.loadButton = LoadButton([self.soundControlL,self.soundControlR])
        self.plotButton = PlotButton([self.soundControlL,self.soundControlR])
        self.plotSmoothButton = PlotSmoothButton([self.soundControlL,self.soundControlR])
        self.applySmoothButton = ApplySmoothButton([self.soundControlL,self.soundControlR])

        layoutRight.addWidget(self.saveButton)
        layoutRight.addWidget(soundTypeLabel)
        layoutRight.addWidget(self.soundTypeMenu)
        layoutRight.addWidget(soundTargetIntensityLabel)
        layoutRight.addWidget(self.soundTargetIntensity)
        layoutRight.addWidget(computerSoundLevelLabel)
        layoutRight.addWidget(self.computerSoundLevel)
        layoutRight.addWidget(self.loadButton)
        layoutRight.addWidget(self.plotButton)
        layoutRight.addStretch()
        layoutRight.addWidget(self.plotSmoothButton)
        layoutRight.addWidget(self.applySmoothButton)

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
        self.messagebar = paramgui.Messenger()
        self.messagebar.timedMessage.connect(self._show_message)
        self.messagebar.collect('Created window')

        # -- Connect signals to messenger
        self.saveButton.logMessage.connect(self.messagebar.collect)

        # -- Connect other signals --
        #self.saveData.buttonSaveData.clicked.connect(self.save_to_file)

    def change_sound_type(self,soundTypeInd):
        for oneOutputButton in self.soundControlL.outputButtons:
            #oneOutputButton.create_sound(self.soundTypeList[soundTypeInd])
            oneOutputButton.soundType = self.soundTypeList[soundTypeInd]
        for oneOutputButton in self.soundControlR.outputButtons:
            #oneOutputButton.create_sound(self.soundTypeList[soundTypeInd])
            oneOutputButton.soundType = self.soundTypeList[soundTypeInd]

    """
    def initialize_sound(self):
        '''
        s = pyo.Server(audio='jack').boot()
        s.start()
        '''
        return s
    """
        
    def _show_message(self,msg):
        self.statusBar().showMessage(str(msg))
        print(msg)

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
        #print('ENTERED closeEvent()') # DEBUG
        #print('Closing all connections.') # DEBUG
        self.soundClient.shutdown()
        #self.pyoServer.shutdown()
        event.accept()


class NoiseSpeakerCalibrationGUI(QtGui.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(NoiseSpeakerCalibrationGUI, self).__init__(parent)

        self.name = 'noisespeakercalibration'
        #self.soundClient = self.initialize_sound()
        self.soundClient = soundclient.SoundClient()

        # -- Add graphical widgets to main window --
        self.centralWidget = QtGui.QWidget()
        layoutMain = QtGui.QHBoxLayout()
        layoutRight = QtGui.QVBoxLayout()

        self.soundControlL = NoiseSoundControlGUI(self.soundClient, channel=0, channelName='left')
        self.soundControlR = NoiseSoundControlGUI(self.soundClient, channel=1, channelName='right')
        for oneOutputButton in self.soundControlL.outputButtons:
            oneOutputButton.soundType = 'noise'
        for oneOutputButton in self.soundControlR.outputButtons:
            oneOutputButton.soundType = 'noise'

        self.saveButton = SaveButton([self.soundControlL,self.soundControlR])

        noiseTargetIntensityLabel = QtGui.QLabel('Target RMS power in time domain [dB-SPL]')
        self.noiseTargetIntensity = QtGui.QLineEdit()
        self.noiseTargetIntensity.setText(str(DEFAULT_POWER_RMS))
        #self.noiseTargetIntensity.setEnabled(False)
        powerTargetIntensityLabel = QtGui.QLabel('Target power at specific frequency [dB-SPL]')
        self.powerTargetIntensity = QtGui.QLineEdit()
        self.powerTargetIntensity.setText(str(DEFAULT_POWER_NARROWBAND))
        #self.powerTargetIntensity.setEnabled(False)
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
        self.messagebar = paramgui.Messenger()
        self.messagebar.timedMessage.connect(self._show_message)
        self.messagebar.collect('Created window')

        # -- Connect signals to messenger
        #TODO: enable saving and uncomment below
        self.saveButton.logMessage.connect(self.messagebar.collect)

    def initialize_sound(self):
        s = pyo.Server(audio='jack').boot()
        #s = pyo.Server().boot()
        s.start()
        return s

    def _show_message(self,msg):
        self.statusBar().showMessage(str(msg))
        print(msg)

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
        #print('ENTERED closeEvent()') # DEBUG
        #print('Closing all connections.') # DEBUG
        self.soundClient.shutdown()
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
            self.frequency = h5file['frequency'][...]
            self.intensity = h5file['intensity'][...]
            h5file.close()
        else:
            self.amplitude = 0.01*np.ones((2,2))
            self.frequency = np.array([1000,4000])
            self.intensity = 60
        self.nChannels = self.amplitude.shape[0]

    def find_amplitude(self,frequency,intensity):
        '''
        Linear interpolation (in log-freq) to find appropriate amplitude
        Returns an array with the amplitude for each channel.
        '''
        ampAtRef = []
        for chn in range(self.nChannels):
            thisAmp = np.interp(np.log10(frequency),np.log10(self.frequency),
                                self.amplitude[chn,:])
            ampAtRef.append(thisAmp)
        # Find factor from ref intensity
        dBdiff = intensity-self.intensity
        ampFactor = 10**(dBdiff/20.0)
        return np.array(ampAtRef)*ampFactor
    
    def find_amplitudes(self,frequencies,intensity):
        '''
        Find amplitudes for multiple frequencies. 
        TODO: 
        - This functions needs to be merged with find_amplitude()
        - It needs to be made more efficient. Not looping and appending to list.
        Returns an array (nFreq, nChan) with the amplitude for each channel, for each freq.
        '''
        ampAll = []
        for frequency in frequencies:
            ampAtRef = []
            for chn in range(self.nChannels):
                thisAmp = np.interp(np.log10(frequency),np.log10(self.frequency),
                                    self.amplitude[chn,:])
                ampAtRef.append(thisAmp)
                # Find factor from ref intensity
                dBdiff = intensity-self.intensity
                ampFactor = 10**(dBdiff/20.0)
                ampsThisFreq = np.array(ampAtRef)*ampFactor
            ampAll.append(ampsThisFreq)
        return np.array(ampAll)
    

class NoiseCalibration(object):
    '''
    Reads data from file and finds appropriate amplitude for a desired
    white noise power.
    This class assumes two channels (left,right)
    '''
    def __init__(self,filename=None):
        if filename is not None:
            h5file = h5py.File(filename,'r')
            self.amplitudeRMS = h5file['amplitudeRMS'][...]
            self.amplitudeNarrowband = h5file['amplitudeNarrowband'][...]
            self.powerRMS = h5file['powerRMS'][...]
            self.powerNarrowband = h5file['powerNarrowband'][...]
            h5file.close()
        else:
            self.amplitudeRMS = 0.1*np.ones(2)
            self.amplitudeNarrowband = 0.1*np.ones(2)
            self.powerRMS = 60
            self.powerNarrowband = 40
        self.nChannels = self.amplitudeRMS.shape[0]

    def find_amplitude(self, intensity, type='rms'):
        '''
        type:
          'rms': intensity corresponds to RMS power in time domain.
          'narrowband': intensity corresponds to power at one frequency (in the audible range).
        Returns an array with the amplitude for each channel.
        '''
        if type == 'rms':
            ampAtRef = self.amplitudeRMS
            dBdiff = intensity-self.powerRMS
        elif type == 'narrowband':
            ampAtRef = self.amplitudeNarrowband
            dBdiff = intensity-self.powerNarrowband
        ampFactor = 10**(dBdiff/20.0)
        return np.array(ampAtRef)*ampFactor


if __name__ == "__main__":
    
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Enable Ctrl-C
    app=QtGui.QApplication.instance() # checks if QApplication already exists
    if not app: # create QApplication if it doesnt exist
        app = QtGui.QApplication(sys.argv)
    args = sys.argv[1:]
    if len(args):
        if args[0]=='noise':
            spkcal = NoiseSpeakerCalibrationGUI()
    else:
        spkcal = SpeakerCalibrationGUI()
    spkcal.show()
    sys.exit(app.exec_())
    '''
    if 1:
        cal=Calibration('/tmp/speaker_calibration_20140322175816.h5')
        print(cal.find_amplitude(1200,60))
        print(cal.find_amplitude(1200,40))
    '''

