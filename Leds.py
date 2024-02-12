from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap
import os.path
import sys

class Led(QLabel):
    def __init__(self, colorIndex = 1, state = False):
        QLabel.__init__(self, parent=None)
        self.pixMaps = [QPixmap('LedAus.png'), QPixmap('LedRot.png'), QPixmap('LedGruen.png'), QPixmap('LedBlau.png'),
                   QPixmap('LedGelb.png'), QPixmap('LedOrange.png'), QPixmap('LedLila.png')]
        self.colorIndex = colorIndex
        self.setLedState(state)
    def setLedState(self, state):
        if type(state) is int:
            pass
        elif state:
            state = self.colorIndex
        else:
            state = 0
        self.setPixmap(self.pixMaps[state])
