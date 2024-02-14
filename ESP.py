import serial
import serial.tools.list_ports
from time import time, sleep
from threading import *
import numpy as np

class Parameter():
    def __init__(self, name, cmd, min, max, scaling = 1, formating = '{0:.0f}', hidden = False, step = 1, type = int):

        self.name = name
        self.cmd = cmd
        self.min = min
        self.max = max
        self.scaling = scaling
        self.formating = formating
        self.hidden = hidden
        self.step = step
        self.type = type
        self.currentValue = 0
        self.slider = None
        self.label = None
    def str(self):
        value = self.formating.format(self.currentValue)
        return f'{self.name} {value}'

class EventList():
    listofAll = []
    def __init__(self,ID, name):
        self.ID = ID
        self.name = name
        self.space = 100
        self.time = np.zeros([self.space ]).astype(int)
        self.data = np.zeros([self.space ]).astype(int)
        self.nData = 0
        self.lastValue = 0
        EventList.listofAll.append(self)
    def addEvent(self, when, data):

        if self.nData >= self.space:
            print(f'extend storage for {self.name}')
            self.reduceSpace()
            #np.append(self.time, self.time[0:1000])
            #np.append(self.data, self.data[0:1000])
        if self.nData > 0:
            if data == self.data[self.nData - 1]: return
        self.time[self.nData] = when
        self.data[self.nData] = data
        self.nData += 1
        self.lastValue = data

    def reduceSpace(self):
        minTime = 0
        for ev in EventList.listofAll:
            minTime = max(minTime, ev.time2Half())
        for ev in EventList.listofAll:
            ev.reduce2Time(minTime)

    def time2Half(self):
        index = int(self.nData - self.space / 2)
        if index <= 0: return 0
        return self.time[index]

    def reduce2Time(self, lowest):
        kill = 0
        for i in range(self.nData):
            if self.time[i] < lowest: kill = i
        if kill <= 0:
            print(f'No cut for {self.name}')
            return
        print(f'{self.name} reduction kill point {kill} data in buffer {self.nData}')
        self.time[0:self.nData-kill] = self.time[kill:self.nData]
        self.data[0:self.nData-kill] = self.data[kill:self.nData]
        self.nData -= kill

class ESP():
    def __init__(self, parameterFile, port = None, baud = 115200):
        self.verbose = True
        self.parameterFile = parameterFile
        self.semaphore = Semaphore(1)
        self.tMin = 4007496193
        self.tMax = 0
        self.widget = None
        if port is None:
            ports = serial.tools.list_ports.comports()
            for p, desc, hwid in sorted(ports):
                if 'CP210' in desc: port = p
            if port is None: raise Exception("No CP210x Port available")
        self.port = serial.Serial(port, baud)
        self.parameter = []
        self.parameter.append(Parameter('Wasser marsch Gewicht', 'g', -1.0, 8.0, 1e3,'{0:5.3f} kg', step = 0.1))
        self.parameter.append(Parameter('Max Rampen Gewicht', 'A', -1.0, 8.0, 1e3,'{0:5.3f} kg', step = 0.1))
        self.parameter.append(Parameter('Maximal Gewicht', 'G', 2, 10,1e3,'{0:5.3f} kg',step=0.1))
        self.parameter.append(Parameter('Pumpe an', 'P', 1, 60, 1,'{0:5.0f} sec'))
        self.parameter.append(Parameter('Pumpe Pause', 'p', 1, 60, 1,'{0:5.0f} sec'))
        self.parameter.append(Parameter('Schritt auf', 'U', 0.0, 1.0, 1e3,'{0:5.3f} kg', step=0.01))
        self.parameter.append(Parameter('Schritt runter', 'D', 0.0, 1.0, 1e3,'{0:5.3f} kg', step=0.01))
        self.parameter.append(Parameter('Wasserzeit', 'V', 1, 60, 1,'{0:5.0f} sec'))
        self.parameter.append(Parameter('Pausenzeit', 'W', 1, 60, 60.0,'{0:5.0f} min'))
        self.parameter.append(Parameter('Rampenzeit', 'K', 1, 10, 60.0,'{0:5.0f} min'))
        self.parameter.append(Parameter('Anzahl Wasser Zyklen', 'Z', 1, 25))
        self.parameter.append(Parameter('Zeit zwischen Zyklen', 'v', 1, 30, 1,'{0:5.0f} sec'))
        self.parameter.append(Parameter('M', 'M', 0, 0, hidden = True))
        self.modePara = self.parameter[-1]
        self.parameter.append(Parameter('r', 'r', 0, 0, hidden = True))
        self.parameter.append(Parameter('s', 's', 0, 0, hidden = True))
        self.parameter.append(Parameter('t', 't', 0, 0, hidden = True))
        self.parameter.append(Parameter('u', 'u', 0, 0, hidden = True))
        self.parameter.append(Parameter('Z1', 'Z1', 0, 0, hidden = True, type = float))
        self.parameter.append(Parameter('Z2', 'Z2', 0, 0, hidden = True, type = float))
        self.parameter.append(Parameter('S1', 'S1', 0, 0, hidden = True, type = float))
        self.parameter.append(Parameter('S2', 'S2', 0, 0, hidden = True, type = float))
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
        self.control = int(self.modePara.currentValue)
        self.deviceNames = ['Pumpe', 'Fan 1', 'Fan 2', 'UVC']
        self.deviceStates = ['aus', 'an', 'auto', 'party']
    def connectWidget(self, widget):
        self.widget = widget

    def saveParameter(self, toESP=True, toFile=True):
        if toESP:
            for para in self.parameter:
                if para.type == float:
                    self.sendCMD(f'{para.cmd}:{para.currentValue * para.scaling}')
                else:
                    self.sendCMD(f'{para.cmd}:{round(para.currentValue * para.scaling)}')
        if toFile:
            with open(self.parameterFile, "w") as file:
                for para in self.parameter:
                    file.write(f'{para.cmd}:{para.currentValue}\n')

    def loadParameter(self, file):
        try:
            with open(file) as f:
                lines = f.readlines()
                if self.verbose: print("Import <" + file + "> lines " + str(len(lines)))
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
        return (self.control >> (dev * 2)) & 3
    def setDevice(self, dev, value):
        shift = dev * 2
        self.control = (self.control & ~(3 << shift))| (value << shift)
        self.modePara.currentValue = float(self.control)
        self.saveParameter()
        self.sendCMD('F:')
    #    self.sendCMD('e:1')
    def setNull(self):
        if self.verbose: print('Setze Nullmarke')
        self.sendCMD('C:0')


    def set10(self):
        self.sendCMD('C:10000')
        if self.verbose: print('Kalibriere 10kGg')
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
        if self.widget is not None: self.widget.updateDisplay()
    def sendCMD(self, msg):
        if self.verbose: print(f'send <{msg}> to ESP')
        msg = msg + '\n'
        self.port.write(bytes(msg.encode()))
    def stop(self):
        self.readerRun = False
        self.sendCMD('F:')

    def reset(self):
        if self.verbose: print('ESP Reset')
        self.port.setRTS(False)
        self.sendCMD('F:')
        sleep(0.5)
        self.port.setRTS(True)
        self.sendCMD('F:')
        sleep(0.5)
        self.port.setRTS(False)
        self.sendCMD('F:')

    def readerProcess(self):
        while (self.readerRun):
            msg = self.port.read_until().decode("utf-8")
            if self.verbose: print(f'received: {msg}', end='')
            self.analyze(msg)

        if self.verbose: print('ESP Reader stopped')