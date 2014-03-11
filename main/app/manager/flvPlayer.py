# coding: utf-8
import subprocess
import threading

from main.app.util import base


class FlvPlayer(threading.Thread):
    """ Classe usada no controle de programas externos(players) """

    def __init__(self, cmd="", filepath="", url=""):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.url = url if url else '"%s"' % filepath

        self.process = None
        self.running = False

        self.setDaemon(True)

    @base.Protected
    def stop(self):
        """ stop player process """
        self.process.terminate()

    def isRunning(self):
        return self.running

    def start(self, **kwargs):
        """ modo de compatibilidade """
        return super(self.__class__, self).start()

    @staticmethod
    def permission_run(cmd, params):
        """ Executa um processo, porï¿½m requistando permissï¿½es. """
        import win32com.shell.shell as shell
        from win32com.shell import shellcon
        from win32con import SW_NORMAL
        import win32event
        import win32api

        process = shell.ShellExecuteEx(
            lpVerb="runas", lpFile=cmd, fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
            lpParameters=params, nShow=SW_NORMAL
        )
        class Process(object):
            processHandle = process["hProcess"]

            @staticmethod
            def terminate():
                win32api.TerminateProcess(process["hProcess"], 0)

            @staticmethod
            def wait():
                win32event.WaitForSingleObject(process["hProcess"], win32event.INFINITE)
        return Process

    def run(self):
        try:
            self.process = self.permission_run(self.cmd, self.url)
            self.running = True
            self.process.wait()
        except ImportError:
            self.process = subprocess.Popen(self.url, executable=self.cmd)
            self.running = True
            self.process.wait()
        finally:
            self.running = False