"""
Widget to save data.
"""

import os
import time
import h5py
import sys
from qtpy import QtWidgets
from qtpy import QtGui
from qtpy import QtCore
import subprocess

# A file with this name must exist in the remote directory
REMOTEDIR_VERIFICATION = 'REMOTEDIR.txt'


class SaveData(QtWidgets.QGroupBox):
    """
    A widget to save data, transfer it to a remote repository, and update the database.
    """
    logMessage = QtCore.Signal(str)

    def __init__(self, datadir, remotedir=None, updatedb=True, parent=None):
        """
        Args:
            datadir (str): data root directory.
            remotedir (str): remote directory of data repository.
                If none given it will not send data to repository.
            updatedb (bool): [not implemented].

        """
        super(SaveData, self).__init__(parent)

        self.datadir = datadir
        self.remotedir = remotedir
        self.filename = None

        # -- Create graphical objects --
        self.buttonSaveData = QtWidgets.QPushButton("Save data")
        self.buttonSaveData.setMinimumHeight(50)
        buttonFont = QtGui.QFont(self.buttonSaveData.font())
        buttonFont.setBold(True)
        self.buttonSaveData.setFont(buttonFont)
        self.checkInteractive = QtWidgets.QCheckBox('Interactive')
        self.checkInteractive.setChecked(False)
        self.checkOverwrite = QtWidgets.QCheckBox('Overwrite')
        self.checkOverwrite.setChecked(False)
        self.checkSendToRepo = QtWidgets.QCheckBox('Send to repository')
        self.checkSendToRepo.setChecked(False)

        # -- Create layouts --
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.buttonSaveData, 0, 0, 1, 2)
        layout.addWidget(self.checkInteractive, 1, 0)
        layout.addWidget(self.checkOverwrite, 1, 1)
        layout.addWidget(self.checkSendToRepo, 2, 0, 1, 2)
        self.setLayout(layout)
        self.setTitle('Manage Data')

    def to_file(self, containers, currentTrial=None, experimenter='', subject='subject',
                paradigm='paradigm', date=None, suffix='a', filename=None):
        """
        Saves the history of parameters, events and results to an HDF5 file.

        Args:
            containers: a list of objects that have a method 'append_to_file'.
                Examples of these are: paramgui.Container,
                dispatcher.Dispatcher, statematrix.StateMatrix
            currentTrial: limits how many elements are stored (up to currentTrial-1)
            experimenter: string (if empty, no experimenter folder is used)
            subject: string
            paradigm: string
            date: (optional) string. If none given, today's date will be used.
            suffix: (optional) string. If none give, it will use a lowercase letter.
            filename: (optional) string with full path. If a filename is given,
                all other string parameters will be ignored.

        The data is saved to:
        ``datadir/experimenter/subject/subject_paradigm_YYMMDDa.h5``
          or, is experimenter is empty:
        ``datadir/subject/subject_paradigm_YYMMDDa.h5``
        """
        if filename is not None:
            defaultFileName = filename
        else:
            if date is None:
                date = time.strftime('%Y%m%d', time.localtime())
            dataRootDir = self.datadir
            fileExt = 'h5'
            relativePath = os.path.join(experimenter, subject, '')
            fullDataDir = os.path.join(dataRootDir, relativePath)
            if not os.path.exists(fullDataDir):
                os.makedirs(fullDataDir)
            fileNameOnly = '{0}_{1}_{2}{3}.{4}'.format(subject, paradigm, date, suffix, fileExt)
            defaultFileName = os.path.join(fullDataDir, fileNameOnly)

        self.logMessage.emit('Saving data...')

        if self.checkInteractive.checkState():
            fname, ffilter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save to file',
                                                                   defaultFileName, '*.*')
            if not fname:
                self.logMessage.emit('Saving cancelled.')
                return
        elif os.path.exists(defaultFileName):
            if self.checkOverwrite.checkState():
                fname = defaultFileName
                self.logMessage.emit('File exists. I will overwrite {0}'.format(fname))
            else:
                msgBox = QtWidgets.QMessageBox()
                msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                msgBox.setText(f'File exists: <br>{defaultFileName} <br>' +
                               'Use <b>Interactive</b> or <b>Overwrite</b> modes.')
                msgBox.exec_()
                return
        else:
            fname = defaultFileName

        # -- Create data file --
        # FIXME: check that the file opened correctly
        h5file = h5py.File(fname, 'w')

        success = True
        for container in containers:
            try:
                container.append_to_file(h5file, currentTrial)
            except UserWarning as uwarn:
                success = False
                self.logMessage.emit(str(uwarn))
                print(uwarn)
            except:  # pylint: disable=bare-except
                success = False
                h5file.close()
                raise
        h5file.close()

        if success:
            self.filename = fname
            self.logMessage.emit('Saved data to {0}'.format(fname))
            if self.checkSendToRepo.checkState():
                if self.remotedir:
                    self.send_to_repository(relativePath, fileNameOnly)
                else:
                    self.logMessage.emit('Remote directory has not been defined. ' +
                                         'Nothing sent to repository.')

    def send_to_repository(self, relativePath, fileNameOnly):
        """
        Send saved data to repository.
        FIXME: The remote subdirectories must exist, otherwise it will fail.
        """
        verificationFile = os.path.join(self. remotedir, REMOTEDIR_VERIFICATION)
        if os.path.exists(verificationFile):
            fullRemoteDir = os.path.join(self. remotedir, relativePath)
            if not os.path.exists(fullRemoteDir):
                os.makedirs(fullRemoteDir)
            cmd = 'rsync'
            flag1 = '-ab'
            flag2 = '--no-g'
            localfile = self.filename
            cmdlist = [cmd, flag1, flag2, localfile, fullRemoteDir]
            p = subprocess.Popen(cmdlist, shell=False, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if stderr:
                raise IOError(stderr)
            self.logMessage.emit('Sent data to {0}'.format(fullRemoteDir))
        else:
            self.logMessage.emit('Remote verification file not found. Nothing was sent.')

        """
        #'sjara@localhost://tmp/remote/'
        cmd = 'rsync'
        flags = '-avb'
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
        """
