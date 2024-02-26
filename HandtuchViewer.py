from time import time
import scipy
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtWidgets import QCheckBox, QFormLayout, QHBoxLayout, QFrame, QPushButton, QMenu, QGroupBox, QGridLayout, \
    QLabel, QRadioButton, QComboBox
from Plot import *
from Leds import *
from Reporter import *
from Events import *

class HandtuchViewer(QWidget):
    def __init__(self, esp, reporter, simulation = False, parent=None,):
        QWidget.__init__(self, parent)
        self.reporter = reporter
        self.simulation = simulation
        self.lastStatus = 0
        self.TimerIDs = ['r', 's', 't', 'u']
        self.needsUpdate = False
        self.windowReady = False
        self.esp = esp
        if simulation:
            event = self.esp.events['G']
            self.t0 = event.time[0]
            self.t1 = event.time[event.nData-1]
        else:
            self.t1 = time()
            self.t0 = self.t1 -60*60*1
        self.timer=QTimer()
        self.timer.timeout.connect(self.timerExpired)
        layout = QHBoxLayout()
        cmd = self.cmdFrame()
   #     cmd.setHidden(simulation)
        layout.addWidget(cmd)
        self.plot = Plot()
        layout.addWidget(self.plot)
        self.setLayout(layout)
        self.redraw()
        self.windowReady = True
        esp.connectWidget(self)
        if not simulation: self.timer.start(2000)
        self.reporter.talk('Handtuch maschine gestarted', 10)


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

    def newButton(self, layout, name, initialState, callBack=None):
        cb = QCheckBox(name)
        if callBack is not None: cb.stateChanged.connect(callBack)
        cb.setChecked(initialState)
        layout.addRow(cb)
        return cb

    def pushButton(self, layout, dev, callBack):
        cb = QPushButton(self.esp.deviveText(dev))
        cb.clicked.connect(callBack)
        layout.addRow(cb)
        return cb



    def updateTime(self):
        timeEdit = self.sender()
        tt = timeEdit.time()
        secs = tt.msecsSinceStartOfDay() / 60000

        for i in range(4):
            if timeEdit == self.ruhe[i]:
                para = self.paramWithID(self.TimerIDs[i])
                para.currentValue = secs
        self.esp.saveParameter()

    def cmdFrame(self):
        frame = QFrame()
        layout = QFormLayout()
        frame.setLayout(layout)

        self.dynamikBtn   = self.newButton(layout, "Dynamische Anzeige",  not self.simulation, self.dynamicDisplay)
        self.followBtn    = self.newButton(layout, "Zeitbereich nachführen", not self.simulation)
        self.dunstBtn     = self.newButton(layout, "Verdunstung berechnen", self.simulation)

        grid = QGroupBox("Geräte")
        gridLayout = QGridLayout()
        grid.setLayout(gridLayout)

        callBacks = [self.setFan1, self.setFan2, self.setUVC, self.setPumpe]
        colours = [3, 3, 6, 1]
        self.leds = []
        for i, label in enumerate(['Lüfter 1', 'Lüfter 2', 'UVC', 'Pumpe']):
            gridLayout.addWidget(QLabel(label), i, 0)
            cb = QComboBox()
            gridLayout.addWidget(cb, i, 1)
            cb.addItems(['aus', 'an', 'Automatik', 'Party'])
            cb.currentIndexChanged.connect(callBacks[i])
            cb.setCurrentIndex(self.esp.getDevice((i+1)&3))
            self.leds.append(Led(colorIndex=colours[i]))
            gridLayout.addWidget(self.leds[i], i, 2)
        layout.addWidget(grid)

        grid = QGroupBox("Betrieb")
        gridLayout = QGridLayout()
        grid.setLayout(gridLayout)
        callBacks = [self.setStop, self.setHochfahren, self.setBetrieb]
        colours = [3, 3, 2]
        for i, label in enumerate(['Stop', 'Hochfahren', 'Betrieb']):
            btn = QPushButton(label)
            gridLayout.addWidget(btn, i, 0)
            btn.clicked.connect(callBacks[i])
            if i > 0:
                self.leds.append(Led(colorIndex=colours[i]))
                gridLayout.addWidget(self.leds[-1], i, 1)
        layout.addWidget(grid)

        grid = QGroupBox("Parameter")
        layout.addWidget(grid)
        gridLayout = QVBoxLayout()
        grid.setLayout(gridLayout)
        parameter = self.esp.parameter
        for para in parameter:
            if not para.hidden:
                para.label = QLabel(para.str())
                gridLayout.addWidget(para.label)
                para.slider = QSlider(Qt.Orientation.Horizontal)
                para.slider.valueChanged.connect(self.setParameter)
                para.slider.sliderReleased.connect(self.setParameterReleased)
                self.updateSlider(para)
                gridLayout.addWidget(para.slider)

        grid = QGroupBox("Ruhezeiten")
        gridLayout = QGridLayout()
        grid.setLayout(gridLayout)

        gridLayout.addWidget(QLabel('Ruhe von...bis'), 0, 0)
        gridLayout.addWidget(QLabel('kein UVC von...bis'), 1, 0)
        self.ruhe = []
        for i, ID in enumerate(self.TimerIDs):
            para = self.paramWithID(ID)
            mSecs = QTime.fromMSecsSinceStartOfDay(int(60000 * para.currentValue))
            self.ruhe.append(QTimeEdit(self))
            self.ruhe[-1].editingFinished.connect(self.updateTime)
            self.ruhe[-1].setTime(mSecs)
            gridLayout.addWidget(self.ruhe[-1], i >> 1, 1 + (i & 1))
        layout.addRow(grid)

        btn = QPushButton('Nullmarke setzen')
        btn.clicked.connect(self.esp.setNull)
        layout.addRow(btn)
        btn = QPushButton('12kg eichen')
        btn.clicked.connect(self.esp.set10)
        layout.addRow(btn)
        btn = QPushButton('ESP Reset')
        btn.clicked.connect(self.esp.reset)
        layout.addRow(btn)

        self.newButton(layout, "ESP Protokoll ausgeben", False, self.setVerbose)
        self.newButton(layout, "Hohe Auflösung", self.esp.getDevice(4), self.setResolution)
        self.newButton(layout, "Sprachnachrichten", True, self.setSprache)
        self.newButton(layout, "Log-Datei erzeugen", True, self.setLog)
        self.newButton(layout, "Log-Daten anzeigern", True, self.showLog)
        frame.setMaximumWidth(500)
        self.setLog(True)
        return frame
    def dynamicDisplay(self, checked):
        if checked:
            self.timer.start(2000)
        else:
            self.timer.stop()

# ESP communication
    # Update request from ESP.py. New data arrived
    def updateDisplay(self):
        self.needsUpdate = True
        t0, t1 = timeSpan(self.esp.events)
        self.t0 = max(self.t0, t0)
    def setResolution(self, checked): self.esp.setDevice(4, checked)
    def setVerbose(self, checked): self.esp.verbose = checked
    def setLog(self, checked): self.esp.logging(checked)
    def showLog(self, checked): self.reporter.setVerbosity(print = checked)
    def setSprache(self, checked):
        if checked:
            self.reporter.setVerbosity(talk=5)
            self.reporter.talk('Sprachnachrichten aktiv', 20)
        else:
            self.reporter.talk('Werde nun den sappel halten', 20)
            self.reporter.setVerbosity(talk=15)
    def setFan1(self, i): self.esp.setDevice(1, i)
    def setFan2(self, i): self.esp.setDevice(2, i)
    def setUVC(self, i): self.esp.setDevice(3, i)
    def setPumpe(self, i): self.esp.setDevice(0, i)
    def setStop(self): self.esp.setState(0)
    def setHochfahren(self): self.esp.setState(1)
    def setBetrieb(self):
        self.reporter.talk('Handtuch maschine startet betrieb', 10)
        self.esp.setState(2)

    # Search for the parameter with ID
    def paramWithID(self, ID):
        for para in self.esp.parameter:
            if para.cmd == ID: return para
        raise(f'No parameter with ID <{ID}>')

    # Callback if a slider is released. Parameter are only set on relaese of the mouse
    def setParameterReleased(self):
        self.setParameter()
        self.esp.saveParameter()

    # Callback for all sliders
    def setParameter(self):
        slider = self.sender()
        for para in self.esp.parameter:
            if para.slider == slider:
                para.currentValue = para.min + para.step * float(slider.value())
                para.label.setText(para.str())

    def updateSlider(self, para):
        m = int((para.max - para.min) / para.step)
        para.slider.setRange(0, m)
        value = round((para.currentValue - para.min) / para.step)
        value = min(max(0, value), m)
        para.slider.setValue(value)



    def timerExpired(self):
        masks = [4, 8, 16, 2, 0x20, 0x40]
        if self.followBtn.isChecked() and self.t1 < int(time() - 10):
            self.t1 = int(time() - 1)
        elif not self.needsUpdate: return
        event = self.esp.events['S']
        status = event.lastValue
        if     (status & 0x200) and not (self.lastStatus & 0x200) : self.reporter.talk('ups wasserüberlauf', 10)
        if not (status & 0x20) and (self.lastStatus & 0x20) : self.reporter.talk('Hochfahren beendet', 10)
        if not (status & 0x40) and (self.lastStatus & 0x40) : self.reporter.talk('Betrieb eingestellt', 10)
        if not (status & 0x80) and (self.lastStatus & 0x80) : self.reporter.talk('Bewässerung beendet', 10)
        if     (status & 0x80) and not (self.lastStatus & 0x80) : self.reporter.talk('handtücher werden bewässert', 10)

        self.lastStatus = status
        for iLed,led in enumerate(self.leds):
            led.setLedState((status & masks[iLed]) > 0)
        newValue = self.esp.events['Z'].lastValue
        para = self.paramWithID('g')
        para.currentValue = newValue
        self.updateSlider(para)
        self.needsUpdate = False
        self.redraw()


    def redraw(self):
        self.esp.gainAccess(1)
        plot = self.plot
        plot.clr()
        plot.share = True
        if self.followBtn.isChecked():
            t0, t1 = timeSpan(self.esp.events)
            self.t1 = max(self.t1, t1)

        if True:
            event = self.esp.events['S']
            n = event.nData
            if n > 1:
                sp = plot.addSubPlot(2, "Status")
                t = event.time[0:n]
                data = event.data[0:n]
                labels = ['Anfahren', 'Betrieb', 'Pause', 'Laden', 'Ventil', 'Flut', 'Pumpe', 'Fan 1', 'Fan 2', 'UVC']
                masks  = [32, 64, 256, 128, 1, 512, 2, 4, 8, 16]
                colors = [1, 2, 8, 0, 3, 3, 6, 9, 9, 4]
                sp.timeAxis = True
                sp.plot(t, data, label=labels, bitmasks=masks, colorIndex=colors)


        if True:
            event = self.esp.events['T']
            t, data = event.extractData(self.t0, self.t1)
            if t is not None:
                sp = plot.addSubPlot(2, f"Temperatur {event.lastValue:4.1f}°")
                sp.timeAxis = True
                sp.ylim = [np.min(data)-1.5, np.max(data)+1.5]
                sp.plot(t, data, colorIndex = 3, yFormat = '{0:4.1f}')

            event = self.esp.events['H']
            t, data = event.extractData(self.t0, self.t1)
            if t is not None:
                sp = plot.addSubPlot(2, f"Luftfeuchte {event.lastValue:4.1f}%")
                sp.timeAxis = True
                sp.ylim = [np.min(data)-1.5, np.max(data)+1.5]
                sp.plot(t, data, colorIndex = 3, yFormat = '{0:4.1f}')
        if True:
            event = self.esp.events['G']
            t, data = event.extractData(self.t0, self.t1)
            if t is not None:
                evSoll = self.esp.events['Z']
                tSoll, dataSoll = evSoll.extractData(self.t0, self.t1)
                sp = plot.addSubPlot(2, f"Gewicht {event.lastValue:.2f}kg Soll = {evSoll.lastValue:.2f}kg")
                sp.timeAxis = True
                sp.plot(t, data, colorIndex = 3, yFormat = '{0:6.3f}')
                if tSoll is not None:
                    sp.setBlockMode()
                    tSoll= np.concatenate((tSoll, np.array([self.t1])))
                    dataSoll = np.concatenate((dataSoll, np.array([dataSoll[-1]])))
                    sp.plot(tSoll, dataSoll, colorIndex = 2, yFormat = '{0:6.3f}')

        if self.dunstBtn.isChecked():
            t,d, ts, ds = self.verdunstung(self.esp.events['G'], self.esp.events['S'], 128)
            if t is not None:
                sp = plot.addSubPlot(2, f"Verdunstung Liter/Tag")
                sp.timeAxis = True
                sp.plot(t, d, colorIndex=2, yFormat='{0:6.3f}')
                sp.plot(ts, ds, colorIndex=0)

        plot.setXlim([self.t0, self.t1+1])
        plot.repaint()
        self.esp.releaseAccess(1)


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
                        poly = np.polynomial.polynomial.polyfit(t, gewicht.data[i0:iGewicht], 2) * (-60 * 60 * 24)
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

