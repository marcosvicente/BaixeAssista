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
import updater

# Instalando a tradução
manager.installTranslation()

import browser, proxy

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
		self.max = 8

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

		self.externalPlayer = None
		self.manage = self.startDown = None
		self.info = manager.Info
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
		path = os.path.join(settings.IMAGES_DIR, "movies.png")
		bitmap = wx.BitmapFromImage(wx.Image(path))
		icon = wx.EmptyIcon()
		icon.CopyFromBitmap(bitmap)
		return icon

	def __del__(self):
		del self.externalPlayer
		del self.streamLoading
		del self.configPath
		del self.info
		del self.manage
		del self.configs

	@staticmethod
	def caluculePorcentagem(currentValue, maxValue):
		""" calcula a porcentagem sem formatar o retorno """
		return (float(currentValue) / float(maxValue) *100.0)
	
	def isLoading(self): return self.streamLoading
	
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
		
		self.Bind(wx.EVT_MENU, self.activeServer, id=300)
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
		filepath = os.path.join(settings.APPDIR, "locale", lang, "LC_MESSAGES", "help.txt")
		try:
			import wx.lib.dialogs
			with open(filepath, "r") as file:
				msg = file.read()
				dlg = wx.lib.dialogs.ScrolledMessageDialog(self, msg, _("Tutorial"), size=(800, 350))
				dlg.ShowModal()
		except Exception as err:
			msg = _("Ocorreu um erro ao tentar abrir o arquivo de ajuda.")
			dlg = GMD.GenericMessageDialog(msg, _("Erro!"), wx.ICON_ERROR|wx.OK)
			dlg.ShowModal(); dlg.Destroy()

	def searchUpdateNow(self, noInfo):
		## _("Erro!")
		# Iniciando ao procura por uma nova versão do programa.
		rel = updater.Release()
		status, msg = rel.search()
		
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
		upd = updater.Updater(packetVersion = self.configs["Controles"]["packetVersion"])
		
		if upd.search() is True:
			# começa o download da atualização
			sucess, msg = upd.download()
			
			if sucess is True:
				language = self.configs["Menus"]["language"]
				# texto informando as mudanças que a nova atualização fez.
				changes = upd.getLastChanges( language)
				
				# aplica a atualização
				sucess, msg = upd.update()
				
				# remove todos os arquivos
				upd.cleanUpdateDir()
				
				if sucess is True:
					## ======================================================
					newVersion = upd.getNewVersion()
					
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
			if upd.isOldRelease():
				wx.CallAfter(
					self.showSafeMessageDialog,
					msg = upd.warning, title=_("Programa atualizado."),
					style = wx.ICON_INFORMATION|wx.OK
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
	
	def startServer(self): # tenta iniciar o servidor
		if not manager.Server.running:
			if not manager.Manage.forceLocalServer(port = 8015):
				msg = u"".join([
					_(u"O servidor falhou ao tentar iniciar no endereço: http://localhost:8080"),
					_(u"\nDesmarque a opção no menu \"Ações / Ligar servidor\" para iniciar o download."),
					_(u"\n\nNote que sem o servidor o player não funcionará.")
				])
				dlg = GMD.GenericMessageDialog(self, msg, _("Erro iniciando o servidor."), wx.ICON_ERROR|wx.OK)
				dlg.ShowModal(); dlg.Destroy()
		return manager.Server.running
		
	def activeServer(self, evt):
		""" inicia ou pára o servidor, com base no menu de controle """
		if evt.IsChecked():
			if not self.startServer():
				self.menuAcoes.Check(evt.GetId(),False)
		else: pass # Todo: executar parada do servidor
		checked = self.menuAcoes.IsChecked( evt.GetId() )
		self.cfg_menu["servidorAtivo"] = checked
	
	def setFullScreenMode(self, evt=None):
		""" sincroniza o modo fullscreen do menu com o widget fullscreen button """
		if evt.GetId() == 301 or (self.IsFullScreen() and evt.GetKeyCode() == wx.WXK_ESCAPE):
			self.barraControles.setFullScreen(evt, self)
		evt.Skip()
		
	def setPlayerPath(self):
		""" chamada para modificar o caminho para o player externo """
		dlg = wx.FileDialog(
			self, message = _(u"Escolha o local do player (executável)"),
			defaultDir = settings.APPDIR, defaultFile = '',
			wildcard = "Player file (*.exe)|*.exe",
			style = wx.OPEN)
		
		if dlg.ShowModal() == wx.ID_OK:
			# caminho para o player externo
			self.cfg_locais['playerPath'] = dlg.GetPath() 
			
		dlg.Destroy()

		# confirma se um camnhinho foi escolhido
		return self.cfg_locais['playerPath']
			
	def startExternalPlayer(self):
		""" carrega o player externo """
		if not self.cfg_locais["playerPath"]:
			self.setPlayerPath()
			
		if self.streamLoading and self.cfg_locais["playerPath"]:
			self.externalPlayer = manager.FlvPlayer(
						self.cfg_locais["playerPath"], 
						host = manager.Server.HOST, 
						port = manager.Server.PORT)
			self.externalPlayer.start()
			
	def stopExternalPlayer(self):
		""" pára a execução do player externo """
		if self.externalPlayer and self.externalPlayer.isRunning():
			self.externalPlayer.stop()
			self.externalPlayer=None
	
	def stopEmbedPlayer(self):
		""" recarrega o player embutido """
		self.playerWin["autostart"] = False
		self.playerWin.reload()
		
	def reloadPlayer(self):
		""" recarrega o player para seu estado inicial """
		if self.cfg_menu.as_bool('playerEmbutido'):
			# o player iniciará automaticamente se baixando a stream
			self.playerWin["hostName"] = manager.Server.HOST
			self.playerWin["portNumber"] = manager.Server.PORT
			self.playerWin["autostart"] = self.streamLoading
			self.playerWin.reload()
		else:
			self.stopExternalPlayer()
			self.startExternalPlayer()
	
	def changePlayer(self, evt):
		menuid = evt.GetId() # id do menu que gerou o evento
		serverIsActive = self.cfg_menu.as_bool('servidorAtivo')
		
		if menuid == 100: # menu player embutido
			self.cfg_menu['playerEmbutido'] = True
			if hasattr(self.manage,"stopStreamers"):
				self.manage.stopStreamers()
			# parando o player externo
			self.stopExternalPlayer()
			self.reloadPlayer()
			
		elif menuid == 102: # menu player externo
			self.cfg_menu["playerEmbutido"] = False
			if hasattr(self.manage,"stopStreamers"):
				self.manage.stopStreamers()
			# parando o player embutido
			self.stopEmbedPlayer()
			self.startExternalPlayer()
			
			# se não houver um caminho válido para o player externo
			if not self.cfg_locais['playerPath']:
				self.menuPlayer.Check(100, True)
				
				self.cfg_menu['playerEmbutido'] = True
				self.reloadPlayer()
				
		elif menuid == 103: # menu reload player
			self.reloadPlayer()

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
			wx.CallAfter( self.stopStreamLoading )

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
		mvr = movie.MovieManager(self, _("Visualize e/ou remova videos"))
		mvr.CenterOnParent(wx.BOTH)

	def openControlUpdadteIps(self, evt):
		ipsh = ipSearch.wIPSearch(self, _("Crie uma nova lista de ips..."))
		# restaurando o último estado de cofiguração
		ipsh.setLastConfigs()
		
	def controleConexoes(self, evt=None, default=False):
		""" Adiciona ou remove conexões """
		if self.streamLoading and not self.manage.isComplete():
			ctrConnection = self.manage.ctrConnection
			
			nActiveConn = ctrConnection.getnActiveConnection()
			nConnCtr = self.barraControles.nConnectionControl.GetValue()
			
			proxyDisable = self.barraControles.proxyDisable.GetValue()
			numOfConn = nConnCtr - nActiveConn
			
			params = {
			    "ratelimit": self.barraControles.rateLimitControl.GetValue(), 
			    "timeout": self.barraControles.timeoutControl.GetValue(),
			    "typechange": self.barraControles.changeTypeControl.GetValue(), 
			    "waittime": self.barraControles.waitTimeControl.GetValue(),
			    "reconexao": self.barraControles.reconexoesControl.GetValue()
			}
			if numOfConn > 0: # adiciona novas conexões.
				if proxyDisable:
					sm_id_list = ctrConnection.startConnectionWithoutProxy(numOfConn, **params)
				else:
					if default:
						sm_id_list =  ctrConnection.startConnectionWithoutProxy(1, **params)
						sm_id_list += ctrConnection.startConnectionWithProxy(numOfConn-1, **params)
					else:
						sm_id_list = ctrConnection.startConnectionWithProxy(numOfConn, **params)
						
				for sm_id in sm_id_list:
					self.detailControl.setInfoItem( sm_id )
				
			elif numOfConn < 0: # remove conexões existentes.
				for sm_id in ctrConnection.stopConnections( numOfConn ):
					self.detailControl.removaItemConexao( sm_id )
					
			else: # mudança dinânica dos parametros das conexões.
				ctrConnection.update( **params)
				
	def updateInterface(self, evt):
		if self.streamLoading:
			# ATUALIZA A BARRA DE PROGRESSO GLOBAL
			last_progress = self.progressBar.GetValue()
			curr_progress = self.caluculePorcentagem(
			    self.manage.received_bytes(), self.manage.getVideoSize()
			)
			if last_progress != curr_progress: 
				self.progressBar.SetValue( curr_progress )
			
			# ATUALIZA O ESTADO DAS CONEXOES
			list_ctr = self.detailControl.GetListCtrl()			
			for smanager in self.manage.ctrConnection.getConnections():
				if not smanager.wasStopped(): # conexões paradas serão ignoradas
					rowIndex = self.detailControl.getRowIndex( smanager.ident )
					
					for colIndex, infokey in enumerate( manager.StreamManager.listInfo ):
						infoValue = self.info.get( smanager.ident, infokey )
						list_ctr.SetStringItem( rowIndex, colIndex, u"%s"%infoValue )
						
					# subprogressbar update
					block_size = self.manage.interval.get_block_size( smanager.ident )
					self.detailControl.listSubProgressBar[ rowIndex ].UpdateValue(smanager.numBytesLidos, block_size)
					self.detailControl.GetListCtrl().RefreshItem( rowIndex )
					
			# ATUALIZA A STATUSBAR
			infospeed = _(" V-Global: %s")% self.manage.velocidadeGlobal
			infotime = _(u"Duração: %10s")% self.manage.tempoDownload
			infoprog = _("Progresso: %10s")% str(self.manage.progresso())
			infoporc = "%5s"% self.manage.porcentagem()
			self.updateStatusBar(infospeed, infotime, infoprog, infoporc)
		else:
			status = self.startDown.get_status()
			if status is True: # iniciou com sucesso
				self.startStreamLoading()
				
			elif status is False: # houve um erro.	
				self.btnStartStopHandle()

	def hasUrl(self, url):
		""" verifica se a url já foi inserida no controlador de urls """
		for urlPlusTitle in self.controladorUrl.GetStrings():
			if self.urlManager.splitUrlDesc(urlPlusTitle)[0] == url:
				return True
		return False
		
	def getUrlOnly(self):
		""" retorna o valor do controlador no formato desejado """
		urlPlusTitle = self.controladorUrl.GetValue()
		return self.urlManager.splitUrlDesc(urlPlusTitle)[0]
	
	def startLoading(self, evt=None):
		if not self.streamLoading:
			url = self.getUrlOnly()
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
			except Exception as err:
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

		urlPlusTitle = self.urlManager.joinUrlDesc(url, title)
		self.controladorUrl.SetLabel(urlPlusTitle)

		if not self.hasUrl( url ):
			self.controladorUrl.Append(urlPlusTitle, title)
			
		# cancela o download atual
		if self.cfg_menu.as_bool('servidorAtivo') and not self.startServer():
			self.btnStartStopHandle(); return
			
		# adiciona as conexões padrão
		self.controleConexoes(default=True)
		
		# atualiza o player para o novo video
		self.reloadPlayer()
		
		# desativando controles, para impedir modifição da configuração ao iniciar a tranferência.
		self.barraControles.enableCtrs( False )

	def stopStreamLoading(self, evt=None):
		self.updateTimer.Stop()
		self.updateStatusBar("","","","")

		if self.streamLoading:
			# só terá efeito, quando usando arquivos temporários
			self.barraControles.questineUsuario()

			self.streamLoading = False
			self.stopExternalPlayer()
			
			if self.cfg_menu.as_bool('playerEmbutido'):
				self.playerWin.pause()
			
			# parando todas as conexões criadas
			self.manage.ctrConnection.stopAllConnections()
			self.detailControl.removaTodosItens()
			self.manage.stop_streamers()
			
			#zera a barra de progresso
			self.progressBar.SetValue(0.0)
			
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
#if __name__ == "__main__":
#	# dir com os diretórios do projeto
#	os.chdir( pardir )
#	app = wx.App(0)
#	BaixeAssistaWin()
#	app.MainLoop()
