# coding: utf-8
import sys
from PySide import QtCore
from PySide import QtGui
from PySide import QtWebKit

class Browser (QtGui.QWidget):
    
    def __init__(self, *arg):
        super(Browser, self).__init__(*arg)
        vBox = QtGui.QVBoxLayout()
        
        self.webView = QtWebKit.QWebView(self)
        
        self.webView.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
        self.webView.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        
        self.webView.load(QtCore.QUrl("http://www.youtube.com/"))
        
        self.webView.linkClicked.connect( self.loadLinkClicked )
        self.webView.loadStarted.connect( self.onPageLoad )
        self.webView.show()
        
        vBox.addLayout( self._createToolbar() )
        vBox.addWidget(self.webView)
        
        self.setLayout( vBox )
        self.show()
        
    def loadLinkClicked(self, url):
        self.webView.load( url )
        print "Clicked: " + url.toString()
        
    def onPageLoad(self):
        print "Loading: " + self.webView.url().toString()
        
    def _createToolbar(self):
        self.edit = QtGui.QLineEdit(self)
        self.edit.show()
        
        ## Back button
        btnBack = QtGui.QPushButton(self)
        btnBack.setIcon(QtGui.QIcon("btnback-blue.png"))
        btnBack.setToolTip("<b>voltar</b>")
        btnBack.clicked.connect( self.webView.back )
        btnBack.show()
        
        ## Foward button
        btnForward = QtGui.QPushButton(self)
        btnForward.setIcon(QtGui.QIcon("btnforward-blue.png"))
        btnForward.setToolTip("<b>avançar</b>")
        btnForward.clicked.connect( self.webView.forward )
        btnForward.show()
        
        ## Refresh button
        btnRefresh = QtGui.QPushButton(self)
        btnRefresh.setIcon(QtGui.QIcon("btnrefresh-blue.png"))
        btnRefresh.setToolTip("<b>recarregar</b>")
        btnRefresh.clicked.connect( self.webView.reload )
        btnRefresh.show()
        
        ## Refresh button
        btnGo = QtGui.QPushButton(self)
        btnGo.setIcon(QtGui.QIcon("btnsearch-blue.png"))
        btnGo.setToolTip("<b>carregar</b>")
        btnGo.clicked.connect( self.loadPage )
        btnGo.show()
        
        hBoxLayout = QtGui.QHBoxLayout()
        hBoxLayout.addWidget(btnBack)
        hBoxLayout.addWidget(btnForward)
        hBoxLayout.addWidget(btnRefresh)
        
        hBoxLayout.addWidget(self.edit)
        hBoxLayout.addWidget(btnGo)
        return hBoxLayout
    
    def loadPage(self):
        url = QtCore.QUrl(self.edit.text())
        self.webView.load(url)
    

## ----------------------------------------------------------------
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = Browser()
    sys.exit(app.exec_())