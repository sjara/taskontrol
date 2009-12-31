#!/usr/bin/env python

'''
Example protocol.
Protocol as a controller of other modules.

'''

__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-15'


import sys
sys.path.append('../')
import time
from PyQt4 import QtCore 
from PyQt4 import QtGui 
import numpy as np
import paramgui
import dispatcher
import statematrix
import rigsettings
import savedata
import messenger

reload(paramgui)
reload(dispatcher)
reload(statematrix)
reload(rigsettings)
reload(savedata)
reload(messenger)

import eventsplot
reload(eventsplot)


class Protocol(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Protocol, self).__init__(parent)

        # -- Read settings --
        smhost = rigsettings.STATE_MACHINE_SERVER

        # -- Add widgets --
        centralWidget = QtGui.QWidget()
        self.dispatcher = dispatcher.Dispatcher(host=smhost,interval=0.3,connectnow=True)
        self.savedata = savedata.SaveData()
        self.params = paramgui.Container()
        for ind in range(6):
            self.params['par%d'%ind] = paramgui.NumericParam('Param%d'%ind,value=1.1*ind)
        self.params['par%d'%(ind+1)] = paramgui.MenuParam('MenuParam',('One','Two','Three'))
        self.evplot = eventsplot.EventsPlot(xlim=[0,4])

        layoutMain = QtGui.QVBoxLayout()
        layoutTop = QtGui.QVBoxLayout()
        layoutBottom = QtGui.QHBoxLayout()
        layoutCol0 = QtGui.QVBoxLayout()
        layoutCol1 = QtGui.QVBoxLayout()
        layoutCol2 = QtGui.QVBoxLayout()
        groupBox1 = QtGui.QGroupBox('Group 1')
        layoutBox1 = QtGui.QVBoxLayout()

        layoutMain.addLayout(layoutTop)
        layoutMain.addStretch()
        layoutMain.addLayout(layoutBottom)

        layoutTop.addWidget(self.evplot)
        layoutBottom.addLayout(layoutCol0)
        layoutBottom.addLayout(layoutCol1)
        layoutBottom.addLayout(layoutCol2)
        #layoutBottom.setStretch(0,1)
        #layoutBottom.setStretch(1,0)

        layoutCol0.addWidget(self.savedata)
        layoutCol0.addWidget(self.dispatcher)
        #layoutCol2.addStretch()
        layoutCol2.addWidget(groupBox1)
        groupBox1.setLayout(layoutBox1)
        for param in self.params.values():
            layoutBox1.addWidget(param)
        centralWidget.setLayout(layoutMain)
        self.setCentralWidget(centralWidget)

        # --- Create state matrix ---
        self.sm = statematrix.StateMatrix(readystate=('ready_next_trial',1))
        self.setStateMatrix()

        # -- Setup events plot --
        #self.evplot.setStatesColor(np.random.rand(6))
        '''
        statesColor = [ [255,0,0],[0,255,0],[0,0,255],\
                        [255,255,0],[255,0,255],[0,255,255] ]  
        self.evplot.setStatesColor(statesColor)
        '''
        statesColorDict = {'wait_for_cpoke': [127,127,255],
                           'play_target':    [255,255,0],
                           'wait_for_apoke': [191,191,255],
                           'reward':         [0,255,0],
                           'punish':         [255,0,0],
                           'ready_next_trial':   [0,0,0]}
        self.evplot.setStatesColor(statesColorDict,self.sm.getStatesDict())


        # -- Connect signals from dispatcher --
        self.connect(self.dispatcher,QtCore.SIGNAL('PrepareNextTrial'),self.prepareNextTrial)
        self.connect(self.dispatcher,QtCore.SIGNAL('StartNewTrial'),self.startNewTrial)
        self.connect(self.dispatcher,QtCore.SIGNAL('TimerTic'),self.timerTic)

        self.connect(self.savedata.buttonSaveData,QtCore.SIGNAL('clicked()'),self.fileSave)

        # -- Connect messenger --
        self.mymess = messenger.Messenger()
        self.connect(self.mymess.emitter,QtCore.SIGNAL('NewMessage'),self.showMessage)
        self.mymess.send('Created window')


    def setStateMatrix(self):
        # -- Set state matrix --
        tmin = 0.001            # Very small time
        Sdur = 0.2              # Duration of sound
        RewAvail = 4            # Length of time reward is available
        Rdur = 0.1              # Duration of reward
        Lw = rigsettings.LEFT_WATER  # Left water valve
        Rw = rigsettings.RIGHT_WATER # Right water valve
        #Corr =  
        #Err  =
        
        self.sm.addState(name='wait_for_cpoke', selftimer=4,
                    transitions={'Cin':'play_target'})
        self.sm.addState(name='play_target', selftimer=Sdur,
                    transitions={'Cout':'wait_for_apoke','Tout':'wait_for_apoke'},
                    actions={'DOut':7})
        self.sm.addState(name='wait_for_apoke', selftimer=RewAvail,
                    transitions={'Lin':'reward','Rin':'punish','Tout':'ready_next_trial'})
        self.sm.addState(name='reward', selftimer=Rdur,
                    transitions={'Tout':'ready_next_trial'},
                    actions={'DOut':2})
        self.sm.addState(name='punish', selftimer=Rdur,
                    transitions={'Tout':'ready_next_trial'},
                    actions={'DOut':4})

        #prepareNextTrialStates = ('ready_next_trial','reward','punish')
        prepareNextTrialStates = ('ready_next_trial')
        self.dispatcher.setPrepareNextTrialStates(prepareNextTrialStates,
                                                  self.sm.getStatesDict())
        self.dispatcher.setStateMatrix(self.sm.getMatrix())

        # QUESTION: what happens if signal 'READY TO START TRIAL'
        #           is sent while on JumpState?
        #           does it jump to new trial or waits for timeout?

        print self.sm
        

    def fileSave(self):
        '''Triggered by button clicked signal'''
        self.savedata.fileSave(self.params)

    def showMessage(self,msg):
        #print msg
        self.statusBar().showMessage(str(msg))

    def prepareNextTrial(self, nextTrial):
        print 'Prepare trial %d'%nextTrial
        self.dispatcher.readyToStartTrial()


    def startNewTrial(self, currentTrial):
        print 'Started trial %d'%currentTrial


    def timerTic(self,etime,lastEvents):
        #timesAndStates = lastEvents[:,[2,3]]
        #timesAndStates[:,0] -= etime
        # FIXME: I should not access attribute of dispatcher directly
        timesAndStates = self.dispatcher.eventsMat[:,[2,3]]
        # FIXME: next line maybe the first place where a copy is made:
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


    '''   THIS DOES NOT WORK
    try:
        app.exec_()
    except TypeError, ValueError:        
        print '****************** EXCEPT ********************'
    finally:
        print '****************** FINALLY ********************'
        protocol.dispatcher.stop()
    '''
    #protocol.dispatcher.stop()
    #raise

