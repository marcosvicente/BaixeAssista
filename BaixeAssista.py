# -*- coding: ISO-8859-1 -*-
import os
os.environ['DJANGO_SETTINGS_MODULE'] = "main.settings"
from main.app.manager import Server
from main.app.window import mainWin
from main import imps
import wx

sv = Server()
sv.start()

app = wx.App( False )
mainWin.BaixeAssistaWin()
app.MainLoop()

