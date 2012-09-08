# -*- coding: ISO-8859-1 -*-
import os, sys

from django.core.management import execute_manager
os.environ['DJANGO_SETTINGS_MODULE'] = "main.settings"

import wx
import main
from main.app import *
from main.app.window import mainWin

def run():
	if len(sys.argv) > 1:
		try:
			execute_manager( main.settings )
		except Exception, err:
			print "ManagerErr: %s"%err
		exit(0)
	# -----------------------------------------------
	
	app = wx.App(False) # arg: False n?o redirecionar
	mainWin.BaixeAssistaWin()
	app.MainLoop()


# ---------------------------------------------------
if __name__== "__main__":
	run()
