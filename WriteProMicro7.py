# this version uses Arduino sketch "ProbeCard_CH4"
# first step in converting program to functions.
import serial
from serial import SerialException
import time
import sys
import struct

gain_map = {
    # key: channel number, value: feedback resistor value in Ohms
    # this map valid as of 11/02/18 for HPK-5x5-GR Readout Board V5.0C, #1
    1: 14.97e6,
    2: 14.98e6,
    3: 14.97e6,
    4: 14.94e6,
    5: 15.01e6,
    6: 14.89e6,
    7: 14.95e6,
    8: 15.06e6,
    9: 14.95e6,
    10: 14.97e6,
    11: 14.99e6,
    12: 14.92e6,
    13: 14.91e6,
    14: 15.05e6,
    15: 14.95e6,
    16: 14.92e6,
    17: 14.89e6,
    18: 14.95e6,
    19: 14.94e6,
    20: 14.94e6,
    21: 15.04e6,
    22: 14.99e6,
    23: 14.96e6,
    24: 15.01e6,
    25: 14.94e6,
    26: 15.02e6
}

reverse_gain_map = {
    # key: lower multiplexer address, value: feedback resistor values in Ohms,
    # for the four channels being read out in order, on output connectors J1-J4.
    # this map valid as of 11/02/18 for HPK-5x5-GR Readout Board V5.0C, #1
    0: (14.97e6, 14.95e6, 14.91e6, 14.94e6),
    1: (14.98e6, 15.06e6, 15.05e6, 14.94e6),
    2: (14.97e6, 14.95e6, 14.95e6, 15.04e6),
    3: (14.94e6, 14.97e6, 14.92e6, 14.99e6),
    4: (15.01e6, 14.99e6, 14.89e6, 15.01e6),
    5: (14.89e6, 14.92e6, 14.95e6, 15.01e6),
    6: (15.02e6, 0, 0, 14.94e6)
}

reverse_channel_map = {
    #key: lower multiplexer address, value: channels output to J1, J2, J3, and J4
    # in order.  all channels are routed through four 8:1 multiplexers with four
    # outputs routed to output connectors J1-J4.  All four multiplexers are controlled
    # by one three bit address.
    0: (1, 7, 13, 19),
    1: (2, 8, 14, 20),
    2: (3, 9, 15, 21),
    3: (4, 10, 16, 22),
    4: (5, 11, 17, 23),
    5: (6, 12, 18, 24),
    6: (26, 99, 99, 25)
}

channel_map = {
    # key: channel number, value: (low multiplexer address, high multiplexer address)
    # HPK 5x5 sensor pads are labeled channel 1 - 25. Channel 26 is the bias ring.
    1: (0,0),
    2: (1, 0),
    3: (2, 0),
    4: (3, 0),
    5: (4, 0),
    6: (5, 0),
    7: (0, 1),
    8: (1, 1),
    9: (2, 1),
    10: (3, 1),
    11: (4, 1),
    12: (5, 1),
    13: (0, 2),
    14: (1, 2),
    15: (2, 2),
    16: (3, 2),
    17: (4, 2),
    18: (5, 2),
    19: (0, 3),
    20: (1, 3),
    21: (2, 3),
    22: (3, 3),
    23: (4, 3),
    24: (5, 3),
    25: (6, 3),
    26: (6, 0)
}

def open_com( port ):
    #open COM port with 5 second timeout
    try:
        ArduinoSerial = serial.Serial(port,9600,timeout=5)
    except SerialException:
        return -1
    time.sleep(2)
    # for debugging, verify that port is open, and parameters correct
    #print(ArduinoSerial)
    return ArduinoSerial

def select_channel( ArduinoSerial, channel_no ):
    #convert channel number (in Unicode string) to integer
    a = int(channel_no)
    if (a < 1 or a > 26):
        sys.exit(1)
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
            sys.exit(2)
    except TimeoutError:
        sys.exit(3)
    #print byte received for debugging
    #print("byte received :", hex(x[0]) )
    # if byte read back is different from byte sent, halt and catch fire
    if (x != f):
        # for debugging
        #print("error:  byte sent: ",hex(f[0]) ," byte received: ", hex(x[0]) )
        sys.exit(4)
    #else: print("Correct bits received from Arduino")
        
def select_channel_group(ArduinoSerial, mux_address):
    #convert mux address (in Unicode string) to integer
    a = int(mux_address)
    if (a<0 or a>7):
        sys.exit(5)
    #convert integer into packed binary.  
    # ">" indicateds "big-endian" bit order
    # "B" indicates Python integer of one byte size.
    # this will leave high order bits = 0, which will not effect the result
    b = struct.pack('>B',a)
    #display byte to send in hex for debugging
    #print("byte to send: ", hex(b[0]) )     
    #write to Arduino
    ArduinoSerial.write(b)
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
            sys.exit(2)
    except TimeoutError:
        sys.exit(3)
    #print byte received for debugging
    #print("byte received :", hex(x[0]) )
    # if byte read back is different from byte sent, halt and catch fire
    # provided we are not asking for a report of current address setting
    if (x != b and a != 7):
        # for debugging
        #print("error:  byte sent: ",hex(f[0]) ," byte received: ", hex(x[0]) )
        sys.exit(4)
    #else: print("Correct bits received from Arduino")
    #return tuple containing channel numbers
    # if enquiring what address the Arduino is currently set to
    if (x !=b and a == 7):
        print("Arduino address set to: ", hex(x[0]))

    
# main program
# N = com port number
if (len(sys.argv) != 3):
    print("syntax: WriteProMicro5.py COMN -[c,a,r]")
    sys.exit()
op = sys.argv[2]
if (op != '-c' and op != '-a' and op != '-r'):
    print("syntax: WriteProMicro5.py COMN -[c,a,r]")
    sys.exit() 

# get com port
port = sys.argv[1]
ArduinoSerial = open_com( port )
if (ArduinoSerial == -1):
    print("couldn't open ", port )
    sys.exit()
    
while 1:
    if (op == '-c'):
        # get channel address to send to Arduino
        channel_no = input("enter channel number (or q for quit): ")  #string variable - channel number in characters.
        if (channel_no == 'q'):
            break
        # write channel number to Arduino
        return_code = select_channel( ArduinoSerial, channel_no )
        if (return_code == 1):
            print("channel number out of range")
        if (return_code == 2):
             print("Quitting: Nothing read back")
        if (return_code == 3):
            print("Quitting: Timeout Error on readback")
        if (return_code == 4):
            print("address read back from Arduino doesn't match address sent")
    if (op == '-a'):
        mux_address = input("enter mux address: ")
        return_code = select_channel_group(ArduinoSerial, mux_address)
        print("channels to read: ", reverse_channel_map[int(mux_address)])
        if (return_code == 5):
            print("multiplexer address out of range")
    if (op == '-r'):
        return_code = select_channel_group(ArduinoSerial, 7)
        break




