from PyQt5 import QtWidgets, uic
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QCheckBox, QFormLayout, QTabWidget
#import pyqtgraph as pg
import sys
import numpy as np
from ESP import *
from HandtuchViewer import *


class MainWindow(QTabWidget):
    def __init__(self, esp):
        super(MainWindow, self).__init__()
        self.addTab(HandtuchViewer(esp)   , "Verlauf")
        self.resize(2400, 1800)
 #       self.addTab(HandtuchParameter(esp), "Parameter")

def main(esp):
    app = QApplication(sys.argv)
    main = MainWindow(esp)
    main.show()
    app.exec_()
    esp.connectWidget(None)

if __name__ == '__main__':

    esp = ESP('Handtuch.para')
    main(esp)
    esp.stop()
    sys.exit()