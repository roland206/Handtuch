import os

from PyQt5 import QtWidgets, uic
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QCheckBox, QFormLayout, QTabWidget
#import pyqtgraph as pg
import glob
import numpy as np
import pathlib
import platform
from HandtuchAnalyzer import *

def main(events):

    app = QApplication(sys.argv)
    main = HandtuchAnalyzer(events)
    main.resize(2400, 1800)
    main.show()
    app.exec_()

if __name__ == '__main__':

    os.chdir(pathlib.Path(__file__).parent.resolve())

    if 'indows' in platform.platform():
        path = 'C:\\Roland\\Python\\Handtuch\\Handtuch_*.log'
    else:
        path = '/media/ramdisk/'

    files = glob.glob(path)
    files.sort()
    events = createEvents()
    for file in files:
        loadEventFile(events, file)
    main(events)

