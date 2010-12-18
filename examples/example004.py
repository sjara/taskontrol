#!/usr/bin/env python

'''
This example shows a very simple protocol with graphical interface that
makes use of schedule waves.
It is very similar to example003.py, but in addition it uses methods in
'statematrix' to add schedule waves.
'''

__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2010-12-14'

import sys
from PyQt4 import QtCore 
from PyQt4 import QtGui 
from taskontrol.settings import rigsettings
from taskontrol.core import dispatcher
from taskontrol.core import statematrix

reload(statematrix)

class Protocol(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Protocol, self).__init__(parent)

        # -- Read settings --
        smhost = rigsettings.STATE_MACHINE_SERVER

        # -- Create dispatcher --
        self.dispatcher = dispatcher.Dispatcher(host=smhost,interval=0.3)

        # -- Add graphical widgets to main window --
        centralWidget = QtGui.QWidget()
        layoutMain = QtGui.QVBoxLayout()
        layoutMain.addWidget(self.dispatcher)
        centralWidget.setLayout(layoutMain)
        self.setCentralWidget(centralWidget)

        # --- Create state matrix ---
        self.setStateMatrix()

        # -- Connect signals from dispatcher --
        self.connect(self.dispatcher,QtCore.SIGNAL('PrepareNextTrial'),self.prepareNextTrial)
        self.connect(self.dispatcher,QtCore.SIGNAL('StartNewTrial'),self.startNewTrial)
        self.connect(self.dispatcher,QtCore.SIGNAL('TimerTic'),self.timerTic)


    def setStateMatrix(self):
        LeftLED  = rigsettings.DOUT['Left LED']
        RightLED = rigsettings.DOUT['Right LED']

        self.sm = statematrix.StateMatrix(readystate=('ready_next_trial',1))

        self.sm.addScheduleWave(name='firstSW',preamble=0.5,sustain=1.0,DIOline=4)
        self.sm.addScheduleWave(name='secondSW',preamble=1.0,sustain=0.5,DIOline=5)

        # -- Set state matrix --
        self.sm.addState(name='first_state', selftimer=100,
                    transitions={'firstSW_In':'second_state','Tup':'first_state'},
                    actions={'Dout':LeftLED, 'SchedWaveTrig':'firstSW'})
        self.sm.addState(name='second_state', selftimer=100,
                    transitions={'secondSW_Out':'ready_next_trial','Tup':'second_state'},
                    actions={'Dout':RightLED, 'SchedWaveTrig':'secondSW'})

        prepareNextTrialStates = ('ready_next_trial')
        self.dispatcher.setPrepareNextTrialStates(prepareNextTrialStates,
                                                  self.sm.getStatesDict())
        self.dispatcher.setStateMatrix(self.sm.getMatrix(),self.sm.getSchedWaves())


    def prepareNextTrial(self, nextTrial):
        print '\nPrepare trial %d'%nextTrial
        lastTenEvents = self.dispatcher.eventsMat[-10:-1,:]
        print 'Last 10 events:'
        print lastTenEvents
        self.dispatcher.readyToStartTrial()


    def startNewTrial(self, currentTrial):
        print '\n======== Started trial %d ======== '%currentTrial


    def timerTic(self,etime,lastEvents):
        print '.',
        sys.stdout.flush() # Force printing on the screen at this point


    def closeEvent(self, event):
        self.dispatcher.die()
        event.accept()


if __name__ == "__main__":
    QtCore.pyqtRemoveInputHook() # To stop looping if error occurs
    app = QtGui.QApplication(sys.argv)
    protocol = Protocol()
    protocol.show()
    app.exec_()
