# -*- coding: ISO-8859-1 -*-

import os
import wx
import sys
import math
import wx.lib.agw.genericmessagedialog as GMD
from main import settings

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necessário para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )

import browser, detail, noteBook, manager
########################################################################

class BarraControles( noteBook.NoteBookImage ):
	""" Cria uma barra de ferramenta que fornece interação ao usuário,
	seja vendo um vídeo pelo player embutido ou usando o navegador para
	capturar a url, ou até apenas modificando o comportamento do grupo de 
	conexões criadas """
	def __init__(self, parent, id):
		noteBook.NoteBookImage.__init__(self, parent)
		self.mainWin = parent

		attrs = [
			(os.path.join(settings.IMAGES_DIR, "apps-display-icon.png"), 
			 _("Assistir"), self.createPlayerWin, self.OnContextMenu),

			(os.path.join(settings.IMAGES_DIR, "settings-tool.png"), 
			 _(u"Configuração"), self.createConnetionWin, None),

			(os.path.join(settings.IMAGES_DIR, "search-computer.png"), 
			 _("Pesquisar"), self.createBrowserWin, None),
		]
		# carrega as páginas
		for imgPath, txt, winBuilder, callback in attrs:
			newpage = self.createPage(imgPath, txt, txt, callback=callback)
			self.addPage(newpage, winBuilder(newpage))
			
		self.setWidget(self.mainWin, "FullScreen", _("Tela cheia"))
		
	def __del__(self):
		del self.mainWin
		
	def OnHide(self, isHidden): # método chamado pelo botão hide
		mainSizer = self.mainWin.GetSizer()
		if isHidden: mainSizer.Hide(0)
		elif not isHidden: mainSizer.Show(0)
		self.mainWin.Layout()
	
	def OnContextMenu(self, event):
		evtMenuOn = event.GetEventObject()
		
		if not hasattr(self, "popupID1"):
			self.popupID1 = 1000
			self.popupID2 = self.popupID1+1
			self.popupID3 = self.popupID2+1
		
		# make a menu
		self.playerMenu = wx.Menu()
		# item.SetBitmap(bmp)
		self.playerMenu.AppendRadioItem(self.popupID1, "jwPlayer")
		self.playerMenu.AppendRadioItem(self.popupID2, "flowPlayer")
		
		self.Bind(wx.EVT_MENU, self.loadEmbedPlayer, id=self.popupID1)
		self.Bind(wx.EVT_MENU, self.loadEmbedPlayer, id=self.popupID2)
		
		checkopts = {"jwPlayer": self.popupID1, "flowPlayer": self.popupID2}
		moduleName = self.mainWin.configs["PlayerWin"]["moduleName"]
		self.playerMenu.Check(checkopts[ moduleName ], True)
		
		self.playerMenu.AppendSeparator()
		
		# sub-menu skins
		self.menuSkins = wx.Menu()
		self.playerMenu.AppendMenu(self.popupID3, _("Mudar skin"), self.menuSkins)
		
		idIntValue = self.popupID3+1
		checked = idIntValue # usado como item padrão
		skinName = self.mainWin.configs["PlayerWin"]["skinName"]
		
		for index, skin in enumerate(self.mainWin.playerWin.getSkinsNames()):
			menuItemId = idIntValue + index
			self.menuSkins.AppendRadioItem(menuItemId, skin)
			self.Bind(wx.EVT_MENU, self.skinChangeHandle, id=menuItemId)
			if skinName == skin: checked = menuItemId
			
		# marca a última skin usada
		self.menuSkins.Check(checked, True)
		
		# Popup the menu.  If an item is selected then its handler
		# will be called before PopupMenu returns.
		evtMenuOn.PopupMenu( self.playerMenu )
		self.playerMenu.Destroy()
		
	def skinChangeHandle(self, evt):
		""" adiciona a skin selecionada para player embutido """
		skinName = self.menuSkins.GetLabelText(evt.GetId())
		
		self.mainWin.configs["PlayerWin"]["skinName"] = skinName
		self.mainWin.playerWin["skinName"] = skinName
		
		# atualiza o player(automaticamente),quando ativado no menu.
		if self.mainWin.cfg_menu.as_bool('playerEmbutido'):
			self.mainWin.recarreguePlayer()
	
	def loadEmbedPlayer(self, evt):
		""" carrega o player embutido escolhido no menu """
		skinName = self.playerMenu.GetLabelText(evt.GetId())
		self.mainWin.configs["PlayerWin"]["moduleName"] = skinName
		playerPanel = self.mainWin.playerWin.GetParent()
		playerPanel.Freeze()
		
		panelSizer = playerPanel.GetSizer()
		panelSizer.Remove( self.mainWin.playerWin )
		# removendo o player atual
		self.mainWin.playerWin.Destroy()
		
		# criando um novo player e atribuindo ao panel da pagina
		newPlayer = self.createPlayerWin( playerPanel )
		panelSizer.Add(newPlayer, 1, wx.EXPAND)
		playerPanel.Layout()
		playerPanel.Thaw()
		
	def createPlayerWin(self, parent):
		""" carrega o flash player """
		configs = getattr(self.mainWin,"configs",None)
		
		if configs:
			# seção de dados muito importante
			if not configs.has_key("PlayerWin"):
				configs["PlayerWin"]={}
			# as configurações sempre devem existir
			pwconfig = configs["PlayerWin"]
			pwconfig["moduleName"] = pwconfig.get("moduleName","flowPlayer")
			pwconfig["skinName"] = pwconfig.get("skinName","")
			
			# importa o player escolhido pelo usuário
			player = __import__(pwconfig["moduleName"], globals(), locals())
			
			self.mainWin.playerWin = player = player.Player( parent )
			player["skinName"] = pwconfig["skinName"]
			player["portNumber"] = manager.Server.PORT
			player["hostName"] = manager.Server.HOST
		else:
			# evita que o programa trave caso algo dê errado
			self.mainWin.playerWin = wx.Panel()
		return self.mainWin.playerWin
	
	def createBrowserWin(self, parent):
		iewindow = browser.Browser(parent, self.mainWin)
		self.mainWin.iewindow = iewindow
		return iewindow

	def createConnetionWin(self, parent):
		topPanel = wx.Panel(parent, -1)
		
		# Painel de detalhes das conexões
		detailPainel = self.detailPanelHandle( topPanel )

		# Painel de controle das conexões
		connectionPainel = self.connectionPainelHandle( topPanel )
		
		mainSizer = wx.BoxSizer( wx.VERTICAL )
		mainSizer.Add(detailPainel, 2, wx.EXPAND|wx.ALL, 10)
		mainSizer.Add(connectionPainel, 1, wx.EXPAND|wx.LEFT|wx.BOTTOM, 10)
		
		topPanel.SetSizer( mainSizer )
		topPanel.SetAutoLayout(1)
		return topPanel
	
	def detailPanelHandle(self, mainPainel):
		""" cria o painel de detalhes das conexões """
		panel = wx.Panel( mainPainel, -1)

		listCtrl = detail.DetailControl( panel)
		self.mainWin.detailControl = listCtrl
		
		sizer = wx.BoxSizer( wx.VERTICAL)
		sizer.Add( listCtrl, 1, wx.EXPAND)

		panel.SetSizer( sizer )
		panel.SetAutoLayout(1)
		return panel
	
	def connectionPainelHandle(self, mainPainel):
		""" cria o painel de controle das conexões """
		notebook = wx.Notebook(mainPainel, -1, style=wx.BK_DEFAULT)
		
		# conexões
		panel = self.connectionHandle( notebook )
		notebook.AddPage(panel, _(u"Conexões"))

		# videos
		panel = self.videoHandle( notebook )
		notebook.AddPage(panel, _("Videos"))

		# arquivos
		panel = self.fileHandle( notebook )
		notebook.AddPage(panel, _("Arquivos"))
		return notebook
	
	def connectionHandle(self, parent):
		panel = wx.Panel( parent, -1)
		panel.SetBackgroundColour(wx.WHITE)
		panelSizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer( panelSizer)
		panel.SetAutoLayout(1)
		# ------------------------------------------------------------
		connectionsHandle = self.mainWin.controleConexoes

		conteiner = wx.StaticBox(panel, -1, "")
		staticBoxSizer = wx.StaticBoxSizer(conteiner, wx.HORIZONTAL)
		panelSizer.Add(staticBoxSizer, 1, wx.EXPAND|wx.ALL, 10)
		# ------------------------------------------------------------

		# agrupa por conjunto de FlexGridSizer
		gradeConjunto = wx.GridSizer(1, 2, 0, 50)
		staticBoxSizer.Add(gradeConjunto, 0, wx.EXPAND)

		# primeiro conjunto de controles
		groupFlexSizer_1 = wx.FlexGridSizer(3, 2, 10, 5)
		gradeConjunto.Add( groupFlexSizer_1, 1, wx.EXPAND)
		# ------------------------------------------------------------

		# controla o número de conexões ativas
		textInfo = wx.StaticText(conteiner, -1, _(u"Conexões ativas: "))
		self.nConnectionControl = wx.SpinCtrl(conteiner, -1, "2")
		helpText = _(u"Inicia novas conexões ou pára conexões existentes.")
		self.nConnectionControl.SetToolTip(wx.ToolTip( helpText ))
		self.nConnectionControl.SetRange(1, 30)

		# event handler
		self.nConnectionControl.Bind(wx.EVT_TEXT_ENTER, connectionsHandle)
		self.nConnectionControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.nConnectionControl)

		groupFlexSizer_1.AddMany([(textInfo, 1, wx.EXPAND),
				                  (self.nConnectionControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------

		# Controla o limite de velocidade de sub-conexões
		textInfo = wx.StaticText(conteiner, -1, _("Limite de velocidade: "))
		self.rateLimitControl = wx.SpinCtrl(conteiner, -1, "35840")

		# event handler
		self.rateLimitControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.rateLimitControl)

		helpText = _(u"Limita o download de sub-conexões criadas para o número de bytes")
		self.rateLimitControl.SetToolTip(wx.ToolTip( helpText ))
		self.rateLimitControl.SetRange(0, sys.maxint)

		groupFlexSizer_1.AddMany([(textInfo, 1, wx.EXPAND),
				                  (self.rateLimitControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------

		# Controla o limite de velocidade de sub-conexões
		textInfo = wx.StaticText(conteiner, -1, _("Tempo de espera: "))
		self.timeoutControl = wx.SpinCtrl(conteiner, -1, "25")

		# event handler
		self.timeoutControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.timeoutControl)

		text = u"".join([
		    _(u"Tempo máximo de espera por uma resposta\n"),
			_(u"do servidor de stream(timeout em segundos)")
		])
		self.timeoutControl.SetToolTip(wx.ToolTip( text ))
		self.timeoutControl.SetRange(5, 60*5)
		
		groupFlexSizer_1.AddMany([(textInfo, 1, wx.EXPAND),
				                  (self.timeoutControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------

		# *** segundo conjunto de controles
		groupFlexSizer_2 = wx.FlexGridSizer(3, 2, 10, 5)
		gradeConjunto.Add( groupFlexSizer_2, 1, wx.EXPAND)

		# *** Controla o número de reconexões
		info = wx.StaticText(conteiner, -1, _(u"Número de reconexões: "))
		self.reconexoesControl = wx.SpinCtrl(conteiner, -1, "3")

		# event handler
		self.reconexoesControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.reconexoesControl)
		text = u"".join([
		    _(u"Define o número de tentativas, \n"),
			_("antes de dar por encerrado o uso do ip atual.")
		])
		self.reconexoesControl.SetToolTip(wx.ToolTip( text ))
		self.reconexoesControl.SetRange(1,100)

		groupFlexSizer_2.AddMany([(info, 1, wx.EXPAND),
				                  (self.reconexoesControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------
		
		# *** Controla o tempo de espera, entre as reconexões
		info = wx.StaticText(conteiner, -1, _(u"Espera entre reconexões: "))
		self.waitTimeControl = wx.SpinCtrl(conteiner, -1, "2")
		
		# event handler
		self.waitTimeControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.waitTimeControl)
		helpText = _(u"Tempo de espera entre as tentativas de conexão(segundos).")
		self.waitTimeControl.SetToolTip(wx.ToolTip( helpText ))
		self.waitTimeControl.SetRange(1,60*5)
		
		groupFlexSizer_2.AddMany([(info, 1, wx.EXPAND),
				                  (self.waitTimeControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------
		
		# controla o número de conexões ativas
		self.changeTypeControl = wx.CheckBox(
		    conteiner, -1, _(u"Habilitar mudança de tipo"), style=wx.ALIGN_LEFT
		)
		text = u"".join([
		    _(u"Mudar o tipo de conexão.\n"),
			_(u"Muda da conexão padrão para um servidor proxie ou vice-versa.")
		])
		self.changeTypeControl.SetToolTip(wx.ToolTip( text ))
		
		# event handler
		self.changeTypeControl.Bind(wx.EVT_CHECKBOX, self.updateSettings)
		self.Bind(wx.EVT_CHECKBOX, connectionsHandle, self.changeTypeControl)
		
		groupFlexSizer_2.Add(self.changeTypeControl, 1, wx.EXPAND)
		# ------------------------------------------------------------
		
		# controla o número de conexões ativas
		self.proxyDisable = wx.CheckBox(
		    conteiner, -1, _(u"Desabilitar proxy"), style=wx.ALIGN_LEFT
		)
		text = _(u"Desabilita o uso de conexões com servidores proxies(não recomendado).")
		self.proxyDisable.SetToolTip(wx.ToolTip( text ))
		
		# event handler
		self.proxyDisable.Bind(wx.EVT_CHECKBOX, self.updateSettings)
		self.Bind(wx.EVT_CHECKBOX, connectionsHandle, self.proxyDisable)
		
		groupFlexSizer_2.Add(self.proxyDisable, 1, wx.EXPAND)
		
		return panel

	def videoHandle(self, parent):
		panel = wx.Panel( parent, -1)
		panel.SetBackgroundColour(wx.WHITE)
		panelSizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer( panelSizer)
		panel.SetAutoLayout(1)

		conteiner = wx.StaticBox(panel, -1, "")
		staticBoxSizer = wx.StaticBoxSizer(conteiner, wx.VERTICAL)
		panelSizer.Add(staticBoxSizer, 0, wx.EXPAND|wx.ALL, 10)
		sizerParControls = wx.FlexGridSizer(1, 2, 5, 5)

		# Controle para escolha da qualidade do vídeo baixado
		textInfo = wx.StaticText(conteiner, -1, _(u"Qualidade do vídeo: "))
		self.videoQualityControl = wx.Choice(conteiner, -1, choices = [_("Baixa"), _(u"Média"), _("Alta")])
		helpText = [
		    _(u"Qualidade do vídeo que será baixado e reproduzido.\n"),
			_(u"Note que nem todos servidores suportam essa opção.")
		]
		self.videoQualityControl.SetToolTip(wx.ToolTip( "".join(helpText) ))
		self.Bind(wx.EVT_CHOICE, self.updateSettings, self.videoQualityControl)
		self.videoQualityControl.SetSelection(0)

		sizerParControls.AddMany([(textInfo, 1, wx.EXPAND|wx.TOP, 10),
				                  (self.videoQualityControl, 1, wx.EXPAND|wx.ALIGN_LEFT|wx.TOP, 10)])
		# GRIDSIZER ADD
		staticBoxSizer.Add( sizerParControls )
		return panel

	def fileHandle(self, parent):
		panel = wx.Panel( parent, -1)
		panel.SetBackgroundColour(wx.WHITE)
		panelSizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer( panelSizer)
		panel.SetAutoLayout(1)

		conteiner = wx.StaticBox(panel, -1, "")
		staticBoxSizer = wx.StaticBoxSizer(conteiner, wx.VERTICAL)
		panelSizer.Add(staticBoxSizer, 1, wx.EXPAND|wx.ALL, 10)

		gradeConjunto = wx.GridSizer(1, 1, 0,0)
		staticBoxSizer.Add(gradeConjunto, 0, wx.EXPAND)

		groupFlexSizer_1 = wx.FlexGridSizer(3, 1, 15, 0)
		gradeConjunto.Add( groupFlexSizer_1, 0, wx.EXPAND)

		# Controla o uso de arquivos temporários
		self.tempFileControl = wx.CheckBox(conteiner, -1, _(u"Use arquivo temporário"), style=wx.ALIGN_LEFT)
		helpText = _(u"Indica se o arquivo de vídeo será removido, \napós parar o download.")
		self.tempFileControl.SetToolTip(wx.ToolTip( helpText ))
		self.Bind(wx.EVT_CHECKBOX, self.updateSettings, self.tempFileControl)

		groupFlexSizer_1.Add(self.tempFileControl, 0, wx.EXPAND)

		# Opções para o arquivo temporário
		self.tempFileOptControl = wx.Choice(conteiner, -1, choices = [_("Apenas remova"), _("Pergunte o que fazer")])
		helpText = _(u"O que fazer, ao usar um arquivo temporário ?")
		self.tempFileOptControl.SetToolTip(wx.ToolTip( helpText ))		
		self.Bind(wx.EVT_CHOICE, self.updateSettings, self.tempFileOptControl)
		self.tempFileOptControl.Enable(False); self.tempFileOptControl.SetSelection(0)

		groupFlexSizer_1.Add(self.tempFileOptControl, 0, wx.EXPAND|wx.LEFT, 10)

		# Controla o número de divisões do arquivo de vídeo
		textInfo = wx.StaticText(conteiner, -1, _(u"Número de divisões: "))
		self.numDivStreamControl = wx.SpinCtrl(conteiner, -1, "2")
		self.Bind(wx.EVT_SPINCTRL, self.updateSettings, self.numDivStreamControl)
		helpText = _(u"Indica o número de partes, que a stream\n de vídeo será divida inicialmente")
		self.numDivStreamControl.SetToolTip(wx.ToolTip( helpText ))
		self.numDivStreamControl.SetRange(2, 25)

		hSizer = wx.BoxSizer(wx.HORIZONTAL)
		hSizer.Add(textInfo, 0, wx.EXPAND)
		hSizer.Add(self.numDivStreamControl, 0, wx.ALIGN_TOP)

		groupFlexSizer_1.Add(hSizer, 0, wx.EXPAND|wx.LEFT, 5)

		return panel

	def questineUsuario(self):
		if self.tempFileOptControl.Enabled and self.tempFileOptControl.GetSelection() == 1:
			msg = _(u"Gostou do vídeo ? Deseja guardá-lo para revê-lo mais tarde ?")
			gm_dlg = GMD.GenericMessageDialog(self, msg, _("O que fazer ?"), wx.ICON_QUESTION|wx.YES_NO)
			if gm_dlg.ShowModal() == wx.ID_YES: self.setTempFileOpt()
			gm_dlg.Destroy()
		# reativando os controles para a tranferência de um novo arquivo.
		self.enableCtrs()
		
	def enableCtrs(self, enable=True):
		# reativando os controles desativadas ao iniciar a transferência.
		for method in [
		    self.tempFileControl, self.videoQualityControl, 
		    self.numDivStreamControl ]:
			method.Enable( enable )
	
	@manager.FM_runLocked()
	def setTempFileOpt(self): ## _("Arquivo corrompido!")
		assert self.mainWin.manage is not None, u"'manage' ainda não iniciado!"
		
		if self.tempFileOptControl.GetSelection() == 1: # index=1: "pergunte o que fazer"
			progressDlg = wx.ProgressDialog(_(u"Copiando arquivo..."), "",
			                                maximum = 100, 
			                                parent = self,
			                                style = 0 
			                                | wx.PD_CAN_ABORT
			                                | wx.PD_ESTIMATED_TIME 
			                                | wx.PD_REMAINING_TIME 
			                                | wx.PD_APP_MODAL)
			for copy in self.mainWin.manage.recoverTempFile():
				if copy.inProgress and not copy.error:
					prog_info = _("Copiado %.2f%% de 100.00%%")% float(copy.progress)
					
					if not copy.sucess:
						keepGoing, skip = progressDlg.Update(copy.progress, prog_info)
						copy.cancel = not keepGoing # permite cancelar a cópia.
					else:
						progressDlg.SetTitle(_(u"Tudo como esperado."))
						progressDlg.Update(copy.progress, prog_info+"\n"+copy.get_msg())
						
				elif copy.error == True:
					progressDlg.SetTitle( _(u"Não foi possível..."))
					progressDlg.Update(100, copy.get_msg())
					
			progressDlg.Destroy()

	def updateSettings(self, evt=None):
		# setting: controles
		cfg_controles = self.mainWin.configs["Controles"]

		# setting: qualidade do vídeo
		selection = self.videoQualityControl.GetSelection()
		cfg_controles["videoQualityControlValue"] = selection

		# setting: número de conexões ativas
		value = self.nConnectionControl.GetValue()
		cfg_controles["numConexoesAtivas"] = value

		# setting: controle de arquivos temporáros
		value = self.tempFileControl.GetValue()
		cfg_controles["tempFileControlValue"] = value
		self.tempFileOptControl.Enable( value )

		# setting: opções de arquivos temporários
		selection = self.tempFileOptControl.GetSelection()
		cfg_controles["tempFileOptControlValue"] = selection

		# setting: número de divisóes inicias do arquivo
		value = self.numDivStreamControl.GetValue()
		cfg_controles["numDivStreamControlValue"] = value

		# setting: taxa limite de download para sub-conexões
		value = self.rateLimitControl.GetValue()
		cfg_controles["rateLimitControlValue"] = value

		value = self.timeoutControl.GetValue()
		cfg_controles["timeoutControlValue"] = value

		value = self.reconexoesControl.GetValue()
		cfg_controles["reconexoesControlValue"] = value
		
		value = self.waitTimeControl.GetValue()
		cfg_controles["waitTimeControlValue"] = value
		
		value = self.changeTypeControl.GetValue()
		cfg_controles["changeTypeControlValue"] = value
		
		value = self.proxyDisable.GetValue()
		cfg_controles["proxyDisable"] = value
		evt.Skip()

########################################################################
if __name__ == "__main__":
	# muda para o diretório pai por depender dos recursos dele.
	os.chdir( pardir )
	
	# instala as traduções.
	manager.installTranslation() 
	
	def metodoTeste(self, *args):
		print "Método teste chamado[controleConexoes]: %s"%str(args)

	app = wx.App(False)
	try:
		frame = wx.Frame(None, -1, "Fram", size = (800, 500))
		frame.controleConexoes = metodoTeste

		sizer = wx.BoxSizer(wx.VERTICAL)
		frame.SetSizer( sizer ); frame.SetAutoLayout(True)

		button = wx.Button(frame,-1, ".....")
		sizer.Add(button, 0, wx.EXPAND)

		control = BarraControles( frame, -1)
		sizer.Add(control, 1, wx.EXPAND)
	except Exception, err:
		print err

	frame.Show()
	app.MainLoop()