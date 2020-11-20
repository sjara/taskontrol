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

'''
TO DO:
- pygame: fromfile mono/stereo amplitude
- jack: fromfile
x jack: stop sounds
- jack multiple sounds
- jack: set sync signal
- general: servertype as argument doesn't work because not all modules are imported.
- Check thread Events in SoundClient
'''

'''
=== BUG 1 ===
Every now and then, when using fakeserial with Jack (not sure if real serial too), I get this:

Exception in thread Thread-1:
Traceback (most recent call last):
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 395, in run
    self.play_sound(soundID)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 412, in play_sound
    self.soundServer.play_sound(soundID)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 213, in play_sound
    soundObj = self.sounds[soundID].obj
KeyError: 12

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3.8/threading.py", line 932, in _bootstrap_inner
    self.run()
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 397, in run
    print(traceback.format_exc())
NameError: name 'traceback' is not defined
Added event 6

'''

'''
=== BUG 2 ===
Sometimes, when adding a sound to the Jack sound server, I get this.

From cffi callback <function Client.set_process_callback.<locals>.callback_wrapper at 0x7ff7b07e55e0>:
Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/jack.py", line 719, in callback_wrapper
    callback(frames)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 266, in _jack_process
    self.port(streamID,'R').get_array().fill(0)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 180, in port
    return self.jackClient.get_port_by_name(baseName+channel)   
  File "/usr/lib/python3/dist-packages/jack.py", line 1404, in get_port_by_name
    raise JackError('Port {0!r} not available'.format(name))
jack.JackError: Port 'tkJackClient:1R' not available
Traceback (most recent call last):
  File "test_bandwidth_masking.py", line 353, in prepare_next_trial
    self.prepare_target_sound(currentBand, currentNoiseAmp, currentToneInt)
  File "test_bandwidth_masking.py", line 281, in prepare_target_sound
    self.soundClient.set_sound(2,s2)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 408, in set_sound
    self.soundServer.set_sound(soundID, soundParams)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 197, in set_sound
    self.create_stream(soundID)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 190, in create_stream
    self.port(streamID,'L').connect(self.targetPorts[0])
  File "/usr/lib/python3/dist-packages/jack.py", line 1903, in connect
    self._client.connect(source.name, destination.name)
  File "/usr/lib/python3/dist-packages/jack.py", line 415, in connect
    _check(err,
  File "/usr/lib/python3/dist-packages/jack.py", line 2887, in _check
    raise JackError('{0} ({1})'.format(msg, error_code))
jack.JackError: Error connecting 'tkJackClient:2L' -> 'system:playback_1' (-1)
'''

'''
Similar to BUG 2 (just starting a paradigm test_band...masking.py

MULATOR: Run.
[00:35:32] Started
From cffi callback <function Client.set_process_callback.<locals>.callback_wrapper at 0x7f64301ec5e0>:
Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/jack.py", line 719, in callback_wrapper
    callback(frames)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 341, in _jack_process
    self.port(streamID,'L').get_array().fill(0)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 241, in port
    return self.jackClient.get_port_by_name(baseName+channel)   
  File "/usr/lib/python3/dist-packages/jack.py", line 1404, in get_port_by_name
    raise JackError('Port {0!r} not available'.format(name))
jack.JackError: Port 'tkJackClient:1L' not available
Traceback (most recent call last):
  File "test_bandwidth_masking.py", line 353, in prepare_next_trial
    self.prepare_target_sound(currentBand, currentNoiseAmp, currentToneInt)
  File "test_bandwidth_masking.py", line 281, in prepare_target_sound
    self.soundClient.set_sound(2,s2)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 487, in set_sound
    self.soundServer.set_sound(soundID, soundParams)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 272, in set_sound
    self.create_stream(soundID)
  File "/home/sjara/src/taskontrol/taskontrol/plugins/soundclient.py", line 264, in create_stream
    self.port(streamID,'L').connect(self.targetPorts[0])
  File "/usr/lib/python3/dist-packages/jack.py", line 1903, in connect
    self._client.connect(source.name, destination.name)
  File "/usr/lib/python3/dist-packages/jack.py", line 415, in connect
    _check(err,
  File "/usr/lib/python3/dist-packages/jack.py", line 2887, in _check
    raise JackError('{0} ({1})'.format(msg, error_code))
jack.JackError: Error connecting 'tkJackClient:2L' -> 'system:playback_1' (-1)
EMULATOR: Set state matrix.
EMULATOR: Set state outputs.
EMULATOR: Force state 1.
Added event 6

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
#from .. import rigsettings
from taskontrol import rigsettings
if rigsettings.SOUND_SERVER=='jack':
    import jack
    import queue
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


# -- Serial port parameters --
SERIAL_PORT_PATH= rigsettings.SOUND_TRIGGER_PORT
SERIAL_BAUD_RATE = 115200  # Should be the same in statemachine.ino
SERIAL_TIMEOUT = 0.1 #None

MAX_NSOUNDS = 128 # According to the serial protocol.
STOP_ALL_SOUNDS = 128  # SoundID to stop all sounds

RISETIME = 0.1002
FALLTIME = 0.1002

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
    """
    DOCUMENT ALL OPTIONS HERE
    """
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
    #elif soundParams['type']=='fromfile':
    #    wavfile = wave.open(soundParams['filename'],'r')

    soundWave = apply_rise_fall(soundWave, samplingRate, risetime, falltime)
    soundWave = soundAmp[:,np.newaxis] * np.tile(soundWave,(nChannels,1))
    return timeVec, soundWave


class SoundContainer(object):
    def __init__(self, soundParams, soundObj, soundWave):
        self.params = soundParams  # Sound parameters dictionary
        self.obj = soundObj        # Sound object (depends on server)
        self.wave = soundWave      # Sound waveform
    def __repr__(self):
        return "{} '{}' {}".format(super().__repr__(),
                                   self.params['type'], self.wave.shape)
    
class SoundServerJack(object):
    def __init__(self, risetime=RISETIME, falltime=FALLTIME):
        self.sounds = {} # Each entry should be: index:SoundContainer()
        self.riseTime = risetime
        self.fallTime = falltime
        
        self.playingEvent = threading.Event()
        self.queueDict = {}
        self.jackClient = jack.Client('tkJackClient')
        self.blocksize = self.jackClient.blocksize
        ###self.zeroBlock = np.zeros(self.blocksize, dtype=np.float64)
        self.samplingRate = self.jackClient.samplerate
        self.jackClient.set_xrun_callback(self._jack_xrun)
        self.jackClient.set_shutdown_callback(self._jack_shutdown)
        self.jackClient.set_process_callback(self._jack_process)
        self.targetPorts = self.jackClient.get_ports(is_physical=True,
                                                     is_input=True, is_audio=True)
        self.nChannels = len(self.targetPorts)
        if self.nChannels!=2:
            raise ValueError('Server only works for systems with 2 channels.')
        self.jackClient.activate()

    def port(self, streamID, channel):
        """
        streamID (int)
        channel (str): 'L' or 'R'
        """
        baseName = '{}:{}'.format(self.jackClient.name,streamID)
        return self.jackClient.get_port_by_name(baseName+channel)   

    def _retry(self):
        pass
    
    def create_stream(self, streamID):
        """
        Register Jack ports and create queue for a new sound.
        """
        if streamID not in self.queueDict:
            self.queueDict[streamID] = queue.Queue()
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
            #raise Exception()
        
    def set_sound(self, soundID, soundParams):
        soundObj, soundwave = self.create_sound(soundParams)
        newSound = SoundContainer(soundParams, soundObj, soundwave)
        self.sounds[soundID] = newSound
        self.create_stream(soundID)

    def create_sound(self, soundParams):
        if soundParams['type']=='fromfile':
            pass
        else:
            timeVec, soundWave = create_soundwave(soundParams, self.samplingRate,
                                                  self.nChannels, self.riseTime, self.fallTime)
            padSize = soundWave.shape[1]%self.blocksize
            padArray = np.zeros((self.nChannels, padSize))
            soundObj = np.hstack((soundWave, padArray))
        return soundObj, soundWave
    
    def play_sound(self, soundID):
        self.playingEvent.set()
        soundObj = self.sounds[soundID].obj
        nBlocks = soundObj.shape[1]//self.blocksize
        for ind in range(nBlocks):
            data = soundObj[:, ind*self.blocksize:(ind+1)*self.blocksize]
            self.queueDict[soundID].put(data)
        
    def stop_sound(self, soundID):
        self._clear_queue(self.queueDict[soundID])
        self.playingEvent.clear()

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
        #jackClientEvent.set()

    def _jack_stop_callback(self,msg=''):
        print('INSIDE stop callback')
        if msg:
            self._print_error(msg)
        for port in self.jackClient.outports:
            port.get_array().fill(0)
        #jackClientEvent.set()
        raise jack.CallbackExit

    def _clear_queue(self, q):
        q.mutex.acquire()
        q.queue.clear()
        q.all_tasks_done.notify_all()
        q.unfinished_tasks = 0
        q.mutex.release()
    
    def _jack_process(self, frames):
        for streamID, oneQueue in self.queueDict.items():
            if self.playingEvent.is_set():
                try:
                    data = oneQueue.get_nowait()
                    self.port(streamID,'L').get_array()[:] = data[0]
                    self.port(streamID,'R').get_array()[:] = data[1]
                except queue.Empty:
                    self.port(streamID,'L').get_array().fill(0)
                    self.port(streamID,'R').get_array().fill(0)
            else:
                self.port(streamID,'L').get_array().fill(0)
                self.port(streamID,'R').get_array().fill(0)
        
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
        newSound = SoundContainer(soundParams, soundObj, soundwave)
        self.sounds[soundID] = newSound

    def create_sound(self, soundParams):
        if soundParams['type']=='fromfile':
            soundObj = pygame.mixer.Sound(soundParams['filename'])
            soundObj.set_volume(soundParams['amplitude'][0])
            print('WARNING! Current implementation using pygame ignores '+\
                  'specified channel for playback!')
            soundWave = None # FUTURE: I could load the samples here
        else:
            timeVec, soundWave = create_soundwave(soundParams, self.samplingRate,
                                                  self.nChannels, self.riseTime, self.fallTime)
            # NOTE: pygame requires C-contiguous arrays of size [nSamples,nChannels]
            soundWave = np.ascontiguousarray(soundWave.T)
            soundObj = pygame.sndarray.make_sound(self.to_signed_int16(soundWave))
        return soundObj, soundWave
    
    def play_sound(self, soundID):
        self.sounds[soundID].obj.play()
        
    def stop_sound(self, soundObj):
        self.sounds[soundID].obj.stop()

    def stop_all(self):
        for oneSound in self.sounds.values():
            oneSound.obj.stop()
            
    def set_sync(self, channel, amplitude, frequency):
        pass
    
    def shutdown(self):
        pygame.mixer.quit()


class SoundClient(threading.Thread):
    """
    Main interface for the generation, triggering, and presentation of sounds.
    """
    def __init__(self, servertype=rigsettings.SOUND_SERVER, serialtrigger=SERIALTRIGGER):
        """
        servertype (str): 'jack', 'pygame', 'pyo'
        """
        threading.Thread.__init__(self)
        self.serialtrigger = serialtrigger
        self.ser = None
        self._stop = threading.Event()
        self._done = threading.Event()
        self.soundServerType = servertype

        if self.soundServerType=='jack':
            self.soundServer = SoundServerJack()
        elif self.soundServerType=='pygame':
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
        self.sounds = self.soundServer.sounds  # Gives access to sounds info
        self.daemon=True

    def start(self):
        """Start the sound player thread."""
        super().start()
        
    def run(self):
        '''Execute thread'''
        if self.serialtrigger:
            while not self._stop.is_set():
                onechar = self.ser.read(1)
                if onechar:
                    soundID = ord(onechar)
                    if soundID==STOP_ALL_SOUNDS:
                        self.stop_all()
                    else:
                        self.play_sound(soundID)
        else:
            try:
                '''Fake serial mode'''
                tempDir = tempfile.gettempdir()
                fakeSerial = open(os.path.join(tempDir,'serialoutput.txt'), 'r')
                while not self._stop.is_set():
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
                            print(traceback.format_exc())
                            print('[soundclient.py] An error occurred while '+\
                                  'triggering sounds. {}'.format(exc))
                if fakeSerial:
                    fakeSerial.close()
            except:
                print(traceback.format_exc())
        self._done.set()

    def init_serial(self):
        print('Connecting to serial port')
        self.ser = serial.Serial(SERIAL_PORT_PATH, SERIAL_BAUD_RATE, timeout=SERIAL_TIMEOUT)

    def set_sound(self, soundID, soundParams):
        self.soundServer.set_sound(soundID, soundParams)

    def play_sound(self, soundID):
        self.soundServer.play_sound(soundID)
        #self.soundServer.play_sound(self.sounds[soundID] ,self.soundwaves[soundID])
        
    def stop_all(self):
        self.soundServer.stop_all()
        
    def shutdown(self):
        '''Stop thread loop and shutdown pyo sound server'''
        self._stop.set() # Set flag to stop thread (checked on the thread loop).
        #1/0
        if self.is_alive():
            while not self._done.is_set(): # Make sure the loop stopped before shutdown.
                time.sleep(0.001)
        self.stop_all()
        self.soundServer.shutdown()


class oldSoundClient(object):
    """
    Main interface for sound generation, triggering, and presentation.
    """

    #def __init__(self, serialtrigger=True):
    def __init__(self, servertype=rigsettings.SOUND_SERVER, serialtrigger=SERIALTRIGGER):
        self.soundPlayer = SoundPlayer(servertype, serialtrigger=serialtrigger)
        #self.soundPlayer = SoundPlayer(serialtrigger=SERIALTRIGGER)
        self.sounds = self.soundPlayer.sounds
        self.soundwaves = self.soundPlayer.soundwaves
        self.soundPlayer.daemon=True

    def start(self):
        self.soundPlayer.start()

    def set_sound(self,soundID,soundParams):
        self.soundPlayer.set_sound(soundID,soundParams)

    def play_sound(self,soundID):
        # FIXME: check that this sound as been defined
        self.soundPlayer.play_sound(soundID)

    def stop_all(self):
        self.soundPlayer.stop_all()

    def shutdown(self):
        # FIXME: disconnect serial
        self.soundPlayer.shutdown()


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


