import json

SAVE_FILE=".settings.json"
def saveSettings(gui):
    settings={
            'cv': getCVSettings(gui),
            'iv': None
        }       
    try:
        with open(SAVE_FILE, 'w+') as f:
            f.write(json.dumps(settings))
            print('Settings saved in the file %s'%SAVE_FILE)
    except Exception as e:
        print(e)
    return

def loadSettings(gui):
    settings=None
    try:
        print("Loading save.")
        with open(SAVE_FILE, 'r') as f:
            f.seek(0)
            settings=json.loads(f.read())
        setCVSettings(gui,settings['cv'])
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
