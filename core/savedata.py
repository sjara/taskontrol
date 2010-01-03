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
import tables
from PyQt4 import QtCore 
from PyQt4 import QtGui 
from taskontrol.core import messenger
from taskontrol.settings import rigsettings

class SaveData(QtGui.QGroupBox):
    '''
    Save data
    '''

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
        #self.connect(self.buttonSaveData,QtCore.SIGNAL('clicked()'),self.fileSave)


    def fileSave(self,paramContainer,eventsMat):
        thissession=dict()
        thissession['date'] = time.strftime('%Y%m%d',time.localtime())
        thissession['experimenter'] = 'santiago'
        thissession['subject'] = 'saja000'
        dataDir = rigsettings.DATA_DIR
        fileExt = 'h5'
        fileNameOnly = '%s_%s.%s'%(thissession['subject'],thissession['date'],fileExt)
        defaultFileName = os.path.join(dataDir,fileNameOnly)

        # FIXME: what happens if the user presses the CANCEL button?
        if self.checkInteractive.checkState():
            fname = unicode(QtGui.QFileDialog.getSaveFileName(self,'CHOOSE','/tmp/','*.*'))
        else:
            fname = defaultFileName

        messenger.Messenger.send('Saving data...')

        # -- Create data file --
        h5file = tables.openFile(fname, mode = "w", title = "Behavioral session data")
        eventsGroup = h5file.createGroup('/', 'events',
                                         'Events that ocurred during the session')
        h5file.createArray(eventsGroup, 'eventsMat', eventsMat, 'Matrix of raw events')
        h5file.close()

        paramContainer.printItems()
        messenger.Messenger.send('Saved data to %s'%fname)
        #messenger.Messenger.send('Saved data to %s'%fname,sender=__name__)


