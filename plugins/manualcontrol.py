#!/usr/bin/env python

'''
Plugin for controlling outputs manually.


THIS MODULE NEEDS TO BE CHANGED TO WORK WITH ANY DISPATCHER/CLIENT


'''

__version__ = '0.1.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2012-08-27'

from PySide import QtCore 
from PySide import QtGui 
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
            self.outputButtons[key].setObjectName('ManualControlButton')
            row = nButtons//nCols # Integer division
            col = nButtons%nCols  # Modulo
            layout.addWidget(self.outputButtons[key], row, col)
            nButtons += 1

        #layout.setContentsMargins(0, 0, 0, 0)
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
        stylestr = 'QPushButton {{color: {0}; font: bold}}'.format(BUTTON_COLORS['on'])
        self.setStyleSheet(stylestr)
        self.statemachine.force_output(self.outputIndex,1)

    def stop(self):
        '''Stop action.'''
        stylestr = ''
        self.setStyleSheet(stylestr)
        self.statemachine.force_output(self.outputIndex,0)


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    import sys
    try:
      app = QtGui.QApplication(sys.argv)
    except RuntimeError:
      app = QtCore.QCoreApplication.instance()
    form = QtGui.QDialog()
    from taskontrol.plugins import smdummy
    statemachine = smdummy.StateMachineClient()
    mc = ManualControl(statemachine)
    layoutMain = QtGui.QHBoxLayout()
    layoutMain.addWidget(mc)
    form.setLayout(layoutMain)
    form.show()
    app.exec_()
