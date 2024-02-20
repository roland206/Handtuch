from datetime import datetime,timedelta
import os

class Reporter:
    def __init__(self, path = None, Linux = True, talk = 0, print = True):
        self._path = path
        self.verbose = True
        self.Linux = Linux
        self._talkLevel = talk
        self._print = print

    def setVerbosity(self, talk = None, print = None):
        if talk  is not None: self._talkLevel = talk
        if print is not None: self._print = print

    def getCacheFilename(self, when = None):
        if self._path == None: return None
        if when is None: when = datetime.now()
        return self._path + when.strftime("Handtuch_%y-%m-%d") + '.log'

    def logEvent(self, what):

        when = datetime.now()
        if self._print:
            print(when.strftime("%d.%b %H:%M:%S") + ":  " + what.replace('\n', ''))
        if self._path is None: return
        with open(self.getCacheFilename(), 'a+') as f:
            f.write(f'{what}')
    def talk(self, text, importance):
        if not self.Linux: return
        if importance >= self._talkLevel:
            cmd = 'echo \' set MyTTS tts ' + text +  '\'' + ' | nc 192.168.188.40 7072 -w 1'
#            cmd = f'espeak-ng -vmb-de5 -s 120 \'{text}\''
            os.system(cmd)
