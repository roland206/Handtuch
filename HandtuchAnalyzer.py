from time import time
import scipy
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtWidgets import QCheckBox, QFormLayout, QHBoxLayout, QFrame, QPushButton, QMenu, QGroupBox, QGridLayout, \
    QLabel, QRadioButton, QComboBox
from Plot import *
from Leds import *
from Reporter import *
from Events import *
import glob

class HandtuchAnalyzer(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.events = None
        layout = QHBoxLayout()
        self.plot = Plot()
        layout.addWidget(self.plot)
        self.setLayout(layout)

    def loadLogFiles(self, path, maxFile):
        files = glob.glob(path + 'Handtuch_*.log')
        files.sort()
        self.events = createEvents()
        if len(files) > maxFile:
            files = files[-maxFile:]
        for file in files:
            loadEventFile(self.events, file)
        self.t0, self.t1 = timeSpan(self.events)
        self.redraw()
    def mousePressEvent(self, event) -> None:
        event.accept()
        self.lastPos = event.localPos().x()

    def mouseMoveEvent(self, event) -> None:
        event.accept()
        newPos = event.localPos().x()
        xMove = -(newPos - self.lastPos) / self.plot.plotWidth
        tMove = xMove * (self.t1 - self.t0)
        t0, t1 = timeSpan(self.esp.events)
        if (self.t0 + tMove) < t0 : tMove = t0 - self.t0
        if (self.t1 + tMove) > t1 : tMove = t1 - self.t1
        self.t0 = self.t0 + tMove
        self.t1 = min(self.t1 + tMove, time())
        self.lastPos = newPos
        self.redraw()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            scale = 0.8
        else:
            scale = 1.2
        center = self.t0 + (self.t1 - self.t0) / 2
        span = scale * (self.t1 - self.t0)
        self.t0 = center - span/2
        self.t1 = min(center + span/2, time())
        self.redraw()


    def redraw(self):
        if self.events is None: return
        plot = self.plot
        plot.clr()
        plot.share = True

        if True:
            event = self.events['S']
            n = event.nData
            if n > 1:
                sp = plot.addSubPlot(2, "Status")
                t = event.time[0:n]
                data = event.data[0:n]
                labels = ['Anfahren', 'Betrieb', 'Pause', 'Laden',  'Flut','Fan 1', 'Fan 2', 'UVC']
                masks  = [32, 64, 256, 128, 512, 4, 8, 16]
                colors = [1, 2, 8, 0, 3, 9, 9, 4]
                sp.timeAxis = True
                sp.plot(t, data, label=labels, bitmasks=masks, colorIndex=colors)


        if True:
            event = self.events['T']
            t, data = event.extractData(self.t0, self.t1)
            if t is not None:
                sp = plot.addSubPlot(2, f"Temperatur")
                sp.timeAxis = True
                sp.ylim = [np.min(data)-1.5, np.max(data)+1.5]
                sp.plot(t, data, colorIndex = 3, yFormat = '{0:4.1f}')

            event = self.events['H']
            t, data = event.extractData(self.t0, self.t1)
            if t is not None:
                sp = plot.addSubPlot(2, f"Luftfeuchte")
                sp.timeAxis = True
                sp.ylim = [np.min(data)-1.5, np.max(data)+1.5]
                sp.plot(t, data, colorIndex = 3, yFormat = '{0:4.1f}')
        if True:
            event = self.events['G']
            t, data = event.extractData(self.t0, self.t1)
            if t is not None:
                evSoll = self.events['Z']
                tSoll, dataSoll = evSoll.extractData(self.t0, self.t1)
                sp = plot.addSubPlot(2, f"Gewicht")
                sp.timeAxis = True
                sp.plot(t, data, colorIndex = 3, yFormat = '{0:6.3f}')
                if tSoll is not None:
                    sp.setBlockMode()
                    tSoll= np.concatenate((tSoll, np.array([self.t1])))
                    dataSoll = np.concatenate((dataSoll, np.array([dataSoll[-1]])))
                    sp.plot(tSoll, dataSoll, colorIndex = 2, yFormat = '{0:6.3f}')

        if True:
            t,d, ts, ds = self.verdunstung(self.events['G'], self.events['S'], 128)
            if t is not None:
                sp = plot.addSubPlot(2, f"Verdunstung Liter/Tag")
                sp.timeAxis = True
                sp.plot(t, d, colorIndex=2, yFormat='{0:6.3f}')
                sp.plot(ts, ds, colorIndex=0)

        plot.setXlim([self.t0, self.t1+1])
        plot.repaint()



    def verdunstung(self, gewicht, status, mask):
        tOut, dOut = None, None
        laden = status.data[0: status.nData] & mask
        fluss = laden[0]
        i0 = 0
        iGewicht = 0
        i = 1
        while i < status.nData-1:
            while gewicht.time[iGewicht] < status.time[i]: iGewicht += 1
            if not fluss and laden[i]:
                if gewicht.time[iGewicht] > self.t0 and gewicht.time[i0] < self.t1:
                    if iGewicht -i0 > 5:
                        t = gewicht.time[i0: iGewicht]
                        d = gewicht.data[i0:iGewicht]
                        poly = np.polyfit(t, d, 1) * (-60 * 60 * 24)
                        #print(poly)
                        nPoints = int((t[-1] - t[0]) / 60)
                        t = np.linspace(t[0], t[-1], nPoints, endpoint=True)
                        d = np.polyval(np.polyder(poly), t)
                        if tOut is None:
                            tOut, dOut = t, d
                        else:
                            tOut = np.append(tOut, t)
                            dOut = np.append(dOut, d)
            elif fluss and not laden[i]: i0 = iGewicht
            fluss = laden[i]
            i += 1
        tSmooth = np.linspace(tOut[0], tOut[-1], 100, endpoint=True)
        dSmooth = np.interp(tSmooth, tOut, dOut)
        dSmooth = scipy.ndimage.gaussian_filter1d(dSmooth, 20)
        return tOut, dOut, tSmooth, dSmooth

