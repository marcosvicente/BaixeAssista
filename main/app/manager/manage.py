# coding: utf-8
from main import settings
from main.app.util import base
from main.app.generators import Universal
from proxyManager import ProxyManager
from fileManager import FileManager
from resumeInfo import ResumeInfo
from connection import Connection
from interval import Interval
from streamer import Streamer
from urls import UrlManager
from info import Info

import time

class ManageMiddleware(object):
    """ insere o object manage em todas as conexões """
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.manage = settings.MANAGE_OBJECT
        
# GRUPO GLOBAL DE VARIAVEIS COMPARTILHADAS
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
        
        self.streamUrl = URL # guarda a url do video
        self.usingTempfile = params["tempfile"]
        self.startCacheSize = 0
        self.cacheBytesTotal = 0
        self.streamerList = []
        
        # manage log
        Info.add("manage")
        # -----------------------------------------
        settings.MANAGE_OBJECT = self
        
        # guarda no banco de dados as urls adicionadas
        self.urlManager = UrlManager()

        try: self.urlManager.analizeUrl( self.streamUrl )
        except: raise AttributeError, _(u"Sem suporte para a url fornecida.")

        # nome do video ligado a url
        self.videoTitle = self.urlManager.getUrlTitle( self.streamUrl )
        self.videoSize = 0 # tamanho total do video
        self.videoExt = "" # extensão do arquivo de vídeo
        
        # embora o método _init tenha outro propósito, ele também 
        # complementa a primeira inicialização do objeto Manage.
        self._init()
        
        # controla a obtenção de links, tamanho do arquivo, title, etc.
        self.clsVideoManager = Universal.getVideoManager(self.streamUrl)
        self.videoManager = self.createVideoManager()
        
        # controle das conexões
        self.ctrConnection = Connection(self)
        
        # gerencia os endereços dos servidores proxies
        self.proxyManager = ProxyManager()
        
    def _init(self, **params):
        """ método chamado para realizar a configuração de leitura aleatória da stream """
        self.params.update( params )
        # velocidade global do download atual
        self.globalSpeed = self.globalEta = ""
        self.cacheBytesCount = 0
        self.resuming = False
        
        self.params.setdefault("tempfile", False)
        self.params.setdefault("seekpos", 0)
        
        self.resumeInfo = ResumeInfo(filename = self.videoTitle)
        
        if not self.params["tempfile"] and not self.resumeInfo.isEmpty:
            self.fileManager = FileManager(
                filename = self.videoTitle, 
                tempfile = self.resumeInfo.isEmpty, 
                filepath = self.resumeInfo["videoPath"],
                fileext  = self.resumeInfo["videoExt"]
            )
            self.cacheBytesCount = self.resumeInfo["cacheBytesCount"]
            self.cacheBytesTotal = self.resumeInfo["cacheBytesTotal"]
            self.videoSize = self.resumeInfo["videoSize"]
            
            seekpos = self.resumeInfo["seekPos"]
            intervs = self.resumeInfo["pending"]
            
            # Sem o parâmetro qualidade do resumo, o usuário poderia 
            # corromper o arquivo de video, dando uma qualidade diferente
            self.params["videoQuality"] = self.resumeInfo["videoQuality"]
            self.params["videoPath"] = self.resumeInfo["videoPath"]
            
            self.videoExt = self.resumeInfo["videoExt"]
            
            self.interval = Interval(maxsize = self.videoSize,
                 seekpos = seekpos, offset = 0,  pending = intervs, 
                 maxsplit = self.params["maxsplit"])
            
            self.startCacheSize = self.cacheBytesTotal
            self.resuming = True
    
    def start(self, ctry=0, ntry=1, proxy={}, callback=None):
        """ Começa a coleta de informações. Depende da internet, por isso pode demorar para reponder. """
        if not self.videoSize or not self.videoTitle:
            if not self.getInfo(ctry, ntry, proxy, callback):
                return False
            
        if not self.isTempFileMode:
            # salvando o link e o título
            if not self.urlManager.exist(self.streamUrl):
                self.urlManager.add(self.streamUrl, self.videoTitle)
                
                # pega o título já com um índice
                title = self.urlManager.getUrlTitle(self.streamUrl)
                self.videoTitle = title or self.videoTitle
                
            # salvando referênica para o ultimo video viusalizado.
            self.urlManager.saveLast(self.streamUrl, self.videoTitle)
            
        elif not self.urlManager.exist(self.streamUrl):
            self.videoTitle = self.urlManager.setTitleIndex(self.videoTitle)
        
        if not self.resuming:
            self.fileManager = FileManager(
                filename = self.videoTitle, 
                tempfile = self.params["tempfile"], 
                filepath = self.params["videoPath"],
                fileext  = self.videoExt
            )
            # blocks serão criados do ponto zero da stream
            self.interval = Interval(maxsize = self.videoSize, 
                                     seekpos = self.params["seekpos"],
                                     maxsplit = self.params["maxsplit"])
            
            # salvando dados de resumo inicial.
            if not self.isTempFileMode: self.salveInfoResumo()
            
        # abre o arquivo. seja criando um novo ou alterando um exitente
        self.fileManager.open()
        
        # tempo inicial da velocidade global
        self.globalStartTime = time.time()
        self.autoSaveTime = time.time()
        # informa que a transferêcia pode começar
        return True

    def getInfo(self, ctry, ntry, proxy, callback):
        message = u"\n".join([
            _(u"Coletando informações necessárias"),
              u"IP: %s" % proxy.get("http", _(u"Conexão padrão")),
            _(u"Tentativa %d/%d\n") % (ctry, ntry)
        ])
        
        callback(message, "")
        
        if self.videoManager.getVideoInfo(ntry=1, proxies=proxy):
            # tamanho do arquivo de vídeo
            self.videoSize = self.videoManager.getStreamSize()
            # título do arquivo de video
            self.videoTitle = self.videoManager.getTitle()
            # extensão do arquivo de video
            self.videoExt = self.videoManager.getVideoExt()
            
        # função de atualização externa
        callback(message, self.videoManager.get_message())
        return (self.videoSize and self.videoTitle)
    
    def createVideoManager(self):
        """ controla a obtenção de links, tamanho do arquivo, title, etc """
        return self.clsVideoManager(self.streamUrl, streamSize = self.videoSize, 
                                    qualidade = self.params["videoQuality"])
        
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
        
        if not self.isTempFileMode: 
            self.salveInfoResumo()
        
        self.fileManager.close()
        self.clear()
        
    def clear(self):
        """ deleta todas as variáveis do objeto """
        Info.delete("manage")
        settings.MANAGE_OBJECT = None
        del self.streamerList
        del self.ctrConnection
        del self.videoManager
        del self.proxyManager
        del self.urlManager
        del self.fileManager
        del self.interval
        del self.params
        
    @FileManager.sincronize
    def recoverTempFile(self):
        """ tenta fazer a recuperação de um arquivo temporário """
        # começa a recuperação do arquivo temporário.
        for copy in self.fileManager.recover(badfile=(not self.isTempFileMode or self.interval.getOffset() != 0)):
            if copy.inProgress and copy.progress == 100.0 and copy.sucess and not copy.error:
                # nunca se deve adcionar a mesma url.
                if not self.urlManager.exist(self.streamUrl):
                    self.urlManager.add(self.streamUrl, self.videoTitle)
                    self.urlManager.saveLast(self.streamUrl, self.videoTitle)
                # caso o download não esteja completo.
                self.salveInfoResumo()
            yield copy
            
    def isComplete(self):
        """ informa se o arquivo já foi completamente baixado """
        return (self.cacheBytesTotal >= (self.videoSize-25))
    
    @property
    def isTempFileMode(self):
        """ avalia se o arquivo de video está sendo salva em um arquivo temporário """
        return (self.usingTempfile or self.params["tempfile"])
    
    def getGlobalStartTime(self):
        return self.globalStartTime
    
    def getStartCacheSize(self):
        return self.startCacheSize
        
    def getInitPos(self):
        return self.params.get("seekpos",0)
    
    def isResuming(self):
        return self.resuming
    
    def getVideoTitle(self):
        return self.videoTitle
    
    def getVideoUrl(self):
        return self.streamUrl
    
    def getVideoSize(self):
        return self.videoSize
    
    def getVideoExt(self):
        return self.videoExt
    
    def nowSending(self): 
        return self.interval.send_info['sending']
    
    def getCacheBytesTotal(self): 
        return self.cacheBytesTotal
    
    def getGlobalSpeed(self):
        return self.globalSpeed
    
    def setGlobalSpeed(self, speed):
        self.globalSpeed = speed
        
    def getGlobalEta(self):
        return self.globalEta
    
    def setGlobalEta(self, eta):
        self.globalEta = eta
    
    @FileManager.sincronize
    def salveInfoResumo(self):
        """ salva todos os dados necessários para o resumo do arquivo atual """
        self.ctrConnection.removeStopped()
        pending = [] # coleta geral de informações.
        
        for smanager in self.ctrConnection.getConnList():
            ident = smanager.ident
            
            # a conexão deve estar ligada a um interv
            if self.interval.has( ident ):
                pending.append((
                    self.interval.getIndex( ident), 
                    smanager.numBytesLidos, 
                    self.interval.getStart( ident), 
                    self.interval.getEnd( ident),
                    self.interval.getBlockSize( ident)
                ))
                
        pending.extend( self.interval.getPending() )
        pending.sort()
        
        self.resumeInfo.update(title = self.videoTitle,
            videoQuality = self.params["videoQuality"],
            cacheBytesTotal = self.cacheBytesTotal, 
            cacheBytesCount = self.cacheBytesCount,
            videoPath = self.params["videoPath"],
            seekPos = self.interval.seekpos,
            videoSize = self.videoSize, 
            videoExt = self.videoExt, 
            pending = pending
        )
    
    def setRandomRead(self, seekpos):
        """ Configura a leitura da stream para um ponto aleatório dela """
        self.notifiqueConexoes(True)

        if not self.isTempFileMode: self.salveInfoResumo()
        
        self.cacheBytesTotal = self.startCacheSize = seekpos
        del self.interval, self.fileManager

        self._init(tempfile = True, seekpos = seekpos)
        self.params["seeking"] = True
        self.start()
        return True

    def reloadSettings(self):
        if self.params.get("seeking", False):
            self.notifiqueConexoes(True)

            self.cacheBytesTotal = self.startCacheSize = 0
            del self.interval, self.fileManager

            self._init(tempfile = self.usingTempfile, seekpos = 0)
            self.params["seeking"] = False
            self.start()
        return True
    
    def notifiqueConexoes(self, condition):
        """ Informa as conexões que um novo ponto da stream está sendo lido """
        for conn in self.ctrConnection.getConnList():
            if condition: conn.setWait()
            elif conn.isWaiting:
                conn.stopWait()
        
    @base.protected()
    def update(self):
        """ atualiza dados de transferência do arquivo de vídeo atual """
        start = self.interval.getFirstStart()
        self.interval.send_info["sending"] = start
        nbytes = self.interval.send_info["nbytes"].get(start,0)
        
        if start >= 0:
            startabs = start - self.interval.getOffset()
            self.cacheBytesCount = startabs + nbytes
            
        elif self.isComplete(): # isComplete: tira a necessidade de uma igualdade absoluta
            self.cacheBytesCount = self.getVideoSize()
            
        if not self.isTempFileMode and (time.time()-self.autoSaveTime) > 300:
            self.autoSaveTime = time.time()
            self.salveInfoResumo()
            
        # reinicia a atividade das conexões
        self.notifiqueConexoes(False)
        