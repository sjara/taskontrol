#!/usr/bin/env python
"""
This example shows how to control the state matrix from a graphical interface.
It uses the module 'dispatcher' to provide an interface for starting
and stopping the state machine.
"""

import sys
from qtpy import QtCore
from qtpy import QtWidgets
from taskontrol import rigsettings
from taskontrol import dispatcher
import signal

# -- Create main window --
signal.signal(signal.SIGINT, signal.SIG_DFL) # Enable Ctrl-C (to close window)
app = QtWidgets.QApplication(sys.argv)
form = QtWidgets.QDialog()

# -- Create dispatcher and upload state transition matrix --
dispatcherModel = dispatcher.Dispatcher(parent=form,
                                        serverType=rigsettings.STATE_MACHINE_TYPE,
                                        interval=0.5,
                                        nInputs=3, nOutputs=2)

#                Ci  Co  Li  Lo  Ri  Ro  Timer
stateMatrix = [ [ 0,  0,  0,  0,  0,  0,  1 ] ,
                [ 1,  1,  1,  1,  1,  1,  2 ] ,
                [ 1,  2,  1,  2,  2,  2,  1 ] ]
stateOutputs = [[0,0], [1,0], [0,1]]
serialOutputs = None
stateTimers  = [  0.1,    0.5 ,    2.0  ]
# NOTE: For this example we use _set_state_matrix() to set the matrix from a python list.
#       However, the usual way to set this matrix uses instead a statematrix.StateMatrix
#       object, discussed in the next examples.
dispatcherModel._set_state_matrix(stateMatrix, stateOutputs, serialOutputs, stateTimers)

# -- Create dispatcher GUI and connect signals --
dispatcherView = dispatcher.DispatcherGUI(model=dispatcherModel)

# -- Create layout and run --
layout = QtWidgets.QVBoxLayout()
layout.addWidget(dispatcherView)
form.setLayout(layout)
form.show()
app.exec_()


