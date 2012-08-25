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
from taskontrol.core import messenger
#from taskontrol.core import smclient

#reload(smclient)


class Dispatcher(QtCore.QObject):
    '''
    Dispatcher is the trial controller. It is an interface between a
    trial-structured protocol and the state machine.
    '''
    # -- Create signals (they need to be before constructor) --
    timerTic = QtCore.Signal(float)
        
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
            self.connectSM()  # Connect to SM and set self.isConnected to True

        # -- Create state machine variables --
        self.time = 0.0         # Time on the state machine
        self.state = 0          # State of the state machine
        self.eventCount = 0     # Number of events so far
        self.currentTrial = 1   # Current trial
        self.lastEvents = np.array([])   # Matrix with info about last events
        self.eventsMat = np.empty((0,3)) # Matrix with info about all events

        # -- Create timer --
        self.interval = interval # Polling interval (sec)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.timeout)

    def connectSM(self):
        '''Connect to state machine server and initialize it.'''
        self.statemachine.connect()
        #self.statemachine.initialize()
        self.isConnected = True

    def timeout(self):
        #self.emit(QtCore.SIGNAL('TimerTic'), self.time, self.lastEvents)
        import datetime
        self.time = datetime.datetime.now().second  ######## DEBUG ##########
        self.timerTic.emit(self.time)
        print 'toc'

    def start(self):
        # --- Start timer ---
        self.timer.start(1e3*self.interval) # timer takes interval in ms
        # -- Start state machine --
        if self.isConnected:
            self.statemachine.run()
        else:
            print 'The dispatcher is not connected to the state machine server.'
        # -- Change button appearance --
        ###  DO THIS IN DispatcherGUI


BUTTON_COLORS = {'start':'limegreen','stop':'red'}

class DispatcherGUI(QtGui.QGroupBox):
    def __init__(self, parent=None, minwidth=200, dummy=False):
        super(DispatcherGUI, self).__init__(parent)

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

        #self.stop()

    @QtCore.Slot(float)
    def updateGUI(self,serverTime):
        '''Update display of time and events.'''
        self.timeLabel.setText(self._timeFormat%serverTime)
        #self.stateLabel.setText(self._stateFormat%self.state)
        #self.eventCountLabel.setText(self._eventCountFormat%self.eventCount)
        #self.currentTrialLabel.setText(self._currentTrialFormat%self.currentTrial)

        #@QtCore.Slot(str)



class oldDispatcher(QtGui.QGroupBox):
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
                 connectnow=True, interval=0.3, minwidth=200, dummy=False):
        super(Dispatcher, self).__init__(parent)

        # -- Use dummy state machine if requested (DOES NOT SEEM TO WORK) --
        if dummy:
            from taskontrol.plugins import smdummy as smclient
        else:
            from taskontrol.core import smclient
        reload(smclient)

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
        self.statemachine = smclient.StateMachineClient(self.host,self.port,
                                                        connectnow=False)
        if connectnow:
            self.connectSM()  # Connect to SM and set self.isConnected to True

        # -- Create state machine variables --
        self.time = 0.0         # Time on the state machine
        self.state = 0          # State of the state machine
        self.eventCount = 0     # Number of events so far
        self.currentTrial = 1   # Current trial
        self.lastEvents = np.array([])   # Matrix with info about last events
        self.eventsMat = np.empty((0,5)) # Matrix with info about all events
        # FIXME: is it really 5 columns?

        # -- Create timer --
        self.interval = interval # Pooling interval (sec)
        self.timer = QtCore.QTimer(self)
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)

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
        self.connect(self.buttonStartStop, QtCore.SIGNAL("clicked()"),
                     self.startOrStop)

        self.stop()


    def connectSM(self):
        '''Connect to state machine server and initialize it.'''
        self.statemachine.connect()
        self.statemachine.initialize()
        # FIXME: connect to sound server
        self.isConnected = True


    def setStateMatrix(self,statesmatrix,schedwavesmatrix=None):
        '''
        Send state transition matrix to server.
        If available, also send matrix of schedule waves.

        The matrices can be python arrays or a numpy arrays.
        '''
        if self.isConnected:
            #if not isinstance(statesmatrix,np.ndarray):
            #    statesmatrix = np.array(statesmatrix)
            if schedwavesmatrix:
                self.statemachine.setScheduledWavesDIO(schedwavesmatrix)        
            self.statemachine.setStateMatrix(statesmatrix)        
        else:
            print 'Call to setStateMatrix, but the client is not connected.\n'


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
        messenger.Messenger.send('Run')


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
        messenger.Messenger.send('Stop')


    def closeEvent(self, event):
        # FIXME: When the window is closed, Dispatcher.closeEvent is not called!
        self.die()
        event.accept()


    def die(self):
        '''Make sure timer stops when user closes the dispatcher.'''
        self.stop()
        if self.isConnected:
            self.statemachine.bypassDout(0)
            try:
                self.statemachine.forceState(0)
            except smclient.baseclient.AckError:
                print 'WARNING! could not force state 0 (maybe no state matrix loaded).'
            #except smclient.baseclient.AckError as e:
            #    print e.msg+'\nMaybe there was no state matrix loaded.'
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


    def setPrepareNextTrialStatesFromIndices(self,statesIndsList):
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
        # -- Needed for Ctrl-C (otherwise you need to kill with Ctrl-\ 
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        app = QtGui.QApplication(sys.argv)
        form = QtGui.QDialog()
        form.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        dispatcherModel = Dispatcher(parent=form,connectnow=False)
        dispatcherView = DispatcherGUI(parent=form)
        dispatcherModel.timerTic.connect(dispatcherView.updateGUI)
        dispatcherModel.start()
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

