# coding: utf-8
import sys, os
from PySide import QtCore, QtGui
from swfplayer import FlowPlayer, JWPlayer
import browser, mainLayout

## --------------------------------------------------------------------------
class Loader(QtGui.QMainWindow):
    
    def __init__(self):
        super(Loader, self).__init__()
        
        self.uiMainWindow = mainLayout.Ui_MainWindow()
        self.uiMainWindow.setupUi(self)
        
        self.setupUI()
        self.setupAction()
    
    def setupUI(self):
        self.setupTab()
        
    def setupTab(self):
        vBox = QtGui.QVBoxLayout()
        self.uiMainWindow.tabBrowser.setLayout( vBox )
        self.browser = browser.Browser(self)
        vBox.addWidget( self.browser )
        # --------------------------------------------------------
                
        vBox = QtGui.QVBoxLayout()
        self.uiMainWindow.tabPlayer.setLayout( vBox )
        self.player = FlowPlayer.Player(self)
        vBox.addWidget(self.player)
        
    def getLocationMainUrl(self):
        return self.uiMainWindow.locationMainUrl
        
    def setupAction(self):
        self.uiMainWindow.actionExit.triggered.connect(self.close)
        
        self.langActionGroup = QtGui.QActionGroup(self)
        self.langActionGroup.addAction(self.uiMainWindow.actionPortuguse)
        self.langActionGroup.addAction(self.uiMainWindow.actionEnglish)
        self.langActionGroup.addAction(self.uiMainWindow.actionSpanish)
        
        self.playerActionGroup = QtGui.QActionGroup(self)
        self.playerActionGroup.addAction(self.uiMainWindow.actionEmbedPlayer)
        self.playerActionGroup.addAction(self.uiMainWindow.actionExternalPlayer)
        
        self.playerLoadActionGroup = QtGui.QActionGroup(self)
        self.playerLoadActionGroup.addAction(self.uiMainWindow.actionLoadExternalPlayer)
        self.playerLoadActionGroup.addAction(self.uiMainWindow.actionReloadPlayer)
        
    def changeTranslation(self):
        action = self.sender()
    
    def closeEvent(self, event):
        # salvando as configurações do navegador no banco de dados
        self.browser.saveSettings()
        
## --------------------------------------------------------------------------

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    translator = QtCore.QTranslator()
    translator.load('mainLayout_pt')
    app.installTranslator(translator)
    
    mw = Loader()
    mw.show()

    sys.exit(app.exec_())
    
    