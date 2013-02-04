# -*- coding: ISO-8859-1 -*-
import os, sys
from PySide import QtCore, QtGui

os.environ['DJANGO_SETTINGS_MODULE'] = "main.settings"

from main.app.manager import Server
from main.app.win import loader
from main.app.util import base
from main import settings
from main import imps

sv = Server()
sv.start()

app = QtGui.QApplication(sys.argv)

base.trans_install()

# pesquisando por todos os arquivo de tradução da ui.
filename = "en_%s-py.qm" % loader.Loader.config["Lang"]["code"]
filepath = os.path.join(settings.INTERFACE_DIR, "i18n", filename)

translator = QtCore.QTranslator()
print "TL: ", translator.load( filepath )
app.installTranslator(translator)

mw = loader.Loader()
mw.show()

sys.exit(app.exec_())

