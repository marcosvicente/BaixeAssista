# -*- coding: ISO-8859-1 -*-

import os
import sys
import wx
import time
import wx.aui
import wx.animate
import wx.html2 as Webview
import wx.lib.agw.genericmessagedialog as GMD
import wx.lib.agw.flatnotebook as FNB

# configurando o ambiente para a execução do script.
import main.environ
main.environ.setup((__name__ == "__main__"))

from main.app import generators
from main import settings
from main.app import models

SEARCH_ENGINE = "http://www.google.com.br/webhp?hl=pt-BR"

with open(os.path.join(settings.STATIC_PATH,"js","ml.js"), "r") as js_file:
	JS_LINK_MONITOR = js_file.read()

with open(os.path.join(settings.STATIC_PATH,"js","el.js"), "r") as js_file:
	JS_LINK_EXTRACTOR = js_file.read()
	
##############################################################################
class HistoryUrl(object):
	""" Classe criada com o objetivo de corrigir o problema de histórico 
	atualmente encontrado na bliblioteca wxpython v2.9.3.1"""
	#----------------------------------------------------------------------
	def __init__(self, **params):
		""" params={}
		max_url: default=50
		webview: referêcia para o objeto webview
		"""
		self.current = ""
		self.browsing = False
		self.params = params
		self.history = []
		self.index = 0

	def append(self, url):
		if self.current:
			## criando um novo ramo - descarta o final
			## [a, b, |c, d|- ramo descartado]
			##	 |
			##	 [e, f, g]- ramo criado, apartir de b
			index = self.history.index(self.current, self.index)
			self.history = self.history[ :index+1]
			self.index = index + 1
			self.history.append( url )
		else:
			self.history.append( url )
			self.index = len(self.history)-1

		if len(self.history) > self.params.get("max_url", 50) and self.index != 0:
			self.history.pop(0)

		self.current = url

	def isBrowsing(self):
		return self.browsing

	def setBrowsing(self, flag):
		self.browsing = flag

	def CanGoBack(self):
		""" verifica se é possível voltar no histórico """
		return self.history.index(self.current, self.index) > 0

	def CanGoForward(self):
		""" verifica se pode avançar no histórico """
		return self.history.index(self.current, self.index) < (len(self.history)-1)

	def GoBack(self):
		""" navega para a página anterior a páginal atual """
		index = self.history.index(self.current, self.index) - 1
		if index < 0: return

		url = self.history[ index ]
		self.params["webview"].LoadURL( url )

		self.current = url
		self.index = index

	def GoForward(self):
		""" navega para próxima página do histórico """
		index = self.history.index(self.current, self.index) + 1
		if index > (len(self.history)-1): return

		url = self.history[ index ]
		self.params["webview"].LoadURL( url )

		self.current = url
		self.index = index
		
##############################################################################
class TooBarGET(object):
	def getInputLocation(self):
		return self.location
	
	def getInputEmbed(self):
		return self.embed
	
	def getBtnGoPrevious(self):
		return self.btnGoPrevious
	
	def getBtnGoNext(self):
		return self.btnGoNext
	
	def getBtnSearch(self):
		return self.btnSearch
	
	def getBtnRefresh(self):
		return self.btnRefresh
	
	def getBtnStop(self):
		return self.btnStop
	
	def getBtnAddUrl(self):
		return self.btnAddUrl
	
	def getBtnDelUrl(self):
		return self.btnDelUrl
	
	def getSpinZoomPage(self):
		return self.spinZoomPage
	
##############################################################################
class ToolBar(wx.Panel, TooBarGET):
	def __init__(self, parent=None, Id=-1):
		super(ToolBar, self).__init__(parent, Id, style=wx.RAISED_BORDER)
		self.parent = parent
		
		self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.mainSizer.Add(self._setupView(), 1, wx.EXPAND|wx.ALL, 2)
		
		self.SetSizer(self.mainSizer)
		self.SetAutoLayout(True)
		
	def _createButtons(self):
		btnFlexGridSizer = wx.FlexGridSizer(1, 8, 0, 5)
		## hSizer = wx.BoxSizer(wx.HORIZONTAL)
		
		# botão go_back
		imgpath = os.path.join(settings.IMAGES_DIR, "go-previous24x24.png")
		
		bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)
		self.btnGoPrevious = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
		
		self.btnGoPrevious.SetToolTipString("Go Back")		
		btnFlexGridSizer.Add(self.btnGoPrevious, 0, wx.LEFT, 2)
		# ---------------------------------------------------------------------------------
		
		# botão go_forward
		imgpath = os.path.join(settings.IMAGES_DIR, "go-next24x24.png")
		
		bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)
		self.btnGoNext = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
		
		self.btnGoNext.SetToolTipString("Go Forward")		
		btnFlexGridSizer.Add(self.btnGoNext)
		# ---------------------------------------------------------------------------------
		
		# botão search
		imgpath = os.path.join(settings.IMAGES_DIR, "search-computer24x24.png")
		
		bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)
		self.btnSearch = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
		
		self.btnSearch.SetToolTipString("Google Search")
		btnFlexGridSizer.Add(self.btnSearch)
		# ---------------------------------------------------------------------------------
		
		# botão reflesh
		imgpath = os.path.join(settings.IMAGES_DIR, "view-refresh24x24.png")
		
		bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)
		self.btnRefresh = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
		
		self.btnRefresh.SetToolTipString("Reflesh")
		btnFlexGridSizer.Add(self.btnRefresh)
		# ---------------------------------------------------------------------------------
		
		# botão Stop loading
		imgpath = os.path.join(settings.IMAGES_DIR, "process-stop24x24.png")
		
		bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)
		self.btnStop = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
		
		self.btnStop.SetToolTipString("Stop")
		btnFlexGridSizer.Add(self.btnStop)
		# ---------------------------------------------------------------------------------
		
		# botão adicionar um novo site
		imgpath = os.path.join(settings.IMAGES_DIR, "list-add24x24.png")
		
		bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)
		self.btnAddUrl = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
		
		self.btnAddUrl.SetToolTipString(_(u"Permite adicionar um novo site de filmes\nà lista de sites favoritos"))
		btnFlexGridSizer.Add(self.btnAddUrl)
		# ---------------------------------------------------------------------------------
		
		# botão remover site
		imgpath = os.path.join(settings.IMAGES_DIR, "list-remove24x24.png")
		
		bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)
		self.btnDelUrl = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
		
		self.btnDelUrl.SetToolTipString(_(u"Use para remover sites, da lista de sites favoritos."))
		btnFlexGridSizer.Add(self.btnDelUrl)
		# ---------------------------------------------------------------------------------

		self.spinZoomPage = wx.SpinButton(self, -1, style=wx.SP_VERTICAL)
		self.spinZoomPage.SetMinSize((-1, self.btnDelUrl.GetSize().y))
		self.spinZoomPage.SetToolTip(wx.ToolTip("Zoom"))
		
		self.spinZoomPage.SetValue( Webview.WEB_VIEW_ZOOM_MEDIUM )
		self.spinZoomPage.SetRange( Webview.WEB_VIEW_ZOOM_TINY, Webview.WEB_VIEW_ZOOM_LARGEST)
		
		btnFlexGridSizer.Add(self.spinZoomPage)
		return btnFlexGridSizer
	
	def _setupView(self):
		hsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		hsizer.Add(self._inputLocationUrl(), 1, wx.EXPAND)
		hsizer.Add(self._createButtons(), 0, wx.LEFT|wx.RIGHT, 20)
		hsizer.Add(self._inputEmbedUrls(), 1, wx.EXPAND)
		
		return hsizer
	
	def _inputLocationUrl(self):
		hSizer = wx.BoxSizer(wx.HORIZONTAL)
		
		locationInfo = wx.StaticText(self, -1, _("Local:"))
		hSizer.Add(locationInfo, 0, wx.ALIGN_CENTER|wx.RIGHT|wx.LEFT, 5)
		
		# controle usado para entrada de urls
		self.location = wx.ComboBox(self, -1, style=wx.CB_DROPDOWN|wx.PROCESS_ENTER)
		self.location.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Arial'))
		
		hSizer.Add(self.location, 1, wx.EXPAND)
		return hSizer
		
	def _inputEmbedUrls(self):
		hSizer = wx.BoxSizer(wx.HORIZONTAL)
		
		embendInfo = wx.StaticText(self, -1, "Embed:")
		hSizer.Add(embendInfo, 0, wx.ALIGN_CENTER|wx.RIGHT|wx.LEFT, 5)
		
		# controle usado para entrada de urls embutidas
		self.embed = wx.ComboBox(self, -1, style=wx.CB_DROPDOWN|wx.PROCESS_ENTER)
		self.embed.SetFont( wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Arial'))
				
		hSizer.Add(self.embed, 1, wx.EXPAND|wx.RIGHT, 2)
		return hSizer
	
##############################################################################
class Browser(wx.Panel):
	def __init__(self, parent, mainWindow=None):
		wx.Panel.__init__(self, parent, -1)
		self.mainWin = mainWindow

		# sizer principal do painel
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		self.progressAni = wx.animate.Animation(os.path.join(settings.IMAGES_DIR,"progress.gif"))
		self._ImageList = wx.ImageList(*self.progressAni.GetSize())
		
		for index in range(self.progressAni.GetFrameCount()):
			img = self.progressAni.GetFrame( index )
			self._ImageList.Add( img.ConvertToBitmap() )

		self.objects = models.Browser.objects # queryset
		self.historySites = [] # preenchido ao abrir um novo site
		self.current = self.getLastSite()
		
		self.rmenuNewTab = wx.Menu()
		item = wx.MenuItem(self.rmenuNewTab, wx.ID_ANY, _("Adicionar nova aba"), "")
		self.Bind(wx.EVT_MENU, lambda evt: self.addNewTab( SEARCH_ENGINE ), item)
		self.rmenuNewTab.AppendItem(item)
		
		item = wx.MenuItem(self.rmenuNewTab, wx.ID_ANY, _("Fechar"), "")
		self.Bind(wx.EVT_MENU, self.closeCurrentPage, item)
		self.rmenuNewTab.AppendItem(item)
		
		self.abasControl = FNB.FlatNotebook(self, wx.ID_ANY, agwStyle=FNB.FNB_VC8) #wx.aui.AuiNotebook(self)
		self.abasControl.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.setTabFocus)
		self.abasControl.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnTabClose)
		self.abasControl.SetRightClickMenu( self.rmenuNewTab )
		self.abasControl.SetImageList( self._ImageList )
		
		# construção da barra de ferramentas
		self.toolBar = ToolBar(self)
		
		# aba padrão - sempre criada
		self.addNewTab(self.current, True)

		# abas secundárias
		for site in self.getHistorySites():
			if not site == self.current:
				self.addNewTab(site)
		
		self.setupToolBar()
		
		self.mainSizer.Add(self.toolBar, 0, wx.EXPAND|wx.ALL, 2)
		self.mainSizer.Add(self.abasControl, 1, wx.EXPAND)
		
		self.SetSizer(self.mainSizer)
		self.SetAutoLayout(True)
		
	def setupToolBar(self):
		location = self.toolBar.getInputLocation()
		for site in self.getSites(): location.Append(site)
		
		location.SetLabel(self.current)
		
		self.Bind(wx.EVT_COMBOBOX, self.OnLocationSelect, location)
		self.Bind(wx.EVT_TEXT_ENTER, self.OnLocationEnter, location)
		## Embed
		self.Bind(wx.EVT_COMBOBOX, self.embedHandle, self.toolBar.getInputEmbed())
		self.Bind(wx.EVT_TEXT_ENTER, self.embedHandle, self.toolBar.getInputEmbed())		
		## Previous
		self.Bind(wx.EVT_BUTTON, self.OnPrevPageButton, self.toolBar.getBtnGoPrevious())
		self.Bind(wx.EVT_UPDATE_UI, self.OnCheckCanGoBack, self.toolBar.getBtnGoPrevious())
		## Next
		self.Bind(wx.EVT_BUTTON, self.OnNextPageButton, self.toolBar.getBtnGoNext())
		self.Bind(wx.EVT_UPDATE_UI, self.OnCheckCanGoForward, self.toolBar.getBtnGoNext())
		## Search
		self.Bind(wx.EVT_BUTTON, self.OnSearchPageButton, self.toolBar.getBtnSearch())
		## Reflesh
		self.Bind(wx.EVT_BUTTON, self.OnRefreshPageButton, self.toolBar.getBtnRefresh())
		## Stop
		self.Bind(wx.EVT_BUTTON, self.OnStopButton, self.toolBar.getBtnStop())
		## Add
		self.Bind(wx.EVT_BUTTON, self.addNewMovieSite, self.toolBar.getBtnAddUrl())
		## Del
		self.Bind(wx.EVT_BUTTON, self.removeMovieSite, self.toolBar.getBtnDelUrl())
		## Zoom
		self.Bind(wx.EVT_SPIN, self.setPageZoom, self.toolBar.getSpinZoomPage())
		
	def closeCurrentPage(self, evt):
		""" Fecha a página pelo menu """
		self.abasControl.DeletePage(self.abasControl.GetSelection())
		
	def getLastSite(self):
		try: return self.objects.get(
			site=None, historysite=None).lastsite
		except: return ""

	def addLastSite(self, site):
		try: query = self.objects.get(site=None, historysite=None)
		except: query = models.Browser()
		query.lastsite = site
		query.save()

	def getHistorySites(self):
		return [query.historysite
				for query in self.objects.filter(
					site=None, lastsite=None)
				]
	def addHistorySites(self, sites):
		""" guarda o histórico de urls """
		queries = self.objects.filter(site=None, lastsite=None)
		queries.delete() # remove referências antigas.
		for site in sites:
			broser = models.Browser(historysite=site)
			broser.save()

	def addSite(self, site):
		models.Browser(site=site).save()

	def getSites(self):
		""" retorna uma lista com todos os sites adicionados """
		return [query.site
				for query in self.objects.filter(
					lastsite=None, historysite=None)
				]

	def __del__(self):
		self.addHistorySites(self.historySites)
		self.addLastSite(self.current)

	def addNewTab(self, url, defaut=False):
		""" abre uma nova aba de navegação """
		self.Freeze()
		
		webview = Webview.WebView.New( self.abasControl)

		# gera histórico das urls navegadas. Usado pelos botões de navegação
		webview.historyUrl = HistoryUrl(webview=webview)
		webview.historyUrl.append(url)

		webview.SetZoomType( Webview.WEB_VIEW_ZOOM_TYPE_LAYOUT )
		self.setPageZoom()

		webview.Url = url

		# variáveis usadas na animação de carregamento da página
		webview.loading = True
		webview.progressFrameNum = 0
		webview.isNullBitmap = False
		webview.timeCount = time.time()
		webview.JS_SCRIPT_RUN = False

		# events
		self.Bind(Webview.EVT_WEB_VIEW_NEWWINDOW, self.OnWebViewNewWindow, webview)
		self.Bind(Webview.EVT_WEB_VIEW_NAVIGATING, self.OnWebViewNavigating, webview)
		self.Bind(Webview.EVT_WEB_VIEW_LOADED, self.OnWebViewLoaded, webview)
		self.Bind(Webview.EVT_WEB_VIEW_TITLE_CHANGED, self.OnWebViewTitleChange, webview)
		
		# add new page
		self.abasControl.AddPage(webview, "Loading...", select = defaut)
		webview.LoadURL(url)

		self.toolBar.getInputLocation().SetToolTip(wx.ToolTip(url))

		# guarda com o objetivo de gera uma lista de histórico
		self.historySites.append(url)
		self.Thaw()
		
	def setShortTitle(self, title, titleSize=25):
		if len(title) > titleSize: title = title[:titleSize]+"..."
		return title

	def pageExist(self, url):
		""" abre uma nova janela(para uma url) numa aba, somente uma vez """
		for pageIndex in range(self.abasControl.GetPageCount()):
			win = self.abasControl.GetPage( pageIndex )
			if win.Url == url: return True
		return False

	def OnWebViewTitleChange(self, evt):
		win = evt.GetEventObject() # objeto webview
		title = win.GetCurrentTitle() or "Loading..."
		title = self.setShortTitle( title )

		# procura pelo indice do objeto webview
		for index in range(self.abasControl.GetPageCount()):
			if win == self.abasControl.GetPage(index):
				self.abasControl.SetPageText(index, title)

	def setTabFocus(self, evt):
		""" Troca o controlador de navegação """
		location = self.toolBar.getInputLocation()
		self.webview = self.abasControl.GetCurrentPage()
		location.SetValue( self.webview.GetCurrentURL())
		location.SetToolTip(wx.ToolTip(self.webview.GetCurrentURL()))
		evt.Skip()
		
	def progressAnimate(self):
		""" atualiza a animação de carregamento de todas a páginas ainda não carregadas """
		num_of_pages = self.abasControl.GetPageCount()
		num_of_frames = self.progressAni.GetFrameCount()
		
		for index in range(num_of_pages):
			webview = self.abasControl.GetPage(index)
			if webview.loading:
				if (time.time() - webview.timeCount) > 0.1:
					webview.timeCount = time.time()
					
					# limita o contador de frames ao numero suportado por animate
					if webview.progressFrameNum == num_of_frames:
						webview.progressFrameNum = 0
						
					# muda o bitmap de animação
					self.abasControl.SetPageImage(index, webview.progressFrameNum)
					webview.progressFrameNum += 1
					
			elif not webview.isNullBitmap: # fixa o o bitmap nulo somente uma vez
				self.abasControl.SetPageImage(index, -1)
				webview.isNullBitmap = True

	def setNavStopLoading(self, webview):
		""" atualiza o evento de parada do carregamento da página """
		webview.loading = False
		
	def OnTabClose(self, evt):
		""" impede que todas as páginas sejam fechadas """
		win = evt.GetEventObject()
		num_of_pages = win.GetPageCount()
		if num_of_pages > 1:
			url = win.GetCurrentPage().Url
			try:
				index = self.historySites.index(url)
				
				# verifica a posição da página
				if (num_of_pages-index-1)== 0: index=index-1
				else: index=index+1
				
				self.current = win.GetPage(index).Url
				self.historySites.remove( url )
			except: pass
		else: # veta o fechamento da primeira tabela(indice 1).
			evt.Veto()
	
	def setPageZoom(self, evt=None):
		""" configura o nível de zoom do layout página com o foco """
		try: self.webview.SetZoom(self.toolBar.getSpinZoomPage().GetValue())
		except: pass # erro ao tentar configurar o mesmo nível de zoom
	
	def addNewMovieSite(self, event):
		dlg = wx.TextEntryDialog(self,
			 _("Entre com a url completa do site"), 
			 _("Adicione um novo site de filmes"), 
			 "", wx.OK|wx.CANCEL)
		dlg.CentreOnParent()
		
		if dlg.ShowModal() == wx.ID_OK:
			local = dlg.GetValue()
			if not local: return
			
			if not local.startswith("http://"): local = "http://" + local
			if not local.endswith("/"): local += "/"
			
			# verifica se já foi adicionado.
			if self.objects.filter(site=local).count():
				dlg = GMD.GenericMessageDialog(self,
				   _(u"O site dado já consta na lista de sites atual"), 
				   _(u"Atenção!"), wx.ICON_WARNING|wx.OK )
				dlg.ShowModal(); dlg.Destroy()
			else:
				# adicionando à base de dados.
				self.addSite( local )
				
				if not self.hasUrl( local ):
					self.toolBar.getInputLocation().Append( local)
		dlg.Destroy()
		
	def removeMovieSite(self, evt):
		sites = self.getSites()
		dlg = wx.MultiChoiceDialog(self, 
		   _(u"Selecione uma ou mais urls e pressione 'OK' para removê-las."),
		   _(u"Sites para remoção."), sites)
		
		if (dlg.ShowModal() == wx.ID_OK):
			selections = dlg.GetSelections()
			if len(selections) > 0:
				for index in selections:
					query = self.objects.get(site=sites[index])
					query.delete()
		dlg.Destroy()

	def OnSearchPageButton(self, event):
		self.webview.LoadURL( SEARCH_ENGINE )
		# limpa o controle de url embutidas
		# porque uma nova página está sendo carregada.
		self.toolBar.getInputEmbed().Clear()

	def ShutdownDemo(self):
		# put the frame title back
		if self.mainWin: self.mainWin.SetTitle(self.titleBase)

	def embedHandle(self, event):
		""" atribui a url do controle de url embutidas para
		o controle de transferência de arquivos """
		url = self.toolBar.getInputEmbed().GetStringSelection()
		if url: self.mainWin.controladorUrl.SetValue( url[4:] )
		self.webview.SetFocus() # passa o foco para o navegador
		
	def custom_enumerate(self, args):
		""" retorna a seguencia de strings com sua posição, na lista, concatenada ['[1] abc','[2] def']"""
		newargs = []; index_str = "[%s] "
		for index, arg in enumerate(args, 1):
			if arg[1].isdigit(): arg=arg[4:]
			newargs.append("%s%s"%((index_str%index), arg))
		return newargs

	def controleFluxoUrlsEmbutidas(self):
		embed = self.toolBar.getInputEmbed()
		items = embed.GetItems()
		if len(items) > 8:
			embed.Set( self.custom_enumerate(items[2:]) )
		else:
			urlsIndexadas = self.custom_enumerate(items)
			embed.Set( urlsIndexadas )
		embed.SetSelection(embed.GetCount()-1)
		
	def OnWebViewNavigating(self, event):
		""" Controla o começo do carregamento de um recurço """
		url = event.GetURL()
		
		webview = event.GetEventObject()
		webviewUrl = webview.GetCurrentURL()
		embed = self.toolBar.getInputEmbed()
		
		# configura os dados para a animação da progress animate
		webview.loading, webview.isNullBitmap = True, False
		
		if webviewUrl != webview.Url and webviewUrl.startswith("http"):
			if not webview.historyUrl.isBrowsing():
				webview.historyUrl.append( webviewUrl )

			webview.JS_SCRIPT_RUN = False
			embed.Clear()
			
			webview.historyUrl.setBrowsing(False)

			self.historySites.remove( webview.Url )
			self.historySites.append( webviewUrl )
			webview.Url = webviewUrl

			if webview == self.webview:
				location = self.toolBar.getInputLocation()
				location.SetLabel( webviewUrl )
				location.SetToolTip(wx.ToolTip( webviewUrl ))
				
			self.current = webviewUrl
		
		if not webview.JS_SCRIPT_RUN and webviewUrl.startswith("http"):
			webview.RunScript( JS_LINK_MONITOR )
			webview.RunScript( JS_LINK_EXTRACTOR )
			webview.JS_SCRIPT_RUN = True
			
		if generators.Universal.has_site(url) and hasattr(self.mainWin, "controladorUrl"):
			is_embed = generators.Universal.isEmbed(url)
			url = generators.Universal.get_inner_url(url)
			
			if not is_embed:
				self.mainWin.controladorUrl.SetValue( url )
				self.setNavStopLoading( webview )
				event.Veto() # cancela o carregamento.
			else:
				embed.SetLabel( url ); embed.Append( url )
				self.controleFluxoUrlsEmbutidas()

	def OnWebViewNewWindow(self, event):
		""" Controla a abertura de novas janelas """
		url = event.GetURL()
		
		prev_title = self.webview.GetCurrentTitle()
		self.webview.RunScript("document.title = clickedLink;")
		clickedLink = self.webview.GetCurrentTitle()
		
		try: clickedLink = clickedLink.decode("utf-8")
		except: clickedLink = clickedLink.encode("utf-8")
		
		self.webview.RunScript("document.title = '%s';" % prev_title)
		isValid = generators.Universal.has_site(url)
		
		if isValid and hasattr(self.mainWin, "controladorUrl"):
			is_embed = generators.Universal.isEmbed(url)
			url = generators.Universal.get_inner_url(url)

			if not is_embed:
				self.mainWin.controladorUrl.SetValue( url )
			else:
				embed = self.toolBar.getInputEmbed()
				embed.SetLabel( url ); embed.Append( url )
				self.controleFluxoUrlsEmbutidas()
				
		if url == clickedLink and not self.pageExist(url) and not \
			isValid and self.abasControl.GetPageCount() < 10:
			# geralmente a url vem duplacada, sendo a segunda a url
			# válida. Por isso sempre a segunda será usada na nova tabela.
			self.addNewTab( url)

		else: event.Veto()
		
	def hasUrl(self, url):
		""" verifica se a url já foi inserida no controlador de urls """
		if hasattr(self.mainWin, "urlManager"):
			for urlPlusTitle in self.toolBar.getInputLocation().GetStrings():
				if self.mainWin.urlManager.splitUrlDesc(urlPlusTitle)[0] == url:
					return True
		return False
		
	def OnWebViewLoaded(self, evt):
		""" chamado sempre que a página termina de carregar """
		webview = evt.GetEventObject()
		self.setNavStopLoading(webview)
		
	# Control bar events
	def OnLocationSelect(self, event):
		""" controla a seleção de uma url, carrega a url selecionada """
		url = self.toolBar.getInputLocation().GetStringSelection()
		self.webview.LoadURL(url)
		# passa o foco para o navegador
		self.webview.SetFocus()

	def OnLocationEnter(self, event):
		location = self.toolBar.getInputLocation()
		url = location.GetValue()
		
		if not self.hasUrl(url):
			location.Append(url)
			
		self.webview.LoadURL(url)

	def OnPrevPageButton(self, event):
		##self.webview.GoBack()
		self.webview.historyUrl.GoBack()
		self.webview.historyUrl.setBrowsing(True)

	def OnNextPageButton(self, event):
		##self.webview.GoForward()
		self.webview.historyUrl.GoForward()
		self.webview.historyUrl.setBrowsing(True)

	def OnCheckCanGoBack(self, event):
		##event.Enable(self.webview.CanGoBack())
		event.Enable(self.webview.historyUrl.CanGoBack())
		self.progressAnimate()

	def OnCheckCanGoForward(self, event):
		##event.Enable(self.webview.CanGoForward())
		event.Enable(self.webview.historyUrl.CanGoForward())

	def OnStopButton(self, event):
		""" pára o carregamento da página que estiver como o foco """
		self.setNavStopLoading( self.webview )
		self.webview.Stop()

	def OnRefreshPageButton(self, event):
		self.webview.Reload()
		self.toolBar.getInputEmbed().Clear()
		self.webview.JS_SCRIPT_RUN = False
		
## -------------------------------------------------------------------------------
if __name__=='__main__':
	from main.app.util import base
	base.trans_install() # instala as traduções.
	
	app = wx.App( 0 )
	frame = wx.Frame(None, -1, "IEKA", size = (800, 500))
	frame.Fit()
	iewindow = Browser( frame)
	frame.Show()
	app.MainLoop()
	
	