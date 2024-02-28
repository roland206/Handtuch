import pathlib
import platform
from ESP import *
from HandtuchViewer import *
from HandtuchAnalyzer import *

class MainWindow(QTabWidget):
    def __init__(self, esp, logPath):
        super().__init__()
        if esp is not None: self.addTab(HandtuchViewer(esp), "Aktuell")
        self.analyzer = HandtuchAnalyzer(logPath)
        self.analyzer.loadLogFiles()
        self.addTab(self.analyzer, "Historie")
        self.currentChanged.connect(self.chanced)
        self.resize(2800, 1800)

    def chanced(self):
        widget = self.currentWidget()
        if (type(widget) == HandtuchAnalyzer):  self.analyzer.loadLogFiles()


if __name__ == '__main__':
    startSimu = True
    app = QApplication(sys.argv)
    os.chdir(pathlib.Path(__file__).parent.resolve())

    if 'indows' in platform.platform():
        logPath, linux  = '.\\', False
    else:
        logPath, linux = '/media/ramdisk/', True
    reporter = Reporter(logPath, Linux = linux)
    try:
        esp = ESP('Handtuch.para', reporter)
    except NoPort as inst:
        if not startSimu:
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
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("USB Error")
        msg.setInformativeText(str(inst))
        msg.setWindowTitle("Error")
        msg.addButton(QPushButton('Historie'), QMessageBox.NoRole)
        msg.addButton(QPushButton('Abbruch'), QMessageBox.RejectRole)
        if msg.exec_() == 1: sys.exit()
        esp = None

    main = MainWindow(esp, logPath)
    main.show()
    app.exec_()

    if esp is not None:
        esp.connectWidget(None)
        esp.stop()


