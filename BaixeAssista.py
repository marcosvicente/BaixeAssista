# -*- coding: ISO-8859-1 -*-
import os
import sys

from PySide import QtCore, QtGui


os.environ['DJANGO_SETTINGS_MODULE'] = "main.settings"

from main.app.manager.server import Server
from main.app.win.loader import Loader
from main.app.util import base
from main import settings
import locale

server = Server()
server.start()

app = QtGui.QApplication(sys.argv)

trans = QtCore.QTranslator()
base.trans_install(Loader.config)

code, encoding = locale.getdefaultlocale()
userCode = Loader.config["Lang"]["code"]
booted = Loader.config["Window"].as_bool("booted")
i18nDir = os.path.join(settings.INTERFACE_DIR, "i18n")

if not booted:
    filename = "en_US_%s.qm" % (code if not code is None else userCode)
    filepath = os.path.join(i18nDir, filename)

    code = code if trans.load(filepath) else userCode

    Loader.config["Lang"]["code"] = code
else:
    filepath = os.path.join(i18nDir, "en_US_%s.qm" % userCode)
    trans.load(filepath)

app.installTranslator(trans)

loader = Loader()
loader.show()

sys.exit(app.exec_())



