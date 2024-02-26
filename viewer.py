import glob

from PyQt5 import QtWidgets, uic
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QCheckBox, QFormLayout, QTabWidget
#import pyqtgraph as pg
import sys
import numpy as np
import pathlib
import platform
from ESP import *
from HandtuchViewer import *
from HandtuchAnalyzer import *

class MainWindow(QTabWidget):
    def __init__(self, esp, reporter, logPath):
        super(MainWindow, self).__init__()
        self.logPath = logPath
        if esp is not None : self.addTab(HandtuchViewer(esp), "Aktuell")
        self.analyzer = HandtuchAnalyzer(None)
        self.analyzer.loadLogFiles(logPath)
        self.addTab( self.analyzer , "Historie")
        self.currentChanged.connect(self.chanced)
        self.resize(1800, 1200)

    def chanced(self):
        widget = self.currentWidget()
        if (type(widget) == HandtuchAnalyzer):  self.analyzer.loadLogFiles(self.logPath)

def main(esp, reporter , logPath):
    app = QApplication(sys.argv)
    main = MainWindow(esp, reporter, logPath)
    main.show()
    app.exec_()


if __name__ == '__main__':

    os.chdir(pathlib.Path(__file__).parent.resolve())

    if 'indows' in platform.platform():
        logPath = '.\\'
        reporter = Reporter(logPath, Linux = False)
    else:
        logPath = '/media/ramdisk/'
        reporter = Reporter(logPath, Linux = True)

    try:
        esp = ESP('Handtuch.para', reporter)
    except NoPort as inst:
        app = QtWidgets.QApplication([])
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        detail = 'No USB Port found\nAvailable Ports :\n'
        for p, desc, hwid in sorted(inst.ports):
            detail += f'{p} : {desc}\n'
        msg.setText(detail)
        msg.setWindowTitle("Error")

        msg.addButton(QPushButton('Historie'), QMessageBox.NoRole)
        msg.addButton(QPushButton('Abbruch'), QMessageBox.RejectRole)
        if msg.exec_() == 1: sys.exit()
        esp = None

    except serial.serialutil.SerialException as inst:
        app = QtWidgets.QApplication([])
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("USB Error")
        msg.setInformativeText(str(inst))
        msg.setWindowTitle("Error")
        msg.addButton(QPushButton('Historie'), QMessageBox.NoRole)
        msg.addButton(QPushButton('Abbruch'), QMessageBox.RejectRole)
        if msg.exec_() == 1: sys.exit()
        esp = None

    main(esp, reporter, logPath)
    if esp is not None:
        esp.connectWidget(None)
        esp.stop()


