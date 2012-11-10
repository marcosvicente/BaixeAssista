# -*- coding: ISO-8859-1 -*-
import os
import wx
import sys
import math
from wx.lib.agw import ultimatelistctrl as ULC

current_dir = None # indicador de mudança do dir
parent_dir = os.path.dirname(os.getcwd())

# ao ser importado, o diretório pai já estará 
# configurado pelo módulo principal.
# a mudança, aqui, será apenas com o objetivo de teste.
if __name__ == "__main__":
	# variável com o "path" do diretorio atual.
	# pode ser usada para acesso a dados do pacote
	current_dir = os.getcwd()
	
	# o diretório pai é onde estão os arquivos do projeto.
	if not parent_dir in sys.path:
		sys.path.append( parent_dir )
	
	# dir com os diretórios do projeto
	os.chdir( parent_dir )
	
	from main.app.util import base
	base.trans_install() # instala as traduções.
#################################################################################################

class ProgressDialog( wx.MiniFrame):
	def __init__( self, mainWin, title, pos=wx.DefaultPosition, 
	              size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE ):
		wx.MiniFrame.__init__(self, mainWin, -1, title, pos, size, style)
		self.SetBackgroundColour("BEIGE")
		
		self.SetMinSize((500, 230))
		self.SetMaxSize((650, 350))
		self.SetSize((620, 320))
		
		self._wasCanceled = False
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		# *** Painel - texto informativo.
		painel = wx.Panel( self, -1)
		mainSizer.Add(painel, 1, wx.EXPAND|wx.TOP, 5)
		
		painelBoxSizer = wx.BoxSizer(wx.VERTICAL)
		painel.SetSizer(painelBoxSizer)
		painel.SetAutoLayout(True)
		
		# *** Texto informativo.
		self.textInfo = wx.StaticText(painel, -1, "")
		self.textInfo.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Courier New'))
		self.textInfo.SetForegroundColour(wx.BLUE)
		painelBoxSizer.Add(self.textInfo, 1, wx.EXPAND|wx.TOP|wx.LEFT, 10)
		
		# *** Texto de aviso.
		box = wx.StaticBox(painel, -1, "info")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		painelBoxSizer.Add(bsizer, 2, wx.EXPAND|wx.ALL, 2)
		
		self.textControl = wx.TextCtrl(painel, -1, style=wx.TE_MULTILINE)
		bsizer.Add(self.textControl, 1, wx.EXPAND)
		
		# *** Barra de progresso.
		self.progress = wx.Gauge(self, -1, 100)
		mainSizer.Add(self.progress, 0, wx.EXPAND|wx.ALL, 5)
		# ---------------------------------------------------------
		
		# *** Painel - botão cancelar.
		painel = wx.Panel(self, -1)
		painel.SetBackgroundColour(wx.Colour(210,210,210))
		
		hSizer = wx.BoxSizer( wx.HORIZONTAL )
		painel.SetSizer( hSizer)
		painel.SetAutoLayout(True)

		mainSizer.Add(painel, 0, wx.EXPAND|wx.TOP)
		
		hSizer.AddStretchSpacer()
		
		self.btnOk = wx.Button( painel, -1, "OK")
		self.Bind(wx.EVT_BUTTON, self.OnClose, self.btnOk)
		hSizer.Add(self.btnOk, 0, wx.LEFT|wx.TOP|wx.BOTTOM, 5)
		self.btnOk.Enable(False)
		
		# *** Botão cancelar.
		self.btnCancel = wx.Button( painel, -1, _("Cancelar"))
		self.Bind(wx.EVT_BUTTON, self.OnCancel, self.btnCancel)
		
		hSizer.Add(self.btnCancel, 0, wx.LEFT|wx.TOP|wx.BOTTOM, 5)
		# ---------------------------------------------------------
		
		self.SetSizer( mainSizer )
		self.CenterOnParent() #centralizado
		self.Show(True)		
		
	def stopProgress(self):
		self.progress.SetValue(0)
		
	def enabeButton(self, _bool=True):
		self.btnCancel.Enable(not _bool)
		self.btnOk.Enable(_bool)
		
	def OnClose(self, evt=None):
		self.Destroy()
		
	def wasCancelled(self):
		return self._wasCanceled
	
	def updateTextControl(self, text):
		if text: # messagem de algum erro, aviso.
			# força a escrita para o final do texto atual.
			textSize = len(self.textControl.GetValue()) + 1
			self.textControl.SetSelection(textSize,textSize)
			
			self.textControl.WriteText(text+u"\n\n")
			
	def update(self, textInfo="", textWarning=""):
		self.textInfo.SetLabel(textInfo)
		self.updateTextControl(textWarning)
		self.progress.Pulse()
		self.Layout()
		
	def OnCancel(self, evt=None):
		self._wasCanceled = True
		
##################################################################################################

if __name__=='__main__':
	def onClose(evt):
		obj = evt.GetEventObject()
		parent = obj.GetParent()
		parent.Destroy()
		obj.Destroy()
		
	app = wx.App(False)
	try:
		frame = wx.Frame(None, -1, "Fram", size = (800, 500))
		control = ProgressDialog(frame, "ProgressDialog")
		control.Bind(wx.EVT_CLOSE, onClose)
		control.update(("blafgsdfgsdfgsdfgsdfgsdfgsd\n"*3), ("fadfa"*100))
	except Exception, err:
		print err

	frame.Show()
	app.MainLoop()
		
