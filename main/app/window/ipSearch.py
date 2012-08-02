# -*- coding: ISO-8859-1 -*-
import os
import wx
import sys

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necess�rio para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )

import proxy, manager
########################################################################

class IpSearchControl(wx.MiniFrame):
	def __init__(self, mainWin, title, pos=wx.DefaultPosition, 
	              size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE ):
		wx.MiniFrame.__init__(self, mainWin, -1, title, pos, size, style)

		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
		
		self.SetMinSize((640, 300))
		self.SetMaxSize((720, 335))
		
		self.mainWin = mainWin
		
		# objeto pesquisador dos ips dos servidores proxies
		self.proxyControl = proxy.ProxyControl(True)
		self.pesquisaCancelada = self.pesquisaIniciada = False
		self.testControl = None
		
		self.updateTimer = wx.Timer(self, wx.ID_ANY)
		self.Bind( wx.EVT_TIMER, self.updateInterface, self.updateTimer)

		mainSizer = wx.BoxSizer( wx.VERTICAL)
		
		# *** Controle de entrada de urls.
		hSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		self.controlUrls = wx.TextCtrl(self, -1, "http://www.videobb.com/video/XuS6EAfMb7nf")
		helpText = [
		    _(u"Url para a qual ser�o direcionadas as conex�es.\n"),
		    _(u"Use: Videobb, Videozer ou UserPorn")
		]
		self.controlUrls.SetToolTip( wx.ToolTip( "".join(helpText) ))
		hSizer.Add( self.controlUrls, 1, wx.EXPAND)

		# *** Bot�o de iniciar a pesquisa.
		self.btnStartCancel = wx.ToggleButton(self, -1, _("Pesquisar"))
		helpText = [
		    _("Inicia a busca por novos ips.\n"),
		    _("Pode demorar para concluir, por isso espere.")
		]
		self.btnStartCancel.SetToolTip( wx.ToolTip( "".join(helpText) ))
		hSizer.Add( self.btnStartCancel, 0, wx.LEFT, 2)

		self.Bind(wx.EVT_TOGGLEBUTTON, self.iniciePesquisa, self.btnStartCancel)
		mainSizer.Add( hSizer, 0, wx.EXPAND|wx.TOP, 2)
		# ---------------------------------------------
		
		panel = wx.Panel(self, -1)
		panel.SetBackgroundColour(wx.Colour(222,222,222))
		panelSizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer( panelSizer)
		panel.SetAutoLayout(1)
		mainSizer.Add(panel, 0, wx.EXPAND)

		conteiner = wx.StaticBox(panel, -1, "")
		staticBoxSizer = wx.StaticBoxSizer(conteiner, wx.VERTICAL)
		panelSizer.Add(staticBoxSizer, 1, wx.EXPAND|wx.ALL, 10)
		
		# **** FlexGridSizer
		flexGridGroup = wx.FlexGridSizer(4, 2, 10, 50)
		staticBoxSizer.Add( flexGridGroup, 1, wx.EXPAND|wx.ALL, 10)
		flexGridGroup.AddGrowableCol(0)
		flexGridGroup.AddGrowableCol(1)
		
		staticText = wx.StaticText(conteiner, -1, _(u"N�mero de bytes: "))
		staticText.SetForegroundColour(wx.Colour(0,0,255))
		self.controlBytesTeste = wx.Choice(conteiner, -1, choices = self.createListChoices())
		helpText = _(u"Quantos bytes ser�o lidos para cada teste de leitura.")
		self.controlBytesTeste.SetToolTip( wx.ToolTip( helpText ))
		self.controlBytesTeste.SetSelection(1)

		flexGridGroup.AddMany([(staticText, 0, wx.EXPAND),
		                         (self.controlBytesTeste, 0, wx.EXPAND)])
		# ---------------------------------------------

		staticText = wx.StaticText(conteiner, -1, _(u"Conex�es simult�neas: "))
		staticText.SetForegroundColour(wx.Colour(0,0,255))
		self.controlThreads = wx.SpinCtrl(conteiner, -1, "10")
		helpText = _(u"Quantas conex�es ser�o criadas ao mesmo tempo.")
		self.controlThreads.SetToolTip( wx.ToolTip( helpText ))
		self.controlThreads.SetRange(1, 25)

		flexGridGroup.AddMany([(staticText, 0, wx.EXPAND),
		                         (self.controlThreads, 0, wx.EXPAND)])
		# ---------------------------------------------

		staticText = wx.StaticText(conteiner, -1, _(u"N�mero de ips: "))
		staticText.SetForegroundColour(wx.Colour(0,0,255))
		self.controlNumIps = wx.SpinCtrl(conteiner, -1, "25")
		helpText = _(u"Quantidade de ips v�lidos a serem encontrados.")
		self.controlNumIps.SetToolTip( wx.ToolTip( helpText ))
		self.controlNumIps.SetRange(1, 100)

		flexGridGroup.AddMany([(staticText, 0, wx.EXPAND), 
		                         (self.controlNumIps, 0, wx.EXPAND)])
		# ---------------------------------------------

		staticText = wx.StaticText(conteiner, -1, _(u"N�mero de testes: "))
		staticText.SetForegroundColour(wx.Colour(0,0,255))
		self.controlNumTestes = wx.SpinCtrl(conteiner, -1, "3")
		helpText = _(u"Quantos testes de leitura ser�o efetuados sobre o mesmo ip.")
		self.controlNumTestes.SetToolTip( wx.ToolTip( helpText ))
		self.controlNumTestes.SetRange(1, 15)

		flexGridGroup.AddMany([(staticText, 0, wx.EXPAND), 
		                         (self.controlNumTestes, 0, wx.EXPAND)])
		# ---------------------------------------------

		panel = wx.Panel(self, -1)
		mainSizer.Add(panel, 1, wx.EXPAND)
		panel.SetBackgroundColour(wx.Colour(235, 235, 235))
		panelSizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer( panelSizer )
		panel.SetAutoLayout(1)

		# barra de progresso
		self.progress = wx.Gauge(panel, -1, 100)

		hSizer = wx.BoxSizer( wx.HORIZONTAL )
		hSizer.Add( self.progress, 1, wx.EXPAND)

		panelSizer.Add( hSizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
		# ---------------------------------------------

		# label informativo
		self.log = wx.StaticText(panel, -1, "...")
		self.log.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Arial'))

		hSizer = wx.BoxSizer( wx.HORIZONTAL )
		hSizer.Add(self.log, 1, wx.EXPAND)

		panelSizer.Add(hSizer, 1, wx.EXPAND|wx.TOP|wx.LEFT, 10)
		# ---------------------------------------------

		self.SetAutoLayout(True)
		self.SetSizer( mainSizer)
		mainSizer.Fit( self)
		
		self.CenterOnParent(wx.BOTH)
		self.Show(True)
		
	def __del__(self):
		del self.proxyControl
		del self.testControl
		
	@staticmethod
	def createListChoices():
		kbyte = 32
		listaKbyte = ["%dk"%kbyte]
		while kbyte < 1024:
			kbyte *= 2
			listaKbyte.append("%dk"% kbyte)
		return listaKbyte
	
	def iniciePesquisa(self, evt):
		isPressed = self.btnStartCancel.GetValue()
		
		if not self.pesquisaIniciada and isPressed:
			self.btnStartCancel.SetLabel( _("Cancelar") )
			self.log.SetLabel( _("Iniciando...") )
			self.pesquisaCancelada = False
			self.pesquisaIniciada = True
			
			url = self.controlUrls.GetValue()
			unit = self.controlBytesTeste.GetStringSelection()
			bytesTeste = int(unit[:-1])*1024

			# parametros de controle dos threads
			params = { "URL": url,
			           "numBytesTeste": 13 + bytesTeste,
			           "numMaxTestes": self.controlNumTestes.GetValue(),
			           "metaProxies": self.controlNumIps.GetValue()}
			
			# recur�os compartilhados pelas conex�es
			self.testControl = proxy.TestControl(numips = params['metaProxies'])
			
			# cria e inicia as conex�es
			for n in range( self.controlThreads.GetValue()):
				connection = proxy.TesteIP(
				    self.proxyControl, self.testControl, params)
				
				self.testControl.addConnection( connection)
				connection.start()

			# inicia a atualiza��o da interface
			self.updateTimer.Start(1000)
			print "iniciado"
			
		# quando cancelar for pressionado
		elif self.pesquisaCancelada is False: 
			self.btnStartCancel.SetLabel( _("Pesquisar") )
			self.testControl.stopConnections()
			self.pesquisaCancelada = True
			
		else:
			self.log.SetLabel( _(u"Aguarde! Parando as conex�es...") )
			
	def updateInterface(self, evt):
		if not self.pesquisaCancelada:
			self.log.SetLabel( _("Pesquisando %s") % self.testControl.getLog())
			self.progress.Pulse()
			
			if not self.testControl.isSearching():
				# salva a nova lista de ips criada
				self.testControl.salveips()
				self.log.SetLabel( self.testControl.getLog() )
				self.pesquisaIniciada  = False
				self.pesquisaCancelada = False
				self.btnStartCancel.SetLabel( _("Pesquisar") )
				self.btnStartCancel.SetValue(False)
				self.progress.SetValue(0) # stop gauge
				# para a atividade de todas as conex�es
				self.testControl.stopConnections()
				self.updateTimer.Stop()
				
		elif not self.testControl.isSearching():
			self.log.SetLabel( _("Pesquisa cancelada.") )
			self.pesquisaIniciada  = False
			self.pesquisaCancelada = False
			self.progress.SetValue(0) # stop gauge
			self.updateTimer.Stop()
		else:
			self.log.SetLabel( _("Por favor aguarde. Cancelando...") )
			
	def OnCloseWindow(self, event):
		# destruir a janela, com a pesquisa sendo
		# realizada, pode gerar threads zumbis
		if self.pesquisaIniciada:
			self.testControl.stopConnections()
		self.Destroy()

########################################################################
if __name__ == "__main__":
	# dir com os diret�rios do projeto
	os.chdir( pardir )
	
	# instala as tradu��es.
	manager.installTranslation() 
	
	def onClose(evt):
		obj = evt.GetEventObject()
		parent = obj.GetParent()
		parent.Destroy()
		obj.Destroy()
		
	try:
		app = wx.App(False)
		frame = wx.Frame(None, -1, "Fram", size = (800, 500))
		frame.CenterOnScreen()
		frame.Show()
		
		control = IpSearchControl(frame, "IpSearchControl")
		control.Bind(wx.EVT_CLOSE, onClose)
		control.CenterOnParent()
		
		app.MainLoop()
	except Exception, err:
		print err