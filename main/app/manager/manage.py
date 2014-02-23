# coding: utf-8
import time

from main import settings
from main.app.util import base
from main.app.generators import Universal
from .proxyManager import ProxyManager
from .fileManager import FileManager
from .resumeInfo import ResumeInfo
from .connection import Connection
from .interval import Interval
from .streamer import Streamer
from .urls import UrlManager
from .info import Info


class ManageMiddleware(object):
    """ insere o object manage em todas as conexões """

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.manage = settings.MANAGE_OBJECT


class Manage(object):
    def __init__(self, URL="", **params):
        """ params: {}
        - tempfile: define se o vídeo será gravado em um arquivo temporário
        - videoQuality: qualidade desejada para o vídeo(1 = baixa; 2 = média; 3 = alta).
        """
        assert URL, _("Entre com uma url primeiro!")
        self.params = params

        params.setdefault("tempfile", False)
        params.setdefault("videoPath", settings.DEFAULT_VIDEOS_DIR)
        params.setdefault("videoQuality", 2)
        params.setdefault("maxsplit", 2)

        self.streamUrl = URL  # guarda a url do video
        self.using_temp_file = params["tempfile"]
        self.start_cache_size = 0
        self.cache_bytes_total = 0
        self.streamerList = []

        # manage log
        Info.add("manage")
        settings.MANAGE_OBJECT = self

        # guarda no banco de dados as urls adicionadas
        self.urlManager = UrlManager()

        try:
            self.urlManager.analizeUrl(self.streamUrl)
        except:
            raise AttributeError(_("Sem suporte para a url fornecida."))

        # nome do video ligado a url
        self.video_title = self.urlManager.getUrlTitle(self.streamUrl)
        self.video_size = 0  # tamanho total do video
        self.video_ext = ""  # extensão do arquivo de vídeo

        # embora o método _init tenha outro propósito, ele também 
        # complementa a primeira inicialização do objeto Manage.
        self._init()

        # controla a obtenção de links, tamanho do arquivo, title, etc.
        self.video_manager = self.create_video_manager()

        # controle das conexões
        self.ctrConnection = Connection(self)

        # gerencia os endereços dos servidores proxies
        self.proxy_manager = ProxyManager()

    def _init(self, **params):
        """ método chamado para realizar a configuração de leitura aleatória da stream """
        self.params.update(params)

        # velocidade global do download atual
        self.global_speed = self.global_eta = ''
        self.cache_bytes_counter = 0

        self.resuming = False

        self.params.setdefault("tempfile", False)
        self.params.setdefault("seekpos", 0)

        self.resume_info = ResumeInfo(filename=self.video_title)

        if not self.params["tempfile"] and not self.resume_info.is_empty:
            self.file_manager = FileManager(
                filename=self.video_title,
                tempfile=self.resume_info.is_empty,
                filepath=self.resume_info["videoPath"],
                fileext=self.resume_info["videoExt"]
            )
            self.cache_bytes_counter = self.resume_info["cacheBytesCount"]
            self.cache_bytes_total = self.resume_info["cacheBytesTotal"]
            self.video_size = self.resume_info["videoSize"]

            seek_pos = self.resume_info["seekPos"]
            pending = self.resume_info["pending"]

            # Sem o parâmetro qualidade do resumo, o usuário poderia 
            # corromper o arquivo de video, dando uma qualidade diferente
            self.params["videoQuality"] = self.resume_info["videoQuality"]
            self.params["videoPath"] = self.resume_info["videoPath"]

            self.video_ext = self.resume_info["videoExt"]

            self.interval = Interval(maxsize=self.video_size,
                                     seekpos=seek_pos, offset=0, pending=pending,
                                     maxsplit=self.params["maxsplit"])

            self.start_cache_size = self.cache_bytes_total
            self.resuming = True

    def start(self, ctry=0, num_try=1, proxy={}, callback=None):
        """ Começa a coleta de informações. Depende da internet, por isso pode demorar para reponder. """
        if not self.video_size or not self.video_title:
            if not self.get_info(ctry, num_try, proxy, callback):
                return False

        if not self.is_tempfile_mode:
            # salvando o link e o título
            if not self.urlManager.exist(self.streamUrl):
                self.urlManager.add(self.streamUrl, self.video_title)

                # pega o título já com um índice
                title = self.urlManager.getUrlTitle(self.streamUrl)
                self.video_title = title or self.video_title

            # salvando referênica para o ultimo video viusalizado.
            self.urlManager.saveLast(self.streamUrl, self.video_title)

        elif not self.urlManager.exist(self.streamUrl):
            self.video_title = self.urlManager.setTitleIndex(self.video_title)

        if not self.resuming:
            self.file_manager = FileManager(
                filename=self.video_title,
                tempfile=self.params["tempfile"],
                filepath=self.params["videoPath"],
                fileext=self.video_ext
            )
            # blocks serão criados do ponto zero da stream
            self.interval = Interval(maxsize=self.video_size,
                                     seekpos=self.params["seekpos"],
                                     maxsplit=self.params["maxsplit"])

            # salvando dados de resumo inicial.
            if not self.is_tempfile_mode:
                self.save_resume()

        # abre o arquivo. seja criando um novo ou alterando um exitente
        self.file_manager.open()

        # tempo inicial da velocidade global
        self.globalStartTime = time.time()
        self.auto_save_time = time.time()
        # informa que a transferêcia pode começar
        return True

    def get_info(self, try_num, num_try, proxy, callback):
        message = "\n".join([
            _("Coletando informações necessárias"),
            "IP: %s" % proxy.get("http", _("Conexão padrão")),
            _("Tentativa %d/%d\n") % (try_num, num_try)
        ])

        callback(message, '')

        if self.video_manager.get_video_info(ntry=1, proxies=proxy):
            # tamanho do arquivo de vídeo
            self.video_size = self.video_manager.get_video_size()
            # título do arquivo de video
            self.video_title = self.video_manager.get_title()
            # extensão do arquivo de video
            self.video_ext = self.video_manager.get_video_ext()

        # função de atualização externa
        callback(message, self.video_manager.get_message())
        return self.video_size and self.video_title

    def create_video_manager(self):
        """ controla a obtenção de links, tamanho do arquivo, title, etc """
        return Universal.getVideoManager(self.streamUrl)(
            self.streamUrl, streamSize=self.video_size,
            quality=self.params["videoQuality"]
        )

    def get_streamer(self):
        """ streamer controla a leitura dos bytes enviados ao player """
        return Streamer(self)

    def add_streamer(self, streamer):
        if not streamer in self.streamerList:
            self.streamerList.append(streamer)

    def del_streamer(self, streamer):
        if streamer in self.streamerList:
            self.streamerList.remove(streamer)

    def stop(self):
        for streamer in self.streamerList:
            streamer.stop()

        if not self.is_tempfile_mode:
            self.save_resume()

        self.file_manager.close()
        self.clear()

    def clear(self):
        """ deleta todas as variáveis do objeto """
        Info.delete("manage")
        settings.MANAGE_OBJECT = None
        del self.streamerList
        del self.ctrConnection
        del self.video_manager
        del self.proxy_manager
        del self.urlManager
        del self.file_manager
        del self.interval
        del self.params

    @FileManager.sincronize
    def recover_tempfile(self):
        """ tenta fazer a recuperação de um arquivo temporário """
        # começa a recuperação do arquivo temporário.
        for copy in self.file_manager.recover(badfile=(not self.is_tempfile_mode or self.interval.getOffset() != 0)):
            if copy.inProgress and copy.progress == 100.0 and copy.sucess and not copy.error:
                # nunca se deve adcionar a mesma url.
                if not self.urlManager.exist(self.streamUrl):
                    self.urlManager.add(self.streamUrl, self.video_title)
                    self.urlManager.saveLast(self.streamUrl, self.video_title)
                # caso o download não esteja completo.
                self.save_resume()
            yield copy

    def is_complete(self):
        """ informa se o arquivo já foi completamente baixado """
        return self.cache_bytes_total >= (self.video_size - 25)

    @property
    def is_tempfile_mode(self):
        """ avalia se o arquivo de video está sendo salva em um arquivo temporário """
        return bool(self.using_temp_file or self.params["tempfile"])

    def get_global_start_time(self):
        return self.globalStartTime

    def get_cache_start_size(self):
        return self.start_cache_size

    def get_init_pos(self):
        return self.params.get("seekpos", 0)

    def is_resuming(self):
        return self.resuming

    def get_video_title(self):
        return self.video_title

    def get_video_url(self):
        return self.streamUrl

    def get_video_size(self):
        return self.video_size

    def get_video_ext(self):
        return self.video_ext

    def position_sent(self):
        return self.interval.send_info['sending']

    def get_cache_bytes_total(self):
        return self.cache_bytes_total

    def get_global_speed(self):
        return self.global_speed

    def set_global_speed(self, speed):
        self.global_speed = speed

    def get_global_eta(self):
        return self.global_eta

    def set_global_eta(self, eta):
        self.global_eta = eta

    @FileManager.sincronize
    def save_resume(self):
        """ salva todos os dados necessários para o resumo do arquivo atual """
        self.ctrConnection.removeStopped()
        pending = []  # coleta geral de informações.

        for stream_manager in self.ctrConnection.getConnList():
            identify = stream_manager.ident

            # a conexão deve estar ligada a um interv
            if self.interval.has(identify):
                pending.append((
                    self.interval.getIndex(identify),
                    stream_manager.bytes_num,
                    self.interval.getStart(identify),
                    self.interval.getEnd(identify),
                    self.interval.getBlockSize(identify)
                ))

        pending.extend(self.interval.getPending())
        pending.sort()

        self.resume_info.update(title=self.video_title,
                               videoQuality=self.params["videoQuality"],
                               cacheBytesTotal=self.cache_bytes_total,
                               cacheBytesCount=self.cache_bytes_counter,
                               videoPath=self.params["videoPath"],
                               seekPos=self.interval.seekpos,
                               videoSize=self.video_size,
                               videoExt=self.video_ext,
                               pending=pending)

    def set_random(self, seek_pos):
        """ Configura a leitura da stream para um ponto aleatório dela """
        self.notify_connections(True)

        if not self.is_tempfile_mode:
            self.save_resume()

        self.cache_bytes_total = self.start_cache_size = seek_pos
        del self.interval, self.file_manager

        self._init(tempfile=True, seekpos=seek_pos)
        self.params["seeking"] = True
        self.start()
        return True

    def reload_settings(self):
        if self.params.get("seeking", False):
            self.notify_connections(True)

            self.cache_bytes_total = self.start_cache_size = 0
            del self.interval, self.file_manager

            self._init(tempfile=self.using_temp_file, seekpos=0)
            self.params["seeking"] = False
            self.start()
        return True

    def notify_connections(self, condition):
        """ Informa as conexões que um novo ponto da stream está sendo lido """
        for conn in self.ctrConnection.getConnList():
            if condition:
                conn.set_wait()
            elif conn.is_waiting:
                conn.stop_wait()

    @base.protected()
    def update(self):
        """ atualiza dados de transferência do arquivo de vídeo atual """
        start = self.interval.getFirstStart()
        self.interval.send_info["sending"] = start
        bytes_num = self.interval.send_info["nbytes"].get(start, 0)

        if start >= 0:
            absolute_start = start - self.interval.getOffset()
            self.cache_bytes_counter = absolute_start + bytes_num

        elif self.is_complete():  # is_complete: tira a necessidade de uma igualdade absoluta
            self.cache_bytes_counter = self.get_video_size()

        if not self.is_tempfile_mode and (time.time() - self.auto_save_time) > 300:
            self.auto_save_time = time.time()
            self.save_resume()

        # reinicia a atividade das conexões
        self.notify_connections(False)