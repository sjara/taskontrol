#!/usr/bin/env python

'''
Base client for either the RT-Linux state machine or sound machine servers.
'''

__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-20'


import socket
import struct
import numpy as np


class BaseClient(object):
    '''
    Generic network client that uses a text protocol.

    It is the base class for the state machine client and the sound client.
    '''
    def __init__(self, host='localhost', port=3333, connectnow=True, verbose=False):
        self.VERBOSE = verbose
        self.host = host
        self.port = port

    def connectSocket(self):
        '''
        Connect to the RT-Linux server.

        Create a network socket to communicate with the RT-Linux sound
        server and connect.

        Based on Modules/NetClient/FSMClient.cpp and NetClient.cpp from
        the matlab client provided by: http://code.google.com/p/rt-fsm/
        '''
        self._verbose_print('Creating network socket (on port %d)'%self.port)
        self.socketClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketClient.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,True)
        # -- Set timeout to 10ms for self.receiveLines() (it failed if 1ms) --
        self.socketClient.settimeout(5) # Only times-out if not receiving
        self._verbose_print('Connecting the socket client (on port %d)'%self.port)
        self.socketClient.connect( (self.host,self.port) )


    def checkConn(self):
        '''
        Check connection to server.
        
        The argument servertype is an optional string used for display
        purposes.
        '''
        self._verbose_print('Checking connection to server (on port %d)'%self.port)
        self.doQueryCmd('NOOP')


    def initialize(self):
        '''Initialize the server (clear all variables).'''
        self.doQueryCmd('INITIALIZE')


    def doQueryCmd(self,cmd,resultsize=0,expect='OK'):
        '''
        Send command (string) to the server.

        'resultsize' indicates how many lines are expected in addition
        to the acknowledgment string.

        'expect' indicates the expected acknowledgment string (e.g. 'OK').

        It returns either:
        - Empty string if resultsize=0
        - String with result if resultsize=1
        - List of strings if resultsize>1
        '''
        self.sendString(cmd+'\n')
        if resultsize==0:
            result = ''
        elif resultsize==1:
            result = self.receiveOneLine()
        else:
            result = self.receiveLines()
        ack = self.receiveOneLine()
        self.receiveAck(cmd,ack,expect)
        return result


    def receiveAck(self,cmd,result,expectedAck='OK'):
        '''
        Check that the server sent an acknowledgement for the last command.

        The expected acknowledgement string is usually 'OK' or
        'READY'. Note that the end-of-line character is assumed to be
        already removed.
        '''
        # FIX ME: is it really necessary to have result as arg?
        ### DELETE: if result.endswith(expectedAck+'\n'):
        if result.endswith(expectedAck):
            self._verbose_print('Received %s after %s'%(expectedAck,cmd))
        else:
            # --- FIXME: define exception --
            self._verbose_print('Server returned: %s'%result)
            raise TypeError(('Server (on port %d) did not send %s '+\
                             'after %s command.')%(self.port,expectedAck,cmd))


    def doQueryMatrixCmd(self,cmd):
        self.sendString(cmd+'\n')
        # FIXME: WATCH OUT!!! THE IMPLEMENTATION OF readLines CHANGED
        matsizestr = self.readLines()
        if 'ERROR' in matsizestr:
            raise ValueError('Server returned an error after '+\
                             'command: %s',cmd)
        if(matsizestr.startswith('MATRIX ')):
            (nrows,ncols) = map(int,matsizestr.split()[1:3])
        else:
            raise ValueError('Server returned incorrect string '+\
                             'for command: %s',cmd)
        self.sendString('READY\n')
        (mat,ackstr) = self.readMatrix(nrows,ncols)
        self.receiveAck(cmd,ackstr,'OK')
        return mat


    def sendString(self,stringToSend):
        '''Send string to server.'''
        try:
            self.socketClient.send(stringToSend)
        except:
            raise Exception('Failed sending command to server '+\
                            '(on port %d).'%self.port)


    def sendData(self,mat,dtype='d',expect='OK'):
        dataToSend = self._packmatrix(mat,dtype=dtype)
        self.sendString(dataToSend)
        result = self.receiveOneLine()
        self.receiveAck('sending data',result,expect)


    def _packmatrix(self,mat,dtype='d'):
        '''
        Pack entries of a matrix into a string of their binary representation.

        The binary representation depends on the parameter dtype. It is usually:
        'd' : double precision floating point numbers (8 bytes)
        'i' : integers (4 bytes)

        This function flattens arrays in Fortran (column-major) order.
        '''
        packedMatrix = ''
        packer = struct.Struct(dtype)
        # -- Ensure that mat is a numpy array --
        if not isinstance(mat,np.ndarray):
            mat = array(mat)
        # NOTE: I thought this could be more efficient using the
        #       iterator ndarray.flat but it only works on the
        #       original order of the array (which is by default 'C')
        # IMPROVE: soundwaves are already flattened
        for item in mat.flatten('F'):
            packedvalue = packer.pack(item)
            packedMatrix = ''.join((packedMatrix,packedvalue))
        return packedMatrix


    def receiveLines(self,nlines=1):
        '''Read strings sent by server.'''
        lines=[]
        for ind in range(nlines):
            lines.append(self.receiveOneLine())
        return lines


    def receiveOneLine(self):
        '''
        Read one string sent by server terminated by '\n'.

        It returns the string without the end-of-line char.
        '''
        line = ''
        lastchar = ''
        while lastchar!='\n':
            line = ''.join((line,lastchar))
            lastchar = self.socketClient.recv(1)
        return line


    def receiveUntilTimeOut(self):
        '''Read characters sent by server until it times out.'''
        lines = ''
        lastchar = ''
        while True:
            try:
                lines = ''.join((lines,lastchar))
                lastchar = self.socketClient.recv(1)
            except socket.timeout:
                break
        return lines


    def closeSocket(self):
        '''Close connection to server.'''
        self.socketClient.close()


    def flushSocket(self):
        '''Read whatever is left on the server's buffer.'''
        return self.receiveUntilTimeOut()


    def _verbose_print(self,msg):
        '''Print client messages if verbose flag is set.'''
        if(self.VERBOSE):
            print(msg)

