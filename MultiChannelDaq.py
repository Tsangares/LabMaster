from queue import Queue
from PowerSupply import *
from Agilent import Agilent4155C
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
from Arduino import Max
DEBUG=True
KEITHLEY=False
def getChan(chan):
    map={
        25:'E' , 24:'2' , 23:'BB', 22:'AA', 21:'W' ,
        20:'6' , 19:'A' , 18:'1' , 17:'24', 16:'19',
        15:'F' , 14:'B' , 13:'12', 12:'23', 11:'V' ,
        10:'7' ,  9:'11',  8:'13',  7:'14',  6:'18',
         5:'H' ,  4:'M' ,  3:'N' ,  2:'P' ,  1:'U' ,
    }
    return map[chan]

class DaqProtocol(QThread):
    newSample = pyqtSignal(dict)
    onLog = pyqtSignal(str)
    def __init__(self,options,widget=None):
        super(DaqProtocol,self).__init__(widget)
        self.options=options

    def log(self,string):
        self.onLog.emit(str(string))
        
    def run(self):
        options=self.options
        #Connect to instruments
        port = 0
        self.arduino=None
        if not DEBUG:
            if KEITHLEY: self.keithley = Keithley2657a()
            if KEITHLEY: self.configureKeithley(options)
            self.agilent = Agilent4155C(reset=True)
            self.configureAglient(options)
            self.arduino = Max(port)
        self.log("Starting data collection")
        data=self.collectData(options) #In the format of {'key': [values...]}
        self.dataPoints=[]
        #calculate the current form voltage if using switch board
        #calculate leakage
        #plots
        #send_email(filename,email,files
            
    def getPoint(self):
        return [random(),random(),random(),random()]

    def configureAglient(self, kwargs):
        if kwargs['nChan'] < 0 or kwargs['nChan'] > 4:
            raise Exception("ERROR: Please set number of channels between 0 and 4!")
        for i in range(1,kwargs['nChan']+1):
            self.agilent.setCurrent(i,0,float(kwargs['comp%d'%i]))
        self.agilent.setMedium()
        self.agilent.setHoldTime(float(kwargs['holdTime']))

    def configureKeithley(self, kwargs):
        #Setting the keithley compliance
        #TODO: Check to see if casting caused errors.
        self.keithley.configure_measurement(1, 0, float(kwargs['kcomp']))

    def getMeasurement(self,samples,duration,prefix=0):
        #For testing
        if DEBUG:
            return {"chan%d"%(i+prefix): random()*i for i in range(1,5)}
        #Release
        agilent={"chan%s"%(key[-1]+prefix): value[-1] for key,value in self.agilent.read(samples,duration).items()} #{'V1': float, ...}
        for key,value in agilent.items():
            if('v' in key.lower() or 'i' in key.lower()):
                print("Failed to properly format measurements")
        if KEITHLEY:
            keithley=self.keithley.get_current() #float
            agilent['keithley%d'%prefix]=keithley
        return agilent
        
    def collectData(self, kwargs):
        delay=.1
        startVolt=float(kwargs['startVolt'])
        endVolt=float(kwargs['endVolt'])
        steps=int(kwargs['steps'])+1
        step=(endVolt-startVolt)/steps
        voltages=list(linspace(startVolt,endVolt,steps))
        results=self.aquireLoop(startVolt,step,endVolt,kwargs['measTime'])
        #print("This is the data aquired: ",results)
        if not DEBUG and KEITHLEY: self.keithley.powerDownPSU()
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
        self.log("Setting keithley to %.02e"%volt)
        self.log("Step is %.02e; while limit is %.02e"%(step,limit))
        if not DEBUG and KEITHLEY: self.keithley.set_output(volt)
        time.sleep(delay)
        
        switchboard = False
        meas = {}
        if switchboard:
            #self.arduino.channel_map
            for chan, value in self.arduino.channel_map:
                self.arduino.getChannel(chan)
                time.sleep(1)
                currentMeas=self.getMeasurement(2,measTime,offset=chan)
                meas={**meas, **currentMeas}
        else:
            meas=self.getMeasurement(2,measTime)
            
        self.newSample.emit(meas) #Plotting
        if abs(volt) >= abs(limit):
            self.log("Last voltage measured, ending data collection.")
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
        #for i in range(1,5):
        #    self.figs.append(self.figure.add_subplot(2,2,i))
        self.fig=self.figure.add_subplot(1,1,1)
        self.show()
        
        #Starts the protocol thread
        self.thread=DaqProtocol(options,self.mainWidget)
        self.thread.newSample.connect(self.addPoint)
        self.thread.onLog.connect(self.log)
        self.thread.start()


