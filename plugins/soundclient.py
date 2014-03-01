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
from taskontrol.settings import rigsettings

#from Pyro.ext import remote_nons
#import Pyro.errors

#PYRO_PORT=rigsettings.SOUND_SERVER_PYRO_PORT

# NOTE: all parameters for the sound server (sampling rate, etc)
#       are defined in the script that runs jackd, not on this file.

SERIAL_PORT_PATH= rigsettings.SOUND_TRIGGER_PORT
SERIAL_BAUD_RATE = 115200  # Should be the same in statemachine.ino
SERIAL_TIMEOUT = None
'''
SOUND_CARD = rigsettings.SOUND_SERVER['soundCard']
SAMPLING_RATE = rigsettings.SOUND_SERVER['samplingRate']
N_CHANNELS = rigsettings.SOUND_SERVER['nChannels']
BUFFER_SIZE = rigsettings.SOUND_SERVER['bufferSize']
REALTIME = rigsettings.SOUND_SERVER['realtime']
'''

MAX_NSOUNDS = 128 # According to the serial protocol.


class SoundPlayer(threading.Thread):
    def __init__(self,serialtrigger=True):
        threading.Thread.__init__(self)
        self.serialtrigger = serialtrigger
        self.pyoServer = None
        self.ser = None
        
        self.init_pyo()
        if self.serialtrigger:
            self.init_serial()
        
        self.sounds = MAX_NSOUNDS*[None]
        self.soundwaves = MAX_NSOUNDS*[None]
 
        self.risetime = 0.002
        self.falltime = 0.002

        self.soundsParamsDict = {}

    def run(self):
        '''Execute thread'''
        if self.serialtrigger:
            while True:
                onechar = self.ser.read(1)
                soundID = ord(onechar)
                self.play_sound(soundID)
                #print soundID

    def init_pyo(self):
        # -- Initialize sound generator (pyo) --
        print 'Creating pyo server.'
        self.pyoServer = pyo.Server(sr=SAMPLING_RATE, nchnls=N_CHANNELS,
                                    buffersize=BUFFER_SIZE,
                                    duplex=0, audio='jack').boot()
        self.pyoServer.start()
        print 'Pyo server ready'

    def init_serial(self):
        print 'Connecting to serial port'
        self.ser = serial.Serial(SERIAL_PORT_PATH, SERIAL_BAUD_RATE, timeout=SERIAL_TIMEOUT)
 
    def set_sound(self,soundID,soundParams):
        '''
        soundParams is a dictionary that defines a sound, for example
        {'type':'tone', 'frequency':200, 'duration':0.2, 'amplitude':0.1}
        '''
        self.soundsParamsDict[soundID] = soundParams

    def create_sounds(self):
        # FIXME: maybe soundsParamsDict it should be an input to this method
        for soundID,soundParams in self.soundsParamsDict.iteritems():
            if soundParams['type']=='tone':
                self.sounds[soundID] = pyo.Fader(fadein=self.risetime,
                                                 fadeout=self.falltime,
                                                 dur=soundParams['duration'],
                                                 mul=soundParams['amplitude'])
                self.soundwaves[soundID] = pyo.Sine(freq=soundParams['frequency'],
                                                    mul=self.sounds[soundID]).mix(2).out()
            else:
                print 'Sound type not implemented.'

    def play_sound(self,soundID):
        # FIXME: check that this sound as been defined
        self.sounds[soundID].play()

    def shutdown(self):
        self.pyoServer.shutdown()



class SoundClient(object):
    '''
    Object for connecting to the sound server and defining sounds.
    '''

    def __init__(self, serialtrigger=True):
        self.soundPlayerThread = SoundPlayer(serialtrigger=serialtrigger)
        self.soundPlayerThread.daemon=True

    def start(self):
        self.soundPlayerThread.start()

    def set_sound(self,soundID,soundParams):
        self.soundPlayerThread.set_sound(soundID,soundParams)

    def create_sounds(self):
        # FIXME: should be removed. set_sound should create the sound.
        self.soundPlayerThread.create_sounds()

    def play_sound(self,soundID):
        # FIXME: check that this sound as been defined
        self.soundPlayerThread.play_sound(soundID)

    def stop_all(self):
        pass

    def shutdown(self):
        # FIXME: disconnect serial
        self.soundPlayerThread.shutdown()


if __name__ == "__main__":
    CASE = 1
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
       

    if CASE==3:
        sc = SoundClient(serial=False)
        s1 = {'type':'tone', 'frequency':210, 'duration':0.2, 'amplitude':0.1}
        sc.set_sound(1,s1)
        sc.start()
        sc.define_sounds()
        #sc.play_sound(1)
    if CASE==2:
        sc = SoundClient(serial=True)
        s1 = {'type':'tone', 'frequency':210, 'duration':0.2, 'amplitude':0.1}
        sc.set_sound(1,s1)
        sc.play_sound(1)


#test.play_sound(0)
#test.change_message(1,'dos')
#test.change_sound(1,200)


