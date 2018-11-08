# coding: utf-8

import time,threading
import platform as platform
import json
import os.path

from Agilent import AgilentE4980a, Agilent4156
from PowerSupply import PowerSupplyFactory

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt

from LabMaster_save import *
from LabMaster_duo import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from multiprocessing import Process
from threading import Thread
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from Core import MenuWindow
from DetailWindow import DetailWindow
from MultiChannelDaq import MultiChannelDaq as Daq

#TODO: Seperate Gui into a mainmenu and a Gui class.
class MainMenu(MenuWindow):
    onExperiment = pyqtSignal(str)
    def __init__(self):
        #States need to be configured first to setup the toolbar
        states=['Read Current', 'Read Voltage']
        super(MainMenu,self).__init__(states)

        #This setups the fields and buttons
        menu=self.getWidget(self.getCurrentSetup(), action=self.initDuo)
        self.setCentralWidget(menu)

        #This will change the page when the toolbar is perturbed.
        self.calibrateBtn=QPushButton('Max Calibrate')
        self.addStateButton('Read Voltage','Max Calibrate',self.test)

        self.loadAutosave()
        self.show()

    def test(self):
        print("pressed")
        
    #Sourcing voltage to zero and reading current on the Agilent
    #Keithly is used to source voltage set by these options
    def getCurrentSetup(self):
        options=[
            {'name': 'Email', 'key': 'email'},
            {'name': 'Filename', 'key': 'filename'},
            {'name': 'Start Volt (V)', 'key': 'startVolt'},
            {'name': 'End Volt (V)',   'key': 'endVolt'},
            {'name': 'Steps',      'key': 'steps'},
            {'name': 'Keithley Compliance (A)',    'key': 'kcomp'},
            {'name': 'Agilent Hold Time (sec)',      'key': 'holdTime'},
            {'name': 'Agilent Measurement Delay (sec)',  'key': 'measDelay'},
            {'name': 'Agilent Measurement Time (sec)',   'key': 'measTime'},
            {'name': 'Number of Channels (1 or 4)',   'key': 'nChan'},
            {'name': 'Arduino COM port number',   'key': 'com'},
            {'name': 'Average value over N samples', 'key': 'repeat'},
            {'name': 'Resistance (Ohms)', 'key': 'resistance'},
        ]
        for i in range(1,5):
            options.append({'name': 'Agilent Compliance for Chan %d (V)'%i, 'key': 'comp%d'%i})
        return options
    
    #Connects gui to the experiments code.
    def initDuo(self):
        self.statusBar().showMessage("Started Duo!", 2000)
        self.onExperiment.emit("init")

#Gui's in general have a lot of boiler plate code.
class Gui(QApplication):

    def __init__(self):
        super(Gui,self).__init__(['Multi-Channel DAQ'])
        self.window = MainMenu()
        self.window.onExperiment.connect(self.startExperiment)
        self.aboutToQuit.connect(self.window.exit)
        self.exec_()
        
    def startExperiment(self,msg):
        if(msg == 'init'):
            self.window.saveSettings()
            data = self.window.getData()
            self.window.close()
            self.window = Daq(data)
            self.window.onFinish.connect(reset)
    def reset(self):
        self.window = MainMenu()
        self.window.onExperiment.connect(self.startExperiment)
        self.aboutToQuit.connect(self.window.exit)
        
gui=Gui()

