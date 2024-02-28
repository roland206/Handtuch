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

correlationNames = ['Verdunstung', "Temperatur", 'Luftfeuchte', 'Gewicht', 'Lüfter']
class HandtuchAnalyzer(QWidget):
    def __init__(self, logPath, parent=None):
        QWidget.__init__(self, parent)
        self.logPath = logPath + 'Handtuch_*.log'
        self.selectedLogFiles = None
        self.useSelection = False
        self.events = None
        self.maxLogFiles = 10
        self.correlation = 0
        self.corrPlot = Plot()
        self.plot = Plot()
        layout = QHBoxLayout()
        leftFrame = QFrame()
        leftLayout = QVBoxLayout()
        leftFrame.setLayout(leftLayout)
        leftFrame.setMaximumWidth(1000)
        leftLayout.addWidget(self.cmdFrame())
        leftLayout.addWidget(self.corrPlot)
        layout.addWidget(leftFrame)
        layout.addWidget(self.plot)
        self.setLayout(layout)
        self.redraw()

    def loadLogFiles(self):
        if self.useSelection:
            files = self.selectedLogFiles
        else:
            files = glob.glob(self.logPath)
        files.sort()
        self.events = createEvents()
        if len(files) > self.maxLogFiles:
            files = files[-self.maxLogFiles:]
        for file in files:
            loadEventFile(self.events, file)
        self.t0, self.t1 = timeSpan(self.events)
        self.redraw()

    def daysChanged(self, i):
        self.maxLogFiles = i
        self.loadLogFiles()

    def selectFiles(self):
        files = QFileDialog.getOpenFileNames(self,'Öffne Log Files', '', 'Log Files (*.log);; Alle Dateien (*)')
        if files:
            self.selectedLogFiles = files[0]
            self.useSelection = True
            self.loadLogFiles()

    def setLogType(self, selection):
        self.useSelection = selection
        if selection and self.selectedLogFiles is None:
            self.selectFiles()
        else:
            self.loadLogFiles()
    def cmdFrame(self):
        frame = QFrame()
        layout = QFormLayout()
        frame.setLayout(layout)

        historyBtn = QRadioButton('Aktuelle Historie')
        historyBtn.setChecked(True)
        selectedBtn = QRadioButton('Selektierte Log-files')
        layout.addRow(historyBtn)
        layout.addRow(selectedBtn)
        historyBtn.toggled.connect(lambda:self.setLogType(False))
        selectedBtn.toggled.connect(lambda:self.setLogType(True))

        layout.addRow(QLabel('Anzahl Tage Rückschau'))
        daysBtn = QSpinBox()
        daysBtn.setValue(self.maxLogFiles)
        daysBtn.setMinimum(1)
        daysBtn.setMaximum(31)
        daysBtn.valueChanged.connect(self.daysChanged)
        daysBtn.setMaximumWidth(200)
        layout.addRow(daysBtn)

        selectBtn = QPushButton('Log files selektieren')
        selectBtn.clicked.connect(self.selectFiles)
        layout.addRow(selectBtn)


        grid = QGroupBox("Korrelationen")
        gridLayout = QGridLayout()
        grid.setLayout(gridLayout)
        layout.addRow(grid)


        self.comboX = QComboBox(self)
        self.comboY = QComboBox(self)
        self.comboX.addItems(correlationNames)
        self.comboY.addItems(correlationNames)
        self.comboX.setCurrentIndex(0)
        self.comboY.setCurrentIndex(1)
        self.comboX.currentIndexChanged.connect(self.redraw)
        self.comboY.currentIndexChanged.connect(self.redraw)
        gridLayout.addWidget(QLabel('X-Achse'), 0, 0)
        gridLayout.addWidget(QLabel('Y-Achse'), 1, 0)
        gridLayout.addWidget(self.comboX, 0, 1)
        gridLayout.addWidget(self.comboY, 1, 1)
        frame.setMaximumWidth(500)
        return frame

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

    def getCorrelationData(self, index, verdunstung, t):
        if index == 0: return verdunstung, None, '{0:4.1f}'
        if index == 1: return self.events['T'].sampleData(t), None, '{0:4.1f}'
        if index == 2: return self.events['H'].sampleData(t), None, '{0:4.1f}'
        if index == 3: return self.events['G'].sampleData(t), None, '{0:4.1f}'
        if index == 4:
            raw = self.events['S'].sampleData(t)
            raw = (raw.astype(int) >> 2) & 3
            return raw, [-0.1, 3.1], '{0:3.1f}'
        return None, None
    def redrawCorrelation(self, time, data):
        ix = self.comboX.currentIndex()
        iy = self.comboY.currentIndex()
        plot = self.corrPlot
        plot.clr()
        sp = plot.addSubPlot(1, title=f'Korrelation {correlationNames[ix]} / {correlationNames[iy]}')
        datax, limitx, formatx = self.getCorrelationData(ix, data, time)
        datay, limity, formaty = self.getCorrelationData(iy, data, time)

        sp.symbol = '*'
        sp.plot(datax, datay, xFormat=formatx, yFormat=formaty)
        sp.setXlim(limitx)
        sp.setYlim(limity)
        plot.repaint()
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
                if self.correlation  >= 0: self.redrawCorrelation(ts, ds)
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

