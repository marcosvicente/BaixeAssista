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

# necess�rio para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )

# m�dulos do projeto
import manager
import updater

# Instalando a tradu��o
manager.installTranslation()

import browser, proxy

# m�dulos do pacote window
import updatedialog
import ctrbar
import ipSearch
import wbugs
import dialog
import detail
import movie

# A vers�o ser� mantida pelo m�dulo principal
PROGRAM_VERSION = manager.PROGRAM_VERSION
########################################################################

class StartDown(threading.Thread):
	""" Coleta informa��es iniciais necess�rias para 
	baixar o video, como tamanho e tit�tulo v�deo"""

	def __init__(self, mainWin):
		threading.Thread.__init__(self)
		self.manage = mainWin.manage
		self.mainWin = mainWin
		self._status = self.status = None
		self.max = 8

		# di�logo informativo
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
		""" cancela a opera��o de download atual """
		self.manage.canceledl()
		self.status = False

		try: self.diag.Destroy()
		except: pass

		if hasattr(evt,"Skip"): evt.Skip()

	def startFailed(self, evt):
		self.status = False
		evt.Skip()

	def get_status(self):
		""" indica se tudo iniciou corretamente ou n�o """
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
		""" BaixeAssistaWin: representa��o principal da interface gr�fica """
		wx.Frame.__init__(self, None, wx.ID_ANY, "BaixeAssista v%s"%PROGRAM_VERSION, size=(800,600))
		self.SetIcon( self.getMovieIcon() )
		
		# configura��es gerais da aplica��o
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

		# criando a barra de ferramentas: player, conex�es, navegador
		self.barraControles = ctrbar.BarraControles(self, -1)
		
		self.progressBar = wx.Gauge(self.statusBar )
		self.Bind(wx.EVT_MAXIMIZE, self.updateProgressBar)
		self.Bind(wx.EVT_UPDATE_UI, self.updateProgressBar)
		self.Bind(wx.EVT_SIZING, self.updateProgressBar)
		#------------------------------

		mainVSizer.Add(painelEntradaUrls, 0, wx.EXPAND)
		mainVSizer.Add(self.barraControles, 1, wx.EXPAND)

		# aplicando as configura��es
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
		""" Termina salvando as configura��es e fechando o servidor """
		# caso um arquivo esteja sendo baixado e for pressionado
		if self.streamLoading: self.btnStartStopHandle()

		# Menu: atualiza��o autom�tica
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

		self.salveConfigs() # salva as configura��es

		# destr�i a janela completamente
		self.Destroy()

	def apliqueConfigs(self):
		""" restaura a interface para o �ltimo estado de configura��o """
		self.cfg_controles = self.configs["Controles"]
		self.cfg_locais = self.configs['Locais']
		self.cfg_menu = self.configs['Menus']

		is_active = self.cfg_controles.as_int("numConexoesAtivas")
		self.barraControles.nConnectionControl.SetValue( is_active )

		# controle de arquivo temp
		is_temp = self.cfg_controles.as_bool("tempFileControlValue")
		self.barraControles.tempFileControl.SetValue( is_temp )

		# controle op��es de arquivos temp
		opt = self.cfg_controles.as_int("tempFileOptControlValue")
		self.barraControles.tempFileOptControl.Enable( is_temp )
		self.barraControles.tempFileOptControl.SetSelection( opt )

		# qualidade do arquivo de video
		vquality = self.cfg_controles.as_int("videoQualityControlValue")
		self.barraControles.videoQualityControl.SetSelection( vquality )

		# n�mero inicial de divis�es do arquivo de video
		value = self.cfg_controles.as_int("numDivStreamControlValue") 
		self.barraControles.numDivStreamControl.SetValue( value)

		# taxa limite de download para sub-conex�es
		value = self.cfg_controles.as_int("rateLimitControlValue")
		self.barraControles.rateLimitControl.SetValue( value )

		# tempo m�ximo de espera, por uma resposta, de uma conex�o
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
		# procurando uma nova vers�o automaticamente.
		if autoSearch: self.findUpdateNow(noInfo=True)
		self.menuUpdate.Check(500, autoSearch)

		# �ltimas configura��es da janela
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
			print "Erro[MainWin] salvando arquivo de configura��o!!!"

	def crieBarraMenus(self):
		""" cria a barra de menus e os menus usados na interface pricipal """
		# menus de controle do player
		self.menuPlayer = wx.Menu()
		self.menuPlayer.Append(100, _("Usar player embutido"), kind = wx.ITEM_RADIO)
		self.menuPlayer.Append(102, _("Usar player externo"), kind = wx.ITEM_RADIO)
		self.menuPlayer.AppendSeparator()
		self.menuPlayer.Append(103, _("Recarregar player"))
		self.menuPlayer.Append(104, _("Escolher outro player"))

		# menus de edi��o
		self.menuEditar = wx.Menu()
		self.menuEditar.Append(200, _("Videos"))
		self.menuEditar.Append(201, _("Atualizar lista de ips"))
		
		# menus de a��o
		self.menuAcoes = wx.Menu()
		self.menuAcoes.Append(300, _("Ligar servidor"), kind = wx.ITEM_CHECK)
		self.menuAcoes.Append(301, _("Tela cheia"))
		self.menuAcoes.Check(300, True)

		# menu linguagem
		self.menuLinguagem = wx.Menu()
		self.menuLinguagem.Append(700, _(u"Portugu�s"), kind = wx.ITEM_RADIO)
		self.menuLinguagem.Append(701, _(u"Ingl�s"), kind = wx.ITEM_RADIO)
		self.menuLinguagem.Append(702, _("Espanhol"), kind = wx.ITEM_RADIO)
		self.menuLinguagem.language_codes = {700: "pt_BR", 701: "en", 702: "es"}

		# ativa a �ltima linguagem selecionada no menu.
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
		self.menuAjuda.AppendMenu(401, _(u"Atualiza��o"), self.menuUpdate)
		self.menuAjuda.AppendSeparator()
		self.menuAjuda.Append(402, _(u"Relat�rio de erros"))
		self.menuAjuda.AppendSeparator()
		self.menuAjuda.Append(403, _("Sobre"))

		# cria a barra de menus a adiciona os menus
		self.barraMenus = wx.MenuBar()
		self.barraMenus.Append(self.menuPlayer, _("Players"))
		self.barraMenus.Append(self.menuEditar, _("Editar"))
		self.barraMenus.Append(self.menuAcoes, _(u"A��es"))
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
		msg = _(u"A nova linguagem s� ser� aplicada, ap�s reiniciar o programa.")
		dlg = GMD.GenericMessageDialog(self, msg, _("Linguagem modificada"), wx.ICON_INFORMATION|wx.OK)
		dlg.ShowModal(); dlg.Destroy()

	def formHandle(self, evt):
		""" cria um formul�rio de informa��o de bugs. 
		o formul�rio � preenchido pelo usu�rio. """
		win = wbugs.BugInfo(self, _(u"Relat�rio de erros"))
		
	def aboutProgram(self, evt):
		# First we create and fill the info object
		info = wx.AboutDialogInfo()
		info.Name = "BaixeAssista"
		info.Version = "v%s"%PROGRAM_VERSION
		info.Copyright = "(C) 2012 Programmers and Coders Everywhere"

		description = u"".join([
			_(u"O programa BaixeAssista busca dar uma solu��o amig�vel a usu�rios"),
			_(u" que se interessam por filmes postados na internet. Como h� muita burocracia"),
			_(u" e empecilhos para assistir a um �nico filme, o programa tentar� resgatar para"),
			_(u" o usu�rio o que mais interessa, a divers�o. Chega de popup, propagandas, limites"),
			_(u" de tempo para assistir filmes.")
		])
		info.Description = wordwrap(description, 400, wx.ClientDC(self))
		info.WebSite = ("http://code.google.com/p/gerenciador-de-videos-online/", "Projeto BaixeAssista")
		info.Developers = ["Alex [geniofuturo@gmail.com]"]

		licenseText = u"".join([
			_(u"Esse programa � de dom�nio p�blico. Isso significa que voc� poder�"),
			_(u" copi�-lo, modific�-lo sem restri��o alguma.")
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
		# Iniciando ao procura por uma nova vers�o do programa.
		rel = updater.Release()
		status, msg = rel.search()
		
		if status is True:
			msg += _(u"\nPressione OK para ir a p�gina de download.")
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
		# Inicia a procura por pacotes de atualiza��o.
		upd = updater.Updater(packetVersion = self.configs["Controles"]["packetVersion"])
		
		if upd.search() is True:
			# come�a o download da atualiza��o
			sucess, msg = upd.download()
			
			if sucess is True:
				language = self.configs["Menus"]["language"]
				# texto informando as mudan�as que a nova atualiza��o fez.
				changes = upd.getLastChanges( language)
				
				# aplica a atualiza��o
				sucess, msg = upd.update()
				
				# remove todos os arquivos
				upd.cleanUpdateDir()
				
				if sucess is True:
					## ======================================================
					newVersion = upd.getNewVersion()
					
					if newVersion: # guarda a vers�o do pacote recebido.
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
		# informa o usu�rio da nova atualiza��o
		# o dialogo fica inst�vel ao ser chamado do thread de atualiza��o.
		isauto = self.configs["Controles"].as_bool("autoUpdateSearch")

		if isauto: titleChunk = _(u"Ativada)")
		else: titleChunk = _(u"Desativada)")

		title = _(u"Novas atualiza��es recebidas! (Atualiza��o autom�tica - ") + titleChunk
		dlgUpdate = updatedialog.UpdateDialog(self, title)

		dlgUpdate.CenterOnParent()
		dlgUpdate.setInfo( msg )
		dlgUpdate.SetFocus()

		# informa o grupo de mudan�as
		dlgUpdate.writeText( changesText )
		dlgUpdate.Show(True)

	def findUpdateNow(self, evt=None, noInfo=False):
		""" inicia a procura por atualiza��es """

		if hasattr(evt, "GetId") and evt.GetId() == 500:
			isChecked = self.menuUpdate.IsChecked(500)
			self.configs["Controles"]["autoUpdateSearch"] = isChecked
			return # atualiza o estado da atualiza��o autom�tica.

		t = threading.Thread(target=self.searchUpdateNow, args=(noInfo,))
		t.start()
	
	def startServer(self): # tenta iniciar o servidor
		if not manager.Server.running:
			if not manager.Manage.forceLocalServer(port = 8015):
				msg = u"".join([
					_(u"O servidor falhou ao tentar iniciar no endere�o: http://localhost:8080"),
					_(u"\nDesmarque a op��o no menu \"A��es / Ligar servidor\" para iniciar o download."),
					_(u"\n\nNote que sem o servidor o player n�o funcionar�.")
				])
				dlg = GMD.GenericMessageDialog(self, msg, _("Erro iniciando o servidor."), wx.ICON_ERROR|wx.OK)
				dlg.ShowModal(); dlg.Destroy()
		return manager.Server.running
		
	def activeServer(self, evt):
		""" inicia ou p�ra o servidor, com base no menu de controle """
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
			self, message = _(u"Escolha o local do player (execut�vel)"),
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
		""" p�ra a execu��o do player externo """
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
			# o player iniciar� automaticamente se baixando a stream
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
			
			# se n�o houver um caminho v�lido para o player externo
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
		self.btnStartStop.SetToolTip(wx.ToolTip( _(u"Come�a ou p�ra a transfer�ncia do arquivo de v�deo") ))
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
		# restaurando o �ltimo estado de cofigura��o
		ipsh.setLastConfigs()
		
	def controleConexoes(self, evt=None, default=False):
		""" Adiciona ou remove conex�es """
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
			if numOfConn > 0: # adiciona novas conex�es.
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
				
			elif numOfConn < 0: # remove conex�es existentes.
				for sm_id in ctrConnection.stopConnections( numOfConn ):
					self.detailControl.removaItemConexao( sm_id )
					
			else: # mudan�a din�nica dos parametros das conex�es.
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
				if not smanager.wasStopped(): # conex�es paradas ser�o ignoradas
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
			infotime = _(u"Dura��o: %10s")% self.manage.tempoDownload
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
		""" verifica se a url j� foi inserida no controlador de urls """
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
			# op��o para uso de arquivo tempor�rio
			tempfile = self.barraControles.tempFileControl.GetValue()
			# op��o de qualidade do v�deo
			vquality = self.barraControles.videoQualityControl.GetSelection()
			# op��o para o n�mero de divis�es iniciais da stream de v�deo
			maxsplit = self.barraControles.numDivStreamControl.GetValue()
			try:
				# inicia o objeto princial: main_obj
				self.manage = manager.Manage( url, tempfile = tempfile, videoQuality = (vquality+1), #0+1=1
								              maxsplit = maxsplit)
			except Exception as err:
				self.btnStartStopHandle()
				
				# O erro principal seria uma url inv�lida.
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
			
		# adiciona as conex�es padr�o
		self.controleConexoes(default=True)
		
		# atualiza o player para o novo video
		self.reloadPlayer()
		
		# desativando controles, para impedir modifi��o da configura��o ao iniciar a tranfer�ncia.
		self.barraControles.enableCtrs( False )

	def stopStreamLoading(self, evt=None):
		self.updateTimer.Stop()
		self.updateStatusBar("","","","")

		if self.streamLoading:
			# s� ter� efeito, quando usando arquivos tempor�rios
			self.barraControles.questineUsuario()

			self.streamLoading = False
			self.stopExternalPlayer()
			
			if self.cfg_menu.as_bool('playerEmbutido'):
				self.playerWin.pause()
			
			# parando todas as conex�es criadas
			self.manage.ctrConnection.stopAllConnections()
			self.detailControl.removaTodosItens()
			self.manage.stop_streamers()
			
			#zera a barra de progresso
			self.progressBar.SetValue(0.0)
			
			self.manage.delete_vars()
			self.manage = None

		elif hasattr(self.startDown, "canceledl"):
			self.startDown.canceledl()

		# valor "None" � para indicar objeto n�o inciado.
		self.startDown = None

	def setUrlTooltip(self, evt):
		controladorUrl = evt.GetEventObject()
		helpText = controladorUrl.GetClientData( controladorUrl.GetSelection() )
		self.controladorUrl.SetToolTip( wx.ToolTip( helpText ) )

	def setUrlHelpText(self, h):
		self.controladorUrl.SetToolTip(wx.ToolTip( h ))
		
########################################################################
#if __name__ == "__main__":
#	# dir com os diret�rios do projeto
#	os.chdir( pardir )
#	app = wx.App(0)
#	BaixeAssistaWin()
#	app.MainLoop()
