#!/usr/bin/env python

'''
This example shows how to use extra-timers with the statematrix module.

The time for each extra-timer is created before the state matrix.
Then, one can set which state will trigger the start of the timer.
When the extra-timer is up, it will generate an event that can be used in any state.
'''

__author__ = 'Santiago Jaramillo <sjara@uoregon.edu>'


import sys
from PySide import QtCore 
from PySide import QtGui 
from taskontrol.settings import rigsettings
from taskontrol.core import dispatcher
from taskontrol.core import statematrix
from taskontrol.core import paramgui
import signal


class Paradigm(QtGui.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(Paradigm, self).__init__(parent)

        # -- Read settings --
        smServerType = rigsettings.STATE_MACHINE_TYPE

        # -- Create dispatcher --
        self.dispatcherModel = dispatcher.Dispatcher(serverType=smServerType,interval=0.1)
        self.dispatcherView = dispatcher.DispatcherGUI(model=self.dispatcherModel)

        # -- Add parameters --
        self.params = paramgui.Container()
        self.params['periodOn'] = paramgui.NumericParam('Period On',value=0.2,
                                                        group='Timing Parameters')
        self.params['periodOff'] = paramgui.NumericParam('Period Off',value=0.2,
                                                         group='Timing Parameters')
        self.params['trainOn'] = paramgui.NumericParam('Train On',value=2,
                                                         group='Timing Parameters')
        self.params['trainOff'] = paramgui.NumericParam('Train Off',value=1,
                                                         group='Timing Parameters')
        timingParams = self.params.layout_group('Timing Parameters')

        # -- Add graphical widgets to main window --
        centralWidget = QtGui.QWidget()
        layoutMain = QtGui.QHBoxLayout()
        layoutMain.addWidget(self.dispatcherView)
        layoutOneColumn = QtGui.QVBoxLayout()
        layoutOneColumn.addWidget(timingParams)
        layoutOneColumn.addStretch()
        layoutMain.addLayout(layoutOneColumn)
        centralWidget.setLayout(layoutMain)
        self.setCentralWidget(centralWidget)

        # -- Center in screen --
        paramgui.center_in_screen(self)

        # -- Connect signals from dispatcher --
        self.dispatcherModel.prepareNextTrial.connect(self.prepare_next_trial)
        self.dispatcherModel.timerTic.connect(self.timer_tic)

        self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                          outputs=rigsettings.OUTPUTS,
                                          readystate='ready_next_trial',
                                          extratimers=['trainTimer'])

    def set_state_matrix(self):
        self.sm.reset_transitions()

        pulseTimeOn = self.params['periodOn'].get_value()
        pulseTimeOff = self.params['periodOff'].get_value()
        trainOn = self.params['trainOn'].get_value()
        trainOff = self.params['trainOff'].get_value()

        # -- Set extra timers --
        self.sm.set_extratimer('trainTimer', duration=trainOn)
        
        # -- Set state matrix --
        self.sm.add_state(name='start', statetimer=0,
                          transitions={'Tup':'pulse_on'},
                          trigger=['trainTimer'])
        self.sm.add_state(name='pulse_on', statetimer=pulseTimeOn,
                          transitions={'Tup':'pulse_off','trainTimer':'end_train'},
                          outputsOn=['centerLED'])
        self.sm.add_state(name='pulse_off', statetimer=pulseTimeOff,
                          transitions={'Tup':'pulse_on','trainTimer':'end_train'},
                          outputsOff=['centerLED'])
        self.sm.add_state(name='end_train', statetimer=trainOff,
                          transitions={'Tup':'ready_next_trial'},
                          outputsOff=['centerLED'])
        print self.sm

        self.dispatcherModel.set_state_matrix(self.sm)


    def prepare_next_trial(self, nextTrial):
        print '\nPrepare trial %d'%nextTrial
        self.set_state_matrix()
        # -- Show results from previous trial --
        lastEvents = self.dispatcherModel.eventsMat[-14:-1]
        print 'Last 14 events:'
        for oneEvent in lastEvents:
            print '%0.3f\t %d\t %d'%(oneEvent[0],oneEvent[1],oneEvent[2])
        self.dispatcherModel.ready_to_start_trial()


    def start_new_trial(self, currentTrial):
        print '\n======== Started trial %d ======== '%currentTrial


    def timer_tic(self,etime,lastEvents):
        print '.',
        sys.stdout.flush() # Force printing on the screen at this point


    def closeEvent(self, event):
        '''
        Executed when closing the main window.
        This method is inherited from QtGui.QMainWindow, which explains
        its camelCase naming.
        '''
        self.dispatcherModel.die()
        event.accept()


if __name__ == '__main__':
    (app,paradigm) = paramgui.create_app(Paradigm)

