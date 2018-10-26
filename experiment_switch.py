from Agilent import *
from PowerSupply import *
from numpy import linspace
import time
from time import sleep
import logging
import matplotlib.pyplot as plt
from threading import Thread
from LabMaster_plotting import *
from emailbot import *
import urllib, base64
import json
from io import BytesIO
_currentV=None
stop=False

def skipMeasurements(result, skip):
    output={}
    for key in result:
        currents=result[key][skip:]
        if len(currents) == 1:
            output[key]=currents[0]
        else:
            output[key]=currents
    return output

def averageCurrent(result):
    output={}
    for key in result:
        currents=result[key][1:]
        output[key]=sum(currents)/len(currents)
    return output

def startSwitch():
    runSwitch(delay,measureTime,samples,holdTime,startV,endV,steps,integration,keithley_comp,comp1,comp2,comp3,comp4)

def writeTemp(data, filename="CurrentRun.json"):
    with open(filename, 'w+') as f:
        f.write(json.dumps(data))

def printMeasurement(meas):
    print("Measurement: ",)
    for key,val in sorted(list(meas.items()), key=lambda item: item[0]!='V'):
        print("%s is %.03eA; "%(key,val),)
    print("\n")

def checkComplianceBreach(compliances,measurements):
    offset=.01 # If the measurement is within 5% of the compliance, shutdown.
    for key,comp in compliances.items():
        trueComp=(1-offset)*float(comp)
        if trueComp<abs(measurements[key]):
            print("Compliance reached, doing a few more test then stopping.")
            return True
       
#make sperearte cpmliance field for each input including the keithly
def runSwitch(delay,measureTime,samples,holdTime,startV,endV,steps,integration,keithley_comp,comp1,comp2,comp3,comp4,email,excelName):
    #keithley_comp #input as amps, but we need it in units of miliamps because that is what we prompted the user for.
    currents=[]
    stop=False
    
    #Add a skip measurement function.
    
    agilent_samples=samples+1 # We add one because the first measurement is usually not correct
    if agilent_samples < 2: agilent_samples=2 #Required at least 2 measurements
    agilent_duration=measureTime
    agilent_samples=2
    #Sets all of the inputs, and get a current reading.
    logging.debug('starting timers')
    agilent=Agilent4155C(reset=True)
    agilent.setSamplingMode()
    agilent.setVoltage(1,0,comp1)
    agilent.setVoltage(2,0,comp2)
    agilent.setVoltage(3,0,comp3)
    agilent.setVoltage(4,0,comp4)
    agilent.inst.timeout=25000 #timeout set to 25 sec
    print("Set integreation time to medium.")
    agilent.setMedium() #Integration Time
    agilent.setHoldTime(holdTime)
    #Now setup the keithly
    keithley = Keithley2657a()
    keithley.configure_measurement(1, 0, keithley_comp)

    #Map to check if compliances are reached.
    compliances={
            'keithley': keithley_comp,
            'I1': comp1, #this variable name corresponds to the keithley variable.
            'I2': comp2,
            'I3': comp3,
            'I4': comp4
        }
    print("=== START Prelim Test Measurement ===")
    print("Agilent Current: %s"%agilent.getCurrent(agilent_samples,agilent_duration))
    print("Keithley Current: %s"%keithley.get_current())
    print("===  END   Prelim Test Measurement ===")

    voltages=list(linspace(startV,endV,steps+1))

    lag=2 #Number of 
    for i,volt in enumerate(voltages):
        if i==len(voltages): break #Compliance reached, voltage list concated
        _currentV=volt
        print("Setting Keithley to %.03fV and measuring current. On step %s out of %s, %.01f%% done"%(volt,1+i,len(voltages),100*(i+1)/float(len(voltages))))
        if stop: return
        keithley.set_output(volt)
        time.sleep(delay)
        measurement=skipMeasurements(agilent.getCurrent(agilent_samples,agilent_duration), skip=1)
        measurement['keithley']=keithley.get_current()
        printMeasurement(measurement)
        currents.append(measurement)

        #Write progress to file.
        timestamp=datetime.today().strftime("_%Y_%b%d_%I.%M%p")
        writeTemp({'voltages':voltages[:i+1],'measurements':measurement,'compliances':compliances},filename="excel/%s_%s.json"%(excelName,timestamp)) 
        if checkComplianceBreach(compliances, measurement):
            voltages=voltages[:i+1+lag]

    #powerDown=Thread(target=powerDownPSU, args=(keithley,))
    #powerDown.start()
    powerDownPSU(keithley=keithley)
    #print("Done.")
    #print("Voltages %s"%voltages)
    #print("Currents %s"%currents)
    print("finished. Finalizing data.")
    
    excelData={'V': voltages, 'keithley': [], 'I1': [], 'I2': [], 'I3': [], 'I4': []}
    for current in currents:
        for key,value in current.items():
            excelData[key].append(value)

    excelData['leakage']=[]
    for i, V in enumerate(excelData['V']):
        leakage=excelData['keithley'][i]+excelData['I1'][i]+excelData['I2'][i]+excelData['I3'][i]+excelData['I4'][i]
        excelData['leakage'].append(leakage)
        
    filename=writeExcel(excelData,excelName)
    print("Wrote to excel file.")
                
    #MAKE SOME PLOTS
    files=[]
    plots=[('V', 'keithley'),('V', 'I1'),('V', 'I2'),('V', 'I3'),('V', 'I4'),('V', 'leakage')]
  
    for x,y in plots:
        title="%s vs %s"%(x,y)
        plt.cla()
        plt.plot(excelData[x],excelData[y])
        plt.title(title)
        fig = plt.gcf()
        imgdata = BytesIO()
        fig.savefig(imgdata, format='png')
        imgdata.seek(0)
        files.append((imgdata.getbuffer(), title))
        
    send_mail(filename,email,files=files)
    print("Sent email.")
    #print("Waiting for Keithley to power down.")
    #powerDown.join()
    #print("Done")
    return voltages,currents
    
def stopSwitch():
    print("Stop requested.")
    #if _currentV is None:
    #    print("Stop called before start.")
    #    return
    #stop=True
    powerDownPSU()
    print("Keithley at 0 volts.")

#`speed` is Volt per seccond
def powerDownPSU(keithley=None, speed=5):
    #Do volts per seccond. Reccomended 5
    if keithley is None: keithley = Keithley2657a()
    voltage=keithley.get_voltage()
    timeStep=.01 #seccond delay per step
    voltStep=speed*timeStep
    totalSteps=int(abs(voltage/voltStep))
    print("Poweing down Keithley from %s to 0V."%voltage)
    print("At a rate of %sV/s with delay of %s, there will be %s steps at %sV per step for %s secconds."%(speed,timeStep,totalSteps,voltStep,totalSteps*timeStep))
    voltages=linspace(voltage,0,totalSteps)
    for volt in voltages:
        keithley.set_output(volt)
        time.sleep(timeStep)
