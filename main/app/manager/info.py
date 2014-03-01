# coding: utf-8
import threading
import time

from django.dispatch import Signal


class Info(object):
    """ Guarda o estado do objeto adicionado """
    ##
    # 'Signal' usado para notificar atualização dos dados de I/O
    ##
    update = Signal(providing_args=["fields"])
    lock = threading.RLock()
    update_sleep = 0.05
    info_timer = {}
    info = {}

    @classmethod
    def send(cls, *args, **kwargs):
        if len(kwargs["fields"]) == 1:
            field = kwargs["fields"][0]
            if (time.time() - cls.info_timer[field]) < cls.update_sleep:
                time.sleep(cls.update_sleep)
                cls.info_timer[field] = time.time()
        cls.update.send(*args, **kwargs)

    @classmethod
    def add(cls, ident):
        cls.info[ident] = {}

    @classmethod
    def delete(cls, ident):
        return cls.info.pop(ident, None)

    @classmethod
    def get(cls, ident, name):
        return cls.info[ident].get(name, '') if ident in cls.info else ''

    @classmethod
    def set(cls, ident, name, value):
        with cls.lock:
            cls.info[ident][name] = value
            cls.info_timer.setdefault(name, time.time())
            cls.send(ident, fields=(name,))

    @classmethod
    def clear(cls, ident, *names, **params):
        with cls.lock:
            for name in (names or cls.info[ident]):
                if not name in params.get("exclude", []):
                    cls.info[ident][name] = ''
            cls.send(ident, fields=names)