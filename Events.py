import numpy as np
def createEvents():
    events = {}
    events['S'] = EventList('S', 'Status')
    events['T'] = EventList('T', 'Temperatur', type=float, scale=1e-3)
    events['H'] = EventList('H', 'Luftfeuchte', type=float, scale=1e-3)
    events['G'] = EventList('G', 'Gewicht', type=float, scale=1e-3)
    events['Z'] = EventList('Z', 'Wasser Marsch', type=float, scale=1e-3)
    return events

def loadEventFile(events, file):
    print(f'Lade log-file <{file}>')
    try:
        with open(file) as f:
            lines = f.readlines()
            for line in lines:
                input = line.split(':')
                if input[0] == 'W':
                    when = int(input[1])
                    for i in range(2, len(input), 2):
                        ev = events[input[i]]
                        ev.addEvent(when, int(input[i + 1]))
    except OSError:
        print("File not found <" + file + ">")
def timeSpan(events):
    tMin, tMax = 4000000000, 0
    for key in events:
        ev = events[key]
        if ev.nData > 0:
            tMin = min(tMin, ev.time[0])
            tMax = max(tMax, ev.time[ev.nData-1])
    return tMin, tMax

class EventList():
    def __init__(self, ID, name, type=int, scale=1.0):
        self.ID = ID
        self.name = name
        self.type = type
        self.scale = scale
        self.space = 100000
        self.time = np.zeros([self.space]).astype(int)
        self.data = np.zeros([self.space]).astype(type)
        self.nData = 0
        self.lastValue = 0

    def sampleData(self, time):
        data = np.full([len(time)], np.nan)
        if self.nData < 1: return data
        iNext = 1
        tNext = self.time[1]
        dSrc = self.data[0]
        for iDst, t in enumerate(time):
            while t > tNext:
                iNext += 1
                if iNext >= self.nData: return data
                tNext = self.time[iNext]
                dSrc = self.data[iNext]
            data[iDst] = dSrc
        return data

    def extractData(self, t0, t1):
        last = self.nData - 1
        if (last < 0) or (t1 < self.time[0]) or (t0 >= self.time[last]): return None, None
        i0, i1 = 0, last
        if t0 > self.time[0]: i0 = np.argmax(self.time > t0)
        if t1 < self.time[last]: i1 = np.argmax(self.time >= t1)

        i1 = min(i1 + 2, last) + 1
        return self.time[i0:i1], self.data[i0:i1]

    def addEvent(self, when, data):

        if (self.nData + 3) >= self.space:
            print(f'adapt storage for {self.name}')
            self.nData = int(self.space / 2)
            self.time[0:self.nData] = self.time[self.nData: 2 * self.nData]
            self.data[0:self.nData] = self.data[self.nData: 2 * self.nData]

        if self.nData > 0:
            if when < self.time[self.nData - 1]: print(f'Zeiten nicht konsekutiv')
            if data == self.data[self.nData - 1]: return

        if self.type is float: data = self.scale * float(data)
        if data == self.data[self.nData - 1]: return
        self.time[self.nData] = when
        self.data[self.nData] = data
        self.nData += 1
        self.lastValue = data



