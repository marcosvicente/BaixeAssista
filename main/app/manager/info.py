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
    update_sleep = 0.05
    info_timer = {}
    info = {}

    class Synchronize(object):
        """ Sicroniza as alterações sobre 'info' nas diferentes threads """
        lock = threading.RLock()

        def __init__(self, func):
            self.func = func

        def __call__(self, *args, **kwargs):
            with self.lock:
                return self.func(*args, **kwargs)

    @classmethod
    @Synchronize
    def send(cls, *args, **kwargs):
        if len(kwargs["fields"]) == 1:
            field = kwargs["fields"][0]
            if (time.time() - cls.info_timer[field]) < cls.update_sleep:
                time.sleep(cls.update_sleep)
                cls.info_timer[field] = time.time()
        cls.update.send(*args, **kwargs)

    @classmethod
    @Synchronize
    def add(cls, ident):
        cls.info[ident] = {}

    @classmethod
    @Synchronize
    def delete(cls, ident):
        return cls.info.pop(ident, None)

    @classmethod
    @Synchronize
    def get(cls, ident, name):
        if ident in cls.info:
            items = cls.info[ident]
        else:
            items = {}
        return items.get(name, '')

    @classmethod
    @Synchronize
    def set(cls, ident, name, value):
        cls.info[ident][name] = value
        cls.info_timer.setdefault(name, time.time())
        cls.send(ident, fields=(name,))

    @classmethod
    @Synchronize
    def clear(cls, ident, *names, **params):
        for name in (names or cls.info[ident]):
            if not name in params.get("exclude", []):
                cls.info[ident][name] = ''
        cls.send(ident, fields=names)