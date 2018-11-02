# this version uses Arduino sketch "ProbeCard_CH4"
# first step in converting program to functions.
import serial
from serial import SerialException
import time
import sys
import struct
class Max:
    def __init__(self,port):
        # key: channel number, value: (low multiplexer address, high multiplexer address)
        # HPK 5x5 sensor pads are labeled channel 1 - 25. Channel 26 is the bias ring.
        self.channel_map = {1: (0,0), 2: (1, 0), 3: (2, 0), 4: (3, 0), 5: (4, 0), 6: (5, 0), 7: (0, 1), 8: (1, 1), 9: (2, 1), 10: (3, 1), 11: (4, 1), 12: (5, 1), 13: (0, 2), 14: (1, 2), 15: (2, 2), 16: (3, 2), 17: (4, 2), 18: (5, 2), 19: (0, 3), 20: (1, 3), 21: (2, 3), 22: (3, 3), 23: (4, 3), 24: (5, 3), 25: (6, 3), 26: (6, 0)}
        self.selectError=["channel number out of range","Quitting: Nothing read back","Quitting: Timeout Error on readback","address read back from Arduino doesn't match address sent"]
        
        self.port=port
        self.ArduinoSerial = open_com( port )
        
        if (ArduinoSerial == -1):
            raise Exception("Arduino ERROR (COM): couldn't open port ", port )
        
    def getChannel( self,chan ):
        return_code = select_channel( self.ArduinoSerial, chan )
        if return_code is None: return None
        else: raise Exception( "Arduino ERROR (CHAN):",self.selectError[return_code] )

    def open_com( self,port ):
        #open COM port with 5 second timeout
        try:
            ArduinoSerial = serial.Serial(port,9600,timeout=5)
        except SerialException:
            return -1
        time.sleep(2)
        # for debugging, verify that port is open, and parameters correct
        #print(ArduinoSerial)
        return ArduinoSerial

    def select_channel( self,ArduinoSerial, channel_no ):
        #convert channel number (in Unicode string) to integer
        a = int(channel_no)
        if (a < 1 or a > 26):
            return 1
            # lookup low and high multiplexer addresses for the channel
        b = channel_map[a]
        # print multiplexer addresses for debugging
        #print("corresponding addresses: ", b)
        # pack addresses into one byte
        c = b[0]
        d = b[1]
        d = d << 4
        e = c|d
        #convert integer into packed binary.  
        # ">" indicateds "big-endian" bit order
        # "B" indicates Python integer of one byte size.
        f = struct.pack('>B',e)
        #display byte to send in hex for debugging
        #print("byte to send: ", hex(f[0]) )     
        #write to Arduino
        ArduinoSerial.write(f)
        # arduino will do a serial.read() and put result into an integer variable
        #arduino will send the byte it received back as confirmation that the address was received
        # it will then separate out the address bits and update digital outputs if needed.
        # arduino also handles multiplexer enable lines locally.  
        try:
            x = ArduinoSerial.read()
            #if the Arduino doesn't answer immediately, serial read returns nothing and
            # program proceeds to next instruction.  Timeout set to 5 seconds doesn't make
            # a difference, so there should never be timeout errors.  
            if(x == b''):  # i.e. if nothing read back
                return 2
        except TimeoutError:
            return 3
            #print byte received for debugging
            #print("byte received :", hex(x[0]) )
            # if byte read back is different from byte sent, halt and catch fire
        if (x != f):
            # for debugging
            #print("error:  byte sent: ",hex(f[0]) ," byte received: ", hex(x[0]) )
            return 4
            #else: print("Correct bits received from Arduino")
        return None
            