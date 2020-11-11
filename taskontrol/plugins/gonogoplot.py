'''
Plugin to plot go/no-go trials.
'''


__version__ = '0.1'
__author__ = 'Santiago Jaramillo <sjara@uoregon.edu>'
__created__ = '2018-04-05'

import sys
if sys.platform=='darwin':
    from qtpy import QtWidgets
    from qtpy import QtGui
    from qtpy import QtCore
else:
    from PySide import QtGui as QtWidgets
    from PySide import QtGui
    from PySide import QtCore
import numpy as np
import pyqtgraph as pg

def set_pg_colors(form):
    '''Set default BG and FG color for pyqtgraph plots.'''
    #bgColorRGBA = form.palette().color(QtGui.QPalette.ColorRole.Window) ### OLD
    #fgColorRGBA = form.palette().color(QtGui.QPalette.ColorRole.WindowText) ### OLD
    bgColorRGBA = form.palette().color(QtGui.QPalette.Window)
    fgColorRGBA = form.palette().color(QtGui.QPalette.WindowText)
    pg.setConfigOption('background', bgColorRGBA)
    pg.setConfigOption('foreground', fgColorRGBA)
    pg.setConfigOptions(antialias=True)  ## this will be expensive for the local plot
    #pg.setConfigOptions(antialias=False)  ##

class GoNoGoPlot(pg.PlotWidget):
    '''
    Plot for change detection go/no-go task.
    '''
    def __init__(self, parent=None, widgetSize=(200,100),nTrials=100):
        super(GoNoGoPlot, self).__init__(parent)
        self.initialSize = widgetSize

        self.nTrialsToPlot = nTrials
        self.trialsToPlot = np.arange(self.nTrialsToPlot)

        self.mainPlot = pg.ScatterPlotItem(size=4, symbol='o', pxMode=True)
        self.addItem(self.mainPlot)

        self.outcomeIDs = {'hit':1, 'miss':2, 'falseAlarm':3,'correctRejection':4,
                           'earlyStop':5, 'freeReward':6, 'aborted':7}

        # -- Graphical adjustments --
        yAxis = self.getAxis('left')
        #self.setLabel('left', 'Reward\nport') #units='xxx'
        self.setLabel('bottom', 'Trial')
        self.setLabel('left', 'Time')
        self.setXRange(0, self.nTrialsToPlot)
        self.setYRange(-0.2, 4)
        yAxis.setTicks([[[0,'0'],[1,'1']]])

    def make_pens(self, points):
        '''
        points should be a list of tuples of the form [ntrials,'colorname']
        '''
        pensList = []
        brushesList = []
        for item in points:
            pensList.append(item[0]*[ pg.mkPen(item[1]) ])
            brushesList.append(item[0]*[ pg.mkBrush(item[1]) ])
        self.pens = np.concatenate(pensList)
        self.brushes = np.concatenate(brushesList)

    def update(self,targetTimes=[],outcome=[],currentTrial=0):
        xd = np.tile(range(self.nTrialsToPlot),3)
        maxPastTrials = (self.nTrialsToPlot*2)//3
        minTrial = max(0,currentTrial-maxPastTrials)
        xPastTrials = np.arange(minTrial,currentTrial)
        xTimes = np.arange(currentTrial,minTrial+self.nTrialsToPlot)
        xHit = np.flatnonzero(outcome[xPastTrials]==self.outcomeIDs['hit'])+minTrial
        xMiss = np.flatnonzero(outcome[xPastTrials]==self.outcomeIDs['miss'])+minTrial
        '''
        xInvalid = np.flatnonzero(outcome[xPastTrials]==self.outcomeIDs['falseAlarm'])+minTrial
        xFree = np.flatnonzero(outcome[xPastTrials]==self.outcomeIDs['correctRejection'])+minTrial
        xNoChoice = np.flatnonzero(outcome[xPastTrials]==self.outcomeIDs['earlyStop'])+minTrial
        xAfterError = np.flatnonzero(outcome[xPastTrials]==self.outcomeIDs['aftererror'])+minTrial
        xAborted = np.flatnonzero(outcome[xPastTrials]==self.outcomeIDs['aborted'])+minTrial
        xAll = np.concatenate((xSide,xCorrect,xError,xInvalid,xFree,xNoChoice,xAfterError,xAborted))
        '''
        xAll = np.concatenate((xTimes,xHit,xMiss))
        yAll = targetTimes[xAll]
        green=(0,212,0)
        gray = 0.75
        pink = (255,192,192)
        '''
        self.make_pens([ [len(xSide),'b'], [len(xCorrect),green], [len(xError),'r'],
                         [len(xInvalid),gray], [len(xFree),'c'], [len(xNoChoice),'w'],
                         [len(xAfterError),pink],[len(xAborted),'k']])
        '''
        self.make_pens([ [len(xTimes),'b'], [len(xHit),green], [len(xMiss),'r'] ])
        self.mainPlot.setData(x=xAll, y=yAll, pen=self.pens, brush=self.brushes)
        self.setXRange(minTrial, minTrial+self.nTrialsToPlot)
        #print minTrial, minTrial+self.nTrialsToPlot ### DEBUG

    def sizeHint(self):
        return QtCore.QSize(self.initialSize[0],self.initialSize[1])

###### FINISH THIS ########


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Enable Ctrl-C
    import sys

    # -- A workaround to enable re-running the app in ipython after closing --
    app=QtWidgets.QApplication.instance() # checks if QApplication already exists
    if not app: # create QApplication if it doesnt exist
        app = QtWidgets.QApplication(sys.argv)
    form = QtWidgets.QDialog()
    form.resize(600,240)
    set_pg_colors(form)

    ntrials = 1000
    splot = GoNoGoPlot(nTrials=50)
    #xd=np.arange(ntrials);
    #targetTimes = np.random.randint(0,2,ntrials)
    targetTimes = 2*np.random.rand(ntrials) + 1
    outcome = np.random.randint(1,3,ntrials)
    splot.update(targetTimes,outcome,currentTrial=90)
    layoutMain = QtWidgets.QHBoxLayout()
    layoutMain.addWidget(splot)
    form.setLayout(layoutMain)
    form.show()
    app.exec_()
