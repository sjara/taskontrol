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

TODO:
* When the form is destroyed, dispatcher.closeEvent is not called!
'''


__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-11'

import sys
from PyQt4 import QtCore 
from PyQt4 import QtGui 
import smclient

BUTTON_COLORS = {'start':'green','stop':'red'}

class Dispatcher(QtGui.QWidget):
    '''
    Dispatcher graphical widget: Interface with state machine.
    
    This widget allows querying the state machine about time, state
    and events. It also sets the trial structure of the protocol.
    '''
    def __init__(self, parent=None, host='localhost', port=3333, connectnow=True):
        super(Dispatcher, self).__init__(parent)

        # -- Create a state machine client --
        self.host = host
        self.port = port
        self.isConnected = False
        self.statemachine = smclient.StateMachineClient(self.host,self.port,\
                                                        connectnow=False)
        if connectnow:
            self.connectToSM()  # Connect and set self.isConnected to True

        self.mat = []

        # -- Create timer --
        self.interval = 300
        self.time = 0.0         # Time on the state machine
        self.state = 0          # State of the state machine
        self.timer = QtCore.QTimer(self)
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)

        # -- Create graphical objects --
        #self.resize(400,300)
        self.stateLabel = QtGui.QLabel("State: %d"%self.state)
        self.timeLabel = QtGui.QLabel("Time: %0.2f"%self.time)
        self.buttonStartStop = QtGui.QPushButton("&Push")
        #self.buttonStartStop.setMinimumSize(200,100)
        self.buttonStartStop.setMinimumHeight(100)
        buttonFont = QtGui.QFont(self.buttonStartStop.font())
        buttonFont.setPointSize(buttonFont.pointSize()+10)
        self.buttonStartStop.setFont(buttonFont)

        # -- Create layouts --
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.stateLabel)
        layout.addWidget(self.timeLabel)
        layout.addWidget(self.buttonStartStop)
        self.setLayout(layout)

        # -- Connect signals --
        self.connect(self.buttonStartStop, QtCore.SIGNAL("clicked()"),
                     self.startOrStop)

        self.stop()


    def connectToSM(self):
        self.statemachine.connect()
        self.isConnected = True


    def timeout(self):
        self.queryStateMachine()
        

    def queryStateMachine(self):
        if self.isConnected:
            self.time = self.statemachine.getTime()
        self.timeLabel.setText("Time: %0.2f"%self.time)


    def startOrStop(self):
        '''Toggle (start or stop) state machine and dispatcher timer.'''
        if(self.timer.isActive()):
            self.stop()
        else:
            self.start()


    def start(self):
        '''Start timer.'''
        self.timer.start(self.interval)
        # -- Start state machine --
        if self.isConnected:
            self.statemachine.initialize()
            self.statemachine.setStateMatrix(self.mat)        
            self.statemachine.run()
        else:
            print 'The dispatcher is not connected to the state machine server.'            
        # -- Change button appearance --
        stylestr = 'QWidget { background-color: %s }'%BUTTON_COLORS['stop']
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
        '''Make sure timer stops when user closes the dispatcher.'''
        # FIXME: When the window is closed, Dispatcher.closeEvent is not called!
        self.stop()
        print 'Enter closeEvent'
        if self.isConnected:
            print 'And is was connected'
            self.statemachine.close()
        event.accept()

'''
        #============= EXTRA CODE ==============#
        #self.buttonStartStop.
        #QtGui.QColor(QtCore.Qt.green)
        #p.setColor(QColorGroup.Base,QtGui.QColor(QtCore.Qt.green))
'''   


def center(guiObj):
    '''Place in the center of the screen (NOT TESTED YET)'''
    screen = QtGui.QDesktopWidget().screenGeometry()
    size =  guiObj.geometry()
    guiObj.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)


if __name__ == "__main__":

    TESTCASE = 2

    app = QtGui.QApplication(sys.argv)
    form = QtGui.QDialog()
    form.setFixedSize(180,200)
    #form.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)

    if TESTCASE==1:
        dispatcherwidget = Dispatcher(parent=form,connectnow=False)
    elif TESTCASE==2:
        dispatcherwidget = Dispatcher(parent=form,host='soul')
        mat = [ [ 0,  0,  0,  0,  0,  0,  2,  1.2,  0,   0       ] ,\
                [ 1,  1,  1,  1,  1,  1,  1,   0,   0,   0       ] ,\
                [ 3,  3,  0,  0,  0,  0,  3,   4,   1,   0       ] ,\
                [ 2,  2,  0,  0,  0,  0,  2,   4,   2,   0       ] ]

    form.show()
    app.exec_()
    
    # FIXME: maybe this way is better
    #sys.exit(app.exec_())

