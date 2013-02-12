# coding: utf-8
from main.app.util import base
import subprocess
import threading

class FlvPlayer(threading.Thread):
    """ Classe usada no controle de programas externos(players) """
    
    def __init__(self, cmd="", filepath="", url=""):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.url = url if url else '"%s"'%filepath
        
        self.process = None
        self.running = False
        
        self.setDaemon(True)
        
    @base.protected()
    def stop(self):
        """ stop player process """
        self.process.terminate()
    
    def isRunning(self):
        return self.running
    
    @staticmethod
    def runElevated(cmd, params):
        """ executa um processo, porém requistando permissões. """
        import win32com.shell.shell as shell
        from win32com.shell import shellcon
        from win32con import SW_NORMAL
        import win32event, win32api
        
        process = shell.ShellExecuteEx(
            lpVerb="runas", lpFile=cmd, fMask=shellcon.SEE_MASK_NOCLOSEPROCESS, 
            lpParameters=params, nShow=SW_NORMAL
        )
        hProcess = process["hProcess"]
        class Process:
            processHandle = hProcess
            @staticmethod
            def terminate(): win32api.TerminateProcess(hProcess,0)
            @staticmethod
            def wait(): win32event.WaitForSingleObject(hProcess, win32event.INFINITE)
        return Process
    
    def run(self):
        try:
            self.process = self.runElevated(self.cmd, self.url)
            self.running = True; self.process.wait()
        except ImportError:
            self.process = subprocess.Popen(self.url, executable=self.cmd)
            self.running = True; self.process.wait()
        except: pass
        finally:
            self.running = False
            
    