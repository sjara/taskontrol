#!/usr/bin/env python

'''
Plugin for presenting sounds (by communicating with sound server).

It needs jackd to be running. In Ubuntu 12.04 you can run it with:
pasuspender -- /usr/bin/jackd -r -dalsa -dhw:STX -r192000 -p512 -n2
 or
pasuspender -- /usr/bin/jackd -r -dalsa -dhw:0 -r41000 -p512 -n2
pasuspender -- /usr/bin/jackd -R -dalsa -dhw:M2496 -r96000 -p128 -n2


You may want to test the sound first:

Without jack, you can test with:
speaker-test -r 41000 -t sine -f 8000

And test pyo:
import pyo
import time
s = pyo.Server(audio='jack').boot()
s.start()
soundObj = pyo.Sine(freq=90000,mul=0.1).mix(2).out(dur=1)
time.sleep(1)

'''

__version__ = '0.1'
__author__ = 'Santiago Jaramillo <sjara@uoregon.edu>'

#from PySide import QtCore 
#from PySide import QtGui 
from taskontrol.settings import rigsettings

import pyo
import threading
import serial
import time
import os
from taskontrol.settings import rigsettings
import numpy as np

#from Pyro.ext import remote_nons
#import Pyro.errors

#PYRO_PORT=rigsettings.SOUND_SERVER_PYRO_PORT

# NOTE: all parameters for the sound server (sampling rate, etc)
#       are defined in the script that runs jackd, not on this file.

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

SYNC_SIGNAL_FREQUENCY=500.0

if rigsettings.STATE_MACHINE_TYPE=='arduino_due':
    USEJACK = True
    SERIALTRIGGER = True
else:
    USEJACK = False
    SERIALTRIGGER = False

STOP_ALL_SOUNDS = 128
    
# -- Set computer's sound level --
if hasattr(rigsettings,'SOUND_VOLUME_LEVEL'):
    baseVol = rigsettings.SOUND_VOLUME_LEVEL
    if baseVol is not None:
        os.system('amixer set Master {0}% > /dev/null'.format(baseVol))
        # Change volume of the first two sound-cards
        #os.system('amixer -c 0 set Master {0}% > /dev/null'.format(baseVol))
        #os.system('amixer -c 1 set Master {0}% > /dev/null'.format(baseVol))
        print 'Set sound volume to {0}%'.format(baseVol)
        
class SoundPlayer(threading.Thread):
    def __init__(self,serialtrigger=True):
        threading.Thread.__init__(self)
        self.serialtrigger = serialtrigger
        self.pyoServer = None
        self.ser = None
        self._stop = threading.Event()
        self._done = threading.Event()

        self.init_pyo()
        if self.serialtrigger:
            self.init_serial()
        
        self.sounds = MAX_NSOUNDS*[None]     # List of objects like pyo.Fader()
        self.soundwaves = MAX_NSOUNDS*[None] # List of objects like pyo.Sine()
        
        self.risetime = 0.002
        self.falltime = 0.002

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
            '''Emulated mode'''
            while not self.stopped():
                try:
                    f=open('/tmp/serialoutput.txt','r')
                    oneval = f.read()
                    if len(oneval):
                        soundID = int(oneval)
                    if soundID==STOP_ALL_SOUNDS:
                        self.stop_all()
                    else:
                        self.play_sound(soundID)
                except:
                    pass
        self._done.set()

    def init_pyo(self):
        # -- Initialize sound generator (pyo) --
        print 'Creating pyo server.'
        if USEJACK:
            self.pyoServer = pyo.Server(audio='jack').boot()
        else:
            self.pyoServer = pyo.Server(audio='offline').boot()
            self.pyoServer.recordOptions(dur=0.1, filename='/tmp/tempsound.wav',
                                         fileformat=0, sampletype=0)
        '''
        self.pyoServer = pyo.Server(sr=SAMPLING_RATE, nchnls=N_CHANNELS,
                                    buffersize=BUFFER_SIZE,
                                    duplex=0, audio='jack').boot()
        '''
        self.pyoServer.start()
        print 'Pyo server ready'

    def init_serial(self):
        print 'Connecting to serial port'
        self.ser = serial.Serial(SERIAL_PORT_PATH, SERIAL_BAUD_RATE, timeout=SERIAL_TIMEOUT)
 
    def set_sound(self,soundID,soundParams):
        '''
        soundParams is a dictionary that defines a sound, for example
        {'type':'tone', 'frequency':200, 'duration':0.2, 'amplitude':0.1}
        {'type':'fromfile','filename':'/tmp/sound.wav','duration':None,'channel':0,'amplitude':0.1}
        channel can be 'left', 'right', 'both'
        '''
        self.soundsParamsDict[soundID] = soundParams
        (self.sounds[soundID],self.soundwaves[soundID]) = \
            self.create_sound(self.soundsParamsDict[soundID])
        ###soundutils.create_sound(self.soundsParamsDict[soundID])

    def create_sound(self,soundParams):
        '''
        NOTE: This methods needs to return both the soundObj and soundwaveObj to be able to
        play the sound form elsewhere. If soundwaveObj is not returned, it will not exist
        outside this scope, and the pyo server plays nothing on soundObj.play()

        Args:
            soundParams (dict): A dictionary of sound parameters.

        Returns:
            soundObj (pyo.PyoObject): pyo object with .play() method (usually pyo.Fader)
            soundWaveObjs (list): List of all pyo soundwave objects needed to produce the sound
        '''
        soundWaveObjs = []
        if isinstance(soundParams['amplitude'],list) or isinstance(soundParams['amplitude'],np.ndarray):
            soundAmp = list(soundParams['amplitude'])
        else:
            soundAmp = 2*[soundParams['amplitude']]
            
        risetime = soundParams.setdefault('fadein',self.risetime)
        falltime = soundParams.setdefault('fadeout',self.falltime)
        
        # -- Setup sound synchronization signal ---
        syncChan = rigsettings.SOUND_SYNC_CHANNEL
        if syncChan is not None:
            #Add the sync signal to the list of soundWaveObjs
            soundAmp[syncChan]=0 #Silence all other sounds in the sync channel
        # -- Define sound according to type --
        if soundParams['type']=='tone':
            soundObj = pyo.Fader(fadein=self.risetime, fadeout=self.falltime,
                                 dur=soundParams['duration'])
            soundWaveObjs.append(pyo.Sine(freq=float(soundParams['frequency']),
                                    mul=soundObj*soundAmp).out())
        elif soundParams['type']=='chord':
            nTones = soundParams['ntones']  # Number of components in chord
            factor = soundParams['factor']  # Components will be in range [f/factor, f*factor]
            centerFreq = soundParams['frequency']
            freqEachComp = np.logspace(np.log10(centerFreq/factor),np.log10(centerFreq*factor),nTones)
            soundObj = pyo.Fader(fadein=risetime, fadeout=falltime,
                                 dur=soundParams['duration'])
            for indcomp in range(nTones):
                #soundwaveObjs.append(pyo.Sine(freq=freqEachComp[indcomp],
                #                              mul=soundObj).mix(2).out())
                soundWaveObjs.append(pyo.Sine(freq=float(freqEachComp[indcomp]),
                                              mul=soundObj*soundAmp).out())
        elif soundParams['type']=='noise':
            soundObj = pyo.Fader(fadein=self.risetime, fadeout=self.falltime,
                                 dur=soundParams['duration'])
            #soundwaveObj = pyo.Noise(mul=soundObj).mix(2).out()
            soundWaveObjs.append(pyo.Noise(mul=soundAmp*soundObj).out())
        elif soundParams['type']=='AM':
            if 'modDepth' in soundParams:
                modFactor = soundParams['modDepth']/100.0
            else:
                modFactor = 1.0
            if isinstance(soundAmp, list):
                multTerm = [(modFactor*0.5)*x for x in soundAmp]
                addTerm = [(1-modFactor*0.5)*x for x in soundAmp]
            else:
                multTerm = (modFactor*0.5) * soundAmp
                addTerm = (1-modFactor*0.5) * soundAmp
            envelope = pyo.Sine(freq=soundParams['modFrequency'],
                                mul=multTerm,
                                add=addTerm, phase=0.75)
            # -- Test code --
            # y = np.sin(0.1*np.arange(200))
            #  m=.2; plot(3*m*0.5*y + 3*(1-(m*0.5))); ylim([-4,4]); grid(1)
            '''
            if isinstance(soundAmp, list):
                halfAmp = [0.5*x for x in soundAmp]
            else:
                halfAmp = 0.5*soundAmp
            envelope = pyo.Sine(freq=soundParams['modFrequency'],
                                mul=halfAmp,
                                add=halfAmp,phase=0.75)
            '''
            soundObj = pyo.Fader(fadein=self.risetime, fadeout=self.falltime,
                                 dur=soundParams['duration'])
            soundWaveObjs.append(envelope)
            soundWaveObjs.append(pyo.Noise(mul=soundObj*envelope).out())
            '''
            soundObj = pyo.Fader(fadein=self.risetime, fadeout=self.falltime,
                                 dur=soundParams['duration'], mul=soundAmp)
            envelope = pyo.Sine(freq=soundParams['modFrequency'],mul=soundObj,add=soundAmp,phase=0)
            soundwaveObj = pyo.Noise(mul=envelope).out()
            return(soundObj,[envelope,soundwaveObj])
            '''
        elif soundParams['type']=='tone_AM':
            if isinstance(soundAmp, list):
                halfAmp = [0.5*x for x in soundAmp]
            else:
                halfAmp = 0.5*soundAmp
            nTones = soundParams['ntones']  # Number of components in harmonic
            factor = soundParams['factor']  # Components will be in range [f/factor, f*factor]
            centerFreq = soundParams['frequency']
            freqEachComp = np.logspace(np.log10(centerFreq/factor),np.log10(centerFreq*factor),nTones) if nTones>1 else [centerFreq]
            envelope = pyo.Sine(freq=soundParams['modRate'],
                                mul=halfAmp,
                                add=halfAmp,phase=0.75)
            soundObj = pyo.Fader(fadein=self.risetime, fadeout=self.falltime,
                                 dur=soundParams['duration'])
            soundWaveObjs.append(envelope)
            for indcomp in range(nTones):
                soundWaveObjs.append(pyo.Sine(freq=float(freqEachComp[indcomp]),
                                              mul=soundObj*envelope).out())
        elif soundParams['type']=='band':
            frequency = soundParams['frequency']
            octaves = soundParams['octaves']
            freqhigh = frequency * np.power(2, octaves/2)
            freqlow = frequency / np.power(2, octaves/2)
            soundObj = pyo.Fader(fadein=self.risetime, fadeout=self.falltime,
                                 dur=soundParams['duration'])
            freqcent = float((freqhigh + freqlow)/2)
            bandwidth = float(freqhigh - freqlow)
            n = pyo.Noise(mul=soundObj*soundAmp)
            soundWaveObjs.append(pyo.IRWinSinc(n, freq=freqcent, bw = bandwidth, type=3, order=400).out())
        elif soundParams['type']=='band_AM':
            if isinstance(soundAmp, list):
                halfAmp = [0.5*x for x in soundAmp]
            else:
                halfAmp = 0.5*soundAmp
            frequency = soundParams['frequency']
            octaves = soundParams['octaves']
            freqhigh = frequency * np.power(2, octaves/2)
            freqlow = frequency / np.power(2, octaves/2)
            envelope = pyo.Sine(freq=soundParams['modRate'],
                                mul=halfAmp,
                                add=halfAmp,phase=0.75)
            soundObj = pyo.Fader(fadein=self.risetime, fadeout=self.falltime,
                                 dur=soundParams['duration'])
            freqcent = float((freqhigh + freqlow)/2)
            bandwidth = float(freqhigh - freqlow)
            n = pyo.Noise(mul=soundObj*envelope)
            soundWaveObjs.append(envelope)
            soundWaveObjs.append(pyo.IRWinSinc(n, freq=freqcent, bw = bandwidth, type=3, order=400).out())
        elif soundParams['type']=='FM':
            #fm1 = FM(carrier=250, ratio=[1.5,1.49], index=10, mul=0.3)
            soundObj = pyo.Fader(fadein=self.risetime, fadeout=self.falltime,
                                 dur=soundParams['duration'])
            #soundWave = pyo.FM(carrier=soundParams['frequency'], ratio=[1.5,1.49], index=10, mul=soundObj*soundAmp)
            #soundWaveObjs.append(soundWave)
            soundWaveObjs.append(pyo.FM(carrier=soundParams['frequency'], ratio=0.005, index=4, mul=soundObj*soundAmp).out())
            ###soundWaveObjs.append(pyo.Sine(freq=float(soundParams['frequency']), mul=soundObj*soundAmp).out())
        elif soundParams['type']=='fromfile':
            if not os.path.isfile(soundParams['filename']):
                raise IOError('File {} does not exist.'.format(soundParams['filename']))
            tableObj = pyo.SndTable(soundParams['filename'])
            samplingFreq = tableObj.getRate()
            if soundParams.get('duration'):
                duration = soundParams['duration']
            else:
                duration = tableObj.getDur()
            if soundParams.get('channel')=='left':
                fs = [samplingFreq,0]
            elif soundParams.get('channel')=='right':
                fs = [0,samplingFreq]
            else:
                fs = 2*[samplingFreq]
            soundObj = pyo.Fader(fadein=self.risetime, fadeout=self.falltime,
                                 dur=duration)
            ###print duration
            ###print fs
            soundWaveObjs.append(pyo.Osc(table=tableObj, freq=fs, mul=soundObj*soundAmp).out())
        else:
            raise TypeError('Sound type "{0}" has not been implemented.'.format(soundParams['type']))
            #return(None,None)
        if syncChan is not None:
            syncAmp = [0,0]
            syncAmp[syncChan]=rigsettings.SYNC_SIGNAL_AMPLITUDE #Only set the sync signal to play in the sync channel
            syncFreq = rigsettings.SYNC_SIGNAL_FREQUENCY
            soundWaveObjs.append(pyo.Sine(float(syncFreq), mul=syncAmp*soundObj, phase=0.5).out())
        return(soundObj, soundWaveObjs)

    def play_sound(self,soundID):
        # FIXME: check that this sound has been defined
        if USEJACK:
            try:
                if isinstance(self.soundwaves[soundID],list):
                    for sw in self.soundwaves[soundID]:
                        sw.reset() # Reset phase to 0
                else:
                    self.soundwaves[soundID].reset()
            except:
                #print 'Warning! Sound #{0} cannot be reset.'.format(soundID)
                pass
                #raise
            self.sounds[soundID].play()
        else:
            soundfile = '/tmp/tempsound.wav'
            duration = self.sounds[soundID].dur
            self.pyoServer.recordOptions(dur=duration, filename=soundfile,
                                         fileformat=0, sampletype=0)
            self.sounds[soundID].play()
            self.pyoServer.start()
            os.system('aplay {0}'.format(soundfile))

    def stop_all(self):
        # We loop only through the sounds that have been defined
        for soundID in self.soundsParamsDict.keys():
            self.sounds[soundID].stop()
        
    def stopped(self):
        return self._stop.isSet()

    def shutdown(self):
        '''Stop thread loop and shutdown pyo sound server'''
        self._stop.set() # Set flag to stop thread (checked on the thread loop).
        while not self._done.isSet(): # Make sure the loop stopped before shutdown.
            pass
        self.pyoServer.shutdown()



class SoundClient(object):
    '''
    Object for connecting to the sound server and defining sounds.
    '''

    #def __init__(self, serialtrigger=True):
    def __init__(self):
        self.soundPlayerThread = SoundPlayer(serialtrigger=SERIALTRIGGER)
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
    CASE = 5
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
        sc = SoundClient(serialtrigger=True)
        s1 = {'type':'tone', 'frequency':210, 'duration':0.2, 'amplitude':0.1}
        sc.set_sound(1,s1)
        sc.play_sound(1)
    if CASE==3:
        sc = SoundClient() #(serialtrigger=False)
        s1 = {'type':'tone', 'frequency':3500, 'duration':0.1, 'amplitude':0.1}
        s2 = {'type':'tone', 'frequency':400, 'duration':0.1, 'amplitude':0.1}
        s3 = {'type':'chord', 'frequency':3000, 'duration':0.1, 'amplitude':0.1, 'ntones':12, 'factor':1.2}
        s4 = {'type':'chord', 'frequency':7000, 'duration':0.1, 'amplitude':0.1, 'ntones':12, 'factor':1.2}
        s5 = {'type':'chord', 'frequency':16000, 'duration':0.1, 'amplitude':0.1, 'ntones':12, 'factor':1.2}
        import time
        TicTime = time.time()
        sc.set_sound(1,s1)
        print 'Elapsed Time: ' + str(time.time()-TicTime)
        TicTime = time.time()
        sc.set_sound(2,s4)
        print 'Elapsed Time: ' + str(time.time()-TicTime)
        TicTime = time.time()
        sc.set_sound(3,s5)
        print 'Elapsed Time: ' + str(time.time()-TicTime)
        sc.start()
        #sc.define_sounds()
        sc.play_sound(1)
        sc.play_sound(2)
        sc.play_sound(3)
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


