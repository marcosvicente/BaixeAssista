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
        
        self.current ="http://www.youtube.com/"
        self.webView = QtWebKit.QWebView(self)
        
        self.webView.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
        self.webView.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        
        self.webView.linkClicked.connect( self.onLinkClicked )
        self.webView.loadStarted.connect( self.onPageLoad )
        self.webView.loadFinished.connect( self.onPageFinished )
        self.webView.urlChanged.connect( self.onChangeUrl )
        self.webView.show()
        
        vBox.addLayout( self._createToolbar() )
        vBox.addWidget(self.webView)
        
        # carregando a página padrão.
        self.webView.load( QtCore.QUrl(self.current) )
        self.onPageLoad()
        
        self.setLayout( vBox )
        self.show()
    
    base.just_try()
    def updateHistoryButton(self, *args):
        while True:
            self.btnBack.setEnabled(self.webView.history().canGoBack())
            self.btnForward.setEnabled(self.webView.history().canGoForward())
            time.sleep(0.5)
            
    def onLinkClicked(self, url):
        self.webView.load( url )
        
    def loadPage(self):
        self.webView.load( QtCore.QUrl(self.location.currentText()) )
        
    def onPageLoad(self):
        self.btnStopRefresh.setStopState()
        
    def onPageFinished(self):
        self.btnStopRefresh.setRefreshState()
        
    def onChangeUrl(self, url):
        self.current = url.toString()
        self.location.setEditText( self.current )
        self.location.setToolTip(self.current)
    
    def handleStopRefresh(self):
        if self.btnStopRefresh["state"] == "refresh":
            self.webView.reload()
            
        elif self.btnStopRefresh["state"] == "stop":
            self.webView.stop()
        
    def _createToolbar(self):
        self.location = QtGui.QComboBox(self)
        self.location.addItem( self.current )
        self.location.activated.connect(self.loadPage)
        self.location.setEditable(True)
        self.location.show()
        
        ## Back button
        self.btnBack = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnback-blue.png")
        self.btnBack.setIcon(QtGui.QIcon(path))
        self.btnBack.setToolTip("<b>voltar</b>")
        self.btnBack.clicked.connect( self.webView.back )
        self.btnBack.show()
        
        ## Foward button
        self.btnForward = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnforward-blue.png")
        self.btnForward.setIcon(QtGui.QIcon(path))
        self.btnForward.setToolTip("<b>avançar</b>")
        self.btnForward.clicked.connect( self.webView.forward )
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
        
        # atualiza o estado dos botões de navegação.
        thread.start_new_thread(self.updateHistoryButton, tuple())
        return hBoxLayout
        

## ----------------------------------------------------------------
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = Browser()
    sys.exit(app.exec_())