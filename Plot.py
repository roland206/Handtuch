from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush
from PyQt5.QtCore import Qt, QRectF
import numpy as np
from time import *
from math import frexp, ldexp
def roundbits(fval):
    """Return the floating-point value `fval` rounded to `nbits` bits
    in the significand."""
    significand, exponent = frexp(fval)
    newsignificand = round(significand * 10000) / 10000
    return ldexp(newsignificand, exponent)
class SubPlot():
    def __init__(self, relHeight, widget):

        self.titleStr = None
        self.widget = widget
        self.relHeight = relHeight
        self.gridColor = QColor(180,180,180)
        self.bgcSub = QColor(250,250,250)
        self.tac = QColor(255,255,255)
        self.bgcGraph = QColor(255,255,255)
        self.bgcGraphDark = QColor(0,0,0)
        self.fc = QColor(0, 0, 0)
        self.onColor = QColor(255, 100, 100)
        self.offColor = QColor(240, 240, 240)
        paired = [QColor(166, 206, 227), QColor(31, 120, 180), QColor(178, 223, 138), QColor(51, 160, 44)
            , QColor(251, 154, 153), QColor(227, 26, 28), QColor(253, 191, 111), QColor(255, 127, 0)
            , QColor(202, 178, 214), QColor(106, 61, 154), QColor(255, 255, 153), QColor(177, 89, 40)
                  ]
        dark2 = [QColor(27, 158, 119), QColor(217, 95, 2), QColor(117, 112, 179), QColor(231, 41, 138)
            , QColor(102, 166, 30), QColor(230, 171, 2), QColor(166, 118, 29), QColor(102, 102, 102)
                 ]
        set1 = [QColor(228, 26, 28), QColor(55, 126, 184), QColor(77, 175, 74), QColor(152, 78, 163)
            , QColor(255, 127, 0), QColor(255, 255, 51), QColor(166, 86, 40), QColor(247, 129, 191)
            , QColor(153, 153, 153)]
        set2 = [QColor(102, 194, 165), QColor(252, 141, 98), QColor(141, 160, 203), QColor(231, 138, 195)
            , QColor(166, 216, 84), QColor(255, 217, 47), QColor(229, 196, 148), QColor(179, 179, 179)
                ]
        set3 = [QColor(141, 211, 199), QColor(255, 255, 179), QColor(190, 186, 218), QColor(251, 128, 114)
            , QColor(128, 177, 211), QColor(253, 180, 98), QColor(179, 222, 105), QColor(252, 205, 229)
            , QColor(217, 217, 217), QColor(188, 128, 189), QColor(204, 235, 197), QColor(255, 237, 111)
                ]
        tab10 = [QColor(31, 119, 180), QColor(255, 127, 14), QColor(44, 160, 44), QColor(214, 39, 40)
            , QColor(148, 103, 189), QColor(140, 86, 75), QColor(227, 119, 194), QColor(127, 127, 127)
            , QColor(188, 189, 34), QColor(23, 190, 207)]
        tab20 = [QColor(31, 119, 180), QColor(174, 199, 232), QColor(255, 127, 14), QColor(255, 187, 120)
            , QColor(44, 160, 44), QColor(152, 223, 138), QColor(214, 39, 40), QColor(255, 152, 150)
            , QColor(148, 103, 189), QColor(197, 176, 213), QColor(140, 86, 75), QColor(196, 156, 148)
            , QColor(227, 119, 194), QColor(247, 182, 210), QColor(127, 127, 127), QColor(199, 199, 199)
            , QColor(188, 189, 34), QColor(219, 219, 141), QColor(23, 190, 207), QColor(158, 218, 229)
                 ]
        tab20b = [QColor(57, 59, 121), QColor(82, 84, 163), QColor(107, 110, 207), QColor(156, 158, 222)
            , QColor(99, 121, 57), QColor(140, 162, 82), QColor(181, 207, 107), QColor(206, 219, 156)
            , QColor(140, 109, 49), QColor(189, 158, 57), QColor(231, 186, 82), QColor(231, 203, 148)
            , QColor(132, 60, 57), QColor(173, 73, 74), QColor(214, 97, 107), QColor(231, 150, 156)
            , QColor(123, 65, 115), QColor(165, 81, 148), QColor(206, 109, 189), QColor(222, 158, 214)
                  ]

        self.bgcGraph = QColor(255,255,255)
        self.bgcGraphDark = QColor(0,0,0)
        self.linec = tab10
        self.linecBright = tab10
        self.linecDark = paired
#        self.linec = [QColor(0,0,0), QColor(255,0,0), QColor(0,255,0), QColor(0,0,255), QColor(0,255,255), QColor(255,0,255), QColor(255,255,0), QColor(128,0,0)]
        self.titleFont = QFont("Arial", 18)
        self.normalFont = QFont("Arial", 12)
        self.clr()

    def clr(self):
        self.dark = False
        self.xdata = []
        self.ydata = []
        self.labels = []
        self.xTicks = []
        self.yTicks = []
        self.color = []
        self.blockMode = []
        self.xlim = None
        self.ylim = None
        self.xGridFlag = True
        self.yGridFlag = True
        self.xAxisFlag = True
        self.yAxisFlag = True
        self.legendFlag = True
        self.bitmasks = None
        self.timeAxis = False
        self.symbol = None
        self.actBlockMode = False
        self.xFormat = None
        self.yFormat = None

    def setBlockMode(self, mode = True): self.actBlockMode = mode
    def title(self, title): self.titleStr = title
    def setXlim(self, xlim): self.xlim = xlim
    def setYlim(self, ylim): self.ylim = ylim
    def drawTitle(self, p):
        if self.title == None: return
        p.setFont(self.titleFont)
        fm = p.fontMetrics()
        p.drawText(round(self.px + self.pWidth/2 - 0.5 * fm.width(self.titleStr)), round(self.py -0.2 *  fm.height()), self.titleStr)


    def plot(self, x, y, label = None, bitmasks = None, colorIndex = -1, xFormat = None, yFormat = None):
        if len(x) < 1: return
        if len(x) != len(y):
            print("X and y must have same length")
            return
        self.xFormat = xFormat
        self.yFormat = yFormat
        if self.bitmasks != None: return
        if bitmasks != None:
            self.xdata = [x]
            self.ydata = [y]
            self.color = colorIndex
            self.bitmasks = bitmasks
            self.yGridFlag = False
            self.yAxisFlag = False
            self.legendFlag = False
            self.labels = label
            self.dark = False
            return
        self.color.append(colorIndex)
        self.xdata.append(x)
        self.ydata.append(y)
        self.labels.append(label)
        self.blockMode.append(self.actBlockMode)

        self.bitmasks = bitmasks

    def genTicks(self, limits):
        delta = limits[1] - limits[0]
        if delta <= 1e-9: return []
        spacing = np.power(10.0, round(np.log10(delta)))
        if int(delta / spacing) < 3: spacing = spacing / 2
        if int(delta / spacing) < 3: spacing = spacing / 2
        tick = spacing * int(limits[0] / spacing)
        grid = []
        while (tick <= limits[1]):
            if tick >= limits[0]: grid.append(tick)
            tick = tick + spacing
        return grid

    def minmax(self):
        if len(self.xdata) < 1: return

        if self.xlim == None:
            self.xmin = self.xdata[0][0]
            self.xmax = self.xmin
            for x in self.xdata:
                self.xmin = min(self.xmin, np.amin(x))
                self.xmax = max(self.xmax, np.amax(x))
            self.xlimit = [self.xmin, self.xmax]
        else:
            self.xlimit = self.xlim

        if self.ylim == None:
            self.ymin = self.ydata[0][0]
            self.ymax = self.ymin
            for y in self.ydata:
                self.ymin = min(self.ymin, np.amin(y))
                self.ymax = max(self.ymax, np.amax(y))

            over = 0.05 * (self.ymax - self.ymin)
            self.ylimit = [self.ymin - over, self.ymax + over]
        else:
            self.ylimit = self.ylim
        self.xTicks = self.genTicks(self.xlimit)
        self.yTicks = self.genTicks(self.ylimit)

    def getPoints(self, x, y):
        dx = self.xlimit[1]-self.xlimit[0]
        dy = self.ylimit[1]-self.ylimit[0]
        if (abs(dx) <= 1e-6) or (abs(dy) < 1e-6): return [self.px], [self.py]
        x = self.px + (x - self.xlimit[0]) * (self.pWidth  / dx)
        y = self.py + self.pHeight - (y - self.ylimit[0]) * (self.pHeight / dy)
        return x,y

    def timeToXClipped(self, t):
        twindow = self.xlimit[1]-self.xlimit[0]
        if twindow == 0: return self.px
        x = (t - self.xlimit[0]) * self.pWidth  /twindow
        if x < 0: x = 0
        if x > self.pWidth: x = self.pWidth
        return self.px + x

    def setGeometry(self,p,x,y,w,h, lw):
        p.setFont(self.titleFont)
        fm = self.widget.fontMetrics()
        titleH = fm.height()
        if self.titleStr == None: titleH = 0
        p.setFont(self.normalFont)
        fm = self.widget.fontMetrics()
        ccw = fm.width('A')
        cch = fm.height()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.px = x+100
        self.py = y + 10 +  2*titleH
        self.pWidth = w - lw - self.px
        self.pHeight = h - 2.5*cch - 2*titleH
        if self.timeAxis and self.xAxisFlag: self.pHeight = self.pHeight - 2.5 * cch
        self.legendWidth = lw
        self.legendHeight = h
        self.xLegend = x + w - lw
        self.yLegend = self.py

    def drawLegend(self, p):
        if not self.legendFlag: return
        p.setClipRect(QRectF(self.xLegend, self.yLegend, self.legendWidth, self.legendHeight))
        p.setFont(self.normalFont)
        fm = self.widget.fontMetrics()
        ccw = fm.width('A')
        cch = fm.height()
        x = self.xLegend + ccw
        y = self.yLegend + cch
        for i in range(len(self.xdata)):
            ic = self.color[i] % len(self.linec)
            p.setPen(QColor(self.linec[ic]))
            p.setBrush(QColor(self.linec[ic]))
            if self.labels[i] != None:
                p.drawLine(round(x), round(y - cch/2), round(x + 3 * ccw), round(y -cch/2))
                p.drawText(round(x + 4*ccw), round(y), self.labels[i])
            y = y + cch * 1.2

    def drawTimeAxis(self, p):
        p.setBrush(QColor(self.tac))
        fm = self.widget.fontMetrics()
        cch = fm.height()
        y = self.py + self.pHeight
        yTick = y + 0.5 * cch
        yText1 = yTick + cch

        yText2 = yText1 + 1.3 * cch
        yBox    = yText2  - cch - 2
        hBox    =  cch + 6
        t0 = self.xlimit[0]
        t1 = self.xlimit[1]
        box_x1 = self.px
        box_x2 = box_x1 + self.pWidth
        l = localtime(t0)
        tday = 3600 * (int((t0+1) / 3600) - l.tm_hour)
        spanMinutes = (t1 - t0) / 60
        minSteps = [1, 2, 5, 10, 30, 60, 120, 240, 360, 720, -1]
        dt = 1
        for i in range(0, 10):
            if (spanMinutes / minSteps[i]) > 15:
                dt = minSteps[i + 1]
        if dt > 0:
            t = t0 - (t0 % 60) - 60 * (int(t0 / 60) % dt)
            if dt > 60:
                l = localtime(t)
                adjustHours = l.tm_hour % (dt / 60)
                t -= adjustHours * 3600
            while t < t1:
                tx = self.timeToXClipped(t)
                l = localtime(t)
                uhr = "%d:%02d" % (l.tm_hour, l.tm_min)
                if (tx - box_x1) > 20 and (box_x2 - tx) > 20:
                    if self.xAxisFlag: p.drawText(round(tx - fm.width(uhr)/2), round(yText1),  uhr)
                if (tx > box_x1) and (tx < box_x2):
                    if self.xAxisFlag: p.drawLine(round(tx), round(y), round(tx), round(yTick))
                    if self.xGridFlag:
                        p.setPen(QColor(self.gridColor))
                        p.drawLine(round(tx), round(self.py), round(tx), round(yTick))
                        p.setPen(QColor(self.fc))
                t = t + dt * 60
            y = y + 30
            dt = 60 * 60 * 24
            while tday < t1:
                l = localtime(tday)
                tx1 = self.timeToXClipped(tday)
                tx2 = self.timeToXClipped(tday + dt)
                if self.xAxisFlag: p.drawRect(round(tx1), round(yBox), round(tx2-tx1), round(hBox))
                if tx2 - tx1 > 60:
                    dayHeute = int(time() / dt) - 1
                    day = int(tday/dt)
                    if dayHeute == day:
                        datum = "Heute"
                    elif (dayHeute-1) == day:
                        datum = "Gestern"
                    else:
                        datum = "%d.%d.%d" % (l.tm_mday, l.tm_mon, l.tm_year)
                    if self.xAxisFlag: p.drawText(round((tx1 + tx2) / 2 - fm.width(datum)/2), round(yText2), datum)
                tday += dt
            return

        dayMonth = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        nameMonth = ["Jan", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
        spanDays = spanMinutes / (60 * 24)
        l = localtime(tday)
        tday = tday - (l.tm_mday - 1) * 3600 * 24
        if spanDays < 90:
            t = tday
            while t < t1:
                l = localtime(t)
                tx = self.timeToXClipped(t)
                if tx > box_x1:

                    if self.xAxisFlag: p.drawLine(round(tx), round(y), round(tx), round(yTick))
                    if self.xGridFlag:
                        p.drawLine(round(tx), round(self.py), round(tx), round(yTick))
                        p.setPen(QColor(self.gridColor))
                        p.drawLine(round(tx),round( self.py), round(tx), round(yTick))
                        p.setPen(QColor(self.fc))
                if spanDays < 40 and tx - box_x1 > 10:
                    uhr = "%d" % l.tm_mday
                    if self.xAxisFlag: p.drawText(round(tx - fm.width(uhr)/2), round(yText1), uhr)
                t = t + 60 * 60 * 24
            y += 30
            t = tday
            month = localtime(tday).tm_mon - 1 # so notwendig wegen Sommerzeit
            while t < t1 and self.xAxisFlag:
                l = localtime(t)
                tx1 = self.timeToXClipped(t)
                dt = dayMonth[month] * 3600 * 24
                tx2 = self.timeToXClipped(t + dt)
                p.drawRect(round(tx1), round(yBox), round(tx2-tx1), round(hBox))
                uhr = nameMonth[month] + (" %d" % l.tm_year)
                if tx2 - tx1 > 60:
                    p.drawText(round((tx1 + tx2) / 2-fm.width(uhr)/2), round(yText2), uhr)
                month = (month + 1) % 12
                t += dt
            return

        t = tday
        while t < t1:
            l = localtime(t)
            tx = self.timeToXClipped(t)
            if tx > box_x1:
                if self.xAxisFlag: p.drawLine(round(tx), round(y), round(tx), round(y + 8))
            if spanDays < 700 and tx - box_x1 > 10:
                if self.xAxisFlag: p.drawText(round(tx), round(yText2), nameMonth[l.tm_mon - 1])
            t = t + dayMonth[l.tm_mon - 1] * 60 * 60 * 24

        y += 30
        t = tday
        dt = 365 * 24 * 60 * 60
        while t < t1 and self.xAxisFlag:
            l = localtime(t)
            tx1 = self.timeToXClipped(t)
            tx2 = self.timeToXClipped(t + dt)
            p.drawRect(round(tx1), round(y), round(tx2), round(y + 20))
            if tx2 - tx1 > 60:
                p.drawText(round((tx1 + tx2) / 2), round(y + 4), l.tm_year)
            t += dt

    def drawAxes(self, p):
        p.setFont(self.normalFont)
        fm = self.widget.fontMetrics()
        cch = fm.height()

        if self.timeAxis:
            self.drawTimeAxis(p)
        elif len(self.xTicks) > 0:
            y0 = self.py
            y1 = y0 + self.pHeight
            y2 = y1 + cch/2
            y3 = y2 + cch
            for x in self.xTicks:
                px,py = self.getPoints(x, 0)
                if self.xGridFlag:
                    p.setPen(QColor(self.gridColor))
                    p.drawLine(round(px), round(y0) , round(px), round(y1))
                if self.xAxisFlag:
                    p.setPen(QColor(self.fc))
                    p.drawLine(round(px), round(y1) , round(px), round(y2))
                    if self.xFormat is None:
                        text = str(roundbits(x))
                    else:
                        text = self.xFormat.format(x)
                  #  text = str(x)
                    px = px - 0.5 * fm.width(text)
                    p.setPen(QColor(self.fc))
                    p.drawText(round(px), round(y3), text)
        if len(self.yTicks) > 0:
            x1 = self.px - cch/2
            x2 = self.px
            x3 = x2 + self.pWidth
            for y in self.yTicks:
                px,py = self.getPoints(0, y)
                if self.yGridFlag:
                    p.setPen(QColor(self.gridColor))
                    p.drawLine(round(x2), round(py) , round(x3), round(py))
                if self.yAxisFlag:
                    p.setPen(QColor(self.fc))
                    p.drawLine(round(x1), round(py) , round(x2), round(py))
                    if self.yFormat is None:
                        text = str(roundbits(y))
                    else:
                        text = self.yFormat.format(y)
                    px = x1 - fm.width(text + 'A')
                    p.setPen(QColor(self.fc))
                    p.drawText(round(px), round(py + 0.4 * cch), text)

    def drawMaskField(self, p, x):
        nFields = len(self.bitmasks)
        dy = self.pHeight / (3 * nFields + 1)
        py = self.py + dy
        fm = self.widget.fontMetrics()
        cch2 = 0.5 * fm.height()
        for i in range(nFields):
            ic = self.color[i] % len(self.linec)
            p.setPen(QColor(self.linec[ic]))
            p.setBrush(QColor(self.linec[ic]))
            mask = self.bitmasks[i]
            xLast = x[0]
            y = self.ydata[0]
            y = y & mask
            yLast =y[0]
            p.setClipRect(QRectF(self.px, self.py,self.pWidth,self.pHeight))
            for ix in range(len(x) - 1):
                if y[ix+1] == yLast: continue
                if yLast == 0:
                    p.setBrush(self.offColor)
                    p.setPen(self.offColor)
                else:
                    p.setBrush(QColor(self.linec[ic]))
                    p.setPen(QColor(self.linec[ic]))
                p.drawRect(round(xLast), round(py), round(x[ix+1]-xLast), round(2*dy))
                xLast = x[ix+1]
                yLast = y[ix+1]
            if yLast == 0:
                p.setBrush(self.offColor)
                p.setPen(self.offColor)
            else:
                p.setBrush(QColor(self.linec[ic]))
                p.setPen(QColor(self.linec[ic]))
            p.drawRect(round(xLast), round(py), round((self.px + self.pWidth)-xLast), round(2*dy))
            p.setBrush(QColor(self.linec[ic]))
            p.setPen(QColor(self.linec[ic]))
            p.setClipRect(QRectF(self.xLegend, self.yLegend, self.legendWidth,self.legendHeight))
            p.drawText(round(self.xLegend), round(py+dy+cch2), self.labels[i])
            py = py + 3*dy

    def draw(self, p):
        if len(self.xdata) < 1 : return
        fm = self.widget.fontMetrics()
        cch2 = 0.5 * fm.height()
        p.setPen(QColor(self.fc))
        p.setBrush(QBrush(self.bgcSub, Qt.SolidPattern))
        p.setClipRect(QRectF(self.x, self.y,self.w,self.h))
        p.drawRect(int(self.x), int(self.y), int(self.w), int(self.h))
        if self.dark:
            p.setBrush(QBrush(self.bgcGraphDark, Qt.SolidPattern))
            self.linec = self.linecDark
        else:
            p.setBrush(QBrush(self.bgcGraph, Qt.SolidPattern))
            self.linec = self.linecBright
        p.drawRect(round(self.px), round(self.py), round(self.pWidth), round(self.pHeight))
        self.drawTitle(p)
        self.drawAxes(p)
        if self.bitmasks == None:
            self.drawLegend(p)

        p.setClipRect(QRectF(self.px, self.py,self.pWidth,self.pHeight))
        for idata in range(len(self.xdata)):
            x = self.xdata[idata]
            y = self.ydata[idata]
            if len(y) < 1: return
            xdata, ydata = self.getPoints(x, y)
            ic = self.color[idata] % len(self.linec)
            p.setPen(QColor(self.linec[ic]))
            p.setBrush(QColor(self.linec[ic]))
            if self.bitmasks != None:
                self.drawMaskField(p, xdata)
            elif self.symbol != None:
                for i in range(len(xdata)):
                    p.drawText(round(xdata[i]), round(ydata[i] + cch2), self.symbol)
            elif self.blockMode[idata]:
                for i in range(len(xdata) - 1):
                    p.drawLine(int(xdata[i]), int(ydata[i]), int(xdata[i+1]), int(ydata[i]))
                    p.drawLine(int(xdata[i+1]), int(ydata[i]), int(xdata[i + 1]), int(ydata[i + 1]))
            else:
                for i in range(len(xdata) - 1):
                    p.drawLine(int(xdata[i]), int(ydata[i]), int(xdata[i+1]), int(ydata[i+1]))


class Plot(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.clr()
        self.bgc = QColor()
        self.bgc.setRgb(200, 200, 200)

    def clr(self):
        self.share = False
        self.subPlots = []
    def addSubPlot(self, relHeight, title=None):
        self.subPlots.append(SubPlot(relHeight, self))
        sp = self.subPlots[-1]
        if title != None: sp.title(title)
        return sp

    def shareX(self, share):
        self.share = share

    def setXlim(self, xlim):
        for sub in self.subPlots:
            sub.xlim = xlim

    def setYlim(self, ylim):
        for sub in self.subPlots:
            sub.ylim = ylim
    def paintEvent(self, event):
        maxLen = 0
        for sub in self.subPlots:
            for label in sub.labels:
                if label != None: maxLen = max(maxLen, len(label))


        rand = 10
        self.p = QPainter()
        self.p.begin(self)
        self.p.setRenderHint(QPainter.Antialiasing)
        total = 0;
        for sub in self.subPlots:
            total = total + sub.relHeight
        if total == 0:
            self.p.end()
            return
        heightScale = (self.height() - rand * (1 + len(self.subPlots))) / total
        width = self.width() - 2 * rand
        y = rand
        if maxLen > 0:
            legendWidth = 200
        else:
            legendWidth = 10

        for sub in self.subPlots: sub.minmax()

        if self.share:
            xmin = np.inf
            xmax = -np.inf
            for sub in self.subPlots:
                if len(sub.xdata) > 0:
                    xmin = min(xmin, sub.xlimit[0])
                    xmax = max(xmax, sub.xlimit[1])
            for sub in self.subPlots: sub.xlimit = [xmin, xmax]

        for sub in self.subPlots:
            sub.setGeometry(self.p, rand, y, width, sub.relHeight * heightScale, legendWidth)
            self.plotWidth = sub.pWidth
            y = y + sub.relHeight * heightScale + rand
            actColor = 0
            for i in range(len(sub.color)):
                if sub.color[i] < 0:
                    sub.color[i] = actColor
                    actColor += 1

        self.p.setBrush(QBrush(self.bgc, Qt.SolidPattern))
        self.p.setClipRect(QRectF(0, 0,self.width(),self.height()))
        self.p.drawRect(0, 0, self.width(), self.height())
        for sub in self.subPlots:
            sub.draw(self.p)
        self.p.end()
        self.plotWidth = width - legendWidth