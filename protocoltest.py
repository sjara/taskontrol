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
import paramgui
import dispatcher

reload(paramgui)
reload(dispatcher)


class Protocol(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Protocol, self).__init__(parent)

        # Add widgets
        self.dispatcher = dispatcher.Dispatcher(host='soul',connectnow=True)
        self.param1 = paramgui.Parameter('OneParam')

        layout = QtGui.QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.dispatcher)
        layout.addWidget(self.param1)
        self.setLayout(layout)
        
        # Set state matrix
        mat = [ [ 0,  0,  0,  0,  0,  0,  2,  1.2,  0,   0       ] ,\
                [ 1,  1,  1,  1,  1,  1,  1,   0,   0,   0       ] ,\
                [ 3,  3,  0,  0,  0,  0,  3,   4,   1,   0       ] ,\
                [ 2,  2,  0,  0,  0,  0,  2,   4,   2,   0       ] ]
        self.dispatcher.setStateMatrix(mat)


    def closeEvent(self, event):
        '''Make sure dispatcher stops and closes when closing window.'''
        # FIXME: this feel recursive, I thought the event would come back
        #        to the parent of dispatcher
        self.dispatcher.die()
        event.accept()


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    form = Protocol()
    form.show()
    app.exec_()
