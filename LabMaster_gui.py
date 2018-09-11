# coding: utf-8
try:
    import Queue as queue
    from Tkinter import *
except ImportError:
    import queue
    from tkinter import *

import ttk,time,threading
import platform as platform

from Agilent import AgilentE4980a, Agilent4156
from PowerSupply import PowerSupplyFactory

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt

from LabMaster_save import *
from LabMaster import *
from LabMaster_duo import *

# These are helper functions that are common GUI objects.

# makeEntry is a text label and a string input
def makeEntry(fig,title,var,row):
    obj = Label(fig, text=title)
    obj.grid(row=row, column=1)
    if var is None: var=StringVar(root, "0")
    obj = Entry(fig, textvariable=var)
    obj.grid(row=row, column=2)

# makeUnitEntry is a Label, Entry box, then a another label showing the specified untis
def makeUnitEntry(fig,title,var,row,unit):
    makeEntry(fig,title,var,row)
    obj = Label(fig, text=unit)
    obj.grid(row=row, column=3)

# makeUnitsEntry is the same at make Unit Entry but allows custom units.
def makeUnitsEntry(fig,title,var,row,units,scale):
    makeEntry(fig,title,var,row)
    scale.set(list(units)[0])
    obj = OptionMenu(fig, scale, *units)
    obj.grid(row=row, column=3)

# Since most experiments use a common configuration setup, here is an object containing them. Any other experiment specific runs should be specified outside of this object.
class Settings:
    def __init__(self,notebook):
        self.start_volt=StringVar(root,"0")
        self.end_volt = StringVar(root,"100")
        self.step_volt = StringVar(root,"5")
        self.hold_time = StringVar(root,"1")
        self.compliance = StringVar(root,"1") 
        self.recipients = StringVar(root,"adapbot@gmail.com")   
        self.compliance_scale = StringVar()
        self.source_choice = StringVar()
        self.figure=ttk.Frame(notebook)

    def buildLabels(self, start=True, end=True, step=True, hold=True, compliance=True):
        if start: makeUnitEntry(self.figure,"Start Volt", self.start_volt, 1, "V")
        if end:   makeUnitEntry(self.figure,"End Volt",   self.end_volt,   2, "V")
        if step:  makeUnitEntry(self.figure,"Step Volt",  self.step_volt,  3, "V")
        if hold:  makeUnitEntry(self.figure,"Hold Time",  self.hold_time,  4, "s")
        if compliance: makeUnitsEntry(self.figure,"Compliance", self.compliance, 5, {'mA', 'uA', 'nA'}, self.compliance_scale)

# This is the mess of a GUI        
class GuiPart:
    
    def __init__(self, master, inputdata, outputdata, stopq):
        self.master = master
        self.inputdata = inputdata
        self.outputdata = outputdata
        self.stop = stopq
        
        self.start_volt = StringVar()
        self.end_volt = StringVar()
        self.step_volt = StringVar()
        self.hold_time = StringVar()
        self.compliance = StringVar()
        
        self.recipients = StringVar()
        self.compliance_scale = StringVar()
        self.source_choice = StringVar()
        self.filename = StringVar()
        
        self.cv_start_volt = StringVar()
        self.cv_end_volt = StringVar()
        self.cv_step_volt = StringVar()
        self.cv_hold_time = StringVar()
        self.cv_compliance = StringVar() 
        self.cv_recipients = StringVar()   
        self.cv_compliance_scale = StringVar()
        self.cv_source_choice = StringVar()
        self.cv_impedance_scale = StringVar()
        self.cv_amplitude = StringVar()
        self.cv_frequencies = StringVar()
        self.cv_integration = StringVar()
        self.started = False
        
        self.multiv_start_volt = StringVar()
        self.multiv_end_volt = StringVar()
        self.multiv_step_volt = StringVar()
        self.multiv_hold_time = StringVar()
        self.multiv_compliance = StringVar() 
        self.multiv_recipients = StringVar()   
        self.multiv_compliance_scale = StringVar()
        self.multiv_source_choice = StringVar()
        self.multiv_filename = StringVar()
        self.multiv_times = StringVar()
        
        self.curmon_start_volt = StringVar()
        self.curmon_end_volt = StringVar()
        self.curmon_step_volt = StringVar()
        self.curmon_hold_time = StringVar()
        self.curmon_compliance = StringVar() 
        self.curmon_recipients = StringVar()   
        self.curmon_compliance_scale = StringVar()
        self.curmon_source_choice = StringVar()
        self.curmon_filename = StringVar()
        self.curmon_time = StringVar()
        
        """
        IV GUI
        """
        ""

        self.start_volt.set("0.0")
        self.end_volt.set("100.0")
        self.step_volt.set("5.0")
        self.hold_time.set("1.0")
        self.compliance.set("1.0")
        
        self.f = plt.figure(figsize=(6, 4), dpi=60)
        self.a = self.f.add_subplot(111)
        
        self.cv_f = plt.figure(figsize=(6, 4), dpi=60)
        self.cv_a = self.cv_f.add_subplot(111)
        
        self.multiv_f = plt.figure(figsize=(6, 4), dpi=60)
        self.multiv_a = self.multiv_f.add_subplot(111)
        
        self.curmon_f = plt.figure(figsize=(6, 4), dpi=60)
        self.curmon_a = self.curmon_f.add_subplot(111)
        
        n = ttk.Notebook(root,width=800)
        n.grid(row=0, column=0, columnspan=100, rowspan=100, sticky='NESW')
        
        self.f2 = ttk.Frame(n)
        self.f3 = ttk.Frame(n)
        self.f4 = ttk.Frame(n)
        self.f5 = ttk.Frame(n)

        self.iv=Settings(n)
        self.f1=self.iv.figure
        self.iv.buildLabels()
        
        self.duo = Settings(n)
        self.duo.steps=StringVar(root, "1")
        self.duo.delay=StringVar(root, "0")
        self.duo.measureTime=StringVar(root, "0")
        self.duo.samples=StringVar(root, "10")
        self.duo.integration=StringVar(root, "None")
        self.duo.keithley_compliance=StringVar(root, "0")
        self.duo.agilent_compliance1=StringVar(root, "0")
        self.duo.agilent_compliance2=StringVar(root, "0")
        self.duo.agilent_compliance3=StringVar(root, "0")
        self.duo.agilent_compliance4=StringVar(root, "0")

                                
        self.f6=self.duo.figure
        self.duo.buildLabels(compliance=False,hold=False,step=False)
        makeUnitEntry(self.duo.figure, "Number of Steps",self.duo.steps,3,"# of Steps")
        makeUnitEntry(self.duo.figure, "Measurement Delay",self.duo.delay,4,"secconds")
        makeUnitEntry(self.duo.figure, "Agilent Measuring Time",self.duo.measureTime,5,"secconds")
        makeUnitEntry(self.duo.figure, "Agilent Hold Time",self.duo.hold_time,6,"secconds")
        #makeUnitEntry(self.duo.figure, "Agilent Samples",self.duo.samples,6,"# of samples")
        makeUnitEntry(self.duo.figure, "Keithley Compliance",self.duo.keithley_compliance,8, "mA")
        makeUnitEntry(self.duo.figure, "Agilent Comp. Chan 1",self.duo.agilent_compliance1,9, "mA")
        makeUnitEntry(self.duo.figure, "Agilent Comp. Chan 2",self.duo.agilent_compliance2,10, "mA")
        makeUnitEntry(self.duo.figure, "Agilent Comp. Chan 3",self.duo.agilent_compliance3,11, "mA")
        makeUnitEntry(self.duo.figure, "Agilent Comp. Chan 4",self.duo.agilent_compliance4,12, "mA")
        Button(self.duo.figure, text="Save Configuation", command=self.saveSettings).grid(row=15,column=2)
        Button(self.duo.figure, text="Start", command=self.prepDuo).grid(row=13,column=2)
        Button(self.duo.figure, text="Stop", command=stopDuo).grid(row=14,column=2)
        
        
        n.add(self.duo.figure, text="Duo IV")
        n.add(self.iv.figure, text='Basic IV')        
        n.add(self.f2, text='CV')
        n.add(self.f3, text='Param Analyzer IV ')
        n.add(self.f4, text='Multiple IV')
        n.add(self.f5, text='Current Monitor')
        
        

        
        if "Windows" in platform.platform():
            self.filename.set("LabMasterData\iv_data")
            s = Label(self.f1, text="File name:")
            s.grid(row=0, column=1)
            s = Entry(self.f1, textvariable=self.filename)
            s.grid(row=0, column=2)
            
        compliance_choices={'mA', 'uA', 'nA'}

        
        
        self.recipients.set("adapbot@gmail.com")
        s = Label(self.f1, text="Email data to:")
        s.grid(row=6, column=1)
        s = Entry(self.f1, textvariable=self.recipients)
        s.grid(row=6, column=2)
    
        source_choices = {'Keithley 2400', 'Keithley 2657a'}
        self.source_choice.set('Keithley 2657a')
        s = OptionMenu(self.f1, self.source_choice, *source_choices)
        s.grid(row=0, column=7)
        
        s = Label(self.f1, text="Progress:")
        s.grid(row=11, column=1)
        
        s = Label(self.f1, text="Est finish at:")
        s.grid(row=12, column=1)
        
        timetext = str(time.asctime(time.localtime(time.time())))
        self.timer = Label(self.f1, text=timetext)
        self.timer.grid(row=12, column=2)
        
        self.pb = ttk.Progressbar(self.f1, orient="horizontal", length=200, mode="determinate")
        self.pb.grid(row=11, column=2, columnspan=5)
        self.pb["maximum"] = 100
        self.pb["value"] = 0
        
        self.canvas = FigureCanvasTkAgg(self.f, master=self.f1)
        self.canvas.get_tk_widget().grid(row=7, columnspan=10)
        self.a.set_title("IV")
        self.a.set_xlabel("Voltage")
        self.a.set_ylabel("Current")

        # plt.xlabel("Voltage")
        # plt.ylabel("Current")
        # plt.title("IV")
        self.canvas.draw()
        
        s = Button(self.f1, text="Start IV", command=self.prepare_values)
        s.grid(row=3, column=7)
        
        s = Button(self.f1, text="Stop", command=self.quit)
        s.grid(row=4, column=7)
        
        """
        /***********************************************************
         * CV GUI
         **********************************************************/
        """
        self.cv_filename = StringVar()
        self.cv_filename.set("LabMasterData\cv_data")
        
        if "Windows" in platform.platform():
            s = Label(self.f2, text="File name")
            s.grid(row=0, column=1)
            s = Entry(self.f2, textvariable=self.cv_filename)
            s.grid(row=0, column=2)
        
        self.cv_start_volt.set("0.0")
        s = Label(self.f2, text="Start Volt")
        s.grid(row=1, column=1)
        s = Entry(self.f2, textvariable=self.cv_start_volt)
        s.grid(row=1, column=2)       
        s = Label(self.f2, text="V")
        s.grid(row=1, column=3)
        
        self.cv_end_volt.set("40.0")
        s = Label(self.f2, text="End Volt")
        s.grid(row=2, column=1)
        s = Entry(self.f2, textvariable=self.cv_end_volt)
        s.grid(row=2, column=2)
        s = Label(self.f2, text="V")
        s.grid(row=2, column=3)
        
        self.cv_step_volt.set("1.0")
        s = Label(self.f2, text="Step Volt")
        s.grid(row=3, column=1)
        s = Entry(self.f2, textvariable=self.cv_step_volt)
        s.grid(row=3, column=2)
        s = Label(self.f2, text="V")
        s.grid(row=3, column=3)
        
        self.cv_hold_time.set("1.0")
        s = Label(self.f2, text="Hold Time")
        s.grid(row=4, column=1)
        s = Entry(self.f2, textvariable=self.cv_hold_time)
        s.grid(row=4, column=2)
        s = Label(self.f2, text="s")
        s.grid(row=4, column=3)

        self.cv_compliance.set("1.0")
        s = Label(self.f2, text="Compliance")
        s.grid(row=5, column=1)
        s = Entry(self.f2, textvariable=self.cv_compliance)
        s.grid(row=5, column=2)
        self.cv_compliance_scale.set('uA')
        s = OptionMenu(self.f2, self.cv_compliance_scale, *compliance_choices)
        s.grid(row=5, column=3)
        
        self.cv_recipients.set("adapbot@gmail.com")
        s = Label(self.f2, text="Email data to:")
        s.grid(row=6, column=1)
        s = Entry(self.f2, textvariable=self.cv_recipients)
        s.grid(row=6, column=2)
        
        s = Label(self.f2, text="Agilent LCRMeter Parameters", relief=RAISED)
        s.grid(row=7, column=1, columnspan=2)
        
        self.cv_impedance = StringVar()
        s = Label(self.f2, text="Function")
        s.grid(row=8, column=1)
        function_choices = {"CPD", "CPQ", "CPG", "CPRP", "CSD", "CSQ", "CSRS", "LPD",
                 "LPQ", "LPG", "LPRP", "LPRD", "LSD", "LSQ", "LSRS", "LSRD",
                 "RX", "ZTD", "ZTR", "GB", "YTD", "YTR", "VDID"}
        self.cv_function_choice = StringVar()
        self.cv_function_choice.set('CPD')
        s = OptionMenu(self.f2, self.cv_function_choice, *function_choices)
        s.grid(row=8, column=2)
        
        self.cv_impedance.set("2000")
        s = Label(self.f2, text="Impedance")
        s.grid(row=9, column=1)
        s = Entry(self.f2, textvariable=self.cv_impedance)
        s.grid(row=9, column=2)
        s = Label(self.f2, text="Ω")
        s.grid(row=9, column=3) 
        
        self.cv_frequencies.set("100, 200, 1000, 2000")
        s = Label(self.f2, text="Frequencies")
        s.grid(row=10, column=1)
        s = Entry(self.f2, textvariable=self.cv_frequencies)
        s.grid(row=10, column=2)
        s = Label(self.f2, text="Hz")
        s.grid(row=10, column=3)
        
        self.cv_amplitude.set("5.0")
        s = Label(self.f2, text="Signal Amplitude")
        s.grid(row=11, column=1)
        s = Entry(self.f2, textvariable=self.cv_amplitude)
        s.grid(row=11, column=2)
        s = Label(self.f2, text="V")
        s.grid(row=11, column=3)
        
        cv_int_choices = {"Short", "Medium", "Long"}
        s = Label(self.f2, text="Integration time")
        s.grid(row=12, column=1)
        self.cv_integration.set("Short")
        s = OptionMenu(self.f2, self.cv_integration, *cv_int_choices)
        s.grid(row=12, column=2)
    
        self.cv_source_choice.set('Keithley 2657a')
        s = OptionMenu(self.f2, self.cv_source_choice, *source_choices)
        s.grid(row=0, column=7)
        
        s = Label(self.f2, text="Progress:")
        s.grid(row=14, column=1)
        
        self.cv_pb = ttk.Progressbar(self.f2, orient="horizontal", length=200, mode="determinate")
        self.cv_pb.grid(row=14, column=2, columnspan=5)
        self.cv_pb["maximum"] = 100
        self.cv_pb["value"] = 0
        
        s = Label(self.f2, text="Est finish at:")
        s.grid(row=15, column=1)
        cv_timetext = str(time.asctime(time.localtime(time.time())))
        self.timer = Label(self.f2, text=cv_timetext)
        self.timer.grid(row=15, column=2)
        
        self.cv_canvas = FigureCanvasTkAgg(self.cv_f, master=self.f2)
        self.cv_canvas.get_tk_widget().grid(row=13, column=0, columnspan=10)
        self.cv_a.set_title("CV")
        self.cv_a.set_xlabel("Voltage")
        self.cv_a.set_ylabel("Capacitance")
        self.cv_canvas.draw()
        
        s = Button(self.f2, text="Start CV", command=self.cv_prepare_values)
        s.grid(row=3, column=7)
        
        s = Button(self.f2, text="Stop", command=self.quit)
        s.grid(row=4, column=7)
        
        """
        Multiple IV GUI
        """
        
        if "Windows" in platform.platform():
            self.multiv_filename.set("iv_data")
            s = Label(self.f4, text="File name:")
            s.grid(row=0, column=1)
            s = Entry(self.f4, textvariable=self.multiv_filename)
            s.grid(row=0, column=2)
        
        s = Label(self.f4, text="Start Volt")
        s.grid(row=1, column=1)
        s = Entry(self.f4, textvariable=self.multiv_start_volt)
        s.grid(row=1, column=2)
        s = Label(self.f4, text="V")
        s.grid(row=1, column=3)
        
        s = Label(self.f4, text="End Volt")
        s.grid(row=2, column=1)
        s = Entry(self.f4, textvariable=self.multiv_end_volt)
        s.grid(row=2, column=2)
        s = Label(self.f4, text="V")
        s.grid(row=2, column=3)
        
        s = Label(self.f4, text="Step Volt")
        s.grid(row=3, column=1)
        s = Entry(self.f4, textvariable=self.multiv_step_volt)
        s.grid(row=3, column=2)
        s = Label(self.f4, text="V")
        s.grid(row=3, column=3)

        s = Label(self.f4, text="Repeat Times")
        s.grid(row=4, column=1)
        s = Entry(self.f4, textvariable=self.multiv_times)
        s.grid(row=4, column=2)
        
        s = Label(self.f4, text="Hold Time")
        s.grid(row=5, column=1)
        s = Entry(self.f4, textvariable=self.multiv_hold_time)
        s.grid(row=5, column=2)
        s = Label(self.f4, text="s")
        s.grid(row=5, column=3)
        
        s = Label(self.f4, text="Compliance")
        s.grid(row=6, column=1)
        s = Entry(self.f4, textvariable=self.multiv_compliance)
        s.grid(row=6, column=2)
        self.multiv_compliance_scale.set('uA')
        s = OptionMenu(self.f4, self.multiv_compliance_scale, *compliance_choices)
        s.grid(row=6, column=3)
        
        self.multiv_recipients.set("adapbot@gmail.com")
        s = Label(self.f4, text="Email data to:")
        s.grid(row=7, column=1)
        s = Entry(self.f4, textvariable=self.multiv_recipients)
        s.grid(row=7, column=2)
    
        source_choices = {'Keithley 2400', 'Keithley 2657a'}
        self.multiv_source_choice.set('Keithley 2657a')
        s = OptionMenu(self.f4, self.multiv_source_choice, *source_choices)
        s.grid(row=0, column=7)
        
        s = Label(self.f4, text="Progress:")
        s.grid(row=11, column=1)
       
        s = Label(self.f4, text="Est finish at:")
        s.grid(row=12, column=1)
        
        self.multiv_timer = Label(self.f4, text=timetext)
        self.multiv_timer.grid(row=12, column=2)
        
        self.multiv_pb = ttk.Progressbar(self.f4, orient="horizontal", length=200, mode="determinate")
        self.multiv_pb.grid(row=11, column=2, columnspan=5)
        self.multiv_pb["maximum"] = 100
        self.multiv_pb["value"] = 0
        
        self.multiv_canvas = FigureCanvasTkAgg(self.multiv_f, master=self.f4)
        self.multiv_canvas.get_tk_widget().grid(row=8, columnspan=10)
        self.multiv_a.set_title("IV")
        self.multiv_a.set_xlabel("Voltage")
        self.multiv_a.set_ylabel("Current")

        self.multiv_canvas.draw()
        
        s = Button(self.f4, text="Start IVs", command=self.multiv_prepare_values)
        s.grid(row=3, column=7)
        
        s = Button(self.f4, text="Stop", command=self.quit)
        s.grid(row=4, column=7)
        
        """
        Current Monitor IV
        """
        
        
        if "Windows" in platform.platform():
            self.curmon_filename.set("iv_data")
            s = Label(self.f5, text="File name:")
            s.grid(row=0, column=1)
            s = Entry(self.f5, textvariable=self.curmon_filename)
            s.grid(row=0, column=2)
        
        s = Label(self.f5, text="Start Volt")
        s.grid(row=1, column=1)
        s = Entry(self.f5, textvariable=self.curmon_start_volt)
        s.grid(row=1, column=2)
        s = Label(self.f5, text="V")
        s.grid(row=1, column=3)
        
        s = Label(self.f5, text="End Volt")
        s.grid(row=2, column=1)
        s = Entry(self.f5, textvariable=self.curmon_end_volt)
        s.grid(row=2, column=2)
        s = Label(self.f5, text="V")
        s.grid(row=2, column=3)
        
        s = Label(self.f5, text="Step Volt")
        s.grid(row=3, column=1)
        s = Entry(self.f5, textvariable=self.curmon_step_volt)
        s.grid(row=3, column=2)
        s = Label(self.f5, text="V")
        s.grid(row=3, column=3)

        s = Label(self.f5, text="Test Time")
        s.grid(row=4, column=1)
        s = Entry(self.f5, textvariable=self.curmon_time)
        s.grid(row=4, column=2)
        s = Label(self.f5, text="M")
        s.grid(row=4, column=3)
        
        s = Label(self.f5, text="Hold Time")
        s.grid(row=5, column=1)
        s = Entry(self.f5, textvariable=self.curmon_hold_time)
        s.grid(row=5, column=2)
        s = Label(self.f5, text="s")
        s.grid(row=5, column=3)
        
        s = Label(self.f5, text="Compliance")
        s.grid(row=6, column=1)
        s = Entry(self.f5, textvariable=self.curmon_compliance)
        s.grid(row=6, column=2)
        self.curmon_compliance_scale.set('uA')
        s = OptionMenu(self.f5, self.curmon_compliance_scale, *compliance_choices)
        s.grid(row=6, column=3)
        
        self.curmon_recipients.set("adapbot@gmail.com")
        s = Label(self.f5, text="Email data to:")
        s.grid(row=7, column=1)
        s = Entry(self.f5, textvariable=self.curmon_recipients)
        s.grid(row=7, column=2)
    
        source_choices = {'Keithley 2400', 'Keithley 2657a'}
        self.curmon_source_choice.set('Keithley 2657a')
        s = OptionMenu(self.f5, self.curmon_source_choice, *source_choices)
        s.grid(row=0, column=7)
        
        
        s = Label(self.f5, text="Progress:")
        s.grid(row=11, column=1)
       
        s = Label(self.f5, text="Est finish at:")
        s.grid(row=12, column=1)
        
        self.curmon_timer = Label(self.f5, text=timetext)
        self.curmon_timer.grid(row=12, column=2)
        
        self.curmon_pb = ttk.Progressbar(self.f5, orient="horizontal", length=200, mode="determinate")
        self.curmon_pb.grid(row=11, column=2, columnspan=5)
        self.curmon_pb["maximum"] = 100
        self.curmon_pb["value"] = 0
        
        self.curmon_canvas = FigureCanvasTkAgg(self.curmon_f, master=self.f5)
        self.curmon_canvas.get_tk_widget().grid(row=8, columnspan=10)
        self.curmon_a.set_title("IV")
        self.curmon_a.set_xlabel("Voltage")
        self.curmon_a.set_ylabel("Current")

        self.curmon_canvas.draw()
        
        s = Button(self.f5, text="Start CurMon", command=self.curmon_prepare_values)
        s.grid(row=3, column=7)
        
        s = Button(self.f5, text="Stop", command=self.quit)
        s.grid(row=4, column=7)
        print("Interface Generated")
        loadSettings(self)
        
    def update(self):
        while self.outputdata.qsize():
            try:
                (data, percent, timeremain) = self.outputdata.get(0)
                
                if self.type is 0:
                    print "Percent done:" + str(percent)
                    self.pb["value"] = percent
                    self.pb.update()
                    (voltages, currents) = data
                    negative = False
                    for v in voltages:
                        if v < 0:
                            negative = True
                    if negative:
                        line, = self.a.plot(map(lambda x: x * -1.0, voltages), map(lambda x: x * -1.0, currents))
                    else:
                        line, = self.a.plot(voltages, currents)
                    line.set_antialiased(True)
                    line.set_color('r')
                    self.a.set_title("IV")
                    self.a.set_xlabel("Voltage [V]")
                    self.a.set_ylabel("Current [A]")
                    self.canvas.draw()

                    timetext = str(time.asctime(time.localtime(time.time() + timeremain)))
                    self.timer = Label(self.f1, text=timetext)
                    self.timer.grid(row=12, column=2)
                    
                    
                elif self.type is 1:
                    (voltages, caps) = data
                    print "Percent done:" + str(percent)
                    self.cv_pb["value"] = percent
                    self.cv_pb.update()
                    # print "Caps:+++++++"
                    # print caps
                    # print "============="
                    colors = {0:'b', 1:'g', 2:'r', 3:'c', 4:'m', 5:'k'}
                    i = 0
                    for c in caps:
                        """
                        print "VOLTS++++++"
                        print voltages
                        print "ENDVOLTS===="
                        #(a, b) = c[0]
                        print "CAPSENSE+++++"
                        print c
                        
                        print "ENDCAP======="
                        """
                        
                        if self.first:
                            
                            line, = self.cv_a.plot(voltages, c, label=(self.cv_frequencies.get().split(",")[i] + "Hz"))
                            self.cv_a.legend()
                        else:
                            line, = self.cv_a.plot(voltages, c)
                        line.set_antialiased(True)
                        line.set_color(colors.get(i))   
                        i += 1
                        self.cv_a.set_title("CV")
                        self.cv_a.set_xlabel("Voltage [V]")
                        self.cv_a.set_ylabel("Capacitance [F]")
                        self.cv_canvas.draw()
                        
                    timetext = str(time.asctime(time.localtime(time.time() + timeremain)))
                    self.timer = Label(self.f2, text=timetext)
                    self.timer.grid(row=15, column=2)
                    self.first=False
                    
                elif self.type is 2:
                    pass
                
                elif self.type is 3:
                    if self.first:
                        #self.multiv_f.clf()
                        pass
                    print "Percent done:" + str(percent)
                    self.multiv_pb["value"] = percent
                    self.multiv_pb.update()
                    (voltages, currents) = data
                    negative = False
                    for v in voltages:
                        if v < 0:
                            negative = True
                    if negative:
                        line, = self.multiv_a.plot(map(lambda x: x * -1.0, voltages), map(lambda x: x * -1.0, currents))
                    else:
                        line, = self.multiv_a.plot(voltages, currents)
                    line.set_antialiased(True)
                    line.set_color('r')
                    self.multiv_a.set_title("IV")
                    self.multiv_a.set_xlabel("Voltage [V]")
                    self.multiv_a.set_ylabel("Current [A]")
                    self.multiv_canvas.draw()

                    timetext = str(time.asctime(time.localtime(time.time() + timeremain)))
                    self.multiv_timer = Label(self.f4, text=timetext)
                    self.multiv_timer.grid(row=12, column=2)
                    
                elif self.type is 4:
                    
                    print "Percent done:" + str(percent)
                    self.curmon_pb["value"] = percent
                    self.curmon_pb.update()
                    (voltages, currents) = data
                    negative = False
                    for v in voltages:
                        if v < 0:
                            negative = True
                    if negative:
                        line, = self.curmon_a.plot(map(lambda x: x * -1.0, voltages), map(lambda x: x * -1.0, currents))
                    else:
                        line, = self.curmon_a.plot(voltages, currents)
                    line.set_antialiased(True)
                    line.set_color('r')
                    self.curmon_a.set_title("IV")
                    self.curmon_a.set_xlabel("Voltage [V]")
                    self.curmon_a.set_ylabel("Current [A]")
                    self.curmon_canvas.draw()

                    timetext = str(time.asctime(time.localtime(time.time() + timeremain)))
                    self.curmon_timer = Label(self.f5, text=timetext)
                    self.curmon_timer.grid(row=12, column=2)
            except Queue.Empty:
                pass
                
    def quit(self):
        print "placing order"
        self.stop.put("random")
        self.stop.put("another random value")
        
    def prepDuo(self):
        self.startDuo()
        #print("Creating new thread.")
        #self.duoThread = threading.Thread(target=self.startDuo)
        #self.duoThread.start()
        
    def startDuo(self):
        obj=self.duo
        return runDuo(delay=float(obj.delay.get()),
                      measureTime=float(obj.measureTime.get()),
                      samples=float(obj.samples.get()),
                      holdTime=float(obj.hold_time.get()),
                      startV=float(obj.start_volt.get()),
                      endV=float(obj.end_volt.get()),
                      steps=int(obj.steps.get()),
                      integration=obj.integration.get(),
                      keithley_comp=float(obj.keithley_compliance.get()),
                      comp1=float(obj.agilent_compliance1.get()),
                      comp2=float(obj.agilent_compliance2.get()),
                      comp3=float(obj.agilent_compliance3.get()),
                      comp4=float(obj.agilent_compliance4.get())
        )
    
    def prepare_values(self):
        print "preparing iv values"
        input_params = ((self.compliance.get(), self.compliance_scale.get(), self.start_volt.get(), self.end_volt.get(), self.step_volt.get(), self.hold_time.get(), self.source_choice.get(), self.recipients.get(), self.filename.get()), 0)
        self.inputdata.put(input_params)   
        self.f.clf()        
        self.a = self.f.add_subplot(111)
        self.type = 0
        
    def cv_prepare_values(self):
        print "preparing cv values"
        self.first = True
        input_params = ((self.cv_compliance.get(), self.cv_compliance_scale.get(), self.cv_start_volt.get(), self.cv_end_volt.get(), self.cv_step_volt.get(), self.cv_hold_time.get(), self.cv_source_choice.get(),
                         map(lambda x: x.strip(), self.cv_frequencies.get().split(",")), self.cv_function_choice.get(), self.cv_amplitude.get(), self.cv_impedance.get(), self.cv_integration.get(), self.cv_recipients.get()
                         , self.cv_filename.get()), 1)
        print input_params
        self.saveSettings()
        self.inputdata.put(input_params)  
        self.cv_f.clf()
        self.cv_a = self.cv_f.add_subplot(111)
        self.type = 1

    def saveSettings(self):
        settings={
            'duo': getDuoSettings(self),
            'cv': getCVSettings(self),
            'iv': None
        }       
        try:
            with open(SAVE_FILE, 'w+') as f:
                f.write(json.dumps(settings))
                print('Settings saved in the file %s'%SAVE_FILE)
        except Exception as e:
            print(e)

    def multiv_prepare_values(self):
        
        print "preparing mult iv values"
        self.first = True
        input_params = ((self.multiv_compliance.get(), self.multiv_compliance_scale.get(), self.multiv_start_volt.get(), self.multiv_end_volt.get(), self.multiv_step_volt.get(), self.multiv_hold_time.get(), self.multiv_source_choice.get(), self.multiv_recipients.get(), self.multiv_filename.get(), self.multiv_times.get()), 3)
        self.inputdata.put(input_params)   
        self.multiv_f.clf()        
        self.multiv_a = self.multiv_f.add_subplot(111)
        self.type = 3
    
    def curmon_prepare_values(self):
        
        print "preparing current monitor values"
        self.first = True
        input_params = ((self.curmon_compliance.get(), self.curmon_compliance_scale.get(), self.curmon_start_volt.get(), self.curmon_end_volt.get(), self.curmon_step_volt.get(), self.curmon_hold_time.get(), self.curmon_source_choice.get(), self.curmon_recipients.get(), self.curmon_filename.get(), self.curmon_time.get()), 4)
        self.inputdata.put(input_params)   
        self.curmon_f.clf()        
        self.curmon_a = self.curmon_f.add_subplot(111)
        self.type = 4
        

class ThreadedProgram:
    
    def __init__(self, master):
        self.master = master
        self.inputdata = Queue.Queue()
        self.outputdata = Queue.Queue()
        self.stopqueue = Queue.Queue()
        
        self.running = 1
        self.gui = GuiPart(master, self.inputdata, self.outputdata, self.stopqueue)
        
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()
        self.periodicCall()
        self.measuring = False
        self.master.protocol("WM_DELETE_WINDOW", self.endapp)

    
    def periodicCall(self):
        # print "Period"
        self.gui.update()
        if self.stopqueue.qsize()==1:
            pass
            #self.stopqueue.get()
            #print "Exiting program"
            #import sys
            #self.master.destroy()
            #self.running = 0
            #sys.exit(0)
            
        self.master.after(200, self.periodicCall)
    
    def workerThread1(self):
        while self.running:
            if self.inputdata.empty() is False and self.measuring is False:
                self.measuring = True
                print "Instantiating Threads"
                (params, type) = self.inputdata.get()
                if type is 0:
                    getvalues(params, self.outputdata, self.stopqueue)
                elif type is 1:
                    cv_getvalues(params, self.outputdata, self.stopqueue)
                elif type is 2:
                    spa_getvalues(params, self.outputdata, self.stopqueue)
                elif type is 3:
                    multiv_getvalues(params, self.outputdata, self.stopqueue)
                elif type is 4:
                    curmon_getvalues(params, self.outputdata, self.stopqueue)
                else:
                    pass
                self.measuring = False
    def endapp(self):
        self.running = 0
        self.master.destroy()
        import sys
        sys.exit(0)
        
root = Tk()
root.geometry('800x800')
root.title('LabMaster')
client = ThreadedProgram(root)
root.mainloop() 
