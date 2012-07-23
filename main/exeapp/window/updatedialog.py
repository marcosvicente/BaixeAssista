# -*- coding: ISO-8859-1 -*-
import os
import wx
import sys
import math
from wx.lib.agw import ultimatelistctrl as ULC

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necessário para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )
########################################################################

class UpdateDialog( wx.MiniFrame):
	def __init__( self, mainWin, title="", pos=wx.DefaultPosition, 
	              size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE ):
		wx.MiniFrame.__init__(self, mainWin, -1, title, pos, size, style)
		
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.SetBackgroundColour("BEIGE")
		
		self.SetMinSize((500, 230))
		self.SetMaxSize((750, 450))
		self.SetSize((620, 320))
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		# *** Painel - texto informativo.
		painel = wx.Panel( self, -1)
		mainSizer.Add(painel, 1, wx.EXPAND|wx.TOP, 5)
		
		painelBoxSizer = wx.BoxSizer(wx.VERTICAL)
		painel.SetSizer(painelBoxSizer)
		painel.SetAutoLayout(True)
		
		# *** Texto informativo.
		self.textInfo = wx.StaticText(painel, -1, "...")
		self.textInfo.SetForegroundColour(wx.BLUE)
		self.textInfo.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Arial'))
		painelBoxSizer.Add(self.textInfo, 1, wx.EXPAND|wx.TOP|wx.LEFT, 10)
		# ===============================================================
		
		# *** Texto das modificações
		box = wx.StaticBox(painel, -1, _("O que mudou"))
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		painelBoxSizer.Add(bsizer, 5, wx.EXPAND|wx.ALL, 2)
		
		self.textControl = wx.TextCtrl(painel, -1, style=wx.TE_MULTILINE|wx.TE_READONLY)
		bsizer.Add(self.textControl, 1, wx.EXPAND)
		# ===============================================================
		
		# *** Painel
		painel = wx.Panel(self, -1)
		painel.SetBackgroundColour(wx.Colour(210,210,210))
		
		hSizer = wx.BoxSizer( wx.HORIZONTAL )
		painel.SetSizer( hSizer)
		painel.SetAutoLayout(True)

		mainSizer.Add(painel, 0, wx.EXPAND|wx.TOP)
		
		info = wx.StaticText(painel, -1, _(u"Será necessário reiniciar o programa."))
		info.SetForegroundColour(wx.RED)
		hSizer.Add(info, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.RIGHT, 5)
		
		hSizer.AddStretchSpacer()
		
		self.btnOk = wx.Button( painel, -1, "OK")
		self.Bind(wx.EVT_BUTTON, self.OnClose, self.btnOk)
		hSizer.Add(self.btnOk, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 5)
		# ===============================================================
		
		self.SetAutoLayout(True)
		self.SetSizer( mainSizer )
		self.Show(False)
		
	def OnClose(self, evt=None):
		self.Destroy()
		
	def setInfo(self, text):
		self.textInfo.SetLabel(text)
		
	def writeText(self, text):
		self.textControl.WriteText(text)
		
########################################################################
if __name__ == "__main__":
	# dir com os diretórios do projeto
	os.chdir( pardir )
	
	from manager import installTranslation
	installTranslation() # instala as traduções.
	
	def onClose(evt):
		obj = evt.GetEventObject()
		obj.Destroy()
		
	app = wx.App(False)
	try:
		frame = wx.Frame(None, -1, "Fram", size = (800, 500))
		frame.Bind(wx.EVT_CLOSE, onClose)
		
		control = UpdateDialog(frame, "Development title")
		
		control.setInfo("Informa o sucesso da atualização")
		control.writeText(("blafgsdfgsdfgsdfgsdfgsdfgsd\n"*3))
		control.Show(True)
	except Exception, err:
		print err

	frame.Show()
	app.MainLoop()
		
