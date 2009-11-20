#!/usr/bin/env python

'''
RT-Linux sound machine client.

Based on 
'''

__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-19'

import socket
import struct

class SoundClient(object):
    '''
    Create a new client that connects to the sound server.

    The soundcardID indicates which of the soundcards on the
    soundmachine is the intended soundcard to use.  Otherwise an 8th
    parameter to LoadSound is required to override this.  This
    parameter is for soundmachines that have more than 1 soundcard.

    A newly constructed RTLSoundMachine has the
    following default properties:

    Sample Rate:  200000
    Host: localhost
    Port: 3334

    Based on Modules/@RTLSoundMachine/RTLSoundMachine.m

    '''
    def __init__(self, host='localhost', port=3334, soundcardID=0, connectnow=True):
        self.soundcardID = soundcardID

        '''
  sm.handle = SoundTrigClient('create', sm.host, sm.port);
  sm = class(sm, 'RTLSoundMachine');
  % just to make sure to explode here if the connection failed
  SoundTrigClient('connect', sm.handle);
  ChkConn(sm);
  sm = SetCard(sm, sm.def_card);
        '''

        if connectnow:
            self.connect()


    def connect(self):
        '''
        Connect the client and set sound machine ID.
        '''
        self.createAndConnectSocket()
        self.chkConn()
        self.chkVersion()
        self.setStateMachine(self.fsmID);




    def setCard(self,card):
        '''Set the active soundcard that we are connected to.'''
        self._verbose_print('Setting sound card to %d'%d)
        self.doQueryCmd('SET CARD %d'%card)
        self.soundcardID = card


class BaseClient(object):
    '''
    Generic network client that uses a text protocol.

    It is the base class for the state machine client and the sound client.
    '''
    def __init__(self, host='localhost', port=3333, connectnow=True):
        self.VERBOSE = False    # Set to True for printing client messages
        self.host = host
        self.port = port

    def checkConn(self,servertype=''):
        '''
        Check connection to server.
        
        servertype is a string used for display purposes.
        '''
        self._verbose_print('Checking connection to %s server'%s)
        self.doQueryCmd('NOOP')

    def createAndConnectSocket(self):
        '''
        Connect to the sound server.

        Create a network socket to communicate with the RT-Linux sound
        server.

        Based on Modules/NetClient/FSMClient.cpp and NetClient.cpp from
        the matlab client provided by: http://code.google.com/p/rt-fsm/
        '''
        # FIXME: code is the same as in smclient.py
        #        Should these be subclasses of a general client class?
        self._verbose_print('Creating network socket')
        self.socketClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketClient.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,True)
        # -- Set timeout to 10ms for self.readLines() (it failed if 1ms) --
        self.socketClient.settimeout(0.1)
        self._verbose_print('Connecting socketClient')
        self.socketClient.connect( (self.host,self.port) )





if __name__ == "__main__":

    '''
    Modules/SoundTrigClient/SoundTrigClient.cpp

        { "create", createNewClient },
        { "destroy", destroyClient },
	{ "connect", tryConnection },
	{ "disconnect", closeSocket },
	{ "sendString", sendString },
	{ "sendMatrix", sendMatrix },
	{ "sendInt32Matrix", sendInt32Matrix },
	{ "readString", readString },
	{ "readLines",  readLines},
        { "readMatrix", readMatrix },
        { "readInt32Matrix", readInt32Matrix },
        { "interleaveMatrix", interleaveMatrix }, 
        { "interlaceMatrix", interleaveMatrix }, 
        { "flattenMatrix", interleaveMatrix },
	{ "toInt32", toInt32 }
'''
