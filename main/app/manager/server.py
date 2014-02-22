# coding: utf-8
import threading
import logging
import os

from django.core.management.commands import runserver


class Server(threading.Thread):
    logger = logging.getLogger("main.app.manager")

    BOOL_TO_INT = {True: 1, False: 0}
    INT_TO_BOOL = {1: True, 0: False}
    HOST, PORT = "localhost", 8002

    class __metaclass__(type):
        """ informa o estado do servidor, com base na vari�vel ambiente """

        @property
        def running(cls):
            flag = int(os.environ.get("LOCAL_SERVER_RUNNING", 0))
            return cls.INT_TO_BOOL[flag]

        @running.setter
        def running(cls, flag):
            os.environ["LOCAL_SERVER_RUNNING"] = str(cls.BOOL_TO_INT[flag])

    def __init__(self, host="localhost", port=8002):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        # update host
        Server.HOST = host
        Server.PORT = port

    def stop(self):
        pass

    def run(self):
        try:
            cmd = runserver.Command()
            Server.running = True
            self.logger.info("[SERVER] running...")
            cmd.execute("%s:%s" % (self.HOST, self.PORT), use_reloader=False)
        except Exception as e:
            self.logger.error("[SERVER] listen: %s" % e)
            Server.running = False
        self.logger.info("[SERVER] stopped!")