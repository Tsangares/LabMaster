from Agilent import *
from PowerSupply import *
from numpy import linspace
from time import sleep
import matplotlib.pyplot as plt
_currentV=None
stop=False
#make sperearte cpmliance field for each input including the keithly
def runDuo(delay,startV,endV,steps,compliance):
    currents=[]
    stop=False
    agilent_samples=1
    agilent_duration=.1
    #Sets all of the inputs, and get a current reading.
    agilent=Agilent4155C(reset=True)
    for i in range (1,5):
        agilent.setVoltage(i,0,compliance*1000) #PLZ CHECK THIS!!!
    print("Test current measurement: %s"%agilent.getCurrent(agilent_samples,agilent_duration))
        #Now setup the keithly
    keithley = Keithley2657a()
    voltage=0
    keithley.configure_measurement(1, 0, compliance)
    voltages=linspace(startV,endV,steps)
    for volt in voltages:
        _currentV=volt
        print("Setting Keithley to %.03fV and measuring current."%volt)
        if stop: return
        keithley.set_output(volt)
        time.sleep(delay)
        currents.append(agilent.getCurrent(agilent_samples,agilent_duration))
        time.sleep(delay)
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
