import matplotlib.pyplot as plt
from numpy import linspace
from random import random
from LabMaster_plotting import writeExcel
from emailbot import send_mail
from io import BytesIO
import json
from time import sleep as delay
from Agilent import Agilent4155C
from PowerSupply import Keithley2657a
#Test function
def getNoise(n=100):
    return list(linspace((random()*10)**random()*10,(random()*10)**random()*10,n))
def testExcel():
    data={
        "Keithley I": list(linspace(0,7,100)),
        "I1": list(linspace(random(),random(),100)),
        "I2": getNoise(),
        "I3": getNoise(),
        "I4": getNoise()
        }
    excel_filename=writeExcel(data,"happy")
    plt.cla()
    fig=plt.figure()
    plt.plot(data['I1'],data['I2'])
    imgdata = BytesIO()
    fig.savefig(imgdata, format='png')
    imgdata.seek(0)
    send_mail(excel_filename,"wwyatt@ucsc.edu", files=[(json.dumps(data),"data.json"),(imgdata.buf,"test.png")])

#Testing new current reading skill
def testAgilent():
    A=Agilent4155C(reset=True)
    K=Keithley2657a()
    A.setSamplingMode()
    A.setCurrent(1,0,0)
    A.setCurrent(2,0,0)
    A.setVoltage(3,0,0)
    A.setVoltage(4,0,0)
    A.read()

testAgilent()
delay(1)
