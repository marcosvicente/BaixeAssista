# -*- coding: ISO-8859-1 -*-
import sys
import sha
import os
import re
import time
import math
import socket
import thread
import cPickle
import urlparse
import tempfile
import threading
import configobj
import subprocess
import unicodedata
import base64
import select

from main import settings
## Servidor multi-threading
from main.concurrent_server.management.commands import runcserver
from main.app.util import sites, base
import logging

logger = logging.getLogger("main.app.manager")
# ------------------------------------------------------
class model(object):
    """ resolve problema com importação circular """
    class __metaclass__(type):
        @property
        def models(self):
            """ modelo de banco de dados """
            from main.app import models
            return models
        
# ------------------------------------------------------
class generators(object):
    class __metaclass__(type):
        @property
        def universal(self):
            from main.app.generators import Universal
            return Universal
        
#################################### INFO ##################################
class Info(object):
    """ guarda o estado do objeto adicionado """
    info = {}
    
    @classmethod
    def add(cls, rootkey):
        cls.info[rootkey]= {}
        
    @classmethod
    def delete(cls, rootkey):
        return cls.info.pop(rootkey, None)
    
    @classmethod
    def get(cls, rootkey, infokey):
        return cls.info.get(rootkey,{}).get(infokey,'')
    
    @classmethod    
    def set(cls, rootkey, infokey, info):
        cls.info[rootkey][infokey] = info
    
    @classmethod
    def clear(cls, rootkey, *keys):
        for infokey in (keys or cls.info[rootkey]):
            cls.info[rootkey][infokey] = ""
            
################################## FLVPLAYER ##################################
class FlvPlayer(threading.Thread):
    """ Classe usada no controle de programas externos(players) """
    
    def __init__(self, cmd="", filepath="", url=""):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.url = url if url else '"%s"'%filepath
        
        self.process = None
        self.running = False
        
        self.setDaemon(True)
        
    @base.protected()
    def stop(self):
        """ stop player process """
        self.process.terminate()
    
    def isRunning(self):
        return self.running
    
    @staticmethod
    def runElevated(cmd, params):
        """ executa um processo, porém requistando permissões. """
        import win32com.shell.shell as shell
        from win32com.shell import shellcon
        from win32con import SW_NORMAL
        import win32event, win32api
        
        process = shell.ShellExecuteEx(
            lpVerb="runas", lpFile=cmd, fMask=shellcon.SEE_MASK_NOCLOSEPROCESS, 
            lpParameters=params, nShow=SW_NORMAL
        )
        hProcess = process["hProcess"]
        class Process:
            processHandle = hProcess
            @staticmethod
            def terminate(): win32api.TerminateProcess(hProcess,0)
            @staticmethod
            def wait(): win32event.WaitForSingleObject(hProcess, win32event.INFINITE)
        return Process
    
    def run(self):
        try:
            self.process = self.runElevated(self.cmd, self.url)
            self.running = True; self.process.wait()
        except ImportError:
            self.process = subprocess.Popen(self.url, executable=self.cmd)
            self.running = True; self.process.wait()
        except: pass
        finally:
            self.running = False
            
################################### SERVER ####################################
class Server( threading.Thread ):
    BOOL_TO_INT = {True: 1, False: 0}
    INT_TO_BOOL = {1: True, 0: False}
    HOST, PORT = "localhost", 8002
    
    class __metaclass__(type):
        """ informa o estado do servidor, com base na variável ambiente """
        @property
        def running(cls):
            flag = int(os.environ.get("LOCAL_SERVER_RUNNING",0))
            return cls.INT_TO_BOOL[flag]
        
        @running.setter
        def running(cls, flag):
            os.environ["LOCAL_SERVER_RUNNING"] = str(cls.BOOL_TO_INT[flag])
        
    def __init__(self, host="localhost", port=8002):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        
        # update host
        Server.HOST = host
        Server.PORT = port
        
    def stop(self): pass
    
    def run(self):
        try:
            cmd = runcserver.Command()
            Server.running = True
            logger.info("Server running...")
            cmd.execute("%s:%s"%(self.HOST, self.PORT), use_reloader=False)
        except Exception as e:
            logger.error("Server listen: %s"%e)
            Server.running = False
        logger.info("Server stoped!")
        
################################ PROXYMANAGER ################################
# PROXY MANAGER: TRABALHA OS IPS DE SERVIDORES PROXY
class ProxyManager(object):
    lockNewIp = threading.Lock()
    ratelimit = 10
    
    def __init__(self):
        self.configPath = os.path.join(settings.CONFIGS_DIR, "iplist.txt")
        self.iplist = configobj.ConfigObj( self.configPath )
        
    def __del__(self):
        self.save()
        del self.iplist
        
    def get_num(self):
        """ retorna o número de ips armazenados no arquivo """
        return len(self.iplist)
        
    def save(self):
        """ Salva todas as modificações """
        self.free_all()
        
        if not base.security_save(self.configPath,  _configobj=self.iplist):
            print "Erro salvando lista de ips!!!"
            
    def free_all(self):
        """ libera todos o ips do lock """
        for ip in self.iplist.iterkeys():
            self.unlock(ip)
        
    def get_formated(self):
        """Retorna um servidor proxy ja mapeado: {"http": "http://0.0.0.0}"""
        return self.formate( self.get_new() )
        
    def formate(self, proxy):
        """Retorna o servidor proxy mapeado: {"http": "http://0.0.0.0}"""
        return {"http": "http://%s"%proxy}
    
    def get_new(self):
        """ retorna um novo ip sem formatação -> 250.180.200.125:8080 """
        with self.lockNewIp:
            iplistkey = self.iplist.keys()
            bestip = iplistkey[0]
            
            for ip in iplistkey:
                if self.iplist[ip].as_int("rating") > self.ratelimit/2 and \
                   not self.iplist[ip].as_bool("lock"):
                    self.iplist[ip]["lock"] = True
                    return ip
            # modo mais complidado
            for ip in iplistkey:
                rate = self.iplist[ip].as_int("rating")
                if self.iplist[ip].as_bool("lock"): continue
                
                for _ip in iplistkey:
                    if ip == _ip: continue
                    if rate > self.iplist[_ip].as_int("rating"):
                        bestip = ip
                        
            # informa que ip já esta em uso
            self.iplist[bestip]["lock"] = True
        return bestip
    
    def unlock(self, ip):
        self.iplist[ip]["lock"] = False
        
    def unformate(self, ip):
        """ removendo a formatação do ip """
        if type(ip) is dict: ip = ip["http"]
        if ip.startswith("http://"): 
            ip = ip[len("http://"):]
        return ip
        
    def set_bad(self, ip):
        """ abaixando a taxa de credibilidade do ip """
        rate = self.iplist[ self.unformate( ip ) ].as_int("rating")
        self.iplist[ self.unformate( ip ) ]["rating"]  = rate-1 if rate > -self.ratelimit else -self.ratelimit
        print "Bad ip: %s"%self.unformate( ip )
        
    def set_good(self, ip):
        """ aumentando a credibilidade do ip """
        rate = self.iplist[ self.unformate( ip ) ].as_int("rating")
        self.iplist[ self.unformate( ip ) ]["rating"]  = rate+1 if rate < self.ratelimit else self.ratelimit
        print "Good ip: %s"%self.unformate( ip )
        
################################# LINKMANAGER #################################
# LINK MANAGER: ADICIONA, REMOVE, E OBTÉM INFORMAÇÕES DOS LINKS ADICIONADAS
class UrlBase(object):
    sep = u"::::::"; short = u"%s[%s]"
    
    @classmethod
    def joinUrlDesc(cls, url, desc):
        """ junta a url com sua decrição(título), usando o separador padrão """
        return u"%s %s %s"%(url, cls.sep, desc)
    
    @classmethod
    def splitUrlDesc(cls, string):
        """ separa a url de sua decrição(título), usando o separador padrão """
        str_split = string.rsplit(cls.sep, 1)
        if len(str_split) == 2:
            url, title = str_split[0].strip(), str_split[1].strip()
        else:
            url, title = str_split[0], ""
        return url, title
    
    @staticmethod
    def splitBaseId(string):
        """ value: megavideo[t53vqf0l] -> (megavideo, t53vqf0l) """
        matchobj = re.search("(?P<base>.+?)\[(?P<id>.+)\]", string, re.S|re.U)
        return (matchobj.group("base"), matchobj.group("id"))
    
    @classmethod
    def formatUrl(cls, string):
        """ megavideo[t53vqf0l] -> http://www.megavideo.com/v=t53vqf0l """
        base, strID = cls.splitBaseId( string )
        return generators.universal.get_url( base ) % strID
    
    @classmethod
    def shortUrl(cls, url):
        return cls.short %cls.analizeUrl( url )
        
    @staticmethod
    def getBaseName(url):
        """ http://www.megavideo.com/v=t53vqf0l -> megavideo.com """
        parse = urlparse.urlparse( url )
        netloc_split = parse.netloc.split(".")
        if parse.netloc.startswith("www"):
            basename = "%s.%s"%tuple(netloc_split[1:3])
        else:# para url sem www inicial
            basename = "%s.%s"%tuple(netloc_split[0:2])
        return basename
    
    @classmethod
    def analizeUrl(cls, url):
        """ http://www.megavideo.com/v=t53vqf0l -> (megavideo.com, t53vqf0l) """
        basename = cls.getBaseName( url )
        urlid = generators.universal.get_video_id(basename, url)
        return (basename, urlid)
        
########################################################################
class UrlManager( UrlBase ):
    def __init__(self):
        super(UrlManager, self).__init__()
        # acesso a queryset
        self.objects = model.models.Url.objects
        
    def getUrlId(self, title):
        """ retorna o id da url, com base no título(desc) """
        query = self.objects.get(title = title)
        basename = self.getBaseName( query.url )
        return generators.universal.get_video_id(basename, query.url)
        
    def setTitleIndex(self, title):
        """ adiciona um índice ao título se ele já existir """
        pattern = title + "(?:###\d+)?"
        query = self.objects.filter(title__regex = pattern)
        query = query.order_by("title")
        count = query.count()
        if count > 0:
            db_title = query[count-1].title # last title
            matchobj = re.search("(?:###(?P<index>\d+))?$", db_title)
            try: index = int(matchobj.group("index"))
            except: index = 0
            title = title + ("###%d"%(index+1))
        return title
    
    @base.just_try()
    def remove(self, title):
        """ remove todas as referêcias do banco de dados, com base no título """
        self.objects.get(title=title).delete()

    def add(self, url, title):
        """ Adiciona o título e a url a base de dados. 
        É importante saber se a url já foi adicionada, use o método 'exist'
        """
        try: lasturl = model.models.LastUrl.objects.latest("url")
        except: lasturl = model.models.LastUrl()
        
        # impede títulos iguais
        if self.objects.filter(title = title).count() > 0:
            title = self.setTitleIndex(title)
        
        # muitas urls para uma unica lasturl
        lasturl.url = url; lasturl.title = title
        lasturl.save()
        
        model.models.Url(_url = self.shortUrl(url), title=title).save()
        
    def getTitleList(self):
        return [query.title for query in self.objects.all().order_by("title")]

    def getUrlTitle(self, url):
        try: query = self.objects.get(_url = self.shortUrl(url))
        except: query = model.models.Url(title = "")
        return query.title
        
    def getUrlTitleList(self):
        """ retorna todas as urls e titulos adicionados na forma [(k,v),] """
        return [(query.url, query.title) for query in self.objects.all()]
        
    def getLastUrl(self):
        """ retorna a url do último video baixado """
        try: query = model.models.LastUrl.objects.latest("url")
        except: query = model.models.LastUrl(url="http://", title="...")
        return (query.url, query.title)
        
    def exist(self, url):
        """ avalia se a url já existe na base de dados """
        query = self.objects.filter(_url = self.shortUrl(url))
        return (query.count() > 0) # se maior então existe
        
########################################################################
class ResumeInfo(object):
    objects = model.models.Resume.objects
    
    def __init__(self, filename):
        try: self.q = self.objects.get(title=filename)
        except: self.q = model.models.Resume(title=filename)
        
        self.filename = filename
        
    def update(self, **kwargs):
        """ kwargs = {}
         - videoExt; videoSize; seekPos; pending; cacheBytesTotal; 
         - cacheBytesCount; videoQuality
        """
        for field in kwargs:
            setattr(self.q, field, kwargs[field])
            
        self.q.save()
        
    def __getitem__(self, name):
        return getattr(self.q, name)
    
    @property
    def query(self):
        return self.q
    
    @property
    def isEmpty(self):
        return self.q.pk is None
    
    @base.just_try()
    def remove(self):
        self.q.delete()
    
################################# FILEMANAGER ##################################
# FILE MANAGER: TUDO ASSOCIADO A ESCRITA DA STREAM NO DISCO
class FM_runLocked(object):
    """ controla o fluxo de escrita e leitura no arquivo de vídeo """
    lock_run = threading.RLock()
    def __call__(self, method):
        def wrapped_method(*args, **kwargs):
            with FM_runLocked.lock_run:
                return method(*args, **kwargs)
        return wrapped_method
    
class FileManager(object):
    tempFilePath = os.path.join(settings.DEFAULT_VIDEOS_DIR, settings.VIDEOS_DIR_TEMP_NAME)
    
    def __init__(self, **params):
        """ params: {}
         ** filepath(default=DEFAULT_VIDEOS_DIR) -> local onde o arquivo de video será salvo.
         ** tempfile(default=False) -> indica o uso de um arquivo temporário para armazenamento.
         ** fileext(default=flv) -> extensão do arquivo sendo processando.
        """
        self.params = params
        params.setdefault("filepath", settings.DEFAULT_VIDEOS_DIR)
        params.setdefault("fileext", "flv")
        params.setdefault("filename", "")
        params.setdefault("tempfile", False)
        
        if not os.path.exists(params["filepath"]):
            params["filepath"] = settings.DEFAULT_VIDEOS_DIR
        
    def __del__(self):
        self.closeFile()
        del self.params
        
    def __setitem__(self, key, value):
        self.params["key"] = value
    
    def __getitem__(self, key):
        return self.params[key]
    
    @base.protected()
    def closeFile(self):
        self.file.close()
    
    def open(self):
        self.file = self.fileGetOrCreate()
    
    @base.just_try()
    def remove(self):
        os.remove(self.getFilePath())
        
    def getFilePath(self):
        """ retorna o caminho completo para o local do arquivo """
        filename = self.params["filename"]
        
        try: filename = unicodedata.normalize("NFKD", unicode(filename,"UTF-8"))
        except: filename = unicodedata.normalize("NFKD", filename)
        
        filename = filename.encode("ASCII", "ignore")
        filename = "%s.%s"%(filename, self.params["fileext"])
        
        return os.path.join(self.params["filepath"], filename)
        
    @FM_runLocked()
    def recover(self, badfile=False):
        """ recupera um arquivo temporário, salvando-o de forma definitiva """
        # pega o tamanho atual do arquivo, movendo o ponteiro para o final dele.
        self.file.seek(0,2); filesize = self.file.tell()
        # retorna para o começo do arquivo de onde começará a leitura.
        self.file.seek(0)
        # local para o novo arquivo.
        filepath = self.getFilePath()
        
        class sucess(object):
            def __init__(self):
                self.msg = _(u"O arquivo foi recuperado com sucesso!")
                self.sucess = False
            def get_msg(self): return self.msg
            
        class error(object):
            bad_file_msg = u"".join([
                _(u"O arquivo de vídeo está corrompido!"), 
                _(u"\nIsso por causa da \"seekbar\".")
            ])
            def __init__(self):
                self.msg = _(u"Erro tentando recuperar arquivo.\nCausa: %s")
                self.error = False
            def get_msg(self): return self.msg
            def set_f_msg(self, msg): self.msg %= msg
            def set_msg(self, msg): self.msg = msg
            
        class copy(object):
            warning = _(u"O arquivo já existe!")
            
            def __init__(self):
                self.progress = 0.0
                self.inProgress = self.cancel = False
                self.err, self.scs = error(), sucess()
                
            def _set_sucess(self, b): self.scs.sucess = b
            def _get_sucess(self): return self.scs.sucess
            sucess = property(fget=_get_sucess, fset=_set_sucess)
            
            def _set_error(self, b): self.err.error = b
            def _get_error(self): return self.err.error
            error = property(fget=_get_error, fset=_set_error)
            
            def get_msg(self):
                if self.error: return self.err.get_msg()
                if self.sucess: return self.scs.get_msg()
                
        cp = copy() # representa o progresso da cópia
        
        if os.path.exists( filepath ) or badfile:
            if not badfile: cp.err.set_f_msg( cp.warning )
            else: cp.err.set_msg( cp.err.bad_file_msg )
            cp.error = True
        else:
            try:
                block_size = (1024**2) *4 # 4M
                bytes_count = 0
                
                with open(filepath, "w+b") as new_file:
                    cp.inProgress = True
                    
                    while not cp.cancel:
                        if filesize == 0: break # zerodivision erro!
                        cp.progress = ((float(bytes_count)/filesize)*100.0)
                        
                        stream = self.file.read( block_size )
                        bytes_len = len( stream )
                        
                        if bytes_len == 0: break
                        
                        new_file.write( stream )
                        bytes_count += bytes_len
                        
                        yield cp # update progress
                    cp.sucess = not cp.cancel
                    yield cp # after break
            except Exception as err:
                cp.err.set_f_msg( str(err) )
                cp.error = True
        if cp.cancel: # cancel copy
            try: os.remove( filepath )
            except: pass
        yield cp

    def fileGetOrCreate(self):
        """ cria o arquivo """
        if self.params["tempfile"]:
            obj = tempfile.TemporaryFile(dir=self.tempFilePath)
        else:
            filepath = self.getFilePath()
            obj = open(filepath, ("w+b" if not os.path.exists(filepath) else "r+b"))
        return obj
        
    @FM_runLocked()
    def write(self, pos, data):
        """ Escreve os dados na posição dada """
        self.file.seek( pos )
        self.file.write( data )

    @FM_runLocked()
    def read(self, pos, data):
        """ Lê o numero de bytes, apartir da posição dada """
        self.file.seek( pos )
        stream = self.file.read( data )
        npos = self.file.tell()
        return (stream, npos)

################################## INTERVALO ###################################
# INDEXADOR: TRABALHA A DIVISÃO DA STREAM
class Interval(object):
    def __init__(self, **params):
        """params = {}; 
        seekpos: posição inicial de leitura da stream; 
        index: indice do bloco de bytes; 
        pending: lista de 'blocks' pendetes(não baixados); 
        offset: deslocamento do ponteiro de escrita à esquerda.
        maxsize: tamanho do block que será segmentado.
        min_block: tamanho mínimo(em bytes) para um bloco de bytes
        """
        assert params.get("maxsize",None), "maxsize is null"
        self.min_block = params.get("min_block", 1024**2)
        
        self.send_info = {"nbytes":{}, "sending":0}
        self.seekpos = params.get("seekpos", 0)
        self.pending = params.get("pending", [])
        
        self.maxsize = params["maxsize"]
        self.maxsplit = params.get("maxsplit",2)
        
        self.default_block_size = self.calcBlockSize()
        
        self.blocks = {}
        self.locks = {}
        
        # caso a posição inicial leitura seja maior que zero, offset 
        # ajusta essa posição para zero. equivalente a start - offset
        self.offset = params.get("offset", self.seekpos)

    def __del__(self):
        del self.offset
        del self.seekpos
        del self.send_info
        del self.blocks
        del self.pending
    
    def canContinue(self, obj_id):
        """ Avalia se o objeto conexão pode continuar a leitura, 
        sem comprometer a montagem da stream de vídeo(ou seja, sem corromper o arquivo) """
        if self.has(obj_id):
            return (self.getEnd(obj_id) == self.seekpos)
        return False
        
    def getMinBlock(self):
        return self.min_block
    
    def getOffset(self):
        """ offset deve ser usado somente para leitura """
        return self.offset

    def getIndex(self, obj_id):
        items = self.blocks.get(obj_id, [])
        return (-1 if len(items) == 0 else items[0])
    
    def getStart(self, obj_id):
        items = self.blocks.get(obj_id, [])
        return (-1 if len(items) == 0 else items[1])
    
    def getEnd(self, obj_id):
        items = self.blocks.get(obj_id, [])
        return (-1 if len(items) == 0 else items[2])
    
    def getBlockSize(self, obj_id):
        """ retorna o tamanho do bloco de bytes"""
        items = self.blocks.get(obj_id, [])
        return (-1 if len(items) == 0 else items[3])
    
    def has(self, obj_id):
        """ avalia se o objeto tem um intervalo ligado a ele """
        return self.blocks.has_key(obj_id)
    
    def getFirstStart(self):
        """ retorna o começo(start) do primeiro intervalo da lista de blocks """
        blocks = (map(lambda item: item[1], self.blocks.values()) +
                  map(lambda item: item[2], self.pending))
        blocks.sort()
        return (-1 if len(blocks) == 0 else blocks[0])
    
    def remove(self, obj_id):
        self.blocks.pop(obj_id, None)
        self.locks.pop(obj_id, None)
    
    def getPending(self):
        return self.pending
        
    def setPending(self, *args):
        """ index; nbytes; start; end; block_size """
        self.pending.append(args)
        
    def countPending(self):
        return len(self.pending)
    
    def calcBlockSize(self):
        """ calcula quantos bytes serão lidos por conexão criada """
        size = int(float(self.maxsize) / float(self.maxsplit))
        return (size if size > self.min_block else self.min_block)
        
    def updateIndex(self):
        """ reorganiza a tabela de indices """
        items = self.blocks.items()
        
        # organiza por start: (obj_id = 1, (0, start = 1, 2, 3))
        items.sort(key=lambda item: item[1][1])
        
        for index, data in enumerate(items, 1):
            # aplicando a reorganização dos indices
            self.blocks[ data[0] ][0] = index
            
    def setNewLock(self, obj_id):
        """ lock usando na sincronização da divisão do intervalo desse objeto """
        self.locks[ obj_id ] = threading.Lock()
        
    def getLock(self, obj_id):
        return self.locks[ obj_id ]
        
    def configurePending(self, obj_id):
        """ Configura uma conexão existente com um intervalo pendente(não baixado) """
        self.pending.sort()
        index, blocklen, start, end, block = self.pending.pop(0)
        
        self.send_info["nbytes"].pop(start,0)
        start += blocklen
        
        self.blocks[obj_id] = [index, start, end, (end-start)]
        self.send_info["nbytes"][start] = 0
        self.setNewLock( obj_id )
    
    def configureDerivate(self, other_obj_id):
        """ cria um novo intervalo, apartir de um já existente """
        def get_average( data ):
            """ retorna a média de bytes atual do intervalo """
            index, start, end, block = data
            nbytes = self.send_info["nbytes"][ start ]
            return int(float((block - nbytes))*0.5)
            
        def is_suitable( data ):
            """ verifica se o intervalo é condidato a alteração """
            return (get_average(data) > self.min_block)
        
        items = self.blocks.items()
        items.sort(key=lambda item: item[1][1])
        
        for obj_id, data in items:
            if not is_suitable( data ): continue
            
            with self.getLock( obj_id ):
                # se o objeto alterou seus dados quando chamou o lock
                data = self.blocks[ obj_id ] # dados atualizados
                index, start, end, block_size = data
                
                # segunda verificação, quarante que o intervalo ainda é candidato.
                if not is_suitable( data ): continue
                # reduzindo o tamanho do intervalo antigo
                new_end = end - get_average( data )
                
                # recalculando o tamanho do bloco de bytes
                new_block_size = new_end - start
                self.blocks[ obj_id ][-2] = new_end
                self.blocks[ obj_id ][-1] = new_block_size
                
                # criando um novo intervalo, derivado do atual
                start = new_end
                block_size = end - start
                
                self.blocks[ other_obj_id ] = [0, start, end, block_size]
                self.setNewLock( other_obj_id )
                
                self.send_info["nbytes"][start] = 0
                self.updateIndex()
                break
            
    def createNew(self, obj_id):
        """ cria um novo intervalo de divisão da stream """
        start = self.seekpos

        if start < self.maxsize: # A origem em relação ao final
            end = start + self.default_block_size

            # verificando se final da stream já foi alcançado.
            if end > self.maxsize: end = self.maxsize
            difer = self.maxsize - end
            
            # Quando o resto da stream for muito pequeno, adiciona ao final do interv.
            if difer > 0 and difer < self.min_block: end += difer
            block_size = end - start
            
            self.blocks[obj_id] = [0, start, end, block_size]
            self.setNewLock( obj_id )
            
            # associando o início do intervalo ao contador
            self.send_info["nbytes"][start] = 0

            self.seekpos = end
            self.updateIndex()

################################ main : manage ################################
class Streamer(object):
    """ lê e retorna a stream de dados """
    #----------------------------------------------------------------------
    def __init__(self, manage, blocksize = 524288):
        self.seekpos = self.sended = 0
        self.blocksize = blocksize
        self.manage = manage
        self._stop = False
    
    def stop(self): self._stop=True
    
    def __iter__(self):
        self.manage.add_streamer(self)
        
        if self.manage.getInitPos() > 0:
            yield self.manage.videoManager.get_header()
        
        while (not self._stop and self.sended < self.manage.getVideoSize()):
            if self.seekpos < self.manage.cacheBytesCount:
                blocklen = self.blocksize
                
                if (self.seekpos + blocklen) > self.manage.cacheBytesCount:
                    blocklen = self.manage.cacheBytesCount - self.seekpos
                    
                stream, self.seekpos = self.manage.fileManager.read(self.seekpos, blocklen)
                self.sended += blocklen
                yield stream
            time.sleep(0.001)
        print "Exiting: %s"%self
        raise StopIteration

    def __del__(self):
        self.stop()
        del self.manage
        
########################################################################
class Connection(object):
    """ controla todas as conexões criadas """
    #----------------------------------------------------------------------
    def __init__(self, manage):
        self.manage = manage
        # controla a transferência do arquivo de vídeo.
        self.streamManager = generators.universal.getStreamManager(manage.getVideoUrl())
        # guarda as conexoes criadas
        self.connlist = []
        
    def __del__(self):
        del self.manage
        del self.streamManager
        del self.connlist
        
    def update(self, **params):
        """ atualiza os parametros de configuração das conexões ativas """
        for conn in self.connlist:
            if conn.wasStopped(): continue
            for key, value in params.items():
                conn[key] = value
            
    def start(self, noProxy=False, numOfConn=0, **params):
        return [self.startNew(noProxy, **params).ident for i in range(numOfConn)]
    
    def startWithProxy(self, numOfConn=0, **params):
        return self.start(False, numOfConn, **params)
    
    def startWithoutProxy(self, numOfConn=0, **params):
        return self.start(True, numOfConn, **params)
    
    def stop(self, numOfConn=0):
        """ pára groupos de conexões dado por 'numOfConn' """
        connlist = []
        for x in range(0, abs(numOfConn)):
            for y in range(len(self.connlist)-1, -1, -1):
                conn = self.connlist[y]
                # desconsidera conexões inativas
                if conn.wasStopped(): continue
                
                connlist.append(conn.ident)
                conn.stop(); break
        # remove todas as conexões paradas
        self.remeveStopped()
        return connlist
        
    def startNew(self, noProxy=False, **params):
        """ inicia uma nova conexão """
        conn = self.streamManager(self.manage, noProxy, **params)
        conn.start(); self.add(conn)
        return conn

    def add(self, refer):
        """ adiciona a referência para uma nova conexão criada """
        self.connlist.append(refer)
        
    def countActive(self):
        """ retorna o número de conexões criadas e ativas """
        return len([conn for conn in self.connlist if not conn.wasStopped()])
        
    def count(self):
        """ retorna o número de conexões criadas"""
        return len(self.connlist)
    
    def remeveStopped(self):
        """ remove as conexões que estiverem completamente paradas """
        self.connlist = [conn for conn in self.connlist if conn.isAlive()]
        
    def stopAll(self):
        """ pára todas as conexões atualmente ativas """
        for conn in self.connlist: conn.stop()
    
    def getConnList(self):
        """ retorna a lista com todas as conexões criadas """
        return self.connlist
    
# ------------------------------------------------------------------------
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
        self.clsVideoManager = generators.universal.getVideoManager(self.streamUrl)
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
                if not self.urlManager.exist( self.streamUrl ):
                    self.urlManager.add(self.streamUrl, self.videoTitle)
                    
                # pega o título já com um índice
                title = self.urlManager.getUrlTitle(self.streamUrl)
                self.videoTitle = title or self.videoTitle
            else:
                if not self.urlManager.exist( self.streamUrl ):
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
        
    @FM_runLocked()
    def recoverTempFile(self):
        """ tenta fazer a recuperação de um arquivo temporário """
        badfile = (not self.isTempFileMode or self.interval.getOffset() != 0)
        # começa a recuperação do arquivo temporário.
        for copy in self.fileManager.recover(badfile=badfile):
            if copy.inProgress and copy.progress == 100.0 and copy.sucess and not copy.error:
                # salvando os dados de resumo. O arquivo será resumível
                self.salveInfoResumo()
                
                # nunca se deve adcionar a mesma url
                if not self.urlManager.exist( self.streamUrl ):
                    self.urlManager.add(self.streamUrl, self.videoTitle)
            yield copy
            
    @classmethod
    def forceLocalServer(cls, port=8005):
        """ força a execução do servidor na porta informada """
        server = Server(port = port)
        server.start()
        # se iniciou com sucesso
        return Server.running
    
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
    
    @FM_runLocked()
    def salveInfoResumo(self):
        """ salva todos os dados necessários para o resumo do arquivo atual """
        self.ctrConnection.remeveStopped()
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

################################# STREAMANAGER ################################
# CONNECTION MANANGER: GERENCIA O PROCESSO DE CONEXÃO
class StreamManager(threading.Thread):
    lockBlocoConfig = threading.Lock()
    syncLockWriteStream = threading.Lock()
    lockBlocoFalha = threading.Lock()
    
    # lockInicialize: impede que todas as conexões iniciem ao mesmo tempo.
    lockInicialize = threading.Lock()
    listStrErro = ["onCuePoint"]
    
    # ordem correta das infos
    listInfo = ["http", "state", "index", "downloaded", 
                "total", "remainder", "percent", "speed"]
    
    # cache de bytes para extração do 'header' do vídeo.
    cacheStartSize = 256
    
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
        self.info = Info()
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
        self.info.delete(self.ident)
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
        self.info.add(self.ident)
        self.info.set(self.ident, "state", _("Iniciando"))
        
        if self.usingProxy:
            self.proxies = self.manage.proxyManager.get_formated()
        
        if self.videoManager.getVideoInfo(proxies = self.proxies, 
                                          timeout = self.params["timeout"]):
            self.link = self.videoManager.getLink()
            
        self.info.set(self.ident, "http", self.proxies.get("http", _(u"Conexão Padrão")))
        
    def stop(self):
        """ pára toda a atividade da conexão """
        self.isRunning = False
        self.failure(_(u"Parado pelo usuário"), 3)

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
    
    def write(self, stream, nbytes):
        """ Escreve a stream de bytes dados de forma controlada """
        with self.syncLockWriteStream:
            if self.isRunning and self.lockWait.is_set() and self.manage.interval.has(self.ident):
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
                    self.info.set(self.ident, "state", _("Baixando") )
                    self.info.set(self.ident, "index", block_index)
                    
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
                    
                    self.info.set(self.ident, "downloaded", self.format_bytes(self.numBytesLidos))
                    self.info.set(self.ident, "total", self.format_bytes(block_size))
                    self.info.set(self.ident, "remainder", self.format_bytes(block_size - self.numBytesLidos))
                    self.info.set(self.ident, "percent", self.calc_percent(self.numBytesLidos, block_size))
                    # calcula a velocidade de transferência da conexão
                    self.info.set(self.ident, "speed", self.calc_speed(local_time, time.time(), 
                                                                       self.numBytesLidos))
                    # tempo total do download do arquivo
                    self.manage.setGlobalEta(self.calc_eta(start, time.time(), total, current))
                    
                    # calcula a velocidade global
                    self.manage.setGlobalSpeed(self.calc_speed(start, time.time(), current))
                    
                    if self.numBytesLidos >= block_size:
                        self.info.clear(self.ident, list(self.listInfo).remove("http"))
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
        self.info.clear(self.ident, list(self.listInfo).remove("http"))
        
        if self.manage.interval.has(self.ident):
            self.manage.interval.remove(self.ident)
            
        if hasattr(self.streamSocket,"close"):
            self.streamSocket.close()
        
    def unconfig(self, errorstring, errornumber):
        """ remove todas as configurações, importantes, dadas a conexão """
        if self.manage.interval.has( self.ident ):
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
        
    @base.just_try()
    def failure(self, errorstring, errornumber):
        self.info.clear(self.ident)
        self.info.set(self.ident, "state", errorstring)
        
        # removendo configurações
        self.unconfig(errorstring, errornumber)
        
        # retorna porque a conexao foi encerrada
        if not self.isRunning or errornumber == 3: return 
        time.sleep(0.5)
        
        self.info.set(self.ident, "state", _("Reconfigurando"))
        time.sleep(0.5)
        
        if not self.usingProxy:
            if self.params["typechange"]:
                self.proxies = self.manage.proxyManager.get_formated()
                
        elif errornumber == 1 or self.numBytesLidos < self.manage.interval.getMinBlock():
            if not self.params["typechange"]:
                self.proxies = self.manage.proxyManager.get_formated()
            else:
                self.proxies = {}
                
        self.usingProxy = bool(self.proxies)
        self.info.set(self.ident, "http", self.proxies.get("http", _(u"Conexão Padrão")))
        
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
                self.info.set(self.ident, "state", _("Conectando"))
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
                    return True
                else:
                    self.info.set(self.ident, "state", _(u"Resposta inválida"))
                    self.streamSocket.close()
                    time.sleep( self.params["waittime"] )
            except Exception as err:
                self.info.set(self.ident, "state", _(u"Falha na conexão"))
                logger.error("%s Connecting: %s" %(self.__class__.__name__, err))
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
                    self.info.set(self.ident, "state", _("Ocioso"))
                    time.sleep(1)
            except Exception as err:
                self.failure(_("Incapaz de conectar"), 1)
                logger.error("%s Mainloop: %s" %(self.__class__.__name__, err))
                
        self.info.set(self.ident, "state", _(u"Conexão parada"))
        
#########################  STREAMANAGER: (megaupload, youtube) ######################
class StreamManager_( StreamManager ):
    def __init__(self, manage, noProxy= False, **params):
        StreamManager.__init__(self, manage, noProxy, **params)
    
    def _init(self):
        """ iniciado com thread. Evita travar no init """
        self.info.add( self.ident )
        self.info.set(self.ident, "state", "Iniciando")
        
        if not self.usingProxy: # conexão padrão - sem proxy
            self.info.set(self.ident, "http", _(u"Conexão Padrão"))
        else:
            self.proxies = self.manage.proxyManager.get_formated()
            self.info.set(self.ident, "http", self.proxies['http'])
            
    @base.just_try()
    def failure(self, errorstring, errornumber):
        self.info.clear(self.ident)
        self.info.set(self.ident, 'state', errorstring)
        
        proxyManager = self.manage.proxyManager
        downbytes = self.unconfig(errorstring, errornumber) # removendo configurações
        
        if errornumber == 3: return # retorna porque a conexao foi encerrada
        time.sleep(0.5)
        
        self.info.set(self.ident, "state", _("Reconfigurando"))
        time.sleep(0.5)
        
        if not self.usingProxy:
            if self.params["typechange"]:
                self.proxies = proxyManager.get_formated()
            
        elif errornumber == 1 or (downbytes < self.manage.interval.getMinBlock()):
            if not self.params["typechange"]:
                self.proxies = proxyManager.get_formated()
            else:
                self.proxies = {}
                
        self.usingProxy = bool(self.proxies)
        self.info.set(self.ident, "http", self.proxies.get("http", _(u"Conexão Padrão")))
    
    def connect(self):
        seekpos = self.manage.interval.getStart(self.ident) # posição inicial de leitura
        videoSize = self.manage.getVideoSize()
        ctry = 0
        while self.isRunning and ctry < self.params["reconexao"]:
            try:
                self.info.set(self.ident, "state", _("Conectando"))
                
                data = self.videoManager.get_init_page( self.proxies ) # pagina incial
                link = self.videoManager.get_file_link( data ) # link de download
                headerRange = {"Range": "bytes=%s-%s" % (seekpos, videoSize)}
                
                for second in range(self.videoManager.get_count( data), 0, -1):
                    self.info.set(self.ident, "state", _(u"Aguarde %02ds")%second)
                    time.sleep(1)
                
                self.info.set(self.ident, "state", _("Conectando"))
                
                self.streamSocket = self.videoManager.connect(link,
                                headers = headerRange, proxies = self.proxies, 
                                timeout = self.params["timeout"])
                
                stream = self.streamSocket.read( self.cacheStartSize )
                stream, header = self.videoManager.get_stream_header(stream, seekpos)
                
                isValid = self.videoManager.check_response(len(header), seekpos, videoSize, 
                                                           self.streamSocket.headers)
                
                if isValid and (self.streamSocket.code == 200 or self.streamSocket.code == 206):
                    if stream: self.write(stream, len(stream))
                    if self.usingProxy:
                        self.manage.proxyManager.set_good(self.proxies["http"])
                    # indica conectado com sucesso.
                    return True
                else:
                    self.info.set(self.ident, "state", _(u"Resposta inválida"))
                    self.streamSocket.close()
                    time.sleep( self.params["waittime"] )
                    
            except Exception as err:
                self.info.set(self.ident, "state", _(u"Falha na conexão"))
                logger.error("%s Connecting: %s" %(self.__class__.__name__, err))
                time.sleep( self.params["waittime"] )
            ctry += 1
        # indica falha na conexão.
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
                    self.info.set(self.ident, "state", _("Ocioso"))
                    time.sleep(1)
            except Exception as err:
                self.failure(_("Incapaz de conectar"), 1)
                logger.error("%s Mainloop: %s" %(self.__class__.__name__, err))
                
        self.info.set(self.ident, "state", _(u"Conexão parada"))
        
########################### EXECUÇÃO APARTIR DO SCRIPT  ###########################
if __name__ == '__main__': pass

