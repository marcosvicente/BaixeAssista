# coding: utf-8
import sys, os, threading
from PySide import QtCore, QtGui
import time

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
    responseUpdateUi = QtCore.Signal()
    responseChanged  = QtCore.Signal(str, str)
    responseFinish   = QtCore.Signal(bool)
    responseError    = QtCore.Signal(str)
    
class VideoLoad(threading.Thread):
    events = VLSignal()
    
    """ Coleta informações iniciais necessárias para baixar o video """
    def __init__(self, manage, ntry=8):
        threading.Thread.__init__(self)
        self.cancel = False
        self.manage = manage
        self.ntry = ntry
        
    def setCancelDl(self, cancelled=True):
        self.cancel = cancelled
        
    def _init(self):
        for index in range(1, self.ntry+1):
            try:
                if self.manage.start(index, self.ntry, callback=self.events.responseChanged.emit):
                    if not self.cancel:
                        self.events.responseFinish.emit(True)
                        break
                if self.cancel: break
            except Exception as error:
                self.events.responseError.emit(str(error))
                break
        else:
            self.events.responseFinish.emit(False)
            
    def run(self):
        self._init()
        
        while not self.cancel:
            self.manage.update()
            self.events.responseUpdateUi.emit()
            time.sleep(0.01)
            
## --------------------------------------------------------------------------
class Loader(QtGui.QMainWindow):
    def __init__(self):
        super(Loader, self).__init__()
        
        self.LOADING = False
        self.manage = None
        
        self.uiMainWindow = mainLayout.Ui_MainWindow()
        self.uiMainWindow.setupUi(self)
        
        self.setupUI()
        self.setupAction()
    
    def setupUI(self):
        self.setupTab()
        self.setupLocation()
        
    def setupLocation(self):
        self.urlManager = manager.UrlManager()
        url, title = self.urlManager.getLastUrl()
        joinedUrl = self.urlManager.joinUrlDesc(url, title)
        
        self.getLocation().setEditText( joinedUrl )
        self.getLocation().setToolTip( title )
        
        self.getLocation().addItems(
            map(lambda d: self.urlManager.joinUrlDesc(d[0], d[1]), 
                self.urlManager.getUrlTitleList())
        )
            
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
        
    def getLocation(self):
        return self.uiMainWindow.location
    
    def closeEvent(self, event):
        # salvando as configurações do navegador no banco de dados
        self.browser.saveSettings()
        
    def setupAction(self):
        self.uiMainWindow.btnStartDl.clicked.connect(self.handleStartStopDl)
        self.uiMainWindow.actionExit.triggered.connect(self.close)
        
        ## self.handleStartupConnection
        self.uiMainWindow.connectionActive.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionSpeed.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionTimeout.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionSleep.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionAttempts.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionType.stateChanged.connect( self.handleStartupConnection )
        
        self.langActionGroup = QtGui.QActionGroup(self)
        self.langActionGroup.addAction(self.uiMainWindow.actionPortuguse)
        self.langActionGroup.addAction(self.uiMainWindow.actionEnglish)
        self.langActionGroup.addAction(self.uiMainWindow.actionSpanish)
        
        self.playerActionGroup = QtGui.QActionGroup(self)
        self.playerActionGroup.addAction(self.uiMainWindow.actionEmbedPlayer)
        self.playerActionGroup.addAction(self.uiMainWindow.actionExternalPlayer)
        
        self.uiMainWindow.actionReloadPlayer.triggered.connect(self.playerReload)
        self.uiMainWindow.actionChooseExternalPlayer.triggered.connect(self.choosePlayerDir)
        
    def playerReload(self):
        self.player["autostart"] = self.LOADING
        self.player.reload()
    
    def choosePlayerDir(self):
        fileName, filtr = QtGui.QFileDialog.getOpenFileName(self,
                        self.tr("Choose the location of the external player"), "", 
                        self.tr("All Files (*);;Exe Files (*.exe)"))
        print fileName
    
    def handleStartStopDl(self):
        """ chama o método de acordo com o estado do botão """
        isChecked = self.uiMainWindow.btnStartDl.isChecked()
        if isChecked: self.handleStartVideoDl()
        else: self.handleStopVideoDl()
        
    def handleStartVideoDl(self):
        """ inicia todo o processo de download e transferênica do video """
        if not self.LOADING:
            url = self.getLocation().currentText()
            url, title = self.urlManager.splitUrlDesc(url)
            
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
                
                self.uiMainWindow.btnStartDl.setChecked(False)
                return
            # -----------------------------------------------------------
            self.uiMainWindow.btnStartDl.setText(self.tr("Stop"))
            
            self.DIALOG = DialogDl(self.tr("Please wait"), self)
            self.DIALOG.show()
            
            self.videoLoad = videoLoad = VideoLoad(self.manage)
            
            videoLoad.events.responseChanged.connect( self.DIALOG.handleUpdate )
            videoLoad.events.responseFinish.connect( self.onStartVideoDl )
            videoLoad.events.responseError.connect( self.onStartVideoDlError )
            videoLoad.events.responseUpdateUi.connect( self.updateUI )
            
            self.DIALOG.rejected.connect( self.onStartVideoDlCancel )
            videoLoad.start()
            
    def handleStopVideoDl(self):
        """ termina todas as ações relacionadas ao download do vídeo atual """
        if self.LOADING:
            # cancela o 'loop' de atualização de dados
            self.videoLoad.setCancelDl(True)
            
            self.manage.ctrConnection.stopAllConnections()
            self.uiMainWindow.btnStartDl.setText(self.tr("Download"))
            
            self.player.pause()
            
            self.manage.stop_streamers()
            self.manage.delete_vars()
            
            self.LOADING = False
            self.manage = None
            
    def onStartVideoDl(self, reponse):
        self.LOADING = reponse
        
        if self.LOADING:
            # titulo do arquivo de video
            title = self.manage.getVideoTitle()
            url = self.manage.getUrl()
            
            self.getLocation().setToolTip( title )
            
            joinedUrl = self.urlManager.joinUrlDesc(url, title)
            self.getLocation().setEditText( joinedUrl )
            
            if self.getLocation().findText( joinedUrl ) < 0:
                self.getLocation().addItem(joinedUrl)
                
            self.handleStartupConnection( reponse )
            
            self.playerReload()
            self.DIALOG.close()
        else:
            self.DIALOG.setWindowTitle(self.tr("Download Faleid"))
    
    def onStartVideoDlCancel(self):
        if not self.LOADING:
            self.videoLoad.setCancelDl(True)
            
            self.uiMainWindow.btnStartDl.setText(self.tr("Download"))
            self.uiMainWindow.btnStartDl.setChecked(False)
        
    def onStartVideoDlError(self, err):
        self.DIALOG.close()
        print err
    
    def updateUI(self):
        print "Event UI"
        
    def handleStartupConnection(self, default=False):
        """ controla o fluxo de criação e remoção de conexões """
        if self.LOADING and not self.manage.isComplete():
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
    
    