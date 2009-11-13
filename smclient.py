#!/usr/bin/env python

'''
RT-Linux state machine client.

This is a client for the RTAI version of the FSM, c. 2009.
Based largely on Modules/@RTLSM2 from the matlab client provided by
http://code.google.com/p/rt-fsm/

Most comments describing the methods are pasted from the Matlab code,
so they may include non-python syntax.
'''

__version__ = '0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-01'


import socket
import struct
import math

VERBOSE = True
MIN_SERVER_VERSION = 220080319  # Update this on protocol change


def verbose_print(msg):
    if(VERBOSE):
        print(msg)


def matsize(array2d):
    '''Get size of array. Not robust, it assumes all rows have same size.'''
    ncols = len(array2d)
    if ncols==0:
        nrows=0
    else:
        nrows = len(array2d[0])
    return (ncols,nrows)


def url_encode(instring):
    '''Encode string using percent-encoding.'''
    # FIXME: Check validity of input 'UrlEncode only works on strings!'
    outstring = ''
    for onechar in instring:
        if onechar.isalnum():
            outstring = ''.join((outstring,onechar))
        else:
            outstring = ''.join((outstring,'%%%02x'%ord(onechar)))
    return outstring


def packmatrix(mat):
    '''Pack entries of a matrix into a string of their binary representation
       as double precision floating point numbers
       This function flattens a matrix by concatenating its columns.
    '''
    packedMatrix = ''
    packer = struct.Struct('d')
    (nrows,ncols) = matsize(mat)
    for indcol in range(ncols):
        for indrow in range(nrows):
            packedvalue = packer.pack(mat[indrow][indcol])
            packedMatrix = ''.join((packedMatrix,packedvalue))
    return packedMatrix


def _OLDpackmatrix(mat):
    '''Flatten by rows'''
    # FIXME: OLDCODE
    packedMatrix = ''
    packer = struct.Struct('d')
    for onerow in mat:
        for oneentry in onerow:
            packedvalue = packer.pack(oneentry)
            packedMatrix = ''.join((packedMatrix,packedvalue))


class StateMachineClient(object):
    '''
    Create a new client that connects to the state machine server
    running on host, port.  Since a state machine server can handle
    more than one virtual state machine, fsm_id specifies which of the
    6 state machines on the server to use.  See method
    GetStateMachine() for more details.

    The new state machine will have the following default properties:
    Output Routing:
        'type': 'dout', 'data': '0-15'
        'type', 'sound', 'data', str(which_state_machine)
    Input Events: 6

    The sm will not have any SchedWave matrix, or any state matrix.
    '''
    def __init__(self, host='localhost', port=3333, fsm_id=0, connectnow=True):
        self.host = host
        self.port = port
        self.fsm_id = fsm_id
        self.in_chan_type = 'ai'             # Use analog input for input
        self.sched_waves = [] #zeros(0,8)    # Default to no scheduled waves
        self.sched_waves_ao = [] #cell(0,4)  # Default to no ao sched waves
        self.input_event_mapping = []        # Written-to by setInputEvents
        self.ready_for_trial_jumpstate = 1   # Traditionally state 35 

        # 'ext' is used in this case for sound
        self.output_routing = [ {'dtype':'dout', 'data':'0-15'},\
                                {'dtype':'ext',  'data':str(self.fsm_id)} ]

        if connectnow:
            self.connect()
            self.chkConn()
            self.chkVersion()
            self.setStateMachine(self.fsm_id);
        self.setInputEvents(6, 'ai') # 6 input events, two for each nosecone


    def connect(self):
        '''
        Connect to the state machine server.

        Create a network socket to communicate with the RT-Linux state
        machine server.

        Based on Modules/NetClient/FSMClient.cpp and NetClient.cpp from
        the matlab client provided by: http://code.google.com/p/rt-fsm/
        '''
        verbose_print('Creating network socket')
        self.socketClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketClient.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,True)
        # -- Set timeout to 10ms for self.readLines() (it failed if 1ms) --
        self.socketClient.settimeout(0.1)
        verbose_print('Connecting socketClient')
        self.socketClient.connect( (self.host,self.port) )
        

    def _disconnect(self):
        '''NOTE: this is implemented by Close()'''
        # FIXME: OLDCODE
        self.close()


    def sendString(self,stringToSend):
        '''Send string to the state matrix server.'''
        try:
            self.socketClient.send(stringToSend)
        except:
            raise Exception('Failed sending command to FSM server.')


    def sendMatrix(self,mat):
        '''
        Send matrix (column-wise) to state matrix server.

        The matlab/C++ version in FSMClient.cpp requires sendData
        (see FSMClient.h), which is inherited from Socket.cpp
        I'm not gonna assume TCP (ignore UDP).
        '''
        ## See: ~/tmp/newbcontrol/Modules/NetClient/Socket.cpp
        ##       unsigned Socket::sendData
        dataToSend = packmatrix(mat)
        self.socketClient.send(dataToSend)


    def readLines(self):
        '''Read strings sent by state matrix server.'''
        # FIXME: Weird implementation. Maybe combine with readMatrix()
        lines = ''
        lastchar = ''
        while True:
            try:
                lines = ''.join((lines,lastchar))
                lastchar = self.socketClient.recv(1)
            except socket.timeout:
                break
        return lines


    def readMatrix(self,nrows,ncols):
        '''Read matrixof data sent by state matrix server.'''
        # FIXME: Weird implementation. Maybe combine with readLines()
        bytesInDoublePrecFloat = 8
        sizeInBytes = bytesInDoublePrecFloat*nrows*ncols
        matdatastr = self.socketClient.recv(sizeInBytes)
        matdata=struct.unpack(nrows*ncols*'d',matdatastr) # data comes column-wise
        ackstr = self.readLines()         # Receive the rest (ack string)
        mat = []
        for indrow in range(nrows):
            mat.append(matdata[indrow::2])
        return (mat,ackstr)

        
    def notifyEvents(self):
        '''Not implemented.'''
        #FIX ME: implement this method
        pass


    def stopNotifyEvents(self):
        '''Not implemented.'''
        #FIX ME: implement this method
        pass


    def chkConn(self):
        '''Check connection to FSM server
           This should probably be implented by catching exceptions.
           And it should not repeat code from DoSimpleCmd+ReceiveOK
        '''
        verbose_print('Checking connection to FSM server')
        self.doQueryCmd('NOOP')


    def chkVersion(self):
        verbose_print('Checking version of FSM server')
        verstr = self.doQueryCmd('VERSION')
        ver = int(verstr.split()[0])
        if (ver >= MIN_SERVER_VERSION):
            okversion = True
            verbose_print('FSM server protocol version %s\n'%verstr.split('\n')[0])
        else:
            # --- FIXME: This should raise an exception --
            okversion = False
            verbose_print('The FSM server does not meet the minimum protocol'+\
                  ' version requirement of %u'%MIN_SERVER_VERSION)
        self.doQueryCmd('CLIENTVERSION %u'%MIN_SERVER_VERSION)

    def setStateMachine(self,fsmID):
        '''
        Assign an ID on the FSM server to the current state machine.

        The ID is a value from 0 to 5 to indicate which of the 6 state
        machines on the FSM server we are going to use.  It is
        important to also make sure the number of the state machine
        corresponds to the number of the soundcard used for sound
        triggering.
        '''
        self.fsm_id = fsmID
        self.doQueryCmd('SET STATE MACHINE %d'%fsmID)

    def getStateMachine(self):
        '''Query the FSM server about the current state machine ID (out of 6).'''
        smIDstr = self.doQueryCmd('GET STATE MACHINE')
        smID = int(smIDstr.split()[0])
        return smID


    def receiveAck(self,cmd,result,ackstring='OK'):
        '''Check that FSM server sent an acknowledgement for the last command.
        The acknowledgement string is either 'OK' or 'READY'
        '''
        # FIX ME: is it really necessary to have result as arg?
        if result.endswith(ackstring+'\n'):
            verbose_print('Received %s after %s'%(ackstring,cmd))
        else:
            # --- FIXME: define exception --
            verbose_print('Server returned: %s'%result)
            raise TypeError(('RTLinux FSM Server did not send %s '+\
                             'after %s command.')%(ackstring,cmd))


    def setInputEvents(self,val,channeltype):
        ### FIXME check .../Modules/@RTLSM2/SetInputEvents.m for what should go here
        # Check validity of 'val': positive scalar or ?
        # Check validity of 'channeltype': either 'ai' or 'dio'
        '''
        From .../Modules/@RTLSM2/SetInputEvents.m 
        Specifies the input events that are caught by the state
        machine and how they relate to the state matrix.
        The first simple usage of this function just tells the 
        state machine that there are SCALAR number of input
        events, so there should be this many columns used in the
        state matrix for input events.  The last parameter to 
        these function(s) is a string specifying either: 'ai' or
        'dio'.  The string 'ai' signifies we are monitoring AI
        lines for input events.  'dio' signifies we are monitoring
        DIO lines for input events.  (All other strings will
        generate an error, of course.)

        The second usage of this function actually specifies how
        the state machine should route physical input channels to 
        state matrix columns.  Each position in the vector 
        corresponds to a state matrix column, and the value of 
        each vector position is the channel number to use for that
        column.  Positive values indicate a rising edge event, and
        negative indicate a falling edge event (or OUT event). A
        value of 0 indicates that this is a 'virtual event' that
        gets its input from the Scheduled Wave specification.

        So [1, -1, 2, -2, 3, -3] tells the state machine to route
        channel 1 to the first column as a rising edge input
        event, channel 1 to the second column as a falling edge
        input event, channel 2 to the third column as a rising
        edge input event, and so on.  Each scalar in the vector
        indicates a channel id, and its sign whether the input
        event is rising edge or falling edge.  Note that channel
        id's are numbered from 1, unlike the internal id's NI
        boards would use (they are numbered from 0), so keep that
        in mind as your id's might be offset by 1 if you are used
        to thinking about channel id's as 0-indexed.
        
        The first usage of this function is shorthand and will
        create a vector that contains SCALAR entries as follows:
        [1, -1, 2, -2, ... SCALAR/2, -(SCALAR/2) ] 

        Note: this new input event mapping does not take effect
        immediately and requires a call to SetStateMatrix().
        '''
        if isinstance(val,int):
            # Create a vector of val entries [1,-1, 2,-2,...]
            f = lambda x : (x/2+1)*(2*(x%2)-1)
            val = map(f,range(val))
        # Assign vector of input events
        self.input_event_mapping = val
        self.in_chan_type = channeltype

    def getInputEvents(self):
        '''
        Returns the input event mapping vector for this FSM.

        This vector was set with a call to SetInputEvents (or was
        default).  The format for this vector is described in
        SetInputEvents() above.
        '''
        return self.input_event_mapping;

    def setOutputRouting(self,routing):
        '''
        Modify the output routing for a state machine.

        FIXME: This doc is from the matlab version. It should be
        updated.

        Output routing is the specification that the state machine
        uses for doing output when a new state is entered.  Using this
        call, you can specify the precise number and meaning of the
        last few columns of the state machine (which are typically
        output columns).  New output routings take effect after the
        next call to SetStateMatrix.

        The format for the output routing is an
        ordered (M x 1) cell array of structs.  The structs correspond
        to columns at the end of the state matrix.  Each struct needs
        to have the following fields: 'type' and 'data'.  'data' is
        interpreted in such a way as to depend on the 'type' field.
        The default output routing for a new state machine object is
        the following:

                { struct('type', 'dout', ...
                         'data', '0-15') ; ...
                  struct('type', 'sound', ...
                         'data', sprintf('%d', fsm.fsm_id)) };

        Which means that the last two columns of the state machine are
        to be used for 'dout' and 'sound' respectively.  The 'dout'
        column is to write data to DIO lines 0-15 on the DAQ card, and
        'sound' column is to trigger soundfiles to be played.

        OUTPUT ROUTING TYPES:

        'dout' - The state machine writes the bitpattern (of the
                 number converted to UINT32) appearing in this column
                 to DIO lines.  Each bit in this number corresponds to
                 a DIO line.  0 means all low (off), 1 means the first
                 line is high (the rest are off), 2 the second is
                 high, 3 the first *two* are high, etc.  The 'data'
                 field of the struct indicates which channels to
                 use. The example above has '0-15' in the data filed
                 meaning use 16 channels from channel 0-15 inclusive.
                          
        'trig' - Identical to the 'dout' type above, however the
                 'trig' type uses a TTL pulse that stays on for 1 ms
                 and then automatically turns off.  So for instance
                 where a 'dout' output of '1' would turn channel 0 on
                 indefinitely (until explicitly turned off by a
                 different state with that bit cleared) a 'trig'
                 output of '1' would always issue a 1ms TTL pulse on
                 the first channel (automatically setting that channel
                 low after 1 ms of time has elapsed).
                  
        'sound' - DEPRECATED (use 'ext' for sounds). The state machine
                 triggers a sound file to play by communicating with
                 the RT-SoundMachine and giving it the number
                 appearing in this column as a sound id to trigger.
                 Note that sounds can be untriggered by using a
                 negative number for the sound id.  The 'data' field
                 is a number string and specifies which sound card to
                 use.  Default is the same number as the fsm_id at
                 RTLSM2 object creation.  Note: when changing FSM id
                 via SetStateMachine.m, be sure to update this number!
                 Note that 'sound' is implemented using 'ext' so the
                 two may not be used at the same time!

        'ext' - The state machine triggers an external module.  By
                 calling its function pointer.  See
                 include/FSMExternalTrig.h and kernel/fsm.c.  Note
                 that 'sound' is implemented using 'ext' so the two
                 may not be used at the same time!

         'sched_wave' - The state machine uses this column to trigger
                 a scheduled wave (analog or digital sched wave).  The
                 'data' field of the struct is ignored.

         'tcp' - The state machine uses this column to trigger a TCP
                 message to be sent in soft-realtime using regular
                 linux networking services.  The 'data' field should
                 be of the form: 'host:port:My data packet %v' Where
                 host is the hostname to contact via TCP, port is the
                 port number of the host, and the last field is an
                 arbitrary text string to be sent to the host (a
                 trailing newline is automatically appended if
                 missing).

                 The %v format specifier tells the state machine to
                 place the number from the state machine column
                 (value) in this %v position.  In this way it is
                 possible to tell some external host *what* the state
                 machine column contained (for example to trigger some
                 external device on the network, etc).  Note that the
                 TCP packet is only sent when the output value
                 *changes*.  This way you don't always get a TCP
                 packet being sent for all of your state matrix states
                 -- you only get 1 TCP packet sent for each change in
                 value of this column.
                          
                 Note about 'tcp': This mechanism is useful for
                 triggering the olfactometer.  You can use the
                 following format to trigger an external olfactometer
                 (at eg IP address 143.48.30.39) to switch odors
                 during the course of an experiment trial:

                          struct('type', 'tcp', ...
                                 'data', '143.48.30.39:3336:SET ODOR Bank1 %v');

                 Thus, for this state machine column, whenever it
                 changes value a TCP message will be sent to
                 143.48.30.39 on port 3336 (the olfactometer port)
                 with the olfactometer command SET ODOR Bank1 %v where
                 %v is the value of the state matrix entry that
                 triggered the output.
                       
                 NOTE: A new connection is initiated each time a TCP
                 message is sent, and then it is immediately closed
                 when the message is finished sending.  There is no
                 way to know from Matlab if the connection failed.
                 One must instead check the console log on the Linux
                 FSM Server.

                 NOTE2: in addition to the state machine column value
                 being placed whenever a %v is encountered in the
                 string, the following other % format codes are also
                 interpreted:

                          %t - Timestamp_seconds (a floating point number)
                          %T - Timestamp_nanos  (a fixed point integer)
                          %s - State machine state (a fixed point integer)
                          %c - State machine column(a fixed point integer)
                          %% - Literal '%' character
                          (Every other %-code gets consumed and
                          produces no output).

                 Examples:

                 Input string to 'data' field of struct:
                  '143.48.30.39:3336:The timestamp was %t seconds
                   (%T nanoseconds) for state %s, col %c the value was %v.'
       
                 Sends (to port 3336 at IP 143.48.30.39): 
                  'The timestamp was 25.6 seconds (2560000000 nanoseconds)
                   for state 10, col 1 the value was 13.'

                          
         'udp' - Identical to 'tcp' above but the protocol used is UDP
                 (a less reliable but faster connectionless version of
                 TCP). UDP doesn't work for olfactometers, though. It
                 is only useful for network servers that support UDP,
                 and is implemented here for completeness.

         'noop' - The state machine column is to be ignored, it is
                 just a placeholder.  This defines a state machine
                 column as existing, but it is never used for anything
                 other than to take up space in the state matrix.
        '''
        # FIXME: Check validity of input 
        # Loop through specified outputs
        for oneoutput in routing:
            outputdtype = oneoutput['dtype'].lower()
            if outputdtype in ['dout','trig']:
                # FIXME: Test for validity of data with format '%d-%d'
                datalist = oneoutput['data'].split('-')
                (first,last) = map(int,datalist)
                if (first<0 or first>last or last>31):
                    # FIXME: define exception
                    raise TypeError('Digital outputs have to be values '+
                                    'between 0-31 and in order.')
            elif outputdtype=='sound':
                # Server protocol expects 'ext' instead of 'sound' here.
                # FIXME: define exception
                raise TypeError("The FSM now expects 'ext' as the output"+\
                                'routing type for sound triggering')
            elif outputdtype=='ext':
                # FIXME: Check that there is only one 'ext'?
                pass
            elif outputdtype=='sched_wave':
                pass
            elif outputdtype=='noop':
                pass
            elif outputdtype in ['dout','trig']:
                # FIXME
                pass
            else:
                # FIXME: define exception
                raise TypeError("Routing type '%s' is invalid."%outputdtype)
        # FIXME: is the next line necessary? only if routing changed
        #self.output_routing = routing


    def getOutputRouting(self):
        '''
        Retreive the currently specified output routing for the fsm.

        Note that output routing takes effect on the next call to
        SetStateMatrix().  For more documentation on output routing
        see SetOutputRouting().
        '''
        return self.output_routing;


    def setScheduledWavesDIO(self,sched_matrix):
        '''
        Set the schedule waves matrix, without sending it to server.

        sm = SetScheduledWaves(sm, sched_matrix)  % Digital I/O line schedwave
 
        sm = SetScheduledWaves(sm, sched_wave_id, ao_line, loop_bool,
        two_by_n_matrix) % Analog I/O line schedwave

        There are two usages of this function, with somewhat different
        implications.  The first usage is for a DIO-line scheduled
        wave, the second is for an AO-line scheduled wave.  See
        descriptions below.

        Note: it is now necessary to call SetOutputRouting() in order
        to specify a column of the state matrix that actually TRIGGERS
        these scheduled waves.  See SetOutputRouting.m documentation
        for more details.


        DIGITAL I/O LINE SCHEDULED WAVE
        -------------------------------

        sm = SetScheduledWaves(sm, sched_matrix)

        Specifies the scheduled waves matrix for a state machine.
        This is an M by 8 matrix of the following format per row:
        ID  IN_EVENT_COL  OUT_EVENT_COL  DIO_LINE
        SOUND_TRIG  PREAMBLE  SUSTAIN  REFRACTION

        Note that this function doesn't actually modify the SchedWaves
        of the FSM immediately.  Instead, a new SetStateMatrix call
        needs to be issued for the effects of this function to take
        effect in the external RTLinux FSM.

        Detailed Explanation of DIO Line Scheduled Wave
        -----------------------------------------------

        The sched matrix is an M by 8 matrix of the following format:
        ID  IN_EVENT_COL  OUT_EVENT_COL  DIO_LINE
        SOUND_TRIG  PREAMBLE  SUSTAIN  REFRACTION

        Note that this function doesn't actually modify the SchedWaves
        of the FSM.  Instead, a new SetStateMatrix (or
        SetStateProgram) call needs to be issued for the effects of
        this function to actually take effect in the external RTLinux
        FSM.

        ID - the numeric id of the scheduled wave.  Each wave is
             numbered from 0-31.  (NOTE: 0 is a valid ID!). The ID is
             later used in the StateMatrix SCHED_WAVE column as a
             bitposition.  So for example if you want wave number with
             ID 10 to fire, you use 2^10 in the SCHED_WAVE column of
             the state matrix and 10 as the ID in this matrix.  You
             can *untrigger* scheduled waves by issuing a negative
             number.  To untrigger wave ID 10, you would issue -(2^10)
             in your state matrix.

        IN_EVENT_COL - The column of the state matrix (not counting
             existing columns, so that 0 should be used for the first
             sched wave) which is to be used as the INPUT event column
             when this wave goes HIGH (edge up). Think of this as a
             WAVE-IN event. Set this value to -1 to have the state
             machine not trigger a state matrix input event for
             edge-up transitions.
 
        OUT_EVENT_COL - The column of the state matrix (0 being the
             first column) which is to be used as the INPUT event
             column when this wave goes LOW (edge down).  Think of
             this as a WAVE-OUT event.  Set this value to -1 to have
             the state machine not trigger a state matrix input event
             for edge-down transitions.

        DIO_LINE - The DIO line on which to echo the output of this
             waveform.  Note that not all waves need have a real DIO
             line associated with them.  Set this value to -1 to not
             use a DIO line.

        SOUND_TRIG - The sound id to trigger when 'sustain' occurs, and
             then to untrigger when 'refraction' occurs.  0 for none.

        PREAMBLE (seconds) - The amount of time to wait (in seconds)
             from the time the scheduled wave is triggered in the
             state matrix SCHED_WAVE column to the time it actually
             goes high.  Fractional numbers are ok.  Note the
             granularity of this time specification is the time
             quantum of the state machine (typically 166 microsecs),
             so values smaller than this quantum are probably going to
             get rounded to the nearest quantum.

        SUSTAIN (seconds) - The amount of time to wait (in seconds)
             from the time the scheduled wave is goes high to the time
             it should go low again.  Stated another way, the amount
             of time a scheduled wave sustains a high state.
             Fractional numbers are ok.  Note the granularity of this
             time specification is the time quantum of the state
             machine (typically 166 microsecs), so values smaller than
             this quantum are probably going to get rounded to the
             nearest quantum

        REFRACTION (seconds) - The amount of time to wait (in seconds)
             from the time the scheduled wave is goes low to the time
             it can successfully be triggered again by the SCHED_WAVE
             column of the state matrix. Fractional numbers are ok.
             Note the granularity of this time specification is the
             time quantum of the state machine (typically 166
             microsecs), so values smaller than this quantum are
             probably going to get rounded to the nearest quantum.
        '''
        # FIXME: what happends if input is empty matrix?
        # -- If only one row, make it a 2d-array --
        if isinstance(sched_matrix[0],int):
            sched_matrix = [sched_matrix]
        (nrows,ncols) = matsize(sched_matrix)
        if(nrows<1 or ncols!=8):
            raise TypeError('Matrix with schedule waves has to be m x 8.')
        # -- Check for duplicates by checking IDs --
        schedwaveIDs = []
        for schedwave in sched_matrix:
            if schedwave[0] > 32:  # FIXME: Shouldn't this be 31?
                raise ValueError('Schedule wave ID has to be less than 32.')            
            if schedwave[0] in self.sched_waves_ao:
                raise ValueError('There is an analog schedule wave with the '+\
                                 'same ID as this one.')
            if schedwave[0] in schedwaveIDs:
                raise ValueError('There is a duplicate schedule wave ID.')
            else:
                schedwaveIDs.append(schedwave[0])
        self.sched_waves = sched_matrix

             
    def setScheduledWavesAO(self,sched_matrix_id, ao_line, loop_bool, two_by_n_matrix):
        '''
        ANALOG I/O LINE SCHEDULED WAVE
        ------------------------------

        sm = SetScheduledWaves(sm, sched_wave_id, ao_line, loop_bool, two_by_n_matrix)
                
        Specifies a scheduled wave using analog I/O for a state
        machine.  The sched_wave_id is in the same id-space as the
        digital scheduled waves described above. The ao_line is the
        analog output channel to use, starting at 1 for the first AO
        line.  loop_bool, if true, means this is a looping wave (it
        loops until untriggered).The last parameter, a 2-by-n matrix,
        is described below.

        Detailed Explanation of AO Line Scheduled Wave
        ----------------------------------------------
 
        Like a digital scheduled wave described above, an analog
        scheduled wave is triggered from the SCHED_WAVES column of the
        state matrix using a 2^sched_wave_id bit position.  Triggering
        it actually causes samples to be written to the ao_line output
        channel on the DAQ card (AO lines are indexed from 1). The
        samples to be written (along with the events in the FSM to
        trigger) are specified in a two-by-n matrix as the fourth
        parameter to this function.  As the output wave is played,
        events to the state machine can be generated to update/notify
        the state machine of progress during playback (see description
        of the two-by-n matrix below).

        Note that this function does not actually modify the
        SchedWaves of the FSM immediately. Instead, a new
        SetStateMatrix call needs to be issued for the effects of this
        function to take effect in the external RTLinux FSM.

        Two-by-n-matrix description
        ---------------------------
        The actual samples to be written to the ao_line are specified in
          a two-by-n matrix.

        The first row of this matrix is a row-vector of samples over
        the range [-1,1].  They get automatically scaled to the output
        range setting of the DAQ hardware (0-5V for instance, etc).
        The rate at which these samples get written is usually 6kHz,
        but it depends on the rate at which the FSM is running, and it
        cannot be changed from Matlab (it is a parameter to the
        realtime kernel module implementing the actual FSM).

        The second row of the matrix may be all zeroes.  If any
        position in the matrix is not zero, then it indicates an input
        event number in the state machine (indexed at 1) to trigger
        when the corresponding sample (in the first row) is
        played. The purpose of this feature is to allow the state
        machine to be notified when 'interesting' parts of the
        scheduled analog wave are being played, so that the state
        machine may do something with that information such as: change
        its state, jump to a sub-block of states, etc.

        Example:

        SetScheduledWaves(sm, 0, 1, 0, [ -1 -.999 -.988 0.25 0.26; ...
                                         0     0     0   1    0   ]);

        Would specify a scheduled wave with id 0, on analog line 1
        (the first line), non-looping.  When wave id 0 is triggered,
        the state machine is to play the five samples in row 1 of the
        above matrix (normally your output matrix will contain more
        than 5 samples -- this is not very useful since it is only 5
        samples at 6kHz but it is an example after all).  For all but
        the fourth sample, no event in the state machine is
        triggered. However, as soon as the fourth sample is played by
        the state machine, input event column 1 (the first column) of
        the state matrix is sent an event (which might cause a state
        transition, depending on the state matrix).

        BUGS & QUIRKS
        -------------

        Untriggering analog or digital scheduled waves requires you to
        issue a *negative* bitpattern.  So to untrigger waves 1,2,3
        and 5 you would need to issue -(2^1+2^2+2^3+2^5) in your state
        matrix scheduled waves output column.

        Triggering sounds from DIO scheduled waves requires the
        @RTLSM2 to have a 'sound' or 'ext' output routing spec (see
        SetOutputRouting).  If it doesn't, the FSM doesn't know which
        sound card to trigger to, so nothing is triggered.  Also, more
        than 1 sound output routing spec leads to undefined behavior
        (as in this case the sound card to trigger is ambiguous).

        The DIO SetScheduledWaves indexes I/O lines at 0 and state
        event columns at 0 while its analog counterpart indexes I/O
        lines at 1 and the same state event columns at 1.  This is
        inconsitent. Let me know which one should win -- ie if you
        want consistency tell me if you prefer indexing at 1 or at 0.
        [Probably written by Calin who rarely adds his name to code]

        The DIO SetScheduledWaves specifies *all* DIO sched waves at
        once as one call, whereas the AO SetScheduledWaves specifies
        one AO wave per call (thus requiring multiple calls for
        multiple AO waves).

        If these functions are called and an AO wave has the same id
        as a pre-existing DIO wave (or vice-versa), the existing wave
        is discarded and a warning is issued.

        '''
        # FIXME: finish this
        pass

    def clearScheduledWaves(self):
        '''
        Clears all scheduled waves.

        Like SetScheduledWaves, this takes effect after the next call
        to SetStateMatrix.
        '''
        self.sched_waves = []     #zeros(0, size(sm.sched_waves,2));
        self.sched_waves_ao = []  #cell(0, size(sm.sched_waves_ao,2));

    def getScheduledWavesDIO(self):
        '''
        Return the current scheduled waves matrix for Digital I/O
        lines registered with a state machine.

        Note that only if SetStateMatrix.m has been called will the
        registered scheduled waves be actually sent to the RT Linux
        machine, so be careful and don't assume that the
        ScheduledWaves returned here are already running unless you
        know that SetStateMatrix has been called.
        '''
        return self.sched_waves

    def startDAQ(self):
        '''
        Specify a set of channels for analog data acquisition, and
        start the acquisition.

        Pass a vector of channel id's which is the set of analog input
        channels that should appear in each scan.
               
        For the purposes of this function, channel id's are indexed
        from 1.

        RANGE SETTINGS:

        Optionally, there is support for specifying a preferred analog
        input range (gain) setting for the DAQ card.  This parameter
        is a vector of the form [minV, maxV] where minV and maxV are
        the minimum and maximum values of the analog input range
        desired.  It defaults to [0, 5].  For a 0-5V range.
               
        Note that the actual set of analog input ranges that are
        supported is DAQ card-specific.  There is no guarantee that
        the specified range can be satisfied, since the card may not
        actually support the specified range.  Additionally, there is
        a further restriction to range settings: They cannot conflict
        with the state machine input channel ranges.  State machine
        input channels always use the implicit range setting of [0,5],
        and so if you happen to be using 'ai' input channels (see the
        SetInputEvents function documentation), and you are using a
        particular channel for both input events and data acquisition,
        *and* if your range vector specifies a range other than [0,5],
        the call to StartDAQ() will fail with an error.

        ACQUISITION SCAN RATE:

        The scan rate (sampling rate) for the data acquisition is the
        same as the clock rate of the FSM, which actually depends on
        how the FSM kernel module was loaded into the RTLinux kernel.
        As a consequence, it is not possible to change the scan rate
        from Matlab at this time.
               
        NOTES:

        The FSM supports data acquisition by reading a set of Analog
        Input channels from the DAQ hardware and buffering them as a
        set of scans.  You need to periodically call 'GetDAQScans()'
        which empties this buffer and returns a matrix of doubles
        which are the voltages read from the DAQ hardware.  This
        matrix is M by N where M corresponds to the number of scans in
        the buffer since the last call to GetDAQScans() and N 1 plus
        the number of channels in each scan (first column is timestamp
        in seconds which is the same timestamp returned by the
        statemachine's GetEvents() function).  Note that the order of
        the channels in each scan is sorted by channel id (so that if
        you specified [1,5,3] as your channel spec, you will get them
        in the order of [1,3,5].

        Since the scans are kept in a finitely-sized buffer, you
        should call GetDAQScans() relatively frequently to ensure you
        don't have any dropped scans due to buffer overflows.

        EXAMPLES:

        If you want to capture channels 1, 3, and 8 (in that order)
        using the default range setting of [0, 5] you would specify:

               sm = StartDAQ(sm, [1, 3, 8]);


         To capture channels 1,2,3 using [-5,5] as the range setting
         you would specify:

               sm = StartDAQ(sm, [1, 2, 3], [-5, 5])

         To retreive the acquired data, later call:

               scans = GetDAQScans(sm);
        '''
        # FIXME: write this method
        pass

    def getDAQScans(self):
        '''
        Retreive the latest block of scans available.

        That is, if the state machine is acquiring data.  See
        StartDAQ().  The returned matrix is MxN where M is the number
        of scans available since the last call to GetDAQScans and N is
        a timestamp column followed by the scan voltage value.

        EXAMPLES:

        To retreive the acquired data call:

                scans = GetDAQScans(sm);
        '''
        # FIXME: write this method
        pass

    def stopDAQ(self):
        '''Stop the currently-running data acquisition. See StartDAQ().'''
        doQueryCmd('STOP DAQ')

    def registerEventsCallback(self):
        '''
        Enable asynchronous notification as the FSM gets new events
        (state transitions).

        Your callback code is executed as new events are generated by
        the FSM.  Your code is evaluated (using the equivalent of an
        eval).  When your code runs, the event(s) that just occurred
        are in an Mx4 matrix (as would be returned from GetEvents())
        as the special variable 'ans'.  Thus, your callback code
        should save this variable right away lest it be destroyed by
        subsequent matlab statements.  Pass an empty callback to
        disable the EventsCallback mechanism (or call
        StopEventsCallback).

        Optionally you can pass a third parameter, an additional
        callback to use so that your code can be notified if there is
        an unexpected TCP connection loss to the FSM server.  This is
        so that your code can be notified that no more events will
        come in due to a connection loss.  Otherwise, it would be
        impossible to know that no more events are possible -- your
        code might wait forever for events that will never arrive.
        Possible actions to take in this callback include displaying
        error messages in matlab and/or trying to restart the
        connection by calling RegisterEventsCallback again.

        Note: This entire callback mechanism only works under Windows
        currently and requires that the executable
        FSM_Event_Notification_Helper_Process.exe be in your Windows
        PATH or in the current working directory!

        Note 2: The events callback mechanism is highly experimental
        and as such, only a maximum of 1 callbacks may be registered
        and enabled at a time globally for all instances of RTLSM2
        objects in the matlab session.  What does this mean?  That
        subsequent calls to this function for *any* insance of an
        @RTLSM2 will actually kill/disable the existing callback that
        was previously registered/active for any other instance of an
        @RTLSM2.
        '''
        # FIXME: write this method
        pass

    def stopEventsCallback(self):
        '''
        Disables asynchronous notification.

        This method unregisters any previously-regsitered callbacks.
        See RegisterEventsCallback()
        '''
        # FIXME: write this method
        pass


    def close(self):
        '''
        Close connection to server.
        '''
        self.halt()
        self.socketClient.close()


    def bypassDout(self,d):
        '''
        Set digital outputs.

        Set outputs to be whatever the state machine would indicate,
        bitwise or `d with "d." To turn this off, call bypassDout(0).
        
        NOTE by sjara (2009-11-07): This is the comment from the
        Matlab version, I don't understand what this does.
        '''
        self.doQueryCmd('BYPASS DOUT %d'%d)


    def triggerSound(self,d):
        '''
        Triggers the sound corresponding to the given ID, bypassing
        the control over sound triggers.
        '''
        self.doQueryCmd('TRIGSOUND %d'%d)


    def getEventCounter(self):
        '''
        Get the number of events that have occurred since the last
        call to initialize().
        '''
        eventcountstr = self.doQueryCmd('GET EVENT COUNTER')
        return int(eventcountstr.split()[0])


    def getEventsOLD(self,startEventNumber,endEventNumber):
        '''
         Get a matrix in which each row corresponds to an event.
         This method has been replaced by a newer GetEvents().
         
         The matrix will have EndEventNumber-StartEventNumber+1 rows
         and 4 columns. (If EndEventNumber is bigger than
         GetEventCounter(), this produces an error).

         Each of the rows in EventList has 4 columns:

         1. The first is the state that was current when the event
            occurred.

         2. The second is the event_id, which is 2^(event_column) that
            occurred. event_column is 0-indexed.  See SetInputEvents()
            for a description of what we mean by event columns.

            In the default event column configuration
            SetInputEvents(sm, 6), you would have as possible
            event_id's:

            1=Cin, 
            2=Cout, 
            4=Lin, 
            8=Lout, 
            16=Rin,
            32=Rout, 
            64=Tup, 
            0=no detected event, (e.g. when a jump to state 0 is forced)
        
         3. The third is the time, in seconds, at which the
            event occurred.

         4. The fourth is the new state that was entered as a result
            of the state transition.
        '''
        # FIXME: implement this function? it is deprecated.
        if startEventNumber>endEventNumber:
            eventList = []
        else:
            eventList = self.doQueryMatrixCmd('GET EVENTS %d %d'%\
                                               (startEventNumber-1,\
                                                endEventNumber-1))
        return eventList


    def getEvents(self,startEventNumber,endEventNumber):
        '''
        Get a matrix in which each row corresponds to an event.
        This improved version replaces GetEventsOLD().

        Improved version of GetEvents.m which supports more than 32
        input events.  GetEventsOLD had the returned event-id be a
        bitset where the bit corresponding to the event-column that
        triggered the state transition would be set.  Use of a bitset
        meant that the event-id would be 2^FSM_COLUMN_OF_INPUT_EVENT,
        which effectively limited the maximum event id to 2^31 on
        32-bit machines.

        This new method fixes that by returning the actual event
        column number in col2, rather than 2^event_col.

        Gets a matrix in which each row corresponds to an Event; the
        matrix will have EndEventNumber-StartEventNumber+1 rows and 4
        columns. (If EndEventNumber is bigger than GetEventCounter(),
        this produces an error).

        Each of the rows in EventList has 4 columns:

        1. The first is the state that was current when the event
           occurred.

        2. The second is the event_column number.  See
           SetInputEvents() for a description of what we mean by event
           columns. In the default event column configuration
           SetInputEvents(sm, 6), you would have as possible
           event_id's:

           0=Cin, 
           1=Cout, 
           2=Lin, 
           3=Lout, 
           4=Rin,
           5=Rout, 
           -1=TIME'S UP EVENT *or* no detected event,
              (e.g. when a jump to state 0 is forced)
       
        3. The third is the time, in seconds, at which the event
           occurred.

        4. The fourth is the new state that was entered as a result of
           the state transition.
        '''
        if startEventNumber>endEventNumber:
            eventList = []
        else:
            eventList = self.doQueryMatrixCmd('GET EVENTS_II %d %d'%\
                                               (startEventNumber-1,\
                                                endEventNumber-1))
        return eventList


    def getTime(self):
        '''
        Get time elapsed (in sec) since last call to initialize().

        Returns: etime
        '''
        etimestr = self.doQueryCmd('GET TIME')
        etime = float(etimestr.split()[0])
        return etime


    def getTimeEventsAndState(self,firstEvent):
        '''
        Request both the time and the events matrix.

        Gets the time, in seconds, that has elapsed since the last
        call to initialize(), as well as the Events matrix starting
        from firstEvent up until the present.
 
        The returned struct has the following 4 fields:
                time:       time in seconds.
                state:      state number the state machine is currently in.
                eventcount: event number of the latest event.
                events:     m by 5 matrix of events.
        '''
        # FIXME: is eventcount correct? or shifted by +1?
        cmd = 'GET TIME, EVENTS, AND STATE %d'%firstEvent
        resultstr = self.doQueryCmd(cmd,expect='')
        resultsbyline = resultstr.splitlines()
        if(len(resultsbyline) != 4):
            raise TypeError('FSM server did not return the correct values.')
        etime = float(resultsbyline[0].split()[1])              # TIME %f
        state = int(resultsbyline[1].split()[1])                # STATE %d
        eventcount = int(resultsbyline[2].split()[2])           # EVENT COUNTER %d
        (nrows,ncols) = map(int,resultsbyline[3].split()[1:3])  # MATRIX %d %d
        # FIXME: this code is repeated in doQueryMatrixCmd()
        #        they should be split/recombined/merged
        self.sendString('READY\n')
        (mat,ackstr) = self.readMatrix(nrows,ncols)
        self.receiveAck(cmd,ackstr,'OK')
        # FIXME: make this dict into an object
        allresults = {'etime':etime,'state':state,\
                      'eventcount':eventcount+firstEvent,'events':mat}
        return allresults


    def isRunning(self):
        '''Return True if state machine is running, False if halted.'''
        runningstr = self.doQueryCmd('IS RUNNING')
        running = bool(int(runningstr.split()[0]))
        return running


    def getVarLogCounter(self):
        '''Get the number of variables that have been logged since the
           last call to initialize().'''
        varlogcountstr = self.doQueryCmd('GET VARLOG COUNTER')
        varlogcount = int(varlogcountstr.split()[0])
        return varlogcount


    def getAIMode(self):
        # FIXME: write this method
        pass


    def setAIMode(self,mode):
        # FIXME: write this method
        pass

 
    def forceState(self, state):
        '''Force an immediate jump to a state.'''
        self.doQueryCmd('FORCE STATE %d'%state)


    def doQueryCmd(self,cmd,expect='OK'):
        self.sendString(cmd+'\n')
        result = self.readLines()
        self.receiveAck(cmd,result,expect)
            
        '''
        --- SHOULD I SPLIT LINES HERE? ---
        results = lines.splitlines()
        for ind in results: print results
        if results[-1]=='OK':
            print results
        else:
            print 'WARNING: FSM did not return OK at the end of query: %s'%cmd
        '''
        return result


    def doQueryMatrixCmd(self,cmd):
        self.sendString(cmd+'\n')
        matsizestr = self.readLines()
        if 'ERROR' in matsizestr:
            raise ValueError('FSM server returned an error after '+\
                             'command: %s',cmd)
        if(matsizestr.startswith('MATRIX ')):
            (nrows,ncols) = map(int,matsizestr.split()[1:3])
        else:
            raise ValueError('FSM server returned incorrect string '+\
                             'for command: %s',cmd)
        self.sendString('READY\n')
        (mat,ackstr) = self.readMatrix(nrows,ncols)
        self.receiveAck(cmd,ackstr,'OK')
        return mat


    def forceTimeUp():
        '''
        Sends a signal to the state machine to force time up.

        This is equivalent to there being a TimeUp event in the state
        that the machine is in when the ForceTimeUp() signal is
        received. Note that due to the asynchronous nature of the link
        between the client and StateMachines, the StateMachine
        framework itself provides no guarantees as to what state the
        machine will be in when the ForceTimeUp() signal is received.
        '''
        self.doQueryCmd('FORCE TIME UP')


    def readyToStartTrial():
        '''
        Signals the StateMachine that it is ok to start a new trial.

        After this routine is called, the next time that the
        StateMachine reaches state 35, it will immediately jump to
        state 0, and a new trial starts.
        '''
        self.doQueryCmd('READY TO START TRIAL')


    def sendData(self,mat,expect='OK'):
        dataToSend = packmatrix(mat)
        self.sendString(dataToSend)
        result = self.readLines()
        self.receiveAck('Sending data',result,expect)


    def initialize(self):
        '''
        Clear all variables, including the state matrices, and
        initializes the state machine.

        initialize() does not start the StateMachine running.  It is
        necessary to call Run() to do that.
        '''
        self.doQueryCmd('INITIALIZE')

    def run(self):
        '''
        Resume a halted StateMachine, so that events have an effect
        again.

        After an initialize(), Run() starts the machine in state
        0. After a Halt(), Run() restarts the machine in whatever
        state is was halted. Note that calling Run() before the state
        matrices have been defined produces undefined behavior and
        should be avoided.
        '''
        self.doQueryCmd('RUN')

    def halt(self):
        '''
        Pauses the StateMachine, putting it in a halted state.

        In this state, input events do not have any effect and state
        transitions are not made.  Variables are not cleared, however,
        and so they can be read by other programs.
        Calling Run() will resume a halted state machine.
        '''
        self.doQueryCmd('HALT')

    def setStateMatrix(self, state_matrix, pend_sm_swap=False):
        '''
        Define the state matrix that governs the control algorithm
        during behavior trials.

        The matrix is M x N, where M is the number of states (so each
        row corresponds to a state) and N is the number of input
        events + output events per state.
        This state_matrix can have nearly unlimited rows (i.e.,
        states), and has a variable number of columns, depending on
        how many input events are defined.
        To specify the number of input events, see SetInputEvents().
        The default number of input events is 6 (CIN, COUT, LIN, LOUT,
        RIN, ROUT).  In addition to the input event columns, the state
        matrix also has 4 or 5 additional columns:
         TIMEOUT_STATE    TIMEOUT_TIME    CONT_OUT    TRIG_OUT
         and the optional SCHED_WAVE.

        The second usage of this function specifies an optional flag.
        If the flag is True, then the state machine will not swap
        state matrices right away, but rather, will wait for the next
        jump to state 0 in the current FSM before swapping state
        matrices.  This is so that one can cleanly exit one FSM by
        jumping to state 0 of another, and thus have cleaner
        inter-trial interval handling.

        Notes:
        - The part of the state matrix that is being run during
          intertrial intervals should remain constant in between any
          two calls of initialize()
        - setStateMatrix() should only be called in-between trials.
        '''

        # FIXME: Check the validity of the matrix
        (nStates, nEvents) = matsize(state_matrix)
        nInputEvents = len(self.input_event_mapping)
        nColsForTimer = 2                      # TIMEOUT_STATE, TIMEOUT_TIME
        nColsForOutputs = len(self.output_routing)

        if(len(self.sched_waves)>0 or len(self.sched_waves_ao)>0):
            # Check ~/tmp/newbcontrol/Modules/@RTLSM2/SetStateMatrix.m
            # Verify that outputs for sched_waves are defined
            found=False
            for oneoutput in self.output_routing:
                if oneoutput['dtype']=='sched_wave':
                    found=True
                    break
            if(not found):
                errstr='The state machine has a sched_waves specification but\n'+\
                       'no sched_wave output routing defined!\n'+\
                       'Please specify a sched_wave output column '+\
                       'using SetOutputRouting!\n'
                raise TypeError(errstr)
            # FIXME: Original code could auto-add output routing
            #        Here I just raise an exception.


        # Verify matrix is sane with respect to number of columns
        if(nEvents != nInputEvents+nColsForTimer+nColsForOutputs):
            nstr = '%d(cols) = %d(input) + %d(timer) + %d(outputs)'%\
                   (nEvents,nInputEvents,nColsForTimer,nColsForOutputs)
            raise TypeError('Number of columns is not consistent '+
                            'with number of events: %s'%nstr)
            # FIXME: define this exception

        # Concatenate the input_event_mapping vector as the last row
        #  of the matrix, server side will deconcatenate it.
        extraRow = nEvents*[0]
        extraRow[0:nInputEvents] = self.input_event_mapping
        state_matrix.append(extraRow)

        # The matlab client did the following:
        # For each scheduled wave, simply add the spec as elements to
        # the matrix -- note these elements are not at all row-aligned
        # and you can end up with multiple sched_waves per matrix row,
        # or one sched_wave taking up more than one matrix row.  The
        # server-side will just pop these out in FIFO order to build
        # its own sched_waves data structure.  It just knows there are
        # 8 columns per scheduled wave.
        # Check ~/tmp/newbcontrol/Modules/@RTLSM2/SetStateMatrix.m
        #
        # NOTE: In this version of the client, I tried to send the
        # state matrix first, then the matrix of sched_waves, but it
        # did not work because matrices are send column-wise (and the
        # padding seems to be necessary).
        #
        # The next piece of code converts (if :
        #  sched_waves = [ [1,2,3,4,5,6,7,8], [9,10,11,12,13,14,15,16] ]
        # into:
        #  extraRows = [ [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        #                [12,13,14,15,16, 0, 0, 0, 0, 0 , 0 ] ]
        # and appends those rows to the state matrix
        nSchedWaves = len(self.sched_waves)
        if nSchedWaves>0:
            oneExtraRow = []
            for oneSchedWave in self.sched_waves:
                for value in oneSchedWave:
                    oneExtraRow.append(value)
                    if len(oneExtraRow)==nEvents:
                        state_matrix.append(oneExtraRow)
                        oneExtraRow = []
            nPadZeros = nEvents-len(oneExtraRow)
            LastRow = oneExtraRow + nPadZeros*[0]
            state_matrix.append(LastRow)
        
        # Format and urlencode the output_spec_str with format:
        # \1.dtype\2.data\1.dtype\2.data... where everything is
        # urlencoded (so \1 becomes %01, \2 becomes %02, etc)
        hasSound = False
        outputSpecStr = ''
        for oneoutput in self.output_routing:
            if oneoutput['dtype'] in ['tcp', 'udp']:
                # Force trailing newline for tcp/udp text packets.
                # FIXME: need to add '\n' at the end of data
                pass
            elif oneoutput['dtype'] in ['sound', 'ext']:
                hasSound = True
            stringThisOutput = '\\1%s\\2%s'%\
                               (oneoutput['dtype'],oneoutput['data'])
            outputSpecStr = ''.join((outputSpecStr,stringThisOutput))
        outputSpecStrUrlEnc = url_encode(outputSpecStr)
 
        # FIXME: Check if schedwave but no sound

        # Format for SET STATE MATRIX command is:
        # SET STATE MATRIX nRows  nCols  nInEvents  nSchedWaves
        #                  InChanType  ReadyForTrialJumpstate
        #                  IGNORED   IGNORED   IGNORED 
        #                  OutputSpecUrlEncoded  PendSMswap
        (nStates, nEvents) = matsize(state_matrix)
        stringpieces = 5*[0]
        stringpieces[0] = 'SET STATE MATRIX %u %u %u'%(nStates, nEvents, nInputEvents)
        stringpieces[1] = '%u %s'%(nSchedWaves, self.in_chan_type)
        stringpieces[2] = '%u'%(self.ready_for_trial_jumpstate)
        stringpieces[3] = '%u %u %u'%(0,0,0)
        stringpieces[4] = '%s %u'%(outputSpecStrUrlEnc, pend_sm_swap)
        stringtosend = ' '.join(stringpieces)

        self.doQueryCmd(stringtosend,expect='READY')
        self.sendData(state_matrix,expect='OK')

        # FIXME: Send AO waves


    def flushQueue(self):
        '''
        Not applicable to this client. It does nothing.

        Some state machines (e.g., RM1s, RTLinux boxes) will be
        self-running; others need a periodic ping to operate on events
        in their incoming events queue. This function is used for the
        latter type of StateMachines. In self-running state machines,
        it is o.k. to define this function to do nothing.
        '''
        pass


    def preferredPollingInterval(self):
        '''
        Not applicable to this client. It does nothing.

        For machines that require FlushQueue() calls, this function
        returns the preferred interval between calls. Note that there
        is no guarantee that this preferred interval will be
        respected. intvl_ms is in milliseconds.
        '''
        pass


    def flushSocket(self):
        '''Read whatever is left on the server's buffer.'''
        return self.readLines()



if __name__ == "__main__":

    TESTCASES = [1,2]

    if 0 in TESTCASES:  #'JustCreate':
        testSM = StateMachineClient('soul',connectnow=0)
    if 1 in TESTCASES:   #'CreateAndConnect':
        testSM = StateMachineClient('soul')
    if 2 in TESTCASES:   #'SendMatrixNoWaves':
        #        Ci  Co  Li  Lo  Ri  Ro  Tout  t  CONTo TRIGo SWo
        testSM.initialize()
        mat = [ [ 0,  0,  0,  0,  0,  0,  2,  1.2,  0,   0       ] ,\
                [ 1,  1,  1,  1,  1,  1,  1,   0,   0,   0       ] ,\
                [ 3,  3,  0,  0,  0,  0,  3,   4,   1,   0       ] ,\
                [ 2,  2,  0,  0,  0,  0,  2,   4,   2,   0       ] ]
        testSM.setStateMatrix(mat)
        testSM.run()
    if 3 in TESTCASES:   #'Get events':
        import time
        time.sleep(2)
        evs = testSM.doQueryMatrixCmd('GET EVENTS 1 2')
        print evs
    if 4 in TESTCASES:   #'Add sched waves':
        ### STILL DON'T KNOW HOW TO TRIGGER SCHED WAVES!!!
        testSM.output_routing.append({'dtype':'sched_wave', 'data':''})
        #               ID  In Out DIO Sound Pre Sus Refr
        schedwaves = [ [ 0, 6, 7,   1,   0,  0.5, 1,  0] ]
        testSM.setScheduledWavesDIO(schedwaves)
        testSM.input_event_mapping = [1,-1, 2,-2, 3,-3, 0, 0]
        #        Ci  Co  Li  Lo  Ri  Ro  SWi SWo Tup   t  CONTo TRIGo SWo
        mat = [ [ 0,  0,  0,  0,  0,  0,  0,  0,  2,  1.2,  0,   0,   0  ] ,\
                [ 1,  1,  1,  1,  1,  1,  0,  0,  1,   0,   0,   0,   0  ] ,\
                [ 3,  3,  0,  0,  0,  0,  1,  1,  2,  100,  1,   1,   1  ] ,\
                [ 2,  2,  0,  0,  0,  0,  1,  1,  3,  100,  2,   1,   1  ] ]
        testSM.setStateMatrix(mat)
        testSM.run()


    # == Other commands ==
    # testSM.initialize()
    # testSM.doQueryMatrixCmd('GET EVENTS 1 2')
    # testSM.sendString('VERSION\n')
    # testSM.readLines()
