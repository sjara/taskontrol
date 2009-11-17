#!/usr/bin/env python

'''
Define objects to set protocol parameters graphically.

Parameters can set either with:
- Label + LineEdit
- Menu ???

TODO:
- Make both label and text expanding horizontally

'''


__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-14'

import sys
from PyQt4 import QtCore 
from PyQt4 import QtGui 


class Parameter(QtGui.QWidget):
    def __init__(self, labelText=QtCore.QString(), labelWidth=80, parent=None):
        super(Parameter, self).__init__(parent)
        self.label = QtGui.QLabel(labelText)
        self.lineEdit = QtGui.QLineEdit()
        self.lineEdit.setAlignment(QtCore.Qt.AlignRight)
        self.label.setBuddy(self.lineEdit)
        self.label.setFixedWidth(labelWidth)

        layout = QtGui.QHBoxLayout(spacing=0,margin=0)
        layout.addWidget(self.lineEdit)
        layout.addSpacing(4)
        layout.addWidget(self.label)
        self.setLayout(layout)


class TestForm(QtGui.QDialog):
    def __init__(self, parent=None):
        super(TestForm, self).__init__(parent)
        # -- Create graphical objects --
        self.resize(400,300)
        #self.value = QtGui.QLineEdit()
        #Orientation=QtCore.Qt.Vertical
        self.value1 = Parameter('OneParam')
        self.value2 = Parameter('aVeryVerVeryVeryyLongParam')
        self.val = []
        for ind in range(10):
            self.val.append(Parameter(str(ind)))
            
        # -- Create layouts --
        self.group = QtGui.QGroupBox('Section')
        self.group.setFixedWidth(200)
        self.groupLayout = QtGui.QVBoxLayout()
        self.groupLayout.setSpacing(0)
        layout = QtGui.QVBoxLayout()
        layout.addStretch()
        #for ind in range(10):
        #    layout.addWidget(self.val[ind])
        
        #self.groupLayout.addStretch()
        self.groupLayout.addWidget(self.value1)
        self.groupLayout.addWidget(self.value2)
        #self.groupLayout.addStretch()
        self.group.setLayout(self.groupLayout)
        layout.addWidget(self.group)
        #layout.addStretch()
        self.setLayout(layout)

        # Change font to bold
        if 0:
            f=self.group.font()
            f.setBold(True)
            self.group.setFont(f)


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    form = TestForm()
    form.show()
    app.exec_()
