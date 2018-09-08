#!/usr/local/bin/python
try:
    import Queue as queue
    from Tkinter import *
except ImportError:
    import queue
    from tkinter import *

import ttk, Queue

import logging
import platform as Platform

import sys

import time
from random import randint

import matplotlib
import xlsxwriter

from Agilent import AgilentE4980a, Agilent4156
from PowerSupply import PowerSupplyFactory
from emailbot import send_mail

matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt

from LabMaster_gui import *
from LabMaster_utilities import *

debug = False

def GetIV(sourceparam, sourcemeter, dataout, stopqueue):
    (start_volt, end_volt, step_volt, delay_time, compliance) = sourceparam
    
    currents = []
    voltages = []
    keithley = 0
    
    if debug:
        pass
    else:
        if sourcemeter is 0:
            keithley = Keithley2400()
        else:
            keithley = Keithley2657a()
        keithley.configure_measurement(1, 0, compliance)
    last_volt = 0
    badCount = 0
    
    scaled = False
    if step_volt < 1.0:
        start_volt *= 1000
        end_volt *= 1000
        step_volt *= 1000
        scaled = True
    
    if start_volt > end_volt:
        step_volt = -1 * step_volt
    
    print "looping now"
    
    for volt in xrange(start_volt, end_volt, int(step_volt)):
        if not stopqueue.empty():
            stopqueue.get()
            break
        start_time = time.time()
        
        curr = 0
        if debug:
            pass
        else:
            if scaled:
                keithley.set_output(volt / 1000.0)
            else:
                keithley.set_output(volt)
        
        time.sleep(delay_time)
        
        if debug:
            curr = (volt + randint(0, 10)) * 1e-9
        else:
            curr = keithley.get_current()
            
        print "Current Reading: "+str(curr)
        
        # curr = volt
        time.sleep(1)
        if abs(curr) > abs(compliance - 50e-9):
            badCount = badCount + 1        
        else:
            badCount = 0    
        
        if badCount >= 5 :
            print "Compliance reached"
            dataout.put(((voltages, currents), 100, 0))
            break
        
        currents.append(curr)
        if scaled:
            voltages.append(volt / 1000.0)
        else:
            voltages.append(volt)

        if scaled:
            last_volt = volt / 1000.0
        else:
            last_volt = volt
        
        time_remain = (time.time() - start_time) * (abs((end_volt - volt) / step_volt))
        
        dataout.put(((voltages, currents), 100 * abs((volt + step_volt) / float(end_volt)), time_remain))
        
        
    while abs(last_volt) > 25:
        if debug:
            pass
        else:
            keithley.set_output(last_volt)
        
        time.sleep(delay_time/2.0)
        
        if last_volt < 0:
            last_volt += abs(step_volt*2.0)
        else:
            last_volt -= abs(step_volt*2.0)
    
    time.sleep(delay_time/2.0)
    if debug:
        pass
    else:
        keithley.set_output(0)
        keithley.enable_output(False)
    return (voltages, currents)

def GetCV(params, sourcemeter, dataout, stopqueue):
    
    capacitance = []
    voltages = []
    p2 = []
    c = []
    keithley = 0
    agilent = 0
    
    if debug:
        pass
    else:
        if sourcemeter is 0:
            keithley = Keithley2400()
        else:
            keithley = Keithley2657a()
    
    last_volt = 0
    
    (start_volt, end_volt, step_volt, delay_time, compliance,
     frequencies, level, function, impedance, int_time) = params
    if debug:
        pass
    else:
        keithley.configure_measurement(1, 0, compliance)
    
    if debug:
        pass
    else:
        agilent = AgilentE4980a()
        agilent.configure_measurement(function)
        agilent.configure_aperture(int_time)
    badCount = 0
    
    scaled = False
    
    if step_volt < 1.0:
        start_volt *= 1000
        end_volt *= 1000
        step_volt *= 1000
        scaled = True
    
    if start_volt > end_volt:
        step_volt = -1 * step_volt
    
    start_time = time.time()
    for volt in xrange(start_volt, end_volt, int(step_volt)):
        if not stopqueue.empty():
            stopqueue.get()
            break
    
        start_time = time.time()
        if debug:
            pass
        else:
            if scaled:
                keithley.set_output(volt / 1000.0)
            else:
                keithley.set_output(volt)
            
        curr = 0
        for f in frequencies:
            time.sleep(delay_time)

            if debug:
                capacitance.append((volt + int(f) * randint(0, 10)))
                curr = volt * 1e-10
                c.append(curr)
                p2.append(volt * 10)
            else:
                agilent.configure_measurement_signal(float(f), 0, level)
                (data, aux) = agilent.read_data()
                capacitance.append(data)
                p2.append(aux)
                curr = keithley.get_current()
                c.append(curr)
            
        if abs(curr) > abs(compliance - 50e-9):
            badCount = badCount + 1        
        else:
            badCount = 0    
        
        if badCount >= 5 :
            print "Compliance reached"
            break
        
        time_remain = (time.time() - start_time) * (abs((end_volt - volt) / step_volt))
        
        if scaled:
            voltages.append(volt / 1000.0)
        else:
            voltages.append(volt)
        formatted_cap = []
        parameter2 = []
        currents = []
        for i in xrange(0, len(frequencies), 1):
            formatted_cap.append(capacitance[i::len(frequencies)])
            parameter2.append(p2[i::len(frequencies)])
            currents.append(c[i::len(frequencies)])
        dataout.put(((voltages, formatted_cap), 100 * abs((volt + step_volt) / float(end_volt)), time_remain))
        
        time_remain = time.time() + (time.time() - start_time) * (abs((volt - end_volt) / end_volt))
        
        if scaled:
            last_volt = volt/1000.0
        else:
            last_volt = volt
        # graph point here

    if scaled:
        last_volt = last_volt/1000

    if debug:
        pass
    else:
        while abs(last_volt) > abs(step_volt):
            if last_volt <= step_volt:
                keithley.set_output(0)
                last_volt = 0
            else:
                keithley.set_output(last_volt - step_volt)
                last_volt -= step_volt

            time.sleep(1)

    if debug:
        pass
    else:
        keithley.enable_output(False)
    
    return (voltages, currents, formatted_cap, parameter2)

def spa_iv(params, dataout, stopqueue):
    (start_volt, end_volt, step_volt, hold_time, compliance, int_time) = params
    
    print params
    voltage_smua = []
    current_smua = []
    
    current_smu1 = []
    current_smu2 = []
    current_smu3 = []
    current_smu4 = []
    voltage_vmu1 = []
    
    voltage_source = Keithley2657a()
    voltage_source.configure_measurement(1, 0, compliance)
    voltage_source.enable_output(True)
    
    daq = Agilent4156()
    daq.configure_integration_time(_int_time=int_time)
    
    scaled = False
    if step_volt < 1.0:
        start_volt *= 1000
        end_volt *= 1000
        step_volt *= 1000
        scaled = True
    
    if start_volt > end_volt:
        step_volt = -1 * step_volt
    
    for i in xrange(0, 4, 1):
        daq.configure_channel(i)  
    daq.configure_vmu()    
    
    last_volt = 0
    for volt in xrange(start_volt, end_volt, step_volt):
        
        if debug:
            pass
        else:
            if scaled:
                voltage_source.set_output(volt / 1000.0)
            else:
                voltage_source.set_output(volt)
        time.sleep(hold_time)
        
        daq.configure_measurement()
        daq.configure_sampling_measurement()
        daq.configure_sampling_stop()
        
        # daq.inst.write(":PAGE:DISP:GRAP:Y2:NAME \'I2\';")
        daq.inst.write(":PAGE:DISP:LIST \'@TIME\', \'I1\', \'I2\', \'I3\', \'I4\', \'VMU1\'")
        daq.measurement_actions()
        daq.wait_for_acquisition()
        
        current_smu1.append(daq.read_trace_data("I1"))
        current_smu2.append(daq.read_trace_data("I2"))
        
        # daq.inst.write(":PAGE:DISP:LIST \'@TIME\', \'I2\', \'I3\'")

        current_smu3.append(daq.read_trace_data("I3"))
        current_smu4.append(daq.read_trace_data("I4"))
        voltage_vmu1.append(daq.read_trace_data("VMU1"))
        current_smua.append(voltage_source.get_current())
        
        if scaled:
            voltage_smua.append(volt / 1000.0)
            last_volt = volt / 1000.0
        else:
            voltage_smua.append(volt)
            last_volt = volt
        
        print "SMU1-4"
        print current_smu1
        print current_smu2
        print current_smu3
        print current_smu4
        print "SMUA"
        print current_smua
        print "VMU1"
        print voltage_vmu1
        dataout.put((voltage_vmu1, current_smua, current_smu1, current_smu2, current_smu3, current_smu4))
    while abs(last_volt) >= 4:
        time.sleep(0.5)

        if debug:
            pass
        else:
            voltage_source.set_output(last_volt)
        
        if last_volt < 0:
            last_volt += 5
        else:
            last_volt -= 5
        
    time.sleep(0.5)
    voltage_source.set_output(0)
    voltage_source.enable_output(False)
    return(voltage_smua, current_smua, current_smu1, current_smu2, current_smu3, current_smu4, voltage_vmu1)

# TODO: current monitor bugfixes and fifo implementation
def curmon(source_params, sourcemeter, dataout, stopqueue):
        
    (voltage_point, step_volt, hold_time, compliance, minutes) = source_params
    print "(voltage_point, step_volt, hold_time, compliance, minutes)"
    print source_params
    currents = []
    timestamps = []
    voltages = []
    
    total_time = minutes*60
    
    keithley=0
    if debug:
        pass
    else:
        if sourcemeter is 0:
            keithley = Keithley2400()
        else:
            keithley = Keithley2657a()
        keithley.configure_measurement(1, 0, compliance)
        
    last_volt = 0
    badCount = 0
     
    scaled = False
      
    if step_volt < 1:
        voltage_point *= 1000
        step_volt *= 1000
        scaled = True
    else:
        step_volt = int(step_volt)
        
    if 0 > voltage_point:
        step_volt = -1 * step_volt
    
    start_time = time.time()
    
    for volt in xrange(0, voltage_point, step_volt):
        if not stopqueue.empty():
            stopqueue.get()
            break
            
        curr = 0
        if debug:
            pass
        else:
            if scaled:
                keithley.set_output(volt / 1000.0)
            else:
                keithley.set_output(volt)
                
        time.sleep(hold_time)
        
        if debug:
            curr = (volt + randint(0, 10)) * 1e-9
        else:
            curr = keithley.get_current()
        # curr = volt
        
        if abs(curr) > abs(compliance - 50e-9):
            badCount = badCount + 1        
        else:
            badCount = 0    
            
        if badCount >= 5 :
            print "Compliance reached"
            break
        
        if scaled:
            last_volt = volt / 1000.0
        else:
            last_volt = volt
        
        dataout.put(((timestamps, currents), 0, total_time+start_time))
        print """ramping up"""
    
    print "current time"
    print time.time()
    print "Start time"
    print start_time
    print "total time"
    print total_time
    
    start_time = time.time()
    while(time.time() < start_time + total_time):
        time.sleep(5)
        
        dataout.put(((timestamps, currents), 100*((time.time()-start_time)/total_time), start_time+total_time))
        if debug:
            currents.append(randint(0, 10) * 1e-9)
        else:
            currents.append(keithley.get_current())
        timestamps.append(time.time() - start_time)
        print "timestamps"
        print timestamps
        print "currents"
        print currents  
    print "Finished"
    
    while abs(last_volt) > 5:
        if debug:
            pass
        else:
            keithley.set_output(last_volt)
        
        time.sleep(hold_time/2.0)
        if last_volt < 0:
            last_volt += 5
        else:
            last_volt -= 5
    
    time.sleep(hold_time/2.0)
    if debug:
        pass
    else:
        keithley.set_output(0)
        keithley.enable_output(False)
    
    return (timestamps, currents)
    
def getvalues(input_params, dataout, stopqueue):
    if "Windows" in platform.platform():
            (compliance, compliance_scale, start_volt, end_volt, step_volt, hold_time, source_choice, recipients, filename) = input_params
    else:
        (compliance, compliance_scale, start_volt, end_volt, step_volt, hold_time, source_choice, recipients, thowaway) = input_params
        filename = tkFileDialog.asksaveasfilename(initialdir="~", title="Save data", filetypes=(("Microsoft Excel file", "*.xlsx"), ("all files", "*.*")))
    print "File done"

    try:
        comp = float(float(compliance) * ({'mA':1e-3, 'uA':1e-6, 'nA':1e-9}.get(compliance_scale, 1e-6)))
        source_params = (int(float(start_volt)), int(float(end_volt)), (float(step_volt)),
                             float(hold_time), comp)
    except ValueError:
        print "Please fill in all fields!"
    data = ()
    if source_params is None:
        pass
    else:
        print source_choice
        choice = 0
        if "2657a" in source_choice:
            print "asdf keithley 366"
            choice = 1
        data = GetIV(source_params, choice, dataout, stopqueue)
            
    fname = (((filename+"_"+str(time.asctime(time.localtime(time.time())))+".xlsx").replace(" ", "_")).replace(":", "_"))

    data_out = xlsxwriter.Workbook(fname)
    if "Windows" in platform.platform():
        fname = "./"+fname
    worksheet = data_out.add_worksheet()
    
    (v, i) = data
    values = []
    pos = v[0]>v[1]
    for x in xrange(0, len(v), 1):
        values.append((v[x], i[x]))
    row = 0
    col = 0
    
    chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
    
    for volt, cur in values:
        worksheet.write(row, col, volt)
        worksheet.write(row, col + 1, cur)
        row += 1
    
    chart.add_series({'categories': '=Sheet1!$A$1:$A$' + str(row), 'values': '=Sheet1!$B$1:$B$' + str(row)})
    chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}, 'reverse':pos})
    chart.set_y_axis({'name':'Current [A]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}, 'reverse':pos})
    chart.set_legend({'none':True})
    worksheet.insert_chart('D2', chart)
    data_out.close()
    
    try:
        mails = recipients.split(",")
        sentTo = []
        for mailee in mails:
            sentTo.append(mailee.strip())
    
        print sentTo
        print fname
        sendMail(fname, sentTo)
    except:
        pass
    
def cv_getvalues(input_params, dataout, stopqueue):
    print input_params
    if "Windows" in platform.platform():
        (compliance, compliance_scale, start_volt, end_volt, step_volt, hold_time, source_choice, frequencies, function, amplitude, impedance, integration, recipients, filename) = input_params
        filename = "./"+filename
    else:
        (compliance, compliance_scale, start_volt, end_volt, step_volt, hold_time, source_choice, frequencies, function, amplitude, impedance, integration, recipients, thowaway) = input_params
        filename = tkFileDialog.asksaveasfilename(initialdir="~", title="Save data", filetypes=(("Microsoft Excel file", "*.xlsx"), ("all files", "*.*")))
    
    try:
        # step_volt was originally int(float(step_volt)), but it was causing problems with steps sizes < 1.0.  Since it is 'scaled'
        # later on, it doesn't need to be cast as an int first.
        comp = float(float(compliance) * ({'mA':1e-3, 'uA':1e-6, 'nA':1e-9}.get(compliance_scale, 1e-6)))
        params = (int(float(start_volt)), int(float(end_volt)), float(step_volt),
                             float(hold_time), comp, frequencies, float(amplitude), function, int(impedance), {"Short":0, "Medium":1, "Long":2}.get(integration))
        print params
    except ValueError:
        print "Please fill in all fields!"
    data = ()
    if params is None:
        pass
    else:
        data = GetCV(params, {"Keithley 2657a":1, "Keithley 2400":0}.get(source_choice), dataout, stopqueue)
        fname = (((filename+"_"+str(time.asctime(time.localtime(time.time())))+".xlsx").replace(" ", "_")).replace(":", "_"))
    
    data_out = xlsxwriter.Workbook(fname)
    if "Windows" in platform.platform():
        fname = "./"+fname
    worksheet = data_out.add_worksheet()
    
    (v, i, c, r) = data
    
    row = 9
    col = 0
    
    chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
    worksheet.write(8, 0, "V")
    for volt in v:
        worksheet.write(row, col, volt)
        row += 1
    
    col += 1
    last_col = col
    for f in frequencies:
        worksheet.write(7, col, "Freq=" + f + "Hz")
        col += 3
        
    col = last_col
    row = 9
    for frequency in i:
        worksheet.write(8, col, "I")
        row = 9
        for current in frequency:
            worksheet.write(row, col, current)
            row += 1
        col += 3
    
    col = last_col + 1
    last_col = col
    for frequency in c:
        worksheet.write(8, col, "C")
        row = 9
        for cap in frequency:
            worksheet.write(row, col, cap)
            row += 1
        col += 3
    
    col = last_col + 1
    last_col = col
    
    fs = 0
    for frequency in r:
        fs += 1
        worksheet.write(8, col, "R")
        row = 9
        for res in frequency:
            worksheet.write(row, col, res)
            row += 1
        col += 3
    row += 5
    if fs >= 1:
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$B$10:$B$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Current [A]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('D' + str(row), chart)

        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$C$10:$C$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Capacitance [F]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('D' + str(row + 20), chart)
        
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$D$10:$D$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Resistance [R]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('D' + str(row + 40), chart)
        
    if fs >= 2:
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$E$10:$E$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Current [A]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('L' + str(row), chart)
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$F$10:$F$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Capacitance [C]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('L' + str(row + 20), chart)
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$G$10:$G$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Resistance [R]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('L' + str(row + 40), chart)
        
    if fs >= 3:
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$H$10:$H$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Current [A]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('T' + str(row), chart)
        
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$I$10:$I$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Capacitance [C]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('T' + str(row + 20), chart)
    
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$J$10:$J$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Resistance [R]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('T' + str(row + 40), chart)
  
    if fs >= 4:
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$K$10:$K$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Current [A]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('AB' + str(row), chart)
    
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$L$10:$L$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Capacitance [C]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('AB' + str(row + 20), chart)
    
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        chart.add_series({'categories': '=Sheet1!$A$10:$A$' + str(row), 'values': '=Sheet1!$M$10:$M$' + str(row), 'marker': {'type': 'star'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_y_axis({'name':'Resistance [R]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}})
        chart.set_legend({'none':True})
        worksheet.insert_chart('AB' + str(row + 40), chart)
    
    data_out.close()
    
    try:
        mails = recipients.split(",")
        sentTo = []
        for mailee in mails:
            sentTo.append(mailee.strip())
                
        print sentTo
        sendMail(fname, sentTo)
    except:
        print "Failed to get recipients"
        pass
    
# TODO: Implement value parsing from gui
def spa_getvalues(input_params, dataout):
    pass

def multiv_getvalues(input_params, dataout, stopqueue):
    if "Windows" in platform.platform():
            (compliance, compliance_scale, start_volt, end_volt, step_volt, hold_time, source_choice, recipients, filename, times_str) = input_params
    else:
        (compliance, compliance_scale, start_volt, end_volt, step_volt, hold_time, source_choice, recipients, thowaway, times_str) = input_params
        filename = tkFileDialog.asksaveasfilename(initialdir="~", title="Save data", filetypes=(("Microsoft Excel file", "*.xlsx"), ("all files", "*.*")))
    print "File done"
    
    try:
        comp = float(float(compliance) * ({'mA':1e-3, 'uA':1e-6, 'nA':1e-9}.get(compliance_scale, 1e-6)))
        source_params = (int(float(start_volt)), int(float(end_volt)), (float(step_volt)),
                             float(hold_time), comp)
        times = int(times_str)
        
    except ValueError:
        print "Please fill in all fields!"
    data = ()
    
    while times>0:
        if not stopqueue.empty():
            break

        if source_params is None:
            pass
        else:
            print source_choice
            choice = 0
            if "2657a" in source_choice:
                print "asdf keithley 366"
                choice = 1
            data = GetIV(source_params, choice, dataout, stopqueue)
        fname = (((filename+"_"+str(time.asctime(time.localtime(time.time())))+".xlsx").replace(" ", "_")).replace(":", "_"))
        print fname
        data_out = xlsxwriter.Workbook(fname)
        if "Windows" in platform.platform():
            fname = "./"+fname
        worksheet = data_out.add_worksheet()
        
        (v, i) = data
        values = []
        pos = v[0]>v[1]
        for x in xrange(0, len(v), 1):
            values.append((v[x], i[x]))
        row = 0
        col = 0
        chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
        for volt, cur in values:
            worksheet.write(row, col, volt)
            worksheet.write(row, col + 1, cur)
            row += 1
        chart.add_series({'categories': '=Sheet1!$A$1:$A$' + str(row), 'values': '=Sheet1!$B$1:$B$' + str(row), 'marker':{'type':'triangle'}})
        chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}, 'reverse':pos})
        chart.set_y_axis({'name':'Current [A]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}, 'reverse':pos})
        chart.set_legend({'none':True})
        worksheet.insert_chart('D2', chart)
        data_out.close()
        
        try:
            mails = recipients.split(",")
            sentTo = []
            for mailee in mails:
                sentTo.append(mailee.strip())
        
            print sentTo
            sendMail(fname, sentTo)
        except:
            pass
        data_out.close()
        times-=1
    
    
# TODO: Implement value parsing from gui
def curmon_getvalues(input_params, dataout, stopqueue):
    
    if "Windows" in platform.platform():
            (compliance, compliance_scale, start_volt, end_volt, step_volt, hold_time, source_choice, recipients, filename, total_time) = input_params
            filename = ((filename+"_"+str(time.asctime(time.localtime(time.time())))+".xlsx").replace(" ", "_")).replace(":","_")
    else:
        (compliance, compliance_scale, start_volt, end_volt, step_volt, hold_time, source_choice, recipients, thowaway, total_time) = input_params
        filename = tkFileDialog.asksaveasfilename(initialdir="~", title="Save data", filetypes=(("Microsoft Excel file", "*.xlsx"), ("all files", "*.*")))
    print "File done"
    
    try:
        comp = float(float(compliance) * ({'mA':1e-3, 'uA':1e-6, 'nA':1e-9}.get(compliance_scale, 1e-6)))
        source_params = (int(float(end_volt)), float(step_volt),
                             float(hold_time), comp, int(total_time))
    except ValueError:
        print "Please fill in all fields!"
    data = ()
    if source_params is None:
        pass
    else:
        print source_choice
        choice = 0
        if "2657a" in source_choice:
            print "asdf keithley 366"
            choice = 1
        data = curmon(source_params, choice, dataout, stopqueue)
            
    data_out = xlsxwriter.Workbook(filename)
    if "Windows" in platform.platform():
        fname = "./"+filename
    path = filename
    worksheet = data_out.add_worksheet()
    
    (v, i) = data
    values = []
    pos = v[0]>v[1]
    for x in xrange(0, len(v), 1):
        values.append((v[x], i[x]))
    row = 0
    col = 0
    
    chart = data_out.add_chart({'type':'scatter', 'subtype':'straight_with_markers'})
    
    for volt, cur in values:
        worksheet.write(row, col, volt)
        worksheet.write(row, col + 1, cur)
        row += 1
    
    chart.add_series({'categories': '=Sheet1!$A$1:$A$' + str(row), 'values': '=Sheet1!$B$1:$B$' + str(row)})
    chart.set_x_axis({'name':'Voltage [V]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}, 'reverse':pos})
    chart.set_y_axis({'name':'Current [A]', 'major_gridlines':{'visible':True}, 'minor_tick_mark':'cross', 'major_tick_mark':'cross', 'line':{'color':'black'}, 'reverse':pos})
    chart.set_legend({'none':True})
    worksheet.insert_chart('D2', chart)
    data_out.close()
    
    try:
        mails = recipients.split(",")
        sentTo = []
        for mailee in mails:
            sentTo.append(mailee.strip())
    
        print sentTo
        sendMail(path, sentTo)
    except:
        pass
    
    
    
