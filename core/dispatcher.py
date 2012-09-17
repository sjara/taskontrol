#!/usr/bin/env python

'''
Dispatcher for behavioral protocols.

It is meant to be the interface between a trial-structured protocol
and the state machine. It will for example halt the state machine
until the next trial has been prepared and ready to start.

NOTES:
- Should I separate GUI from trial structure control?
- Should I implement it with QThread instead?
- If running on Windows I may need to change name to *.pyw
- Does the time keep going even if close the window?
- Crashing should be graceful (for example close connection to statemachine)
- Style sheets (used for changing color) may not be supported on MacOSX
- There is a delay when pressing Start button before it changes color.
  This happens even if I move the code to the beginning of the method,
  but only when I'm using the StateMachine (not in dummy mode).

TODO:
* When the form is destroyed, dispatcher.closeEvent is not called!
'''


__version__ = '0.1.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2012-08-20'

import sys
from PySide import QtCore 
from PySide import QtGui 
import numpy as np
#from taskontrol.core import messenger
#from taskontrol.core import smclient

#reload(smclient)


class Dispatcher(QtCore.QObject):
    '''
    Dispatcher is the trial controller. It is an interface between a
    trial-structured protocol and the state machine.

    It emits the following signals:
    - 'timerTic'        : at every tic of the dispatcher timer.
                          It sends: serverTime,currentState,eventCount,currentTrial
    - 'prepareNextTrial': whenever one of the prepare-next-trial-states is reached.
                          It sends: 'nextTrial'
    - 'startNewTrial'   : whenever READY TO START TRIAL is sent to state machine.
                          It sends: 'currentTrial'
    '''
    # -- Create signals (they need to be before constructor) --
    timerTic = QtCore.Signal(float,int,int,int)
    prepareNextTrial = QtCore.Signal(int)
    startNewTrial = QtCore.Signal(int)
    logMessage = QtCore.Signal(str)

    def __init__(self, parent=None,serverType='maple_dummy', connectnow=True, interval=0.3):
        super(Dispatcher, self).__init__(parent)

        if serverType=='maple':
            pass
        elif serverType=='maple_dummy':
            from taskontrol.plugins import smdummy as smclient
        else:
            pass
        
        # -- Set trial structure variables --
        self.prepareNextTrialStates = []
        self.preparingNextTrial = False      # True while preparing next trial

        # -- Create a state machine client --
        #self.host = host
        #self.port = port
        self.isConnected = False
        self.statemachine = smclient.StateMachineClient(connectnow=False)

        if connectnow:
            self.connect_to_sm()  # Connect to state machine

        # -- Create state machine variables --
        self.serverTime = 0.0   # Time on the state machine
        self.currentState = 0   # State of the state machine
        self.eventCount = 0     # Number of events so far
        self.currentTrial = 1   # Current trial
        #self.lastEvents = np.array([])   # Matrix with info about last events
        #self.eventsMat = np.empty((0,3)) # Matrix with info about all events
        self.lastEvents = []   # Matrix with info about last events
        self.eventsMat = []    # Matrix with info about all events

        # -- Create timer --
        self.interval = interval # Polling interval (sec)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.timeout)

    def connect_to_sm(self):
        '''Connect to state machine server and initialize it.'''
        self.statemachine.connect()
        #self.statemachine.initialize()
        self.isConnected = True

    def set_state_matrix(self,stateMatrix,stateOutputs,stateTimers,schedwavesmatrix=None):
        '''
        Send state transition matrix to server.
        If available, also send matrix of schedule waves.

        The matrices can be python lists (2D) or numpy arrays.
        '''
        if self.isConnected:
            #if not isinstance(statesmatrix,np.ndarray):
            #    statesmatrix = np.array(statesmatrix)
            if schedwavesmatrix:
                #self.statemachine.setScheduledWavesDIO(schedwavesmatrix)        
                print 'Sending sched waves; Not implemented yet.'
            self.statemachine.set_state_matrix(stateMatrix)
            self.statemachine.set_state_outputs(stateOutputs)
            self.statemachine.set_state_timers(stateTimers)
        else:
            print 'Call to setStateMatrix, but the client is not connected.\n'


    def ready_to_start_trial(self):
        '''
        Tell the state machine that it can jump to state 0 and start new trial.
        '''
        self.statemachine.force_state(0)
        self.currentTrial += 1
        self.preparingNextTrial = False
        self.startNewTrial.emit(self.currentTrial)

    def timeout(self):
        self.query_state_machine()
        self.timerTic.emit(self.serverTime,self.currentState,self.eventCount,self.currentTrial)
        print self.serverTime ### DEBUG
        # -- Check if one of the PrepareNextTrialStates has been reached --
        '''
        if self.lastEvents.size>0 and not self.preparingNextTrial:
            laststates = self.lastEvents[:,3]
            for state in self.prepareNextTrialStates:
                if state in laststates:
                    self.preparingNextTrial = True
                    self.emit(QtCore.SIGNAL('PrepareNextTrial'), self.currentTrial+1)
                    break
       '''

    #@QtCore.Slot()
    def resume(self):
        # --- Start timer ---
        self.timer.start(1e3*self.interval) # timer takes interval in ms
        # -- Start state machine --
        if self.isConnected:
            self.statemachine.run()
            self.logMessage.emit('Resume')
        else:
            print 'The dispatcher is not connected to the state machine server.'

    #@QtCore.Slot()
    def pause(self):
        # --- Start timer ---
        self.timer.stop()
        # -- Start state machine --
        if self.isConnected:
            self.statemachine.stop()
            self.logMessage.emit('Pause')
        else:
            print 'The dispatcher is not connected to the state machine server.'

    def query_state_machine(self):
        '''Request events information to the state machine'''
        if self.isConnected:
            #resultsDict = self.statemachine.getTimeEventsAndState(self.eventCount+1)
            self.serverTime = self.statemachine.get_time()
            self.lastEvents = self.statemachine.get_events()
            #self.eventsMat = np.vstack((self.eventsMat,self.lastEvents))
            self.eventsMat.append(self.lastEvents)
            self.currentState = self.eventsMat[-1][2]
            self.eventCount = len(self.eventsMat)
            # FIXME: this may fail if eventsMat is empty on the first call

    def die(self):
        '''Make sure timer stops when user closes the dispatcher.'''
        self.pause()
        if self.isConnected:
            # FIXME: set all outputs to zero
            #self.statemachine.bypassDout(0)
            self.statemachine.force_state(0)
            self.statemachine.close()



BUTTON_COLORS = {'start':'limegreen','stop':'red'}

class DispatcherGUI(QtGui.QGroupBox):
    resumeSM = QtCore.Signal()
    pauseSM = QtCore.Signal()
    def __init__(self, parent=None, minwidth=200, dummy=False):
        super(DispatcherGUI, self).__init__(parent)

        self.runningState = False

        # -- Set string formats --
        self._timeFormat = 'Time: %0.1f s'
        self._stateFormat = 'State: %d'
        self._eventCountFormat = 'N events: %d'
        self._currentTrialFormat = 'Current trial: %d'

        ################ FIX ME TEMPORARY. SHOULD NOT BE HERE !!!  #############
        self.time = 0.0         # Time on the state machine
        self.state = 0          # State of the state machine
        self.eventCount = 0     # Number of events so far
        self.currentTrial = 1   # Current trial
        
        # -- Create graphical objects --
        self.stateLabel = QtGui.QLabel(self._stateFormat%self.state)
        self.stateLabel.setObjectName('DispatcherLabel')
        self.timeLabel = QtGui.QLabel(self._timeFormat%self.time)
        self.timeLabel.setObjectName('DispatcherLabel')
        self.eventCountLabel = QtGui.QLabel(self._eventCountFormat%self.time)
        self.eventCountLabel.setObjectName('DispatcherLabel')
        self.currentTrialLabel = QtGui.QLabel(self._currentTrialFormat%self.currentTrial)
        self.currentTrialLabel.setObjectName('DispatcherLabel')
        self.buttonStartStop = QtGui.QPushButton('')
        self.buttonStartStop.setCheckable(False)
        self.buttonStartStop.setMinimumHeight(100)
        #self.buttonStartStop.setMinimumWidth(160)
        buttonFont = QtGui.QFont(self.buttonStartStop.font())
        buttonFont.setPointSize(buttonFont.pointSize()+10)
        self.buttonStartStop.setFont(buttonFont)
        self.setMinimumWidth(minwidth)

        # -- Create layouts --
        layout = QtGui.QGridLayout()
        layout.addWidget(self.stateLabel,0,0)
        layout.addWidget(self.eventCountLabel,0,1)
        layout.addWidget(self.timeLabel,1,0)
        layout.addWidget(self.currentTrialLabel,1,1)
        layout.addWidget(self.buttonStartStop, 2,0, 1,2) # Span 1 row, 2 cols
        self.setLayout(layout)
        self.setTitle('Dispatcher')

        # -- Connect signals --
        #self.connect(self.buttonStartStop, QtCore.SIGNAL("clicked()"),self.startOrStop)
        self.buttonStartStop.clicked.connect(self.startOrStop)

        self.stop()

    #@QtCore.Slot(float,int,int,int)  # FIXME: is this really needed?
    def update(self,serverTime,currentState,eventCount,currentTrial):
        '''Update display of time and events.'''
        self.timeLabel.setText(self._timeFormat%serverTime)
        self.stateLabel.setText(self._stateFormat%currentState)
        self.eventCountLabel.setText(self._eventCountFormat%eventCount)
        self.currentTrialLabel.setText(self._currentTrialFormat%currentTrial)

    def startOrStop(self):
        '''Toggle (start or stop) state machine and dispatcher timer.'''
        if(self.runningState):
            self.stop()
        else:
            self.start()

    def start(self):
        '''Resume state machine.'''
        # -- Change button appearance --
        stylestr = 'QWidget {background-color: %s}'%BUTTON_COLORS['stop']
        self.buttonStartStop.setStyleSheet(stylestr)
        self.buttonStartStop.setText('Stop')

        self.resumeSM.emit()
        self.runningState = True

    def stop(self):
        '''Pause state machine.'''
        # -- Change button appearance --
        stylestr = 'QWidget { background-color: %s }'%BUTTON_COLORS['start']
        self.buttonStartStop.setStyleSheet(stylestr)
        self.buttonStartStop.setText('Start')
        self.pauseSM.emit()
        self.runningState = False


    #------------------- End of DispatcherGUI class ------------------


def center(guiObj):
    '''Place in the center of the screen (NOT TESTED YET)'''
    screen = QtGui.QDesktopWidget().screenGeometry()
    size =  guiObj.geometry()
    guiObj.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)


if __name__ == "__main__":

    TESTCASE = 2
    if TESTCASE==1:
        import signal
        # -- Needed for Ctrl-C (otherwise you need to kill with Ctrl-\ 
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        app = QtCore.QCoreApplication(sys.argv)
        d = Dispatcher(parent=None,serverType='maple_dummy', connectnow=False, interval=1)
        d.start()
        sys.exit(app.exec_())
    elif TESTCASE==2:
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        app = QtGui.QApplication(sys.argv)
        form = QtGui.QDialog()
        form.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        #form.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        dispatcherModel = Dispatcher(parent=form,connectnow=True, interval=0.5)
        dispatcherView = DispatcherGUI(parent=form)
        dispatcherModel.timerTic.connect(dispatcherView.update)
        dispatcherView.resumeSM.connect(dispatcherModel.resume)
        dispatcherView.pauseSM.connect(dispatcherModel.pause)
        #dispatcherModel.start()
        form.show()
        app.exec_()

'''
    TESTCASE = 1

    app = QtGui.QApplication(sys.argv)
    form = QtGui.QDialog()
    form.setFixedSize(180,200)
    #form.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)

    if TESTCASE==100:
        dispatcherwidget = Dispatcher(parent=form,connectnow=False)
    elif TESTCASE==101:
        dispatcherwidget = Dispatcher(parent=form,host='soul')
        #        Ci  Co  Li  Lo  Ri  Ro  Tout  t  CONTo TRIGo
        mat = [ [ 0,  0,  0,  0,  0,  0,  2,  1.2,  0,   0   ] ,\
                [ 1,  1,  1,  1,  1,  1,  1,   0,   0,   0   ] ,\
                [ 3,  3,  0,  0,  0,  0,  3,   4,   1,   0   ] ,\
                [ 2,  2,  0,  0,  0,  0,  2,   4,   2,   0   ] ]
        mat = np.array(mat)
        dispatcherwidget.setStateMatrix(mat)

    form.show()
    app.exec_()
    
    # FIXME: maybe this way is better
    #sys.exit(app.exec_())
'''

