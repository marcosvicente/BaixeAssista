# coding: utf-8
import sys, os, threading
from PySide import QtCore, QtGui

from swfplayer import FlowPlayer, JWPlayer
import mainLayout, uiDialogDl
import browser

from main.app import manager

from main.app.util import base
base.trans_install() # instala as traduções.

class DialogDl(QtGui.QDialog):
    
    def __init__(self, title="Dialog", parent=None):
        super(DialogDl, self).__init__(parent)
        
        self.uiDialog = uiDialogDl.Ui_Dialog()
        self.uiDialog.setupUi(self)
        
        self.setWindowTitle(title)
    
    def updateProgressValue(self, current, value):
        self.uiDialog.progressBar.value((current/value) * 100.0)
        
    def handleUpdate(self, message, sitemsg):
        self.uiDialog.infoProgress.setText(message)
        self.uiDialog.siteResponse.setHtml("<br/>"+sitemsg)
        
## --------------------------------------------------------------------------
class VLSignal(QtCore.QObject):
    responseChanged = QtCore.Signal(str, str)
    responseFinish = QtCore.Signal(bool)
    responseError = QtCore.Signal(str)
    
class VideoLoad(threading.Thread):
    events = VLSignal()
    
    """ Coleta informações iniciais necessárias para baixar o video """
    def __init__(self, manage, maxTry=8):
        threading.Thread.__init__(self)
        
        self.manage = manage
        self.maxTry = maxTry
        
    def run(self):
        try:
            response = self.manage.start(self.maxTry, recall=self.events.responseChanged.emit)
            self.events.responseFinish.emit( response )
        except Exception as error:
            self.events.responseError.emit(str(error))
            
## --------------------------------------------------------------------------
class Loader(QtGui.QMainWindow):
    def __init__(self):
        super(Loader, self).__init__()
        self.videoLoading = False
        
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
        self.uiMainWindow.btnStartDl.clicked.connect(self.startVideoDl)
        self.uiMainWindow.actionExit.triggered.connect(self.close)
        
        self.langActionGroup = QtGui.QActionGroup(self)
        self.langActionGroup.addAction(self.uiMainWindow.actionPortuguse)
        self.langActionGroup.addAction(self.uiMainWindow.actionEnglish)
        self.langActionGroup.addAction(self.uiMainWindow.actionSpanish)
        
        self.playerActionGroup = QtGui.QActionGroup(self)
        self.playerActionGroup.addAction(self.uiMainWindow.actionEmbedPlayer)
        self.playerActionGroup.addAction(self.uiMainWindow.actionExternalPlayer)
        
        #self.playerLoadActionGroup = QtGui.QActionGroup(self)
        #self.playerLoadActionGroup.addAction(self.uiMainWindow.actionLoadExternalPlayer)
        #self.playerLoadActionGroup.addAction(self.uiMainWindow.actionReloadPlayer)
        
        self.uiMainWindow.actionReloadPlayer.triggered.connect(self.reloadEmbedPlayer)
    
    def reloadEmbedPlayer(self):
        self.player["autostart"] = self.videoLoading
        self.player.reload()
        
    def closeEvent(self, event):
        # salvando as configurações do navegador no banco de dados
        self.browser.saveSettings()
    
    def startVideoDl(self):
        if not self.videoLoading:
            
            url = self.uiMainWindow.locationMainUrl.currentText()
            
            # opção para uso de arquivo temporário
            tempfile = self.uiMainWindow.tempFiles.isChecked()
            
            # opção de qualidade do vídeo
            videoQuality = self.uiMainWindow.videoQuality.currentIndex()
            
            # diretório onde serão salvos os arquivos de vídeos.
            videoDir = self.uiMainWindow.videoDir.text()
            
            # opção para o número de divisões iniciais da stream de vídeo
            videoSplitSize = self.uiMainWindow.videoSplitSize.value()
            
            try:
                # inicia o objeto princial: main_obj
                self.manage = manager.Manage(url, tempfile = tempfile, 
                                videoQuality = (videoQuality+1), #0+1=1
                                videoPath = videoDir, maxsplit = videoSplitSize)
            except Exception as err:
                QtGui.QMessageBox.information(self, self.tr("Error"), 
                        self.tr("An error occurred starting the download."
                                "\n\n%s"%err))
                return
            # -----------------------------------------------------------
            self.dialogDl = DialogDl(self.tr("Please wait"), self)
            self.dialogDl.show()
            
            videoLoad = VideoLoad( self.manage)
            
            videoLoad.events.responseChanged.connect( self.dialogDl.handleUpdate )
            videoLoad.events.responseFinish.connect( self.onStartVideoDl )
            videoLoad.events.responseError.connect( self.onStartVideoDlError )
            
            self.dialogDl.rejected.connect( self.manage.canceledl )
            videoLoad.start()
            
    def onStartVideoDl(self, reponse):
        self.videoLoading = reponse
        
        if self.videoLoading:
            self.handleStartupConnection( reponse )
            self.player.reload()
            self.dialogDl.close()
        else:
            self.dialogDl.setWindowTitle(self.tr("Download Faleid"))
            
    def onStartVideoDlError(self, err):
        self.dialogDl.close()
        print err
        
    def handleStartupConnection(self, default=False):
        """ controla o fluxo de criação e remoção de conexões """
        if self.videoLoading and not self.manage.isComplete():
            connection = self.manage.ctrConnection
            
            nActiveConn = connection.getnActiveConnection()
            nConnCtr = self.uiMainWindow.connectionActive.value()
            
            proxyDisable = self.uiMainWindow.proxyDisable.isChecked()
            numOfConn = nConnCtr - nActiveConn
            params = {
                "ratelimit": self.uiMainWindow.connectionSpeed.value(), 
                "timeout": self.uiMainWindow.connectionTimeout.value(),
                "typechange": self.uiMainWindow.connectionType.isChecked(), 
                "waittime": self.uiMainWindow.connectionSleep.value(),
                "reconexao": self.uiMainWindow.connectionAttempts
            }
            if numOfConn > 0: # adiciona novas conexões.
                if proxyDisable:
                    sm_id_list = connection.startConnectionWithoutProxy(numOfConn, **params)
                else:
                    if default:
                        sm_id_list =  connection.startConnectionWithoutProxy(1, **params)
                        sm_id_list += connection.startConnectionWithProxy(numOfConn-1, **params)
                    else:
                        sm_id_list = connection.startConnectionWithProxy(numOfConn, **params)
                        
                #for sm_id in sm_id_list:
                #self.detailControl.setInfoItem( sm_id )
                
            elif numOfConn < 0: # remove conexões existentes.
                for sm_id in connection.stopConnections( numOfConn ):
                    self.detailControl.removaItemConexao( sm_id )
                    
            else: # mudança dinânica dos parametros das conexões.
                connection.update( **params)
                
## --------------------------------------------------------------------------

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    translator = QtCore.QTranslator()
    translator.load('mainLayout_pt')
    app.installTranslator(translator)
    
    mw = Loader()
    mw.show()

    sys.exit(app.exec_())
    
    