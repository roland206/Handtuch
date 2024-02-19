from PyQt5 import QtWidgets, uic
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QCheckBox, QFormLayout, QTabWidget
#import pyqtgraph as pg
import sys
import numpy as np
from ESP import *
from HandtuchViewer import *


class MainWindow(QTabWidget):
    def __init__(self, esp, reporter):
        super(MainWindow, self).__init__()
        self.addTab(HandtuchViewer(esp, reporter)   , "Verlauf")
        self.resize(2400, 1800)
 #       self.addTab(HandtuchParameter(esp), "Parameter")

def main(esp, reporter):
    app = QApplication(sys.argv)
    main = MainWindow(esp, reporter)
    main.show()
    app.exec_()
    esp.connectWidget(None)

if __name__ == '__main__':

    reporter = Reporter('/media/ramdisk/')
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
        msg.exec_()
    except serial.serialutil.SerialException as inst:
        app = QtWidgets.QApplication([])
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("USB Error")
        msg.setInformativeText(str(inst))
        msg.setWindowTitle("Error")
        msg.exec_()
    else:
        main(esp, reporter)
        esp.stop()
    sys.exit()