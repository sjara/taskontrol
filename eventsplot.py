#!/usr/bin/env python

'''
Plot state matrix events and states as they happen.
'''

__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-28'


import sys
from PyQt4 import QtCore 
from PyQt4 import QtGui 
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure



class EventsPlot(QtGui.QWidget):
    '''Plot state matrix events and states as they happen.'''
    def __init__(self, parent=None):
        super(EventsPlot, self).__init__(parent)
        self.setFixedHeight(40)
        self.stateRect = list()
        self.pX = 4                  # Origin X
        self.pY = 1                  # Origin Y
        self.pH = 0.5*self.height()  # Plot Height
        self.pW = self.pWidth()      # Plot Width
        self.labelsY = 0.85*self.height()
        self.xLims = [-15,0]
        self.xLen = self.xLims[1]-self.xLims[0]
        self.xTicks = range(-15,1)

        self._lastStatesOnset  = []
        self._lastStatesOffset = []
        self._lastStatesColor  = []

        self.statesColor = np.array([])
        #colors = [QtCore.Qt.red]


    def setStatesColor(self,newColors):
        self.statesColor = map(QtGui.QColor,newColors)


    def updatePlot(self,timesAndStates,etime):
        '''
        Updates the plot.
        This method expects a numpy array where each row is of the
        form [time, state]
        '''
        # -- Find states to plot --
        earliestTime = etime+self.xLims[0]
        eventsToInclude = timesAndStates[:,0]>=earliestTime
        self._lastStatesOnset = timesAndStates[eventsToInclude,0] - etime
        self._lastStatesOffset = np.r_[self._lastStatesOnset[1:],0]
        #eventsOff = np.r_[timesAndStates[:-1,0]-etime]
        lastStates = timesAndStates[eventsToInclude,1].astype('int')
        #self._lastStatesColor = self.statesColor[lastStates]
        # FIX: there must be a better way!
        self._lastStatesColor = [self.statesColor[s] for s in lastStates]
        self.repaint()


    def paintEvent(self, event):
        self.pW = self.pWidth()      # Update plot width
        painter = QtGui.QPainter()
        painter.begin(self)
        statesOnset = [[-5,0]]
        painter.setPen(QtCore.Qt.NoPen)
        for oneOnset,oneOffset,oneColor in zip(self._lastStatesOnset,
                                               self._lastStatesOnset,
                                               self._lastStatesColor):
            print oneColor.getRgb()
            painter.setBrush(QtGui.QBrush(oneColor))
            (pOnset,pOffset) = map(self.valueToPixel,(oneOnset,oneOffset))
            oneRect = QtCore.QRectF(pOnset,self.pY+1,pOffset-pOnset+1,self.pH-1)
            painter.drawRect(oneRect)
        self.drawAxis(painter)
        painter.end()


    def pWidth(self):
        '''Width of axes in pixels'''
        return self.width()-2*self.pX


    def valueToPixel(self,xval):
        return (float(xval-self.xLims[0])/self.xLen)*self.pW + self.pX


    def drawAxis(self,painter):
        painter.setPen(QtGui.QColor(QtCore.Qt.gray))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRect(self.pX,self.pY,self.pW,self.pH)

        painter.setPen(QtGui.QColor(0,0,0))
        for oneTick in self.xTicks:
            posX = self.valueToPixel(oneTick)
            tickPos = QtCore.QPointF(posX-3,self.labelsY)
            painter.drawText(tickPos, QtCore.QString(str(oneTick)))


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    form = EventsPlot()
    form.show()
    app.exec_()
