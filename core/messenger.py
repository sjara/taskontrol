#!/usr/bin/env python

'''
Class for routing messages between modules.
'''


__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-12-30'

import time
from PyQt4 import QtCore 

class Message(object):
    '''
    Base container for a message.

    It contains the timestamp, the message and the sender.
    '''
    def __init__(self,text,sender=''):
        self.text=text
        self.timestamp=time.localtime()
        self.sender=sender
    def __str__(self):
        '''String representation of the message'''
        timeString = time.strftime('[%H:%M:%S] ',self.timestamp)
        if self.sender:   # If not empty, format the string
            senderString = '<%s> '%self.sender
        else:             # If empty don't print anything
            senderString = ''
        return '%s%s%s'%(timeString,senderString,self.text)


class Messenger(object):
    '''
    Class for routing messages between modules.

    Maybe use Singleton or Borg pattern to keep track of messages:
    http://code.activestate.com/recipes/66531/
    '''
    messages = []
    emitter = QtCore.QObject()

    def __init__(self):
        pass

    @staticmethod
    def send(text,sender=''):
        newMessage = Message(text,sender)
        Messenger.messages.append(newMessage)
        Messenger.emitter.emit(QtCore.SIGNAL('NewMessage'), newMessage)


if __name__ == "__main__":

    onemsg = Message('My short message')
    print onemsg
 
    mess1 = Messenger()
    mess1.send('One message')

    mess2 = Messenger()
    mess2.send('Another message')

