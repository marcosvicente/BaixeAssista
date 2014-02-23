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
    def event_update(cls, *args, **kwargs):
        if len(kwargs["fields"]) == 1:
            field = kwargs["fields"][0]
            if (time.time() - cls.info_timer[field]) < cls.update_sleep:
                time.sleep(cls.update_sleep)
                cls.info_timer[field] = time.time()
        cls.update.send(*args, **kwargs)

    @classmethod
    def sent_event(cls, *args, **kwargs):
        """ Emitindo o sinal para atualização de I/O """
        th = threading.Thread(target=cls.event_update, args=args, kwargs=kwargs)
        th.start()

    @classmethod
    def add(cls, identify):
        cls.info[identify] = {}

    @classmethod
    def delete(cls, identify):
        return cls.info.pop(identify, None)

    @classmethod
    def get(cls, identify, info):
        return cls.info.get(identify, {}).get(info, '')

    @classmethod
    @Synchronize
    def set(cls, identify, info, value):
        cls.info[identify][info] = value
        cls.info_timer.setdefault(info, time.time())
        cls.sent_event(sender=identify, fields=(info,))

    @classmethod
    @Synchronize
    def clear(cls, identify, *args, **params):
        args = [name for name in (args or cls.info[identify]) if not name in params.get("exclude", [])]
        for info in args:
            cls.info[identify][info] = ''
        cls.sent_event(sender=identify, fields=args)