"""
Templates for standard paradigms.

NOTE: while using templates has the advantage of having to write less code
      for your paradigm, it obscures some of the methods and attributes,
      so make sure you check your template before using it.
"""

import sys
from qtpy import QtWidgets
from qtpy import QtCore
from taskontrol import rigsettings
from taskontrol import dispatcher
from taskontrol import statematrix
from taskontrol import savedata
from taskontrol import paramgui
from taskontrol import utils
from taskontrol.plugins import manualcontrol
from taskontrol.plugins import sidesplot


class ParadigmTest(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(ParadigmTest, self).__init__(parent)
        self.myvar=0


class ParadigmMinimal(QtWidgets.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(ParadigmMinimal, self).__init__(parent)

        self.name = 'minimal'
        smServerType = rigsettings.STATE_MACHINE_TYPE

        # -- Create an empty statematrix --
        self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                          outputs=rigsettings.OUTPUTS,
                                          readystate='ready_next_trial')

        # -- Create dispatcher --
        self.dispatcherModel = dispatcher.Dispatcher(serverType=smServerType,interval=0.1)
        self.dispatcherView = dispatcher.DispatcherGUI(model=self.dispatcherModel)

        # -- Add graphical widgets to main window --
        self.centralWidget = QtWidgets.QWidget()
        layoutMain = QtWidgets.QVBoxLayout()
        layoutMain.addWidget(self.dispatcherView)

        self.centralWidget.setLayout(layoutMain)
        self.setCentralWidget(self.centralWidget)

        # -- Connect signals from dispatcher --
        self.dispatcherModel.prepareNextTrial.connect(self.prepare_next_trial)

    def prepare_next_trial(self, nextTrial):
        pass

    def _timer_tic(self,etime,lastEvents):
        pass

    def closeEvent(self, event):
        '''Executed when closing the main window. Inherited from QtWidgets.QMainWindow.'''
        self.dispatcherModel.die()
        event.accept()


class Paradigm2AFC(QtWidgets.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(Paradigm2AFC, self).__init__(parent)

        self.name = '2afc'
        smServerType = rigsettings.STATE_MACHINE_TYPE

        # -- Sides plot --
        sidesplot.set_pg_colors(self)
        self.mySidesPlot = sidesplot.SidesPlot(nTrials=120)

        # -- Module for saving data --
        self.saveData = savedata.SaveData(rigsettings.DATA_DIR, remotedir=rigsettings.REMOTE_DIR)

        # -- Create an empty state matrix --
        self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                          outputs=rigsettings.OUTPUTS,
                                          readystate='readyForNextTrial')

        # -- Add parameters --
        self.params = paramgui.Container()
        self.params['trainer'] = paramgui.StringParam('Trainer (initials)',
                                                      value='',
                                                      group='Session info')
        self.params['experimenter'] = paramgui.StringParam('Experimenter',
                                                           value='experimenter',
                                                           group='Session info')
        self.params['subject'] = paramgui.StringParam('Subject',value='subject',
                                                      group='Session info')
        self.sessionInfo = self.params.layout_group('Session info')

        # -- Create dispatcher --
        self.dispatcherModel = dispatcher.Dispatcher(serverType=smServerType,interval=0.1)
        self.dispatcherView = dispatcher.DispatcherGUI(model=self.dispatcherModel)

        # -- Connect to sound server and define sounds --
        # FINISH

        # -- Manual control of outputs --
        self.manualControl = manualcontrol.ManualControl(self.dispatcherModel.statemachine)

        # -- Add graphical widgets to main window --
        self.centralWidget = QtWidgets.QWidget()
        layoutMain = QtWidgets.QVBoxLayout()
        layoutTop = QtWidgets.QVBoxLayout()
        layoutBottom = QtWidgets.QHBoxLayout()
        layoutCol1 = QtWidgets.QVBoxLayout()
        layoutCol2 = QtWidgets.QVBoxLayout()


        layoutMain.addLayout(layoutTop)
        #layoutMain.addStretch()
        layoutMain.addSpacing(0)
        layoutMain.addLayout(layoutBottom)

        layoutTop.addWidget(self.mySidesPlot)

        layoutBottom.addLayout(layoutCol1)
        layoutBottom.addLayout(layoutCol2)

        layoutCol1.addWidget(self.saveData)
        layoutCol1.addWidget(self.sessionInfo)
        layoutCol1.addWidget(self.dispatcherView)

        layoutCol2.addWidget(self.manualControl)
        layoutCol2.addStretch()

        self.centralWidget.setLayout(layoutMain)
        self.setCentralWidget(self.centralWidget)

        # -- Center in screen --
        self._center_in_screen()

        # -- Add variables storing results --
        self.results = utils.EnumContainer()

        # -- Connect signals from dispatcher --
        self.dispatcherModel.prepareNextTrial.connect(self.prepare_next_trial)
        self.dispatcherModel.timerTic.connect(self._timer_tic)

        # -- Connect messenger --
        self.messagebar = paramgui.Messenger()
        self.messagebar.timedMessage.connect(self._show_message)
        self.messagebar.collect('Created window')

        # -- Connect signals to messenger
        self.saveData.logMessage.connect(self.messagebar.collect)
        self.dispatcherModel.logMessage.connect(self.messagebar.collect)

        # -- Connect other signals --
        self.saveData.buttonSaveData.clicked.connect(self.save_to_file)

        #### -- Prepare first trial --
        ### self.prepare_next_trial(0) # It cannot be called until one defines params

    def _show_message(self,msg):
        self.statusBar().showMessage(str(msg))
        print(msg)

    def _center_in_screen(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _timer_tic(self,etime,lastEvents):
        pass

    def save_to_file(self):
        '''Triggered by button-clicked signal'''
        '''NOTE: if we want to use folders for each experimenter,
                 the code would need to have:
                 experimenter=self.params['experimenter'].get_value()'''
        self.saveData.to_file([self.params, self.dispatcherModel,
                               self.sm, self.results],
                              self.dispatcherModel.currentTrial,
                              experimenter='',
                              subject=self.params['subject'].get_value(),
                              paradigm=self.name)

    def prepare_next_trial(self, nextTrial):
        pass

    def closeEvent(self, event):
        '''
        Executed when closing the main window.
        This method is inherited from QtWidgets.QMainWindow, which explains
        its camelCase naming.
        '''
        #print 'ENTERED closeEvent()' # DEBUG
        #print 'Closing all connections.' # DEBUG
        #self.soundClient.shutdown()
        self.dispatcherModel.die()
        event.accept()

'''
    def set_state_matrix(self,nextCorrectChoice):
        pass
'''


class ParadigmGoNoGo(QtWidgets.QMainWindow):
    def __init__(self, parent=None, paramfile=None, paramdictname=None):
        super(ParadigmGoNoGo, self).__init__(parent)

        self.name = 'go-nogo'
        smServerType = rigsettings.STATE_MACHINE_TYPE

        # -- Sides plot --
        #sidesplot.set_pg_colors(self)
        #self.mySidesPlot = sidesplot.SidesPlot(nTrials=120)

        # -- Module for saving data --
        self.saveData = savedata.SaveData(rigsettings.DATA_DIR, remotedir=rigsettings.REMOTE_DIR)

        # -- Create an empty state matrix --
        self.sm = statematrix.StateMatrix(inputs=rigsettings.INPUTS,
                                          outputs=rigsettings.OUTPUTS,
                                          readystate='readyForNextTrial')

        # -- Add parameters --
        self.params = paramgui.Container()
        self.params['trainer'] = paramgui.StringParam('Trainer (initials)',
                                                      value='',
                                                      group='Session info')
        self.params['experimenter'] = paramgui.StringParam('Experimenter',
                                                           value='experimenter',
                                                           group='Session info')
        self.params['subject'] = paramgui.StringParam('Subject',value='subject',
                                                      group='Session info')
        self.sessionInfo = self.params.layout_group('Session info')

        # -- Create dispatcher --
        self.dispatcherModel = dispatcher.Dispatcher(serverType=smServerType,interval=0.1)
        self.dispatcherView = dispatcher.DispatcherGUI(model=self.dispatcherModel)

        # -- Manual control of outputs --
        self.manualControl = manualcontrol.ManualControl(self.dispatcherModel.statemachine)

        # -- Add graphical widgets to main window --
        self.centralWidget = QtWidgets.QWidget()
        layoutMain = QtWidgets.QVBoxLayout()
        layoutTop = QtWidgets.QVBoxLayout()
        layoutBottom = QtWidgets.QHBoxLayout()
        layoutCol1 = QtWidgets.QVBoxLayout()
        layoutCol2 = QtWidgets.QVBoxLayout()


        layoutMain.addLayout(layoutTop)
        #layoutMain.addStretch()
        layoutMain.addSpacing(0)
        layoutMain.addLayout(layoutBottom)

        #layoutTop.addWidget(self.mySidesPlot)

        layoutBottom.addLayout(layoutCol1)
        layoutBottom.addLayout(layoutCol2)

        layoutCol1.addWidget(self.saveData)
        layoutCol1.addWidget(self.sessionInfo)
        layoutCol1.addWidget(self.dispatcherView)

        layoutCol2.addWidget(self.manualControl)
        layoutCol2.addStretch()

        self.centralWidget.setLayout(layoutMain)
        self.setCentralWidget(self.centralWidget)

        # -- Center in screen --
        self._center_in_screen()

        # -- Add variables storing results --
        self.results = utils.EnumContainer()

        # -- Connect signals from dispatcher --
        self.dispatcherModel.prepareNextTrial.connect(self.prepare_next_trial)
        self.dispatcherModel.timerTic.connect(self._timer_tic)

        # -- Connect messenger --
        self.messagebar = paramgui.Messenger()
        self.messagebar.timedMessage.connect(self._show_message)
        self.messagebar.collect('Created window')

        # -- Connect signals to messenger
        self.saveData.logMessage.connect(self.messagebar.collect)
        self.dispatcherModel.logMessage.connect(self.messagebar.collect)

        # -- Connect other signals --
        self.saveData.buttonSaveData.clicked.connect(self.save_to_file)

        #### -- Prepare first trial --
        ### self.prepare_next_trial(0) # It cannot be called until one defines params

    def _show_message(self,msg):
        self.statusBar().showMessage(str(msg))
        print(msg)

    def _center_in_screen(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _timer_tic(self,etime,lastEvents):
        pass

    def save_to_file(self):
        '''Triggered by button-clicked signal'''
        self.saveData.to_file([self.params, self.dispatcherModel,
                               self.sm, self.results],
                              self.dispatcherModel.currentTrial,
                              experimenter='',
                              subject=self.params['subject'].get_value(),
                              paradigm=self.name)

    def prepare_next_trial(self, nextTrial):
        pass

    def closeEvent(self, event):
        '''
        Executed when closing the main window.
        This method is inherited from QtWidgets.QMainWindow, which explains
        its camelCase naming.
        '''
        #print 'ENTERED closeEvent()' # DEBUG
        #print 'Closing all connections.' # DEBUG
        #self.soundClient.shutdown()
        self.dispatcherModel.die()
        event.accept()

'''
    def set_state_matrix(self,nextCorrectChoice):
        pass
'''
