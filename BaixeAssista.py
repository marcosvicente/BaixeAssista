# -*- coding: ISO-8859-1 -*-
import os, sys
from PySide import QtCore, QtGui

os.environ['DJANGO_SETTINGS_MODULE'] = "main.settings"

from main.app.manager import Server
from main.app.win import loader
from main import imps

sv = Server()
sv.start()

app = QtGui.QApplication(sys.argv)

translator = QtCore.QTranslator()
translator.load('mainLayout_pt')
app.installTranslator(translator)

mw = loader.Loader()
mw.show()

sys.exit(app.exec_())

