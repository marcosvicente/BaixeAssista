# coding: utf-8
import sys, os
from PySide import QtCore, QtGui
import mainLayout
import browser

## --------------------------------------------------------------------------
class MainWindow(QtGui.QMainWindow):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        self.uiMainWindow = mainLayout.Ui_MainWindow()
        self.uiMainWindow.setupUi(self)
        
        self.setupUI()
        self.setupAction()
    
    def setupUI(self):
        self.setupTab()
        
    
    def setupTab(self):
        vBox = QtGui.QVBoxLayout()
        self.uiMainWindow.tabBrowser.setLayout( vBox )
        
        brw = browser.Browser( self.uiMainWindow.tabBrowser )
        vBox.addWidget(brw)
        
        
    def setupAction(self):
        self.uiMainWindow.actionExit.triggered.connect(self.close)
        
        self.uiMainWindow.actionEnglish.triggered.connect(self.changeTranslation)
        self.uiMainWindow.actionPortuguse.triggered.connect(self.changeTranslation)
        
    def changeTranslation(self):
        action = self.sender()
    
## --------------------------------------------------------------------------

app = QtGui.QApplication(sys.argv)

translator = QtCore.QTranslator()
translator.load('mainLayout_pt')
app.installTranslator(translator)

mw = MainWindow()
mw.show()

sys.exit(app.exec_())