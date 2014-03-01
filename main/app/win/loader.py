# coding: utf-8
import sys
import os
import webbrowser
import time
import threading

import configobj
from PySide import QtCore, QtGui


OldPixmap = QtGui.QPixmap


def pixmap(*args, **kwargs):
    """ hacke para correção do caminho do pixmap """
    args = list(args)
    if isinstance(args[0], str):
        fileName = os.path.basename(args[0])
        args[0] = os.path.join(settings.IMAGES_DIR, fileName)
    return OldPixmap(*tuple(args), **kwargs)


QtGui.QPixmap = pixmap

from . import mainLayout
from . import uiDialogDl
from . import browser

from .paypalDonation import DialogDonate
from .dialogUpdate import DialogUpdate
from .playerDialog import PlayerDialog
from .dialogAbout import DialogAbout
from .dialogError import DialogError
from .dialogRec import DialogRec
from .tableRow import TableRow

from main.app.manager.streamManager import StreamManager
from main.app.manager.fileManager import FileManager
from main.app.manager.resumeInfo import ResumeInfo
from main.app.manager.flvPlayer import FlvPlayer
from main.app.manager.urls import UrlManager
from main.app.manager.manage import Manage
from main.app.manager.server import Server
from main.app.manager.info import Info
from main.app.util import base
from main.app import updater
from main import settings


class DialogDl(QtGui.QDialog):
    def __init__(self, title="Dialog", parent=None):
        super(DialogDl, self).__init__(parent)

        self.uiDialog = uiDialogDl.Ui_Dialog()
        self.uiDialog.setupUi(self)

        self.setWindowTitle(title)

    @property
    def btnCancel(self):
        return self.uiDialog.buttonBox.button(QtGui.QDialogButtonBox.Cancel)

    @property
    def siteResponse(self):
        return self.uiDialog.siteResponse

    def handleUpdate(self, textInfo, siteInfo):
        self.uiDialog.infoProgress.setText(textInfo)
        if siteInfo: self.siteResponse.setHtml(siteInfo)


class VideoLoad(threading.Thread, QtCore.QObject):
    """ Coleta informações iniciais necessárias para baixar o video """
    responseUpdateUi = QtCore.Signal()
    responseUpdateUiExit = QtCore.Signal()
    responseChanged = QtCore.Signal(str, str)
    responseFinish = QtCore.Signal(bool)
    responseError = QtCore.Signal(str)

    def __init__(self, manage, ntry=8):
        threading.Thread.__init__(self)
        QtCore.QObject.__init__(self)

        self.cancel = False
        self.manage = manage
        self.ntry = ntry

    def setCancelDl(self, cancelled=True):
        self.cancel = cancelled

    def _init(self):
        proxy = {}
        for index in range(1, self.ntry + 1):
            try:
                if self.manage.start(index, self.ntry, proxy=proxy,
                                     callback=self.responseChanged.emit):
                    if not self.cancel:
                        self.responseFinish.emit(True)
                        return True
                if self.cancel: break
            except Exception as error:
                self.responseError.emit(str(error))
                break
            proxy = self.manage.proxy_manager.get_formated()
        else:
            self.responseFinish.emit(False)
        return False

    def run(self):
        started = self._init()

        while started and not self.cancel:
            self.manage.update()
            self.responseUpdateUi.emit()
            time.sleep(0.01)
        # informa que o evento de atualização parou de correr.
        self.responseUpdateUiExit.emit()


## --------------------------------------------------------------------------
class Loader(QtGui.QMainWindow):
    developerEmail = "geniofuturo@gmail.com"

    releaseSource = "http://code.google.com/p/gerenciador-de-videos-online/downloads/list"
    configPath = os.path.join(settings.CONFIGS_DIR, "configs.cfg")

    baixeAssista = "BaixeAssista v%s" % settings.PROGRAM_VERSION
    config = configobj.ConfigObj(configPath)
    table_rows = {}

    def __init__(self):
        super(Loader, self).__init__()

        self.uiMainWindow = mainLayout.Ui_MainWindow()
        self.uiMainWindow.setupUi(self)
        self.setWindowTitle(self.baixeAssista)

        self.is_loading = self.WCLOSE = False
        self.manage = self.mplayer = None

        self.setupUI()
        self.setupAction()

        # restaurando configurações da ui
        self.configUI()

        QtCore.QTimer.singleShot(1000 * 3, self._initAfter)

        # Eventos gerados por atividade de conexões.
        Info.update.connect(self.update_connection_ui)

    def __del__(self):
        del self.browser
        super(Loader, self).__del__()

    def onAbout(self):
        about = DialogAbout(self, title=" - ".join([self.tr("About"), self.baixeAssista]))
        about.setDevInfoText(self.tr("BaixeAssista search uncomplicate viewing videos on the internet.\n"
                                     "Developer: geniofuturo@gmail.com"))
        about.btnMakeDonation.clicked.connect(self.showDonationDialog)
        about.exec_()

    def onErroReporting(self):
        dialogError = DialogError()
        dialogError.setDeveloperEmail(self.developerEmail)
        dialogError.setModal(True)
        dialogError.exec_()

    def closeEvent(self, event):
        if self.is_loading:
            # salvando o arquivo atualmente sendo baixado.
            self.WCLOSE = True

            self.stop_video_dl()
            event.ignore()
        else:
            # browser settings
            self.browser.saveSettings()

            # ui settings
            self.saveSettings()

    def on_update_ui(self):
        if self.is_loading:
            self.update_table()

    def on_update_ui_exit(self):
        if not self.is_loading: self.update_table_exit()

    def showDonationDialog(self, event=None, show=True):
        """ show: mostra o diálogo independente da decisão do usuário """
        if show or self.confWindow.as_bool("donationBoxIsOn"):
            donate = DialogDonate(self)
            donate.setOff(not self.confWindow.as_bool("donationBoxIsOn"))
            donate.exec_()

            # atualizando com decisão do usuário. sempre respeite isso!
            self.confWindow["donationBoxIsOn"] = donate.isOn

    def _initAfter(self):
        self.showDonationDialog(show=False)

        # iniciando a procura por atualizações.
        if self.uiMainWindow.actionAutomaticSearch.isChecked():
            self.onSearchUpdate(False)

    def setupUI(self):
        # o player externo terá uma instância única.
        self.embedPlayer = PlayerDialog(parent=self, configs=self.config)
        self.embedPlayer.btnReload.clicked.connect(self.reload_player)
        self.embedPlayer.hide()

        self.setup_tab()
        self.setup_location()

        self.videoQualityList = [self.tr("Low"), self.tr("Normal"), self.tr("High")]
        self.uiMainWindow.videoQuality.addItems(self.videoQualityList)
        self.uiMainWindow.tempFileAction.addItems([self.tr("Just remove"), self.tr("Before remove, ask")])

        self.setup_view_files()

    def setupAction(self):
        self.uiMainWindow.btnStartDl.clicked.connect(self.on_start_stop_handle)
        self.uiMainWindow.actionExit.triggered.connect(self.close)

        self.uiMainWindow.btnToolDir.clicked.connect(self.handle_video_dir)
        self.uiMainWindow.refreshFiles.clicked.connect(self.setup_view_files)

        self.uiMainWindow.actionErroReporting.triggered.connect(self.onErroReporting)
        self.uiMainWindow.actionCheckNow.triggered.connect(self.onSearchUpdate)

        self.uiMainWindow.connectionActive.valueChanged.connect(self.startup_connection_handle)
        self.uiMainWindow.connectionSpeed.valueChanged.connect(self.startup_connection_handle)
        self.uiMainWindow.connectionTimeout.valueChanged.connect(self.startup_connection_handle)
        self.uiMainWindow.connectionSleep.valueChanged.connect(self.startup_connection_handle)
        self.uiMainWindow.connectionAttempts.valueChanged.connect(self.startup_connection_handle)
        self.uiMainWindow.connectionType.stateChanged.connect(self.startup_connection_handle)

        self.uiMainWindow.actionAbout.triggered.connect(self.onAbout)

        self.langActionGroup = QtGui.QActionGroup(self)
        self.langActionGroup.addAction(self.uiMainWindow.actionPortuguse)
        self.langActionGroup.addAction(self.uiMainWindow.actionEnglish)
        self.langActionGroup.addAction(self.uiMainWindow.actionSpanish)

        self.codeLang = {self.uiMainWindow.actionPortuguse: "pt_BR",
                         self.uiMainWindow.actionEnglish: "en_US",
                         self.uiMainWindow.actionSpanish: "es_ES"}

        # action para a alteração do idioma
        self.langActionGroup.triggered.connect(self.on_locale_change)

        self.playerActionGroup = QtGui.QActionGroup(self)
        self.playerActionGroup.addAction(self.uiMainWindow.actionEmbedPlayer)
        self.playerActionGroup.addAction(self.uiMainWindow.actionExternalPlayer)

        self.playerActionGroup.triggered.connect(self.on_setup_player)

        self.uiMainWindow.actionReloadPlayer.triggered.connect(self.reload_player)
        self.uiMainWindow.actionChooseExternalPlayer.triggered.connect(self.choose_player_path)

    @base.LogOnError
    def setup_location(self):
        """ adiciona as urls dos vídeos baixados e adcionandos ao bd. """
        self.url_manager = UrlManager()
        self.get_location().addItems(
            [self.url_manager.joinUrlDesc(*items) for items in self.url_manager.getUrlTitleList()])
        url, title = self.url_manager.getLastUrl()
        joinedUrl = self.url_manager.joinUrlDesc(url, title)

        index = self.get_location().findText(joinedUrl)
        self.get_location().setCurrentIndex(index)

        # inserindo a ultima url adicionada na visualização padrão.
        self.get_location().setEditText(joinedUrl)
        self.get_location().setToolTip(title)

    def on_locale_change(self):
        """ Como o idioma está sendo feito na inicialização, apenas avisa para reinicializar """
        QtGui.QMessageBox.information(self, self.tr("about changing the language"),
                                      self.tr(
                                          "You need to manually restart the program for the new language to take effect."))

    @base.LogOnError
    def setup_view_files(self):
        video_view = self.uiMainWindow.videosView
        video_view.setColumnCount(1)
        video_view.clear()
        fields = {
            "videoExt": self.tr("Video extension"),
            "videoSize": {
                "title": self.tr("Video size"),
                "conversor": StreamManager.format_bytes
            },
            "cacheBytesTotal": {
                "title": self.tr("Downloaded"),
                "conversor": StreamManager.format_bytes
            },
            "videoQuality": {
                "title": self.tr("Video quality"),
                "conversor": lambda v: self.videoQualityList[v]
            },
            "videoPath": self.tr("Video path")
        }
        queryset = ResumeInfo.objects.all()

        items = [QtGui.QTreeWidgetItem([q.title + "." + q.videoExt]) for q in queryset]
        values = queryset.values(*list(fields.keys()))

        def children(element):
            list_item = []
            for key in element:
                title, value = fields[key], element[key]
                if type(title) is dict:
                    value = title["conversor"](value)
                    title = title["title"]
                obj = QtGui.QTreeWidgetItem(["{0} ::: {1}".format(title, value)])
                list_item.append(obj)
            return list_item

        for index, item in enumerate(items):
            item.addChildren(children(values[index]))

        video_view.addTopLevelItems(items)

    def setup_tab(self):
        box_layout = QtGui.QVBoxLayout()
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(0)

        self.uiMainWindow.tabBrowser.setLayout(box_layout)
        self.browser = browser.Browser(self)
        box_layout.addWidget(self.browser)

    def on_player_view(self):
        """ iniciializa a visualização do vídeo(selecionado) através do player externo. """
        item = self.uiMainWindow.videosView.currentItem()

        title = os.path.splitext(item.text(0))[0]
        resume_info = ResumeInfo(filename=title)

        if not resume_info.is_empty:
            file_manager = FileManager(
                filename=title, filepath=resume_info["videoPath"],
                fileext=resume_info["videoExt"]
            )
            path = file_manager.getFilePath()
            print((path, os.path.exists(path)))

            if os.path.exists(path):
                mplayer = FlvPlayer(cmd=self.get_external_player_path(), filepath=path)
                mplayer.start()

    def get_external_player_path(self):
        """ valida e retorna o local do player externo """
        if not os.path.exists(self.confPath["externalPlayer"]):
            path = self.choose_player_path()
        else:
            path = self.confPath["externalPlayer"]
        return path

    def on_video_remove(self):
        """ remove o video selecionando """
        item = self.uiMainWindow.videosView.currentItem()
        title = os.path.splitext(item.text(0))[0]

        resume_info = ResumeInfo(filename=title)

        if not resume_info.is_empty:
            file_manager = FileManager(
                filename=title, filepath=resume_info["videoPath"],
                fileext=resume_info["videoExt"]
            )
            path = file_manager.getFilePath()
            print((path, os.path.exists(path)))

            self.url_manager.remove(title)
            resume_info.remove()
            file_manager.remove()

            self.setup_view_files()

    def contextMenuEvent(self, event):
        if self.uiMainWindow.tabFiles == self.uiMainWindow.tabPanel.currentWidget():
            ## cria o menu para visualização e remoção de arquivos

            icon = QtGui.QIcon(os.path.join(settings.IMAGES_DIR, "preview-doc.png"))
            actionPreview = QtGui.QAction(self.tr("preview"), self,
                                          statusTip="", triggered=self.on_player_view,
                                          icon=icon)

            icon = QtGui.QIcon(os.path.join(settings.IMAGES_DIR, "remove-db.png"))
            actionRemove = QtGui.QAction(self.tr("remove"), self,
                                         statusTip="", triggered=self.on_video_remove,
                                         icon=icon)

            menu = QtGui.QMenu(self)
            menu.addAction(actionPreview)
            menu.addAction(actionRemove)
            menu.exec_(event.globalPos())

    def add_table_row(self, ident):
        """ Agrupa items por linha """
        # relacionando  com o id para facilitar na atualização de dados
        self.table_rows[ident] = TableRow(self.uiMainWindow.connectionInfo)
        self.table_rows[ident].create(wCol=StreamManager.list_info.index("percent"))
        return self.table_rows[ident]

    def remove_table_row(self, identify):
        row = self.table_rows.pop(identify)
        row.clear()

    def clear_table(self):
        """ removendo todas as 'rows' e dados relacionandos """
        for identify in list(self.table_rows.keys()):
            self.remove_table_row(identify)

    @base.Protected
    def update_table(self):
        """ Atualizando apenas as tabelas apresentadas na 'MainWindow' """
        video_size_formatted = StreamManager.format_bytes(self.manage.get_video_size())
        video_percent = base.calc_percent(self.manage.get_cache_bytes_total(), self.manage.get_video_size())

        self.uiMainWindow.videoTileInfo.setText(self.manage.get_video_title())
        self.uiMainWindow.videoSizeInfo.setText(video_size_formatted)
        self.uiMainWindow.videoExtInfo.setText(self.manage.get_video_ext())

        self.uiMainWindow.progressBarInfo.setValue(video_percent)

        self.uiMainWindow.downloadedFromInfo.setText(StreamManager.format_bytes(self.manage.get_cache_bytes_total()))
        self.uiMainWindow.downloadedToInfo.setText(video_size_formatted)
        self.uiMainWindow.globalSpeedInfo.setText(self.manage.get_global_speed())
        self.uiMainWindow.globalEtaInfo.setText(self.manage.get_global_eta())

    @base.Protected
    def update_connection_ui(self, identify, **kwargs):
        """ Interface de atualização das infos da conexão """
        if identify in self.table_rows:
            for name in kwargs["fields"]:
                self.table_rows[identify].update(
                    col=StreamManager.list_info.index(name),
                    value=Info.get(identify, name)
                )

    def update_table_exit(self):
        """ atualização de saída das tabelas. desativando todos os controles """
        self.uiMainWindow.progressBarInfo.setValue(0.0)

    def get_location(self):
        """ Controle principal para entradas de urls """
        return self.uiMainWindow.location

    def reload_player(self):
        try:
            self.mplayer.reload(autostart=self.is_loading)
        except:
            self.on_setup_player()

    def choose_player_path(self, value=None):
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

    def handle_video_dir(self, value=None):
        current_dir = self.uiMainWindow.videoDir.text()
        video_dir = QtGui.QFileDialog.getExistingDirectory(self,
                                                           self.tr("Choose the directory of videos"), current_dir)
        self.uiMainWindow.videoDir.setText(
            video_dir if os.path.exists(video_dir) else (
                current_dir if os.path.exists(current_dir) else settings.DEFAULT_VIDEOS_DIR
            )
        )

    def setup_player(self):
        url = "http://{0}:{1}/stream/file.flv"
        url = url.format(Server.HOST, Server.PORT)

        action_external = self.uiMainWindow.actionExternalPlayer
        action_embed = self.uiMainWindow.actionEmbedPlayer
        action = self.playerActionGroup.checkedAction()

        if action == action_embed:  # referencia embutido.
            self.mplayer = self.embedPlayer

        elif action == action_external:
            self.mplayer = FlvPlayer(cmd=self.get_external_player_path(), url=url)

    def on_setup_player(self):
        if self.mplayer:
            self.mplayer.stop()
        self.setup_player()
        if self.is_loading:
            self.mplayer.start()

    def on_start_stop_handle(self):
        """ chama o método de acordo com o estado do botão """
        if self.uiMainWindow.btnStartDl.isChecked():
            self.start_video_dl()
        else:
            self.stop_video_dl()

    @base.LogOnError
    def start_video_dl(self):
        """ inicia todo o processo de download e transferênica do video """
        if not self.is_loading:
            self.change_button_dl_state("Stop", True)
            self.setup_player()

            url = self.get_location().currentText()
            url, title = self.url_manager.splitUrlDesc(url)

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
                self.manage = Manage(url, tempfile=tempfile,
                                     videoQuality=videoQuality, videoPath=videoDir,
                                     maxsplit=videoSplitSize)
            except Exception as err:
                QtGui.QMessageBox.information(self, self.tr("Error"),
                                              "{!s}\n\n{!s}".format(self.tr("An error occurred starting the download."),
                                                                    err))
                self.change_button_dl_state("Download", False)
                return  # failed
            self.dialog = DialogDl(self.tr("Please wait"), self)
            self.dialog.rejected.connect(self.on_cancel_video_handle)
            self.dialog.show()

            self.videoLoad = VideoLoad(self.manage)
            self.videoLoad.responseChanged.connect(self.dialog.handleUpdate)
            self.videoLoad.responseFinish.connect(self.on_start_video_handle)
            self.videoLoad.responseError.connect(self.on_error_video_handle)
            self.videoLoad.responseUpdateUi.connect(self.on_update_ui)
            self.videoLoad.responseUpdateUiExit.connect(self.on_update_ui_exit)
            self.videoLoad.start()

    def change_button_dl_state(self, text, checked):
        """ modifica o estado e o texto do botão inicializador do download """
        self.uiMainWindow.btnStartDl.setText(self.tr(text))
        self.uiMainWindow.btnStartDl.setChecked(checked)

    def stop_video_dl(self):
        """ termina todas as ações relacionadas ao download do vídeo atual """
        if self.is_loading:
            self.recover_tempfile()

            self.videoLoad.setCancelDl(True)  # emit cancel
            self.change_button_dl_state("Download", False)
            self.manage.ctrConnection.stopAll()

            self.clear_table()
            self.mplayer.stop()
            self.manage.stop()

            self.is_loading = False
            self.manage = None

            if self.WCLOSE:
                self.destroy()
        else:
            self.on_cancel_video_handle()

    def on_start_video_handle(self, response):
        self.is_loading = response

        if self.is_loading:
            self.dialog.close()

            # titulo do arquivo de video
            title = self.manage.get_video_title()
            url = self.manage.get_video_url()

            self.get_location().setToolTip(title)

            joined_url = self.url_manager.joinUrlDesc(url, title)
            self.get_location().setEditText(joined_url)

            if self.get_location().findText(joined_url) < 0:
                self.get_location().addItem(joined_url)
            self.startup_connection_handle(default=response)

            self.mplayer.start(autostart=self.is_loading)
            self.setup_view_files()
        else:
            self.dialog.setWindowTitle(self.tr("Download Failed"))
            self.dialog.btnCancel.setText(self.tr("Ok"))

    def on_cancel_video_handle(self):
        if not self.is_loading:
            self.videoLoad.setCancelDl(True)  # emit cancel
            self.change_button_dl_state("Download", False)
            self.dialog.close()

    def on_error_video_handle(self, err):
        self.dialog.close()
        print(err)

    @FileManager.sincronize
    def recover_tempfile(self):
        checked_tempfile = self.uiMainWindow.tempFiles.isChecked()
        ask = bool(self.uiMainWindow.tempFileAction.currentIndex())

        if ask and checked_tempfile and self.manage.is_tempfile_mode:
            reply = QtGui.QMessageBox.question(self, self.tr("recovery of the temporary file"),
                                               self.tr("The current video file is saved in a temporary file.\n"
                                                       "Want to save permanently ?"),
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                dialog = DialogRec()
                dialog.setModal(True)
                dialog.show()

                dialog.textProgress.setText(self.tr("Processing..."))

                for copy in self.manage.recover_tempfile():
                    if copy.inProgress and not copy.sucess:
                        dialog.textProgress.setText("Processing %.2f%%" % copy.progress)
                        dialog.progressBar.setValue(copy.progress)
                    elif copy.sucess:
                        dialog.textProgress.setText(
                            self.tr("The video file was successfully recovered!"))
                        dialog.progressBar.setValue(100.0)
                        break
                    elif copy.error:
                        dialog.textProgress.setText(copy.get_info())
                        dialog.progressBar.setValue(0.0)
                        break

                dialog.btnOK.setEnabled(True)
                dialog.btnCancel.setEnabled(False)
                dialog.exec_()

    def startup_connection_handle(self, value=None, default=False):
        """ controla o fluxo de criação e remoção de conexões """
        if self.is_loading and not self.manage.is_complete():
            connection = self.manage.ctrConnection
            active_conn = connection.countActive()

            max_conn = self.uiMainWindow.connectionActive.value()
            proxy_disable = self.uiMainWindow.proxyDisable.isChecked()
            num_of_conn = max_conn - active_conn

            params = {
                "ratelimit": self.uiMainWindow.connectionSpeed.value(),
                "timeout": self.uiMainWindow.connectionTimeout.value(),
                "typechange": self.uiMainWindow.connectionType.isChecked(),
                "waittime": self.uiMainWindow.connectionSleep.value(),
                "reconexao": self.uiMainWindow.connectionAttempts.value()
            }
            if num_of_conn > 0:  # adiciona novas conexões.
                if proxy_disable:
                    sm_id_list = connection.startWithoutProxy(num_of_conn, **params)
                else:
                    if default:
                        sm_id_list = connection.startWithoutProxy(1, **params)
                        sm_id_list += connection.startWithProxy(num_of_conn - 1, **params)
                    else:
                        sm_id_list = connection.startWithProxy(num_of_conn, **params)

                for sm_id in sm_id_list:
                    self.add_table_row(sm_id)

            elif num_of_conn < 0:  # remove conexões existentes.
                for sm_id in connection.stop(num_of_conn):
                    self.remove_table_row(sm_id)
            else:  # mudança dinânica dos parametros das conexões.
                connection.update(**params)

    @staticmethod
    def set_default_config(conf):
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
        conf["Window"].setdefault("donationBoxIsOn", True)
        conf["Window"].setdefault("booted", False)

        conf["Path"].setdefault("videoDir", settings.DEFAULT_VIDEOS_DIR)
        conf["Lang"].setdefault("code", "en")

        conf["Prog"].setdefault("packetVersion", "1.6.9")

    def configUI(self):
        conf = self.config
        self.set_default_config(conf)

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

        if not self.confWindow.as_bool("booted"):
            self.resize(800, 600)

            # centralizando a janela no desktop
            qr = self.frameGeometry()
            cp = QtGui.QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())
        else:
            self.move(*list(map(int, self.confWindow.as_list("position"))))
            self.resize(*list(map(int, self.confWindow.as_list("size"))))

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
        self.confWidgetUi["tempFiles"] = self.uiMainWindow.tempFiles.isChecked()
        self.confWidgetUi["tempFileAction"] = self.uiMainWindow.tempFileAction.currentIndex()
        self.confWidgetUi["videoSplitSize"] = self.uiMainWindow.videoSplitSize.value()

        if not self.isMaximized():
            self.confWindow["position"] = self.pos().toTuple()
            self.confWindow["size"] = self.size().toTuple()

        self.confPath["videoDir"] = self.uiMainWindow.videoDir.text()

        # traduzindo a 'action' da ui em um código de linguagem.
        self.confLang["code"] = self.codeLang[self.langActionGroup.checkedAction()]
        self.confWindow["booted"] = True

        # salvando as configurações no arquivo
        if not base.security_save((path or self.configPath), _configobj=self.config):
            print("*** Warnnig: config save error!")

    def onShowResultInfo(self, title, text):
        QtGui.QMessageBox.information(self, title, text)

    def onReleasedFound(self, response):
        response += _("\nPressione OK para ir a página de download.")
        reply = QtGui.QMessageBox.information(self, _("Novidade!"),
                                              response, buttons=QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel
        )
        if reply == QtGui.QMessageBox.Ok:
            webbrowser.open_new_tab(self.releaseSource)

    def showDialogUpdate(self, response, changes, version):
        automatic = self.uiMainWindow.actionAutomaticSearch.isChecked()
        self.confProg["packetVersion"] = version

        title = _("Ativada)") if automatic else _("Desativada)")
        title = _("Novas atualizações recebidas! (Atualização automática - ") + title

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
    resultInfo = QtCore.Signal(str, str)
    releaseFound = QtCore.Signal(str)
    updateFound = QtCore.Signal(str, str, str)

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

        if result:
            self.releaseFound.emit(response)
        elif result is False and self.showWin:
            self.resultInfo.emit(_("Ainda em desenvolvimento..."), response)
        elif result is None and self.showWin:
            self.resultInfo.emit(_("Error"), response)

    def run(self):
        self.check_release()
        upd = updater.Updater(packetVersion=self.version)
        if upd.search():
            # começa o download da atualização
            result, response = upd.download()

            if result:
                # texto informando as mudanças que a nova atualização fez.
                changes = upd.getLastChanges(self.code)

                # aplica a atualização
                result, response = upd.update()

                # remove todos os arquivos
                upd.cleanUpdateDir()

                if result:
                    self.updateFound.emit(response, "\n\n".join(changes), upd.getNewVersion())

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
    print(("TL: ", translator.load(filepath)))
    app.installTranslator(translator)

    mw = Loader()
    mw.show()

    sys.exit(app.exec_())
    
    