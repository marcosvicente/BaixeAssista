# coding: utf-8
from django.dispatch import Signal
import threading
import time

class Info(object):
    """ guarda o estado do objeto adicionado """
    # 'Signal' usado para notificar atualização dos dados de I/O
    update = Signal(providing_args=["fields"])
    updateSleep = 0.05
    info = {}
    infoTimer = {}
    
    class sincronize(object):
        """ sicroniza as alterações sobre 'info' nas diferentes threads """
        _lock = threading.RLock()
        def __init__(self, func): self.func = func
        def __call__(self, *args, **kwargs):
            with self._lock: return self.func(*args,**kwargs)
        
    @classmethod
    @sincronize
    def eventUpdate(cls, *args, **kwargs):
        field = kwargs["fields"][0]
        
        if len(kwargs["fields"]) == 1:
            if (time.time() - cls.infoTimer[field]) < cls.updateSleep:
                time.sleep( cls.updateSleep )
                cls.infoTimer[field] = time.time()
                
        cls.update.send(*args, **kwargs)
        
    @classmethod
    def sendEvent(cls, *args, **kwargs):
        """ emitindo o sinal para atualização de I/O """
        th = threading.Thread(target = cls.eventUpdate, 
                              args = args, kwargs = kwargs)
        th.start()
        
    @classmethod
    def add(cls, rootkey):
        cls.info[rootkey] = {}
        
    @classmethod
    def delete(cls, rootkey):
        return cls.info.pop(rootkey,None)
    
    @classmethod
    def get(cls, rootkey, infokey):
        return cls.info.get(rootkey,{}).get(infokey,"")
    
    @classmethod
    @sincronize
    def set(cls, rootkey, infokey, info):
        cls.info[rootkey][infokey] = info
        cls.infoTimer.setdefault(infokey, time.time())
        cls.sendEvent(sender=rootkey, fields=(infokey,))
        
    @classmethod
    @sincronize
    def clear(cls, rootkey, *keys, **params):
        keys = [name for name in (keys or cls.info[rootkey]) if not name in params.get("exclude",[])]
        for infokey in keys: cls.info[rootkey][infokey] = ""
        cls.sendEvent(sender=rootkey, fields=keys)
        
        