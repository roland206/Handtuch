import serial
import serial.tools.list_ports
import time

class ESP():
    def __init__(self, port = None, baud = 115200):
        if port is None:
            ports = serial.tools.list_ports.comports()
            for p, desc, hwid in sorted(ports):
                if 'CP210x' in desc: port = p
            if port is None: raise Exception("No CP210x Port available")
        self.port = serial.Serial(port, baud)

        para = [{'Name': 'Wasser marsch', 'Cmd': 'g', 'Min' : -1, 'Max' : 8}]
        para.append({'Name': 'Pumpe an', 'Cmd': 'P', 'Min': 1, 'Max': 60})
        para.append({'Name': 'Pumpe aus', 'Cmd': 'p', 'Min': 0, 'Max': 60})
        para.append({'Name': 'Gewicht max', 'Cmd': 'G', 'Min': 0, 'Max': 10})
        para.append({'Name': 'Gewicht up', 'Cmd': 'U', 'Min': 0, 'Max': 1000})
        para.append({'Name': 'Gewicht down', 'Cmd': 'D', 'Min': 0, 'Max': 2000})
        para.append({'Name': 'Wasser Zeit', 'Cmd': 'V', 'Min': 0, 'Max': 30})
        para.append({'Name': 'Wasser Pausen Zeit', 'Cmd': 'v', 'Min': 0, 'Max': 60})
        para.append({'Name': 'Wasser Zyklen', 'Cmd': 'Z', 'Min': 0, 'Max': 30})
    def reset(self):
        self.port.setRTS(False)
        time.sleep(0.5)
        self.port.setRTS(True)
        time.sleep(0.5)
        self.port.setRTS(False)

    def readMSG(self):
        msg = str(self.port.read_until(expected='\n',size=100))
        return msg

esp = ESP()
esp.reset()
