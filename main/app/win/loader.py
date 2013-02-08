#! /usr/bin/python
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
from playerDialog import PlayerDialog
from dialogError import DialogError
from dialogUpdate import DialogUpdate
from dialogRec import DialogRec
from tableRow import TableRow

import webbrowser
import browser
import glob

from main.app import manager
from main.app.util import base
from main.app import updater

def transUi_install(code):
    """ instala as traduções da interface gráfica """
    translator = QtCore.QTranslator()
    
    # pesquisando por todos os arquivo de tradução da ui.
    transfile = glob.glob(os.path.join(settings.APPDIR, "win", "locale", code, "*.qm"))
    
    for filepath in transfile:
        # carregando os arquivos de tradução.
        translator.load( filepath )
        
    return translator

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
        proxy = {}
        for index in range(1, self.ntry+1):
            try:
                if self.manage.start(index, self.ntry, proxy=proxy, 
                                     callback=self.events.responseChanged.emit):
                    if not self.cancel:
                        self.events.responseFinish.emit(True)
                        return True
                if self.cancel: break
            except Exception as error:
                self.events.responseError.emit(str(error))
                break
            proxy = self.manage.proxyManager.get_formated()
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
    developerEmail = "geniofuturo@gmail.com"
    
    releaseSource = "http://code.google.com/p/gerenciador-de-videos-online/downloads/list"
    configPath = os.path.join(settings.CONFIGS_DIR, "configs.cfg")
    
    baixeAssista = "BaixeAssista v%s"%settings.PROGRAM_VERSION
    config = configobj.ConfigObj( configPath )
    
    updateLock = threading.RLock()
    
    def __init__(self):
        super(Loader, self).__init__()
                
        self.uiMainWindow = mainLayout.Ui_MainWindow()
        self.uiMainWindow.setupUi(self)
        self.setWindowTitle(self.baixeAssista)
        
        self.tableRows = {}
        self.LOADING = False
        self.manage = self.mplayer = None
        
        self.setupUI()
        self.setupAction()
        
        # restaurando configurações da ui
        self.configUI()
        
        # iniciando a procura por atualizações.
        if self.uiMainWindow.actionAutomaticSearch.isChecked():
            self.onSearchUpdate(False)
        
    def onAbout(self):
        QtGui.QMessageBox.information(self, " - ".join([self.tr("About"), self.baixeAssista]),
          self.tr("BaixeAssista search uncomplicate viewing videos on the internet.\n"
                  "Developer: geniofuturo@gmail.com"))
    
    def onErroReporting(self):
        dialogError = DialogError()
        dialogError.setDeveloperEmail(self.developerEmail)
        dialogError.setModal(True)
        dialogError.exec_()
        
    def closeEvent(self, event):
        # browser settings
        self.browser.saveSettings()
        # ui settings
        self.saveSettings()
        
    def updateUI(self):
        if self.LOADING: self.updateTable()
        
    def updateUIExit(self):
        if not self.LOADING:
            self.updateTableExit()
        
    def setupUI(self):
        self.setupTab()
        self.setupLocation()
                
        self.videoQualityList = [self.tr("Low"), self.tr("Normal"), self.tr("High")]
        self.uiMainWindow.videoQuality.addItems( self.videoQualityList )
        self.uiMainWindow.tempFileAction.addItems([self.tr("Just remove"), self.tr("Before remove, ask")])
        
        self.setupFilesView()
        
    def setupAction(self):
        self.uiMainWindow.btnStartDl.clicked.connect(self.handleStartStopDl)
        self.uiMainWindow.actionExit.triggered.connect(self.close)
        
        self.uiMainWindow.btnToolDir.clicked.connect( self.handleVideoDir )
        self.uiMainWindow.refreshFiles.clicked.connect( self.setupFilesView )
        
        self.uiMainWindow.actionErroReporting.triggered.connect( self.onErroReporting )
        self.uiMainWindow.actionCheckNow.triggered.connect( self.onSearchUpdate )
        
        self.uiMainWindow.connectionActive.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionSpeed.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionTimeout.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionSleep.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionAttempts.valueChanged.connect( self.handleStartupConnection )
        self.uiMainWindow.connectionType.stateChanged.connect( self.handleStartupConnection )
        
        self.uiMainWindow.actionAbout.triggered.connect( self.onAbout )
        
        self.langActionGroup = QtGui.QActionGroup(self)
        self.langActionGroup.addAction(self.uiMainWindow.actionPortuguse)
        self.langActionGroup.addAction(self.uiMainWindow.actionEnglish)
        self.langActionGroup.addAction(self.uiMainWindow.actionSpanish)
        self.codeLang = {
            self.uiMainWindow.actionPortuguse: "pt_BR",
            self.uiMainWindow.actionEnglish: "en",
            self.uiMainWindow.actionSpanish: "es"
        }
        self.playerActionGroup = QtGui.QActionGroup(self)
        self.playerActionGroup.addAction(self.uiMainWindow.actionEmbedPlayer)
        self.playerActionGroup.addAction(self.uiMainWindow.actionExternalPlayer)
        
        self.uiMainWindow.actionEmbedPlayer.triggered.connect( self.onSetupVideoPlayer )
        self.uiMainWindow.actionExternalPlayer.triggered.connect( self.onSetupVideoPlayer )
        
        self.uiMainWindow.actionReloadPlayer.triggered.connect( self.playerReload )
        self.uiMainWindow.actionChooseExternalPlayer.triggered.connect(self.choosePlayerPath)
        
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
        queryset = manager.ResumeInfo.objects.all()
        
        items = [QtGui.QTreeWidgetItem([q.title+"."+q.videoExt]) for q in queryset]
        values = queryset.values(*fields.keys())
        
        def children(element):
            listItems = []
            for key in element:
                title, value = fields[key], element[key]
                if type(title) is dict:
                    value = title["conversor"](value)
                    title = title["title"]
                item = QtGui.QTreeWidgetItem([u"{0} ::: {1}".format(title, value)])
                listItems.append( item )
            return listItems
        
        for index, item in enumerate(items):
            item.addChildren(children(values[index]))
            
        videosView.addTopLevelItems( items )
        
    def setupTab(self):
        boxLayout = QtGui.QVBoxLayout()
        boxLayout.setContentsMargins(0, 0, 0, 0)
        boxLayout.setSpacing(0)
        
        self.uiMainWindow.tabBrowser.setLayout( boxLayout )
        self.browser = browser.Browser(self)
        boxLayout.addWidget( self.browser )
        
    def onPlayeView(self):
        item = self.uiMainWindow.videosView.currentItem()
        title = item.text(0)
        
        _title = os.path.splitext(title)[0]
        
        resumeInfo = manager.ResumeInfo(filename=_title)
        
        if not resumeInfo.isEmpty:
            fileManager = manager.FileManager(filename=_title,
                          filepath = resumeInfo["videoPath"],
                          fileext = resumeInfo["videoExt"])
            
            path = fileManager.getFilePath()
            print path, os.path.exists(path)
            
            if os.path.exists(path):
                mplayer = manager.FlvPlayer(cmd=self.getExternalPlayerPath(), 
                                            filepath=path)
                mplayer.start()
                
    def getExternalPlayerPath(self):
        if not os.path.exists(self.confPath["externalPlayer"]):
            path = self.choosePlayerPath()
        else:
            path = self.confPath["externalPlayer"]
        return path
                
        
    def onVideoRemove(self):
        item = self.uiMainWindow.videosView.currentItem()
        title = item.text(0)
        
        _title = os.path.splitext(title)[0]
        
        resumeInfo = manager.ResumeInfo(filename=_title)
        
        if not resumeInfo.isEmpty:
            fileManager = manager.FileManager(filename=_title,
                            filepath = resumeInfo["videoPath"],
                            fileext = resumeInfo["videoExt"])
            
            path = fileManager.getFilePath()
            print path, os.path.exists(path)
            
            self.urlManager.remove(_title)
            resumeInfo.remove()
            fileManager.remove()
            
            self.setupFilesView()
            
    def contextMenuEvent(self, event):
        icon = QtGui.QIcon(os.path.join(settings.IMAGES_DIR,"preview-doc.png"))
        actionPreview = QtGui.QAction(self.tr("preview"), self,
            statusTip = "", triggered = self.onPlayeView,
            icon = icon)
        
        icon = QtGui.QIcon(os.path.join(settings.IMAGES_DIR,"remove-db.png"))
        actionRemove = QtGui.QAction(self.tr("remove"), self,
            statusTip = "", triggered = self.onVideoRemove,
            icon = icon)
        
        menu = QtGui.QMenu(self)
        menu.addAction( actionPreview )
        menu.addAction( actionRemove )
        menu.exec_(event.globalPos())
        
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
        videoSizeFormated = manager.StreamManager.format_bytes(self.manage.getVideoSize())
        videoPercent = base.calc_percent(self.manage.getCacheBytesTotal(), self.manage.getVideoSize())
        
        self.uiMainWindow.videoTileInfo.setText(self.manage.getVideoTitle())
        self.uiMainWindow.videoSizeInfo.setText( videoSizeFormated )
        self.uiMainWindow.videoExtInfo.setText(self.manage.getVideoExt())
        
        self.uiMainWindow.progressBarInfo.setValue( videoPercent )
        
        self.uiMainWindow.downloadedFromInfo.setText(manager.StreamManager.format_bytes(self.manage.getCacheBytesTotal()))
        self.uiMainWindow.downloadedToInfo.setText( videoSizeFormated )
        self.uiMainWindow.globalSpeedInfo.setText(self.manage.getGlobalSpeed())
        self.uiMainWindow.globalEtaInfo.setText(self.manage.getGlobalEta())
        
    @base.protected()
    def updateConnectionUi(self, sender, **kwargs):
        """ interface de atualização das infos da conexão"""
        # conexão que emitiu o sinal através de 'Info'.
        sender = self.manage.ctrConnection.getById(sender)
        
        for name in kwargs["fields"]:
            col = manager.StreamManager.listInfo.index(name)
            value = manager.Info.get(sender.ident, name)
            self.tableRows[sender.ident].update(col=col, value=value)
        
    def updateTableExit(self):
        """ atualização de saída das tabelas. desativando todos os controles """
        self.uiMainWindow.progressBarInfo.setValue(0.0)
        
    def getLocation(self):
        return self.uiMainWindow.location
        
    def playerReload(self):
        try: self.mplayer.reload( self.LOADING )
        except: self.onSetupVideoPlayer()
        
    def choosePlayerPath(self, value=None):
        """ guardando o local do player externo nas configuração """
        filepath, filtr = QtGui.QFileDialog.getOpenFileName(self,
                            self.tr("Choose the location of the external player"), "", 
                            self.tr("All Files (*);;Exe Files (*.exe)"))
        if os.path.exists(filepath):
            self.confPath["externalPlayer"] = filepath
        else:
            QtGui.QMessageBox.warning(self, self.tr("choose a valid location!"), 
                self.tr("Operation canceled or informed way is not in the file system."))
        return filepath
    
    def handleVideoDir(self, value=None):
        currentDir = self.uiMainWindow.videoDir.text()
        videoDir = QtGui.QFileDialog.getExistingDirectory(self,
                    self.tr("Choose the directory of videos"), currentDir)
        self.uiMainWindow.videoDir.setText(
            videoDir if os.path.exists(videoDir) else (
                currentDir if os.path.exists(currentDir) else settings.DEFAULT_VIDEOS_DIR
                )
        )
    
    def setupVideoPlayer(self):
        url = "http://{0}:{1}/stream/file.flv"
        url = url.format(manager.Server.HOST, manager.Server.PORT)
        
        actionExternal = self.uiMainWindow.actionExternalPlayer
        actionEmbed = self.uiMainWindow.actionEmbedPlayer
        action = self.playerActionGroup.checkedAction()
        
        if action == actionEmbed:
            self.mplayer = PlayerDialog(parent=self)
            self.mplayer.btnReload.clicked.connect(self.playerReload)
            
        elif action == actionExternal:
            self.mplayer = manager.FlvPlayer(cmd=self.getExternalPlayerPath(), url=url)
            
    def onSetupVideoPlayer(self):
        if self.mplayer: self.mplayer.stop()
        self.setupVideoPlayer()
        if self.LOADING: self.mplayer.start()
        
    def handleStartStopDl(self):
        """ chama o método de acordo com o estado do botão """
        if self.uiMainWindow.btnStartDl.isChecked():
            self.handleStartVideoDl()
        else:
            self.handleStopVideoDl()
        
    def handleStartVideoDl(self):
        """ inicia todo o processo de download e transferênica do video """
        if not self.LOADING:
            self.setupVideoPlayer()
            
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
                        self.tr("An error occurred starting the download.")+"\n\n%s"%err)
                self.uiMainWindow.btnStartDl.setChecked(False)
                return
            # --------------------------------------------------
            self.uiMainWindow.btnStartDl.setText(self.tr("Stop"))
            self.DIALOG = DialogDl(self.tr("Please wait"), self)
            self.DIALOG.rejected.connect( self.onCancelVideoDl )
            self.DIALOG.show()
            
            self.videoLoad = videoLoad = VideoLoad(self.manage)
            videoLoad.events.responseChanged.connect( self.DIALOG.handleUpdate )
            videoLoad.events.responseFinish.connect( self.onStartVideoDl )
            videoLoad.events.responseError.connect( self.onErrorVideoDl )
            videoLoad.events.responseUpdateUi.connect( self.updateUI )
            videoLoad.events.responseUpdateUiExit.connect( self.updateUIExit )
            videoLoad.start()
            
    def handleStopVideoDl(self):
        """ termina todas as ações relacionadas ao download do vídeo atual """
        # cancela o 'loop' de atualização de dados
        self.videoLoad.setCancelDl(True)
        self.uiMainWindow.btnStartDl.setText(self.tr("Download"))
        self.DIALOG.close()
        
        if self.LOADING:
            self.tryRecoverFile()
            self.manage.ctrConnection.stopAll()
            
            self.clearTable()
            # Eventos gerados por atividade de conexões.
            manager.Info.update.disconnect(self.updateConnectionUi)
            
            self.mplayer.stop()
            self.manage.stop()
            
            self.LOADING = False
            self.manage = None
            
    def onStartVideoDl(self, reponse):
        self.LOADING = reponse
        
        if self.LOADING:
            # titulo do arquivo de video
            title = self.manage.getVideoTitle()
            url = self.manage.getVideoUrl()
            
            self.getLocation().setToolTip( title )
            
            joinedUrl = self.urlManager.joinUrlDesc(url, title)
            self.getLocation().setEditText( joinedUrl )
            
            if self.getLocation().findText( joinedUrl ) < 0:
                self.getLocation().addItem(joinedUrl)
                
            self.handleStartupConnection(default = reponse)
            self.mplayer.start()
            self.DIALOG.close()
            
            self.setupFilesView()
            
            # Eventos gerados por atividade de conexões.
            manager.Info.update.connect(self.updateConnectionUi)
        else:
            self.DIALOG.setWindowTitle(self.tr("Download Faleid"))
            self.DIALOG.btnCancel.setText(self.tr("Ok"))
            
    def onCancelVideoDl(self):
        if not self.LOADING:
            self.videoLoad.setCancelDl(True)
            
            self.uiMainWindow.btnStartDl.setText(self.tr("Download"))
            self.uiMainWindow.btnStartDl.setChecked(False)
        
    def onErrorVideoDl(self, err):
        self.DIALOG.close()
        print err
    
    @manager.FM_runLocked()
    def tryRecoverFile(self):
        isTempFile = self.uiMainWindow.tempFiles.isChecked()
        haveAsk = self.uiMainWindow.tempFileAction.currentIndex()
        
        if isTempFile and self.manage.isTempFileMode and haveAsk == 1:
            reply = QtGui.QMessageBox.question(self, self.tr("recovery of the temporary file"),
                   self.tr("The current video file is saved in a temporary file.\n"
                           "Want to save permanently ?"), 
                   QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
            
            if reply == QtGui.QMessageBox.Yes:
                dialog = DialogRec()
                dialog.setModal(True)
                dialog.show()
                
                dialog.textProgress.setText(self.tr("Processing..."))
                
                for copy in self.manage.recoverTempFile():
                    if copy.inProgress and not copy.sucess:
                        dialog.textProgress.setText("Processing %.2f%%"%copy.progress)
                        dialog.progressBar.setValue(copy.progress)
                    elif copy.sucess:
                        dialog.textProgress.setText(
                            self.tr("The video file was successfully recovered!"))
                        dialog.progressBar.setValue(100.0)
                        break
                    elif copy.error:
                        dialog.textProgress.setText(copy.get_msg())
                        dialog.progressBar.setValue(0.0)
                        break
                
                dialog.btnOK.setEnabled(True)
                dialog.btnCancel.setEnabled(False)
                dialog.exec_()
                
    def handleStartupConnection(self, value=None, default=False):
        """ controla o fluxo de criação e remoção de conexões """
        if self.LOADING and not self.manage.isComplete():
            connection = self.manage.ctrConnection
            nActiveConn = connection.countActive()
            
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
                    sm_id_list = connection.startWithoutProxy(numOfConn, **params)
                else:
                    if default:
                        sm_id_list =  connection.startWithoutProxy(1, **params)
                        sm_id_list += connection.startWithProxy(numOfConn-1, **params)
                    else:
                        sm_id_list = connection.startWithProxy(numOfConn, **params)
                        
                for sm_id in sm_id_list:
                    self.addTableRow( sm_id )
            elif numOfConn < 0: # remove conexões existentes.
                for sm_id in connection.stop( numOfConn ):
                    self.removeTableRow( sm_id )
            else: # mudança dinânica dos parametros das conexões.
                connection.update( **params)
    
    def setConfigDefault(self, conf):
        conf.setdefault("Path", {})
        conf.setdefault("MenuUi", {})
        conf.setdefault("WidgetUi", {})
        conf.setdefault("Window", {})
        conf.setdefault("Lang", {})
        conf.setdefault("Prog", {})
        
        conf["MenuUi"].setdefault("actionEmbedPlayer", True)
        conf["MenuUi"].setdefault("actionExternalPlayer", False)
        conf["MenuUi"].setdefault("actionExternalPlayer", False)
        conf["MenuUi"].setdefault("actionAutomaticSearch", True)
        
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
        
        conf["Window"].setdefault("position", [0, 0])
        conf["Window"].setdefault("size", [640, 480])
        
        conf["Path"].setdefault("videoDir", settings.DEFAULT_VIDEOS_DIR)
        conf["Lang"].setdefault("code", "en")
        
        conf["Prog"].setdefault("packetVersion", "1.6.9")
        
    def configUI(self):
        conf = self.config
        self.setConfigDefault( conf )
        
        self.confMenuUi = menuUi = conf["MenuUi"]
        self.uiMainWindow.actionEmbedPlayer.setChecked(menuUi.as_bool("actionEmbedPlayer"))
        self.uiMainWindow.actionExternalPlayer.setChecked(menuUi.as_bool("actionExternalPlayer"))
        self.uiMainWindow.actionAutomaticSearch.setChecked(menuUi.as_bool("actionAutomaticSearch"))
        
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
        
        self.confWindow = conf["Window"]
        self.move(*map(int, self.confWindow.as_list("position")))
        self.resize(*map(int, self.confWindow.as_list("size")))
        
        self.confPath = conf["Path"]
        self.uiMainWindow.videoDir.setText(self.confPath["videoDir"] 
                if os.path.exists(self.confPath["videoDir"]) else 
                    settings.DEFAULT_VIDEOS_DIR)
        
        self.confLang = conf["Lang"]
        # traduzindo 'code' em uma 'action' da ui.
        action = [action for action in self.codeLang if self.confLang["code"] == self.codeLang[action]]
        action[0].setChecked(True)
        
        self.confProg = conf["Prog"]
        
    def saveSettings(self, path=None):
        self.confMenuUi["actionEmbedPlayer"] = self.uiMainWindow.actionEmbedPlayer.isChecked()
        self.confMenuUi["actionExternalPlayer"] = self.uiMainWindow.actionExternalPlayer.isChecked()
        self.confMenuUi["actionAutomaticSearch"] = self.uiMainWindow.actionAutomaticSearch.isChecked()
        
        self.confWidgetUi["connectionActive"] = self.uiMainWindow.connectionActive.value()
        self.confWidgetUi["connectionSpeed"] = self.uiMainWindow.connectionSpeed.value()
        self.confWidgetUi["connectionTimeout"] = self.uiMainWindow.connectionTimeout.value()
        self.confWidgetUi["connectionAttempts"] = self.uiMainWindow.connectionAttempts.value()
        self.confWidgetUi["connectionSleep"] = self.uiMainWindow.connectionSleep.value()
        self.confWidgetUi["proxyDisable"] = self.uiMainWindow.proxyDisable.isChecked()
        self.confWidgetUi["connectionType"] = self.uiMainWindow.connectionType.isChecked()
        
        self.confWidgetUi["videoQuality"] = self.uiMainWindow.videoQuality.currentIndex()
        self.confWidgetUi["tempFiles"] =  self.uiMainWindow.tempFiles.isChecked()
        self.confWidgetUi["tempFileAction"] = self.uiMainWindow.tempFileAction.currentIndex()
        self.confWidgetUi["videoSplitSize"] = self.uiMainWindow.videoSplitSize.value()
        
        if not self.isMaximized():
            self.confWindow["position"] = self.pos().toTuple()
            self.confWindow["size"] = self.size().toTuple()
            
        self.confPath["videoDir"] = self.uiMainWindow.videoDir.text()
        
        # traduzindo a 'action' da ui em um código de linguagem.
        self.confLang["code"] = self.codeLang[self.langActionGroup.checkedAction()]
        
        # salvando as configurações no arquivo
        if not base.security_save((path or self.configPath), _configobj=self.config):
            print "*** Warnnig: config save error!"
            
    def onShowResultInfo(self, title, text):
        QtGui.QMessageBox.information(self, title, text)
        
    def onReleasedFound(self, response):
        response += _(u"\nPressione OK para ir a página de download.")
        reply = QtGui.QMessageBox.information(self, _("Novidade!"),
            response, buttons = QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel
            )
        if reply == QtGui.QMessageBox.Ok:
            webbrowser.open_new_tab(self.releaseSource)
            
    def showDialogUpdate(self, response, changes, version):
        automatic = self.uiMainWindow.actionAutomaticSearch.isChecked()
        self.confProg["packetVersion"] = version
        
        title = _(u"Ativada)") if automatic else _(u"Desativada)")
        title = _(u"Novas atualizações recebidas! (Atualização automática - ") + title
        
        dialogUpdate = DialogUpdate(self)
        dialogUpdate.setWindowTitle(title)
        dialogUpdate.setTextInfo(response)
        dialogUpdate.setTextChanges(changes)
        dialogUpdate.exec_()
        
    def onSearchUpdate(self, showWin=True):
        """ inicia a procura por atualizações """
        if self.sender() == self.uiMainWindow.actionAutomaticSearch:
            automatic = self.uiMainWindow.actionAutomaticSearch.isChecked()
            self.confMenuUi["actionAutomaticSearch"] = automatic
            return
        search = SearchUpdate(self.confProg["packetVersion"], 
                              self.confLang["code"], self, showWin)
        search.updateFound.connect(self.showDialogUpdate)
        search.releaseFound.connect(self.onReleasedFound)
        search.resultInfo.connect(self.onShowResultInfo)
        search.start()
        
## --------------------------------------------------------------------------------
class SearchUpdate(QtCore.QObject, threading.Thread):
    resultInfo   = QtCore.Signal(str, str)
    releaseFound = QtCore.Signal(str)
    updateFound  = QtCore.Signal(str, str, str)
    
    def __init__(self, version, code, parent=None, showWin=False):
        QtCore.QObject.__init__(self, parent)
        threading.Thread.__init__(self)
        self.showWin = showWin
        self.version = version
        self.code = code
        
    def check_release(self):
        """ iniciando a procura por uma nova versão do programa """
        rel = updater.Release()
        result, response = rel.search()
        
        if result: self.releaseFound.emit(response)
        elif result is False and self.showWin:
            self.resultInfo.emit(_("Ainda em desenvolvimento..."), response)
        elif result is None and self.showWin:
            self.resultInfo.emit(_("Error"), response)
            
    def run(self):
        self.check_release()
        upd = updater.Updater(packetVersion = self.version)
        if upd.search():
            # começa o download da atualização
            result, response = upd.download()
            
            if result:
                # texto informando as mudanças que a nova atualização fez.
                changes = upd.getLastChanges( self.code )
                
                # aplica a atualização
                result, response = upd.update()
                
                # remove todos os arquivos
                upd.cleanUpdateDir()
                
                if result:
                    self.updateFound.emit(response,"\n\n".join(changes), upd.getNewVersion())
                    
                elif self.showWin:
                    self.resultInfo.emit(_("Atualizando."), response)
                    
            elif self.showWin:
                self.resultInfo.emit(_("Baixando pacote."), response)
                
        elif self.showWin and upd.isOldRelease():
            self.resultInfo.emit(_("Programa atualizado."), upd.warning)
            
## --------------------------------------------------------------------------

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    base.trans_install()
    
    # pesquisando por todos os arquivo de tradução da ui.
    filename = "en_%s-py.qm" % Loader.config["Lang"]["code"]
    filepath = os.path.join(settings.INTERFACE_DIR, "i18n", filename)
    
    translator = QtCore.QTranslator()
    print "TL: ", translator.load( filepath )
    app.installTranslator(translator)
    
    mw = Loader()
    mw.show()

    sys.exit(app.exec_())
    
    