from time import time
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtWidgets import QCheckBox, QFormLayout, QHBoxLayout, QFrame, QPushButton, QMenu, QGroupBox, QGridLayout, \
    QLabel, QRadioButton, QComboBox
from Plot import *
from Leds import *

class HandtuchViewer(QWidget):
    def __init__(self, esp, parent=None):
        QWidget.__init__(self, parent)
        self.TimerIDs = ['r', 's', 't', 'u']
        self.needsUpdate = False
        self.windowReady = False
        self.esp = esp
        self.t1 = time()
        self.t0 = self.t1 -60*60*1
        self.timer=QTimer()
        self.timer.timeout.connect(self.timerExpired)
        layout = QHBoxLayout()
        layout.addWidget(self.cmdFrame())
        self.plot = Plot()
        layout.addWidget(self.plot)
        self.setLayout(layout)
        self.redraw()
        self.windowReady = True
        esp.connectWidget(self)
        self.timer = QTimer()
        self.timer.timeout.connect(self.timerExpired)
        self.timer.start(2000)


    def mousePressEvent(self, event) -> None:
        event.accept()
        self.lastPos = event.localPos().x()

    def mouseMoveEvent(self, event) -> None:
        event.accept()
        newPos = event.localPos().x()
        xMove = -(newPos - self.lastPos) / self.plot.plotWidth
        tMove = xMove * (self.t1 - self.t0)
        if (self.t0 + tMove) < self.esp.tMin : tMove = self.esp.tMin - self.t0
        if (self.t1 + tMove) > self.esp.tMax : tMove = self.esp.tMax - self.t1
        self.t0 = self.t0 + tMove
        self.t1 = min(self.t1 + tMove, time())
        self.lastPos = newPos
        self.redraw()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            scale = 0.8
        else:
            scale = 1.2
        center = 0.5 * (self.t1 + self.t0)
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

    def setFan1(self, i): self.esp.setDevice(1, i)
    def setFan2(self, i): self.esp.setDevice(2, i)
    def setUVC(self, i): self.esp.setDevice(3, i)
    def setPumpe(self, i): self.esp.setDevice(0, i)

    def setStop(self):
        self.esp.setState(0)
    def setHochfahren(self):
        self.esp.setState(1)
    def setBetrieb(self):
        self.esp.setState(2)

    def setParameterReleased(self):
        self.esp.saveParameter()

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
    def paramWithID(self, ID):
        for para in self.esp.parameter:
            if para.cmd == ID: return para
        print(f'No parameter {ID}')
        return None
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

        self.dynamikBtn     = self.newButton(layout, "Dynamische Anzeige", True, self.displayChange)
        self.followBtn     = self.newButton(layout, "Zeitbereich nachführen", True)

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
        colours = [3, 2, 3]
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
        btn = QPushButton('10kg eichen')
        btn.clicked.connect(self.esp.set10)
        layout.addRow(btn)
        btn = QPushButton('ESP Reset')
        btn.clicked.connect(self.esp.reset)
        layout.addRow(btn)

        frame.setMaximumWidth(500)
        return frame
    def displayChange(self, checked):
        if checked:
            self.timer.start(2000)
        else:
            self.timer.stop()

    def timerExpired(self):
        masks = [4, 8, 16, 2, 0x20, 0x40]
        if self.followBtn.isChecked() and self.t1 < int(time() - 10):
            self.t1 = int(time() - 1)
        elif not self.needsUpdate: return
        event = self.esp.events['S']
        status = event.lastValue
        for iLed,led in enumerate(self.leds):
            led.setLedState((status & masks[iLed]) > 0)
        newValue = self.esp.events['Z'].lastValue
        para = self.paramWithID('g')
        para.currentValue = newValue / para.scaling
        self.updateSlider(para)
        self.needsUpdate = False
        self.redraw()
    def updateDisplay(self):
        self.needsUpdate = True

    def redraw(self):
        if not self.windowReady: return
        self.esp.gainAccess(1)
        plot = self.plot
        plot.clr()
        plot.share = True

        if True:
            event = self.esp.events['S']
            n = event.nData
            if n > 1:
                sp = plot.addSubPlot(2, "Status")
                t = event.time[0:n]
                data = event.data[0:n]
                labels = ['Anfahren', 'Betrieb', 'Warten', 'Laden', 'Ventil', 'Flut', 'Pumpe', 'Fan 1', 'Fan 2', 'UVC']
                masks  = [32, 64, 256, 128, 1, 512, 2, 4, 8, 16]
                colors = [1, 2, 8, 0, 3, 3, 6, 9, 9, 4]
                sp.timeAxis = True
                sp.plot(t, data, label=labels, bitmasks=masks, colorIndex=colors)


        if True:
            event = self.esp.events['T']
            n = event.nData
            if n > 0:
                sp = plot.addSubPlot(2, f"Temperatur {event.lastValue/1000:4.1f}°")
                sp.timeAxis = True
                sp.plot(event.time[0:n], event.data[0:n].astype(float) / 1000.0, colorIndex = 3)
            event = self.esp.events['H']
            n = event.nData
            if n > 0:
                sp = plot.addSubPlot(2, f"Luftfeuchte {event.lastValue/1000:4.1f}%")
                sp.timeAxis = True
                sp.plot(event.time[0:n], event.data[0:n].astype(float) / 1000.0, colorIndex = 3)
        if True:
            event = self.esp.events['G']
            n = event.nData
            evSoll = self.esp.events['Z']
            if n > 1:
                sp = plot.addSubPlot(2, f"Gewicht {event.lastValue/1000:5.2}kg Soll = {evSoll.lastValue/1000:5.2}kg")
                sp.timeAxis = True
                sp.plot(event.time[0:n], event.data[0:n].astype(float) / 1000, colorIndex = 3)
                event = self.esp.events['Z']
                n = evSoll.nData
                if n > 0: sp.plot(evSoll.time[0:n], evSoll.data[0:n].astype(float) / 1000, colorIndex = 2)
        if self.followBtn.isChecked(): self.t1 = max(self.t1, self.esp.tMax)
        plot.setXlim([self.t0, self.t1+1])
        plot.repaint()
        self.esp.releaseAccess(1)

