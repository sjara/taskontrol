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

        #self.fig = Figure((5.0, 4.0), dpi=100)
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setFixedSize(200,140)
        self.setMinimumHeight(150)
        self.canvas.setParent(self)
        self.ax = self.canvas.figure.add_subplot(111)
        BGcolorRGB = self.palette().color(QtGui.QPalette.Background).getRgbF()
        self.fig.set_facecolor(BGcolorRGB)
        #self.fig.set_facecolor('None')
         #self.ax.grid()
        #self.canvas.draw()

        self.statesColor = np.array([])

        # -- Set properties of axes and plot --
        self.ax.set_yticks([])
        self.XLim = [-5,0]
        self.ax.set_xlim(self.XLim)
        self.ax.set_xticks(np.arange(self.XLim[0],self.XLim[1]+1,1))

        #timesAndEvents = np.array([ [-1,1],[-2,2],[-4,3] ])

        #self.updatePlot(timesAndEvents)
        self.canvas.draw()


    def setStatesColor(self,statesColor):
        self.statesColor = statesColor


    def updatePlot(self,timesAndStates,etime):
        '''
        Updates the plot.

        This method expects a numpy array where each row is of the
        form [time, state]
        '''
        # -- Find states to plot --
        earliestTime = etime+self.XLim[0]
        eventsToInclude = timesAndStates[:,0]>=earliestTime
        eventsOn = timesAndStates[eventsToInclude,0] - etime
        eventsOff = np.r_[eventsOn[1:],0]
        #eventsOff = np.r_[timesAndStates[:-1,0]-etime]
        lastStates = timesAndStates[eventsToInclude,1].astype('int')
        theseStatesColor = self.statesColor[lastStates]
        #self.ax.cla()
        for eOn,eOff,eCol in zip(eventsOn,eventsOff,theseStatesColor):
            xvals = [eOn,eOn,eOff,eOff]
            yvals = [0,1,1,0]
            statecolor = str(eCol)
            self.ax.fill(xvals,yvals,color=statecolor)
        self.ax.set_yticks([])
        self.ax.set_xlim(self.XLim)
        self.canvas.draw()


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    form = EventsPlot()
    form.show()
    app.exec_()
