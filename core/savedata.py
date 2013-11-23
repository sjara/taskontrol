#!/usr/bin/env python

'''
Widget to save data.
'''

__version__ = '0.2'
__author__ = 'Santiago Jaramillo <sjara@uoregon.edu>'

import os
import time
import h5py
from PySide import QtCore 
from PySide import QtGui 
import subprocess
#from taskontrol.settings import rigsettings

class SaveData(QtGui.QGroupBox):
    '''
    A widget to save data, transfer it to a remote repository, and update the database.
    '''
    logMessage = QtCore.Signal(str)

    def __init__(self, datadir, remotedir=None, updatedb=True, parent=None):
        '''
        Args:
            datadir (str): data root directory.
            remotedir (str): remote directory of data repository.
                If none given it will not send data to repository.
            updatedb (bool): [not implemented].

        '''
        super(SaveData, self).__init__(parent)

        self.filename = None
        self.datadir = datadir
        self.remotedir = remotedir
        
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


    def to_file(self,containers,currentTrial=None,experimenter='experimenter',
                subject='subject',paradigm='paradigm',date=None,suffix='a',filename=None):
        '''
        Saves the history of parameters, events and results to an HDF5 file.

        Args:
            containers: a list of objects that have a method 'append_to_file'.
                Examples of these are: paramgui.Container,
                dispatcher.Dispatcher, statematrix.StateMatrix
            currentTrial: limits how many elements are stored (up to currentTrial-1)
            experimenter: string
            subject: string
            paradigm: string
            date: (optional) string. If none given, today's date will be used.
            suffix: (optional) string. If none give, it will use a lowercase letter.
            filename: (optional) string with full path. If a filename is given,
                all other string parameters will be ignored.

        The data is saved to:
        ``datadir/experimenter/subject/subject_paradigm_YYMMDDa.h5``
        '''

        if filename is not None:
            defaultFileName = filename
        else:
            if date is None:
                date = time.strftime('%Y%m%d',time.localtime())
            dataRootDir = self.datadir
            fileExt = 'h5'
            dataDir = os.path.join(dataRootDir,experimenter,subject)
            if not os.path.exists(dataDir):
                os.makedirs(dataDir)
            fileNameOnly = '{0}_{1}_{2}{3}.{4}'.format(subject,paradigm,date,suffix,fileExt)
            defaultFileName = os.path.join(dataDir,fileNameOnly)

        self.logMessage.emit('Saving data...')

        if self.checkInteractive.checkState():
            fname,ffilter = QtGui.QFileDialog.getSaveFileName(self,'CHOOSE','/tmp/','*.*')
            if not fname:
                self.logMessage.emit('Saving cancelled.')
                return
        else:
            fname = defaultFileName
        
        # -- Create data file --
        # FIXME: check that the file opened correctly
        if os.path.exists(fname):
            self.logMessage.emit('File exists. I will rewrite {0}'.format(fname))
        h5file = h5py.File(fname,'w')

        for container in containers:
            try:
                container.append_to_file(h5file,currentTrial)
            except UserWarning as uwarn:
                self.logMessage.emit(uwarn.message)
                print uwarn.message
            except:
                h5file.close()
                raise
        h5file.close()
 
        self.filename = fname
        self.logMessage.emit('Saved data to {0}'.format(fname))

        if self.remotedir:
            self.send_to_repository()

    def send_to_repository(self):
        '''
        Send saved data to repository.
        FIXME: The remote directory must exist, otherwise it will fail.
        '''
        remoteLocation = self.remotedir + os.path.sep
        #'sjara@localhost://tmp/remote/'
        self.logMessage.emit('Sent data to {0}'.format(remoteLocation))
        cmd = 'rsync'
        flags = '-av'
        args1 = '-e'
        args2 = 'ssh -o "NumberOfPasswordPrompts 0"'
        localfile = self.filename
        cmdlist = [cmd,flags,args1,args2,localfile,remoteLocation]
        p = subprocess.Popen(cmdlist,shell=False,stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if stderr:
            raise IOError(stderr)
        pass
        self.logMessage.emit('Done sending data.')

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Enable Ctrl-C
    import sys
    from taskontrol.settings import rigsettings
    # -- A workaround to enable re-running the app in ipython after closing --
    app=QtGui.QApplication.instance() # checks if QApplication already exists 
    if not app: # create QApplication if it doesnt exist 
        app = QtGui.QApplication(sys.argv)
    form = QtGui.QDialog()
    saveData = SaveData(rigsettings.DATA_DIR)
    layoutMain = QtGui.QHBoxLayout()
    layoutMain.addWidget(saveData)
    form.setLayout(layoutMain)
    def onbutton():
        import arraycontainer
        results = arraycontainer.Container()
        results['onevar'] = [1,2,3,4]
        saveData.to_file([results],currentTrial=3)
        print('Saved data to {0}'.format(saveData.filename))
    saveData.buttonSaveData.clicked.connect(onbutton)
    form.show()
    app.exec_()



'''
        import paramgui
        params = paramgui.Container()
    class Dispatcher(object):
        eventsMatrix = [[0,0,0]]
    dispatcherModel = Dispatcher()

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

