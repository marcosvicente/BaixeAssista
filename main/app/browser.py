# -*- coding: ISO-8859-1 -*-

import os, sys
import wx
import re
import time
import wx.aui
import configobj
import wx.animate
import wx.html2 as Webview
import wx.lib.agw.genericmessagedialog as GMD
import wx.lib.agw.flatnotebook as FNB

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = "main.settings"
    scriptPath = os.path.dirname(os.path.abspath(__file__))
    
    parentDir = os.path.dirname(scriptPath)
    mainDir = os.path.dirname(parentDir)
    
    if not mainDir in sys.path: sys.path.append(mainDir)
    if not parentDir in sys.path: sys.path.append(parentDir)
    if not scriptPath in sys.path: sys.path.append(scriptPath)
    
    os.chdir( mainDir )

import gerador, manager
from main import settings
from main.app import models

PROGRAM_VERSION = gerador.PROGRAM_VERSION
SEARCH_ENGINE = "http://www.google.com.br/webhp?hl=pt-BR"

with open(os.path.join(settings.APPDIR,"js","ml.js"), "r") as js_file:
    JS_LINK_MONITOR = js_file.read()

with open(os.path.join(settings.APPDIR,"js","el.js"), "r") as js_file:
    JS_LINK_EXTRACTOR = js_file.read()
    
with open(os.path.join(settings.APPDIR,"js","rl.js"), "r") as js_file:
    JS_LINK_REGISTER = js_file.read()
    
######################################################################################

class FiltroUrl:
    def __init__(self ):
        self.listaSite = gerador.Universal.get_sites()
        self.url, self.is_embed = "", False

    def getUrl(self):
        return self.url

    def isEmbed(self):
        return self.is_embed

    def reverseUrl(self, url):
        return "".join([url[i] for i in range(len(url)-1, -1, -1)])

    def extraiSegundUrl(self, url):
        http = "http://"; httpLen = len(http)
        httpReverso = self.reverseUrl( http)
        urlReversa = self.reverseUrl( url)

        if len(url) > httpLen:
            index = url.find(http, httpLen)
            # retorna só a segunda url
            if index >= 0: return url[index:]

            index = urlReversa.find("=", httpLen)
            if urlReversa.startswith( http ) and index >= 0:
                return urlReversa[ :index]

        # se a url não for dupla apenas retorna
        return url

    def isValid(self, url):
        """ Cada site carregado pelo IE, terá sua url 
        analizada com as regex dos sites suportados """
        urls = [url, self.reverseUrl(url)]
        
        for site in self.listaSite:
            # as vezes a url válida está dentro de outra url, então search irá extraí-la
            for url in urls:
                matchobj = gerador.Universal.patternMatch(site, url)
                if matchobj: # retorna só o grupo da url completa
                    self.url = matchobj.group("inner_url")
                    self.is_embed = gerador.Universal.isEmbed(url)
                    return True
        else:
            # anula as variaveis, para evitar pegar dados incorretos
            self.url, self.is_embed = "", False

            # quando a url analizada não for válida
            return False

##############################################################################
class HistoryUrl:
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
            ##     |
            ##     [e, f, g]- ramo criado, apartir de b
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
class Browser(wx.Panel):
    def __init__(self, parent, mainWindow=None):
        wx.Panel.__init__(self, parent, -1)
        self.mainWin = mainWindow

        # sizer principal do painel
        mainBoxSizer = wx.BoxSizer(wx.VERTICAL)

        if mainWindow:
            self.titleBase = mainWindow.GetTitle()
        
        self.progressAni = wx.animate.Animation(os.path.join(settings.IMAGES_DIR,"progress.gif"))
        self._ImageList = wx.ImageList(*self.progressAni.GetSize())
        
        for index in range(self.progressAni.GetFrameCount()):
            img = self.progressAni.GetFrame( index )
            self._ImageList.Add( img.ConvertToBitmap() )
            
        self.filtroUrl = FiltroUrl()

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
        toolBarSizer = self.createToolBar()

        # aba padrão - sempre criada
        self.addNewTab(self.current, True)
        self.location.SetLabel(self.current)

        # abas secundárias
        for site in self.getHistorySites():
            if not site == self.current:
                self.addNewTab(site)

        mainBoxSizer.Add(toolBarSizer, 0, wx.EXPAND)
        mainBoxSizer.Add(self.abasControl, 1, wx.EXPAND)

        mainBoxSizer.Layout()
        self.SetSizer( mainBoxSizer )
        self.SetAutoLayout(True)
    
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

        self.location.SetToolTip(wx.ToolTip(url))

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
        win = evt.GetEventObject()
        self.webview = self.abasControl.GetCurrentPage()
        self.location.SetValue( self.webview.GetCurrentURL())
        self.location.SetToolTip(wx.ToolTip(self.webview.GetCurrentURL()))
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
            
    def createToolBar( self):
        hBoxSizer = wx.BoxSizer( wx.HORIZONTAL )

        flexGridSizerGroup = wx.FlexGridSizer(1, 8, 0, 2)
        hBoxSizer.Add( flexGridSizerGroup)
        width = height = 25
        # ---------------------------------------------------------------------------------

        # botão go_back
        imgpath = os.path.join(settings.IMAGES_DIR, "go-previous24x24.png")
        bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)
        #bmp.Rescale(width, height)

        btn = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
        btn.SetToolTipString("Go Back")
        self.Bind(wx.EVT_BUTTON, self.OnPrevPageButton, btn)
        flexGridSizerGroup.Add(btn, 0, wx.LEFT, 2)
        self.Bind(wx.EVT_UPDATE_UI, self.OnCheckCanGoBack, btn)
        # ---------------------------------------------------------------------------------

        # botão go_forward
        imgpath = os.path.join(settings.IMAGES_DIR, "go-next24x24.png")
        bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)

        btn = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
        btn.SetToolTipString("Go Forward")
        self.Bind(wx.EVT_BUTTON, self.OnNextPageButton, btn)
        flexGridSizerGroup.Add(btn)
        self.Bind(wx.EVT_UPDATE_UI, self.OnCheckCanGoForward, btn)
        # ---------------------------------------------------------------------------------

        # botão search
        imgpath = os.path.join(settings.IMAGES_DIR, "search-computer24x24.png")
        bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)

        btn = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
        btn.SetToolTipString("Google Search")
        self.Bind(wx.EVT_BUTTON, self.OnSearchPageButton, btn)
        flexGridSizerGroup.Add(btn)	
        # ---------------------------------------------------------------------------------

        # botão reflesh
        imgpath = os.path.join(settings.IMAGES_DIR, "view-refresh24x24.png")
        bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)

        btn = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
        btn.SetToolTipString("Reflesh")
        self.Bind(wx.EVT_BUTTON, self.OnRefreshPageButton, btn)
        flexGridSizerGroup.Add(btn)
        # ---------------------------------------------------------------------------------

        # botão Stop loading
        imgpath = os.path.join(settings.IMAGES_DIR, "process-stop24x24.png")
        bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)

        btn = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
        btn.SetToolTipString("Stop")
        self.Bind(wx.EVT_BUTTON, self.OnStopButton, btn)
        flexGridSizerGroup.Add(btn)
        # ---------------------------------------------------------------------------------

        # botão adicionar um novo site
        imgpath = os.path.join(settings.IMAGES_DIR, "list-add24x24.png")
        bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)

        btn = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
        btn.SetToolTipString( _(u"Permite adicionar um novo site de filmes\nà lista de sites favoritos") )
        self.Bind(wx.EVT_BUTTON, self.addNewMovieSite, btn)
        flexGridSizerGroup.Add(btn)
        # ---------------------------------------------------------------------------------
        # botão remover site
        imgpath = os.path.join(settings.IMAGES_DIR, "list-remove24x24.png")
        bmp = wx.Image(imgpath, wx.BITMAP_TYPE_PNG)

        btn = wx.BitmapButton(self, -1, bmp.ConvertToBitmap())
        btn.SetToolTipString( _(u"Use para remover sites, da lista de sites favoritos.") )
        self.Bind(wx.EVT_BUTTON, self.removeMovieSite, btn)
        flexGridSizerGroup.Add(btn)
        # ---------------------------------------------------------------------------------

        self.zoomControl = wx.SpinButton(self, -1, style=wx.SP_VERTICAL)
        self.zoomControl.SetMinSize( (-1, btn.GetSize().y) )

        self.zoomControl.SetToolTip( wx.ToolTip("Zoom") )
        self.zoomControl.SetValue( Webview.WEB_VIEW_ZOOM_MEDIUM )
        self.zoomControl.SetRange( Webview.WEB_VIEW_ZOOM_TINY, Webview.WEB_VIEW_ZOOM_LARGEST)
        self.zoomControl.Bind(wx.EVT_SPIN, self.setPageZoom)

        flexGridSizerGroup.Add(self.zoomControl)
        # ---------------------------------------------------------------------------------
        gridSizer = wx.GridSizer(1,2)
        hBoxSizer.Add(gridSizer, 1, wx.EXPAND)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        gridSizer.Add(hSizer, 0, wx.EXPAND)

        info = wx.StaticText(self, -1, _("Local:"))
        hSizer.Add(info, 0, wx.ALIGN_CENTER|wx.RIGHT|wx.LEFT, 5)

        # controle usado para entrada de urls
        self.location = wx.ComboBox(self, -1, self.current, style=wx.CB_DROPDOWN|wx.PROCESS_ENTER)
        self.location.SetFont( wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Arial'))

        for site in self.getSites(): self.location.Append(site)

        self.Bind(wx.EVT_COMBOBOX, self.OnLocationSelect, self.location)
        self.location.Bind(wx.EVT_TEXT_ENTER, self.OnLocationEnter)
        hSizer.Add(self.location, 1, wx.EXPAND)
        # ---------------------------------------------------------------------------------
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        gridSizer.Add( hSizer, 1, wx.EXPAND)

        info = wx.StaticText(self, -1, "Embed:")
        hSizer.Add(info, 0, wx.ALIGN_CENTER|wx.RIGHT|wx.LEFT, 5)

        # controle usado para entrada de urls embutidas
        self.controlEmbedUrls = wx.ComboBox(self, -1, "", style=wx.CB_DROPDOWN|wx.PROCESS_ENTER)
        self.controlEmbedUrls.SetFont( wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Arial'))

        self.Bind(wx.EVT_COMBOBOX, self.embedHandle, self.controlEmbedUrls)
        self.controlEmbedUrls.Bind(wx.EVT_TEXT_ENTER, self.embedHandle)
        hSizer.Add(self.controlEmbedUrls, 1, wx.EXPAND|wx.RIGHT, 2)

        return hBoxSizer

    def setPageZoom(self, evt=None):
        """ configura o nível de zoom do layout página com o foco """
        try: self.webview.SetZoom( self.zoomControl.GetValue() )
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
            
            if not local.startswith("http://"):
                local = "http://" + local
            if not local.endswith("/"):
                local += "/"
                
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
                    self.location.Append( local)
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
        self.controlEmbedUrls.Clear()

    def ShutdownDemo(self):
        # put the frame title back
        if self.mainWin: self.mainWin.SetTitle(self.titleBase)

    def embedHandle(self, event):
        """ atribui a url do controle de url embutidas para
        o controle de transferência de arquivos """
        url = self.controlEmbedUrls.GetStringSelection()
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
        items = self.controlEmbedUrls.GetItems()
        if len(items) > 8:
            self.controlEmbedUrls.Set( self.custom_enumerate(items[2:]) )
        else:
            urlsIndexadas = self.custom_enumerate(items)
            self.controlEmbedUrls.Set( urlsIndexadas )
        self.controlEmbedUrls.SetSelection(self.controlEmbedUrls.GetCount()-1)

    def OnWebViewNavigating(self, event):
        """ Controla o começo do carregamento de um recurço """
        webview = event.GetEventObject()
        webviewUrl = webview.GetCurrentURL()
        
        # configura os dados para a animação da progress animate
        webview.loading, webview.isNullBitmap = True, False
        
        if webviewUrl != webview.Url and webviewUrl.startswith("http"):
            if not webview.historyUrl.isBrowsing():
                webview.historyUrl.append( webviewUrl )

            webview.JS_SCRIPT_RUN = False
            self.controlEmbedUrls.Clear()

            webview.historyUrl.setBrowsing(False)

            self.historySites.remove( webview.Url )
            self.historySites.append( webviewUrl )
            webview.Url = webviewUrl

            if webview == self.webview:
                self.location.SetLabel( webviewUrl )
                self.location.SetToolTip(wx.ToolTip( webviewUrl ))

            self.current = webviewUrl
        
        if not webview.JS_SCRIPT_RUN and webviewUrl.startswith("http"):
            ## webview.RunScript( JS_LINK_REGISTER )
            webview.RunScript( JS_LINK_MONITOR )
            webview.RunScript( JS_LINK_EXTRACTOR )
            webview.JS_SCRIPT_RUN = True
            
        url = event.GetURL()
        
        if self.filtroUrl.isValid( url ) and hasattr(self.mainWin, "controladorUrl"):
            url = self.filtroUrl.getUrl() # só quando for válida.
            isEmbed = self.filtroUrl.isEmbed() # é do tipo embutido, player
            
            if not isEmbed:
                self.mainWin.controladorUrl.SetValue( url )
                self.setNavStopLoading( webview )
                # This is how you can cancel loading a page.
                event.Veto()
            else:
                self.controlEmbedUrls.SetLabel( url )
                self.controlEmbedUrls.Append( url )
                self.controleFluxoUrlsEmbutidas()

    def OnWebViewNewWindow(self, event):
        """ Controla a abertura de novas janelas """
        prev_title = self.webview.GetCurrentTitle()
        self.webview.RunScript("document.title = clickedLink;")
        clickedLink = self.webview.GetCurrentTitle()
        
        try: clickedLink = clickedLink.decode("utf-8")
        except: clickedLink = clickedLink.encode("utf-8")
        
        self.webview.RunScript("document.title = '%s';" % prev_title)
        url = event.GetURL(); isValid = self.filtroUrl.isValid( url )
        
        if isValid and hasattr(self.mainWin, "controladorUrl"):
            url = self.filtroUrl.getUrl() # só quando for válida.
            isEmbed = self.filtroUrl.isEmbed() # é do tipo embutido, player

            if not isEmbed:
                self.mainWin.controladorUrl.SetValue( url )
            else:
                self.controlEmbedUrls.SetLabel( url )
                self.controlEmbedUrls.Append( url )
                self.controleFluxoUrlsEmbutidas()

        if url == clickedLink and not self.pageExist(url) and not isValid and self.abasControl.GetPageCount() < 10:
            # geralmente a url vem duplacada, sendo a segunda a url
            # válida. Por isso sempre a segunda será usada na nova tabela.
            self.addNewTab( self.filtroUrl.extraiSegundUrl( url ) )

        else: event.Veto()
        
    def hasUrl(self, url):
        """ verifica se a url já foi inserida no controlador de urls """
        if hasattr(self.mainWin, "urlManager"):
            for urlPlusTitle in self.location.GetStrings():
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
        url = self.location.GetStringSelection()
        self.webview.LoadURL(url)
        # passa o foco para o navegador
        self.webview.SetFocus()

    def OnLocationEnter(self, event):
        url = self.location.GetValue()
        
        if not self.hasUrl(url):
            self.location.Append(url)
            
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
        self.controlEmbedUrls.Clear()
        self.webview.JS_SCRIPT_RUN = False


if __name__=='__main__':
    from manager import installTranslation
    # instala as traduções.
    installTranslation()

    app = wx.App( 0 )
    frame = wx.Frame(None, -1, "IEKA", size = (800, 500))
    iewindow = Browser( frame)
    frame.Show()
    app.MainLoop()