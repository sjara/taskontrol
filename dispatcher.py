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
'''


__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-11'

import sys
from PyQt4 import QtCore 
from PyQt4 import QtGui 

class Dispatcher(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Dispatcher, self).__init__(parent)

        self.__buttonColors = {'start':'green','stop':'red'}
        # -- Create timer --
        self.interval = 1000
        self.counter = 0
        self.timer = QtCore.QTimer(self)
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)

        # -- Create graphical objects --
        #self.resize(400,300)
        self.timeLabel = QtGui.QLabel("Time: %d"%self.counter)
        self.buttonStartStop = QtGui.QPushButton("&Push")
        self.buttonStartStop.setMinimumSize(200,100)
        buttonFont = QtGui.QFont(self.buttonStartStop.font())
        buttonFont.setPointSize(buttonFont.pointSize()+10)
        self.buttonStartStop.setFont(buttonFont)

        # -- Create layouts --
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.timeLabel)
        layout.addWidget(self.buttonStartStop)
        self.setLayout(layout)

        # -- Connect signals --
        self.connect(self.buttonStartStop, QtCore.SIGNAL("clicked()"),
                     self.startOrStop)

        self.stopTimer()


    def timeout(self):
        self.queryStateMachine()
        

    def queryStateMachine(self):
        self.counter +=1
        print self.counter
        self.timeLabel.setText("Time: %d"%self.counter)


    def startOrStop(self):
        if(self.timer.isActive()):
            self.stopTimer()
        else:
            self.startTimer()


    def startTimer(self):
        '''Stop timer.'''
        self.timer.start(self.interval)
        stylestr = 'QWidget { background-color: %s }'%self.__buttonColors['stop']
        self.buttonStartStop.setStyleSheet(stylestr)
        self.buttonStartStop.setText('Stop')


    def stopTimer(self):
        '''Stop timer.'''
        self.timer.stop()
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
        self.stopTimer()
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

