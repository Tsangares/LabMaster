import json

SAVE_FILE=".settings.json"

def loadSettings(gui):
    settings=None
    try:
        with open(SAVE_FILE, 'r') as f:
            f.seek(0)
            settings=json.loads(f.read())
        setCVSettings(gui,settings['cv'])
        setDuoSettings(gui,settings['duo'])
        print("Loaded saved configuration.")
    except Exception as e:
        print(e)

def getCVSettings(gui):
    cv={}
    cv['compliance']=gui.cv_compliance.get()
    cv['complianceScale']=gui.cv_compliance_scale.get()
    cv['startVoltage']=gui.cv_start_volt.get()
    cv['endVoltage']=gui.cv_end_volt.get()
    cv['stepVoltage']=gui.cv_step_volt.get()
    cv['holdTime']=gui.cv_hold_time.get()
    cv['device']=gui.cv_source_choice.get()
    cv['freq']=gui.cv_frequencies.get().split(",")
    cv['function']=gui.cv_function_choice.get()
    cv['amplitude']=gui.cv_amplitude.get()
    cv['impedance']=gui.cv_impedance.get()
    cv['integration']=gui.cv_integration.get()
    cv['recipients']=gui.cv_recipients.get()
    return cv

def setCVSettings(gui,cv):
    gui.cv_compliance.set(cv['compliance'])
    gui.cv_compliance_scale.set(cv['complianceScale'])
    gui.cv_start_volt.set(cv['startVoltage'])
    gui.cv_end_volt.set(cv['endVoltage'])
    gui.cv_step_volt.set(cv['stepVoltage'])
    gui.cv_hold_time.set(cv['holdTime'])
    gui.cv_source_choice.set(cv['device'])
    gui.cv_function_choice.set(cv['function'])
    gui.cv_amplitude.set(cv['amplitude'])
    gui.cv_impedance.set(cv['impedance'])
    gui.cv_integration.set(cv['integration'])
    gui.cv_recipients.set(cv['recipients'])
    
    freq=""
    for f in cv['freq']:
        freq+=f+','
    freq=freq[:-1]
    gui.cv_frequencies.set(freq)
    
    return



def getDuoSettings(gui):
    s=gui.duo
    duo={}
    duo['holdTime']=s.hold_time.get()
    duo['start']=s.start_volt.get()
    duo['stop']=s.end_volt.get()
    duo['steps']=s.steps.get()
    duo['delay']=s.delay.get()
    duo['measureTime']=s.measureTime.get()
    duo['samples']=s.samples.get()
    duo['integration']=s.integration.get()
    duo['keithley_comp']=s.keithley_compliance.get()
    duo['comp1']=s.agilent_compliance1.get()
    duo['comp2']=s.agilent_compliance2.get()
    duo['comp3']=s.agilent_compliance3.get()
    duo['comp4']=s.agilent_compliance4.get()
    duo['email']=s.recipients.get()
    return duo

def setDuoSettings(gui,duo):
    s=gui.duo
    s.hold_time.set(duo['holdTime'])
    s.start_volt.set(duo['start'])
    s.end_volt.set(duo['stop'])
    s.steps.set(duo['steps'])
    s.delay.set(duo['delay'])
    s.measureTime.set(duo['measureTime'])
    s.samples.set(duo['samples'])
    s.integration.set(duo['integration'])
    s.keithley_compliance.set(duo['keithley_comp'])
    s.agilent_compliance1.set(duo['comp1'])
    s.agilent_compliance2.set(duo['comp2'])
    s.agilent_compliance3.set(duo['comp3'])
    s.agilent_compliance4.set(duo['comp4'])
    s.recipients.set(duo['email'])


