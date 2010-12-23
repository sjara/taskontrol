#!/usr/bin/env python

'''
RT-Linux sound machine client.

Based on Modules/@RTLSoundMachine/RTLSoundMachine.m
         Modules/SoundTrigClient/SoundTrigClient.cpp
'''

__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-19'

import sys
import numpy as np
from taskontrol.core import baseclient


class SoundClient(baseclient.BaseClient):
    '''
    Client for the RT-Linux sound server.

    The soundcardID indicates which of the soundcards on the
    soundmachine is the intended soundcard to use.  Otherwise an 8th
    parameter to LoadSound is required to override this.  This
    parameter is for soundmachines that have more than 1 soundcard.

    A newly constructed RTLSoundMachine has the
    following default properties:

    Sample Rate:  200000
    Host: localhost
    Port: 3334
    '''
    def __init__(self, host='localhost', port=3334, soundcardID=0,
                                         samplerate = 200000,
                                         connectnow=True, verbose=False):

        super(SoundClient,self).__init__(host,port,connectnow,verbose)
        self.soundcardID = soundcardID
        self.samplerate = float(samplerate)
        if connectnow:
            self.connect()


    def connect(self):
        '''
        Connect the client and set sound machine ID.
        '''
        self.connectSocket()
        self.checkConn()
        self.setCard(self.soundcardID);


    def setCard(self,card):
        '''Set the active soundcard that we are connected to.'''
        self._verbose_print('Setting sound card to %d'%card)
        self.doQueryCmd('SET CARD %d'%card)
        self.soundcardID = card


    def getNumCards(self):
        '''Get the active soundcard that we are connected to.'''
        ncardsstr = self.doQueryCmd('GET NCARDS',resultsize=1)
        return int(ncardsstr)


    def setSampleRate(self,srate):
        '''Set sample rate for future calls to loadSound().'''
        self.samplerate = float(srate)


    def getSampleRate(self):
        '''Get sample rate to be used for future calls to loadSound().'''
        return self.samplerate


    def loadSound(self, soundID, soundwave, stopramp_ms=0, predelay=0, loop=False):
        '''
        This function sends a sound to the server.

        It associates that sound with a soundID (which is used for
        triggering the sound). The soundID must be an integer greater
        than zero.
 
        The soundVector is either a 1xNUM_SAMPLES (mono) or
        2xNUM_SAMPLES (stereo) in the range [-1,1].

        NOT IMPLEMENTED: side is either 'left', 'right' or 'both', and
        controls which speaker side the sound will play from.  Calling
        this function with a stereo soundVector and any side parameter
        other than 'both' is supported and is a good way to suppress
        the output of one side.

        tau_ms is the number of milliseconds to do a cosine2 stop-ramp
        function when triggering the sound to 'stop'.  Default is 0,
        meaning don't ramp-down the volume.  If nonzero, the volume
        will be ramped-down for a 'gradual stop' over time tau_ms on
        trigger-stop events.  NB: On natural, untriggered stops, no
        ramping is ever applied, since it is assumed that the
        soundfile itself ramps whatever it contains down to 0 volume
        naturally.

        predelay_s is the amount of time in seconds to pre-delay the
        playing of the sound when triggering.  This functionally
        prepends predelay_s seconds worth of zeroes to the sound
        matrix so as to cause sounds to play with a predefined delay
        from the time they are triggered to the time that real sounds
        actually begin emanating from the speakers.  (As strange as
        this may seem, delaying sound output from the time of the
        trigger to when the sound really plays is useful to some
        protocols).

        If loop_flg is true, the sound should loop indefinitely
        whenever it is triggered, otherwise it will play only once for
        each triggering.

        Sampling rate note: Each file that is loaded to the
        RTLSoundMachine takes the sampling rate currently set via the
        SetSampleRate() method.  In other words, it is necessary to
        call SetSampleRate() before calling LoadSound() for each file
        you load via LoadSound() if all your sound files' sampling
        rates differ!  Likewise, you need to reload sound files if you
        want new sampling rates set via SetSamplingRate() to take
        effect.
        '''
        # FIXME: Do we really need the argument 'side', for the moment
        # everything is binaural, and the user can create monoaural
        # sounds by making one channel full of zeros.
        if stopramp_ms<0:
            raise ValueError('Stop ramp tau cannot be negative.')

        if soundwave.ndim==1:
            soundwave = np.vstack((soundwave,soundwave))

        # Add predelay. As in the matlab implementation we just pad
        # with zeros. Maybe it will be done by the server one day.
        if predelay>0: 
            nsampdelay = int(round(float(predelay)*self.samplerate))
            soundwave = np.hstack((np.zeros((2,nsampdelay)),soundwave))
        
        # Convert from float (-1,1) to signed int32 (MinInt32,MaxInt32)
        # FIXME: this is potentially very slow (and called often)
        soundwave = (soundwave*sys.maxint).astype('int32')

        # Interleave entries from each channel to create a 1D vector
        # To do it we flatten column-major (Fortran way)
        soundwave = soundwave.flatten('F')

        #if self.samplerate != 200000:
            # Why are we limited to srate of 200k?
            #raise ValueError('For now, the client only works for srate=200kHz.')

        # The parameters for the SET SOUND command are a mistery,
        # the Matlab client does not explain the details.
        nBytes = 4*np.prod(soundwave.shape)
        nChans = 2              # Hardcoded (always binaural)
        stringpieces = 3*[0]
        stringpieces[0] = 'SET SOUND %d %d'%(soundID, nBytes)
        stringpieces[1] = '%d %d %d'%(nChans, 32, self.samplerate)
        stringpieces[2] = '%d %d'%(stopramp_ms, loop)
        stringtosend = ' '.join(stringpieces)

        self.doQueryCmd(stringtosend,expect='READY')
        self.sendData(soundwave, dtype='i', expect='OK')


    def playSound(self,soundID):
        '''
        Force sound server to play sound associated with soundID.

        Triggering sounds this way is not realtime. This method should
        be used only for testing.
        '''
        self.doQueryCmd('TRIGGER %d'%soundID)
 
       
    def stopSound(self,soundID):
        '''
        Force sound server to stop sound associated with soundID.
        '''
        negSoundID = -(abs(soundID))
        self.doQueryCmd('TRIGGER %d'%negSoundID)


    def getLastTrigger(self):
        '''
        Get the soundID of the last sound triggered.

        Negative numbers indicate STOP events, positive PLAY events.
        Zero indicates that no sound events have occured since last
        reset.
        '''
        lastSoundID = self.doQueryCmd('GET LAST EVENT',resultsize=1)
        return int(lastSoundID)


    def stopLastSound(self):
        '''
        Forces the soundmachine to stop the last sound (with ramping).
        '''
        lastSoundID = self.getLastTrigger()
        self.stopSound(lastSoundID)


    def getTime(self):
        '''Gets the time, in seconds, that has elapsed since initialize()'''
        etimestr = self.doQueryCmd('GET TIME',resultsize=1)
        return float(etimestr)
 

    def close(self):
        '''
        Close connection to server.
        '''
        self.stopLastSound()
        self.closeSocket()


if __name__ == "__main__":

    testSC = SoundClient('localhost',samplerate=44100,verbose=True)
    #soundwave = 0.1*np.random.standard_normal(200e3/10)
    #soundwave = 0.1*np.random.standard_normal(2*8193)
    #soundwave = 0.1*np.tile(np.repeat([1,-1],100),2)
    timeVec = np.arange(0,0.02,1/testSC.getSampleRate())
    #soundwave = 1*np.sin(2*np.pi*1e3*timeVec)
    soundwave = np.vstack((1*np.sin(2*np.pi*1000*timeVec),
                           1*np.sin(2*np.pi*400*timeVec)))
    
    # NOTE: a sound of with more than 2^13 (8192) samples
    # does not work on the emulator, it times-out even at 20sec.
    
    #testSC.loadSound(1,soundwave,predelay=0.001)
    testSC.loadSound(1,soundwave)
