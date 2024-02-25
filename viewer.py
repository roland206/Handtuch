import os

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

def main(esp, reporter, simulation = False):
    app = QApplication(sys.argv)
    main = HandtuchViewer(esp, reporter, simulation)
    main.resize(2400, 1800)
    main.show()

    if simulation:
        esp.log = False
        fnames = QFileDialog.getOpenFileNames(main, 'Simulation File(s)', reporter._path, 'Log-files (*.log);;All Files (*)')
        print(str(fnames))
        for name in fnames[0]:
            esp.loadEventsFromFile(name)
    app.exec_()
    esp.connectWidget(None)

if __name__ == '__main__':

    os.chdir(pathlib.Path(__file__).parent.resolve())

    if 'indows' in platform.platform():
        reporter = Reporter('.', Linux = False)
    else:
        reporter = Reporter('/media/ramdisk/', Linux = True)


    try:
        esp = ESP('Handtuch.para', reporter, useHW=True)
    except NoPort as inst:
        app = QtWidgets.QApplication([])
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        detail = 'No USB Port found\nAvailable Ports :\n'
        for p, desc, hwid in sorted(inst.ports):
            detail += f'{p} : {desc}\n'
        msg.setText(detail)
        msg.setWindowTitle("Error")

        msg.addButton(QPushButton('Simulation'), QMessageBox.NoRole)
        msg.addButton(QPushButton('Abbruch'), QMessageBox.RejectRole)
        wish = msg.exec_()
        useHW = wish != 0
    except serial.serialutil.SerialException as inst:
        app = QtWidgets.QApplication([])
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("USB Error")
        msg.setInformativeText(str(inst))
        msg.setWindowTitle("Error")
        msg.addButton(QPushButton('Simulation'), QMessageBox.NoRole)
        msg.addButton(QPushButton('Abbruch'), QMessageBox.RejectRole)
        wish = msg.exec_()
        useHW = wish != 0
    else:
        wish = 2

    if wish == 1: sys.exit()
    if wish == 0: esp = ESP('Handtuch.para', reporter, useHW=False)
    main(esp, reporter, wish == 0)
    esp.stop()

