import visa

#This is used to connect to devices using gpib
class Instrument:
    def __init__(self):
        self.inst=None

    def getName(self,inst=None):
        if inst is None:
            if self.inst is not None:
                inst=self.inst
            else:
                raise(Exception("Called getName without an Instrument selected."))
        return str(inst.query('*IDN?')).lower()


    def test(self):
        return "working"

    def connect(self,name,model=None):
        print("always get here")
        rm=visa.ResourceManager()
        print("never get here")
        for device in rm.list_resources():
            inst=rm.open_resource(device)
            idn=self.getName(inst).lower()
            if name in idn and (model is None or model in idn):
                print("Connected to the device named %s"%name)
                self.inst=inst
                return inst
        if self.inst is None:
            raise Exception("The device %s was not found."%name)

    def reset(self):
        self.inst.write("*RST;")
