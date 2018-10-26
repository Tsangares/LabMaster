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

#Value Handler simplifies getting the data from the input fields on the gui.
class ValueHandler():
    def __init__(self):
        self.data={}
    def getSpinBox(self,label):
        self.data[label] = QSpinBox()
        return self.data[label]
    def getLineEdit(self,label):
        self.data[label] = QLineEdit()
        return self.data[label]
    def getData(self):
        output={}
        for key,data in self.data.items():
            output[key]=data.text()
        return output
    def dump(self):
        print(self.getData())
        
#Gui's in general have a lot of boiler plate code.
class Gui():
    def __init__(self):
        self.processes=[]
        self.states=[]
        self.functions=['Read Current', 'Read Voltage']
        self.oracle=ValueHandler()
        self.app = QApplication([])
        self.window = QMainWindow()
        self.toolbar = QToolBar()

        #getWidget is a big function that calls getLayout
        main=self.getWidget("Read Current", self.getCurrentSetup(), self.initDuo)
        #self.getWidget("Read Voltage", self.getVoltageSetup())
        self.buildToolBar(self.toolbar)
        self.window.addToolBar(self.toolbar)
        self.window.setCentralWidget(main)
        self.loadAutosave()
        self.window.show()
        self.app.aboutToQuit.connect(self.exit)
        self.app.exec_()

    def exit(self):
        self.saveSettings(filename=".settings.tmp.json")
        
    def saveSettings(self, filename=".settings.json"):
        saveData=json.dumps(self.oracle.getData())
        with open(filename, "w") as f:
            f.write(saveData)

    def loadSettings(self,filename=".settings.json"):
        data=None
        try:
            with open(filename) as f:
                data=json.loads(f.read())
                f.close()
            if data != None:
                for key,field in self.oracle.data.items():
                    try:
                        self.oracle.data[key].setText(data[key])
                    except KeyError:
                        print("Nothing saved for %s"%key)
                self.setState()
        except json.decoder.JSONDecodeError:
            print("Save file is corrupted, please delete %s"%filename)            
        except FileNotFoundError:
            print("No settings file.")

    def loadAutosave(self):
        self.loadSettings(filename=".settings.tmp.json")
            
    def getToolbarButtons(self):
        out=[]
        for child in self.toolbar.children():
            if type(child) == QWidget:
                for c in child.children():
                    if type(c) == QRadioButton:
                        out.append(c)
        return out
            
    def setState(self):
        state=self.oracle.data['state'].text()
        for btn in self.getToolbarButtons():
            if btn.text() == state:
                print(btn.isChecked())
                btn.toggle()
                print(btn.isChecked())
            
    def getState(self):
        for btn in self.getToolbarButtons():
            if btn.isChecked():
                return btn.text()
        return None

    def storeState(self):
        self.oracle.data['state'].setText(self.getState())

            
    #Toolbar is used to switch between main-widgets/experiments
    def buildToolBar(self, toolbar):
        layout = QHBoxLayout()
        self.oracle.data['state']=QLineEdit()
        for func in self.functions:
            layout.addSpacing(70)
            btn=QRadioButton(func)
            btn.clicked.connect(self.storeState)
            layout.addWidget(btn)
        widget = QWidget()
        widget.setLayout(layout)
        toolbar.addWidget(widget)

    #Converts a dict of <name,key> objects to a form.
    #The `name` is a human readable descriptior,
    # and `key` pulls options from the gui to give to the experiment's code
    def getLayout(self,options):
        layout = QFormLayout()
        keys=[key for key,item in self.oracle.data.items()]
        for opt in options:
            key=opt['key']
            if key in keys:
                print("Handling a duplicate key, %s"%key)
                layout.addRow(QLabel(opt['name']),self.oracle.data[key])
            else:
                layout.addRow(QLabel(opt['name']),self.oracle.getLineEdit(key))
        return layout

    #Generates the fields based on options and sets up the standard buttons.
    def getWidget(self,name,options,action=None):
        #Get options
        layout=self.getLayout(options)

        #Setup buttons
        startBtn=QPushButton('Start')
        powerBtn=QPushButton('Pnower Down')
        saveBtn=QPushButton('Save Configuration')
        loadBtn=QPushButton('Load Autosave')
        if action != None: startBtn.clicked.connect(action)
        saveBtn.clicked.connect(lambda: self.saveSettings())
        loadBtn.clicked.connect(self.loadAutosave)
        layout.addRow(startBtn)
        layout.addRow(powerBtn)
        #layout.addRow(saveBtn)
        #layout.addRow(loadBtn)

        #Create widget
        widget = QWidget()
        widget.setLayout(layout)
        widget.setAccessibleName(name)
        return widget

    #Sourcing voltage to zero and reading current on the Agilent
    #Keithly is used to source voltage set by these options
    def getCurrentSetup(self):
        options=[
            {'name': 'Email', 'key': 'email'},
            {'name': 'Filename', 'key': 'filename'},
            {'name': 'Start Volt', 'key': 'startVolt'},
            {'name': 'End Volt',   'key': 'endVolt'},
            {'name': 'Steps',      'key': 'steps'},
            {'name': 'Keithley Compliance',    'key': 'kcomp'},
            {'name': 'Agilent Hold Time',      'key': 'holdTime'},
            {'name': 'Agilent Measurement Delay',  'key': 'measDelay'},
            {'name': 'Agilent Measurement Time',   'key': 'measTime'},
        ]
        for i in range(1,5):
            options.append({'name': 'Agilent Compliance for Chan %d'%i, 'key': 'comp%d'%i})
        return options

    #Sourcing current to zero and reading voltage on the Agilent
    #Keithly is used to source voltage configured by these options
    def getVoltageSetup(self):
        options=[
            {'name': 'Email', 'key': 'email'},
            {'name': 'Filename', 'key': 'filename'},
            {'name': 'Start Volt', 'key': 'startVolt'},
            {'name': 'End Volt',   'key': 'endVolt'},
            {'name': 'Steps',      'key': 'steps'},
            {'name': 'Keithley Compliance',    'key': 'kcomp'},
            {'name': 'Agilent Hold Time',      'key': 'holdTime'},
            {'name': 'Agilent Measurement Delay',  'key': 'measDelay'},
            {'name': 'Agilent Measurement Time',   'key': 'measTime'},
        ]
        for i in range(1,5):
            options.append({'name': 'Agilent Compliance for Chan %d'%i, 'key': 'comp%d'%i})
        return options

    
    #Connects gui to the experiments code.
    def initDuo(self):
        oracle=self.oracle.getData()
        args=(float(oracle['measDelay']),
               float(oracle['measTime']),
               1,
               float(oracle['holdTime']),
               float(oracle['startVolt']),
               float(oracle['endVolt']),
               int(oracle['steps']),
               "None",
               float(oracle['kcomp']),
               float(oracle['comp1']),
               float(oracle['comp2']),
               float(oracle['comp3']),
               float(oracle['comp4']),
               oracle['email'],
               oracle['filename'])
        p=Thread(target=runDuo, args=args)
        p.start()
        self.processes.append(p)
gui=Gui()

