"""
This is the beast of the multi-channel reading experiment.
Use DEBUG & KEITHLEY to enable and disable testing & debug
When DEBUG is true, no attempt will be made to access visa/gpib devices.
But to be sure ALWAYS disable KEITHLEY when testing.
Dont kill someone by applying a voltage by accident!

When KEITHLEY=False, no voltage will be applied,
but currents from the agilent will be read.
 - WCW 181127
"""

from queue import Queue
from PowerSupply import *
from Agilent import Agilent4155C
from numpy import linspace
from random import random
from DetailWindow import DetailWindow
from io import BytesIO
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QLabel,QPushButton
import json, time
from threading import Thread
from multiprocessing import Process
import matplotlib.pyplot as plt
from Arduino import Max
from Excel import writeExcel
import statistics as stat
from emailbot import send_mail
DEBUG=True
KEITHLEY=False

def getChan(chan):
    map={
        25:'E' , 24:'2' , 23:'BB', 22:'AA', 21:'W' ,
        20:'6' , 19:'A' , 18:'1' , 17:'24', 16:'19',
        15:'F' , 14:'B' , 13:'12', 12:'23', 11:'V' ,
        10:'7' ,  9:'11',  8:'13',  7:'14',  6:'18',
         5:'H' ,  4:'M' ,  3:'N' ,  2:'P' ,  1:'U' ,
        99: 'pass-empty', 26: 'pass-guard',
    }
    try:
        return 'Ch%s'%int(map[chan])
    except ValueError:
        return map[chan]
    
#All of the main code is put into a seperate thread to allow
#The UI to not freeze and respond to button clicking like Force Shutdown.
class DaqProtocol(QThread):
    newSample = pyqtSignal(tuple)
    onLog = pyqtSignal(tuple)
    onFinish = pyqtSignal(dict)
    onClearPlot = pyqtSignal(str)
    onCalibrationDone = pyqtSignal(str)
    onEmergencyStop = pyqtSignal(str)
    
    def __init__(self,options,widget=None):
        super(DaqProtocol,self).__init__(widget)
        self.options=options
        self.calibration={}
        self.calibrated=False
        self.emergencyStop=False
        self.onEmergencyStop.connect(self.initEmergencyStop)
                                     
    def initEmergencyStop(self,msg=None):
        print("Emergency Stop Initialized")
        self.log("Emergency Stop Initialized")
        self.emergencyStop=True
        
    def log(self,*args):
        self.onLog.emit(args)
        
    def run(self):
        if self.calibrated:
            self.collectData(self.options)
            return
        options=self.options
        #Connect to instruments
        port = 0
        self.arduino=None
        if not DEBUG:
            if KEITHLEY:
                self.keithley = Keithley2657a()
                self.configureKeithley(options)
            self.agilent = Agilent4155C(reset=True)
            self.configureAglient(options)
            self.arduino = Max("COM%s"%options['com'])
        self.log("Starting data collection")
        
        self.log("STARTING CALIBRATION")
        self.calibration=self.aquireLoop(0,None,None,self.options['measTime'],int(self.options['repeat']),self.options['nChan'])[0]
        self.onClearPlot.emit("clear")
        self.log("ENDING CALIBRATION")
        
        self.calibrated=True
        self.onCalibrationDone.emit('done')
        #calculate leakage
            
    def getPoint(self):
        return [random(),random(),random(),random()]

    def configureAglient(self, kwargs):
        self.agilent.setSamplingMode()
        self.agilent.setLong()
        #self.agilent.setShort()
        if int(kwargs['nChan']) < 0 or int(kwargs['nChan']) > 4:
            raise Exception("ERROR: Please set number of channels between 0 and 4!")
        for i in range(1,int(kwargs['nChan'])+1):
            self.agilent.setCurrent(i,0,float(kwargs['comp%d'%i]))
        self.agilent.setMedium()
        self.agilent.setHoldTime(float(kwargs['holdTime']))

    def configureKeithley(self, kwargs):
        #Setting the keithley compliance
        #TODO: Check to see if casting caused errors.
        self.keithley.configure_measurement(1, 0, float(kwargs['kcomp']))

    def getMeasurement(self,samples,duration,channels=None,index=None):
        if DEBUG:
            time.sleep(.2)
            return {"chan%d"%(i+4*index): random()*i for i in range(1,5)}
        agilentData=self.agilent.read(samples,duration)
        agilent={ getChan(channels[int(key[-1])-1]): value[-1] for key,value in agilentData.items() }
        
        if KEITHLEY and index is not None:
            keithley=self.keithley.get_current() #float
            agilent['keithley%d'%index]=keithley
        return agilent

    #collectData    
    def collectData(self, kwargs):
        self.log("Started data collection.".upper())
        print("Started data collection.")
        delay=.1
        startVolt=float(kwargs['startVolt'])
        endVolt=float(kwargs['endVolt'])
        steps=int(kwargs['steps'])
        step=(endVolt-startVolt)/float(steps)
        voltages=list(linspace(startVolt,endVolt,steps+1))
        measured=self.aquireLoop(startVolt,step,endVolt,kwargs['measTime'],1,kwargs['nChan'])
        calculated=[]
        output={'Voltage': voltages}
        #Please note list[::-1] will reverse a list
        for meas in measured[::-1]:
            for chan,volt in meas.items():
                try:
                    output[chan]
                except KeyError:
                    output[chan]=[]
                output[chan].append(volt)
        if not DEBUG and KEITHLEY: self.keithley.powerDownPSU()
        #Possibly calculate leakage later?
        if self.emergencyStop: print("Emergency Stop Successful.")
        self.onFinish.emit(output)


    def getResistance(self,chan=None):
        return float(self.options['resistance'])
    
    def checkCompliance(self,meas):
        return False
    def saveDataToFile(self, data):
        filename=self.options['filename']
        with open('./json/%s.json'%filename ,'w+') as f:
            f.write(json.dumps(data))

    #This is a recursive loop that gathers data & calls itself at the next voltage.
    def aquireLoop(self,volt,step,limit,measTime,repeat=1,nChan=4,delay=.1):
        if self.emergencyStop: return []
        if limit is not None and abs(volt) >= abs(limit):
            self.log("Last voltage measured, ending data collection.")
            return []
        self.log("Setting keithley to %.02e"%volt)
        if limit is not None: self.log("Step is %.02e; while limit is %.02e; currently at %.02e"%(step,limit,volt))
        if not DEBUG and KEITHLEY and limit is not None:
            print("setting Keithley voltage to ", volt)
            self.keithley.set_output(volt)
        time.sleep(float(delay))
        
        switchboard = True
        if(nChan == 1): mode = 'single'
        else: mode = 'group'
        output=[]
        meas = {}
        if switchboard:
            #self.arduino.channel_map
            if mode == 'group':
                if repeat > 1 : self.log("Taking %d measurements on each mux to average."%repeat)
                for mux in range(0,7): #7
                    if self.emergencyStop: return []
                    if not DEBUG: self.arduino.getGroup(mux)
                    channels=Max.reverse_map[mux]
                    self.log("Set mux to %d, reading channels: %s"%(mux,channels))
                    if not DEBUG: time.sleep(1)
                    cache={}
                    for i in range(repeat):
                        if i < repeat and repeat is not 1: self.log("On sample %d out of %d. %2d%%"%(i,repeat,100.0*i/repeat))
                        currentMeas=self.getMeasurement(1,measTime,channels,index=mux)
                        for chan,val in currentMeas.items():
                            try:
                                cache[chan]
                            except KeyError:
                                cache[chan]=[]
                            try:
                                self.calibration[chan]
                            except KeyError:
                                self.calibration[chan]=0
                            if "keithley" in chan:
                                amps=val
                            else:
                                amps=val/self.getResistance(chan)-self.calibration[chan]
                            cache[chan].append(amps)
                            self.log("Chan %s reads %.03e A"%(chan,amps))
                    cache={key: stat.mean(vals) for key,vals in cache.items()}
                    if repeat is 1 and limit is not None: self.newSample.emit((volt,cache))
                    meas={**meas, **cache}
                output.append(meas)
            elif mode == 'single':
                for chan, value in self.arduino.channel_map:
                    self.arduino.getChannel(chan)
                    time.sleep(1)
                    currentMeas=self.getMeasurement(2,measTime)
                    meas={**meas, **currentMeas}
                    self.newSample.emit(currentMeas)
        else:
            meas=self.getMeasurement(2,measTime)
            self.newSample.emit(currentMeas)
            output.append(meas)
        self.saveDataToFile(output)
        if limit is None:
            print("RETURN")
            return output
        elif (limit-volt)/step > 3 and self.checkCompliance(meas):
            print("Compliance congition")
            return self.aquireLoop(volt+step,step,volt+step*2,measTime,repeat,nChan,delay)+output
        else:
            print("Acquisition cycle on volt %.02e ended, continuing..."%float(volt))
            return self.aquireLoop(volt+step,step,limit,measTime,repeat,nChan,delay)+output

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
    onFinish = pyqtSignal(str)
    def __init__(self, options):
        super(MultiChannelDaq,self).__init__()
        #Build number of plots
        #for i in range(1,5):
        #    self.figs.append(self.figure.add_subplot(2,2,i))
        self.fig=self.figure.add_subplot(1,1,1)
        self.show()
        self.options=options
        #Starts the protocol thread
        self.thread=DaqProtocol(options,self.mainWidget)
        self.thread.newSample.connect(self.addPoint)
        self.thread.onLog.connect(self.log)
        self.thread.onClearPlot.connect(self.clearPlot)
        self.thread.onFinish.connect(self.finalizeData)
        self.thread.onCalibrationDone.connect(self.afterCalibration)
        self.thread.start()
        
    def afterCalibration(self,msg=None):
        start=QPushButton("Start")
        self.menuLayout.insertRow(0,start)
        start.clicked.connect(self.startExperiment)
        
    def startExperiment(self,msg=None):
        shutdown=QPushButton("Force Shutdown")
        shutdown.clicked.connect(lambda: self.thread.onEmergencyStop.emit('stop'))
        self.menuLayout.removeRow(0)
        self.menuLayout.insertRow(0,shutdown)
        self.thread.start()
        
    def finalizeData(self,data):
        files=[]
        filename=writeExcel(data,self.options['filename'])
        print("Wrote excel.")
        imgdata = BytesIO()
        self.figure.savefig(imgdata, format='png')
        imgdata.seek(0)
        files.append((imgdata.getbuffer(), "log"))
        print("Saved plot.")
        send_mail(filename,self.options['email'],files=files)
        print("Sent mail.")
        self.onFinish.emit('done')
        self.close()


