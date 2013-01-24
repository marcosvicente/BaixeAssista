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
        self.setToolTip("<b>reload</b>")
        
    def setStopState(self):
        qicon = QtGui.QIcon(os.path.join(settings.IMAGES_DIR, "btnstop-blue.png"))
        self.setIcon( qicon )
        self.btnState["state"] = "stop"
        self.setToolTip("<b>stop</b>")
        
    def __getitem__(self, key):
        return self.btnState[key]
        
class Browser (QtGui.QWidget):
    searchEngine = "http://www.google.com/"
    
    def __init__(self, parent=None):
        super(Browser, self).__init__(parent)
        vBox = QtGui.QVBoxLayout()
        
        self.webView = None
        self.mainWin = parent
        self.objects = models.Browser.objects # queryset
        
        self.starEnableIcon = QtGui.QIcon(os.path.join(settings.IMAGES_DIR, "btnstart-blue.png"))
        self.starDisableIcon = self.starEnableIcon.pixmap(QtCore.QSize(22, 22),
                                                           QtGui.QIcon.Disabled, QtGui.QIcon.Off)
        
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
    
    @staticmethod
    def formatUrl(url):
        """ tornando automaticamente a url válida """
        url = "http://"+url if not url.startswith("http://") else url
        url = url+ "/" if not url.endswith("/") else url
        return url
    
    def saveSettings(self):
        # salva os dados de navegação
        historyUrl = []
        for index in range(self.tabPagePanel.count()):
            webView = self.tabPagePanel.widget( index )
            historyUrl.append( webView.PAGE_URL )
            
        self.addHistorySites( historyUrl )
        self.addLastSite( self.webView.PAGE_URL )
        
    def closeEvent(self, event):
        self.saveSettings()
        
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
        urlString = url.toString()
        
        if generators.Universal.has_site(urlString) and hasattr(self.mainWin, "getLocationMainUrl"):
            locationMainUrl = self.mainWin.getLocationMainUrl()
            
            isEmbedUrl = generators.Universal.isEmbed(urlString)
            url = generators.Universal.get_inner_url(urlString)
            
            if not isEmbedUrl:
                locationMainUrl.setEditText( urlString )
            else: pass
        else:
            self.webView.load( url )
            
    def loadPage(self):
        url = self.location.currentText()
        self.webView.load(QtCore.QUrl(url))
        self.updateFavoriteIcon()
        
    def onPageLoad(self):
        webView = self.sender()
        
        webView.PAGE_LOADING = True
        webView.MOVIE_LOADING.start()
        
        self.btnStopRefresh.setStopState()
        self.updateFavoriteIcon()
        
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
    
    def handleFavoriteSite(self):
        text, ok = QtGui.QInputDialog.getText(self, self.tr("Add url as favorite"),
                          self.tr("Enter the url below."), text = self.location.currentText())
        text = text.strip()
        if text:
            text = self.formatUrl( text )
            
            # adicionando ao controle de url e ao banco de dados
            if self.objects.filter(site=text).count() == 0:
                if self.location.findText( text ) < 0:
                    self.location.addItem( text )
                    
                self.addSite( text )
                
                # atualiza o índice, com a nova url
                self.location.setCurrentIndex(self.location.findText( text ))
                
                # atualizando a 'start' com ativa
                self.updateFavoriteIcon()
            else:
                reply = QtGui.QMessageBox.question(self, self.tr("Without panic :)"), 
                                    self.tr("Url already in the list. Want to add another ?"),
                                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                
                # tentando adicionar dados novamente.
                if reply == QtGui.QMessageBox.Yes:
                    self.handleFavoriteSite()
        elif ok:
            warningBoxEmpty = QtGui.QMessageBox(QtGui.QMessageBox.Warning, 
                        self.tr("Empty ?"), self.tr("Enter a url first."), 
                        QtGui.QMessageBox.NoButton, self)
            
            warningBoxEmpty.addButton("Retry", QtGui.QMessageBox.AcceptRole)
            warningBoxEmpty.addButton("Cancel", QtGui.QMessageBox.RejectRole)
            
            # tentando adicionar dados novamente.
            if warningBoxEmpty.exec_() == QtGui.QMessageBox.AcceptRole:
                self.handleFavoriteSite()
                
    def handleUnFavoriteSite(self):
        url = self.formatUrl( self.location.currentText() )
        
        index = self.location.findText( url )
        
        if index > -1:
            # ação que leva a remoção de uma url do banco de dados e do controle de urls.
            reply = QtGui.QMessageBox.question(self, self.tr("Requires confirmation"), 
                       self.tr("The url below will be removed.\n") + url, 
                       QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            
            if reply == QtGui.QMessageBox.Yes:
                self.location.removeItem(index)
                
                # removendo do bando de dados
                query = self.objects.get(site = url)
                query.delete()
                
                self.webView.load(self.location.currentText())
        else:
            QtGui.QMessageBox.information(self, self.tr("Not found"), 
                self.tr("The url can not be found in the current list."))
        
    def updateFavoriteIcon(self, url=None):
        if url is None: url = self.formatUrl(self.location.currentText())
        
        if self.objects.filter(site=url).count() > 0:
            self.btnFavorite.setIcon(self.starEnableIcon)
        else:
            self.btnFavorite.setIcon(self.starDisableIcon)
            
    def handleUrlAction(self):
        url = self.formatUrl( self.location.currentText() )
        
        if self.objects.filter(site=url).count() == 0:
            self.handleFavoriteSite()
        else:
            self.handleUnFavoriteSite()
            
    def _createToolbar(self):
        self.location = QtGui.QComboBox(self)
        # adicionando a lista de site favoritos.
        self.location.addItems( self.getSites() )
        self.location.activated.connect(self.loadPage)
        # fazendo eventos de edição atualizarem a 'start' de favoritos.
        self.location.editTextChanged.connect(self.updateFavoriteIcon)
        self.location.setEditable(True)
        self.location.show()
        
        ## Back button
        self.btnBack = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnback-blue.png")
        self.btnBack.setIcon(QtGui.QIcon(path))
        self.btnBack.setToolTip("<b>back</b>")
        self.btnBack.clicked.connect(lambda: self.webView.back())
        self.btnBack.show()
        
        ## Foward button
        self.btnForward = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnforward-blue.png")
        self.btnForward.setIcon(QtGui.QIcon(path))
        self.btnForward.setToolTip("<b>forward</b>")
        self.btnForward.clicked.connect(lambda: self.webView.forward())
        self.btnForward.show()
        
        ## Refresh button
        self.btnStopRefresh = StopRefreshButton(self)
        self.btnStopRefresh.clicked.connect( self.handleStopRefresh )
        
        ## New page button
        self.btnNewPage = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnpage-blue.png")
        self.btnNewPage.setIcon(QtGui.QIcon(path))
        self.btnNewPage.setToolTip("<b>new page</b>")
        self.btnNewPage.clicked.connect(lambda: self.setupPage(self.searchEngine, True))
        self.btnNewPage.show()
        
        ## Favorite button
        self.btnFavorite = QtGui.QPushButton(self)
        self.btnFavorite.setToolTip("<b>favorite</b>")
        self.btnFavorite.setIcon(self.starEnableIcon)
        self.btnFavorite.clicked.connect( self.handleUrlAction)
        
        ##path = os.path.join(settings.IMAGES_DIR, "btnplus-blue.png")
        ##path = os.path.join(settings.IMAGES_DIR, "btnminus-blue.png")
        
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
        
        hBoxLayout.addWidget(self.location, 1)
        hBoxLayout.addWidget(self.btnFavorite)
        hBoxLayout.addWidget(self.btnNewPage)
        hBoxLayout.addWidget( btnSearch )
        return hBoxLayout
        

## ----------------------------------------------------------------
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = Browser()
    sys.exit(app.exec_())