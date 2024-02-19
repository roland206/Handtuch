from datetime import datetime,timedelta
import os

class Reporter:
    def __init__(self, path = None):
        self._path = path
        self.verbose = True
        self._verbosityLevel = 0

    def setVerbosity(self, level):
        self._verbosityLevel = level
    def setLogfilePath(self, path):
        if path[-1] != '/': path += '/'
        self._path = path
    def deleteLogFiles(self):
        if self._path == None: return
        fileList = glob.glob(self._path + "*.log")
        for file in fileList:
            os.remove(file)
    def getCacheFilename(self, when):
        if self._path == None: return None
        return self._path + when.strftime("Handtuch_%y-%m-%d") + '.log'

    def logEvent(self, what):
        when = datetime.now()
        if self.verbose:
            print(when.strftime("%d.%b %H:%M:%S") + ":  " + what)
        with open(self.getCacheFilename(when), 'a+') as f:
            f.write(f'{what}')
    def talk(self, text, importance):
        if importance >= self._verbosityLevel:
        #    print(f'Gesagt wird : {text}')
            cmd = 'echo \' set MyTTS tts ' + text +  '\'' + ' | nc 192.168.188.40 7072 -w 1'
#            cmd = f'espeak-ng -vmb-de5 -s 120 \'{text}\''
            os.system(cmd)
