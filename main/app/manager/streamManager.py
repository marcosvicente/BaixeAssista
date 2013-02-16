# coding: utf-8
from main.app.util import base, sites
from info import Info
import threading
import logging
import math
import time

class StreamManager(threading.Thread):
    logger = logging.getLogger("main.app.manager")
    
    lockBlocoConfig = threading.Lock()
    lockBlocoFalha = threading.Lock()
    
    # lockInicialize: impede que todas as conexões iniciem ao mesmo tempo.
    lockInicialize = threading.Lock()
    listStrErro = ["onCuePoint"]
    
    # ordem correta das infos
    listInfo = ["http", "try", "state", "index", "downloaded", 
                "total", "remainder", "percent", "speed"]
                
    # cache de bytes para extração do 'header' do vídeo.
    cacheStartSize = 256
    
    class sincronize(object):
        """ sicroniza as alterações sobre 'info' nas diferentes threads """
        _lock = threading.RLock()
        def __init__(self, func): self.func = func
        def __get__(self, inst, cls):
            def wrap(*args, **kwargs):
                with self._lock: 
                    return self.func(inst,*args,**kwargs)
            return wrap
            
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
        
        self.setDefaultParams()
        
        # conexão com ou sem um servidor
        self.usingProxy = not noProxy
        self.proxies = {}
        
        self.videoManager = manage.createVideoManager()
        self.link = ""
        
        self.lockWait = threading.Event()
        self.isWaiting = False
        self.lockWait.set()
        
        self.numBytesLidos = 0
        self.isRunning = True
        
    def setDefaultParams(self):
        self.params.setdefault("typechange", False)
        self.params.setdefault("ratelimit", 35840)
        self.params.setdefault("reconexao", 2)
        self.params.setdefault("waittime", 2)
        self.params.setdefault("timeout", 30)
        
    def __setitem__(self, key, value):
        assert self.params.has_key( key ), "invalid option name: '%s'"%key
        self.params[ key ] = value
        
    def __del__(self):
        Info.delete(self.ident)
        del self.manage
        del self.params
        
    @staticmethod
    def calc_eta(start, now, total, current):
        if total is None: return '--:--'
        dif = now - start
        if current == 0 or dif < 0.001: # One millisecond
            return '--:--'
        rate = float(current) / dif
        eta = long((float(total) - float(current)) / rate)
        (eta_mins, eta_secs) = divmod(eta, 60)
        (eta_hours, eta_mins)=  divmod(eta_mins, 60)
        return '%02d:%02d:%02d' % (eta_hours, eta_mins, eta_secs)

    @staticmethod
    def best_block_size(elapsed_time, bytes):
        new_min = max(bytes / 2.0, 1.0)
        new_max = min(max(bytes * 2.0, 1.0), 4194304) # Do not surpass 4 MB
        if elapsed_time < 0.001:
            return long(new_max)
        rate = bytes / elapsed_time
        if rate > new_max:
            return long(new_max)
        if rate < new_min:
            return long(new_min)
        return long(rate)

    @staticmethod
    def format_bytes(bytes):
        if bytes is None:
            return 'N/A'
        if type(bytes) is str:
            bytes = float(bytes)
        if bytes == 0.0:
            exponent = 0
        else:
            exponent = long(math.log(float(bytes), 1024.0))
        suffix = 'bkMGTPEZY'[exponent]
        converted = float(bytes) / float(1024**exponent)
        return '%.2f%s' % (converted, suffix)
    
    @staticmethod
    def calc_speed(start, now, bytes):
        dif = now - start
        if bytes == 0 or dif < 0.001:
            result = "---b/s" # One millisecond
        else:
            result = "%s/s"% StreamManager.format_bytes(float(bytes) / dif)
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
        
        if self.usingProxy:
            self.proxies = self.manage.proxyManager.get_formated()
        
        if self.videoManager.getVideoInfo(proxies = self.proxies, 
                                          timeout = self.params["timeout"]):
            self.link = self.videoManager.getLink()
            
        Info.set(self.ident, "http", self.proxies.get("http", _(u"Conexão Padrão")))
        
    def stop(self):
        """ pára toda a atividade da conexão """
        self.unconfig(_(u"Parado pelo usuário"), 3)
        self.isRunning = False
        
    def wasStopped(self):
        return (not self.isRunning)

    def checkStreamError(self, stream):
        """Verifica se os dados da stream estao corretos"""
        for err in self.listStrErro:
            index = stream.find( err )
            if index >= 0: return index
        return -1

    def wait(self):
        """ aguarda o processo de configuração terminar """
        self.isWaiting = True; self.lockWait.wait()
        self.isWaiting = False
        
    @property
    def isWaiting(self):
        return self.lockWait.isWaiting
    
    @isWaiting.setter
    def isWaiting(self, flag):
        self.lockWait.isWaiting = flag
    
    def setWait(self): self.lockWait.clear()
    def stopWait(self): self.lockWait.set()
    
    @sincronize
    def write(self, stream, nbytes):
        """ Escreve a stream de bytes dados de forma controlada """
        if not self.manage.interval.has(self.ident): return
        if self.isRunning and self.lockWait.is_set():
            start = self.manage.interval.getStart( self.ident )
            offset = self.manage.interval.getOffset()
            
            # Escreve os dados na posição resultante
            pos = start - offset + self.numBytesLidos
            self.manage.fileManager.write(pos, stream)
            
            # quanto ja foi baixado da stream
            self.manage.cacheBytesTotal += nbytes
            self.manage.interval.send_info["nbytes"][start] += nbytes
            
            # bytes lidos da conexão.
            self.numBytesLidos += nbytes

    def read(self ):
        local_time = time.time()
        block_read = 1024
        
        while self.isRunning:
            # bloqueia alterações sobre os dados do intervalo da conexão
            with self.manage.interval.getLock( self.ident ):
                try:
                    # o intervalo da conexão pode sofrer alteração.
                    seekpos = self.manage.interval.getStart(self.ident)
                    block_size = self.manage.interval.getBlockSize(self.ident)
                    block_index = self.manage.interval.getIndex(self.ident)
                    
                    # condição atual da conexão: Baixando
                    Info.set(self.ident, "state", _("Baixando") )
                    Info.set(self.ident, "index", block_index)
                    
                    # limita a leitura ao bloco de dados
                    if (self.numBytesLidos + block_read) > block_size:
                        block_read = block_size - self.numBytesLidos
                        
                    # inicia a leitura da stream
                    before = time.time()
                    stream = self.streamSocket.read( block_read )
                    after = time.time()
                    
                    streamLen = len(stream) # número de bytes baixados
                    
                    if not self.lockWait.is_set(): # caso onde a seekbar é usada
                        self.wait(); break
                        
                    # o servidor fechou a conexão
                    if block_read > 0 and streamLen == 0 or self.checkStreamError(stream) != -1:
                        self.failure(_("Parado pelo servidor"), 2); break
                        
                    # ajusta a quantidade de bytes baixados a capacidade atual da rede, ou ate seu limite
                    block_read = self.best_block_size((after - before), streamLen)
                    
                    # começa a escrita da stream de video no arquivo local.
                    self.write(stream, streamLen)
                    
                    start = self.manage.getGlobalStartTime()
                    current = self.manage.getCacheBytesTotal() - self.manage.getStartCacheSize()
                    total = self.manage.getVideoSize() - self.manage.getStartCacheSize()
                    
                    Info.set(self.ident, "downloaded", self.format_bytes(self.numBytesLidos))
                    Info.set(self.ident, "total", self.format_bytes(block_size))
                    Info.set(self.ident, "remainder", self.format_bytes(block_size - self.numBytesLidos))
                    Info.set(self.ident, "percent", base.calc_percent(self.numBytesLidos, block_size))
                    # calcula a velocidade de transferência da conexão
                    Info.set(self.ident, "speed", self.calc_speed(local_time, time.time(), 
                                                                       self.numBytesLidos))
                    # tempo total do download do arquivo
                    self.manage.setGlobalEta(self.calc_eta(start, time.time(), total, current))
                    
                    # calcula a velocidade global
                    self.manage.setGlobalSpeed(self.calc_speed(start, time.time(), current))
                    
                    if self.numBytesLidos >= block_size:
                        self.manage.interval.remove(self.ident)
                        
                        if not self.manage.isComplete() and self.manage.interval.canContinue(self.ident):
                            # associando aconexão a um novo bloco de bytes
                            if not self.configure(): break
                            local_time = time.time()
                        else:
                            break
                    elif self.manage.nowSending() != seekpos:
                        self.slow_down(local_time, self.numBytesLidos)
                except:
                    self.failure(_("Erro de leitura"), 2)
                    break
        self._finally()
        
        
    def _finally(self):
        Info.clear(self.ident, *self.listInfo, exclude=("http",))
        
        if self.manage.interval.has(self.ident):
            self.manage.interval.remove(self.ident)
            
        if hasattr(self.streamSocket,"close"):
            self.streamSocket.close()
    
    @sincronize
    def unconfig(self, errorstring, errornumber):
        """ remove todas as configurações, importantes, dadas a conexão """
        if self.manage.interval.has(self.ident):
            self.manage.interval.setPending(
                        self.manage.interval.getIndex(self.ident), 
                        self.numBytesLidos, 
                        self.manage.interval.getStart(self.ident),
                        self.manage.interval.getEnd(self.ident), 
                        self.manage.interval.getBlockSize(self.ident))
            
            self.manage.interval.remove(self.ident)
                
        ip = self.proxies.get("http","default")
        bad_read = (errornumber != 3 and self.numBytesLidos < self.manage.interval.getMinBlock())
        
        if ip != "default" and (errornumber == 1 or bad_read):
            self.manage.proxyManager.set_bad( ip )
            
        # desassociando o ip dos dados do vídeo.
        del self.videoManager[ ip ] 
        
    @base.LogOnError
    def failure(self, errorstring, errornumber):
        # removendo configurações
        self.unconfig(errorstring, errornumber)
        
        # retorna porque a conexao foi encerrada
        if not self.isRunning or errornumber == 3: return
        Info.clear(self.ident)
        
        Info.set(self.ident, "state", errorstring)
        Info.set(self.ident, "state", _("Reconfigurando"))
        
        if not self.usingProxy:
            if self.params["typechange"]:
                self.proxies = self.manage.proxyManager.get_formated()
                
        elif errornumber == 1 or self.numBytesLidos < self.manage.interval.getMinBlock():
            if not self.params["typechange"]:
                self.proxies = self.manage.proxyManager.get_formated()
            else:
                self.proxies = {}
                
        self.usingProxy = bool(self.proxies)
        Info.set(self.ident, "http", self.proxies.get("http", _(u"Conexão Padrão")))
        
        if self.videoManager.getVideoInfo(proxies=self.proxies, timeout=self.params["timeout"]):
            self.link = self.videoManager.getLink()
            
    def connect(self):
        seekpos = self.manage.interval.getStart(self.ident)
        start = self.videoManager.get_relative( seekpos )
        link = sites.get_with_seek(self.link, start)
        videoSize = self.manage.getVideoSize()
        ctry = 0
        while self.isRunning and ctry < self.params["reconexao"]:
            try:
                Info.set(self.ident, "state", _("Conectando"))
                Info.set(self.ident, "try", str(ctry+1))
                self.streamSocket = self.videoManager.connect(link, proxies = self.proxies, 
                                                              timeout = self.params["timeout"], 
                                                              login = False)
                stream = self.streamSocket.read( self.cacheStartSize )
                stream, header = self.videoManager.get_stream_header(stream, seekpos)
                
                # verifica a validade a resposta.
                isValid = self.videoManager.check_response(len(header), seekpos, videoSize, 
                                                           self.streamSocket.headers)
                
                if isValid and (self.streamSocket.code == 200 or self.streamSocket.code == 206):
                    if stream: self.write(stream, len(stream))
                    if self.usingProxy:
                        self.manage.proxyManager.set_good( self.proxies["http"] )
                    Info.set(self.ident, "try", "Ok")
                    return True
                else:
                    Info.set(self.ident, "state", _(u"Resposta inválida"))
                    self.streamSocket.close()
                    time.sleep( self.params["waittime"] )
            except Exception as err:
                Info.set(self.ident, "state", _(u"Falha na conexão"))
                self.logger.error("%s Connecting: %s" %(self.__class__.__name__, err))
                time.sleep( self.params["waittime"] )
            ctry += 1
        return False # nao foi possível conectar

    def configure(self):
        """ associa a conexão a uma parte da stream """
        if self.lockWait.is_set():
            with self.lockBlocoConfig:
                if self.manage.interval.countPending() > 0:
                    # associa um intervalo pendente(intervalos pendentes, são gerados em falhas de conexão)
                    self.manage.interval.configurePending( self.ident )
                else:
                    # cria um novo intervalo e associa a conexão.
                    self.manage.interval.createNew( self.ident )

                    # como novos intervalos não são infinitos, atribui um novo, apartir de um já existente.
                    if not self.manage.interval.has( self.ident ):
                        self.manage.interval.configureDerivate( self.ident )
                        
                # contador de bytes do intervalod de bytes atual
                self.numBytesLidos = 0
        else:
            # aguarda a configuração do 'manage' terminar
            self.wait()
        return self.manage.interval.has(self.ident)
        
    def run(self):
        # configura um link inicial
        self._init()
        
        while self.isRunning and not self.manage.isComplete():
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
                self.logger.error("%s Mainloop: %s" %(self.__class__.__name__, err))
                
        Info.set(self.ident, "state", _(u"Conexão parada"))
        
        
class StreamManager_( StreamManager ):
    def __init__(self, manage, noProxy= False, **params):
        StreamManager.__init__(self, manage, noProxy, **params)
    
    def _init(self):
        """ iniciado com thread. Evita travar no init """
        Info.add(self.ident)
        Info.set(self.ident, "state", _(u"Iniciando"))
        
        if self.usingProxy: self.proxies = self.manage.proxyManager.get_formated()
        
        Info.set(self.ident, "http", self.proxies.get("http",_(u"Conexão Padrão")))
        self.link = self.getVideoLink()
        
    @base.LogOnError
    def failure(self, errorstring, errornumber):
        Info.clear(self.ident)
        Info.set(self.ident, 'state', errorstring)
        
        self.unconfig(errorstring, errornumber) # removendo configurações
        
        if not self.isRunning or errornumber == 3: return # retorna porque a conexao foi encerrada
        Info.set(self.ident, "state", _("Reconfigurando"))
        
        if not self.usingProxy:
            if self.params["typechange"]:
                self.proxies = self.manage.proxyManager.get_formated()
            
        elif errornumber == 1 or self.numBytesLidos < self.manage.interval.getMinBlock():
            if not self.params["typechange"]:
                self.proxies = self.manage.proxyManager.get_formated()
            else:
                self.proxies = {}
                
        self.usingProxy = bool(self.proxies)
        Info.set(self.ident, "http", self.proxies.get("http", _(u"Conexão Padrão")))
        self.link = self.getVideoLink()
    
    @base.LogOnError
    def getVideoLink(self):
        data = self.videoManager.get_init_page(self.proxies) # pagina incial
        link = self.videoManager.get_file_link(data) # link de download
        for second in range(self.videoManager.get_count(data), 0, -1):
            Info.set(self.ident, "state", _(u"Aguarde %02ds")%second)
            time.sleep(1)
        return link
        
    def connect(self):
        seekpos = self.manage.interval.getStart(self.ident)
        start = self.videoManager.get_relative( seekpos )
        link = sites.get_with_seek(self.link, start)
        videoSize = self.manage.getVideoSize()
        ctry = 0
        while self.isRunning and ctry < self.params["reconexao"]:
            try:                
                Info.set(self.ident, "state", _("Conectando"))
                Info.set(self.ident, "try", str(ctry+1))
                
                self.streamSocket = self.videoManager.connect(link,
                                headers = {"Range": "bytes=%s-%s" %(seekpos, videoSize)},
                                proxies = self.proxies, timeout = self.params["timeout"])
                
                stream = self.streamSocket.read( self.cacheStartSize )
                stream, header = self.videoManager.get_stream_header(stream, seekpos)
                
                isValid = self.videoManager.check_response(len(header), seekpos, videoSize, 
                                                           self.streamSocket.headers)
                
                if isValid and (self.streamSocket.code == 200 or self.streamSocket.code == 206):
                    if stream: self.write(stream, len(stream))
                    if self.usingProxy:
                        self.manage.proxyManager.set_good(self.proxies["http"])
                    Info.set(self.ident, "try", "Ok")
                    return True
                else:
                    Info.set(self.ident, "state", _(u"Resposta inválida"))
                    self.streamSocket.close()
                    time.sleep( self.params["waittime"] )
            except Exception as err:
                Info.set(self.ident, "state", _(u"Falha na conexão"))
                self.logger.error("%s Connecting: %s" %(self.__class__.__name__, err))
                time.sleep( self.params["waittime"] )
            ctry += 1
        return False

    def run(self):
        # configura um link inicial
        self._init()
        
        while self.isRunning and not self.manage.isComplete():
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
                self.logger.error("%s Mainloop: %s" %(self.__class__.__name__, err))
                
        Info.set(self.ident, "state", _(u"Conexão parada"))
        