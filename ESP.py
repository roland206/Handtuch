import serial
import serial.tools.list_ports
from time import time, sleep
from threading import *
import numpy as np
from Events import *
class NoPort(Exception):
    def __init__(self, ports):
        self.ports = ports

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



class ESP():
    def __init__(self, parameterFile, reporter, port = None, baud = 115200, useHW = True):
        self.reporter = reporter
        self.log = False
        self.verbose = False
        self.parameterFile = parameterFile
        self.semaphore = Semaphore(1)
        self.tMin = 4007496193
        self.tMax = 0
        self.ladeVorgang = False
        self.widget = None
        self.useHW = useHW
        if useHW:
            if port is None:
                ports = serial.tools.list_ports.comports()
                for p, desc, hwid in sorted(ports):
                    if 'CP210' in desc: port = p
                if port is None: raise NoPort(ports)
            self.port = serial.Serial(port, baud)
        else:
            self.port = None
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
        self.parameter.append(Parameter('Rampenzeit', 'K', 1, 30, 60.0,'{0:5.0f} min'))
        self.parameter.append(Parameter('Anzahl Wasser Zyklen', 'Z', 1, 25))
        self.parameter.append(Parameter('Zeit zwischen Zyklen', 'v', 1, 30, 1,'{0:5.0f} sec'))
        self.parameter.append(Parameter('M', 'M', 0, 0, hidden = True))
        self.modePara = self.parameter[-1]
        self.parameter.append(Parameter('r', 'r', 0, 0, hidden = True))
        self.parameter.append(Parameter('s', 's', 0, 0, hidden = True))
        self.parameter.append(Parameter('t', 't', 0, 0, hidden = True))
        self.parameter.append(Parameter('u', 'u', 0, 0, hidden = True))
        self.parameter.append(Parameter('a', 'a', 0, 0, hidden = True))
        self.parameter.append(Parameter('c', 'c', 0, 0, hidden = True))
        self.parameter.append(Parameter('b', 'b', 0, 0, hidden = True, type = float))
        self.parameter.append(Parameter('d', 'd', 0, 0, hidden = True, type = float))
        self.loadParameter(self.parameterFile)
        self.events = createEvents()

        if useHW:
            self.readerRun = True
            self.reader = Thread(target = self.readerProcess)
            self.reader.start()
            self.sendCMD(f'T:{int(time())}') # set the ESP time
        self.control = int(self.modePara.currentValue)
        self.deviceNames = ['Pumpe', 'Fan 1', 'Fan 2', 'UVC']
        self.deviceStates = ['aus', 'an', 'auto', 'party']

        if useHW: self.loadEventsFromFile(self.reporter.getCacheFilename())

    def loadEventsFromFile(self, file):
        print(f'Lade log-file <{file}>')
        try:
            with open(file) as f:
                lines = f.readlines()
                for line in lines:
                    self.analyze(line)
        except OSError:
            print("File not found <" + file + ">")
    def connectWidget(self, widget):
        self.widget = widget
    def logging(self, flag):
        self.log = flag
        if flag: self.sendCMD('F:')
    def saveParameter(self, toESP=True, toFile=True):
        if toESP and self.useHW:
            msg = ''
            for para in self.parameter:
                if msg != '' : msg += ':'
                if para.type == float:
                    msg += f'{para.cmd}:{para.currentValue * para.scaling}'
                else:
                    msg += f'{para.cmd}:{round(para.currentValue * para.scaling)}'
            self.sendCMD(msg)
            self.sendCMD('F:')
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
        if dev == 4: return self.control & 0x400
        return (self.control >> (dev * 2)) & 3
    def setDevice(self, dev, value):
        if dev == 4:
            if value:
                self.control |= 0x400
            else:
                self.control &= ~0x400
        else:
            shift = dev * 2
            self.control = (self.control & ~(3 << shift))| (value << shift)
        self.modePara.currentValue = float(self.control)
        self.saveParameter()

    def setNull(self):
        if self.verbose: print('Setze Nullmarke')
        self.sendCMD('C:0')

    def set10(self):
        self.sendCMD('C:12000')
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
        if input[0] =='a':
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
        else:
            print(f'Kommentar {cmd}')
        if self.log: self.reporter.logEvent(cmd)
        self.releaseAccess(0)
        if self.widget is not None: self.widget.updateDisplay()
    def sendCMD(self, msg):
        if self.verbose: print(f'send <{msg}> to ESP')
        msg = msg + '\n'
        if self.useHW:
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
