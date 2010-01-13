#!/usr/bin/env python

'''
Classes for graphical protocol parameters.

Two parameters classes are defined:
- NumericParam: For a numeric entry and its label.
- MenuParam: For a menu entry and its label.

TODO:
- Make both label and text expanding horizontally

'''


__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-14'

import sys
from PyQt4 import QtCore 
from PyQt4 import QtGui 

# FIXME: Add validation of numbers
#NUMERIC_REGEXP = 

class Container(dict):
    def __init__(self):
        super(Container, self).__init__()        
        self._groups = {}
        self.history = {}
    #def append(self,item):
    #    self.items.append(item)

    def __setitem__(self, paramName, paramInstance):
        # -- Check if there is already a parameter with that name --
        if paramName in self:
            print 'There is already a parameter named %s'%paramName
            raise ValueError
        # -- Check if paramInstance is of valid type and has a group --
        try:
            groupName = paramInstance.getGroup()
        except AttributeError:
            print 'Container cannot hold items of type %s'%type(paramInstance)
            raise
        # -- Append name of parameter to group list --
        if groupName in self._groups:
            self._groups[groupName].append(paramName)
        else:
            self._groups[groupName] = [paramName]
        # -- Add paramInstance to Container --
        dict.__setitem__(self, paramName, paramInstance)

    def printItems(self):
        for key,item in self.iteritems():
            print '[%s] %s : %f'%(type(item),key,item.getValue())

    def updateHistory(self):
        '''Append the value of each parameter for this trial.'''
        for key,item in self.iteritems():
            # FIXME: I think there is a nicer way to do this for the first trial
            try:
                self.history[key].append(item.getValue())
            except KeyError: # If the key does not exist yet (e.g. first trial)
                self.history[key] = [item.getValue()]

    def appendToFile(self,h5file):
        dataParent = 'trialData'
        itemsParent = 'menuItems'
        tdataGroup = h5file.createGroup('/','trialData',
                                        'Parameters from each trial')
        menuItemsGroup = h5file.createGroup('/','menuItems',
                                        'Items in menu parameters')
        for key,item in self.iteritems():
            paramLabel = self[key].getLabel()
            h5file.createArray(tdataGroup, key, self.history[key], paramLabel)
            # FIXME: not very ObjectOriented to use getType
            #        the object should be able to save itself
            if self[key].getType()=='menu':
                h5file.createArray(menuItemsGroup, key, self[key].getItems(),
                                   '%s menu items'%paramLabel)

    def layoutGroup(self,groupName):
        '''Create box and layout with all parameters of a given group'''
        groupBox = QtGui.QGroupBox(groupName)
        #self.layoutForm = QtGui.QFormLayout()
        self.layoutForm = ParamGroupLayout()
        #self.layoutForm.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        #self.layoutForm.setAlignment(QtCore.Qt.AlignRight)
        for paramkey in self._groups[groupName]:
            self.layoutForm.addRow(self[paramkey].labelWidget,self[paramkey].editWidget)

        groupBox.setLayout(self.layoutForm)
        return groupBox

    '''
    def layoutGroup(self,groupName):
        #Create box and layout with all parameters of a given group
        groupBox = QtGui.QGroupBox(groupName)
        layoutBox = QtGui.QVBoxLayout()
        paramsInGroup = self.findParamsInGroup(groupName)
        for paramkey in paramsInGroup:
            layoutBox.addWidget(self[paramkey])
        groupBox.setLayout(layoutBox)
        return groupBox

    def findParamsInGroup(self,groupName):
        # This is inefficient, but it should only happen once
        paramsInGroup = []
        for key in self._orderedKeys:
            if self[key].inGroup(groupName):
                paramsInGroup.append(key)
        return paramsInGroup
    '''

class oldParamGroupLayout(QtGui.QGridLayout):
    def __init__(self,parent=None):
        super(ParamGroupLayout, self).__init__(parent)
    def addRow(self,labelWidget,editWidget):
        currentRow = self.rowCount()
        self.addWidget(labelWidget,currentRow,0,QtCore.Qt.AlignRight)
        self.addWidget(editWidget,currentRow,1,QtCore.Qt.AlignLeft)


class ParamGroupLayout(QtGui.QGridLayout):
    def __init__(self,parent=None):
        super(ParamGroupLayout, self).__init__(parent)
        self.setVerticalSpacing(0)
    def addRow(self,labelWidget,editWidget):
        currentRow = self.rowCount()
        self.addWidget(labelWidget,currentRow,0,QtCore.Qt.AlignRight)
        self.addWidget(editWidget,currentRow,1,QtCore.Qt.AlignLeft)


class GenericParam(QtGui.QWidget):
    def __init__(self, labelText=QtCore.QString(), value=0, group=None,
                 labelWidth=80, parent=None):
        super(GenericParam, self).__init__(parent)
        self._group = group
        self._type = None
        self._value = None
        self.labelWidget = QtGui.QLabel(labelText)
        self.editWidget = None

    #def setGroup(self,group):
    #    self._group = group

    def getType(self):
        return self._type

    def getLabel(self):
        return str(self.label.text())

    def getGroup(self):
        return self._group

    def inGroup(self,groupName):
        return self._group==groupName


class NumericParam(GenericParam):
    def __init__(self, labelText=QtCore.QString(), value=0, group=None,
                 labelWidth=80, parent=None):
        super(NumericParam, self).__init__(labelText, value, group, labelWidth, parent)
        self._type = 'numeric'

        # -- Define graphical interface --
        self.editWidget = QtGui.QLineEdit()

        # -- Define value --
        self.setValue(value)

    def setValue(self,value):
        self._value = value
        self.editWidget.setText(str(value))

    def getValue(self):
        return float(self.editWidget.text())



class MenuParam(GenericParam):
    def __init__(self, labelText=QtCore.QString(), menuItems=(), value=0, group=None,
                 labelWidth=80, parent=None):
        super(MenuParam, self).__init__(labelText, value, group, labelWidth, parent)
        self._type = 'menu'

        # -- Define graphical interface --
        self.editWidget = QtGui.QComboBox()
        self.editWidget.addItems(menuItems)

        # -- Define value --
        self._items = menuItems
        self.setValue(value)

    def setValue(self,value):
        self._value = value
        self.editWidget.setCurrentIndex(value)

    def setString(self,newstring):
        # FIXME: graceful warning if wrong string (ValueError exception)
        value = self._items.index(newstring)
        self._value = value
        self.editWidget.setCurrentIndex(value)

    def getValue(self):
        return self.editWidget.currentIndex()

    def getString(self):
        return str(self.editWidget.currentText())

    def getItems(self):
        return self._items

    #def appendToFile(self,h5file,dataParent,itemsParent):
    #    h5file.createArray(dataParent, key, paramContainer.history[key], paramLabel)
    #    h5file.createArray(menuItemsGroup, key, paramContainer[key].getItems(),
    #                               '%s menu items'%paramLabel)
        

class TestForm(QtGui.QDialog):
    def __init__(self, parent=None):
        super(TestForm, self).__init__(parent)
        # -- Create graphical objects --
        self.resize(400,300)
        #self.value = QtGui.QLineEdit()
        #Orientation=QtCore.Qt.Vertical
        self.value1 = NumericParam('OneParam')
        self.value2 = NumericParam('aVeryVerVeryVeryyLongParam')
        self.val = []
        for ind in range(10):
            self.val.append(NumericParam(str(ind)))
            
        self.menu1 = MenuParam('TheMenu',('One','Two','Three'))

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
        self.groupLayout.addWidget(self.menu1)
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

    # To get the item (as string) of a menuparam for the last trial in the history:
    #protocol.params['chooseNumber'].getItems()[protocol.params.history['chooseNumber'][-1]]
