"""
Classes for routing messages between modules.
"""

import time
from qtpy import QtCore


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
