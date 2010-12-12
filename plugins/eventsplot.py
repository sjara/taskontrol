#!/usr/bin/env python

'''
Plot state matrix events and states as they happen.
'''

__version__ = '0.0.1'
__author__ = 'Santiago Jaramillo <jara@cshl.edu>'
__created__ = '2009-11-28'


from PyQt4 import QtCore 
from PyQt4 import QtGui 
import numpy as np


class EventsPlot(QtGui.QWidget):
    '''Plot state matrix events and states as they happen.'''
    def __init__(self, parent=None,xlim=[0,10]):
        super(EventsPlot, self).__init__(parent)
        self.setFixedHeight(40)
        self.stateRect = list()
        self.pX = 4                  # Origin X
        self.pY = 1                  # Origin Y
        self.pH = 0.5*self.height()  # Plot Height
        self.pW = self.pWidth()      # Plot Width
        self.labelsY = 0.85*self.height()
        self.xLims = xlim
        self.xLen = self.xLims[1]-self.xLims[0]
        #self.xTicks = range(-10,1)
        self.xTicks = range(self.xLims[0],self.xLims[1])

        self._lastStatesOnset  = []
        self._lastStatesOffset = []
        self._lastStatesColor  = []

        self.statesColor = np.array([])
        #colors = [QtCore.Qt.red]


    def setStatesColor(self,statesColorDict,statesNameToIndex):
        '''
        Set colors for each state.

        statesColorsDict is a dict mapping state names to colors.
        statesNameToIndex is a dict mapping states names to indeces.
        A valid color is a list of 3 elements in the range 0-255
        '''
        self.statesColor = len(statesNameToIndex)*[[0,0,0]]
        for (stateName,color) in statesColorDict.iteritems():
            stateIndex = statesNameToIndex[stateName]
            self.statesColor[stateIndex] = QtGui.QColor(*color)


    def setStatesColorList(self,newColors):
        '''A valid color is a list of 3 elements in the range 0-255'''
        self.statesColor = []
        for color in newColors:
            self.statesColor.append(QtGui.QColor(*color))
 

    def updatePlot(self,timesAndStates,etime):
        '''
        Updates the plot.
        This method expects a numpy array where each row is of the
        form [time, state]
        '''
        # -- Find states to plot --
        earliestTime = etime-self.xLims[1]
        eventsToInclude = timesAndStates[:,0]>=earliestTime
        if sum(eventsToInclude)>0:
            # FIXME: Ugly way of adding an extra state (with onset outside range)
            eventsToInclude = np.r_[eventsToInclude[1:],eventsToInclude[0]] | eventsToInclude
            self._lastStatesOnset = etime - timesAndStates[eventsToInclude,0]
            self._lastStatesOnset[0] = self.xLims[1]
            self._lastStatesOffset = np.r_[self._lastStatesOnset[1:],0]
            lastStates = timesAndStates[eventsToInclude,1].astype('int')
            #self._lastStatesColor = self.statesColor[lastStates]
            # FIXME: there must be a better way!
            self._lastStatesColor = [self.statesColor[s] for s in lastStates]
            self.repaint()
        pass

    def paintEvent(self, event):
        self.pW = self.pWidth()      # Update plot width
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setPen(QtCore.Qt.NoPen)
        for oneOnset,oneOffset,oneColor in zip(self._lastStatesOnset,
                                               self._lastStatesOffset,
                                               self._lastStatesColor):
            painter.setBrush(QtGui.QBrush(oneColor))
            (pOnset,pOffset) = map(self.valueToPixel,(oneOnset,oneOffset))
            oneRect = QtCore.QRectF(pOnset,self.pY+1,pOffset-pOnset,self.pH-1)
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

    import sys
    app = QtGui.QApplication(sys.argv)
    form = EventsPlot()
    form.show()
    app.exec_()
