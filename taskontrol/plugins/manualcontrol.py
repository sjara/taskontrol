#!/usr/bin/env python

"""
Plugin for controlling outputs manually.

TO DO:
- The sorting of the buttons is currently alphabetical. Bad idea.
  I will need to sort by the value of OUTPUTS.
"""

__version__ = '0.1.1'
__author__ = 'Santiago Jaramillo <sjara@uoregon.edu>'
__created__ = '2012-08-27'

import sys
from qtpy import QtWidgets as QtGui
from qtpy import QtCore
from taskontrol import rigsettings

BUTTON_COLORS = {'on':'red','off':'black'}

class ManualControl(QtGui.QGroupBox):
    """
    Manual control of outputs.
    """
    def __init__(self, statemachine, parent=None):
        super(ManualControl, self).__init__(parent)

        # -- Create graphical objects --
        layout = QtGui.QGridLayout()
        self.outputButtons = {}
        nButtons = 0
        nCols = 2
        #dictIterator = iter(sorted(rigsettings.OUTPUTS.iteritems()))
        dictIterator = rigsettings.OUTPUTS.items()
        for key,value in dictIterator:
            self.outputButtons[key] = OutputButton(statemachine, key,value)
            self.outputButtons[key].setObjectName('ManualControlButton')
            row = nButtons//nCols # Integer division
            col = nButtons%nCols  # Modulo
            layout.addWidget(self.outputButtons[key], row, col)
            nButtons += 1

        #layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setTitle('Manual control')


class OutputButton(QtGui.QPushButton):
    """
    Single button for manual output.
    """
    def __init__(self, statemachine, buttonText, outputIndex, parent=None):
        super(OutputButton, self).__init__(buttonText, parent)
        #self.setMinimumHeight(50)
        self.statemachine = statemachine
        self.outputIndex = outputIndex
        self.setCheckable(True)
        #self.connect(self,QtCore.SIGNAL('clicked()'),self.toggleOutput) ### OOLD
        self.clicked.connect(self.toggleOutput)

        #stylestr = 'QPushButton {font: 10pt}'
        #self.setStyleSheet(stylestr)

    def toggleOutput(self):
        if self.isChecked():
            self.start()
        else:
            self.stop()

    def start(self):
        stylestr = 'QPushButton {{color: {0}; font: bold}}'.format(BUTTON_COLORS['on'])
        self.setStyleSheet(stylestr)
        self.statemachine.force_output(self.outputIndex,1)

    def stop(self):
        stylestr = ''
        self.setStyleSheet(stylestr)
        self.statemachine.force_output(self.outputIndex,0)

class WaterControl(QtGui.QGroupBox):
    """
    Manual control of water valves
    """
    def __init__(self, statemachine, parent=None):
        super(WaterControl, self).__init__(parent)
        # -- Create graphical objects --
        layout = QtGui.QHBoxLayout()
        self.outputButtons = {}
        outputsDict = {'Left':rigsettings.OUTPUTS['leftWater'],
                       'Right':rigsettings.OUTPUTS['rightWater']}
        for key,value in sorted(outputsDict.items()):
            self.outputButtons[key] = OutputButton(statemachine, key,value)
            self.outputButtons[key].setObjectName('ManualControlButton')
            self.outputButtons[key].setMinimumHeight(80)
            layout.addWidget(self.outputButtons[key])
        self.setLayout(layout)
        self.setTitle('Water control')


class TimedButton(QtGui.QPushButton):
    """
    Single button for timed activation of output.
    """
    def __init__(self, statemachine, buttonText, outputIndex, toggleTime=0.03, parent=None):
        super(TimedButton, self).__init__(buttonText, parent)
        self.statemachine = statemachine
        self.outputIndex = outputIndex
        self.toggleTime = toggleTime
        self.clicked.connect(self.start)
        self.timer = QtCore.QTimer(self)

    def start(self):
        stylestr = 'QPushButton {{color: {0}; font: bold}}'.format(BUTTON_COLORS['on'])
        self.setStyleSheet(stylestr)
        self.statemachine.force_output(self.outputIndex,1)
        self.timer.singleShot(1e3*self.toggleTime, self.stop) # timer takes interval in ms

    def stop(self):
        stylestr = ''
        self.setStyleSheet(stylestr)
        self.statemachine.force_output(self.outputIndex,0)

class SingleDrop(QtGui.QGroupBox):
    """
    Buttons to deliver a small drop of water.
    """
    def __init__(self, statemachine, toggleTime=0.03, parent=None):
        super(SingleDrop, self).__init__(parent)
        # -- Create graphical objects --
        layout = QtGui.QHBoxLayout()
        self.outputButtons = {}
        outputsDict = {'Left':rigsettings.OUTPUTS['leftWater'],
                       'Right':rigsettings.OUTPUTS['rightWater']}
        for key,value in sorted(outputsDict.items()):
            self.outputButtons[key] = TimedButton(statemachine, key, value, toggleTime=toggleTime)
            self.outputButtons[key].setObjectName('SingleDropButton')
            self.outputButtons[key].setMinimumHeight(40)
            layout.addWidget(self.outputButtons[key])
        self.setLayout(layout)
        self.setTitle('Single drop')


if __name__ == "__main__":

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    import sys
    try:
      app = QtGui.QApplication(sys.argv)
    except RuntimeError:
      app = QtCore.QCoreApplication.instance()
    form = QtGui.QDialog()
    #from taskontrol.plugins import smdummy as statemachine
    from taskontrol.plugins import smemulator as statemachine
    statemachine = statemachine.StateMachineClient()
    mc = ManualControl(statemachine)
    sdrop = SingleDrop(statemachine, toggleTime=0.5)
    layoutMain = QtGui.QHBoxLayout()
    layoutMain.addWidget(mc)
    layoutMain.addWidget(sdrop)
    form.setLayout(layoutMain)
    form.show()
    app.exec_()
