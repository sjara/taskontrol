"""
Plugin for presenting sounds (by communicating with a sound server).

You can choose what sound server to use by changing rigsettings.py.
The available servers are:
1. pyo (which uses jack)
2. pygame (this is useful when using taskontrol on emulator mode)
3. jack (this uses jackclient directly)

To use pyo or jack with low latency, you need to have jackd running.
In Ubuntu you can jackd with:
pasuspender -- /usr/bin/jackd -r -dalsa -dhw:STX -r192000 -p512 -n2

where STX is the name of the soundcard. Usually STX or DX.
"""

"""
Other options are:
pasuspender -- /usr/bin/jackd -r -dalsa -dhw:0 -r41000 -p512 -n2
pasuspender -- /usr/bin/jackd -R -dalsa -dhw:M2496 -r96000 -p128 -n2

You may want to test the sound first. 

- Without jack, you can test with:
speaker-test -r 41000 -t sine -f 8000

- And test pyo:
import pyo
import time
s = pyo.Server(audio='jack').boot()
s.start()
soundObj = pyo.Sine(freq=90000,mul=0.1).mix(2).out(dur=1)
time.sleep(1)
"""

import os
import sys
import time
import threading
import numpy as np
import tempfile
import serial
#from .. import rigsettings
from taskontrol import rigsettings
if rigsettings.SOUND_SERVER=='jack':
    import jack
elif rigsettings.SOUND_SERVER=='pygame':
    import pygame
elif rigsettings.SOUND_SERVER=='pyo':
    from taskontrol.plugins import soundserverpyo
else:
    raise("'{}' if not a valid sound server type.".format(rigsettings.SOUND_SERVER))

############ FIX THIS AT THE END (once other servers are implemented ##############
if rigsettings.STATE_MACHINE_TYPE=='arduino_due':
    SERIALTRIGGER = True
elif rigsettings.STATE_MACHINE_TYPE=='emulator':
    #from taskontrol.plugins import smemulator
    SERIALTRIGGER = False
else:
    raise ValueError('STATE_MACHINE_TYPE not recognized.')


# NOTE: all parameters for the sound server (sampling rate, etc)
#       are defined in the script that runs jackd, not on this file.

#SOUND_SERVER = rigsettings.SOUND_SERVER
SERIAL_PORT_PATH= rigsettings.SOUND_TRIGGER_PORT
SERIAL_BAUD_RATE = 115200  # Should be the same in statemachine.ino
SERIAL_TIMEOUT = 0.1 #None
'''
SOUND_CARD = rigsettings.SOUND_SERVER['soundCard']
SAMPLING_RATE = rigsettings.SOUND_SERVER['samplingRate']
N_CHANNELS = rigsettings.SOUND_SERVER['nChannels']
BUFFER_SIZE = rigsettings.SOUND_SERVER['bufferSize']
REALTIME = rigsettings.SOUND_SERVER['realtime']
'''

MAX_NSOUNDS = 128 # According to the serial protocol.
STOP_ALL_SOUNDS = 128  # SoundID to stop all sounds

RISETIME = 0.002
FALLTIME = 0.002

randomGen = np.random.default_rng()

# -- Set computer's sound level (for Linux only) --
if hasattr(rigsettings,'SOUND_VOLUME_LEVEL'):
    baseVol = rigsettings.SOUND_VOLUME_LEVEL
    if baseVol is not None:
        os.system('amixer set Master {0}% > /dev/null'.format(baseVol))
        # Change volume of the first two sound-cards
        #os.system('amixer -c 0 set Master {0}% > /dev/null'.format(baseVol))
        #os.system('amixer -c 1 set Master {0}% > /dev/null'.format(baseVol))
        print('Set sound volume to {0}%'.format(baseVol))


def apply_rise_fall(waveform, samplingRate, riseTime, fallTime):
    nSamplesRise = round(samplingRate * riseTime)
    nSamplesFall = round(samplingRate * fallTime)
    riseVec = np.linspace(0, 1, nSamplesRise)
    fallVec = np.linspace(1, 0, nSamplesFall)
    newWaveform = waveform.copy()
    newWaveform[:nSamplesRise] *= riseVec
    newWaveform[-nSamplesRise:] *= fallVec
    return newWaveform


def create_soundwave(soundParams, samplingRate=44100, nChannels=2,
                     risetime=RISETIME, falltime=FALLTIME):
        timeVec = np.arange(0, soundParams['duration'], 1/samplingRate)
        if isinstance(soundParams['amplitude'],list) or \
           isinstance(soundParams['amplitude'],np.ndarray):
            soundAmp = np.array(soundParams['amplitude'])
        else:
            soundAmp = np.tile(soundParams['amplitude'], nChannels)
        if soundParams['type']=='tone':
            soundWave = np.sin(2*np.pi*soundParams['frequency']*timeVec)
        elif soundParams['type']=='chord':
            freqEachComp = np.logspace(np.log10(soundParams['frequency']/soundParams['factor']),
                                       np.log10(soundParams['frequency']*soundParams['factor']),
                                       soundParams['ntones'])
            soundWave = np.zeros(len(timeVec))
            for indcomp, freqThisComp in enumerate(freqEachComp):
                soundWave += np.sin(2*np.pi*freqThisComp*timeVec)
        elif soundParams['type']=='noise':
            soundWave = randomGen.uniform(-1,1,len(timeVec))
        elif soundParams['type']=='AM':
            modFactor = soundParams['modDepth']/100.0 if 'modDepth' in soundParams else 1.0
            multTerm = modFactor*0.5
            addTerm = (1-modFactor*0.5)
            modFreq = soundParams['modFrequency']
            envelope = addTerm + multTerm*np.sin(2*np.pi*modFreq*timeVec + np.pi/2)
            carrier = randomGen.uniform(-1,1,len(timeVec))
            soundWave = envelope*carrier
        elif soundParams['type']=='fromfile':
            pass
        soundWave = apply_rise_fall(soundWave, samplingRate, risetime, falltime)
        soundWave = soundAmp[:,np.newaxis] * np.tile(soundWave,(nChannels,1))
        return timeVec,soundWave


class SoundServerPygame(object):
    def __init__(self, risetime=RISETIME, falltime=FALLTIME):
        self.riseTime = risetime
        self.fallTime = falltime
        self.samplingRate = 44100
        self.nChannels = 2  # As of 2020-11-14, it only works for 2 channels
        self.bufferSize = 4*512
        pygame.mixer.init(self.samplingRate, size=-16,
                          channels=self.nChannels, buffer=self.bufferSize)
        
    def to_signed_int16(self, waveform):
        return (waveform*32767).astype(np.int16)
    
    def create_sound(self, soundParams):
        timeVec, soundWave = create_soundwave(soundParams, self.samplingRate,
                                              self.nChannels, self.riseTime, self.fallTime)
        # NOTE: pygame requires C-contiguous arrays of size [nSamples,nChannels]
        soundWave = np.ascontiguousarray(soundWave.T)
        #soundWave = soundAmp * np.ascontiguousarray(np.tile(soundWave,(self.nChannels,1)).T)
        #soundWave = self.apply_rise_fall(soundWave)
        soundObj = pygame.sndarray.make_sound(self.to_signed_int16(soundWave))
        return soundObj, soundWave
    
    def play_sound(self, soundObj, soundWave):
        soundObj.play()
        
    def stop_sound(self, soundObj):
        soundObj.stop()


class SoundPlayer(threading.Thread):
    def __init__(self, servertype, serialtrigger=True):
        """
        servertype (str): 'jack', 'pygame', 'pyo'
        """
        threading.Thread.__init__(self)
        self.serialtrigger = serialtrigger
        self.ser = None
        self._stop = threading.Event()
        self._done = threading.Event()
        self.soundServerType = servertype

        if self.soundServerType=='pygame':
            self.soundServer = SoundServerPygame()
        elif self.soundServerType=='pyo':
            USEJACK = rigsettings.STATE_MACHINE_TYPE!='emulator'
            self.soundServer = soundserverpyo.SoundServerPyo(RISETIME, FALLTIME, USEJACK)
        else:
            raise ValueError('Sound server type not recognized.')

        # -- Set sync channel --
        if rigsettings.SOUND_SYNC_CHANNEL is not None:
            self.soundServer.set_sync(rigsettings.SOUND_SYNC_CHANNEL,
                                      rigsettings.SOUND_SYNC_AMPLITUDE,
                                      rigsettings.SOUND_SYNC_FREQUENCY)
        
        if self.serialtrigger:
            self.init_serial()
        
        self.sounds = MAX_NSOUNDS*[None]     # List of sound objects like pyo.Fader()
        self.soundwaves = MAX_NSOUNDS*[None] # List of waveforms like pyo.Sine()

        # Dictionary with sound parameters. Each key is one soundID.
        self.soundsParamsDict = {}
        
    def run(self):
        '''Execute thread'''
        if self.serialtrigger:
            while not self.stopped():
                onechar = self.ser.read(1)
                if onechar:
                    soundID = ord(onechar)
                    if soundID==STOP_ALL_SOUNDS:
                        self.stop_all()
                    else:
                        self.play_sound(soundID)
        else:
            '''Fake serial mode'''
            tempDir = tempfile.gettempdir()
            fakeSerial = open(os.path.join(tempDir,'serialoutput.txt'), 'r')
            while not self.stopped():
                oneval = fakeSerial.read()
                time.sleep(0.01)
                if len(oneval):
                    soundID = int(oneval)
                    try:
                        if soundID==STOP_ALL_SOUNDS:
                            self.stop_all()
                        else:
                            self.play_sound(soundID)
                    except Exception as exc:
                        print('[soundclient.py] An error occurred while '+\
                              'playing sounds. {}'.format(exc))
            if fakeSerial:
                fakeSerial.close()
        self._done.set()

    def init_serial(self):
        print('Connecting to serial port')
        self.ser = serial.Serial(SERIAL_PORT_PATH, SERIAL_BAUD_RATE, timeout=SERIAL_TIMEOUT)

    def set_sound(self, soundID, soundParams):
        '''
        soundParams is a dictionary that defines a sound, for example
        {'type':'tone', 'frequency':200, 'duration':0.2, 'amplitude':0.1}
        {'type':'fromfile','filename':'/tmp/sound.wav','duration':None,'channel':0,'amplitude':0.1}
        channel can be 'left', 'right', 'both'
        '''
        self.soundsParamsDict[soundID] = soundParams
        (self.sounds[soundID] ,self.soundwaves[soundID]) = \
            self.create_sound(self.soundsParamsDict[soundID])

    def create_sound(self, soundParams):
        (soundObj, soundWaveObj) =  self.soundServer.create_sound(soundParams)
        return (soundObj, soundWaveObj)
        
    def play_sound(self, soundID):
        #self.soundServer.play_sound(soundID)
        self.soundServer.play_sound(self.sounds[soundID] ,self.soundwaves[soundID])
        
    def stop_all(self):
        for soundID in self.soundsParamsDict.keys():
            self.sounds[soundID].stop()
    
    def stopped(self):
        return self._stop.isSet()

    def shutdown(self):
        '''Stop thread loop and shutdown pyo sound server'''
        self._stop.set() # Set flag to stop thread (checked on the thread loop).
        while not self._done.isSet(): # Make sure the loop stopped before shutdown.
            pass
        self.soundServer.shutdown()


class SoundClient(object):
    '''
    Object for connecting to the sound server and defining sounds.
    '''

    #def __init__(self, serialtrigger=True):
    def __init__(self, soundserver=rigsettings.SOUND_SERVER, serialtrigger=SERIALTRIGGER):
        self.soundPlayerThread = SoundPlayer(soundserver, serialtrigger=serialtrigger)
        #self.soundPlayerThread = SoundPlayer(serialtrigger=SERIALTRIGGER)
        self.sounds = self.soundPlayerThread.sounds
        self.soundwaves = self.soundPlayerThread.soundwaves
        self.soundPlayerThread.daemon=True

    def start(self):
        self.soundPlayerThread.start()

    def set_sound(self,soundID,soundParams):
        self.soundPlayerThread.set_sound(soundID,soundParams)

    '''
    def create_sounds(self):
        # FIXME: should be removed. set_sound should create the sound.
        self.soundPlayerThread.create_sounds()
    '''

    def play_sound(self,soundID):
        # FIXME: check that this sound as been defined
        self.soundPlayerThread.play_sound(soundID)

    def stop_all(self):
        self.soundPlayerThread.stop_all()

    def shutdown(self):
        # FIXME: disconnect serial
        self.soundPlayerThread.shutdown()


if __name__ == "__main__":
    CASE = 2
    if CASE==1:
        soundPlayerThread = SoundPlayer(serialtrigger=True)
        soundPlayerThread.daemon=True
        s1 = {'type':'tone', 'frequency':210, 'duration':0.2, 'amplitude':0.1}
        s2 = {'type':'tone', 'frequency':240, 'duration':0.2, 'amplitude':0.1}
        soundPlayerThread.set_sound(1,s1)
        soundPlayerThread.set_sound(2,s2)
        soundPlayerThread.create_sounds()
        #soundPlayerThread.play_sound(1)
        soundPlayerThread.start()
        time.sleep(4)
        s1 = {'type':'tone', 'frequency':410, 'duration':0.2, 'amplitude':0.1}
        s2 = {'type':'tone', 'frequency':440, 'duration':0.2, 'amplitude':0.1}
        soundPlayerThread.set_sound(1,s1)
        soundPlayerThread.set_sound(2,s2)
        soundPlayerThread.create_sounds()
        #soundPlayerThread.play_sound(1)
        time.sleep(4)
    if CASE==2:
        sc = SoundClient()
        #s1 = {'type':'tone', 'frequency':300, 'duration':0.5, 'amplitude':[0.1,0]}
        #s1 = {'type':'tone', 'frequency':300, 'duration':0.5, 'amplitude':0.1}
        #s1 = {'type':'chord', 'frequency':500, 'duration':1.5, 'amplitude':[0.1,0], 'factor':1.2, 'ntones':12}
        #s1 = {'type':'noise', 'duration':0.5, 'amplitude':0.1}
        s1 = {'type':'AM', 'duration':0.5, 'amplitude':0.1, 'modDepth':30, 'modFrequency':4}
        sc.set_sound(1,s1)
        sc.play_sound(1)
        time.sleep(1)
    if CASE==3:
        sc = SoundClient()
        s1 = {'type':'tone', 'frequency':700, 'duration':1.1, 'amplitude':[0,0.1]}
        s2 = {'type':'tone', 'frequency':400, 'duration':1.1, 'amplitude':[0.1,0]}
        #s3 = {'type':'chord', 'frequency':3000, 'duration':0.1, 'amplitude':0.1, 'ntones':12, 'factor':1.2}
        #s4 = {'type':'chord', 'frequency':7000, 'duration':0.1, 'amplitude':0.1, 'ntones':12, 'factor':1.2}
        #s5 = {'type':'chord', 'frequency':16000, 'duration':0.1, 'amplitude':0.1, 'ntones':12, 'factor':1.2}
        import time
        TicTime = time.time()
        sc.set_sound(1,s1)
        print('Elapsed Time: ' + str(time.time()-TicTime))
        TicTime = time.time()
        sc.set_sound(2,s2)
        print('Elapsed Time: ' + str(time.time()-TicTime))
        #TicTime = time.time()
        #sc.set_sound(3,s5)
        #print('Elapsed Time: ' + str(time.time()-TicTime))
        sc.start()
        #sc.define_sounds()
        sc.play_sound(2)
        print('Elapsed Time: ' + str(time.time()-TicTime))
        sc.play_sound(1)
        print('Elapsed Time: ' + str(time.time()-TicTime))
        #sc.play_sound(3)
        time.sleep(2)
    if CASE==4:
        sc = SoundClient() #(serialtrigger=False)
        s1 = {'type':'tone', 'frequency':500, 'duration':0.2, 'amplitude':np.array([1,1])}
        filename = '/home/sjara/src/taskontrol/examples/left.wav'
        s2 = {'type':'fromfile', 'filename':filename, 'amplitude':[1,0]}
        sc.set_sound(1,s1)
        sc.set_sound(2,s2)
        sc.start()
        sc.play_sound(1)
        sc.shutdown()
    if CASE==5:
        sc = SoundClient() #(serialtrigger=False)
        s1 = {'type':'AM', 'modFrequency':3, 'duration':1, 'modDepth':50,
              'amplitude':0.1*np.array([1,1])}
        #s1 = {'type':'AM', 'modFrequency':10, 'duration':1, 'amplitude':0.1*np.array([1,1])}
        #s1 = {'type':'AM', 'modFrequency':10, 'duration':1, 'amplitude':0.1}
        sc.set_sound(1,s1)
        sc.start()
        sc.play_sound(1)
        sc.shutdown()

#test.play_sound(0)
#test.change_message(1,'dos')
#test.change_sound(1,200)


