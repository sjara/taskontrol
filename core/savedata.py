#!/usr/bin/env python

'''
Plugin (widget) to save data.
It may become a more general module/plugin (probably called sessiondata).


NOTE: as of Dec2009 there was a bug that shows a warning about
      KPluginLoader::load when opening the dialog. It seems to be
      harmless.  https://bugs.kde.org/show_bug.cgi?id=210904

'''


__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-12-27'

import os
import time
import h5py
from PySide import QtCore 
from PySide import QtGui 
from taskontrol.settings import rigsettings
import numpy as np

#class SaveData(QtGui.QWidget):
class SaveData(QtGui.QGroupBox):
    '''
    Save data
    '''
    logMessage = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(SaveData, self).__init__(parent)

        # -- Parameters --
        ###self.defaultFileName = '/tmp/defaultdata.hd5'

        # -- Create graphical objects --
        self.buttonSaveData = QtGui.QPushButton("Save data")
        self.buttonSaveData.setMinimumHeight(50)
        buttonFont = QtGui.QFont(self.buttonSaveData.font())
        buttonFont.setBold(True)
        self.buttonSaveData.setFont(buttonFont)
        self.checkInteractive = QtGui.QCheckBox('Interactive')
        self.checkInteractive.setChecked(False)

        # -- Create layouts --
        layout = QtGui.QGridLayout()
        layout.addWidget(self.buttonSaveData, 0,0)
        layout.addWidget(self.checkInteractive, 1,0)
        self.setLayout(layout)
        self.setTitle('Manage Data')
        #self.buttonSaveData.clicked.connect(self.fileSave)


    def to_file(self,listOfContainers,currentTrial=None):
        ###paramContainer,dispatcherModel,stateMatrixObj ### DELETE THIS
        '''
        Save history of parameters, events and results to a file.
        listOfContainers must be a list of objects that have a method 'append_to_file'.
                         examples of these are: paramgui.Container,
                         dispatcher.Dispatcher, statematrix.StateMatrix
        currentTrial is used to limit how many elements are stored for some arrays
        '''
        thissession=dict()
        thissession['date'] = time.strftime('%Y%m%d',time.localtime())
        thissession['experimenter'] = 'santiago'
        thissession['subject'] = 'saja000'
        dataDir = rigsettings.DATA_DIR
        fileExt = 'h5'
        fileNameOnly = '%s_%s.%s'%(thissession['subject'],thissession['date'],fileExt)
        defaultFileName = os.path.join(dataDir,fileNameOnly)

        self.logMessage.emit('Saving data...')

        if self.checkInteractive.checkState():
            #fname = unicode(QtGui.QFileDialog.getSaveFileName(self,'CHOOSE','/tmp/','*.*'))
            fname,ffilter = QtGui.QFileDialog.getSaveFileName(self,'CHOOSE','/tmp/','*.*')
            if not fname:
                self.logMessage.emit('Saving cancelled.')
                return
        else:
            fname = defaultFileName

        # -- Create data file --
        # FIXME: check that file opened correctly
        if os.path.exists(fname):
            self.logMessage.emit('File exists. I will rewrite {0}'.format(fname))
        h5file = h5py.File(fname,'w')

        for container in listOfContainers:
            try:
                container.append_to_file(h5file,currentTrial)
            except UserWarning as uwarn:
                self.logMessage.emit(uwarn.message)
                print uwarn.message
            except:
                h5file.close()
                raise
        h5file.close()

        self.logMessage.emit('Saved data to %s'%fname)
        #messenger.Messenger.send('Saved data to %s'%fname)
        #messenger.Messenger.send('Saved data to %s'%fname,sender=__name__)

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Enable Ctrl-C
    import sys
    # -- A workaround to enable re-running the app in ipython after closing --
    app=QtGui.QApplication.instance() # checks if QApplication already exists 
    if not app: # create QApplication if it doesnt exist 
        app = QtGui.QApplication(sys.argv)
    form = QtGui.QDialog()
    saveData = SaveData()
    layoutMain = QtGui.QHBoxLayout()
    layoutMain.addWidget(saveData)
    form.setLayout(layoutMain)
    class Dispatcher(object):
        eventsMatrix = [[0,0,0]]
    dispatcherModel = Dispatcher()
    def onbutton():
        import paramgui
        params = paramgui.Container()
        saveData.to_file(params,dispatcherModel)
    saveData.buttonSaveData.clicked.connect(onbutton)
    form.show()
    app.exec_()



'''
        try:
            ###print dispatcherModel.eventsMat ### DEBUG
            success = dispatcherModel.append_to_file(h5file)
            if not success:
                self.logMessage.emit('WARNING: No trials have been completed. Nothing was saved.')
                h5file.close()
                return
            paramContainer.append_to_file(h5file)
            stateMatrixObj.append_to_file(h5file)
        except:
            h5file.close()
            raise
'''

