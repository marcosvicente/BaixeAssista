# -*- coding: ISO-8859-1 -*-
import os
import wx
import sys

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necessário para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )

import proxy, manager
########################################################################

class wIPSearch( wx.MiniFrame ):
	def __init__(self, mainWin, title, pos=wx.DefaultPosition, 
	              size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE ):
		wx.MiniFrame.__init__(self, mainWin, -1, title, pos, size, style)

		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
		self.SetMinSize((640, 300)); self.SetMaxSize((720, 335))
		
		self.mainWin = mainWin
		
		# objeto pesquisador dos ips dos servidores proxies
		self.proxyControl = proxy.ProxyControl(True)
		self.stopSearch = self.startSearch = False
		self.ctrSearch = None
		
		self.updateTimer = wx.Timer(self, wx.ID_ANY)
		self.Bind( wx.EVT_TIMER, self.updateInterface, self.updateTimer)
		
		mainSizer = wx.BoxSizer( wx.VERTICAL)
		
		# *** Controle de entrada de urls.
		hSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		self.ctrStreamUrl = wx.TextCtrl(self, -1, "")
		helpText = _(u"Url para a qual serão direcionadas as conexões.\n")
		self.ctrStreamUrl.SetToolTip( wx.ToolTip( helpText ))
		hSizer.Add( self.ctrStreamUrl, 1, wx.EXPAND)
		
		# *** Botão de iniciar a pesquisa.
		self.btnStartCancel = wx.ToggleButton(self, -1, _("Pesquisar"))
		helpText = [
		    _("Inicia a busca por novos ips.\n"),
		    _("Pode demorar para concluir, por isso espere.")
		]
		self.btnStartCancel.SetToolTip( wx.ToolTip( "".join(helpText) ))
		hSizer.Add( self.btnStartCancel, 0, wx.LEFT, 2)

		self.Bind(wx.EVT_TOGGLEBUTTON, self.startIPSearch, self.btnStartCancel)
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
		
		staticText = wx.StaticText(conteiner, -1, _(u"Número de bytes: "))
		staticText.SetForegroundColour(wx.Colour(0,0,255))
		self.ctrBlockSize = wx.Choice(conteiner, -1, choices = self.getKbyteList())
		helpText = _(u"Quantos bytes serão lidos para cada teste de leitura.")
		self.ctrBlockSize.SetToolTip( wx.ToolTip( helpText ))
		self.ctrBlockSize.SetSelection(1)
		
		flexGridGroup.AddMany([(staticText, 0, wx.EXPAND),
		                         (self.ctrBlockSize, 0, wx.EXPAND)])
		# ---------------------------------------------
		
		staticText = wx.StaticText(conteiner, -1, _(u"Conexões simultâneas: "))
		staticText.SetForegroundColour(wx.Colour(0,0,255))
		self.ctrNumConnection = wx.SpinCtrl(conteiner, -1, "10")
		helpText = _(u"Quantas conexões serão criadas ao mesmo tempo.")
		self.ctrNumConnection.SetToolTip( wx.ToolTip( helpText ))
		self.ctrNumConnection.SetRange(1, 25)

		flexGridGroup.AddMany([(staticText, 0, wx.EXPAND),
		                         (self.ctrNumConnection, 0, wx.EXPAND)])
		# ---------------------------------------------

		staticText = wx.StaticText(conteiner, -1, _(u"Número de ips: "))
		staticText.SetForegroundColour(wx.Colour(0,0,255))
		self.ctrNumOfIps = wx.SpinCtrl(conteiner, -1, "25")
		helpText = _(u"Quantidade de ips válidos a serem encontrados.")
		self.ctrNumOfIps.SetToolTip( wx.ToolTip( helpText ))
		self.ctrNumOfIps.SetRange(1, 100)

		flexGridGroup.AddMany([(staticText, 0, wx.EXPAND), 
		                         (self.ctrNumOfIps, 0, wx.EXPAND)])
		# ---------------------------------------------

		staticText = wx.StaticText(conteiner, -1, _(u"Número de testes: "))
		staticText.SetForegroundColour(wx.Colour(0,0,255))
		self.ctrNumOfTests = wx.SpinCtrl(conteiner, -1, "3")
		helpText = _(u"Quantos testes de leitura serão efetuados sobre o mesmo ip.")
		self.ctrNumOfTests.SetToolTip( wx.ToolTip( helpText ))
		self.ctrNumOfTests.SetRange(1, 15)

		flexGridGroup.AddMany([(staticText, 0, wx.EXPAND), 
		                         (self.ctrNumOfTests, 0, wx.EXPAND)])
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
		
	def check_configs(self, configs):
		""" caso as configs não existam, força uma configuração padrão """
		default_conf = (
			("ctrStreamUrl", ""), ("ctrBlockSize", 1),
			("ctrNumOfIps", 25), ("ctrNumOfTests", 4),
			("ctrNumConnection", 10)
		)
		if not configs.has_key("wIPSearch"):
			configs["wIPSearch"] = {}
			
		for confname, default in default_conf:
			if not configs["wIPSearch"].has_key( confname ):
				configs["wIPSearch"][confname] = default
		
	def setLastConfigs(self, configs={}):
		configs = getattr(self.mainWin, "configs", configs)
		self.check_configs( configs )
		conf = configs["wIPSearch"]
		self.ctrStreamUrl.SetValue(conf["ctrStreamUrl"])
		self.ctrBlockSize.SetSelection(conf.as_int("ctrBlockSize"))
		self.ctrNumConnection.SetValue(conf.as_int("ctrNumConnection"))
		self.ctrNumOfIps.SetValue(conf.as_int("ctrNumOfIps"))
		self.ctrNumOfTests.SetValue(conf.as_int("ctrNumOfTests"))
		
	def saveConfigs(self, configs={}):
		configs = getattr(self.mainWin, "configs", configs)
		self.check_configs( configs )
		conf = configs["wIPSearch"]
		conf["ctrStreamUrl"] = self.ctrStreamUrl.GetValue()
		conf["ctrBlockSize"] = self.ctrBlockSize.GetSelection()
		conf["ctrNumConnection"] = self.ctrNumConnection.GetValue()
		conf["ctrNumOfIps"] = self.ctrNumOfIps.GetValue()
		conf["ctrNumOfTests"] = self.ctrNumOfTests.GetValue()
		
	def __del__(self):
		del self.proxyControl
		del self.ctrSearch
		
	@staticmethod
	def getKbyteList(start = 32):
		kbyteCount = start
		listKbyte = ["%dk"%kbyteCount]
		while kbyteCount < 1024:
			kbyteCount *= 2
			listKbyte.append("%dk"%kbyteCount)
		return listKbyte
		
	def startIPSearch(self, evt):
		if not self.startSearch and self.btnStartCancel.GetValue():
			self.btnStartCancel.SetLabel(_("Cancelar"))
			self.log.SetLabel(_("Iniciando..."))
			
			self.startSearch, self.stopSearch = True, False
			
			url = self.ctrStreamUrl.GetValue()
			unit = self.ctrBlockSize.GetStringSelection()
			block_size = int(unit[:-1])*1024
			
			# parametros de controle dos threads
			params = {
			    "url": url,
			    "bytes_block_test": 13 + block_size,
			    "num_of_ips": self.ctrNumOfIps.GetValue(),
			    "num_of_tests": self.ctrNumOfTests.GetValue()
			}
			# recurços compartilhados pelas conexões
			self.ctrSearch = proxy.CtrSearch(numips = params['num_of_ips'])
			
			# cria e inicia as conexões
			for index in range(self.ctrNumConnection.GetValue()):
				conn = proxy.TesteIP(self.proxyControl, self.ctrSearch, params)
				self.ctrSearch.addConnection( conn )
				conn.start()
				
			# inicia a atualização da interface
			self.updateTimer.Start(1000)
			print "started..."
			
		# quando cancelar for pressionado
		elif not self.stopSearch: 
			self.btnStartCancel.SetLabel( _("Pesquisar") )
			self.ctrSearch.stopConnections()
			self.stopSearch = True
		else:
			self.log.SetLabel(_(u"Aguarde! Parando as conexões..."))
			
	def updateInterface(self, evt):
		if not self.stopSearch:
			self.log.SetLabel(_("Pesquisando %s") %self.ctrSearch.getLog())
			self.progress.Pulse()
			
			if not self.ctrSearch.isSearching():
				# salva a nova lista de ips criada
				self.ctrSearch.save()
				self.log.SetLabel( self.ctrSearch.getLog() )
				self.startSearch = self.stopSearch = False
				self.btnStartCancel.SetLabel( _("Pesquisar") )
				self.btnStartCancel.SetValue(False)
				self.progress.SetValue(0) # stop gauge
				# para a atividade de todas as conexões
				self.ctrSearch.stopConnections()
				self.updateTimer.Stop()
				
		elif not self.ctrSearch.isSearching():
			self.log.SetLabel(_("Pesquisa cancelada."))
			self.startSearch = self.stopSearch = False
			self.progress.SetValue(0) # stop gauge
			self.updateTimer.Stop()
		else:
			self.log.SetLabel(_("Por favor aguarde. Cancelando..."))
			
	def OnCloseWindow(self, event):
		self.saveConfigs() # guardando as últimas configurações
		# destruir a janela, com a pesquisa sendo realizada, pode gerar threads zumbis
		if self.startSearch: self.ctrSearch.stopConnections()
		self.Destroy()
		
########################################################################
if __name__ == "__main__":
	# dir com os diretórios do projeto
	os.chdir( pardir )
	
	from main.app.util import base
	base.trans_install() # instala as traduções.
	
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
		
		control = wIPSearch(frame, "wIPSearch")
		control.Bind(wx.EVT_CLOSE, onClose)
		control.CenterOnParent()
		
		app.MainLoop()
	except Exception, err:
		print err
