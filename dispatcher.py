#!/usr/bin/env python

'''
Dispatcher for behavioral protocols running on the RT-Linux state machine.

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


__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-11'

import sys
from PyQt4 import QtCore 
from PyQt4 import QtGui 
import numpy as np
import smclient

BUTTON_COLORS = {'start':'limegreen','stop':'red'}

class Dispatcher(QtGui.QGroupBox):
    '''
    Dispatcher graphical widget: Interface with state machine.
    
    This widget allows querying the state machine about time, state
    and events. It also sets the trial structure of the protocol.

    It emits the following signals:
    - 'PrepareNextTrial': whenever one of the prepare-next-trial-states is reached.
                          It sends: 'nextTrial'
    - 'StartNewTrial'   : whenever READY TO START TRIAL is sent to state machine.
                          It sends: 'currentTrial'
    - 'TimerTic'        : at every tic of the dispatcher timer.
                          It sends: 'time','lastEvents'
    '''
    def __init__(self, parent=None, host='localhost', port=3333,
                 connectnow=True, interval=0.3):
        super(Dispatcher, self).__init__(parent)

        # -- Set string formats --
        self._timeFormat = 'Time: %0.1f s'
        self._stateFormat = 'State: %d'
        self._eventCountFormat = 'N events: %d'
        self._currentTrialFormat = 'Current trial: %d'

        # -- Set trial structure variables --
        self.prepareNextTrialStates = []
        self.preparingNextTrial = False      # True while preparing next trial

        # -- Create a state machine client --
        self.host = host
        self.port = port
        self.isConnected = False
        self.statemachine = smclient.StateMachineClient(self.host,self.port,\
                                                        connectnow=False)
        if connectnow:
            self.connectSM()  # Connect to SM and set self.isConnected to True

        # -- Create state machine variables --
        self.time = 0.0         # Time on the state machine
        self.state = 0          # State of the state machine
        self.eventCount = 0     # Number of events so far
        self.currentTrial = 1   # Current trial
        self.lastEvents = np.array([])   # Matrix with info about last events
        self.eventsMat = np.zeros((0,5)) # Matrix with info about all events

        # -- Create timer --
        self.interval = interval # Pooling interval (sec)
        self.timer = QtCore.QTimer(self)
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)

        # -- Create graphical objects --
        self.stateLabel = QtGui.QLabel(self._stateFormat%self.state)
        self.timeLabel = QtGui.QLabel(self._timeFormat%self.time)
        self.eventCountLabel = QtGui.QLabel(self._eventCountFormat%self.time)
        self.currentTrialLabel = QtGui.QLabel(self._currentTrialFormat%self.currentTrial)
        self.buttonStartStop = QtGui.QPushButton("&Push")
        self.buttonStartStop.setMinimumHeight(100)
        buttonFont = QtGui.QFont(self.buttonStartStop.font())
        buttonFont.setPointSize(buttonFont.pointSize()+10)
        self.buttonStartStop.setFont(buttonFont)

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
        self.connect(self.buttonStartStop, QtCore.SIGNAL("clicked()"),
                     self.startOrStop)

        self.stop()


    def connectSM(self):
        '''Connect to state machine server and initialize it.'''
        self.statemachine.connect()
        self.statemachine.initialize()
        # FIXME: connect to sound server
        self.isConnected = True


    def setStateMatrix(self,statematrix):
        '''
        Send state transition matrix to server.

        The matrix can be given as a python array or a numpy array.
        '''
        if not isinstance(statematrix,np.ndarray):
            statematrix = np.array(statematrix)
        self.statemachine.setStateMatrix(statematrix)        


    def timeout(self):
        '''This method is called at every tic of the clock.'''
        self.queryStateMachine()
        self.emit(QtCore.SIGNAL('TimerTic'), self.time, self.lastEvents)
        # -- Check if one of the PrepareNextTrialStates has been reached --
        if self.lastEvents.size>0 and not self.preparingNextTrial:
            laststates = self.lastEvents[:,3]
            for state in self.prepareNextTrialStates:
                if state in laststates:
                    self.preparingNextTrial = True
                    self.emit(QtCore.SIGNAL('PrepareNextTrial'), self.currentTrial+1)
                    break


    def readyToStartTrial(self):
        '''
        Tell the state machine the it can jump to state 0 and start new trial.
        '''
        self.statemachine.readyToStartTrial()
        self.currentTrial += 1
        self.preparingNextTrial = False
        self.emit(QtCore.SIGNAL('StartNewTrial'), self.currentTrial)


    def queryStateMachine(self):
        '''Request events information to the state machine'''
        if self.isConnected:
            resultsDict = self.statemachine.getTimeEventsAndState(self.eventCount+1)
            self.time = resultsDict['etime']
            self.state = resultsDict['state']
            self.eventCount = resultsDict['eventcount']
            self.lastEvents = resultsDict['events']
            self._updateGUI()
            self._updateEventsMat()


    def _updateEventsMat(self):
        '''Concatenate last events to matrix of all events.'''
        self.eventsMat = np.vstack((self.eventsMat,self.lastEvents))


    def _updateGUI(self):
        '''Update display of time and events.'''
        self.timeLabel.setText(self._timeFormat%self.time)
        self.stateLabel.setText(self._stateFormat%self.state)
        self.eventCountLabel.setText(self._eventCountFormat%self.eventCount)
        self.currentTrialLabel.setText(self._currentTrialFormat%self.currentTrial)


    def startOrStop(self):
        '''Toggle (start or stop) state machine and dispatcher timer.'''
        if(self.timer.isActive()):
            self.stop()
        else:
            self.start()


    def start(self):
        '''Start timer.'''
        self.timer.start(1e3*self.interval) # timer takes interval in ms
        # -- Start state machine --
        if self.isConnected:
            self.statemachine.run()
        else:
            print 'The dispatcher is not connected to the state machine server.'
        # -- Change button appearance --
        stylestr = 'QWidget {background-color: %s}'%BUTTON_COLORS['stop']
        self.buttonStartStop.setStyleSheet(stylestr)
        self.buttonStartStop.setText('Stop')


    def stop(self):
        '''Stop timer.'''
        self.timer.stop()
        # -- Start state machine --
        if self.isConnected:
            self.statemachine.halt()
        else:
            print 'The dispatcher is not connected to the state machine server.'
        # -- Change button appearance --
        stylestr = 'QWidget { background-color: %s }'%BUTTON_COLORS['start']
        self.buttonStartStop.setStyleSheet(stylestr)
        self.buttonStartStop.setText('Start')


    def closeEvent(self, event):
        # FIXME: When the window is closed, Dispatcher.closeEvent is not called!
        self.die()
        event.accept()


    def die(self):
        '''Make sure timer stops when user closes the dispatcher.'''
        self.stop()
        if self.isConnected:
            try:
                self.statemachine.forceState(0)
            except smclient.baseclient.AckError as e:
                print e.msg+'\nMaybe there was no state matrix loaded.'
            self.statemachine.close()


    def setPrepareNextTrialStates(self,statesNamesList,statesNamesDict):
        '''
        Set states where next trial can start to be prepared.
        States are given as a list of names, and a dict that maps names to indices.
        '''
        if not isinstance(statesNamesList,(tuple,list)):
            statesNamesList = [statesNamesList]
        statesIndsList = []
        for stateName in statesNamesList:
            statesIndsList.append(statesNamesDict[stateName])
        self.prepareNextTrialStates = statesIndsList


    def setPrepareNextTrialStatesFromIndices(self,statesIndsList=[]):
        '''
        Set states where next trial can start to be prepared.
        Here, states are specified by their indices instead of their names.
        '''
        # FIXME: is this ever used
        self.prepareNextTrialStates = statesIndsList


    #--- End of Dispatcher class ---


def center(guiObj):
    '''Place in the center of the screen (NOT TESTED YET)'''
    screen = QtGui.QDesktopWidget().screenGeometry()
    size =  guiObj.geometry()
    guiObj.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)


if __name__ == "__main__":

    TESTCASE = 1

    app = QtGui.QApplication(sys.argv)
    form = QtGui.QDialog()
    form.setFixedSize(180,200)
    #form.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)

    if TESTCASE==1:
        dispatcherwidget = Dispatcher(parent=form,connectnow=False)
    elif TESTCASE==2:
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

