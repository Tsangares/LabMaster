from queue import Queue
from PowerSupply import *
from numpy import linspace
from random import random
from DetailWindow import DetailWindow
from io import BytesIO
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QLabel
import json, time
from threading import Thread
from multiprocessing import Process
import matplotlib.pyplot as plt

class DaqProtocol(QThread):
    newSample = pyqtSignal(dict)
    def __init__(self,options,widget=None):
        super(DaqProtocol,self).__init__(widget)
        self.options=options
    def run(self):
        options=self.options
        #Connect to instruments
        ka=(False,False)
        if ka[0]:
            self.keithley = Keithley2657a()
            self.configureKeithley(options)
        if ka[1]:
            self.agilent = Agilent4155C(reset=True)
            self.configureAglient(options)
        #self.log("Starting data collection")
        data=self.collectData(options) #In the format of {'key': [values...]}
        self.dataPoints=[]
        #calculate the current form voltage if using switch board
        #calculate leakage
        #plots
        #send_email(filename,email,files
            
    def getPoint(self):
        return [random(),random(),random(),random()]

    def configureAglient(self, kwargs):
        for i in range(1,5):
            self.agilent.setVoltage(i,0,float(kwargs['comp%d'%i]))
        self.agilent.setMedium()
        self.agilent.setHoldTime(float(kwargs['holdTime']))

    def configureKeithley(self, kwargs):
        #Setting the keithley compliance
        #TODO: Check to see if casting caused errors.
        self.keithley.configure_measurement(1, 0, float(kwargs['kcomp']))

    def getMeasurement(self,samples,duration):
        #For testing
        return {"chan1": random(),"chan2": random(),"chan3": random(),"chan4": random()}
        #Release
        agilent={"chan%d"%key[-1]: value[-1] for key,value in self.agilent.getCurrent(samples,duration).items()} #{'V1': float, ...}
        for key,value in agilent.items():
            if('v' in key.lower() or 'i' in key.lower()):
                print("Failed to properly format measurements")
            else:
                print("Successfully formated measurements")
        keithley=self.keithley.get_current() #float
        agilent['keithley']=keithley
        return agilent
        
    def collectData(self, kwargs):
        #self.log(self.agilent.getCurrent(1,1))
        #self.log(keithley.get_current())
        delay=.1
        startVolt=float(kwargs['startVolt'])
        endVolt=float(kwargs['endVolt'])
        steps=int(kwargs['steps'])+1
        step=(endVolt-startVolt)/steps
        voltages=list(linspace(startVolt,endVolt,steps))
        results=self.aquireLoop(startVolt,step,endVolt,kwargs['measTime'])
        #print("This is the data aquired: ",results)
        #self.keithley.powerDownPSU()
        output={'V': voltages}
        for key,value in results[0].items(): output[key]=[]
        for result in results:
            for key,value in result.items():
                output[key].append(value)
        #Possibly calculate leakage later?
        return output

    def checkCompliance(self,meas):
        return False

    def aquireLoop(self,volt,step,limit,measTime,delay=1):
        #self.keithley.set_output(volt)
        time.sleep(delay)
        meas=self.getMeasurement(2,measTime)
        #meas=self.getPoint()
        self.newSample.emit(meas)
        if volt >= limit:
            return [meas]
        elif (limit-volt)/step > 3 and self.checkCompliance(meas):
            return self.aquireLoop(volt+step,step,volt+step*2,measTime)+[meas]
        else:
            return self.aquireLoop(volt+step,step,limit,measTime)+[meas]
    
    #returns the second item in this weird format.
    def skipMeasurements(result, skip):
        
        output={}
        for key in result:
            currents=result[key][skip:]
            if len(currents) == 1:
                output[key]=currents[0]
            else:
                output[key]=currents
        return output


#Just a window now.
class MultiChannelDaq(DetailWindow):
    def __init__(self, options):
        super(MultiChannelDaq,self).__init__()
        #Build number of plots
        for i in range(1,5):
            self.figs.append(self.figure.add_subplot(2,2,i))
        self.show()
        
        #Starts the protocol thread
        self.thread=DaqProtocol(options,self.mainWidget)
        self.thread.newSample.connect(self.addPoint)
        self.thread.start()


