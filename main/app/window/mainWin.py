# -*- coding: ISO-8859-1 -*-
import sys
import os
import wx
import time
import math
import thread
import threading
import configobj
from wx.lib.wordwrap import wordwrap
import wx.lib.agw.hyperlink as hyperlink
import wx.lib.agw.genericmessagedialog as GMD

from main import settings

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necessário para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )

# módulos do projeto
import manager

# Instalando a tradução
manager.installTranslation()

import jwPlayer, browser, proxy

# módulos do pacote window
import updatedialog
import ctrbar
import ipSearch
import wbugs
import dialog
import detail
import movie

# A versão será mantida pelo módulo principal
PROGRAM_VERSION = manager.PROGRAM_VERSION
########################################################################

class StartDown(threading.Thread):
	""" Coleta informações iniciais necessárias para 
	baixar o video, como tamanho e titítulo vídeo"""

	def __init__(self, mainWin):
		threading.Thread.__init__(self)
		self.manage = mainWin.manage
		self.mainWin = mainWin
		self._status = self.status = None
		self.max = 3

		# diálogo informativo
		self.diag = dialog.ProgressDialog(mainWin, _("Por favor, aguarde..."))
		self.diag.Bind(wx.EVT_CLOSE, self.canceledl)
		self.diag.btnCancel.Bind(wx.EVT_BUTTON, self.canceledl)
		self.diag.btnOk.Bind(wx.EVT_BUTTON, self.startFailed)

	def __del__(self):
		del self.diag
		del self.manage
		del self.mainWin
		del self.status
		del self.max

	def canceledl(self, evt=None):
		""" cancela a operação de download atual """
		self.manage.canceledl()
		self.status = False

		try: self.diag.Destroy()
		except: pass

		if hasattr(evt,"Skip"): evt.Skip()

	def startFailed(self, evt):
		self.status = False
		evt.Skip()

	def get_status(self):
		""" indica se tudo iniciou corretamente ou não """
		return self.status

	def run(self):
		try: 
			self._status = self.manage.start(
				self.max, recall=self.diag.update)
		except Exception, err:
			self._status = False

		if self.status is None:
			if self._status == False:
				self.diag.SetTitle(_("Falha !!!"))
				self.diag.enabeButton(True)
				self.diag.stopProgress()
			else:
				self.status = True
				self.diag.Destroy()

#----------------------------------------------------------------------	
class BaixeAssistaWin( wx.Frame ):
	def __init__(self):
		""" BaixeAssistaWin: representação principal da interface gráfica """
		wx.Frame.__init__(self, None, wx.ID_ANY, "BaixeAssista v%s"%PROGRAM_VERSION, size=(800,600))
		self.SetIcon( self.getMovieIcon() )
		
		# configurações gerais da aplicação
		self.configPath = os.path.join(settings.APPDIR,"configs","configs.cfg")
		self.configs = self.getConfigs()

		# sizer principal do frame
		mainVSizer = wx.BoxSizer( wx.VERTICAL )
		self.SetSizer( mainVSizer )
		self.SetAutoLayout(True)

		self.Bind(wx.EVT_CLOSE, self.baixeAssistaFinish)

		self.playerExterno = None
		self.manage = self.startDown = None
		self.globalInfo = manager.globalInfo
		self.streamLoading = False
		self.iewindow = None

		# status bar
		self.statusBar = wx.StatusBar(self)
		self.statusBar.SetFieldsCount(5)
		self.statusBar.SetStatusWidths([-2,-2,-3,-1,-2])
		self.SetStatusBar( self.statusBar)
		#------------------------------

		# cria todo o conjunto de menus.
		self.crieBarraMenus()
		#------------------------------

		# atualiza informacoes relativas as conexoes
		self.updateTimer = wx.Timer(self, wx.ID_ANY)
		self.Bind( wx.EVT_TIMER, self.updateInterface, self.updateTimer)

		# criando o painel de controle da entrada de urls
		painelEntradaUrls = self.criePainelEntradaUrls()

		# criando a barra de ferramentas: player, conexões, navegador
		self.barraControles = ctrbar.BarraControles(self, -1)

		# referências para as skins do player embutido
		self.addSkinsMenu()

		self.progressBar = wx.Gauge(self.statusBar )
		self.Bind(wx.EVT_MAXIMIZE, self.updateProgressBar)
		self.Bind(wx.EVT_UPDATE_UI, self.updateProgressBar)
		self.Bind(wx.EVT_SIZING, self.updateProgressBar)
		#------------------------------

		mainVSizer.Add(painelEntradaUrls, 0, wx.EXPAND)
		mainVSizer.Add(self.barraControles, 1, wx.EXPAND)

		# aplicando as configurações
		self.apliqueConfigs()

		self.Show()

	def getMovieIcon(self):
		path = os.path.join(settings.APPDIR, "imagens", "movies.png")
		bitmap = wx.BitmapFromImage(wx.Image(path))
		icon = wx.EmptyIcon()
		icon.CopyFromBitmap(bitmap)
		return icon

	def __del__(self):
		del self.playerExterno
		del self.streamLoading
		del self.configPath
		del self.globalInfo
		del self.manage
		del self.configs

	@staticmethod
	def caluculePorcentagem(currentValue, maxValue):
		""" calcula a porcentagem sem formatar o retorno """
		return (float(currentValue) / float(maxValue) *100.0)

	def getConfigs(self):
		try:
			configs = configobj.ConfigObj(self.configPath)
			if not configs: raise IOError, "configs null!!!"
		except Exception, err:
			raise IOError, "%s\nError[Fatal] config file is missin!!!"% ("System error: %s"%err)
		return configs

	def baixeAssistaFinish(self, evt=None):
		""" Termina salvando as configurações e fechando o servidor """
		# caso um arquivo esteja sendo baixado e for pressionado
		if self.streamLoading: self.btnStartStopHandle()

		# Menu: atualização automática
		isChecked = self.menuUpdate.IsChecked(500)
		self.cfg_controles["autoUpdateSearch"] = isChecked

		# Win configs
		if not self.IsMaximized():
			win_configs = self.configs["BaixeAssistaWin"]
			winPosition = self.GetPositionTuple()
			win_configs["winPositionX"] = winPosition[0]
			win_configs["winPositionY"] = winPosition[1]
			winSize = self.GetSizeTuple()
			win_configs["winWidth"] = winSize[0]
			win_configs["winHeight"] = winSize[1]

		self.salveConfigs() # salva as configurações

		# destrói a janela completamente
		self.Destroy()

	def apliqueConfigs(self):
		""" restaura a interface para o último estado de configuração """
		self.cfg_controles = self.configs["Controles"]
		self.cfg_locais = self.configs['Locais']
		self.cfg_menu = self.configs['Menus']

		is_active = self.cfg_controles.as_int("numConexoesAtivas")
		self.barraControles.nConnectionControl.SetValue( is_active )

		# controle de arquivo temp
		is_temp = self.cfg_controles.as_bool("tempFileControlValue")
		self.barraControles.tempFileControl.SetValue( is_temp )

		# controle opções de arquivos temp
		opt = self.cfg_controles.as_int("tempFileOptControlValue")
		self.barraControles.tempFileOptControl.Enable( is_temp )
		self.barraControles.tempFileOptControl.SetSelection( opt )

		# qualidade do arquivo de video
		vquality = self.cfg_controles.as_int("videoQualityControlValue")
		self.barraControles.videoQualityControl.SetSelection( vquality )

		# número inicial de divisões do arquivo de video
		value = self.cfg_controles.as_int("numDivStreamControlValue") 
		self.barraControles.numDivStreamControl.SetValue( value)

		# taxa limite de download para sub-conexões
		value = self.cfg_controles.as_int("rateLimitControlValue")
		self.barraControles.rateLimitControl.SetValue( value )

		# tempo máximo de espera, por uma resposta, de uma conexão
		value = self.cfg_controles.as_int("timeoutControlValue")
		self.barraControles.timeoutControl.SetValue( value )

		value = self.cfg_controles.as_int('reconexoesControlValue')
		self.barraControles.reconexoesControl.SetValue( value)

		value = self.cfg_controles.as_int('waitTimeControlValue')
		self.barraControles.waitTimeControl.SetValue( value)

		value = self.cfg_controles.as_bool('changeTypeControlValue')
		self.barraControles.changeTypeControl.SetValue( value)

		value = self.cfg_controles.as_bool('proxyDisable')
		self.barraControles.proxyDisable.SetValue( value)

		playerEmbutido = self.cfg_menu.as_bool('playerEmbutido')
		self.menuPlayer.Check(100, playerEmbutido) # ativar player embutido ?

		servidorAtivo = self.cfg_menu.as_bool('servidorAtivo')
		self.menuAcoes.Check(300, servidorAtivo)

		if self.cfg_locais["playerPath"]:
			self.menuPlayer.Check(102, not playerEmbutido) # ativar player externo ?

		autoSearch = self.cfg_controles.as_bool("autoUpdateSearch")
		# procurando uma nova versão automaticamente.
		if autoSearch: self.findUpdateNow(noInfo=True)
		self.menuUpdate.Check(500, autoSearch)

		# últimas configurações da janela
		win_configs = self.configs["BaixeAssistaWin"]

		if not win_configs.has_key("firstRun"):
			win_configs["firstRun"] = False

		# ao iniciar pela primeria vez a janela fica no centro da tela.
		if win_configs.as_bool("firstRun"):
			win_configs["firstRun"] = False
			self.CenterOnScreen()
		else:
			# aplicando o posicionamento
			px = win_configs.as_int("winPositionX")
			py = win_configs.as_int("winPositionY")
			self.SetPosition((px, py))

			# ajustando o tamanho da janela
			ww = win_configs.as_int("winWidth")
			wh = win_configs.as_int("winHeight")
			self.SetSize((ww, wh))

	def salveConfigs(self):
		if not manager.security_save(self.configPath, _configobj=self.configs):
			print "Erro[MainWin] salvando arquivo de configuração!!!"

	def crieBarraMenus(self):
		""" cria a barra de menus e os menus usados na interface pricipal """
		# menus de controle do player
		self.menuPlayer = wx.Menu()
		self.menuPlayer.Append(100, _("Usar player embutido"), kind = wx.ITEM_RADIO)
		self.menuPlayer.Append(102, _("Usar player externo"), kind = wx.ITEM_RADIO)
		self.menuPlayer.AppendSeparator()
		self.menuPlayer.Append(103, _("Recarregar player"))
		self.menuPlayer.Append(104, _("Escolher outro player"))

		# menus de edição
		self.menuEditar = wx.Menu()
		self.menuEditar.Append(200, _("Videos"))
		self.menuEditar.Append(201, _("Atualizar lista de ips"))
		self.menuEditar.AppendSeparator()
		self.menuSkins = wx.Menu()
		self.menuEditar.AppendMenu(202, _("Mudar skin"), self.menuSkins)

		# menus de ação
		self.menuAcoes = wx.Menu()
		self.menuAcoes.Append(300, _("Ligar servidor"), kind = wx.ITEM_CHECK)
		self.menuAcoes.Append(301, _("Tela cheia"))
		self.menuAcoes.Check(300, True)

		# menu linguagem
		self.menuLinguagem = wx.Menu()
		self.menuLinguagem.Append(700, _(u"Português"), kind = wx.ITEM_RADIO)
		self.menuLinguagem.Append(701, _(u"Inglês"), kind = wx.ITEM_RADIO)
		self.menuLinguagem.Append(702, _("Espanhol"), kind = wx.ITEM_RADIO)
		self.menuLinguagem.language_codes = {700: "pt_BR", 701: "en", 702: "es"}

		# ativa a última linguagem selecionada no menu.
		language = self.configs["Menus"]["language"]

		for _id, _lang in self.menuLinguagem.language_codes.items():
			if _lang == language:
				self.menuLinguagem.Check(_id, True)
				break

		self.menuAjuda = wx.Menu()
		self.menuAjuda.Append(400, _("Tutorial"))
		self.menuUpdate = wx.Menu() #menu ajuda
		self.menuUpdate.Append(500, _("Procurar automaticamente"), kind = wx.ITEM_CHECK)
		self.menuUpdate.Append(501, _("Verifique agora"))
		self.menuAjuda.AppendMenu(401, _(u"Atualização"), self.menuUpdate)
		self.menuAjuda.AppendSeparator()
		self.menuAjuda.Append(402, _(u"Relatório de erros"))
		self.menuAjuda.AppendSeparator()
		self.menuAjuda.Append(403, _("Sobre"))

		# cria a barra de menus a adiciona os menus
		self.barraMenus = wx.MenuBar()
		self.barraMenus.Append(self.menuPlayer, _("Players"))
		self.barraMenus.Append(self.menuEditar, _("Editar"))
		self.barraMenus.Append(self.menuAcoes, _(u"Ações"))
		self.barraMenus.Append(self.menuLinguagem, _("Linguagem"))
		self.barraMenus.Append(self.menuAjuda, _("Ajuda"))

		# atribuindo eventos aos menus
		for i in range(100, 104 +1):
			self.Bind( wx.EVT_MENU, self.changePlayer, id= i)

		self.Bind(wx.EVT_MENU, self.openMovieManager, id=200)
		self.Bind(wx.EVT_MENU, self.openControlUpdadteIps, id=201)
		self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.skinsHandle, id=202)

		self.Bind(wx.EVT_MENU, self.ativeServidor, id=300)
		self.Bind(wx.EVT_MENU, self.setFullScreenMode, id=301)
		self.Bind(wx.EVT_CHAR_HOOK, self.setFullScreenMode)

		for i in range(700, 703):
			self.Bind(wx.EVT_MENU, self.changeLanguage, id=i)

		self.Bind(wx.EVT_MENU, self.helpProgram, id=400)
		# update commands
		self.Bind(wx.EVT_MENU, self.findUpdateNow, id=500)
		self.Bind(wx.EVT_MENU, self.findUpdateNow, id=501)

		self.Bind(wx.EVT_MENU, self.formHandle, id=402)
		self.Bind(wx.EVT_MENU, self.aboutProgram, id=403)

		self.SetMenuBar( self.barraMenus )

	def changeLanguage(self, evt):
		menuId = evt.GetId()
		code = self.menuLinguagem.language_codes.get(menuId,"")
		self.configs["Menus"]["language"] = code
		msg = _(u"A nova linguagem só será aplicada, após reiniciar o programa.")
		dlg = GMD.GenericMessageDialog(self, msg, _("Linguagem modificada"), wx.ICON_INFORMATION|wx.OK)
		dlg.ShowModal(); dlg.Destroy()

	def formHandle(self, evt):
		""" cria um formulário de informação de bugs. 
		o formulário é preenchido pelo usuário. """
		win = wbugs.BugInfo(self, _(u"Relatório de erros"))

	def addSkinsMenu(self ):
		""" Termina de montar o menu de skins """
		idIntValue = 600
		checked = idIntValue # usado como item padrão
		skinName = self.configs["PlayerWin"]["skinName"]
		for index, skin in enumerate(self.playerWin.getSkinsNames()):
			menuItemId = idIntValue + index
			self.menuSkins.AppendRadioItem(menuItemId, skin)
			self.Bind(wx.EVT_MENU, self.skinsHandle, id= menuItemId)
			if skinName == skin: checked = menuItemId
		# marca a última skin usada
		self.menuSkins.Check(checked, True)

	def skinsHandle(self, evt):
		""" adiciona a skin selecionada para player embutido """
		skinname = self.menuSkins.GetLabelText(evt.GetId())
		self.configs["PlayerWin"]["skinName"] = skinname
		self.playerWin["skinName"] = skinname
		# atualiza o player(automaticamente),quando ativado no menu.
		if self.cfg_menu.as_bool('playerEmbutido'):
			self.recarreguePlayer()

	def aboutProgram(self, evt):
		# First we create and fill the info object
		info = wx.AboutDialogInfo()
		info.Name = "BaixeAssista"
		info.Version = "v%s"%PROGRAM_VERSION
		info.Copyright = "(C) 2012 Programmers and Coders Everywhere"

		description = u"".join([
			_(u"O programa BaixeAssista busca dar uma solução amigável a usuários"),
			_(u" que se interessam por filmes postados na internet. Como há muita burocracia"),
			_(u" e empecilhos para assistir a um único filme, o programa tentará resgatar para"),
			_(u" o usuário o que mais interessa, a diversão. Chega de popup, propagandas, limites"),
			_(u" de tempo para assistir filmes.")
		])
		info.Description = wordwrap(description, 400, wx.ClientDC(self))
		info.WebSite = ("http://code.google.com/p/gerenciador-de-videos-online/", "Projeto BaixeAssista")
		info.Developers = ["Alex [geniofuturo@gmail.com]"]

		licenseText = u"".join([
			_(u"Esse programa é de domínio público. Isso significa que você poderá"),
			_(u" copiá-lo, modificá-lo sem restrição alguma.")
		])
		info.License = wordwrap(licenseText, 500, wx.ClientDC(self))
		# Then we call wx.AboutBox giving it that info object
		wx.AboutBox(info)

	def helpProgram(self, evt):
		menus = self.configs.get("Menus",{})
		lang = menus.get("language","en")

		filepath = os.path.join(settings.APPDIR, "locale",lang,"LC_MESSAGES","help.txt")
		try:
			import wx.lib.dialogs
			with open(filepath, "r") as file:
				msg = file.read()
				dlg = wx.lib.dialogs.ScrolledMessageDialog(self, msg, _("Tutorial"), size=(800, 350))
				dlg.ShowModal()
		except Exception, err:
			msg = _("Ocorreu um erro ao tentar abrir o arquivo de ajuda.")
			dlg = GMD.GenericMessageDialog(msg, _("Erro!"), wx.ICON_ERROR|wx.OK)
			dlg.ShowModal(); dlg.Destroy()

	def searchUpdateNow(self, noInfo):
		# *** Procurando por uma nova versão do programa ***
		updateSearch = manager.UpdateSearch()
		status, msg = updateSearch.search()

		if status is True:
			msg += _(u"\nPressione OK para ir a página de download.")
			wx.CallAfter(
				self.showSafeMessageDialog,
				msg = msg, title = _("Novidade!"),
				style = wx.ICON_INFORMATION|wx.OK|wx.CANCEL,
				link = "http://code.google.com/p/gerenciador-de-videos-online/downloads/list"
			)
		if status is False and noInfo is False:
			wx.CallAfter(
				self.showSafeMessageDialog,
				msg = msg, title=_("Ainda em desenvolvimento..."), 
				style = wx.ICON_INFORMATION|wx.OK
			)
		elif status is None and noInfo is False:
			wx.CallAfter(
				self.showSafeMessageDialog,	    
				msg = msg, title = _("Erro!"), 
				style = wx.ICON_ERROR|wx.OK
			)
		# Inicia a procura por pacotes de atualização.
		packetVersion = self.configs["Controles"]["packetVersion"]
		updater = manager.Updater(packetVersion = packetVersion)
		
		if updater.search() is True:
			# começa o download da atualização
			sucess, msg = updater.download()
			
			if sucess is True:
				language = self.configs["Menus"]["language"]
				# texto informando as mudanças que a nova atualização fez.
				changes = updater.getLastChanges( language)
				
				# aplica a atualização
				sucess, msg = updater.update()
				
				# remove todos os arquivos
				updater.cleanUpdateDir()
				
				if sucess is True:
					## ======================================================
					newVersion = updater.getNewVersion()
					
					if newVersion: # guarda a versão do pacote recebido.
						self.configs["Controles"]["packetVersion"] = newVersion
					## ======================================================
					
					wx.CallAfter(self.showDialogUpdate, msg, "\n\n".join(changes))
					## ======================================================
				elif noInfo is False:
					wx.CallAfter(
						self.showSafeMessageDialog,
						msg = msg, title=_("Atualizando."),
						style = wx.ICON_ERROR|wx.OK
					)
			elif noInfo is False:
				wx.CallAfter(
					self.showSafeMessageDialog,
					msg = msg, title=_("Baixando pacote."),
					style = wx.ICON_ERROR|wx.OK
				)
		elif noInfo is False:
			if updater.isOldRelease():
				wx.CallAfter(
					self.showSafeMessageDialog,
					msg = updater.warning, title=_("Programa atualizado."),
					style = wx.ICON_INFORMATION|wx.OK
				)
		elif noInfo is False:
			wx.CallAfter(
				self.showSafeMessageDialog,
				msg = msg, title=_("Erro!"),
				style = wx.ICON_ERROR|wx.OK
			)

	def showSafeMessageDialog(self, **kwargs):
		dlg = GMD.GenericMessageDialog(self, kwargs["msg"], kwargs["title"], kwargs["style"])					
		dlgModal = dlg.ShowModal(); dlg.Destroy()

		if kwargs.get("link", "") and dlgModal == wx.ID_OK:
			hyper = hyperlink.HyperLinkCtrl(self, wx.ID_ANY, "", URL = kwargs["link"])
			hyper.GotoURL(kwargs["link"], True, False)
			hyper.Destroy()

	def showDialogUpdate(self, msg, changesText):
		# informa o usuário da nova atualização
		# o dialogo fica instável ao ser chamado do thread de atualização.
		isauto = self.configs["Controles"].as_bool("autoUpdateSearch")

		if isauto: titleChunk = _(u"Ativada)")
		else: titleChunk = _(u"Desativada)")

		title = _(u"Novas atualizações recebidas! (Atualização automática - ") + titleChunk
		dlgUpdate = updatedialog.UpdateDialog(self, title)

		dlgUpdate.CenterOnParent()
		dlgUpdate.setInfo( msg )
		dlgUpdate.SetFocus()

		# informa o grupo de mudanças
		dlgUpdate.writeText( changesText )
		dlgUpdate.Show(True)

	def findUpdateNow(self, evt=None, noInfo=False):
		""" inicia a procura por atualizações """

		if hasattr(evt, "GetId") and evt.GetId() == 500:
			isChecked = self.menuUpdate.IsChecked(500)
			self.configs["Controles"]["autoUpdateSearch"] = isChecked
			return # atualiza o estado da atualização automática.

		t = threading.Thread(target=self.searchUpdateNow, args=(noInfo,))
		t.start()

	def getLinkControlVal(self):
		""" retorna o valor do controlador no formato desejado """
		url_str = self.controladorUrl.GetValue()
		url, desc = self.urlManager.splitUrlDesc( url_str )
		return url

	def startServer(self): # tenta iniciar o servidor
		if isinstance(self.manage, manager.Manage):
			if not self.manage.startServer():
				msg = u"".join([
					_(u"O servidor falhou ao tentar iniciar no endereço: http://localhost:8080"),
					_(u"\nDesmarque a opção no menu \"Ações / Ligar servidor\" para iniciar o download."),
					_(u"\n\nNote que sem o servidor o player não funcionará.")
				])
				dlg = GMD.GenericMessageDialog(self, msg, _("Erro iniciando o servidor."), wx.ICON_ERROR|wx.OK)
				dlg.ShowModal(); dlg.Destroy()
				return False  # erro iniciando o servidor
			else: return True # servidor iniciado com sucesso
		else: return None     # manage ainda não iniciado

	def stopServer(self):
		""" pára o servidor se ele já estiver ativado """
		if isinstance(self.manage, manager.Manage):
			self.manage.stopServer()

	def ativeServidor(self, evt):
		""" inicia ou pára o servidor, com base no menu de controle """
		self.cfg_menu["servidorAtivo"] = checked = evt.IsChecked()
		if checked: self.startServer()
		else: self.stopServer()

	def setPlayerPath(self):
		""" chamada para modificar o caminho para o player externo """
		dlg = wx.FileDialog(
			self, message = _(u"Escolha o local do player (executável)"),
			defaultDir = settings.APPDIR, 
			defaultFile = "",
			wildcard = "Player file (*.exe)|*.exe",
			style = wx.OPEN)

		if dlg.ShowModal() == wx.ID_OK:
			# caminho para o player externo
			self.cfg_locais['playerPath'] = dlg.GetPath() 

		dlg.Destroy()

		# confirma se um camnhinho foi escolhido
		return self.cfg_locais['playerPath']

	def stopExternalPlayer(self):
		""" pára a execução do player externo """
		if self.playerExterno and self.playerExterno.isRunning():
			self.playerExterno.playerStop()
			self.playerExterno = None

	def stopEmbedPlayer(self):
		""" recarrega o player embutido """
		self.stopConnection()
		self.playerWin["autostart"] = False
		self.playerWin.reload()

	def stopConnection(self):
		""" fecha a conexão atual do servidor com o player """
		if isinstance(self.manage, manager.Manage) and \
		   hasattr(self.manage.streamServer, "clienteStop"):
			self.manage.streamServer.clienteStop()

	def carreguePlayerExterno(self):
		""" carrega o player externo """
		if self.streamLoading:
			playerPath = self.cfg_locais["playerPath"]

			if playerPath:
				if self.manage.streamServer and self.cfg_menu.as_bool("servidorAtivo"):
					self.manage.streamServer.setMeta(False)
					self.playerExterno = manager.FlvPlayer( playerPath)
					self.playerExterno.start()
			else:
				# caso não haja um caminho válido para o player
				self.setPlayerPath()

	def recarreguePlayer(self):
		""" recarrega o player para seu estado inicial """
		self.stopConnection()

		if self.cfg_menu.as_bool('playerEmbutido'):
			# o player iniciará automaticamente se baixando a stream
			self.playerWin["autostart"] = self.streamLoading
			self.playerWin.reload()
		else:
			self.stopExternalPlayer()
			self.carreguePlayerExterno()

	def setFullScreenMode(self, evt=None):
		""" sincroniza o modo fullscreen do menu com o widget fullscreen button """
		if evt.GetId() == 301 or (self.IsFullScreen() and evt.GetKeyCode() == wx.WXK_ESCAPE):
			self.barraControles.setFullScreen(evt, self)
		evt.Skip()

	def changePlayer(self, evt):
		menuid = evt.GetId() # id do menu que gerou o evento

		playerPath = self.cfg_locais['playerPath']
		servidorAtivo = self.cfg_menu.as_bool('servidorAtivo')

		if menuid == 100: # menu player embutido
			self.cfg_menu['playerEmbutido'] = True

			if servidorAtivo and self.manage.streamServer: 
				self.manage.streamServer.setMeta(True)

			# parando o player externo
			self.stopExternalPlayer()

		elif menuid == 102: # menu player externo
			self.cfg_menu["playerEmbutido"] = False
			self.stopEmbedPlayer()

			# se não houver um caminho válido para o player externo
			if not playerPath:
				if not self.setPlayerPath():
					self.menuPlayer.Check(100, True)
					self.cfg_menu['playerEmbutido'] = True
					return # cancelado

			self.carreguePlayerExterno()

		elif menuid == 103: # menu reload player
			self.recarreguePlayer()

		elif menuid == 104:
			self.setPlayerPath()

	def criePainelEntradaUrls(self):
		painel = wx.Panel(self, style = wx.BORDER_STATIC)

		# link manager -------------------------
		self.urlManager = manager.UrlManager()
		link, desc = self.urlManager.getLastUrl()
		defautUrl = self.urlManager.joinUrlDesc(link, desc)

		self.controladorUrl = wx.ComboBox( painel, value = "", style= wx.CB_DROPDOWN )
		self.controladorUrl.SetFont(wx.Font(11, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Arial'))
		wx.CallAfter( lambda evt=None: self.controladorUrl.SetValue( defautUrl) )
		self.setUrlHelpText( desc)

		for link, desc in self.urlManager.getUrlTitleList():
			self.controladorUrl.Append(self.urlManager.joinUrlDesc(link, desc), desc)

		# evento associado ao texto descrivo da url selecionado 
		self.controladorUrl.Bind(wx.EVT_COMBOBOX, self.setUrlTooltip )
		# ----------------------------------------------------------

		self.btnStartStop = wx.ToggleButton(painel, -1, _("Baixar"))
		self.btnStartStop.SetToolTip(wx.ToolTip( _(u"Começa ou pára a transferência do arquivo de vídeo") ))
		self.btnStartStop.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Arial'))
		self.Bind(wx.EVT_TOGGLEBUTTON, self.btnStartStopHandle, self.btnStartStop)

		painelSizer = wx.BoxSizer( wx.HORIZONTAL )
		painelSizer.Add(self.controladorUrl, 1, wx.EXPAND|wx.LEFT|wx.UP, 2)
		painelSizer.Add(self.btnStartStop, 0, wx.LEFT|wx.RIGHT, 2)

		painel.SetSizer( painelSizer )
		painel.SetAutoLayout(True)
		return painel

	def btnStartStopHandle(self, evt=None):
		btnText = self.btnStartStop.GetLabel()
		isPressed = self.btnStartStop.GetValue()
		if isPressed and btnText == _("Baixar"):
			self.btnStartStop.SetLabel( _("Parar") )
			self.startLoading()
		else:
			self.btnStartStop.SetValue(False)
			self.btnStartStop.SetLabel( _("Baixar") )
			self.stopStreamLoading()

	def updateStatusBar(self, *args):
		for index, value in enumerate( args): 
			self.statusBar.SetStatusText(value, index)
		self.updateProgressBar() # progressbar update

	def updateProgressBar(self, evt=None):
		lastField = self.statusBar.GetFieldsCount()-1
		rect = self.statusBar.GetFieldRect( lastField)
		x, y, w, h = rect.x+1, rect.y, rect.width, rect.height
		self.progressBar.SetPosition((x, y+1))
		self.progressBar.SetSize((w, h-3))

	def openMovieManager(self, evt):
		mv = movie.MovieManager(self, _("Visualize e/ou remova videos"))
		mv.CenterOnParent(wx.BOTH)

	def openControlUpdadteIps(self, evt):
		control = ipSearch.IpSearchControl(self, _("Crie uma nova lista de ips..."))

	def controleConexoes(self, evt=None, default=False):
		""" Adiciona ou remove conexões """
		if self.streamLoading and not self.manage.isComplete():
			numConnections = self.barraControles.nConnectionControl.GetValue()
			ratelimit = self.barraControles.rateLimitControl.GetValue()
			timeout = self.barraControles.timeoutControl.GetValue()
			typechange = self.barraControles.changeTypeControl.GetValue()
			reconexao = self.barraControles.reconexoesControl.GetValue()
			waittime = self.barraControles.waitTimeControl.GetValue()
			proxyDisable = self.barraControles.proxyDisable.GetValue()
			difer = numConnections - self.manage.getnConnection()

			# --------------------------------------------------------------
			if difer > 0: # *** adiciona novas conexões
				for index in range(difer):
					if default and index > 0: default = False
					if proxyDisable: default=True

					smanager = self.manage.startNewConnection(default,
										                      ratelimit = ratelimit, timeout = timeout,
										                      typechange = typechange, waittime = waittime,
										                      reconexao = reconexao )
					###
					self.detailControl.setInfoItem( smanager.ident )

			# --------------------------------------------------------------
			elif difer < 0: # *** remove conexões existentes
				# referência para as conexões criadas
				connections = self.manage.getConnections()
				numConnections = self.manage.getnConnectionReal()

				for index in range(0, abs(difer)):
					for index in range(numConnections-1, -1, -1):
						smanager = connections[ index ]
						if not smanager.wasStopped(): # desconsidera conexões inativas
							smanager.stop()
							# remove o item ligado a conexão
							self.detailControl.removaItemConexao( smanager.ident )
							break

				# remove todas as conexões paradas
				self.manage.removaConexoesInativas()

			# --------------------------------------------------------------
			else: # *** mudança dinânica dos parâmetros das conexões
				for smanager in self.manage.getConnections():
					if not smanager.wasStopped():
						smanager["timeout"] = timeout       # tempo de espera
						smanager["ratelimit"] = ratelimit   # taxa limite de velocidade
						smanager["typechange"] = typechange # mudança do estado dos ips
						smanager["waittime"] = waittime    # espera entre reconões
						smanager["reconexao"] = reconexao   # número de reconexões

	def updateInterface(self, evt):
		if self.streamLoading:
			# ATUALIZA A BARRA DE PROGRESSO GLOBAL
			progress = self.caluculePorcentagem(self.manage.numBytesRecebidos(), self.manage.getVideoSize())
			if self.progressBar.GetValue() != progress: self.progressBar.SetValue(progress)

			# ATUALIZA O ESTADO DAS CONEXOES
			listControl = self.detailControl.GetListCtrl()

			for smanager in self.manage.getConnections():
				if not smanager.wasStopped(): # conexões paradas serão ignoradas
					rowIndex = self.detailControl.getRowIndex( smanager.ident )

					for colIndex, key_info in enumerate( manager.StreamManager.listInfo ):
						info_value = self.globalInfo.get_info( smanager.ident, key_info )

						listControl.SetStringItem( rowIndex, colIndex, u"%s"%info_value)

					# subprogressbar update
					blockSize = self.manage.interval.get_block_size( smanager.ident)
					self.detailControl.listSubProgressBar[ rowIndex ].UpdateValue(smanager.numBytesLidos, blockSize)
					self.detailControl.GetListCtrl().RefreshItem( rowIndex)

			# ATUALIZA A STATUSBAR
			velocidade = _(" V-Global: %s") % self.manage.velocidadeGlobal
			tempo = _(u"Duração: %10s") % self.manage.tempoDownload
			progresso = _("Progresso: %10s") %str( self.manage.progresso() )
			porcentagem = "%5s"%self.manage.porcentagem()
			self.updateStatusBar(velocidade, tempo, progresso, porcentagem)

		else:
			status = self.startDown.get_status()
			if status is True: # iniciou com sucesso
				self.startStreamLoading()

			elif status is False: # houve um erro.	
				self.btnStartStopHandle()

	def url_existe(self, url):
		for url_dec in self.controladorUrl.GetStrings():
			url_, dec = self.urlManager.splitUrlDesc( url_dec )
			if url == url_: return True
		return False

	def startLoading(self, evt=None):
		if not self.streamLoading:
			url = self.getLinkControlVal()
			# opção para uso de arquivo temporário
			tempfile = self.barraControles.tempFileControl.GetValue()
			# opção de qualidade do vídeo
			vquality = self.barraControles.videoQualityControl.GetSelection()
			# opção para o número de divisões iniciais da stream de vídeo
			maxsplit = self.barraControles.numDivStreamControl.GetValue()
			try:
				# inicia o objeto princial: main_obj
				self.manage = manager.Manage( url, tempfile = tempfile, videoQuality = (vquality+1), #0+1=1
								              maxsplit = maxsplit)
			except Exception, err:
				self.btnStartStopHandle()

				# O erro principal seria uma url inválida.
				dlg = GMD.GenericMessageDialog(self, _(u"Erro: %s")%err, 
								               _("Erro iniciando download."), wx.ICON_ERROR|wx.OK)
				dlg.ShowModal(); dlg.Destroy()
				return

			self.startDown = StartDown(self)
			self.startDown.start()

			# inicia: updateInterface
			self.updateTimer.Start(500)

	def startStreamLoading(self):
		self.streamLoading = True

		# titulo do arquivo de video
		title = self.manage.getVideoTitle()
		url = self.manage.getUrl()

		# ajuda a indentificar a url
		self.setUrlHelpText( title )

		urlTitle = self.urlManager.joinUrlDesc(url, title)
		self.controladorUrl.SetLabel(urlTitle)

		if not self.url_existe( url ):
			self.controladorUrl.Append(urlTitle, title)

		# cancela o download atual
		if self.cfg_menu.as_bool("servidorAtivo") and not self.startServer():
			self.btnStartStopHandle(); return

		# adiciona as conexões padrão
		self.controleConexoes(default=True)

		if not self.cfg_menu.as_bool('playerEmbutido'):
			self.carreguePlayerExterno()
		elif self.manage.streamServer:
			self.manage.streamServer.setMeta(True)

		# uma vez iniciada a transferência, desativa o controle
		# por motivo de segurança. Essa configuração torna-se in-
		# válida para a tranferência do arquivo.
		self.barraControles.tempFileControl.Enable(False)
		self.barraControles.videoQualityControl.Enable(False)
		self.barraControles.numDivStreamControl.Enable(False)

	def stopStreamLoading(self, evt=None):
		self.updateTimer.Stop()
		self.updateStatusBar("","","","")

		if self.streamLoading:
			# só terá efeito, quando usando arquivos temporários
			self.barraControles.questineUsuario()

			self.streamLoading = False
			self.stopExternalPlayer()
			self.recarreguePlayer()

			# parando todas as conexões criadas
			self.manage.stopConnections()
			self.detailControl.removaTodosItens()

			#zera a barra de progresso
			self.progressBar.SetValue(0.0)

			# parando o servidor
			self.manage.stopServer()

			self.manage.delete_vars()
			self.manage = None

		elif hasattr(self.startDown, "canceledl"):
			self.startDown.canceledl()

		# valor "None" é para indicar objeto não inciado.
		self.startDown = None

	def setUrlTooltip(self, evt):
		controladorUrl = evt.GetEventObject()
		helpText = controladorUrl.GetClientData( controladorUrl.GetSelection() )
		self.controladorUrl.SetToolTip( wx.ToolTip( helpText ) )

	def setUrlHelpText(self, h):
		self.controladorUrl.SetToolTip(wx.ToolTip( h ))
		
########################################################################
if __name__ == "__main__":
	# dir com os diretórios do projeto
	os.chdir( pardir )
	
	app = wx.App(0)
	BaixeAssistaWin()
	app.MainLoop()