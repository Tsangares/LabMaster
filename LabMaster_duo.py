from Agilent import *
from PowerSupply import *
from numpy import linspace
from time import sleep
import matplotlib.pyplot as plt
_currentV=None
stop=False

def averageCurrent(result):
    output={}
    for key in result:
        currents=result[1:]
        output[key]=sum(currents)/len(currents)
    return output

#make sperearte cpmliance field for each input including the keithly
def runDuo(delay,measureTime,samples,startV,endV,steps,integration,keithley_comp,comp1,comp2,comp3,comp4):
    keithley_comp/=1000 #input as amps, but we need it in units of miliamps because that is what we prompted the user for.
    currents=[]
    stop=False
    agilent_samples=samples+1
    agilent_duration=measureTime
    #Sets all of the inputs, and get a current reading.
    agilent=Agilent4155C(reset=True)
    agilent.setVoltage(1,0,comp1)
    agilent.setVoltage(2,0,comp2)
    agilent.setVoltage(3,0,comp3)
    agilent.setVoltage(4,0,comp4)
    print("Test current measurement: %s"%agilent.getCurrent(agilent_samples,agilent_duration))
        #Now setup the keithly
    keithley = Keithley2657a()
    voltage=0
    keithley.configure_measurement(1, 0, keithley_comp)
    voltages=linspace(startV,endV,steps)
    for volt in voltages:
        _currentV=volt
        print("Setting Keithley to %.03fV and measuring current."%volt)
        if stop: return
        keithley.set_output(volt)
        time.sleep(delay)
        
        currents.append(averageCurrent(agilent.getCurrent(agilent_samples,agilent_duration)))
    powerDownPSU(voltages[-1],keithley)
    print("Done.")
    print("Voltages %s"%voltages)
    print("Currents %s"%currents)
    plt.plot(voltages, currents)
    plt.show()
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
