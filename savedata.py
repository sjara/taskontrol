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

from PyQt4 import QtCore 
from PyQt4 import QtGui 

class SaveData(QtGui.QGroupBox):
    '''
    Save data
    '''

    def __init__(self, parent=None):
        super(SaveData, self).__init__(parent)

        # -- Create graphical objects --
        self.buttonSaveData = QtGui.QPushButton("Save data")
        self.buttonSaveData.setMinimumHeight(50)
        #self.buttonSaveData.setMinimumWidth(160)
        buttonFont = QtGui.QFont(self.buttonSaveData.font())
        #buttonFont.setPointSize(buttonFont.pointSize()+10)
        buttonFont.setBold(True)
        self.buttonSaveData.setFont(buttonFont)
        #self.setMinimumWidth(minwidth)

        # -- Create layouts --
        layout = QtGui.QGridLayout()
        layout.addWidget(self.buttonSaveData, 0,0)
        self.setLayout(layout)
        self.setTitle('Save Data')
        self.connect(self.buttonSaveData,QtCore.SIGNAL('clicked()'),self.fileSave)

    def fileSave(self):
        fname = unicode(QtGui.QFileDialog.getSaveFileName(self,'CHOOSE','/tmp/','*.*'))
        print fname
