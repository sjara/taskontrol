#!/usr/bin/env python

'''
Test protocol to see what is missing.
'''

__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-15'


import sys
from PyQt4 import QtCore 
from PyQt4 import QtGui 
import numpy as np
import paramgui
import dispatcher
import settings

reload(paramgui)
reload(dispatcher)
reload(settings)

import eventsplot
reload(eventsplot)


class Protocol(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Protocol, self).__init__(parent)

        # -- Read settings --
        smhost = settings.STATE_MACHINE_SERVER

        # -- Add widgets --
        self.dispatcher = dispatcher.Dispatcher(host=smhost,connectnow=True)
        self.param1 = paramgui.Parameter('OneParam')
        self.evplot = eventsplot.EventsPlot()

        layout = QtGui.QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.evplot)
        layout.addWidget(self.dispatcher)
        layout.addWidget(self.param1)
        self.setLayout(layout)
        
        # -- Set state matrix --
        tmin = 0.001            # Very small time
        Sdur = 0.1              # Duration of sound
        Tout = 4                # Length of time reward is available
        Rdur = 0.1              # Duration of reward
        Lw = settings.LEFT_WATER  # Left water valve
        Rw = settings.RIGHT_WATER # Right water valve
        #Corr =  
        #Err  =
        mat = []
        #           Ci  Co  Li  Lo  Ri  Ro  Tout  t  CONTo TRIGo
        mat.append([ 0,  0,  0,  0,  0,  0,  2, tmin,  0,   0   ]) # 0: State 0
        mat.append([ 1,  1,  1,  1,  1,  1,  1,   0,   0,   0   ]) # 1: PrepareNextTrial
        mat.append([ 3,  2,  2,  2,  2,  2,  2,   0,   0,   0   ]) # 2: WaitForCpoke
        mat.append([ 3,  3,  3,  3,  3,  3,  4, Sdur,  1,   1   ]) # 3: PlayTarget
        mat.append([ 4,  4,  5,  4,  1,  4,  1, Tout,  0,   0   ]) # 4: WaitForApoke
        mat.append([ 5,  5,  5,  5,  5,  5,  1, Rdur, Lw,   0   ]) # 5: Reward
        mat = np.array(mat)
        self.dispatcher.setPrepareNextTrialStates([1,5])
        self.dispatcher.setStateMatrix(mat)

        # -- Setup events plot --
        #self.evplot.setStatesColor(np.random.rand(6))
        statesColor = [ [255,0,0],[0,255,0],[0,0,255],\
                        [255,255,0],[255,0,255],[0,255,255] ]  
        self.evplot.setStatesColor(statesColor)

        # -- Connect signals from dispatcher --
        self.connect(self.dispatcher,QtCore.SIGNAL('PrepareNextTrial'),self.prepareNextTrial)
        self.connect(self.dispatcher,QtCore.SIGNAL('StartNewTrial'),self.startNewTrial)
        self.connect(self.dispatcher,QtCore.SIGNAL('TimerTic'),self.timerTic)


    def prepareNextTrial(self, nextTrial):
        print 'Prepare trial %d'%nextTrial
        self.dispatcher.readyToStartTrial()
        

    def startNewTrial(self, currentTrial):
        print 'Started trial %d'%currentTrial


    def timerTic(self,etime,lastEvents):
        #timesAndStates = lastEvents[:,[2,3]]
        #timesAndStates[:,0] -= etime
        # FIX: I should not access attribute of dispatcher directly
        timesAndStates = self.dispatcher.eventsMat[:,[2,3]]
        # FIX: next line maybe the first place where a copy is made:
        # It's either inefficient to copy all states, or I'm modifying
        # the original eventsMat which is BAD!
        #timesAndStates[:,0] -= etime
        #print etime
        #print timesAndStates
        self.evplot.updatePlot(timesAndStates, etime)


    def closeEvent(self, event):
        '''Make sure dispatcher stops and closes when closing window.'''
        # FIXME: this feel recursive, I thought the event would come back
        #        to the parent of dispatcher
        self.dispatcher.die()
        event.accept()


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    protocol = Protocol()
    protocol.show()
    app.exec_()
