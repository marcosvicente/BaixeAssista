# -*- coding: ISO-8859-1 -*-

import os
import wx
import sys
import math
import wx.lib.agw.genericmessagedialog as GMD
from main import settings

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necess�rio para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )

import browser, jwPlayer, detail, noteBook, manager
########################################################################

class BarraControles( noteBook.NoteBookImage ):
	""" Cria uma barra de ferramenta que fornece intera��o ao usu�rio,
	seja vendo um v�deo pelo player embutido ou usando o navegador para
	capturar a url, ou at� apenas modificando o comportamento do grupo de 
	conex�es criadas """
	def __init__(self, parent, id):
		noteBook.NoteBookImage.__init__(self, parent)
		self.mainWin = parent

		attrs = [
			(os.path.join(settings.APPDIR,"imagens", "apps-display-icon.png"), 
			 _("Assistir"), self.createPlayerWin),

			(os.path.join(settings.APPDIR,"imagens", "settings-tool.png"), 
			 _(u"Configura��o"), self.createConnetionWin),

			(os.path.join(settings.APPDIR,"imagens", "search-computer.png"), 
			 _("Pesquisar"), self.createBrowserWin),
		]
		# carrega as p�ginas
		for imgpath, txt, metodo in attrs:
			panel = self.addPage(imgpath, txt, txt)
			# "metodo" chama a contru��o de um tipo de controle.
			panel.GetSizer().Add(metodo(panel), 1, wx.EXPAND)
			panel.GetSizer().Layout()
			
		self.setWidget(self.mainWin, "FullScreen", _("Tela cheia"))
		
	def __del__(self):
		del self.mainWin
		
	def OnHide(self, isHidden): # m�todo chamado pelo bot�o hide
		mainSizer = self.mainWin.GetSizer()
		if isHidden: mainSizer.Hide(0)
		elif not isHidden: mainSizer.Show(0)
		
		self.mainWin.Layout()
		
	def createPlayerWin(self, parent):
		""" carrega o flash player """
		skin = ""
		if hasattr(self.mainWin, "configs"):
			config = self.mainWin.configs.get("PlayerWin",{})
			skin = config.get("skinName", "")

		playerWin = jwPlayer.JWPlayer(parent, skinName=skin)
		self.mainWin.playerWin = playerWin
		return playerWin
	
	def createBrowserWin(self, parent):
		iewindow = browser.Browser(parent, self.mainWin)
		self.mainWin.iewindow = iewindow
		return iewindow

	def createConnetionWin(self, parent):
		topPanel = wx.Panel(parent, -1)
		
		# Painel de detalhes das conex�es
		detailPainel = self.detailPanelHandle( topPanel )

		# Painel de controle das conex�es
		connectionPainel = self.connectionPainelHandle( topPanel )
		
		mainSizer = wx.BoxSizer( wx.VERTICAL )
		mainSizer.Add(detailPainel, 2, wx.EXPAND|wx.ALL, 10)
		mainSizer.Add(connectionPainel, 1, wx.EXPAND|wx.LEFT|wx.BOTTOM, 10)
		
		topPanel.SetSizer( mainSizer )
		topPanel.SetAutoLayout(1)
		return topPanel
	
	def detailPanelHandle(self, mainPainel):
		""" cria o painel de detalhes das conex�es """
		panel = wx.Panel( mainPainel, -1)

		listCtrl = detail.DetailControl( panel)
		self.mainWin.detailControl = listCtrl
		
		sizer = wx.BoxSizer( wx.VERTICAL)
		sizer.Add( listCtrl, 1, wx.EXPAND)

		panel.SetSizer( sizer )
		panel.SetAutoLayout(1)
		return panel
	
	def connectionPainelHandle(self, mainPainel):
		""" cria o painel de controle das conex�es """
		notebook = wx.Notebook(mainPainel, -1, style=wx.BK_DEFAULT)
		
		# conex�es
		panel = self.connectionHandle( notebook )
		notebook.AddPage(panel, _(u"Conex�es"))

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

		# controla o n�mero de conex�es ativas
		textInfo = wx.StaticText(conteiner, -1, _(u"Conex�es ativas: "))
		self.nConnectionControl = wx.SpinCtrl(conteiner, -1, "2")
		helpText = _(u"Inicia novas conex�es ou p�ra conex�es existentes.")
		self.nConnectionControl.SetToolTip(wx.ToolTip( helpText ))
		self.nConnectionControl.SetRange(1, 30)

		# event handler
		self.nConnectionControl.Bind(wx.EVT_TEXT_ENTER, connectionsHandle)
		self.nConnectionControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.nConnectionControl)

		groupFlexSizer_1.AddMany([(textInfo, 1, wx.EXPAND),
				                  (self.nConnectionControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------

		# Controla o limite de velocidade de sub-conex�es
		textInfo = wx.StaticText(conteiner, -1, _("Limite de velocidade: "))
		self.rateLimitControl = wx.SpinCtrl(conteiner, -1, "35840")

		# event handler
		self.rateLimitControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.rateLimitControl)

		helpText = _(u"Limita o download de sub-conex�es criadas para o n�mero de bytes")
		self.rateLimitControl.SetToolTip(wx.ToolTip( helpText ))
		self.rateLimitControl.SetRange(0, sys.maxint)

		groupFlexSizer_1.AddMany([(textInfo, 1, wx.EXPAND),
				                  (self.rateLimitControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------

		# Controla o limite de velocidade de sub-conex�es
		textInfo = wx.StaticText(conteiner, -1, _("Tempo de espera: "))
		self.timeoutControl = wx.SpinCtrl(conteiner, -1, "25")

		# event handler
		self.timeoutControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.timeoutControl)

		text = u"".join([
		    _(u"Tempo m�ximo de espera por uma resposta\n"),
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

		# *** Controla o n�mero de reconex�es
		info = wx.StaticText(conteiner, -1, _(u"N�mero de reconex�es: "))
		self.reconexoesControl = wx.SpinCtrl(conteiner, -1, "3")

		# event handler
		self.reconexoesControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.reconexoesControl)
		text = u"".join([
		    _(u"Define o n�mero de tentativas, \n"),
			_("antes de dar por encerrado o uso do ip atual.")
		])
		self.reconexoesControl.SetToolTip(wx.ToolTip( text ))
		self.reconexoesControl.SetRange(1,100)

		groupFlexSizer_2.AddMany([(info, 1, wx.EXPAND),
				                  (self.reconexoesControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------
		
		# *** Controla o tempo de espera, entre as reconex�es
		info = wx.StaticText(conteiner, -1, _(u"Espera entre reconex�es: "))
		self.waitTimeControl = wx.SpinCtrl(conteiner, -1, "2")
		
		# event handler
		self.waitTimeControl.Bind(wx.EVT_SPINCTRL, self.updateSettings)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.waitTimeControl)
		helpText = _(u"Tempo de espera entre as tentativas de conex�o(segundos).")
		self.waitTimeControl.SetToolTip(wx.ToolTip( helpText ))
		self.waitTimeControl.SetRange(1,60*5)
		
		groupFlexSizer_2.AddMany([(info, 1, wx.EXPAND),
				                  (self.waitTimeControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------
		
		# controla o n�mero de conex�es ativas
		self.changeTypeControl = wx.CheckBox(
		    conteiner, -1, _(u"Habilitar mudan�a de tipo"), style=wx.ALIGN_LEFT
		)
		text = u"".join([
		    _(u"Mudar o tipo de conex�o.\n"),
			_(u"Muda da conex�o padr�o para um servidor proxie ou vice-versa.")
		])
		self.changeTypeControl.SetToolTip(wx.ToolTip( text ))
		
		# event handler
		self.changeTypeControl.Bind(wx.EVT_CHECKBOX, self.updateSettings)
		self.Bind(wx.EVT_CHECKBOX, connectionsHandle, self.changeTypeControl)
		
		groupFlexSizer_2.Add(self.changeTypeControl, 1, wx.EXPAND)
		# ------------------------------------------------------------
		
		# controla o n�mero de conex�es ativas
		self.proxyDisable = wx.CheckBox(
		    conteiner, -1, _(u"Desabilitar proxy"), style=wx.ALIGN_LEFT
		)
		text = _(u"Desabilita o uso de conex�es com servidores proxies(n�o recomendado).")
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

		# Controle para escolha da qualidade do v�deo baixado
		textInfo = wx.StaticText(conteiner, -1, _(u"Qualidade do v�deo: "))
		self.videoQualityControl = wx.Choice(conteiner, -1, choices = [_("Baixa"), _(u"M�dia"), _("Alta")])
		helpText = [
		    _(u"Qualidade do v�deo que ser� baixado e reproduzido.\n"),
			_(u"Note que nem todos servidores suportam essa op��o.")
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

		# Controla o uso de arquivos tempor�rios
		self.tempFileControl = wx.CheckBox(conteiner, -1, _(u"Use arquivo tempor�rio"), style=wx.ALIGN_LEFT)
		helpText = _(u"Indica se o arquivo de v�deo ser� removido, \nap�s parar o download.")
		self.tempFileControl.SetToolTip(wx.ToolTip( helpText ))
		self.Bind(wx.EVT_CHECKBOX, self.updateSettings, self.tempFileControl)

		groupFlexSizer_1.Add(self.tempFileControl, 0, wx.EXPAND)

		# Op��es para o arquivo tempor�rio
		self.tempFileOptControl = wx.Choice(conteiner, -1, choices = [_("Apenas remova"), _("Pergunte o que fazer")])
		helpText = _(u"O que fazer, ao usar um arquivo tempor�rio ?")
		self.tempFileOptControl.SetToolTip(wx.ToolTip( helpText ))		
		self.Bind(wx.EVT_CHOICE, self.updateSettings, self.tempFileOptControl)
		self.tempFileOptControl.Enable(False); self.tempFileOptControl.SetSelection(0)

		groupFlexSizer_1.Add(self.tempFileOptControl, 0, wx.EXPAND|wx.LEFT, 10)

		# Controla o n�mero de divis�es do arquivo de v�deo
		textInfo = wx.StaticText(conteiner, -1, _(u"N�mero de divis�es: "))
		self.numDivStreamControl = wx.SpinCtrl(conteiner, -1, "2")
		self.Bind(wx.EVT_SPINCTRL, self.updateSettings, self.numDivStreamControl)
		helpText = _(u"Indica o n�mero de partes, que a stream\n de v�deo ser� divida inicialmente")
		self.numDivStreamControl.SetToolTip(wx.ToolTip( helpText ))
		self.numDivStreamControl.SetRange(2, 25)

		hSizer = wx.BoxSizer(wx.HORIZONTAL)
		hSizer.Add(textInfo, 0, wx.EXPAND)
		hSizer.Add(self.numDivStreamControl, 0, wx.ALIGN_TOP)

		groupFlexSizer_1.Add(hSizer, 0, wx.EXPAND|wx.LEFT, 5)

		return panel

	def questineUsuario(self):
		if self.tempFileOptControl.Enabled and self.tempFileOptControl.GetSelection() == 1:
			msg = _(u"Gostou do v�deo ? Deseja guard�-lo para rev�-lo mais tarde ?")
			confirmDialog = GMD.GenericMessageDialog(self, msg, _("O que fazer ?"), wx.ICON_QUESTION|wx.YES_NO)
			if confirmDialog.ShowModal() == wx.ID_YES: self.setTempFileOpt()
			confirmDialog.Destroy()
			
		# reativando o controle(note que ele foi 
		# desativado no come�o da transfer�ncia)
		self.tempFileControl.Enable(True)
		self.videoQualityControl.Enable(True)
		self.numDivStreamControl.Enable(True)

	def setTempFileOpt(self):
		manage = self.mainWin.manage
		assert manage is not None, u"'manage' ainda n�o iniciado!"
		
		if self.tempFileOptControl.GetSelection() == 1: # index=1: "pergunte o que fazer"
			sucess, message = manage.recoverTempFile()
			
			if sucess is True:
				msg = _("O arquivo foi recuperado com sucesso!")
				dlg = GMD.GenericMessageDialog(self, message, _("Tudo como esperado."), wx.ICON_INFORMATION|wx.OK)
				dlg.ShowModal(); dlg.Destroy()
				
			elif sucess is False:
				dlg = GMD.GenericMessageDialog(self, message, _(u"N�o foi poss�vel..."), wx.ICON_ERROR|wx.OK)
				dlg.ShowModal(); dlg.Destroy()
				
			elif sucess is None:
				msg = u"".join([
				    _(u"O arquivo de v�deo est� corrompido!"),
				    _(u"\nIsso por causa da \"seekbar\".")])
				dlg = GMD.GenericMessageDialog(self, msg, _("Arquivo corrompido!"), wx.ICON_ERROR|wx.OK)
				dlg.ShowModal(); dlg.Destroy()
			
	def updateSettings(self, evt=None):
		# setting: controles
		cfg_controles = self.mainWin.configs["Controles"]

		# setting: qualidade do v�deo
		selection = self.videoQualityControl.GetSelection()
		cfg_controles["videoQualityControlValue"] = selection

		# setting: n�mero de conex�es ativas
		value = self.nConnectionControl.GetValue()
		cfg_controles["numConexoesAtivas"] = value

		# setting: controle de arquivos tempor�ros
		value = self.tempFileControl.GetValue()
		cfg_controles["tempFileControlValue"] = value
		self.tempFileOptControl.Enable( value )

		# setting: op��es de arquivos tempor�rios
		selection = self.tempFileOptControl.GetSelection()
		cfg_controles["tempFileOptControlValue"] = selection

		# setting: n�mero de divis�es inicias do arquivo
		value = self.numDivStreamControl.GetValue()
		cfg_controles["numDivStreamControlValue"] = value

		# setting: taxa limite de download para sub-conex�es
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
	# muda para o diret�rio pai por depender dos recursos dele.
	os.chdir( pardir )
	
	# instala as tradu��es.
	manager.installTranslation() 
	
	def metodoTeste(self, *args):
		print "M�todo teste chamado[controleConexoes]: %s"%str(args)

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