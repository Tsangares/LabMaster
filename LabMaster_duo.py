from Agilent import *
from PowerSupply import *
from numpy import linspace
from time import sleep
import logging
import matplotlib.pyplot as plt
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

#make sperearte cpmliance field for each input including the keithly
def runDuo(delay,measureTime,samples,holdTime,startV,endV,steps,integration,keithley_comp,comp1,comp2,comp3,comp4):
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
    
    print("=== START Prelim Test Measurement ===")
    print("Agilent Current: %s"%agilent.getCurrent(agilent_samples,agilent_duration))
    print("Keithley Current: %s"%keithley.get_current())
    print("===  END   Prelim Test Measurement ===")

    voltages=linspace(startV,endV,steps)
    for volt in voltages:
        _currentV=volt
        print("Setting Keithley to %.03fV and measuring current."%volt)
        if stop: return
        keithley.set_output(volt)
        time.sleep(delay)
        measurement=skipMeasurements(agilent.getCurrent(agilent_samples,agilent_duration), skip=1)
        measurement['keithley']=keithley.get_current()
        currents.append(measurement)
    powerDownPSU(voltages[-1],keithley)
    print("Done.")
    print("Voltages %s"%voltages)
    print("Currents %s"%currents)
    return voltages,currents
    
def stopDuo():
    print("Stop requested.")
    if _currentV is None:
        print("Stop called before start.")
        return
    stop=True
    powerDownPSU()
    print("Keithley at 0 volts.")

def powerDownPSU(_currentV,keithley=None):
    if keithley is None: keithley = Keithley2657a()
    print("Ramping voltage down from %s to 0 in 1 seccond."%_currentV)
    voltages=linspace(_currentV,0,100)
    for volt in voltages:
        keithley.set_output(volt)
        time.sleep(.01)
