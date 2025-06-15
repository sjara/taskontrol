"""
Plugin for presenting images and sounds (by communicating with a sound server).

This is an expanded version of soundclient.py that allows triggering the
presentation of static images on a separate window.

You can choose what sound server to use by changing rigsettings.py.
The available servers are:
1. jack (to use jackclient directly on Linux. This option provides the minimum latency.)
2. pygame (this is useful when using taskontrol on emulator mode)

Note that pygame is still used in both cases for presenting images.

To use jack with low latency, you need to have jackd running.
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
"""

'''
TO DO (from soundclient.py):
- Fix error when fadein/out is zero.
- pygame: fromfile mono/stereo amplitude
- jack: fromfile
- jack: set sync signal
- general: servertype as argument doesn't work because not all modules are imported.
- Check thread Events in SoundClient
'''

import os
import sys
import time
import threading
import traceback
import numpy as np
import tempfile
import wave
import serial
import scipy.io.wavfile
import scipy.signal
from taskontrol import rigsettings
if rigsettings.SOUND_SERVER=='jack':
    import jack
    import queue
elif rigsettings.SOUND_SERVER=='pygame':
    import pygame
else:
    raise("'{}' if not a valid sound server type.".format(rigsettings.SOUND_SERVER))

############ FIX THIS AT THE END (once other servers are implemented ##############
if rigsettings.STATE_MACHINE_TYPE=='arduino_due':
    SERIAL_TRIGGER = True
elif rigsettings.STATE_MACHINE_TYPE=='emulator':
    #from taskontrol.plugins import smemulator
    SERIAL_TRIGGER = False
    TEMP_DIR = tempfile.gettempdir()
    FAKE_SERIAL = 'fakeserial.txt'
else:
    raise ValueError('STATE_MACHINE_TYPE not recognized.')


# -- Serial port parameters --
SERIAL_PORT_PATH= rigsettings.SOUND_TRIGGER_PORT
SERIAL_BAUD_RATE = 115200  # Should be the same in statemachine.ino
SERIAL_TIMEOUT = 0.1 #None

MAX_SERIAL_STIM = 128 # According to the serial protocol.
# NOTE: The first 64 are used for sounds, the next 64 used for images.
#       The idea was to use negative numbers for stopping each stim,
#       but this is not implemented.
MAX_NSOUNDS = 64
MAX_NIMAGES = 64
STOP_ALL_SOUNDS = 128  # SoundID to stop all sounds


RISETIME = 0.002
FALLTIME = 0.002

randomGen = np.random.default_rng()

def set_system_volume(volumeLevel=None):
    """
    Set computer's sound level (for Linux only).
    """
    if volumeLevel is not None:
        os.system('amixer set Master {0}% > /dev/null'.format(volumeLevel))
        # Change volume of the first two sound-cards
        #os.system('amixer -c 0 set Master {0}% > /dev/null'.format(volumeLevel))
        #os.system('amixer -c 1 set Master {0}% > /dev/null'.format(volumeLevel))
        print('Set sound volume to {0}%'.format(volumeLevel))


def apply_rise_fall(waveform, samplingRate, riseTime, fallTime):
    nSamplesRise = round(samplingRate * riseTime)
    nSamplesFall = round(samplingRate * fallTime)
    riseVec = np.linspace(0, 1, nSamplesRise)
    fallVec = np.linspace(1, 0, nSamplesFall)
    newWaveform = waveform.copy()
    newWaveform[:nSamplesRise] *= riseVec
    newWaveform[-nSamplesFall:] *= fallVec
    return newWaveform


def create_soundwave(soundParams, samplingRate=44100, nChannels=2):
    """
    Create a sound waveform give parameters.

    Args:
        soundParams (dict): a dictionary defining sound parameters. See details below.
        samplingRate (float): sampling rate for the waveform.
        nChannels (int): number of channels. Usually 2, for stereo sound.
    Returns:
        timeVec (np.ndarray): array with timestamps
        soundWave (np.ndarray): array with waveform amplitude at each time point.

    The string in soundParams['type'] defines the type of sound to be created. Some
    parameters are common to all sound types, while some parameters depend on the type.
    Some parameters have defaults, and therefore do not need to be specified.

    Parameters common to all sound types:
        'fadein': time period for amplitude fade in (at the beginning of the sound)
        'fadeout': time period for amplitude fade out (at the end of the sound)
        'duration': duration of sound. Ignored when loading sound from file.
        'amplitude': it can be a single number, or a list/array with as many elements
            as channels.
    
    Parameters specific to each sound type:
        'tone' (pure sinusoidal)
            'frequency'
        'chord' (multiple simultaneous sinusoidals): 
            'frequency' (center frequency)
            'factor' (maxFreq/centerFreq)
            'ntones' (number of tones included in the chord)
        'noise' (white noise):
            (no additional parameters)
        'AM' (amplitude modulated white noise):
            'modDepth': modulation depth as a percentage (0-100).
            'modFrequency': amplitude modulation rate.
        'toneCloud':
            'nFreq'
            'freqRange'
            'toneDuration'
            'toneOnsetAsync'
        'toneTrain' (train of pure tones of a given freq)
            'frequency' (frequency of the pure tone)
            'rate' (how many tones per second in the train)
            'toneDuration' duration of each individual tone.
            Note that 'duration' refers to the duration of the whole train.
    """
    risetime = soundParams.setdefault('fadein', RISETIME)   # Set if not specified
    falltime = soundParams.setdefault('fadeout', FALLTIME)  # Set if not specified
    if soundParams['type']!='fromfile':
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
    elif soundParams['type']=='FM':
        f0 = soundParams['frequencyStart']
        f1 = soundParams['frequencyEnd']
        duration = soundParams['duration']
        fInstant = f0*timeVec +  ((f1-f0) / (2.0*duration)) * timeVec**2
        soundWave = np.sin(2.0 * np.pi * fInstant)
    elif soundParams['type']=='toneCloud':
        nFreq = soundParams['nFreq']
        freqEachTone = np.logspace(np.log10(soundParams['freqRange'][0]),
                                   np.log10(soundParams['freqRange'][1]),
                                   soundParams['nFreq'])
        toneTimeVec = np.arange(0, soundParams['toneDuration'], 1/samplingRate)
        allFreqTime = np.outer(freqEachTone, toneTimeVec)
        waveEachTone = np.sin(2*np.pi*allFreqTime)
        if 'calibration' in soundParams:
            waveEachTone *= soundParams['calibration'][:,np.newaxis]
        nSamplesPerTone = waveEachTone.shape[1]
        # -- Make end of waveform smooth --
        toneFallTime = 0.001 # Use a ramp-down of 1ms
        toneFallVec = np.linspace(1, 0, round(samplingRate * toneFallTime))
        if len(toneFallVec)>0:
            waveEachTone[:, -len(toneFallVec):] *= toneFallVec

        toneOnsets = np.arange(0, soundParams['duration'], soundParams['toneOnsetAsync'])
        toneOnsetsInds = (toneOnsets*samplingRate).astype(int)
        # Don't count last overhanging tones
        nTones = np.sum((toneOnsetsInds+nSamplesPerTone) < len(timeVec))
        nFreqInTargetRange = nFreq//3
        pTarget = (1 + 2*abs(soundParams['strength'])/100) / 3
        nTonesFromTarget = int(np.round(pTarget*nTones))
        if soundParams['strength']>0:
            targetFreqInds = np.arange(nFreq-nFreqInTargetRange, nFreq)
        else:
            targetFreqInds = np.arange(0, nFreqInTargetRange)
        pNonTargetTone = (1-pTarget)/(nFreq-len(targetFreqInds))   
        pEachFreq = np.tile(pNonTargetTone, nFreq)
        pEachFreq[targetFreqInds] = pTarget/len(targetFreqInds)
        nTonesEachFreq = np.random.multinomial(nTones, pEachFreq)
        toneSequenceSorted = np.repeat(np.arange(nFreq), nTonesEachFreq)
        toneSequence = np.random.permutation(toneSequenceSorted)
        sampleRange = nSamplesPerTone
        soundWave = np.zeros(len(timeVec))
        for toneInd in range(nTones):
            onsetSample = toneOnsetsInds[toneInd]
            waveThisTone = waveEachTone[toneSequence[toneInd], :]
            soundWave[onsetSample:onsetSample+nSamplesPerTone] += waveThisTone
    elif soundParams['type']=='toneTrain':
        toneTimeVec = np.arange(0, soundParams['toneDuration'], 1/samplingRate)
        waveEachTone = np.sin(2*np.pi*soundParams['frequency']*toneTimeVec)
        # -- Make ends of waveform smooth --
        toneRiseFallTime = 0.001 # Use a ramp of 1ms
        toneRiseVec = np.linspace(0, 1, round(samplingRate * toneRiseFallTime))
        toneFallVec = np.linspace(1, 0, round(samplingRate * toneRiseFallTime))
        if len(toneRiseVec)>0:
            waveEachTone[0:len(toneRiseVec)] *= toneRiseVec
            waveEachTone[-len(toneFallVec):] *= toneFallVec
        toneOnsetAsync = 1/soundParams['rate']
        toneOnsets = np.arange(0, soundParams['duration'], toneOnsetAsync)
        toneOnsetsInds = (toneOnsets*samplingRate).astype(int)
        soundWave = np.zeros(len(timeVec))
        for onsetSample in toneOnsetsInds:
            offsetSample = min(onsetSample+len(toneTimeVec), len(timeVec))
            soundWave[onsetSample:offsetSample] += waveEachTone
    elif soundParams['type']=='fromfile':
        '''
        # -- The version with wave+struct does not work yet --
        import struct
        wavfile = wave.open(soundParams['filename'],'r')
        fileFs = wavfile.getframerate()         # sampling rate
        fileNsamples = wavfile.getnframes()     # number of channels
        fileNchannels = wavfile.getnchannels()  # number of samples
        fileNbits = 8*wavfile.getsampwidth()    # getsampwidth() returns number of bytes
        timeVec = np.arange(0, fileNsamples/fileFs, 1/fileFs)
        byteStr = wavfile.readframes(fileNsamples)
        # Assumes 16bit
        soundWave = np.array(struct.unpack('<'+fileNsamples*'H', byteStr)).astype(np.float)
        soundWave = soundWave/(2**(fileNbits-1))-1  # Convert uint to [-1,1)
        '''
        fileFs, soundWave = scipy.io.wavfile.read(soundParams['filename'])
        nSamples = len(soundWave)
        maxIntValue = abs(np.iinfo(soundWave.dtype).min) # For example, int16 range is -32768 to 32767
        soundWave = soundWave.astype(np.float)/maxIntValue
        newNsamples = round(samplingRate*nSamples/fileFs)
        #soundWave = scipy.signal.resample(soundWave, newNsamples) # This way is too slow
        soundWave = scipy.signal.resample_poly(soundWave, samplingRate, fileFs) # Faster resample
        timeVec = np.arange(0, newNsamples/samplingRate, 1/samplingRate)
    else:
        raise ValueError("Sound type '{}' not recognized.".format(soundParams['type']))
    
    soundWave = apply_rise_fall(soundWave, samplingRate, risetime, falltime)
    soundWave = soundAmp[:,np.newaxis] * np.tile(soundWave,(nChannels,1))
    return timeVec, soundWave


class SoundContainer(object):
    def __init__(self, soundParams, soundObj, soundWave, samplingRate):
        self.params = soundParams  # Sound parameters dictionary
        self.obj = soundObj        # Sound object (depends on server)
        self.wave = soundWave      # Sound waveform
        self.fs = samplingRate     # Sound sampling rate
    def __repr__(self):
        return "{} '{}' {}".format(super().__repr__(),
                                   self.params['type'], self.wave.shape)
    def get_wave(self):
        timeVec = np.arange(0, self.wave.shape[1]/self.fs, 1/self.fs)
        return (timeVec, self.wave)
    def get_duration(self):
        return self.wave.shape[1]/self.fs
    
class SoundServerJack(object):
    def __init__(self, risetime=RISETIME, falltime=FALLTIME):
        self.sounds = {} # Each entry should be: index:SoundContainer()
        self.riseTime = risetime
        self.fallTime = falltime
        
        self.playingEvent = {}  # Stores a threading.Event() for each stream
        self.loopFlag = {}
        self.queueDict = {}     # Stores a queue for each stream
        self.preloadingThreads = {}  # Stores threads for preloading each stream
        self.jackClient = jack.Client('tkJackClient')
        self.blocksize = self.jackClient.blocksize
        self.samplingRate = self.jackClient.samplerate
        self.jackClient.set_xrun_callback(self._jack_xrun)
        self.jackClient.set_shutdown_callback(self._jack_shutdown)
        self.jackClient.set_process_callback(self._jack_process)
        self.targetPorts = self.jackClient.get_ports(is_physical=True,
                                                     is_input=True, is_audio=True)
        #self.nChannels = len(self.targetPorts)
        #if self.nChannels!=2:
        #    raise ValueError('Server only works for systems with 2 channels.')
        self.nChannels = 2 # FIXME: hardcoded for the moment
        if len(self.targetPorts)>2:
            print('WARNING! the sound card has more than two channels.')
        self.jackClient.activate()

    class PreloadQueue(threading.Thread):
        def __init__(self, soundObj, soundQueue, blocksize):
            super().__init__()
            self.soundObj = soundObj
            self.soundQueue = soundQueue
            self.bsize = blocksize
            self.daemon = True  # The program exits when only daemon threads are left.
        def run(self):
            nBlocks = self.soundObj.shape[1]//self.bsize
            for ind in range(nBlocks):
                data = self.soundObj[:, ind*self.bsize:(ind+1)*self.bsize]
                self.soundQueue.put(data)
    
    def port(self, streamID, channel):
        """
        streamID (int)
        channel (str): 'L' or 'R'
        """
        baseName = '{}:{}'.format(self.jackClient.name,streamID)
        return self.jackClient.get_port_by_name(baseName+channel)   

    def create_stream(self, streamID):
        """
        Register Jack ports and create queue for a new sound.
        """
        # Create a new queue or replace the queue if it already exists.
        self.queueDict[streamID] = queue.Queue()
        if streamID not in self.playingEvent:
            self.playingEvent[streamID] = threading.Event()
            self.loopFlag[streamID] = False
            self.jackClient.outports.register(str(streamID)+'L')
            self.jackClient.outports.register(str(streamID)+'R')
            portsReady = False
            while not portsReady:
                try:
                    self.port(streamID,'L')
                    self.port(streamID,'R')
                    portsReady = True
                except jack.JackError:
                    print(traceback.format_exc())
                    print('Trying again to connect Jack ports.')
                    time.sleep(0.001)
            self.port(streamID,'L').connect(self.targetPorts[0])
            self.port(streamID,'R').connect(self.targetPorts[1])

    '''    
    def _jack_process(self, frames):
        for streamID, oneQueue in self.queueDict.items():
            if self.playingEvent[streamID].is_set():
                try:
                    data = oneQueue.get_nowait()
                    self.port(streamID,'L').get_array()[:] = data[0]
                    self.port(streamID,'R').get_array()[:] = data[1]
                except queue.Empty:
                    self.port(streamID,'L').get_array().fill(0)
                    self.port(streamID,'R').get_array().fill(0)
                    self.playingEvent[streamID].clear() # Finished playing stream
                    self.preload_queue_no_thread(streamID)
    '''    
    def _jack_process(self, frames):
        for streamID, oneQueue in self.queueDict.items():
            if self.playingEvent[streamID].is_set():
                try:
                    data = oneQueue.get_nowait()
                    self.port(streamID,'L').get_array()[:] = data[0]
                    self.port(streamID,'R').get_array()[:] = data[1]
                except queue.Empty:
                    if self.loopFlag[streamID]:
                        self.preload_queue(streamID)  # FIXME: which preload to use?
                    else:
                        self.port(streamID,'L').get_array().fill(0)
                        self.port(streamID,'R').get_array().fill(0)
                        self.playingEvent[streamID].clear() # Finished playing stream
                        #self.preload_queue_no_thread(streamID) # FIXME: which preload to use?
                        self.preload_queue(streamID)  # FIXME: which preload to use?
        
    def set_sound(self, soundID, soundParams):
        soundObj, soundwave = self.create_sound(soundParams)
        newSound = SoundContainer(soundParams, soundObj, soundwave, self.samplingRate)
        self.sounds[soundID] = newSound
        self.create_stream(soundID)
        #self.preload_queue_no_thread(soundID) # FIXME: which preload to use?
        self.preload_queue(soundID)  # FIXME: which preload to use?
        return newSound

    def preload_queue(self, soundID):
        """Preload a sound via a thread. It will not block processing."""
        self.preloadingThreads[soundID] = self.PreloadQueue(self.sounds[soundID].obj,
                                                            self.queueDict[soundID],
                                                            self.blocksize)
        self.preloadingThreads[soundID].start()
        
    def preload_queue_no_thread(self, soundID):
        """Preload a sound without invoking a thread. It will block processing until done."""
        soundObj = self.sounds[soundID].obj
        nBlocks = soundObj.shape[1]//self.blocksize
        for ind in range(nBlocks):
            data = soundObj[:, ind*self.blocksize:(ind+1)*self.blocksize]
            self.queueDict[soundID].put(data)
        
    def create_sound(self, soundParams):
        if 0: #soundParams['type']=='fromfile':
            pass
        else:
            timeVec, soundWave = create_soundwave(soundParams, self.samplingRate, self.nChannels)
            padSize = soundWave.shape[1]%self.blocksize
            padArray = np.zeros((self.nChannels, padSize))
            soundObj = np.hstack((soundWave, padArray))
        return soundObj, soundWave
    
    def play_sound(self, soundID):
        # TicTime = time.time()
        self.playingEvent[soundID].set()
        # print('Elapsed Time (triggering): ' + str(time.time()-TicTime))
        
    def loop_sound(self, soundID):
        self.loopFlag[soundID] = True
        self.playingEvent[soundID].set()
        
    def stop_sound(self, soundID):
        self.loopFlag[soundID] = False
        if self.playingEvent[soundID].is_set():
            self.queueDict[soundID] = queue.Queue()  # Get a clean queue

    def stop_all(self):
        for soundID in self.sounds:
            self.stop_sound(soundID)
    
    def _print_error(self, *args):
        print(*args, file=sys.stderr)
 
    def _jack_xrun(self, delay):
        #self._print_error("JACK xrun occured.")
        pass
        
    def _jack_shutdown(self, status, reason):
        self._print_error('JACK shutdown!')
        self._print_error('status:', status)
        self._print_error('reason:', reason)

    def _jack_stop_callback(self,msg=''):
        print('INSIDE stop callback')
        if msg:
            self._print_error(msg)
        for port in self.jackClient.outports:
            port.get_array().fill(0)
        raise jack.CallbackExit

    def _clear_queue(self, q):
        q.mutex.acquire()
        q.queue.clear()
        q.all_tasks_done.notify_all()
        q.unfinished_tasks = 0
        q.mutex.release()
    
    def shutdown(self):
        self.jackClient.deactivate()
        self.jackClient.close()


class SoundServerPygame(object):
    def __init__(self, risetime=RISETIME, falltime=FALLTIME):
        self.sounds = {} # Each entry should be: index:SoundContainer()
        self.riseTime = risetime
        self.fallTime = falltime
        
        self.samplingRate = 44100
        self.nChannels = 2  # As of 2020-11-14, it only works for 2 channels
        self.bufferSize = 512
        pygame.mixer.init(self.samplingRate, size=-16,
                          channels=self.nChannels, buffer=self.bufferSize)
        
    def to_signed_int16(self, waveform):
        return (waveform*32767).astype(np.int16)
    
    def set_sound(self, soundID, soundParams):
        soundObj, soundwave = self.create_sound(soundParams)
        newSound = SoundContainer(soundParams, soundObj, soundwave, self.samplingRate)
        self.sounds[soundID] = newSound
        return newSound

    def create_sound(self, soundParams):
        if soundParams['type']=='pygameFile':
            soundObj = pygame.mixer.Sound(soundParams['filename'])
            soundObj.set_volume(soundParams['amplitude'][0])
            print('WARNING! Current implementation using pygame ignores '+\
                  'specified channel for playback!')
            soundWave = None # FUTURE: I could load the samples here
        else:
            timeVec, soundWave = create_soundwave(soundParams, self.samplingRate, self.nChannels)
            # NOTE: pygame requires C-contiguous arrays of size [nSamples,nChannels]
            #       but this function will return an array of [nChannels,nSamples]
            soundWave = np.ascontiguousarray(soundWave.T)
            soundObj = pygame.sndarray.make_sound(self.to_signed_int16(soundWave))
        return soundObj, soundWave.T
    
    def play_sound(self, soundID):
        self.sounds[soundID].obj.play()
        
    def loop_sound(self, soundID):
        self.sounds[soundID].obj.play(loops=-1)
        
    def stop_sound(self, soundID):
        self.sounds[soundID].obj.stop()

    def stop_all(self):
        for oneSound in self.sounds.values():
            oneSound.obj.stop()
            
    def set_sync(self, channel, amplitude, frequency):
        pass
    
    def shutdown(self):
        pygame.mixer.quit()

class ImageServer(object):
    def __init__(self):
        self.images = {}  # Each entry should be: index:ImageContainer()

    def set_image(self, imageID, imagePixels):
        """
        Set an image in the server.
        imageID (int): unique identifier for the image.
        imagePixels (np.ndarray): 2D array with pixel values of the image.
        """
        self.images[imageID] = imagePixels  # Store image pixels

    def get_image(self, imageID):
        return self.images[imageID]

    def show_image(self, imageID):
        print('******* Showing image with ID {} *********'.format(imageID))
        img = self.get_image(imageID)
        print(img)

    def shutdown(self):
        pass
        
class SoundClient(threading.Thread):
    """
    Main interface for the generation, triggering, and presentation of sounds.
    """
    def __init__(self, servertype=rigsettings.SOUND_SERVER, serialtrigger=SERIAL_TRIGGER):
        """
        servertype (str): 'jack', 'pygame', 'pyo'
        """
        super().__init__()

        set_system_volume(rigsettings.SOUND_VOLUME_LEVEL)
        self.serialtrigger = serialtrigger
        self.ser = None
        self._stop = threading.Event()
        self.soundServerType = servertype

        if self.soundServerType=='jack':
            self.soundServer = SoundServerJack()
        elif self.soundServerType=='pygame':
            self.soundServer = SoundServerPygame()
        else:
            raise ValueError('Sound server type not recognized.')

        self.ImageServer = ImageServer()
        
        # -- Set sync channel --
        if rigsettings.SOUND_SYNC_CHANNEL is not None:
            self.soundServer.set_sync(rigsettings.SOUND_SYNC_CHANNEL,
                                      rigsettings.SOUND_SYNC_AMPLITUDE,
                                      rigsettings.SOUND_SYNC_FREQUENCY)
        if self.serialtrigger:
            self.init_serial()
        else:
            fakeSerialFullPath = os.path.join(TEMP_DIR, FAKE_SERIAL)
            #if not os.path.isfile(fakeSerialFullPath):
            open(fakeSerialFullPath, 'w').close() # Create empty file
            
        self.sounds = self.soundServer.sounds  # Gives access to sounds info
        self.daemon = True  # The program exits when only daemon threads are left.
        
    def start(self):
        """Start the sound player thread."""
        super().start()
        
    def run(self):
        '''Execute thread'''
        try:
            #1/0
            if self.serialtrigger:
                while not self._stop.is_set():
                    onechar = self.ser.read(1)
                    if onechar:
                        soundID = ord(onechar)
                        if soundID==STOP_ALL_SOUNDS:
                            self.stop_all()
                        elif soundID<MAX_NSOUNDS:
                            self.play_sound(soundID)
                        elif soundID>=MAX_NSOUNDS and soundID<(MAX_NSOUNDS+MAX_NIMAGES):
                            self.show_image(soundID)
                        else:
                            raise ValueError('Sound ID {} not recognized.'.format(soundID))
            else:
                '''Fake serial mode'''
                fakeSerial = open(os.path.join(TEMP_DIR, FAKE_SERIAL), 'r')
                while not self._stop.is_set():
                    oneval = fakeSerial.read(1)
                    time.sleep(0.01)
                    if len(oneval):
                        soundID = ord(oneval)
                        if soundID==STOP_ALL_SOUNDS:
                            self.stop_all()
                        elif soundID<MAX_NSOUNDS:
                            self.play_sound(soundID)
                        elif soundID>=MAX_NSOUNDS and soundID<(MAX_NSOUNDS+MAX_NIMAGES):
                            self.show_image(soundID)
                        else:
                            raise ValueError('Sound ID {} not recognized.'.format(soundID))
                        # if fakeSerial:
                        #     fakeSerial.close()
        except Exception as exc:
            #print(traceback.format_exc())
            #print('[soundclient.py] An error occurred in the sound client thread. {}'.format(exc))
            raise

    def init_serial(self):
        connected = False
        while not connected:
            print('Connecting to serial port for sound trigger...')
            try:
                self.ser = serial.Serial(SERIAL_PORT_PATH, SERIAL_BAUD_RATE,
                                         timeout=SERIAL_TIMEOUT)
                connected = True
            except serial.serialutil.SerialException:
                time.sleep(0.1)
                #print('**************** GOOD *****************')
                #raise

    def get_wave(self, soundID):
        [timeVec, waveform] = self.sounds[soundID].get_wave()
        return (timeVec, waveform)
    
    def set_sound(self, soundID, soundParams):
        newSound = self.soundServer.set_sound(soundID, soundParams)
        return newSound
    
    def play_sound(self, soundID):
        self.soundServer.play_sound(soundID)
        
    def loop_sound(self, soundID):
        self.soundServer.loop_sound(soundID)
        
    def stop_sound(self, soundID):
        self.soundServer.stop_sound(soundID)
        
    def stop_all(self):
        self.soundServer.stop_all()

    def set_image(self, imageID, imagePixels):
        self.ImageServer.set_image(imageID, imagePixels)
        
    def show_image(self, imageID):
        self.ImageServer.show_image(imageID)
        
    def shutdown(self):
        '''Stop thread loop and shutdown pyo sound server'''
        self._stop.set() # Set flag to stop thread (checked on the thread loop).
        if self.is_alive():
            time.sleep(0.001)
        self.stop_all()
        self.soundServer.shutdown()

"""
if __name__ == "__main__":
    CASE = 2
    if CASE==1:
        soundPlayer = SoundPlayer(serialtrigger=True)
        soundPlayer.daemon=True
        s1 = {'type':'tone', 'frequency':210, 'duration':0.2, 'amplitude':0.1}
        s2 = {'type':'tone', 'frequency':240, 'duration':0.2, 'amplitude':0.1}
        soundPlayer.set_sound(1,s1)
        soundPlayer.set_sound(2,s2)
        soundPlayer.create_sounds()
        #soundPlayer.play_sound(1)
        soundPlayer.start()
        time.sleep(4)
        s1 = {'type':'tone', 'frequency':410, 'duration':0.2, 'amplitude':0.1}
        s2 = {'type':'tone', 'frequency':440, 'duration':0.2, 'amplitude':0.1}
        soundPlayer.set_sound(1,s1)
        soundPlayer.set_sound(2,s2)
        soundPlayer.create_sounds()
        #soundPlayer.play_sound(1)
        time.sleep(4)
    if CASE==2:
        sc = SoundClient()
        s1 = {'type':'tone', 'frequency':300, 'duration':0.5, 'amplitude':[0.1,0.2]}
        #s1 = {'type':'tone', 'frequency':300, 'duration':0.5, 'amplitude':0.1}
        #s1 = {'type':'chord', 'frequency':500, 'duration':1.5, 'amplitude':[0.1,0], 'factor':1.2, 'ntones':12}
        #s1 = {'type':'noise', 'duration':0.5, 'amplitude':0.1}
        #s1 = {'type':'AM', 'duration':0.5, 'amplitude':0.1, 'modDepth':30, 'modFrequency':4}
        sc.set_sound(1,s1)
        sc.play_sound(1)
        time.sleep(1)
    if CASE==22:
        sc = SoundServerJack()
        s1 = {'type':'tone', 'frequency':300, 'duration':0.5, 'amplitude':0.1}
        soundObj, soundWave = sc.create_sound(s1)
        sc.play_sound(soundObj,soundWave)
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

"""
