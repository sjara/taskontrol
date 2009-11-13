#!/usr/bin/env python

'''
Dispatcher for behavioral protocols running on the RT-Linux state machine.

It is meant to be the interface between a trial-structured protocol
and the state machine. It will for example halt the state machine
until the next trial has been prepared and ready to start.

NOTES:
- Should I implement it with QThread instead?
- If running on Windows I may need to change name to *.pyw
- Does the time keep going even if close the window?
- Crashing should be graceful (for example close connection to statemachine)
'''


__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-11'

import sys
from PyQt4 import QtCore 
from PyQt4 import QtGui 
import smclient

class Dispatcher(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Dispatcher, self).__init__(parent)

        self.__buttonColors = {'start':'green','stop':'red'}

        # -- Create a state machine client --
        self.host = 'soul'
        self.port = 3333
        self.statemachine = smclient.StateMachineClient(self.host,self.port)

        self.mat = [ [ 0,  0,  0,  0,  0,  0,  2,  1.2,  0,   0       ] ,\
                [ 1,  1,  1,  1,  1,  1,  1,   0,   0,   0       ] ,\
                [ 3,  3,  0,  0,  0,  0,  3,   4,   1,   0       ] ,\
                [ 2,  2,  0,  0,  0,  0,  2,   4,   2,   0       ] ]


        # -- Create timer --
        self.interval = 300
        self.time = 0.0         # Time on the state machine
        self.state = 0          # State of the state machine
        self.timer = QtCore.QTimer(self)
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)

        # -- Create graphical objects --
        #self.resize(400,300)
        self.stateLabel = QtGui.QLabel("State: %d"%self.state)
        self.timeLabel = QtGui.QLabel("Time: %d"%self.time)
        self.buttonStartStop = QtGui.QPushButton("&Push")
        self.buttonStartStop.setMinimumSize(200,100)
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


    def timeout(self):
        self.queryStateMachine()
        

    def queryStateMachine(self):
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
        self.statemachine.initialize()
        self.statemachine.setStateMatrix(self.mat)        
        self.statemachine.run()
        # -- Change button appearance --
        stylestr = 'QWidget { background-color: %s }'%self.__buttonColors['stop']
        self.buttonStartStop.setStyleSheet(stylestr)
        self.buttonStartStop.setText('Stop')


    def stop(self):
        '''Stop timer.'''
        self.timer.stop()
        # -- Start state machine --
        self.statemachine.halt()
        # -- Change button appearance --
        stylestr = 'QWidget { background-color: %s }'%self.__buttonColors['start']
        self.buttonStartStop.setStyleSheet(stylestr)
        self.buttonStartStop.setText('Start')


    def center(self):
        '''Place in the center of the screen (NOT TESTED YET)'''
        screen = QtGui.QDesktopWidget().screenGeometry()
        size =  self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)


    def closeEvent(self, event):
        '''Make sure timer stops when user closes the dispatcher.'''
        self.stop()
        self.statemachine.close()
        event.accept()

'''
        #============= EXTRA CODE ==============#
        #self.buttonStartStop.
        #QtGui.QColor(QtCore.Qt.green)
        #p.setColor(QColorGroup.Base,QtGui.QColor(QtCore.Qt.green))
'''   


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    form = Dispatcher()
    form.show()
    app.exec_()
    
    # FIXME: maybe this way is better
    #sys.exit(app.exec_())

