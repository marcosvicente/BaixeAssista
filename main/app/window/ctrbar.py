# -*- coding: ISO-8859-1 -*-

import os
import wx
import sys
import math
import wx.lib.agw.genericmessagedialog as GMD
import wx.lib.agw.multidirdialog as MDD
from main import settings

# configurando o ambiente para a execu��o do script.
import main.environ
main.environ.setup((__name__ == "__main__"))

import detail, noteBook
from main.app import manager, browser
import wEmbed
########################################################################

class BarraControles( noteBook.NoteBookImage ):
	""" Cria uma barra de ferramenta que fornece intera��o ao usu�rio,
	seja vendo um v�deo pelo player embutido ou usando o navegador para
	capturar a url, ou at� apenas modificando o comportamento do grupo de 
	conex�es criadas """
	def __init__(self, parent, id):
		noteBook.NoteBookImage.__init__(self, parent)
		self.mainWin = parent
		
		newpage = self.createPage(
			os.path.join(settings.IMAGES_DIR, "apps-display-icon.png"),
			pageTootip = _("Assistir"), callback = self.OnContextMenu
			)
		self.addPage(newpage, self.createPlayerWin( newpage ))
		self.buttonDisplayPanel = newpage # referencia para 'panel' raiz
		
		attrs = [
			(os.path.join(settings.IMAGES_DIR, "settings-tool.png"), 
			 _(u"Configura��o"), self.createConnetionWin),
			
			(os.path.join(settings.IMAGES_DIR, "search-computer.png"), 
			 _("Pesquisar"), self.createBrowserWin),
		]
		# carrega as p�ginas
		for imgPath, txt, winBuilder in attrs:
			newpage = self.createPage(imgPath, "", txt)
			self.addPage(newpage, winBuilder(newpage))
			
		self.setWidget(self.mainWin, "FullScreen", _("Tela cheia"))
		
	def __del__(self):
		del self.mainWin
		
	def OnHide(self, isHidden): # m�todo chamado pelo bot�o hide
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
		
		wplayerSection = self.mainWin.configs["PlayerWin"]
		moduleName = wplayerSection["moduleName"]
		
		player_opts = (
			{"id": self.popupID1, "name": "JWPlayer"},
			{"id": self.popupID2, "name": "FlowPlayer"}
		)
		for opts in player_opts:
			self.playerMenu.AppendRadioItem(opts["id"], opts["name"])
			if opts["name"] == moduleName: # ultmo player escolhido
				self.playerMenu.Check(opts["id"],True)
			
		self.Bind(wx.EVT_MENU, self.updateEmbedPlayer, id=self.popupID1)
		self.Bind(wx.EVT_MENU, self.updateEmbedPlayer, id=self.popupID2)
		self.playerMenu.AppendSeparator()
		
		# sub-menu skins
		self.menuSkins = wx.Menu()
		self.playerMenu.AppendMenu(self.popupID3, _("Mudar skin"), self.menuSkins)
		
		skin_id = self.popupID3+1
		checked = skin_opt_id = skin_id # usado como item padr�o
		skinName = self.mainWin.configs["PlayerWin"][moduleName]["skinName"]
		
		for index, skin in enumerate(self.mainWin.playerWin.getSkinsNames()):
			skin_opt_id = skin_id + index
			self.menuSkins.AppendRadioItem(skin_opt_id, skin)
			self.Bind(wx.EVT_MENU, self.changeEmbedPlayerSkin, id=skin_opt_id)
			if skinName == skin: checked = skin_opt_id
			
		# marca a �ltima skin usada
		self.menuSkins.Check(checked, True)
		
		popup_id = skin_opt_id +index +1
		self.playerMenu.Append(popup_id, _("Abra em uma janela"))
		self.Bind(wx.EVT_MENU, self.popupEmbedPlayer, id=popup_id)
		
		popup_autohide_id = popup_id +1
		self.playerMenu.AppendCheckItem(popup_autohide_id, _("Oculte automaticamente"))
		self.Bind(wx.EVT_MENU, self.updateAutoHide, id=popup_autohide_id)
		self.playerMenu.Check(popup_autohide_id, wplayerSection.as_bool("autoHide"))
		# o menu interage diretamente com a janela, quando esta estiver ativada.
		self.playerMenu.Enable(popup_autohide_id, self.isModePopupWin)
		
		# Popup the menu.  If an item is selected then its handler
		# will be called before PopupMenu returns.
		evtMenuOn.PopupMenu( self.playerMenu )
		self.playerMenu.Destroy()
	
	def updateAutoHide(self, evt):
		checked = self.playerMenu.IsChecked( evt.GetId() )
		wplayerSection = self.mainWin.configs["PlayerWin"]
		wplayerSection["autoHide"] = checked
	
	@property
	def isPopupHidden(self):
		return self.mainWin.configs["PlayerWin"]["autoHide"]
	
	@property
	def isModePopupWin(self):
		return bool(getattr(self,"wplayer",None))
	
	@property
	def haveHideWin(self):
		return (self.isModePopupWin and
				self.isPopupHidden)
		
	def showEmbedPlayer(self, boolflag=True):
		""" mostra/oculta a janela do player, completamente de acordo com o 'flag'"""
		wplayer = self.mainWin.playerWin.GetParent()
		wplayer.Show( boolflag )
		
	def changeEmbedPlayerSkin(self, evt):
		""" adiciona a skin selecionada para player embutido """
		skinName = self.menuSkins.GetLabelText(evt.GetId())
		
		moduleName = self.mainWin.configs["PlayerWin"]["moduleName"]
		playerSection = self.mainWin.configs["PlayerWin"][moduleName]
		playerSection["skinName"] = skinName
		
		# Player params
		self.mainWin.playerWin["skinName"] = skinName
		
		# atualiza o player(automaticamente),quando ativado no menu.
		if self.mainWin.cfg_menu.as_bool("playerEmbutido"):
			self.mainWin.reloadPlayer()
			
	def updateEmbedPlayer(self, evt):
		""" carrega o player embutido escolhido no menu """
		module = self.playerMenu.GetLabelText(evt.GetId())
		
		playerSection = self.mainWin.configs["PlayerWin"]
		playerSection["moduleName"] = module
		
		self.loadEmbedPlayer(self.mainWin.playerWin.GetParent())
	
	def loadEmbedPlayer(self, newparent):
		""" carrega o player embutido escolhido no menu """
		oldparent = self.mainWin.playerWin.GetParent()
		oldparent.Freeze()
		
		sizer = oldparent.GetSizer()
		sizer.Remove( self.mainWin.playerWin )
		# removendo o player atual
		self.mainWin.playerWin.Destroy()
		
		newpsizer = newparent.GetSizer()
		newparent.Freeze()
		
		newplayer = self.createPlayerWin( newparent )
		newpsizer.Add(newplayer, 1, wx.EXPAND)
		
		newparent.Layout()
		newparent.Refresh()
		newparent.Thaw()
		
		oldparent.Layout()
		oldparent.Refresh()
		oldparent.Thaw()
		
	def restoreEmbedPlayer(self, evt):
		evtobj = evt.GetEventObject()
		
		# restaura para o painel padr�o(button page panel)
		self.loadEmbedPlayer( self.buttonDisplayPanel )
		
		wx.CallAfter( evtobj.Destroy)
		self.wplayer = None
		
	def popupEmbedPlayer(self, evt):
		if not getattr(self, "wplayer", None):
			self.wplayer = wEmbed.wEmbedPlayer( self.mainWin)
			self.wplayer.Bind(wx.EVT_CLOSE, self.restoreEmbedPlayer)
			self.wplayer.CenterOnParent(wx.BOTH)
			self.loadEmbedPlayer( self.wplayer )
			
	def createPlayerWin(self, parent):
		""" carrega o flash player """
		configs = getattr(self.mainWin,"configs",None)
		
		if configs:
			moduleName = str(self.mainWin.configs["PlayerWin"]["moduleName"])
			playerSection = self.mainWin.configs["PlayerWin"][moduleName]
			
			# importa o player escolhido pelo usu�rio
			swplayer = __import__("main.app.swfplayer", {}, {}, [moduleName])
			player = getattr(swplayer, moduleName)
			params = dict(
				autostart = self.mainWin.isLoading(),
				portNumber = manager.Server.PORT,
				hostName = manager.Server.HOST,
				skinName = playerSection["skinName"]
			)
			self.mainWin.playerWin = player.Player(parent, **params)
			playerSection["skinName"] = self.mainWin.playerWin["skinName"]
		else:
			# evita que o programa trave caso algo d� errado
			self.mainWin.playerWin = wx.Panel()
		return self.mainWin.playerWin
		
	def createBrowserWin(self, parent):
		self.mainWin.iewindow = browser.Browser(parent, self.mainWin)
		return self.mainWin.iewindow

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
		ctrStaticInfo = wx.StaticText(conteiner, -1, _(u"Conex�es ativas: "))
		self.nConnectionControl = wx.SpinCtrl(conteiner, -1, "2")
		help_text = _(u"Inicia novas conex�es ou p�ra conex�es existentes.")
		self.nConnectionControl.SetToolTip(wx.ToolTip( help_text ))
		self.nConnectionControl.SetRange(1, 30)

		# event handler
		self.nConnectionControl.Bind(wx.EVT_TEXT_ENTER, connectionsHandle)
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.nConnectionControl)

		groupFlexSizer_1.AddMany([(ctrStaticInfo, 1, wx.EXPAND),
				                  (self.nConnectionControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------

		# Controla o limite de velocidade de sub-conex�es
		ctrStaticInfo = wx.StaticText(conteiner, -1, _("Limite de velocidade: "))
		self.rateLimitControl = wx.SpinCtrl(conteiner, -1, "35840")
		
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.rateLimitControl)

		help_text = _(u"Limita o download de sub-conex�es criadas para o n�mero de bytes")
		self.rateLimitControl.SetToolTip(wx.ToolTip( help_text ))
		self.rateLimitControl.SetRange(0, sys.maxint)

		groupFlexSizer_1.AddMany([(ctrStaticInfo, 1, wx.EXPAND),
				                  (self.rateLimitControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------

		# Controla o limite de velocidade de sub-conex�es
		ctrStaticInfo = wx.StaticText(conteiner, -1, _("Tempo de espera: "))
		self.timeoutControl = wx.SpinCtrl(conteiner, -1, "25")
		
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.timeoutControl)

		help_text = u"".join([
		    _(u"Tempo m�ximo de espera por uma resposta\n"),
			_(u"do servidor de stream(timeout em segundos)")
		])
		self.timeoutControl.SetToolTip(wx.ToolTip( help_text ))
		self.timeoutControl.SetRange(5, 60*5)
		
		groupFlexSizer_1.AddMany([(ctrStaticInfo, 1, wx.EXPAND),
				                  (self.timeoutControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------

		# *** segundo conjunto de controles
		groupFlexSizer_2 = wx.FlexGridSizer(3, 2, 10, 5)
		gradeConjunto.Add( groupFlexSizer_2, 1, wx.EXPAND)

		# *** Controla o n�mero de reconex�es
		ctrStaticInfo = wx.StaticText(conteiner, -1, _(u"N�mero de reconex�es: "))
		self.reconexoesControl = wx.SpinCtrl(conteiner, -1, "3")
		
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.reconexoesControl)
		help_text = u"".join([
		    _(u"Define o n�mero de tentativas, \n"),
			_("antes de dar por encerrado o uso do ip atual.")
		])
		self.reconexoesControl.SetToolTip(wx.ToolTip( help_text ))
		self.reconexoesControl.SetRange(1,100)
		
		groupFlexSizer_2.AddMany([(ctrStaticInfo, 1, wx.EXPAND),
				                  (self.reconexoesControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------
		
		# *** Controla o tempo de espera, entre as reconex�es
		ctrStaticInfo = wx.StaticText(conteiner, -1, _(u"Espera entre reconex�es: "))
		self.waitTimeControl = wx.SpinCtrl(conteiner, -1, "2")
		
		self.Bind(wx.EVT_SPINCTRL, connectionsHandle, self.waitTimeControl)
		help_text = _(u"Tempo de espera entre as tentativas de conex�o(segundos).")
		self.waitTimeControl.SetToolTip(wx.ToolTip( help_text ))
		self.waitTimeControl.SetRange(1,60*5)
		
		groupFlexSizer_2.AddMany([(ctrStaticInfo, 1, wx.EXPAND),
				                  (self.waitTimeControl, 1, wx.EXPAND)])
		# ------------------------------------------------------------
		
		# controla o n�mero de conex�es ativas
		self.changeTypeControl = wx.CheckBox(conteiner, -1, _(u"Habilitar mudan�a de tipo"), 
											 style=wx.ALIGN_LEFT)
		help_text = u"".join([
		    _(u"Mudar o tipo de conex�o.\n"),
			_(u"Muda da conex�o padr�o para um servidor proxie ou vice-versa.")
		])
		self.changeTypeControl.SetToolTip(wx.ToolTip( help_text ))
		self.Bind(wx.EVT_CHECKBOX, connectionsHandle, self.changeTypeControl)
		groupFlexSizer_2.Add(self.changeTypeControl, 1, wx.EXPAND)
		# ------------------------------------------------------------
		
		# controla o n�mero de conex�es ativas
		self.proxyDisable = wx.CheckBox(conteiner, -1, _(u"Desabilitar proxy"), 
									    style=wx.ALIGN_LEFT)
		help_text = _(u"Desabilita o uso de conex�es com servidores proxies(n�o recomendado).")
		self.proxyDisable.SetToolTip(wx.ToolTip( help_text ))
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
		
		sizerGroups = wx.FlexGridSizer(2, 2, 5, 5)
		
		# Controle para escolha da qualidade do v�deo baixado
		ctrStaticInfo = wx.StaticText(conteiner, -1, _(u"Qualidade do v�deo: "))
		self.videoQualityControl = wx.Choice(conteiner, -1, choices = [_("Baixa"), _(u"M�dia"), _("Alta")])
		help_text = [
		    _(u"Qualidade do v�deo que ser� baixado e reproduzido.\n"),
			_(u"Note que nem todos servidores suportam essa op��o.")
		]
		self.videoQualityControl.SetToolTip(wx.ToolTip( "".join(help_text) ))
		self.videoQualityControl.SetSelection(0)
		
		sizerGroups.AddMany([(ctrStaticInfo, 1, wx.EXPAND|wx.TOP, 10),
				             (self.videoQualityControl, 1, wx.EXPAND|wx.ALIGN_LEFT|wx.TOP, 10)])
		
		# --------------------------------------------------------------------------------------------------
		ctrStaticInfo = wx.StaticText(conteiner, wx.ID_ANY, _(u"Diret�rio de v�deos: "))
		self.ctrVideoDir = wx.TextCtrl(conteiner, wx.ID_ANY, settings.DEFAULT_VIDEOS_DIR)
		sizerGroups.AddMany([(ctrStaticInfo, 1, wx.EXPAND|wx.TOP, 10),
			                 (self.ctrVideoDir, 1, wx.EXPAND|wx.ALIGN_LEFT|wx.TOP, 10)])
		self.ctrVideoDir.Bind(wx.EVT_LEFT_DOWN, self.OnShowDialog)
		self.ctrVideoDir.Bind(wx.EVT_ENTER_WINDOW, self.updateHelpTextDir)
		# GRIDSIZER ADD
		staticBoxSizer.Add( sizerGroups )
		return panel
	
	def updateHelpTextDir(self, evt):
		help_text = [
			_(u"Diret�rio, dentro do qual, ser�o quardados os arquivos de v�deo."),
			_(u"Diret�rio atual: ")+('"%s"'% self.ctrVideoDir.GetValue())
		]
		self.ctrVideoDir.SetToolTip(wx.ToolTip(u"\n".join(help_text)))
		
	def OnShowDialog(self, event):
		dlg = wx.DirDialog(self, _(u"Diret�rio de v�deos"),
				  defaultPath = self.ctrVideoDir.GetValue(),
				  style=wx.DD_DEFAULT_STYLE
				   #| wx.DD_DIR_MUST_EXIST
				   #| wx.DD_CHANGE_DIR
				   )
		if dlg.ShowModal() == wx.ID_OK:
			self.ctrVideoDir.SetValue( dlg.GetPath() )
			
		dlg.Destroy()
		
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
		help_text = _(u"Indica se o arquivo de v�deo ser� removido, \nap�s parar o download.")
		self.tempFileControl.SetToolTip(wx.ToolTip( help_text ))
		
		self.Bind(wx.EVT_CHECKBOX, lambda evt: self.tempFileOptControl.Enable(evt.GetEventObject().GetValue()), 
				self.tempFileControl)
		
		groupFlexSizer_1.Add(self.tempFileControl, 0, wx.EXPAND)
		
		# Op��es para o arquivo tempor�rio
		self.tempFileOptControl = wx.Choice(conteiner, -1, choices = [_("Apenas remova"), _("Pergunte o que fazer")])
		help_text = _(u"O que fazer, ao usar um arquivo tempor�rio ?")
		self.tempFileOptControl.SetToolTip(wx.ToolTip( help_text ))
		
		self.tempFileOptControl.Enable(False)
		self.tempFileOptControl.SetSelection(0)
		
		groupFlexSizer_1.Add(self.tempFileOptControl, 0, wx.EXPAND|wx.LEFT, 10)

		# Controla o n�mero de divis�es do arquivo de v�deo
		ctrStaticInfo = wx.StaticText(conteiner, -1, _(u"N�mero de divis�es: "))
		self.numDivStreamControl = wx.SpinCtrl(conteiner, -1, "2")
		
		help_text = _(u"Indica o n�mero de partes, que a stream\n de v�deo ser� divida inicialmente")
		self.numDivStreamControl.SetToolTip(wx.ToolTip( help_text ))
		self.numDivStreamControl.SetRange(2, 25)

		hSizer = wx.BoxSizer(wx.HORIZONTAL)
		hSizer.Add(ctrStaticInfo, 0, wx.EXPAND)
		hSizer.Add(self.numDivStreamControl, 0, wx.ALIGN_TOP)

		groupFlexSizer_1.Add(hSizer, 0, wx.EXPAND|wx.LEFT, 5)

		return panel

	def questineUsuario(self):
		if self.tempFileOptControl.Enabled and self.tempFileOptControl.GetSelection() == 1:
			msg = _(u"Gostou do v�deo ? Deseja guard�-lo para rev�-lo mais tarde ?")
			gm_dlg = GMD.GenericMessageDialog(self, msg, _("O que fazer ?"), wx.ICON_QUESTION|wx.YES_NO)
			if gm_dlg.ShowModal() == wx.ID_YES: self.setTempFileOpt()
			gm_dlg.Destroy()
		# reativando os controles para a tranfer�ncia de um novo arquivo.
		self.enableCtrs()
		
	def enableCtrs(self, enable=True):
		# reativando os controles desativadas ao iniciar a transfer�ncia.
		for method in [
		    self.tempFileControl, self.videoQualityControl, 
		    self.numDivStreamControl ]:
			method.Enable( enable )
	
	@manager.FM_runLocked()
	def setTempFileOpt(self): ## _("Arquivo corrompido!")
		assert self.mainWin.manage is not None, u"'manage' ainda n�o iniciado!"
		
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
						copy.cancel = not keepGoing # permite cancelar a c�pia.
					else:
						progressDlg.SetTitle(_(u"Tudo como esperado."))
						progressDlg.Update(copy.progress, prog_info+"\n"+copy.get_msg())
						
				elif copy.error == True:
					progressDlg.SetTitle( _(u"N�o foi poss�vel..."))
					progressDlg.Update(100, copy.get_msg())
					
			progressDlg.Destroy()

	def update_conf(self):
		# setting: controles
		control_conf = self.mainWin.configs["Controles"]
		
		# setting: qualidade do v�deo
		control_conf["videoQualityControlValue"] = self.videoQualityControl.GetSelection()
		
		# setting: diret�rio de arquivos de videos
		control_conf["ctrVideoDir"] = self.ctrVideoDir.GetValue()
		
		# setting: n�mero de conex�es ativas
		control_conf["numConexoesAtivas"] = self.nConnectionControl.GetValue()
		
		# setting: controle de arquivos tempor�ros
		control_conf["tempFileControlValue"] = self.tempFileControl.GetValue()
		
		# setting: op��es de arquivos tempor�rios
		control_conf["tempFileOptControlValue"] = self.tempFileOptControl.GetSelection()
		
		# setting: n�mero de divis�es inicias do arquivo
		control_conf["numDivStreamControlValue"] = self.numDivStreamControl.GetValue()

		# setting: taxa limite de download para sub-conex�es
		control_conf["rateLimitControlValue"] = self.rateLimitControl.GetValue()
		
		#
		control_conf["timeoutControlValue"] = self.timeoutControl.GetValue()
		
		#
		control_conf["reconexoesControlValue"] = self.reconexoesControl.GetValue()
		
		#
		control_conf["waitTimeControlValue"] = self.waitTimeControl.GetValue()
		
		#
		control_conf["changeTypeControlValue"] = self.changeTypeControl.GetValue()
		
		#
		control_conf["proxyDisable"] = self.proxyDisable.GetValue()

########################################################################
if __name__ == "__main__":
	from main.app.util import base
	base.trans_install() # instala as tradu��es.
	
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