"""
Classes for graphical parameters and other graphical elements in a paradigm.

The following parameters classes are defined:
- NumericParam: For a numeric entry.
- StringParam: For entry of a string.
- MenuParam: For a menu entry.

In addition, a Messenger class is provided for displaying messages in a status bar,
as well as functions for creating the main Qt app for a paradigm.
"""

# TODO:  Make both label and text expanding horizontally

from qtpy import QtCore
from qtpy import QtWidgets
import imp
import numpy as np  # To be able to save strings with np.string_()
import signal
import sys
import socket
import time
from . import utils
from . import rigsettings


class Container(dict):
    def __init__(self):
        super(Container, self).__init__()
        self._groups = {}
        self._paramsToKeepHistory = []
        self.history = {}

    def __setitem__(self, paramName, paramInstance):
        # -- Check if there is already a parameter with that name --
        if paramName in self:
            print('There is already a parameter named {}'.format(paramName))
            raise ValueError
        # -- Check if paramInstance is of valid type and has a group --
        try:
            groupName = paramInstance.get_group()
            historyEnabled = paramInstance.history_enabled()
        except AttributeError:
            print('Container cannot hold items of type {}'.format(type(paramInstance)))
            raise
        # -- Append name of parameter to group list --
        try:
            self._groups[groupName].append(paramName)
        except KeyError:  # If group does not exist yet
            self._groups[groupName] = [paramName]
        # -- Append name of parameter to list of params to keep history --
        if historyEnabled:
            try:
                self._paramsToKeepHistory.append(paramName)
            except KeyError:  # If group does not exist yet
                self._paramsToKeepHistory = [paramName]

        # -- Add paramInstance to Container --
        dict.__setitem__(self, paramName, paramInstance)

    def print_items(self):
        for key, item in self.items():
            print('[{0}] {1}} : {2}}'.format(type(item), key, str(item.get_value())))

    def layout_group(self, groupName):
        """Create box and layout with all parameters of a given group"""
        groupBox = QtWidgets.QGroupBox(groupName)
        self.layoutForm = ParamGroupLayout()
        for paramkey in self._groups[groupName]:
            self.layoutForm.add_row(self[paramkey]. labelWidget, self[paramkey].editWidget)

        groupBox.setLayout(self.layoutForm)
        return groupBox

    def update_history(self, lastTrial=None):
        """Append the value of each parameter (to track) for this trial."""
        for key in self._paramsToKeepHistory:
            try:
                self.history[key].append(self[key].get_value())
            except KeyError:  # If the key does not exist yet (e.g. first trial)
                self.history[key] = [self[key].get_value()]
            if lastTrial is not None:
                msg = 'The length of the history does not match the number of trials.'
                assert len(self.history[key])==lastTrial+1, msg

    def set_values(self, valuesdict):
        """Set the value of many parameters at once.
        valuesDict is a dictionary of parameters and their values.
        for example: {param1:val1, param2:val2}
        """
        for key, val in valuesdict.items():
            if key in self:
                if isinstance(self[key], MenuParam):
                    self[key].set_string(val)
                else:
                    self[key].set_value(val)
            else:
                print('Warning! {0} is not a valid parameter.'.format(key))

    def from_file(self, filename, dictname='default'):
        """
        Set values from a dictionary stored in a file.
        filename: (string) file with parameters (full path)
        dictname: (string) name of dictionary in filename containing parameters
                  If none is given, it will attempt to load 'default'
        """
        if filename is not None:
            paramsmodule = imp.load_source('module.name', filename)
            try:
                self.set_values(getattr(paramsmodule, dictname))
            except AttributeError:
                print("There is no '{0}' in {1}".format(dictname, filename))
                raise

    def append_to_file(self, h5file, currentTrial):
        """
        Append parameters' history to an HDF5 file.
        It truncates data to the trial before currentTrial, because currentTrial has not ended.
        """
        dataParent = 'resultsData'      # Parameters from each trial
        itemsParent = 'resultsLabels'   # Items in menu parameters
        sessionParent = 'sessionData'   # Parameters for the whole session
        # descriptionAttr = 'Description'
        # FIXME: the contents of description should not be the label, but the
        #        description of the parameter (including its units)
        trialDataGroup = h5file.require_group(dataParent)
        menuItemsGroup = h5file.require_group(itemsParent)
        sessionDataGroup = h5file.require_group(sessionParent)

        # -- Append date/time and hostname --
        dset = sessionDataGroup.create_dataset('hostname', data=socket.gethostname())
        dateAndTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        dset = sessionDataGroup.create_dataset('date', data=dateAndTime)

        # -- Append all other parameters --
        for key, item in self.items():
            # -- Store parameters with history --
            if item.history_enabled():
                if key not in self.history:
                    raise ValueError('No history was recorded for "{0}". '.format(key) +
                                     'Did you use paramgui.Container.update_history() correctly?')
                dset = trialDataGroup.create_dataset(key, data=self.history[key][:currentTrial])
                dset.attrs['Description'] = item.get_label()
                if item.get_type() == 'numeric':
                    dset.attrs['Units'] = item.get_units()
                # FIXME: not very ObjectOriented to use getType
                #        the object should be able to save itself
                if item.get_type() == 'menu':
                    menuList = item.get_items()
                    menuDict = dict(zip(menuList, range(len(menuList))))
                    utils.append_dict_to_HDF5(menuItemsGroup, key, menuDict)
                    dset.attrs['Description'] = '{} menu items'.format(item.get_label())
            else:  # -- Store parameters without history (Session parameters) --
                if item.get_type() == 'string':
                    dset = sessionDataGroup.create_dataset(key, data=np.string_(item.get_value()))
                else:
                    dset = trialDataGroup.create_dataset(key, data=item.get_value())
                dset.attrs['Description'] = item.get_label()


class ParamGroupLayout(QtWidgets.QGridLayout):
    """Layout for group of parameters."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalSpacing(0)

    def add_row(self, labelWidget, editWidget):
        currentRow = self.rowCount()
        self.addWidget(labelWidget, currentRow, 0, QtCore.Qt.AlignRight)
        self.addWidget(editWidget, currentRow, 1, QtCore.Qt.AlignLeft)


class GenericParam(QtWidgets.QWidget):
    """Generic class to use as parent for parameter classes."""
    def __init__(self, labelText='', value=0, group=None,
                 history=True, labelWidth=80, parent=None):
        super(GenericParam, self).__init__(parent)
        self._group = group
        self._historyEnabled = history
        self._type = None
        self._value = None
        self.labelWidget = QtWidgets.QLabel(labelText)
        self.labelWidget.setObjectName('ParamLabel')
        self.editWidget = None

    def get_type(self):
        return self._type

    def get_label(self):
        return str(self.labelWidget.text())

    def get_group(self):
        return self._group

    def in_group(self, groupName):
        return self._group == groupName

    def history_enabled(self):
        return self._historyEnabled

    def set_enabled(self, enabledStatus):
        """Enable/disable the widget"""
        self.editWidget.setEnabled(enabledStatus)


class StringParam(GenericParam):
    def __init__(self, labelText='', value='', group=None,
                 labelWidth=80, enabled=True, parent=None):
        super().__init__(labelText, value, group,
                         history=False, labelWidth=labelWidth,  parent=parent)
        self._type = 'string'
        if self._historyEnabled:
            raise ValueError('Keeping a history for string parameters is not supported.\n' +
                             'When creating the instance use: history=False')

        # -- Define graphical interface --
        self.editWidget = QtWidgets.QLineEdit()
        self.editWidget.setObjectName('ParamEdit')
        self.set_enabled(enabled)

        # -- Define value --
        self.set_value(value)

    def set_value(self, value):
        self._value = value
        self.editWidget.setText(str(value))

    def get_value(self):
        return str(self.editWidget.text())


class NumericParam(GenericParam):
    def __init__(self, labelText='', value=0, units='', group=None, decimals=None,
                 history=True, labelWidth=80, enabled=True, parent=None):
        super(NumericParam, self).__init__(labelText, value, group,
                                           history, labelWidth,  parent)
        self._type = 'numeric'
        self.decimals = decimals

        # -- Define graphical interface --
        self.editWidget = QtWidgets.QLineEdit()
        self.editWidget.setToolTip('{0}'.format(units))
        self.editWidget.setObjectName('ParamEdit')
        self.set_enabled(enabled)

        # -- Define value --
        self.set_value(value)
        self._units = units

    def set_value(self, value):
        self._value = value
        if self.decimals is not None:
            strFormat = '{{0:0.{0}f}}'.format(self.decimals)
            self.editWidget.setText(strFormat.format(value))
        else:
            self.editWidget.setText(str(value))

    def get_value(self):
        try:
            return int(self.editWidget.text())
        except ValueError:
            return float(self.editWidget.text())

    def get_units(self):
        return self._units

    def add(self, value):
        self.set_value(self.get_value()+value)


class MenuParam(GenericParam):
    def __init__(self, labelText='', menuItems=(), value=0, group=None,
                 history=True, labelWidth=80, enabled=True, parent=None):
        super(MenuParam, self).__init__(labelText, value, group,
                                        history, labelWidth, parent)
        self._type = 'menu'

        # -- Check if spaces in items --
        if ' ' in ''.join(menuItems):
            raise ValueError('MenuParam items cannot contain spaces')

        # -- Define graphical interface --
        self.editWidget = QtWidgets.QComboBox()
        self.editWidget.addItems(menuItems)
        self.editWidget.setObjectName('ParamMenu')

        # -- Define value --
        self._items = menuItems
        self.set_value(value)
        self.set_enabled(enabled)

    def set_value(self, value):
        self._value = value
        self.editWidget.setCurrentIndex(value)

    def set_string(self, newstring):
        # FIXME: graceful warning if wrong string (ValueError exception)
        try:
            value = self._items.index(newstring)
        except ValueError:
            print("'{0}' is not a valid menu item".format(newstring))
            raise
        self._value = value
        self.editWidget.setCurrentIndex(value)

    def get_value(self):
        return self.editWidget.currentIndex()

    def get_string(self):
        return str(self.editWidget.currentText())

    def get_items(self):
        return self._items


# -----------------------------------------------------------------------------

class Message(object):
    """
    Base container for a message.

    It contains the timestamp, the message, and the sender.
    """
    def __init__(self, text):
        self.text = text
        self.timestamp = time.localtime()

    def __str__(self):
        '''String representation of the message'''
        timeString = time.strftime('[%H:%M:%S] ', self.timestamp)
        return '{}{}'.format(timeString, self.text)


class Messenger(QtCore.QObject):
    """
    Class for keeping a log of messages.

    You use it within a QMainWindow by connecting it's signals and slots as follows:
        self.messagebar = messenger.Messenger()
        self.messagebar.timedMessage.connect(self.show_message)
        self.messagebar.collect('Created window')
    where show_message() does something like:
        self.statusBar().showMessage(str(msg))
    """
    timedMessage = QtCore.Signal(str)
    messages = []

    def __init__(self):
        super().__init__()

    @QtCore.Slot(str)
    def collect(self, text):
        newMessage = Message(text)
        Messenger.messages.append(newMessage)
        self.timedMessage.emit(str(newMessage))

    def get_list(self):
        return [str(x) for x in Messenger.messages]

    def __str__(self):
        return '\n'.join(self.get_list())


# -----------------------------------------------------------------------------
def create_app(paradigmClass):
    """
    The paradigm file needs to run something like:
    (app,paradigm) = templates.create_app(Paradigm)
    """
    app = QtWidgets.QApplication.instance()  # checks if QApplication already exists
    if not app:  # create QApplication if it doesnt exist
        app = QtWidgets.QApplication(sys.argv)

    if len(sys.argv) == 1:
        paramfile = None
        paramdictname = None
    elif len(sys.argv) == 2:
        paramfile = rigsettings.DEFAULT_PARAMSFILE
        paramdictname = sys.argv[1]
    elif len(sys.argv) == 3:
        paramfile = sys.argv[1]
        paramdictname = sys.argv[2]
    else:
        raise ValueError('Number of arguments must less than 3')

    if len(sys.argv) > 1:
        paradigm = paradigmClass(paramfile=paramfile, paramdictname=paramdictname)
    else:
        paradigm = paradigmClass()

    paradigm.show()

    # The following line needs to be right before exec_(). It had stopped working in 2023.
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Enable Ctrl-C
    app.exec_()
    return (app, paradigm)


def create_app_only():
    """
    NOT FINISHED
    When using this version, the paradigm file needs to run the following:
        app = templates.create_app_only()
        paradigm = Paradigm()
        paradigm.show()
        app.exec_()
    """
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Enable Ctrl-C
    app = QtWidgets.QApplication.instance()  # checks if QApplication already exists
    if not app:  # create QApplication if it doesnt exist
        app = QtWidgets.QApplication(sys.argv)
    return app


def center_on_screen(widget):
    qr = widget.frameGeometry()
    cp = QtWidgets.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    widget.move(qr.topLeft())
