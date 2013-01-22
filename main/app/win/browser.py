# coding: utf-8
import sys, os
from PySide import QtCore
from PySide import QtGui
from PySide import QtWebKit
from main import settings

import main.environ
main.environ.setup((__name__ == "__main__"))


class Browser (QtGui.QWidget):
    searchEngine = "http://www.google.com/"
    
    def __init__(self, *arg):
        super(Browser, self).__init__(*arg)
        vBox = QtGui.QVBoxLayout()
        
        self.webView = QtWebKit.QWebView(self)
        
        self.webView.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
        self.webView.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        
        self.current ="http://www.youtube.com/"
        self.webView.load( QtCore.QUrl(self.current) )
        
        self.webView.linkClicked.connect( self.onLinkClicked )
        self.webView.loadStarted.connect( self.onPageLoad )
        self.webView.urlChanged.connect( self.onChangeUrl )
        
        self.webView.show()
        
        vBox.addLayout( self._createToolbar() )
        vBox.addWidget(self.webView)
        
        self.setLayout( vBox )
        self.show()
        
    def onLinkClicked(self, url):
        self.webView.load( url )
        
    def loadPage(self):
        self.webView.load( QtCore.QUrl(self.location.currentText()) )
        
    def onPageLoad(self):
        url = self.webView.url().toString()
    
    def onChangeUrl(self, url):
        self.current = url.toString()
        self.location.setEditText( self.current )
        self.location.setToolTip(self.current)
        
    def _createToolbar(self):
        self.location = QtGui.QComboBox(self)
        self.location.addItem( self.current )
        self.location.activated.connect(self.loadPage)
        self.location.setEditable(True)
        self.location.show()
        
        ## Back button
        btnBack = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnback-blue.png")
        btnBack.setIcon(QtGui.QIcon(path))
        btnBack.setToolTip("<b>voltar</b>")
        btnBack.clicked.connect( self.webView.back )
        btnBack.show()
        
        ## Foward button
        btnForward = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnforward-blue.png")
        btnForward.setIcon(QtGui.QIcon(path))
        btnForward.setToolTip("<b>avançar</b>")
        btnForward.clicked.connect( self.webView.forward )
        btnForward.show()
        
        ## Refresh button
        btnRefresh = QtGui.QPushButton(self)
        path = os.path.join(settings.IMAGES_DIR, "btnrefresh-blue.png")
        btnRefresh.setIcon(QtGui.QIcon(path))
        btnRefresh.setToolTip("<b>recarregar</b>")
        btnRefresh.clicked.connect( self.webView.reload )
        btnRefresh.show()
        
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
        hBoxLayout.addWidget(btnBack)
        hBoxLayout.addWidget(btnForward)
        hBoxLayout.addWidget(btnRefresh)
        
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