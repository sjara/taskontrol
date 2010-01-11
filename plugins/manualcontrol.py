#!/usr/bin/env python

'''
Plugin for controlling outputs manually.
'''

from PyQt4 import QtCore 
from PyQt4 import QtGui 
from taskontrol.settings import rigsettings

BUTTON_COLORS = {'on':'red','off':'black'}

class ManualControl(QtGui.QGroupBox):
    '''
    Manual control of outputs
    '''

    def __init__(self, dispatcher, parent=None):
        super(ManualControl, self).__init__(parent)

        # -- Create graphical objects --
        layout = QtGui.QGridLayout()
        self.outputButtons = {}
        nButtons = 0
        nCols = 2
        dictIterator = iter(sorted(rigsettings.DOUT.iteritems()))
        for key,value in dictIterator:
            self.outputButtons[key] = OutputButton(dispatcher, key,value)
            row = nButtons//nCols # Integer division
            col = nButtons%nCols  # Modulo
            layout.addWidget(self.outputButtons[key], row, col)
            nButtons += 1

        self.setLayout(layout)
        self.setTitle('Manual control')

 
class OutputButton(QtGui.QPushButton):
    '''Single button for manual output'''
    def __init__(self, dispatcher, buttonText, outputValue, parent=None):
        super(OutputButton, self).__init__(buttonText, parent)

        #self.setMinimumHeight(50)
        self._dispatcher = dispatcher
        self._outputValue = outputValue
        self.setCheckable(True)
        self.connect(self,QtCore.SIGNAL('clicked()'),self.toggleOutput)


    def toggleOutput(self):
        if self.isChecked():
            self.start()
        else:
            self.stop()

    def start(self):
        '''Start action.'''
        stylestr = 'QWidget {color: %s}'%BUTTON_COLORS['on']
        self.setStyleSheet(stylestr)
        self._dispatcher.statemachine.bypassDout(self._outputValue)

    def stop(self):
        stylestr = 'QWidget {color: %s}'%BUTTON_COLORS['off']
        self.setStyleSheet(stylestr)
        self._dispatcher.statemachine.bypassDout(-self._outputValue)
