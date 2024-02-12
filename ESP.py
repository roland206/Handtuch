import serial
import serial.tools.list_ports
from time import time, sleep
from threading import *
import numpy as np

class Parameter():
    def __init__(self, name, cmd, min, max, scaling = 1, formating = '{0:.0f}', hidden = False, step = 1):
        self.name = name
        self.cmd = cmd
        self.min = min
        self.max = max
        self.scaling = scaling
        self.formating = formating
        self.hidden = hidden
        self.step = step
        self.currentValue = 0
        self.slider = None
        self.label = None
    def str(self):
        value = self.formating.format(self.currentValue)
        return f'{self.name} {value}'

class EventList():
    def __init__(self,ID, name):
        self.ID = ID
        self.name = name
        self.time = np.zeros([1000]).astype(int)
        self.data = np.zeros([1000]).astype(int)
        self.nData = 0
        self.lastValue = 0
    def addEvent(self, when, data):

        if self.nData >= self.time.size:
            print(f'extend storage for {self.name}')
            np.append(self.time, self.time[0:1000])
            np.append(self.data, self.data[0:1000])
        if self.nData > 0:
            if data == self.data[self.nData - 1]: return
        self.time[self.nData] = when
        self.data[self.nData] = data
        self.nData += 1
        self.lastValue = data
#        print(f'Add event at {when} to {self.name}')
class ESP():
    def __init__(self, parameterFile, port = None, baud = 115200):
        self.parameterFile = parameterFile
        self.semaphore = Semaphore(1)
        self.tMin = 4007496193
        self.tMax = 0
        self.widget = None
        if port is None:
            ports = serial.tools.list_ports.comports()
            for p, desc, hwid in sorted(ports):
                if 'CP210x' in desc: port = p
            if port is None: raise Exception("No CP210x Port available")
        self.port = serial.Serial(port, baud)
        self.parameter = []
        self.parameter.append(Parameter('Wasser marsch Gewicht', 'g', -1.0, 8.0, 1e3,'{0:5.3f} kg', step = 0.1))
        self.parameter.append(Parameter('Maximal Gewicht', 'G', 2, 10,1e3,'{0:5.3f} kg',step=0.1))
        self.parameter.append(Parameter('Pumpe an', 'P', 1, 60, 1e3,'{0:5.0f} sec'))
        self.parameter.append(Parameter('Pumpe Pause', 'p', 1, 60, 1e3,'{0:5.0f} sec'))
        self.parameter.append(Parameter('Schritt auf', 'U', 0.0, 1.0, 1e3,'{0:5.3f} kg', step=0.01))
        self.parameter.append(Parameter('Schritt runter', 'D', 0.0, 1.0, 1e3,'{0:5.3f} kg', step=0.01))
        self.parameter.append(Parameter('Wasserzeit', 'V', 1, 60, 1e3,'{0:5.0f} sec'))
        self.parameter.append(Parameter('Pausenzeit', 'v', 1, 60, 60e3,'{0:5.0f} min'))
        self.parameter.append(Parameter('Anzahl Wasser Zyklen', 'Z', 1, 25))
        self.parameter.append(Parameter('r', 'r', 0, 0, hidden = True))
        self.parameter.append(Parameter('s', 's', 0, 0, hidden = True))
        self.parameter.append(Parameter('t', 't', 0, 0, hidden = True))
        self.parameter.append(Parameter('u', 'u', 0, 0, hidden = True))
        self.parameter.append(Parameter('Z1', 'Z1', 0, 0, hidden = True))
        self.parameter.append(Parameter('Z2', 'Z2', 0, 0, hidden = True))
        self.parameter.append(Parameter('S1', 'S1', 0, 0, hidden = True))
        self.parameter.append(Parameter('S2', 'S2', 0, 0, hidden = True))
        self.loadParameter(self.parameterFile)
        self.events = {}
        self.events['S'] = EventList('S', 'Status')
        self.events['T'] = EventList('T', 'Temperatur')
        self.events['H'] = EventList('H', 'Luftfeuchte')
        self.events['G'] = EventList('G', 'Gewicht')
        self.events['Z'] = EventList('Z', 'Wasser Marsch')

        self.readerRun = True
        self.reader = Thread(target = self.readerProcess)
        self.reader.start()
        self.sendCMD(f'T:{int(time())}') # set the ESP time
        self.sendCMD('F:')
        self.control = 0xa0
        self.deviceNames = ['Pumpe', 'Fan 1', 'Fan 2', 'UVC']
        self.deviceStates = ['aus', 'an', 'auto', 'party']
    def connectWidget(self, widget):
        self.widget = widget

    def saveParameter(self, toESP=True, toFile=True):
        if toESP:
            for para in self.parameter:
                self.sendCMD(f'{para.cmd}:{round(para.currentValue * para.scaling)}')
        if toFile:
            with open(self.parameterFile, "w") as file:
                for para in self.parameter:
                    file.write(f'{para.cmd}:{para.currentValue}\n')

    def loadParameter(self, file):
        try:
            with open(file) as f:
                lines = f.readlines()
                print("Import <" + file + "> lines " + str(len(lines)))
                for line in lines:
                    line = line[0:-1]
                    entries = line.split(":")
                    if len(entries) == 2:
                        id = entries[0]
                        found = False
                        for para in self.parameter:
                            if id == para.cmd:
                                para.currentValue = float(entries[1])
                                found = True
                                break
                        if not found: print(f'Unknown Parameter <{line}>')
                    else:
                        print("unverstandene Zeile <" + line + "> ignoriert")

        except OSError:
            print("File not found <" + file + ">")
    def getDevice(self, dev):
        return (self.control >> (dev * 2) ) & 3
    def setDevice(self, dev, value):
        shift = dev * 2
        self.control = (self.control & ~(3 << shift))| (value << shift)
        self.sendCMD(f'M:{self.control}')
        self.sendCMD('F:')

    def setNull(self):
        print('Setze Null')
        self.sendCMD('C:0')


    def set10(self):
        self.sendCMD('C:10000')
        print('Setze 10kG')
    def setState(self, state):
        self.sendCMD(f'X:{state}')
    def gainAccess(self, id):
        self.semaphore.acquire()

    def releaseAccess(self,id):
        self.semaphore.release()

    def analyze(self, cmd):
        input = cmd.split(':')
        self.gainAccess(0)
        if input[0] =='Z1':
            for iCmd in range(0, len(input), 2):
                cmd = input[iCmd]
                for para in self.parameter:
                    if para.cmd == cmd: para.currentValue = float(input[iCmd + 1])
            self.saveParameter(toESP = False)

        elif input[0] == 'W':
            when = int(input[1])
            self.tMin = min(self.tMin, when)
            self.tMax = max(self.tMax, when)
            for i in range(2, len(input), 2):
                ev = self.events[input[i]]
                ev.addEvent(when, int(input[i+1]))
        self.releaseAccess(0)
        if self.widget is not None: self.widget.updateDisplay(self.events['S'].lastValue)
    def sendCMD(self, msg):
        print(f'send <{msg}> to ESP')
        msg = msg + '\n'
        self.port.write(bytes(msg.encode()))
    def stop(self):
        self.readerRun = False
        self.sendCMD('F:')

    def reset(self):
        self.port.setRTS(False)
        time.sleep(0.5)
        self.port.setRTS(True)
        time.sleep(0.5)
        self.port.setRTS(False)

    def readerProcess(self):
        w = 100
        i=0
        while (self.readerRun):
            msg = self.port.read_until().decode("utf-8")
#            sleep(2)
#            msg = f'W:{int(time())}:G:{w}:S:{i}:Z:2000:T:{21123+w}:H:{50123+w}'
            w += 100
            if w > 5000: w = 0
            print(msg)
            self.analyze(msg)
            i = (i + 23798463) & 0xfffffff

        print('ESP Reader stopped')