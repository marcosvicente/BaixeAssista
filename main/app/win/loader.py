# coding: utf-8
import sys, os
import time, threading, configobj
from PySide import QtCore, QtGui
from main import settings

OldPixmap = QtGui.QPixmap
def pixmap(*args, **kwargs):
    """ hack para correção do caminho do pixmap """
    args = list(args)
    if isinstance(args[0],(str, unicode)):
        fileName = os.path.basename(args[0])
        args[0] = os.path.join(settings.IMAGES_DIR, fileName)
    return OldPixmap(*tuple(args), **kwargs)
QtGui.QPixmap = pixmap

import mainLayout, uiDialogDl
from tableRow import TableRow
from playerDialog import PlayerDialog
import browser

from main.app import manager
from main.app.util import base

base.trans_install() # instala as traduções.
       
## --------------------------------------------------------------------------
class DialogDl(QtGui.QDialog):
    
    def __init__(self, title="Dialog", parent=None):
        super(DialogDl, self).__init__(parent)
        
        self.uiDialog = uiDialogDl.Ui_Dialog()
        self.uiDialog.setupUi(self)
        
        self.setWindowTitle(title)
        
    @property
    def btnCancel(self):
        return self.uiDialog.buttonBox.button(QtGui.QDialogButtonBox.Cancel)
        
    def handleUpdate(self, message, sitemsg):
        self.uiDialog.infoProgress.setText(message)
        self.uiDialog.siteResponse.setHtml("<br/>"+sitemsg)
        
## --------------------------------------------------------------------------
class VLSignal(QtCore.QObject):
    responseUpdateUi     = QtCore.Signal()
    responseUpdateUiExit = QtCore.Signal()
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
                        return True
                if self.cancel: break
            except Exception as error:
                self.events.responseError.emit(str(error))
                break
        else:
            self.events.responseFinish.emit(False)
        return False
        
    def run(self):
        started = self._init()
        
        while started and not self.cancel:
            self.manage.update()
            self.events.responseUpdateUi.emit()
            time.sleep(0.01)
        # informa que o evento de atualização parou de correr.
        self.events.responseUpdateUiExit.emit()
        
## --------------------------------------------------------------------------
class Loader(QtGui.QMainWindow):
    configPath = os.path.join(settings.CONFIGS_DIR, "configs.cfg")
    
    def __init__(self):
        super(Loader, self).__init__()
        
        self.LOADING = False
        self.manage = None
        self.tableRows = {}
        self.config = {}
        
        self.uiMainWindow = mainLayout.Ui_MainWindow()
        self.uiMainWindow.setupUi(self)
        
        self.setupUI()
        self.setupAction()
        
    def closeEvent(self, event):
        # browser settings
        self.browser.saveSettings()
        # ui settings
        self.saveConfigUI()
        
    def updateUI(self):
        if self.LOADING:
            self.updateTable()
    
    def updateUIExit(self):
        if not self.LOADING:
            self.updateTableExit()
        
    def setupUI(self):
        self.setupTab()
        self.setupLocation()
        
        self.playerDialog = PlayerDialog(parent = self)
        self.playerDialog.hide()
        
        self.videoQualityList = [self.tr("Low"), self.tr("Normal"), self.tr("High")]
        self.uiMainWindow.videoQuality.addItems( self.videoQualityList )
        self.uiMainWindow.tempFileAction.addItems([self.tr("Just remove"), self.tr("Before remove, ask")])
        
        self.setupFilesView()
        
        # restaurando configurações.
        self.configUI()
        
    def setupAction(self):
        self.uiMainWindow.btnStartDl.clicked.connect(self.handleStartStopDl)
        self.uiMainWindow.actionExit.triggered.connect(self.close)
        
        self.uiMainWindow.btnToolDir.clicked.connect( self.handleVideoDir )
        
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
        
        self.playerDialog.btnReload.clicked.connect( self.playerReload )
        self.uiMainWindow.actionReloadPlayer.triggered.connect( self.playerReload )
        
        self.uiMainWindow.actionChooseExternalPlayer.triggered.connect(self.choosePlayerDir)
        
    def setupLocation(self):
        self.urlManager = manager.UrlManager()
        url, title = self.urlManager.getLastUrl()
        joinedUrl = self.urlManager.joinUrlDesc(url, title)
        
        self.getLocation().setEditText( joinedUrl )
        self.getLocation().setToolTip( title )
        
        self.getLocation().addItems(map(lambda d: self.urlManager.joinUrlDesc(d[0], d[1]), 
                                        self.urlManager.getUrlTitleList()))
        
    def setupFilesView(self):
        videosView = self.uiMainWindow.videosView
        videosView.setColumnCount(1)
        videosView.clear()
        fields = {
            "videoExt": self.tr("Video extension"),
            "videoSize": {
                "title": self.tr("Video size"), 
                "conversor": manager.StreamManager.format_bytes
            },
            "cacheBytesTotal": {
                "title": self.tr("Downloaded"), 
                "conversor": manager.StreamManager.format_bytes
            },
            "videoQuality": {
                "title": self.tr("Video quality"),
                "conversor": lambda v: self.videoQualityList[v]
            },
            "videoPath": self.tr("Video path")
        }        
        info = manager.ResumeInfo()
        queryset = info.objects.all()
        
        items = [QtGui.QTreeWidgetItem([q.title]) for q in queryset]
        values = queryset.values(*fields.keys())
        
        def children(element):
            listItems = []
            for key in element:
                title, value = fields[key], element[key]
                if type(title) is dict:
                    value = title["conversor"](value)
                    title = title["title"]
                item = QtGui.QTreeWidgetItem(["{0} ::: {1}".format(title, value)])
                listItems.append( item )
            return listItems
        
        for index, item in enumerate(items):
            item.addChildren(children(values[index]))
            
        videosView.addTopLevelItems( items )
        
    def setupTab(self):
        vBox = QtGui.QVBoxLayout()
        self.uiMainWindow.tabBrowser.setLayout( vBox )
        self.browser = browser.Browser(self)
        vBox.addWidget( self.browser )
        # --------------------------------------------------------
    
    def addTableRow(self, _id):
        """ agrupa items por linha """
        # relacionando  com o id para facilitar na atualização de dados
        self.tableRows[_id] = TableRow( self.uiMainWindow.connectionInfo )
        self.tableRows[_id].create()
        return self.tableRows[_id]
    
    def removeTableRow(self, _id):
        tableRow = self.tableRows.pop(_id)
        tableRow.clear()
    
    def clearTable(self):
        """ removendo todas as 'rows' e dados relacionandos """
        for _id in self.tableRows:
            self.tableRows[_id].clear()
        self.tableRows.clear()
    
    @base.protected()
    def updateTable(self):
        """ atualizando apenas as tabelas apresentadas na 'MainWindow' """
        for sm in self.manage.ctrConnection.getConnections():
            if not sm.wasStopped():
                values = map(lambda key: sm.info.get(sm.ident, key), 
                             manager.StreamManager.listInfo)
                self.tableRows[ sm.ident ].update(values = values)
        
        videoSizeFormated = manager.StreamManager.format_bytes(self.manage.getVideoSize())
        videoPercent = base.calc_percent(self.manage.getCacheSize(), self.manage.getVideoSize())
        
        self.uiMainWindow.videoTileInfo.setText(self.manage.getVideoTitle())
        self.uiMainWindow.videoSizeInfo.setText( videoSizeFormated )
        self.uiMainWindow.videoExtInfo.setText(self.manage.getVideoExt())
        
        self.uiMainWindow.progressBarInfo.setValue( videoPercent )
        
        self.uiMainWindow.downloadedFromInfo.setText(manager.StreamManager.format_bytes(self.manage.getCacheSize()))
        self.uiMainWindow.downloadedToInfo.setText( videoSizeFormated )
    
    def updateTableExit(self):
        """ atualização de saída das tabelas. desativando todos os controles """
        self.uiMainWindow.progressBarInfo.setValue(0.0)
        
    def getLocation(self):
        return self.uiMainWindow.location
        
    def playerReload(self):
        self.playerDialog.playerReload( self.LOADING )
    
    def choosePlayerDir(self, value=None):
        """ guardando o local do player externo nas configuração """
        filePath, filtr = QtGui.QFileDialog.getOpenFileName(self,
                            self.tr("Choose the location of the external player"), "", 
                            self.tr("All Files (*);;Exe Files (*.exe)"))
        
        self.config["Dirs"]["externalPlayerPath"] = filePath
        return filePath
    
    def handleVideoDir(self, value=None):
        fileName = QtGui.QFileDialog.getExistingDirectory(self,
                    self.tr("Choose the directory of videos"), "")
        self.uiMainWindow.videoDir.setText( fileName )
        
    def handleStartStopDl(self):
        """ chama o método de acordo com o estado do botão """
        if self.uiMainWindow.btnStartDl.isChecked():
            self.handleStartVideoDl()
        else:
            self.handleStopVideoDl()
        
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
            videoLoad.events.responseUpdateUiExit.connect( self.updateUIExit )
            
            self.DIALOG.rejected.connect( self.onStartVideoDlCancel )
            videoLoad.start()
            
    def handleStopVideoDl(self):
        """ termina todas as ações relacionadas ao download do vídeo atual """
        # cancela o 'loop' de atualização de dados
        self.videoLoad.setCancelDl(True)
        self.uiMainWindow.btnStartDl.setText(self.tr("Download"))
        self.DIALOG.close()
        
        if self.LOADING:
            self.clearTable()
            
            self.manage.ctrConnection.stopAllConnections()
            
            self.playerDialog.hide()
            self.playerDialog.player.pause()
            
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
                
            self.handleStartupConnection(default = reponse)
            
            self.playerDialog.show()
            self.playerReload()
            
            self.DIALOG.close()
            
            ##self.setupFilesView()
        else:
            self.DIALOG.setWindowTitle(self.tr("Download Faleid"))
            self.DIALOG.btnCancel.setText(self.tr("Ok"))
            
    def onStartVideoDlCancel(self):
        if not self.LOADING:
            self.videoLoad.setCancelDl(True)
            
            self.uiMainWindow.btnStartDl.setText(self.tr("Download"))
            self.uiMainWindow.btnStartDl.setChecked(False)
        
    def onStartVideoDlError(self, err):
        self.DIALOG.close()
        print err
        
    def handleStartupConnection(self, value=None, default=False):
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
                "reconexao": self.uiMainWindow.connectionAttempts.value()
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
                        
                for sm_id in sm_id_list:
                    self.addTableRow( sm_id )
                    
            elif numOfConn < 0: # remove conexões existentes.
                for sm_id in connection.stopConnections( numOfConn ):
                    self.removeTableRow( sm_id )
                    
            else: # mudança dinânica dos parametros das conexões.
                connection.update( **params)
    
    def setConfigDefaultSection(self, conf):
        conf.setdefault("Path", {})
        conf.setdefault("MenuUi", {})
        conf.setdefault("WidgetUi", {})
        conf.setdefault("Window", {})
        conf.setdefault("Lang", {})
    
    def setConfigDefaultWidget(self, conf):
        conf["MenuUi"].setdefault("actionEmbedPlayer", True)
        conf["MenuUi"].setdefault("actionExternalPlayer", False)
        
        conf["WidgetUi"].setdefault("connectionActive", 1)
        conf["WidgetUi"].setdefault("connectionSpeed", 35840)
        conf["WidgetUi"].setdefault("connectionTimeout", 60)
        conf["WidgetUi"].setdefault("connectionAttempts", 2)
        conf["WidgetUi"].setdefault("connectionSleep", 5)
        conf["WidgetUi"].setdefault("proxyDisable", True)
        conf["WidgetUi"].setdefault("connectionType", True)
        
        conf["WidgetUi"].setdefault("videoQuality", 1)
        conf["WidgetUi"].setdefault("tempFiles", True)
        conf["WidgetUi"].setdefault("tempFileAction", 0)
        conf["WidgetUi"].setdefault("videoSplitSize", 4)
        
        conf["Path"].setdefault("videoDir", settings.DEFAULT_VIDEOS_DIR)
        conf["Lang"].setdefault("code", "pt_BR")
        
    def configUI(self, path=None):
        self.config = conf = configobj.ConfigObj((path or self.configPath))
        self.setConfigDefaultSection( conf )
        self.setConfigDefaultWidget( conf )
        
        self.confMenuUi = menuUi = conf["MenuUi"]
        self.uiMainWindow.actionEmbedPlayer.setChecked(menuUi.as_bool("actionEmbedPlayer"))
        self.uiMainWindow.actionExternalPlayer.setChecked(menuUi.as_bool("actionExternalPlayer"))
        
        self.confWidgetUi = widgetUi = conf["WidgetUi"]
        self.uiMainWindow.connectionActive.setValue(widgetUi.as_int("connectionActive"))
        self.uiMainWindow.connectionSpeed.setValue(widgetUi.as_int("connectionSpeed"))
        self.uiMainWindow.connectionTimeout.setValue(widgetUi.as_int("connectionTimeout"))
        self.uiMainWindow.connectionAttempts.setValue(widgetUi.as_int("connectionAttempts"))
        self.uiMainWindow.connectionSleep.setValue(widgetUi.as_int("connectionSleep"))
        
        self.uiMainWindow.proxyDisable.setChecked(widgetUi.as_bool("proxyDisable"))
        self.uiMainWindow.connectionType.setChecked(widgetUi.as_bool("connectionType"))
        
        self.uiMainWindow.videoQuality.setCurrentIndex(widgetUi.as_int("videoQuality"))
        self.uiMainWindow.tempFiles.setChecked(widgetUi.as_bool("tempFiles"))
        self.uiMainWindow.tempFileAction.setCurrentIndex(widgetUi.as_int("tempFileAction"))
        self.uiMainWindow.videoSplitSize.setValue(widgetUi.as_int("videoSplitSize"))
        
        self.confPath = conf["Path"]
        self.uiMainWindow.videoDir.setText(self.confDirs["videoDir"])
        
    def saveConfigUI(self, path=None):
        if not base.security_save(self.configPath, _configobj=self.config):
            print "config save error!"
            
## --------------------------------------------------------------------------

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    translator = QtCore.QTranslator()
    translator.load('mainLayout_pt')
    app.installTranslator(translator)
    
    mw = Loader()
    mw.show()

    sys.exit(app.exec_())
    
    