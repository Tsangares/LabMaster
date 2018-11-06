from Arduino import Max

def testConnect():
    GRADE=False
    port=None
    arduino=Max()
    for i in range(0,100):
        connected=arduino.connect(i)
        if connected:
            GRADE=True
            port=i
            break
    return GRADE,port,arduino.ArduinoSerial


def testSelect(port):
    GRADE=False
    arduino=Max(port)
    

def run():
    grade,port,arduino=testConnect()
    print("TestConnect Grade, port ArduinoSerial:",grade)



    

    
