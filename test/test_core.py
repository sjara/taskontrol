
def arraycontainer_test():

    from core.arraycontainer import Container
    import h5py
    import numpy as np
    c = Container()
    c['myvar1'] = np.arange(10)
    c.labels['myvar2labels'] = {'yes':1,'no':0}
    c['myvar2'] = np.array([0,1,1,1,0])
    h5file = h5py.File('/tmp/testh5.h5','w')
    h5file.create_group('resultsData')
    c.append_to_file(h5file,4)
    h5file.close()

def dispatcher_test_one():

    from core.dispatcher import *
    import sys
    from PySide import QtCore 
    from PySide import QtGui 
    import numpy as np
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL) # Enable Ctrl-C
    app=QtGui.QApplication.instance() # checks if QApplication already exists 
    if not app: # create QApplication if it doesnt exist 
        app = QtGui.QApplication(sys.argv)
    form = QtGui.QDialog()
    form.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    #form.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
    dispatcherModel = Dispatcher(parent=form,serverType='dummy',connectnow=True, interval=0.5)
    dispatcherView = DispatcherGUI(parent=form)
    dispatcherModel.timerTic.connect(dispatcherView.update)
    dispatcherView.resumeSM.connect(dispatcherModel.resume)
    dispatcherView.pauseSM.connect(dispatcherModel.pause)
    dispatcherModel.resume()
    #form.show()
    #app.exec_()
    #app.quit()


    
