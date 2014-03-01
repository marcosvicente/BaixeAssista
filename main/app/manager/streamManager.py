# coding: utf-8
import threading
import logging
import math
import time

from main.app.util import base, sites
from .info import Info


class StreamManager(threading.Thread):
    logger = logging.getLogger("main.app.manager")

    lock_block_config = threading.Lock()
    lock_block_fail = threading.Lock()

    # lockInicialize: impede que todas as conexões iniciem ao mesmo tempo.
    lock_initialize = threading.Lock()
    errors = ["onCuePoint"]

    list_info = ["http", "try", "state", "index", "downloaded",
                 "total", "remainder", "percent", "speed"]

    # cache de bytes para extração do 'header' do vídeo.
    cache_start_size = 2048

    class Synchronize(object):
        """ sicroniza as alterações sobre 'info' nas diferentes threads """
        lock = threading.RLock()

        def __init__(self, method):
            self.method = method

        def __get__(self, inst, cls):
            def wrapper(*args, **kwargs):
                with self.__class__.lock:
                    return self.method(inst, *args, **kwargs)
            return wrapper

    def __init__(self, manage, noProxy=False, **params):
        """ params: {}
        ratelimit: limita a velocidade de sub-conexões (limite em bytes)
        timeout: tempo de espera para se estabeler a conexão (tempo em segundos)
        reconexao: número de vezes que conexão com o servidor, tentará ser estabelecida.
        waittime: intervalo de tempo aguardado, quando houver falha na tentativa de conexão.
        typechange: muda o tipo de conexão(True ou False)
        """
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.params = params
        self.manage = manage

        self.set_default_params()

        # conexão com ou sem um servidor
        self.using_proxy = not noProxy
        self.proxies = {}

        self.video_manager = manage.create_video_manager()
        self.link = ''

        self.lock_wait = threading.Event()
        self.is_waiting = False
        self.lock_wait.set()

        self.bytes_num = 0
        self.is_running = True
        self._stream = None

    def set_default_params(self):
        self.params.setdefault("typechange", False)
        self.params.setdefault("ratelimit", 35840)
        self.params.setdefault("reconexao", 2)
        self.params.setdefault("waittime", 2)
        self.params.setdefault("timeout", 30)

    def __setitem__(self, key, value):
        assert key in self.params, "invalid option name: '%s'" % key
        self.params[key] = value

    def __del__(self):
        Info.delete(self.ident)
        del self.manage
        del self.params

    @staticmethod
    def calc_eta(start, now, total, current):
        if total is None: return '--:--'
        dif = now - start
        if current == 0 or dif < 0.001:  # One millisecond
            return '--:--'
        rate = float(current) / dif
        eta = int((float(total) - float(current)) / rate)
        (eta_mins, eta_secs) = divmod(eta, 60)
        (eta_hours, eta_mins) = divmod(eta_mins, 60)
        return '%02d:%02d:%02d' % (eta_hours, eta_mins, eta_secs)

    @staticmethod
    def best_block_size(elapsed_time, bytes):
        new_min = max(bytes / 2.0, 1.0)
        new_max = min(max(bytes * 2.0, 1.0), 4194304)  # Do not surpass 4 MB
        if elapsed_time < 0.001:
            return int(new_max)
        rate = bytes / elapsed_time
        if rate > new_max:
            return int(new_max)
        if rate < new_min:
            return int(new_min)
        return int(rate)

    @staticmethod
    def format_bytes(bytes):
        if bytes is None:
            return 'N/A'
        if type(bytes) is str:
            bytes = float(bytes)
        if bytes == 0.0:
            exponent = 0
        else:
            exponent = int(math.log(float(bytes), 1024.0))
        suffix = 'bkMGTPEZY'[exponent]
        converted = float(bytes) / float(1024 ** exponent)
        return '%.2f%s' % (converted, suffix)

    @staticmethod
    def calc_speed(start, now, bytes):
        dif = now - start
        if bytes == 0 or dif < 0.001:
            result = "---b/s"  # One millisecond
        else:
            result = "%s/s" % StreamManager.format_bytes(float(bytes) / dif)
        return result

    @staticmethod
    def calc_percent(byte_counter, data_len):
        if data_len is None:
            return '---.-%'
        return '%6s' % ('%3.1f%%' % (float(byte_counter) / float(data_len) * 100.0))

    def slow_down(self, start_time, byte_counter):
        """Sleep if the download speed is over the rate limit."""
        rate_limit = self.params["ratelimit"]
        if rate_limit is None or rate_limit == 0 or byte_counter == 0:
            return
        now = time.time()
        elapsed = now - start_time
        if elapsed <= 0.0:
            return
        speed = float(byte_counter) / elapsed
        if speed > rate_limit:
            time.sleep((byte_counter - rate_limit * (now - start_time)) / rate_limit)

    def _init(self):
        """ iniciado com thread. Evita travar no init """
        Info.add(self.ident)
        Info.set(self.ident, "state", _("Iniciando"))

        if self.using_proxy:
            self.proxies = self.manage.proxy_manager.get_formated()

        if self.video_manager.get_video_info(proxies=self.proxies,
                                             timeout=self.params["timeout"]):
            self.link = self.video_manager.get_link()

        Info.set(self.ident, "http", self.proxies.get("http", _("Conexão Padrão")))

    def stop(self):
        """ pára toda a atividade da conexão """
        self.unconfig(_("Parado pelo usuário"), 3)
        self.is_running = False

    @property
    def was_stopped(self):
        return not self.is_running

    def check_stream_errors(self, stream):
        """ Verifica se os dados da stream estao corretos """
        for err in self.errors:
            index = str(stream).find(err)
            if index >= 0:
                return index
        return -1

    def wait(self):
        """ aguarda o processo de configuração terminar """
        self.is_waiting = True
        self.lock_wait.wait()
        self.is_waiting = False

    @property
    def is_waiting(self):
        return self.lock_wait.is_waiting

    @is_waiting.setter
    def is_waiting(self, flag):
        self.lock_wait.is_waiting = flag

    def set_wait(self):
        self.lock_wait.clear()

    def stop_wait(self):
        self.lock_wait.set()

    @Synchronize
    def write(self, stream, bytes_num):
        """ Escreve a stream de bytes dados de forma controlada """
        if not self.manage.interval.has(self.ident):
            return
        if self.is_running and self.lock_wait.is_set():
            start = self.manage.interval.get_start(self.ident)
            offset = self.manage.interval.get_offset()

            # Escreve os dados na posição resultante
            pos = start - offset + self.bytes_num
            self.manage.file_manager.write(pos, stream)

            # quanto ja foi baixado da stream
            self.manage.cache_bytes_total += bytes_num
            self.manage.interval.nbytes[start] += bytes_num

            # bytes lidos da conexão.
            self.bytes_num += bytes_num

    def read(self):
        local_time = time.time()
        block_read = 1024

        while self.is_running:
            # bloqueia alterações sobre os dados do intervalo da conexão
            with self.manage.interval.get_lock(self.ident):
                try:
                    # o intervalo da conexão pode sofrer alteração.
                    seekpos = self.manage.interval.get_start(self.ident)
                    block_size = self.manage.interval.get_block_size(self.ident)
                    block_index = self.manage.interval.get_index(self.ident)

                    # condição atual da conexão: Baixando
                    Info.set(self.ident, "state", _("Baixando"))
                    Info.set(self.ident, "index", block_index)

                    # limita a leitura ao bloco de dados
                    if (self.bytes_num + block_read) > block_size:
                        block_read = block_size - self.bytes_num

                    # inicia a leitura da stream
                    before = time.time()
                    stream = self._stream.read(block_read)
                    after = time.time()

                    stream_len = len(stream)  # número de bytes baixados

                    if not self.lock_wait.is_set():  # caso onde a seekbar é usada
                        self.wait()
                        break

                    # o servidor fechou a conexão
                    if block_read > 0 and stream_len == 0:
                        self.failure(_("Parado pelo servidor"), 2)
                        break

                    # ajusta a quantidade de bytes baixados a capacidade atual da rede, ou ate seu limite
                    block_read = self.best_block_size((after - before), stream_len)

                    # começa a escrita da stream de video no arquivo local.
                    self.write(stream, stream_len)

                    start = self.manage.get_global_start_time()
                    current = self.manage.get_cache_bytes_total() - self.manage.get_cache_start_size()
                    total = self.manage.get_video_size() - self.manage.get_cache_start_size()

                    Info.set(self.ident, "downloaded", self.format_bytes(self.bytes_num))
                    Info.set(self.ident, "total", self.format_bytes(block_size))
                    Info.set(self.ident, "remainder", self.format_bytes(block_size - self.bytes_num))
                    Info.set(self.ident, "percent", base.calc_percent(self.bytes_num, block_size))
                    # calcula a velocidade de transferência da conexão
                    Info.set(self.ident, "speed", self.calc_speed(local_time, time.time(),
                                                                  self.bytes_num))
                    # tempo total do download do arquivo
                    self.manage.set_global_eta(self.calc_eta(start, time.time(), total, current))

                    # calcula a velocidade global
                    self.manage.set_global_speed(self.calc_speed(start, time.time(), current))

                    if self.bytes_num >= block_size:
                        if not self.manage.is_complete() and self.manage.interval.can_continue(self.ident):
                            self.manage.interval.remove(self.ident)
                            # associando aconexão a um novo bloco de bytes
                            if not self.configure():
                                break
                            local_time = time.time()
                        else:
                            break
                    elif self.manage.position_sent() != seekpos:
                        self.slow_down(local_time, self.bytes_num)
                except:
                    self.failure(_("Erro de leitura"), 2)
                    break
        self._finally()

    def _finally(self):
        Info.clear(self.ident, *self.list_info, exclude=("http",))

        if self.manage.interval.has(self.ident):
            self.manage.interval.remove(self.ident)

        if hasattr(self._stream, "close"):
            self._stream.close()

    @Synchronize
    def unconfig(self, error_string, number_error):
        """ remove todas as configurações, importantes, dadas a conexão """
        if self.manage.interval.has(self.ident):
            self.manage.interval.set_pending(
                self.manage.interval.get_index(self.ident),
                self.bytes_num,
                self.manage.interval.get_start(self.ident),
                self.manage.interval.get_end(self.ident),
                self.manage.interval.get_block_size(self.ident))

            self.manage.interval.remove(self.ident)

        ip = self.proxies.get("http", "default")
        bad_read = (number_error != 3 and self.bytes_num < self.manage.interval.get_min_block())

        if ip != "default" and (number_error == 1 or bad_read):
            self.manage.proxy_manager.set_bad(ip)

        # desassociando o ip dos dados do vídeo.
        del self.video_manager[ip]

    @base.LogOnError
    def failure(self, error_string, error_number):
        # removendo configurações
        self.unconfig(error_string, error_number)

        # retorna porque a conexao foi encerrada
        if not self.is_running or error_number == 3:
            return
        Info.clear(self.ident)

        Info.set(self.ident, "state", error_string)
        Info.set(self.ident, "state", _("Reconfigurando"))

        if not self.using_proxy:
            if self.params["typechange"]:
                self.proxies = self.manage.proxy_manager.get_formated()

        elif error_number == 1 or self.bytes_num < self.manage.interval.get_min_block():
            if not self.params["typechange"]:
                self.proxies = self.manage.proxy_manager.get_formated()
            else:
                self.proxies = {}

        self.using_proxy = bool(self.proxies)
        Info.set(self.ident, "http", self.proxies.get("http", _("Conexão Padrão")))

        if self.video_manager.get_video_info(proxies=self.proxies, timeout=self.params["timeout"]):
            self.link = self.video_manager.get_link()

    def connect(self):
        seek_pos = self.manage.interval.get_start(self.ident)
        start = self.video_manager.get_relative(seek_pos)
        link = sites.get_with_seek(self.link, start)
        video_size = self.manage.get_video_size()
        try_num = 0
        while self.is_running and try_num < self.params["reconexao"]:
            try:
                Info.set(self.ident, "state", _("Conectando"))
                Info.set(self.ident, "try", str(try_num + 1))
                self._stream = self.video_manager.connect(link,
                                    proxies=self.proxies,
                                    timeout=self.params["timeout"],
                                    login=False)
                stream = self._stream.read(self.cache_start_size)
                if self.check_stream_errors(stream) != -1:
                    raise RuntimeError('Corrupt stream!')
                stream, header = self.video_manager.get_stream_header(stream, seek_pos)

                # verifica a validade a resposta
                is_valid = self.video_manager.check_response(len(header),
                                     seek_pos, video_size,
                                     self._stream.headers)
                if is_valid and (self._stream.code == 200 or self._stream.code == 206):
                    if stream:
                        self.write(stream, len(stream))
                    if self.using_proxy:
                        self.manage.proxy_manager.set_good(self.proxies["http"])
                    Info.set(self.ident, "try", "Ok")
                    return True
                else:
                    Info.set(self.ident, "state", _("Resposta inválida"))
                    self._stream.close()
                    time.sleep(self.params["waittime"])
            except Exception as err:
                Info.set(self.ident, "state", _("Falha na conexão"))
                self.logger.error("%s Connecting: %s" % (self.__class__.__name__, err))
                time.sleep(self.params["waittime"])
            try_num += 1
        return False  # nao foi possível conectar

    def configure(self):
        """ associa a conexão a uma parte da stream """
        if self.lock_wait.is_set():
            with self.lock_block_config:
                if self.manage.interval.size_pending() > 0:
                    # associa um intervalo pendente(intervalos pendentes, são gerados em falhas de conexão)
                    self.manage.interval.config_pending(self.ident)
                else:
                    # cria um novo intervalo e associa a conexão.
                    self.manage.interval.create_new(self.ident)

                    # como novos intervalos não são infinitos, atribui um novo, apartir de um já existente.
                    if not self.manage.interval.has(self.ident):
                        self.manage.interval.config_derivative(self.ident)

                # contador de bytes do intervalod de bytes atual
                self.bytes_num = 0
        else:
            # aguarda a configuração do 'manage' terminar
            self.wait()
        return self.manage.interval.has(self.ident)

    def run(self):
        # configura um link inicial
        self._init()

        while self.is_running and not self.manage.is_complete():
            try:
                if self.configure():
                    # iniciando a conexão com o servidor de vídeo.
                    assert self.connect(), "connect error"
                    # inicia a transferencia de dados.
                    self.read()
                else:
                    Info.set(self.ident, "state", _("Ocioso"))
                    time.sleep(1.0)
            except Exception as err:
                self.failure(_("Incapaz de conectar"), 1)
                self.logger.error("%s Mainloop: %s" % (self.__class__.__name__, err))

        Info.set(self.ident, "state", _("Conexão parada"))


class StreamManager_(StreamManager):
    def __init__(self, manage, noProxy=False, **params):
        StreamManager.__init__(self, manage, noProxy, **params)

    def _init(self):
        """ iniciado com thread. Evita travar no init """
        Info.add(self.ident)
        Info.set(self.ident, "state", _("Iniciando"))

        if self.using_proxy: self.proxies = self.manage.proxy_manager.get_formated()

        Info.set(self.ident, "http", self.proxies.get("http", _("Conexão Padrão")))
        self.link = self.getVideoLink()

    @base.LogOnError
    def failure(self, error_string, error_number):
        Info.clear(self.ident)
        Info.set(self.ident, 'state', error_string)

        self.unconfig(error_string, error_number)  # removendo configurações

        if not self.is_running or error_number == 3: return  # retorna porque a conexao foi encerrada
        Info.set(self.ident, "state", _("Reconfigurando"))

        if not self.using_proxy:
            if self.params["typechange"]:
                self.proxies = self.manage.proxy_manager.get_formated()

        elif error_number == 1 or self.bytes_num < self.manage.interval.get_min_block():
            if not self.params["typechange"]:
                self.proxies = self.manage.proxy_manager.get_formated()
            else:
                self.proxies = {}

        self.using_proxy = bool(self.proxies)
        Info.set(self.ident, "http", self.proxies.get("http", _("Conexão Padrão")))
        self.link = self.getVideoLink()

    @base.LogOnError
    def getVideoLink(self):
        data = self.video_manager.get_init_page(self.proxies)  # pagina incial
        link = self.video_manager.get_file_link(data)  # link de download
        for second in range(self.video_manager.get_count(data), 0, -1):
            Info.set(self.ident, "state", _("Aguarde %02ds") % second)
            time.sleep(1)
        return link

    def connect(self):
        seek_pos = self.manage.interval.get_start(self.ident)
        start = self.video_manager.get_relative(seek_pos)
        link = sites.get_with_seek(self.link, start)
        video_size = self.manage.get_video_size()
        try_num = 0
        while self.is_running and try_num < self.params["reconexao"]:
            try:
                Info.set(self.ident, "state", _("Conectando"))
                Info.set(self.ident, "try", str(try_num + 1))

                self._stream = self.video_manager.connect(link,
                                headers={"Range": "bytes=%s-%s" % (seek_pos, video_size)},
                                proxies=self.proxies, timeout=self.params["timeout"])

                stream = self._stream.read(self.cache_start_size)
                if self.check_stream_errors(stream) != -1:
                    raise RuntimeError('Corrupt stream!')
                stream, header = self.video_manager.get_stream_header(stream, seek_pos)

                is_valid = self.video_manager.check_response(len(header),
                                         seek_pos, video_size,
                                         self._stream.headers)
                if is_valid and (self._stream.code == 200 or self._stream.code == 206):
                    if stream:
                        self.write(stream, len(stream))
                    if self.using_proxy:
                        self.manage.proxy_manager.set_good(self.proxies["http"])
                    Info.set(self.ident, "try", "Ok")
                    return True
                else:
                    Info.set(self.ident, "state", _("Resposta inválida"))
                    self._stream.close()
                    time.sleep(self.params["waittime"])
            except Exception as err:
                Info.set(self.ident, "state", _("Falha na conexão"))
                self.logger.error("%s Connecting: %s" % (self.__class__.__name__, err))
                time.sleep(self.params["waittime"])
            try_num += 1
        return False

    def run(self):
        # configura um link inicial
        self._init()

        while self.is_running and not self.manage.is_complete():
            try:
                if self.configure():
                    # inciando a conexão com o servidor de vídeo.
                    assert self.connect(), "conect error"
                    # inicia a transferência de dados.
                    self.read()
                else:
                    Info.set(self.ident, "state", _("Ocioso"))
                    time.sleep(1.0)
            except Exception as err:
                self.failure(_("Incapaz de conectar"), 1)
                self.logger.error("%s Mainloop: %s" % (self.__class__.__name__, err))

        Info.set(self.ident, "state", _("Conexão parada"))