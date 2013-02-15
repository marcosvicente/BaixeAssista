# coding: utf-8
from main.app.util import base
from main import settings
import threading
import configobj
import os

class ProxyManager(object):
    lockNewIp = threading.Lock()
    
    def __init__(self):
        self.configPath = os.path.join(settings.CONFIGS_DIR, "iplist.txt")
        self.iplist = configobj.ConfigObj( self.configPath )
        
    def __del__(self):
        self.save()
        del self.iplist
        
    def get_num(self):
        """ retorna o número de ips armazenados no arquivo """
        return len(self.iplist)
        
    def save(self):
        """ Salva todas as modificações """
        self.free_all()
        
        if not base.security_save(self.configPath,  _configobj=self.iplist):
            print "Erro salvando lista de ips!!!"
            
    def free_all(self):
        """ libera todos o ips do lock """
        for ip in self.iplist.iterkeys():
            self.unlock(ip)
        
    def get_formated(self):
        """Retorna um servidor proxy ja mapeado: {"http": "http://0.0.0.0}"""
        return self.formate( self.get_new() )
        
    def formate(self, proxy):
        """Retorna o servidor proxy mapeado: {"http": "http://0.0.0.0}"""
        return {"http": "http://%s"%proxy}
    
    def get_new(self):
        """ retorna um novo ip sem formatação -> 250.180.200.125:8080 """
        with self.lockNewIp:
            iplistkey = self.iplist.keys()
            newip = ""
            for ip in iplistkey:
                obj = self.iplist[ip]
                if obj.as_bool("lock"): continue
                if obj.as_int("rate") >= 0:
                    newip = ip; break
            else:
                for ip in iplistkey:
                    obj = self.iplist[ip]
                    if obj.as_bool("lock"): continue
                    newip = ip; break
        self.iplist[newip]["lock"] = True
        return newip
        
    def unlock(self, ip):
        self.iplist[ip]["lock"] = False
        
    def unformate(self, ip):
        """ removendo a formatação do ip """
        if type(ip) is dict: ip = ip["http"]
        if ip.startswith("http://"): 
            ip = ip[len("http://"):]
        return ip
        
    def set_bad(self, ip):
        """ abaixando a taxa de credibilidade do ip """
        rate = self.iplist[ self.unformate( ip ) ].as_int("rate")
        self.iplist[ self.unformate( ip ) ]["rate"]  = rate-1 if rate > -1 else -1
        print "Bad ip: %s"%self.unformate( ip )
        
    def set_good(self, ip):
        """ aumentando a credibilidade do ip """
        rate = self.iplist[ self.unformate( ip ) ].as_int("rate")
        self.iplist[ self.unformate( ip ) ]["rate"]  = rate+1 if rate < 1 else 1
        print "Good ip: %s"%self.unformate( ip )
        
