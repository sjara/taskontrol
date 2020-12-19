#!/usr/bin/env python
"""
This example shows a simple paradigm organized by trials (using dispatcher)
and how to use the statematrix module to assemble the matrix easily.
"""

import sys
from qtpy import QtWidgets
from taskontrol import rigsettings
from taskontrol import dispatcher
from taskontrol import statematrix
import signal


class Paradigm(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Paradigm, self).__init__(parent)

        # -- Read settings --
        smServerType = rigsettings.STATE_MACHINE_TYPE

        # -- Create dispatcher --
        self.dispatcherModel = dispatcher.Dispatcher(serverType=smServerType, interval=0.3)
        self.dispatcherView = dispatcher.DispatcherGUI(model=self.dispatcherModel)

        # -- Add graphical widgets to main window --
        centralWidget = QtWidgets.QWidget()
        layoutMain = QtWidgets.QVBoxLayout()
        layoutMain.addWidget(self.dispatcherView)
        centralWidget.setLayout(layoutMain)
        self.setCentralWidget(centralWidget)

        # --- Create state matrix ---
        self.set_state_matrix()

        # -- Connect signals from dispatcher --
        self.dispatcherModel.prepareNextTrial.connect(self.prepare_next_trial)
        self.dispatcherModel.timerTic.connect(self.timer_tic)

    def set_state_matrix(self):
        self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                          outputs=rigsettings.OUTPUTS,
                                          readystate='ready_next_trial')

        # -- Set state matrix --
        self.sm.add_state(name='first_state', statetimer=1.0,
                          transitions={'Cin':'second_state', 'Tup':'second_state'},
                          outputsOn=['centerLED'])
        self.sm.add_state(name='second_state', statetimer=2.0,
                          transitions={'Lin':'first_state', 'Tup':'ready_next_trial'},
                          outputsOff=['centerLED'])
        print(self.sm)

        self.dispatcherModel.set_state_matrix(self.sm)

    def prepare_next_trial(self, nextTrial):
        print('\nPrepare trial {}'.format(nextTrial))
        lastTenEvents = self.dispatcherModel.eventsMat[-10:-1]
        print('Last 10 events:')
        for oneEvent in lastTenEvents:
            print('{:.3f}\t {:.0f}\t {:.0f}'.format(oneEvent[0], oneEvent[1], oneEvent[2]))
        self.dispatcherModel.ready_to_start_trial()

    def timer_tic(self, etime, lastEvents):
        print('.', end='', flush=True)

    def closeEvent(self, event):
        """
        Executed when closing the main window. This method is inherited
        from QtWidgets.QMainWindow, which explains its camelCase name.
        """
        self.dispatcherModel.die()
        event.accept()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Enable Ctrl-C
    app = QtWidgets.QApplication(sys.argv)
    paradigm = Paradigm()
    paradigm.show()
    app.exec_()
