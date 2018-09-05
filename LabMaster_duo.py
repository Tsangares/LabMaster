from Agilent import *
from PowerSupply import *
from numpy import linspace
from time import sleep

_currentV=None
stop=False
def runDuo(delay,startV,endV,steps,compliance):
    currents=[]
    stop=False
    #Sets all of the inputs, and get a current reading.
    agilent=Agilent4155C(reset=True)
    for i in range (1,5):
        agilent.setVoltage(i,0,compliance)
        agilent.getCurrent(1,0,compliance)
        #Now setup the keithly
    keithley = Keithley2657a()
    voltage=0
    keithley.configure_measurement(1, 0, compliance)
    voltages=linspace(startV,endV,steps)
    for volt in voltages:
        _currentV=volt
        if stop: return
        keithley.set_output(volt)
        time.sleep(delay)
        currents.append(agilent.getCurrent(1,0,compliance))
        time.sleep(delay)
    return voltages,currents
    
def stopDuo():
    print("Stop requested.")
    if _currentV is None:
        print("Stop called before start.")
        return
    stop=True
    keithley = Keithley2657a()
    print("Ramping voltage down from %s to 0 in 1 seccond."%_currentV)
    voltages=linspace(_currentV,0,100)
    for volt in voltages:
        keithley.set_output(volt)
        time.sleep(.01)
    print("Keithley at 0 volts.")
