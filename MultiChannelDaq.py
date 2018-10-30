from Agilent import *
from PowerSupply import *
from numpy import linspace
from random import random
from DetailWindow import DetailWindow
from io import BytesIO
from PyQt5.QtWidgets import QLabel
import json, time
from threading import Thread
from multiprocessing import Process
class MultiChannelDaq(DetailWindow):
    def __init__(self, options):
        super(MultiChannelDaq,self).__init__()
        print(options)
        self.figs=[]
        for i in range(1,5):
            self.figs.append(self.figure.add_subplot(2,2,i))
        self.testPlot()
        self.log("heyi")
        self.show()
        self.child=Thread(target=self.start,args=(options,))
        self.child.start()

    def start(self,options):
        #Connect to instruments
        self.agilent  = Agilent4155C(reset=True)
        #self.keithley = Keithley2657a()
        print(options)
        #Setup their initial configuration
        self.configureAglient(options)
        #self.configureKeithley(options)
        self.collectData(options)
        
    def configureAglient(self, kwargs):
        for i in range(1,5):
            self.agilent.setVoltage(i,0,float(kwargs['comp%d'%i]))
        self.agilent.setMedium()
        self.agilent.setHoldTime(float(kwargs['holdTime']))

    def configureKeithley(self, kwargs):
        #Setting the keithley compliance
        #TODO: Check to see if casting caused errors.
        self.keithley.configure_measurement(1, 0, float(kwargs['kcomp']))

    def collectData(self, kwargs):
        self.log(self.agilent.getCurrent(1,1))
        #self.log(keithley.get_current())
        
    def testPlot(self):
        for fig in self.figs:
            fig.plot([x for x in range(100)],[random() for y in range(100)])

