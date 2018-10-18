# coding: utf-8

import time,threading
import platform as platform

from Agilent import AgilentE4980a, Agilent4156
from PowerSupply import PowerSupplyFactory

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt

from LabMaster_save import *
from LabMaster_duo import *
from PyQt5.QtWidgets import *
from multiprocessing import Process
from multiprocessing import Process
from threading import Thread

# These are helper functions that are common GUI objects.
# makeEntry is a text label and a string input
def makeEntry(fig,title,var,row):
    obj = Label(fig, text=title)
    obj.grid(row=row, column=1)
    if var is None: var=StringVar(root, "0")
    obj = Entry(fig, textvariable=var)
    obj.grid(row=row, column=2)

# makeUnitEntry is a Label, Entry box, then a another label showing the specified untis
def makeUnitEntry(fig,title,var,row,unit):
    makeEntry(fig,title,var,row)
    obj = Label(fig, text=unit)
    obj.grid(row=row, column=3)

# makeUnitsEntry is the same at make Unit Entry but allows custom units.
def makeUnitsEntry(fig,title,var,row,units,scale):
    makeEntry(fig,title,var,row)
    scale.set(list(units)[0])
    obj = OptionMenu(fig, scale, *units)
    obj.grid(row=row, column=3)

# Since most experiments use a common configuration setup, here is an object containing them. Any other experiment specific runs should be specified outside of this object.
class Settings:
    def __init__(self,notebook):
        self.start_volt=StringVar(root,"0")
        self.end_volt = StringVar(root,"100")
        self.step_volt = StringVar(root,"5")
        self.hold_time = StringVar(root,"1")
        self.compliance = StringVar(root,"1") 
        self.recipients = StringVar(root,"adapbot@gmail.com")   
        self.compliance_scale = StringVar()
        self.source_choice = StringVar()
        self.figure=ttk.Frame(notebook)

    def buildLabels(self, start=True, end=True, step=True, hold=True, compliance=True):
        if start: makeUnitEntry(self.figure,"Start Volt", self.start_volt, 1, "V")
        if end:   makeUnitEntry(self.figure,"End Volt",   self.end_volt,   2, "V")
        if step:  makeUnitEntry(self.figure,"Step Volt",  self.step_volt,  3, "V")
        if hold:  makeUnitEntry(self.figure,"Hold Time",  self.hold_time,  4, "s")
        if compliance: makeUnitsEntry(self.figure,"Compliance", self.compliance, 5, {'mA', 'uA', 'nA'}, self.compliance_scale)

# This is the mess of a GUI        
class GuiPart:
    def __init__(self):
        print("Interface Generating")
        n = ttk.Notebook(root,width=800)
        n.grid(row=0, column=0, columnspan=100, rowspan=100, sticky='NESW')
        print("Checkpoint c")
        #Setting the settings for duo
        self.duo = Settings(n)
        self.duo.filename=StringVar(root, "happy")
        self.duo.steps=StringVar(root, "1")
        self.duo.delay=StringVar(root, "0")
        self.duo.measureTime=StringVar(root, "0")
        self.duo.samples=StringVar(root, "10")
        self.duo.integration=StringVar(root, "None")
        self.duo.keithley_compliance=StringVar(root, "0")
        self.duo.agilent_compliance1=StringVar(root, "0")
        self.duo.agilent_compliance2=StringVar(root, "0")
        self.duo.agilent_compliance3=StringVar(root, "0")
        self.duo.agilent_compliance4=StringVar(root, "0")

        #Build Gui components
        self.f1=self.duo.figure
        self.duo.buildLabels(compliance=False,hold=False,step=False)
        makeEntry(self.duo.figure, "Email",self.duo.recipients,3)
        makeEntry(self.duo.figure, "Filename (omit .xlsx)",self.duo.filename,4)
        makeUnitEntry(self.duo.figure, "Number of Steps",self.duo.steps,5,"# of Steps")
        makeUnitEntry(self.duo.figure, "Measurement Delay",self.duo.delay,6,"secconds")
        makeUnitEntry(self.duo.figure, "Agilent Measuring Time",self.duo.measureTime,7,"secconds")
        makeUnitEntry(self.duo.figure, "Agilent Hold Time",self.duo.hold_time,8,"secconds")
        #makeUnitEntry(self.duo.figure, "Agilent Samples",self.duo.samples,6,"# of samples")
        makeUnitEntry(self.duo.figure, "Keithley Compliance",self.duo.keithley_compliance,9, "mA")
        makeUnitEntry(self.duo.figure, "Agilent Comp. Chan 1",self.duo.agilent_compliance1,10, "mA")
        makeUnitEntry(self.duo.figure, "Agilent Comp. Chan 2",self.duo.agilent_compliance2,11, "mA")
        makeUnitEntry(self.duo.figure, "Agilent Comp. Chan 3",self.duo.agilent_compliance3,12, "mA")
        makeUnitEntry(self.duo.figure, "Agilent Comp. Chan 4",self.duo.agilent_compliance4,13, "mA")
        Button(self.duo.figure, text="Save Configuation", command=self.saveSettings).grid(row=18,column=2)
        Button(self.duo.figure, text="Start", command=self.prepDuo).grid(row=16,column=2)
        Button(self.duo.figure, text="Stop", command=stopDuo).grid(row=17,column=2)
        
        
        n.add(self.duo.figure, text="Duo IV")
        print("Interface Generated")
        loadSettings(self)
     
    def quit(self):
        print("placing order")
        self.stop.put("random")
        self.stop.put("another random value")

    def prepDuo(self):
        obj=self.duo
        runDuo(float(obj.delay.get()),
                      float(obj.measureTime.get()),
                      float(obj.samples.get()),
                      float(obj.hold_time.get()),
                      float(obj.start_volt.get()),
                      float(obj.end_volt.get()),
                      int(obj.steps.get()),
                      obj.integration.get(),
                      float(obj.keithley_compliance.get())/1000,
                      float(obj.agilent_compliance1.get())/1000,
                      float(obj.agilent_compliance2.get())/1000,
                      float(obj.agilent_compliance3.get())/1000,
                      float(obj.agilent_compliance4.get())/1000,
                      obj.recipients.get(),
                      obj.filename.get())

    def saveSettings(self):
        settings={
            'duo': getDuoSettings(self),
            'cv': getCVSettings(self),
            'iv': None
        }       
        try:
            with open(SAVE_FILE, 'w+') as f:
                f.write(json.dumps(settings))
                print('Settings saved in the file %s'%SAVE_FILE)
        except Exception as e:
            print(e)


#root = Tk()
#root.geometry('800x800')
#root.title('LabMaster')
#GUI=GuiPart()

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
        
class Gui:
    def __init__(self):
        self.processes=[]
        self.app = QApplication([])
        self.window = QWidget()
        self.oracle=ValueHandler()
        self.layout = QFormLayout()
        self.buildDuo(self.oracle)
        self.window.setLayout(self.layout)
        self.window.show()
        self.app.exec_()
        
    def buildDuo(self,oracle):
        #build data inputs
        self.layout.addRow(QLabel('Email'),      oracle.getLineEdit('email'))
        self.layout.addRow(QLabel('Filename'),   oracle.getLineEdit('filename'))
        self.layout.addRow(QLabel('Start Volt'), oracle.getSpinBox('startVolt'))
        self.layout.addRow(QLabel('End Volt'),   oracle.getSpinBox('endVolt'))
        self.layout.addRow(QLabel('Steps'),      oracle.getSpinBox('steps'))
        self.layout.addRow(QLabel('Keithley Compliance'),    oracle.getSpinBox('kcomp'))
        self.layout.addRow(QLabel('Agilent Hold Time'),      oracle.getSpinBox('holdTime'))
        self.layout.addRow(QLabel('Agilent Measurement Delay'),  oracle.getSpinBox('measDelay'))
        self.layout.addRow(QLabel('Agilent Measurement Time'),   oracle.getSpinBox('measTime'))
        for i in range(1,5):
            self.layout.addRow(QLabel('Agilent Compliance for Chan %d'%i),oracle.getSpinBox('comp%d'%i))

        #build buttons
        startBtn=QPushButton('Start')
        powerBtn=QPushButton('Power Down')
        saveBtn=QPushButton('Save Configuration')
        startBtn.clicked.connect(self.initDuo)
        self.layout.addRow(startBtn)
        self.layout.addRow(powerBtn)
        self.layout.addRow(saveBtn)

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
