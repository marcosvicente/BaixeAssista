# coding: utf-8
import threading
import os

import configobj

from main.app.util import base
from main import settings


class ProxyManager(object):

    lock_ip = threading.Lock()

    def __init__(self):
        self.config_path = os.path.join(settings.CONFIGS_DIR, "iplist.txt")
        self.ips = configobj.ConfigObj(self.config_path)

    def __del__(self):
        self.save()
        del self.ips

    def get_num(self):
        """ Returns the number of ips stored in the file """
        return len(self.ips)

    def save(self):
        """ Saves all changes """
        self.unlock_all()
        if not base.security_save(self.config_path, _configobj=self.ips):
            print("Erro salvando lista de IPS!")

    def unlock_all(self):
        """ Releases all the ips of the lock """
        for ip in list(self.ips.keys()):
            self.unlock(ip)

    def get_formatted(self):
        """Retorna um servidor proxy ja mapeado: {"http": "http://0.0.0.0}"""
        return self.format(self.get_new())

    @staticmethod
    def format(proxy):
        """ mapper {"http": "http://0.0.0.0} """
        return {"http": "http://%s" % proxy}

    def get_new(self):
        """ retorna um novo ip sem formatação -> 250.180.200.125:8080 """
        with self.lock_ip:
            ips = list(self.ips.keys())
            for ip in ips:
                obj = self.ips[ip]
                if obj.as_bool("lock"):
                    continue
                if obj.as_int("rate") >= 0:
                    choose_ip = ip
                    break
            else:
                for ip in ips:
                    obj = self.ips[ip]
                    if obj.as_bool("lock"):
                        continue
                    choose_ip = ip
                    break
                else:
                    choose_ip = ips[-1]
            self.ips[choose_ip]["lock"] = True
        return choose_ip

    def unlock(self, ip):
        self.ips[ip]["lock"] = False

    @staticmethod
    def unformat(ip):
        """ Removing formatting ip """
        if type(ip) is dict:
            ip = ip["http"]
        if ip.startswith("http://"):
            ip = ip[len("http://"):]
        return ip

    def set_bad(self, ip):
        """ Lowering the rate of credibility of IP """
        rate = self.ips[self.unformat(ip)].as_int("rate")
        self.ips[self.unformat(ip)]["rate"] = rate - 1 if rate > -1 else -1
        print("Bad ip: {!s}".format(self.unformat(ip)))

    def set_good(self, ip):
        """ Increasing the credibility of the IP """
        rate = self.ips[self.unformat(ip)].as_int("rate")
        self.ips[self.unformat(ip)]["rate"] = rate + 1 if rate < 1 else 1
        print("Good ip: {!s}".format(self.unformat(ip)))