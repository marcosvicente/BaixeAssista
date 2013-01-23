# coding: utf-8
import sys, os
from PySide import QtCore
from PySide import QtGui
from PySide import QtWebKit

import time, thread
import main.environ
main.environ.setup((__name__ == "__main__"))

from main.app.util import base
from main.app import generators
from main.app import models
from main import settings


class StopRefreshButton(QtGui.QPushButton):
    def __init__(self, *arg):
        super(StopRefreshButton, self).__init__()
        self.btnState = {}
        self.setRefreshState()
        
    def setRefreshState(self):
        path = os.path.join(settings.IMAGES_DIR, "btnrefresh-blue.png")
        self.setIcon(QtGui.QIcon(path))
        self.btnState["state"] = "refresh"
        self.setToolTip("<b>recarregar</b>")
        
    def setStopState(self):
        qicon = QtGui.QIcon(os.path.join(settings.IMAGES_DIR, "btnstop-blue.png"))
        self.setIcon( qicon )
        self.btnState["state"] = "stop"
        self.setToolTip("<b>parar</b>")
        
    def __getitem__(self, key):
        return self.btnState[key]
        
class Browser (QtGui.QWidget):
    searchEngine = "http://www.google.com/"
    
    def __init__(self, *arg):
        super(Browser, self).__init__(*arg)
        vBox = QtGui.QVBoxLayout()
        
        self.webView = None
        self.objects = models.Browser.objects # queryset
        
        self.tabPagePanel = QtGui.QTabWidget(self)
        self.tabPagePanel.setTabsClosable(True)
        ##self.tabPagePanel.setTabShape(QtGui.QTabWidget.Triangular)
        self.tabPagePanel.currentChanged.connect( self.updateWebView )
        self.tabPagePanel.tabCloseRequested.connect( self.handleTabCloseRequest )
        vBox.addLayout( self._createToolbar() )
        
        # página inicial padrão
        lastSite = (self.getLastSite() or self.searchEngine)
        
        for site in self.getHistorySites():
            self.setupPage(site, (site==lastSite))
        
        vBox.addWidget( self.tabPagePanel )
        
        self.setLayout( vBox )
        # atualiza o estado dos botões de navegação.
        thread.start_new_thread(self.updateHistoryButton, tuple())
        self.show()
    
    def setupPage(self, url, isDefaulf=False):
        webView = QtWebKit.QWebView(self.tabPagePanel)
        
        webView.MOVIE_LOADING = QtGui.QMovie(os.path.join(settings.IMAGES_DIR, "spin-progress.gif"))
        webView.PAGE_LOADING = True
        webView.PAGE_URL = url
        
        webView.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
        webView.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        
        webView.linkClicked.connect( self.onLinkClicked )
        webView.loadStarted.connect( self.onPageLoad )
        webView.loadFinished.connect( self.onPageFinished )
        webView.loadProgress.connect( self.onProgress )
        webView.urlChanged.connect( self.onChangeUrl )
        webView.titleChanged.connect( self.onTitleChange )
        webView.load(QtCore.QUrl(url))
        webView.show()
        
        self.tabPagePanel.addTab(webView, self.tr("Loading..."))
        if isDefaulf: self.tabPagePanel.setCurrentWidget( webView )
        
    def getLastSite(self):
        try: query = self.objects.get(site=None, historysite=None)
        except: query = models.Browser(lastsite="")
        return query.lastsite
    
    def addLastSite(self, site):
        try: query = self.objects.get(site=None, historysite=None)
        except: query = models.Browser()
        query.lastsite = site
        query.save()
    
    def getHistorySites(self):
        queries = self.objects.filter(site=None, lastsite=None)
        return map(lambda q: q.historysite, queries)
    
    def addHistorySites(self, sites):
        """ guarda o histórico de urls """
        self.objects.filter(site=None, lastsite=None).delete()
        for site in sites:
            models.Browser(historysite=site).save()
            
    def addSite(self, site):
        models.Browser(site=site).save()
    
    def getSites(self):
        """ retorna uma lista com todos os sites adicionados """
        queries = self.objects.filter(lastsite=None, historysite=None)
        return map(lambda q: q.site, queries)

    def closeEvent(self, event):
        # salva os dados de navegação
        historyUrl = []
        for index in range(self.tabPagePanel.count()):
            webView = self.tabPagePanel.widget( index )
            historyUrl.append( webView.PAGE_URL )
            
        self.addHistorySites( historyUrl )
        self.addLastSite( self.webView.PAGE_URL )
        
    def handleTabCloseRequest(self, index):
        # garante que pelo menos um tabela exista(tabela padrão).
        if self.tabPagePanel.count() > 1:
            webView = self.tabPagePanel.widget( index )
            self.tabPagePanel.removeTab( index )
            webView.reload(); webView.close()
            
    def updateHistoryButton(self, *args):
        while True:
            try:
                self.btnBack.setEnabled(self.webView.history().canGoBack())
                self.btnForward.setEnabled(self.webView.history().canGoForward())
                time.sleep(0.5)
            except: break
            
    def updateWebView(self, index):
        webView = self.tabPagePanel.widget( index )
        
        if webView == self.tabPagePanel.currentWidget():
            self.location.setEditText(webView.PAGE_URL)
            self.location.setToolTip(webView.PAGE_URL)
            self.webView = webView
            
        if not webView.PAGE_LOADING:
            self.btnStopRefresh.setRefreshState()
        else:
            self.btnStopRefresh.setStopState()
            
    def onLinkClicked(self, url):
        self.webView.load( url )
        
    def loadPage(self):
        self.webView.load( QtCore.QUrl(self.location.currentText()) )
        
    def onPageLoad(self):
        webView = self.sender()
        webView.PAGE_LOADING = True
        webView.MOVIE_LOADING.start()
        
        self.btnStopRefresh.setStopState()
        
    def onPageFinished(self):
        webView = self.sender()
        webView.PAGE_LOADING = False
        webView.MOVIE_LOADING.stop()
        
        index = self.tabPagePanel.indexOf( webView )
        self.tabPagePanel.setTabIcon(index, webView.icon())
        
        self.btnStopRefresh.setRefreshState()
        
    def onProgress(self, porcent):
        webView = self.sender()
        self.tabPagePanel.setTabIcon(self.tabPagePanel.indexOf(webView), 
                                     QtGui.QIcon(webView.MOVIE_LOADING.currentPixmap()))
        webView.MOVIE_LOADING.jumpToNextFrame()
        
    def onTitleChange(self, title):
        webView = self.sender()
        index = self.tabPagePanel.indexOf( webView )
        self.tabPagePanel.setTabText(index, title if len(title) < 20 else (title[:20]+"..."))
        self.tabPagePanel.setTabToolTip(index, title)
        
    def onChangeUrl(self, url):
        webView = self.sender()
        webView.PAGE_URL = url.toString()
        if self.webView == webView:
            self.location.setEditText(webView.PAGE_URL)
            self.location.setToolTip(webView.PAGE_URL)
            
    def handleStopRefresh(self):
        if self.btnStopRefresh["state"] == "refresh":
            self.webView.reload()
            
        elif self.btnStopRefresh["state"] == "stop":
            self.webView.stop()
    
    def handleNewFavoriteSite(self):
        print self.sender()
        
    def _createToolbar(self):
        self.location = QtGui.QComboBox(self)
        # adicionando a lista de site favoritos.
        self.location.addItems( self.getSites() )
        self.location.activated.connect(self.loadPage)
        self.location.setEditable(True)
        self.location.show()
        
        ## Back button
        self.btnBack = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnback-blue.png")
        self.btnBack.setIcon(QtGui.QIcon(path))
        self.btnBack.setToolTip("<b>voltar</b>")
        self.btnBack.clicked.connect(lambda: self.webView.back())
        self.btnBack.show()
        
        ## Foward button
        self.btnForward = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnforward-blue.png")
        self.btnForward.setIcon(QtGui.QIcon(path))
        self.btnForward.setToolTip("<b>avançar</b>")
        self.btnForward.clicked.connect(lambda: self.webView.forward())
        self.btnForward.show()
        
        ## Refresh button
        self.btnStopRefresh = StopRefreshButton(self)
        self.btnStopRefresh.clicked.connect( self.handleStopRefresh )
        
        ## New page button
        self.btnNewPage = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnpage-blue.png")
        self.btnNewPage.setIcon(QtGui.QIcon(path))
        self.btnNewPage.setToolTip("<b>nova página</b>")
        self.btnNewPage.clicked.connect(lambda: self.setupPage(self.searchEngine, True))
        self.btnNewPage.show()
        
        ## Favorite button
        self.btnFavorite = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnstart-blue.png")
        self.btnFavorite.setIcon(QtGui.QIcon(path))
        
        menu = QtGui.QMenu(self)
        
        path = os.path.join(settings.IMAGES_DIR, "btnplus-blue.png")
        self.addUrlAction = QtGui.QAction(self.tr("&favorite"), self, 
                                    triggered=self.handleNewFavoriteSite,
                                    icon = QtGui.QIcon(path))
        menu.addAction( self.addUrlAction )
        ###
        path = os.path.join(settings.IMAGES_DIR, "btnminus-blue.png")
        self.removeUrlAction = QtGui.QAction(self.tr("&remove"), self, 
                                    triggered=self.handleNewFavoriteSite,
                                    icon = QtGui.QIcon(path))
        menu.addAction( self.removeUrlAction )
        
        self.btnFavorite.setMenu( menu )
        
        ## Refresh button
        btnSearch = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnsearch-blue.png")
        btnSearch.setIcon(QtGui.QIcon(path))
        btnSearch.setToolTip("<b>search</b>")
        btnSearch.clicked.connect(lambda: self.webView.load(self.searchEngine))
        btnSearch.show()
        
        hBoxLayout = QtGui.QHBoxLayout()
        
        hBoxLayout.addWidget(self.btnBack)
        hBoxLayout.addWidget(self.btnForward)
        hBoxLayout.addWidget(self.btnStopRefresh)
        hBoxLayout.addWidget(self.btnNewPage)
        
        hBoxLayout.addWidget(self.location, 1)
        hBoxLayout.addWidget(self.btnFavorite)
        hBoxLayout.addWidget( btnSearch )
        return hBoxLayout
        

## ----------------------------------------------------------------
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = Browser()
    sys.exit(app.exec_())