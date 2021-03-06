#!/usr/bin/env python
"""
This example shows how to add parameters to a paradigm.
The example also shows how to use paramgui.create_app() to run the application,
and how to specify parameters in an external file.

Using and external parameters file:
-----------------------------------
To load parameters values from an external file:
1. The Paradigm class constructor must have paramfile and paramdictname as arguments,
2. The method self.params.from_file() should be called after creating the parameters.
3. You need a parameters file (e.g., params.example.py) containing a dictionary (e.g. test000)

You can then specify the values of parameters from an external file as follows;
  python example005_parameters.py params.example.py test000
"""

from qtpy import QtWidgets
from taskontrol import rigsettings
from taskontrol import dispatcher
from taskontrol import statematrix
from taskontrol import paramgui


class Paradigm(QtWidgets.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(Paradigm, self).__init__(parent)

        # -- Read settings --
        smServerType = rigsettings.STATE_MACHINE_TYPE

        # -- Create dispatcher --
        self.dispatcher = dispatcher.Dispatcher(serverType=smServerType, interval=0.1)

        # -- Add parameters --
        self.params = paramgui.Container()
        self.params['periodOn'] = paramgui.NumericParam('Period On', value=0.5,
                                                        group='Timing Parameters')
        self.params['periodOff'] = paramgui.NumericParam('Period Off', value=1,
                                                         group='Timing Parameters')
        timingParams = self.params.layout_group('Timing Parameters')
        self.params['irrelevant1'] = paramgui.MenuParam('Irrelevant 1',
                                                        ['one_item', 'another_item'],
                                                        value=0, group='Irrelevant')
        self.params['irrelevant2'] = paramgui.StringParam('Irrelevant 2', value='nothing',
                                                          group='Irrelevant')
        irrelevantParams = self.params.layout_group('Irrelevant')

        # -- Load parameters from a file --
        self.params.from_file(paramfile, paramdictname)

        # -- Add graphical widgets to main window --
        centralWidget = QtWidgets.QWidget()
        layoutMain = QtWidgets.QHBoxLayout()
        layoutMain.addWidget(self.dispatcher.widget)
        layoutOneColumn = QtWidgets.QVBoxLayout()
        layoutOneColumn.addWidget(timingParams)
        layoutOneColumn.addWidget(irrelevantParams)
        layoutMain.addLayout(layoutOneColumn)
        centralWidget.setLayout(layoutMain)
        self.setCentralWidget(centralWidget)

        # -- Center on screen --
        paramgui.center_on_screen(self)

        # -- Connect signals from dispatcher --
        self.dispatcher.prepareNextTrial.connect(self.prepare_next_trial)
        self.dispatcher.timerTic.connect(self.timer_tic)

    def set_state_matrix(self):
        self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                          outputs=rigsettings.OUTPUTS,
                                          readystate='ready_next_trial')

        timeOn = self.params['periodOn'].get_value()
        timeOff = self.params['periodOff'].get_value()

        # -- Set state matrix --
        self.sm.add_state(name='first_state', statetimer=timeOn,
                          transitions={'Cin':'second_state', 'Tup':'second_state'},
                          outputsOn=['centerLED'])
        self.sm.add_state(name='second_state', statetimer=timeOff,
                          transitions={'Lin':'first_state', 'Tup':'ready_next_trial'},
                          outputsOff=['centerLED'])
        print(self.sm)
        self.dispatcher.set_state_matrix(self.sm)

    def prepare_next_trial(self, nextTrial):
        print('\nPrepare trial {}'.format(nextTrial))
        self.set_state_matrix()
        # -- Show results from previous trial --
        lastTenEvents = self.dispatcher.eventsMat[-10:-1]
        print('Last 10 events:')
        for oneEvent in lastTenEvents:
            print('{:.3f}\t {:.0f}\t {:.0f}'.format(oneEvent[0], oneEvent[1], oneEvent[2]))
        self.dispatcher.ready_to_start_trial()

    def timer_tic(self, etime, lastEvents):
        print('.', end='', flush=True)

    def closeEvent(self, event):
        """
        Executed when closing the main window. This method is inherited
        from QtWidgets.QMainWindow, which explains its camelCase name.
        """
        self.dispatcher.die()
        event.accept()


if __name__ == '__main__':
    (app, paradigm) = paramgui.create_app(Paradigm)
