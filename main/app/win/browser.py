# coding: utf-8
import sys, os
from PySide import QtCore
from PySide import QtGui
from PySide import QtWebKit
from main import settings
import time, thread

import main.environ
main.environ.setup((__name__ == "__main__"))
from main.app.util import base

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
        
        self.tabPagePanel = QtGui.QTabWidget(self)
        self.tabPagePanel.currentChanged.connect( self.updateWebView )
        vBox.addLayout( self._createToolbar() )
        
        self.setupPage("http://www.youtube.com/")
        self.setupPage("http://www.python.org/")
        self.setupPage("http://www.itau.com.br/")
        self.setupPage("http://code.google.com/p/gerenciador-de-videos-online/downloads/list")
        
        vBox.addWidget( self.tabPagePanel )
        
        self.setLayout( vBox )
        # atualiza o estado dos botões de navegação.
        thread.start_new_thread(self.updateHistoryButton, tuple())
        self.show()
    
    def setupPage(self, url):
        tabPage = QtGui.QWidget()
        vBox = QtGui.QVBoxLayout()
        tabPage.setLayout( vBox )
        
        webView = QtWebKit.QWebView(tabPage)
        vBox.addWidget( webView )
        
        tabPage.webView = webView
        webView.MOVIE_LOADING = QtGui.QMovie(os.path.join(settings.IMAGES_DIR, "spin-progress.gif"))
        webView.MOVIE_LOADING.start()
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
        
        self.tabPagePanel.addTab(tabPage, self.tr("Loading..."))
        webView.load(QtCore.QUrl(url))
        webView.show()
        
    def updateHistoryButton(self, *args):
        while True:
            try:
                self.btnBack.setEnabled(self.webView.history().canGoBack())
                self.btnForward.setEnabled(self.webView.history().canGoForward())
                time.sleep(0.5)
            except: pass
            
    def updateWebView(self, index):
        tabPage = self.tabPagePanel.widget( index )
        
        if tabPage == self.tabPagePanel.currentWidget():
            self.webView = tabPage.webView
            
            self.location.setEditText(self.webView.PAGE_URL)
            self.location.setToolTip(self.webView.PAGE_URL)
        
        if not tabPage.webView.PAGE_LOADING:
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
        
        index = self.tabPagePanel.indexOf( webView.parent() )
        self.tabPagePanel.setTabIcon(index, webView.icon())
        
        self.btnStopRefresh.setRefreshState()
        
    def onProgress(self, porcent):
        webView = self.sender()
        index = self.tabPagePanel.indexOf( webView.parent() )
        self.tabPagePanel.setTabIcon(index, QtGui.QIcon(webView.MOVIE_LOADING.currentPixmap()))
    
    def onTitleChange(self, title):
        webView = self.sender()
        index = self.tabPagePanel.indexOf( webView.parent() )
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
        
    def _createToolbar(self):
        self.location = QtGui.QComboBox(self)
        ##self.location.addItem( self.current )
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
        
        ## Refresh button
        btnSearch = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnsearch-blue.png")
        btnSearch.setIcon(QtGui.QIcon(path))
        btnSearch.setToolTip("<b>pesquisar</b>")
        btnSearch.clicked.connect(lambda: self.webView.load(self.searchEngine))
        btnSearch.show()
        
        ## Add url button
        btnNewUrl = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnplus-blue.png")
        btnNewUrl.setIcon(QtGui.QIcon(path))
        btnNewUrl.setToolTip("<b>adicionar nova url</b>")
        #btnNewUrl.clicked.connect()
        btnNewUrl.show()
        
        ## Add url button
        btnDelUrl = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnminus-blue.png")
        btnDelUrl.setIcon(QtGui.QIcon(path))
        btnDelUrl.setToolTip("<b>remover url existente</b>")
        #btnDelUrl.clicked.connect()
        btnDelUrl.show()
        
        hBoxLayout = QtGui.QHBoxLayout()
        hBoxLayout.addWidget(self.btnBack)
        hBoxLayout.addWidget(self.btnForward)
        hBoxLayout.addWidget(self.btnStopRefresh)
        
        hBoxLayout.addWidget(self.location, 1)
        hBoxLayout.addWidget( btnSearch )
        hBoxLayout.addWidget( btnNewUrl )
        hBoxLayout.addWidget( btnDelUrl )
        return hBoxLayout
        

## ----------------------------------------------------------------
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = Browser()
    sys.exit(app.exec_())