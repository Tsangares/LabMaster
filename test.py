from Agilent import *

a=Agilent4155C(reset=True)
for i in range (1,5):
    a.setVoltage(i,0,.01)
a.getCurrent(1,1,.1)
