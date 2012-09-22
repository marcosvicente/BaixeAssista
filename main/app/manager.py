# -*- coding: ISO-8859-1 -*-
## guarda a vers�o do programa.
from symbol import except_clause
PROGRAM_VERSION = "0.2.1"
PROGRAM_SYSTEM = {"Windows": "oswin", "Linux": "oslinux"}

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
from main.app import models # modelo de banco de dados

# INTERNACIONALIZATION
def installTranslation(configs = None):
    """ instala as tradu��es apartir do arquivo de configura��es. """
    if not isinstance(configs, configobj.ConfigObj):
        try:
            path = os.path.join(settings.CONFIGS_DIR, "configs.cfg")
            configs = configobj.ConfigObj( path )
        except:
            configs = {}
    try: import gettext
    except ImportError, err:
        print "Error[import gettext] %s"%err
        raise err

    menus = configs.get("Menus", {})
    lang = menus.get("language", "en")

    localepath = os.path.join(settings.APPDIR, "locale")
    language = gettext.translation("ba_trans", localepath, languages=[lang])

    # instala no espa�o de nomes embutidos
    language.install(unicode=True)
#######################################################################################
class just_try:
    """ executa o m�thodo dentro de um try:except """
    def __call__(this, method):
        def wrap(self, *args, **kwargs): # magic!
            try: method(self, *args, **kwargs)
            except Exception as e:
                print "JUST_TRY - Err: %s"%(e)
                method.error = str(e)
        return wrap
    
def get_filename(filepath, fullname=True):
    """
    fullname: True  -> C:\\filedir\\file.txt -> file.txt
    fullname: False -> C:\\filedir\\file.txt -> file
    """
    filename = os.path.split( filepath )[-1]
    if not fullname: filename = os.path.splitext( filename )[0]
    return filename

def security_save(filepath, _configobj=None, _list=None, newline="\n"):
    """ salva as configura��es da forma mais segura poss�vel. 
    filepath - local para salvar o arquivo
    _configobj - dicion�rio de configura��es
    _list - salva a lista, aplicando ou n�o a newline.
    newline='' - caso n�o haja interesse na adi��o de uma nova linha.
    """
    try: # criando o caminho para o arquivo de backup
        filename = get_filename( filepath ) # nome do arquivo no path.
        backFilePath = filepath.replace(filename, ("_"+filename))
    except Exception, err:
        try: print "Error[security_save:backfilename] %s"%err
        except: pass
        return False
    ######
    # guarda o arquivo antigo temporariamente
    if os.path.exists(filepath):
        try: os.rename(filepath, backFilePath)
        except Exception, err:
            try: print "Error[security_save:rename-backfile] %s"%err
            except: pass
            try:
                os.remove(backFilePath); os.rename(filepath,backFilePath)
            except Exception, err:
                try: print "Error[security_save:remove-backfile] %s"%err
                except: pass
                return False
    ######
    try: # come�a a cria��o do novo arquivo de configura��o
        with open(filepath, "w") as configsfile:
            if type(_list) is list:
                for data in _list:
                    configsfile.write("%s%s"%(data, newline))
            elif isinstance(_configobj, configobj.ConfigObj):
                _configobj.write( configsfile )
            # levanta a exe��o com o objetivo de recuperar o arquivo original
            else: raise AttributeError, "invalid attribute" 

            if os.path.exists(filepath):
                try: os.remove(backFilePath)
                except: pass
    except Exception, err:
        try: print "Error[security_save:saving-configs] %s"%err
        except: pass
        # remove o arquivo atual do erro.
        if os.path.exists(filepath):
            try: os.remove(filepath)
            except: pass
        # restaura o arquivo original
        if not os.path.exists(filepath):
            try: os.rename(backFilePath, filepath)
            except: pass
        return False
    return True
###############################################################################
class GlobalInfo:
    """ Guarda informa��es de estado de outros objetos.
    O objetivo � criar um meio f�cil de obter informa��es de objetos, no escopo
    global, sem precisar ficar acessando o objeto diretamento """

    def __init__(self):
        self.info = {}

    def add_info(self, keyRoot):
        self.info[ keyRoot ] = {}

    def del_info(self, keyRoot):
        if self.info.has_key( keyRoot ):
            del self.info[ keyRoot ]
        return self.info.get(keyRoot, False)

    def get_info(self, keyRoot, keyInfo):
        return self.info.get(keyRoot, {}).get(keyInfo, "")

    def set_info(self, keyRoot, keyInfo, valueInfo):
        self.info[ keyRoot ][ keyInfo ] = valueInfo

globalInfo = GlobalInfo()

################################## FLVPLAYER ##################################
def runElevated(cmd, params):
    """ executa um processo, por�m requistando permiss�es. """
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

class FlvPlayer( threading.Thread):
    """ Classe de controle para player externo. 
    O objetivo � abrir o player exeterno e indicar a ele o que fazer.
    """
    def __init__(self, cmd="", filename="streamFlv", filepath="", port=80):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.cmd = cmd
        self.process, self.running = None, False

        if not filepath:
            self.url="http://localhost:%d/%s"%(port, filename)
        else:
            self.url = '"%s"'%filepath

    def playerStop(self):
        """ p�ra a execu��o do player """
        try: self.process.terminate()
        except: pass

    def isRunning(self):
        return self.running

    def run(self):
        try:
            self.process = runElevated(self.cmd, self.url)
            self.running = True; self.process.wait()
        except ImportError:
            self.process = subprocess.Popen(self.url, executable=self.cmd)
            self.running = True; self.process.wait()
        except: pass
        finally:
            self.running = False

################################ STREAMHANDLE ################################
class RequestHandle( threading.Thread ):
    """ Controla requisi��es de m�dia """
    
    HEADER_OK_200 = "\r\n".join([
        "HTTP/1.1 200 OK", 
        "Server: Python/2.7", 
        "Connection: keep-alive",
        "Content-Length: %s", 
        "Content-Type: video/flv", 
        "Content-Disposition: attachment", 
        "Content-Transfer-Encoding: binary",
        "Accept-Ranges: bytes", 
        "icy-metaint: 0",
        "\n"])

    HEADER_PARTIAL_206 = "\r\n".join([
        "HTTP/1.1 206 OK Partial Content", 
        'Content-type: video/flv',
        'Content-Length: %s' ,
        "icy-metaint: 0",
        'Content-Range: bytes %d-%d/%d',
        '\n'])

    def __init__(self, server, request):
        threading.Thread.__init__(self)
        self.request = request
        self.server = server
        self.sended = self.streamPos = 0
        self.GET, self.headers = "", {}
        
    def get_headers(self, request_data):
        headers = dict( re.findall(r"(.+?):\s*(.*?)(?:\r)?\n+", request_data) )
        get = re.search(r"(GET.+?(?:start=)?\d*)(?:\r)?\n+", request_data).group(1)
        return get, headers

    def get_range(self, get="", headers={}):
        if headers.has_key("Range"):
            matchobj = re.search("bytes=(?P<range>\d+)-?\d*", headers["Range"])
        else:
            matchobj = re.search("GET.+?(?:start=)?(?P<range>[\d\.]+?)\s+HTTP.+", get)
        if matchobj: seekpos = matchobj.group("range")
        else: seekpos = 0
        return seekpos
    
    def send_206_PARTIAL(self, streamPos, streamSize):
        headers = self.HEADER_PARTIAL_206 %(str(streamSize-streamPos), streamPos, (streamSize-1), streamSize)
        self.request.send( headers )

    def send_200_OK(self):
        headers = self.HEADER_OK_200 % self.manage.getVideoSize()
        self.request.send( headers )

    def get_request_data(self, timeout=60):
        data = ""
        ready = select.select([self.request],[],[],timeout)[0]
        while ready:
            data += self.request.recv(1024)
            ready = select.select([self.request],[],[],0)[0]
        return data

    def close_me(self, headers):
        agent = headers.get("User-Agent", "").lower()
        conn = headers.get("Connection", "close").lower()
        return (conn=="close" and not re.search("VLC",agent,re.IGNORECASE))
    
    def lookup_filepath(self, filepath):
        for root, dirs, files in os.walk(settings.STATIC_PATH):
            for name in files:
                path = os.path.join(root, name)
                netpath = path.replace(os.sep, "/") # path network
                if not netpath.endswith( filepath ):
                    continue
                return path
            
    def run(self):
        try:
            data = self.get_request_data()
            self.GET, self.headers = self.get_headers( data )
            
            networkpath = self.getRequestFile()
            filepath = self.lookup_filepath( networkpath )
            
            if not filepath : self.handle_stream()
            else: self.handle_files( filepath )
        except:
            pass
        self.request.close()
        self.server.remove_client( self.request )
        
    def getRequestFile(self):
        matchobj = re.search("GET\s+(?P<file>.+?)\s+(?:HTTP.*)?", self.GET, re.I|re.U)
        if matchobj: getfile = matchobj.group("file")
        else: getfile = None
        return getfile
    
    def handle_files(self, filepath):
        length = os.path.getsize(filepath)
        self.request.send("HTTP/1.0 200 OK\r\n")
        self.request.send("Server: Python/2.7\r\n")
        self.request.send("Connection: keep-alive\r\n")
        self.request.send("Content-Length: %s\r\n\n"%length)
        with open(filepath,"rb") as mediafile:
            self.request.send( mediafile.read() )
            
    def handle_stream(self):
        self.manage = self.server.manage
        self.streammer = self.manage.get_streammer()
        
        position = self.get_range(self.GET, self.headers)
        try: self.streamPos = long(position)
        except:
            self.streamPos = long(self.manage.getVideoSize()/float(position))
            
        print "REQUEST: %s RANGE: %s"%(self.GET, self.streamPos)
        if self.close_me(self.headers): return

        if self.streamPos > 0 and self.manage.videoManager.suportaSeekBar():
            self.manage.setRandomRead( self.streamPos )
            self.send_206_PARTIAL(self.streamPos, self.manage.getVideoSize())
            self.request.send( self.manage.videoManager.getStreamHeader() )
        else:
            self.manage.reloadSettings()
            self.send_200_OK()

        # n�mero de bytes j� enviados ao cliente(player)
        self.sended = self.streamPos

        for stream in self.streammer.get_stream():
            self.sended += self.request.send( stream )
            if self.manage.isComplete(): # diminui a sobrecarga
                time.sleep(0.001)

################################### SERVER ####################################
class Server( threading.Thread ):
    BOOL_TO_INT = {True: 1, False: 0}
    INT_TO_BOOL = {1: True, 0: False}
    
    class __metaclass__(type):
        """ informa o estado do servidor, com base na vari�vel ambiente """
        @property
        def running(cls):
            flag = int(os.environ.get("LOCAL_SERVER_RUNNING",0))
            return cls.INT_TO_BOOL[flag]
        
        @running.setter
        def running(cls, flag):
            os.environ["LOCAL_SERVER_RUNNING"] = str(cls.BOOL_TO_INT[flag])
        
    def __init__(self, manage=None, host="localhost", port=80):
        threading.Thread.__init__(self)
        # p�ra com o processo principal
        self.setDaemon( True )
        self.execute(host, port)
        
        self.manage = manage
        self.clients = []
        
    def __del__(self):
        del self.manage
        self.stop()
        
    def set_manage(self, manage):
        self.manage = manage
    
    def del_manage(self):
        self.manage = None
        
    def execute(self, host, port):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((host, port)); self.server.listen(5)
            Server.running = True
        except Exception as e:
            Server.running = False
            
    def stop_clients(self):
        """ fecha todas as conex�es atualmente ativas """
        for clt in self.clients: clt.close()

    def remove_client(self, clt):
        self.clients.remove(clt)
        
    def stop(self):
        self.server.close()
        Server.running = False
        
    def run(self):
        print "Starting server..."
        while True:
            try:
                rlist, wlist, xlist = select.select([self.server],[],[])
                if len(rlist) == 0: continue
                client, addr = self.server.accept()
            except: break
            RequestHandle(self, client).start()
            self.clients.append( client )
        print "Server stoped!"

################################ PROXYMANAGER ################################
# PROXY MANAGER: TRABALHA OS IPS DE SERVIDORES PROXY
class ProxyManager:
    lockNewIp = threading.Lock()

    def __init__(self, manage):
        self.manage = manage

        self.configPath = os.path.join(settings.APPDIR, "configs")
        self.filePath = os.path.join(self.configPath, "ipSP.cfg")

        fileIp = open( self.filePath )
        self.listaIp = [ip[:-1] for ip in fileIp.readlines()]
        fileIp.close() # close file

        self.generator = self.create_generator()

    def __del__(self):
        self.save()
        del self.configPath
        del self.filePath
        del self.generator
        del self.manage		
        del self.listaIp

    def getNumIps(self):
        """ retorna o n�mero de ips armazenados no arquivo """
        return len(self.listaIp)

    def save(self):
        """ Salva todas as modifica��es """
        if not security_save(self.filePath, _list=self.listaIp):
            print "Erro salvando lista de ips!!!"
            
    def create_generator( self):
        """ Cria um gerador para iterar sobre a lista de ips """
        return (ip for ip in self.listaIp)

    def proxyFormatado( self):
        """Retorna um servidor proxy ja mapeado: {"http": "http://0.0.0.0}"""
        proxy = self.getNewProxy()
        return self.formateProxy( proxy)

    def formateProxy(self, proxy):
        """Retorna o servidor proxy mapeado: {"http": "http://0.0.0.0}"""
        return {"http": "http://%s"%proxy}

    def getNewProxy(self):
        """ retorna um novo ip sem formata��o -> 250.180.200.125:8080 """
        ProxyManager.lockNewIp.acquire()
        try:
            new_proxy = self.generator.next()
        except StopIteration:
            self.generator = self.create_generator()
            new_proxy = self.generator.next()

        ProxyManager.lockNewIp.release()
        return new_proxy

    def setBadIp(self, ip):
        """ reoganiza a lista de ips, 
        colocando os piores para o final """
        if type(ip) is dict: ip = ip["http"]

        # remove a formata��o do ip
        if ip.startswith("http://"):
            httpLen = len("http://")
            ip = ip[httpLen: ]

        # remove o bad ip de sua localiza��o atual
        self.listaIp.remove( ip )

        # desloca o bad ip para o final da lista
        self.listaIp.append( ip )

    def getProxyLink(self, timeout=25):
        """ retona um endere�o de um servidor 
        proxy e um link para um arquivo de video.
        """
        vmanager = self.manage.videoManager

        while True:	
            proxy = self.getNewProxy()
            proxies = self.formateProxy(proxy)

            if vmanager.getVideoInfo(ntry=1, proxies=proxies, timeout=timeout):
                videoLink = vmanager.getLink(); break
            else:
                self.setBadIp(proxies["http"])

        return (proxies, videoLink)

################################# LINKMANAGER #################################
# LINK MANAGER: ADICIONA, REMOVE, E OBT�M INFORMA��ES DOS LINKS ADICIONADAS
class UrlBase(object):
    def __init__(self):
        self.sep = u"::::"

    def __del__(self):
        del self.sep

    def joinUrlDesc(self, url, desc):
        """ junta a url com sua decri��o(t�tulo), usando o separador padr�o """
        return u"%s %s %s"%(url, self.sep, desc)

    def splitUrlDesc(self, url_desc_str):
        """ separa a url de sua decri��o(t�tulo), usando o separador padr�o """
        str_split = url_desc_str.rsplit( self.sep, 1)
        if len(str_split) == 2:
            url, desc = str_split
            return url.strip(), desc.strip()
        # caso n�o haja ainda, uma desc(t�tulo)
        return str_split[0], ""

    def splitBaseId(self, value):
        """ value: megavideo[t53vqf0l] -> (megavideo, t53vqf0l) """
        base, id = value.split("[")
        return base, id[:-1] #remove ]

    def formatUrl(self, valor):
        """ megavideo[t53vqf0l] -> http://www.megavideo.com/v=t53vqf0l """
        import gerador
        base, id = self.splitBaseId( valor )
        return gerador.Universal.get_url( base ) % id

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

    def analizeUrl(self, url):
        """ http://www.megavideo.com/v=t53vqf0l -> (megavideo.com, t53vqf0l) """
        import gerador
        basename = self.getBaseName(url)
        urlid = gerador.Universal.get_video_id(basename, url)
        return (basename, urlid)

########################################################################
class UrlManager( UrlBase ):
    def __init__(self):
        super(UrlManager, self).__init__()
        self.objects = models.Url.objects # acesso a queryset
        self.lastUrl_objects = models.LastUrl.objects

    def getUrlId(self, title):
        """ retorna o id da url, com base no t�tulo(desc) """
        query = self.objects.get(title = title)
        return self.splitBaseId( query.url )[-1]

    def setTitleIndex(self, title):
        """ adiciona um �ndice ao t�tulo se ele j� existir """
        pattern = title + "(?:###\d+)?"
        query = self.objects.filter(title__regex = pattern).order_by("title")
        count = query.count()
        if count > 0:
            db_title = query[count-1].title # last title
            matchobj = re.search("(?:###(?P<index>\d+))?$", db_title)
            try: index = int(matchobj.group("index"))
            except: index = 0
            title = title + ("###%d"%(index+1))
        return title

    def remove(self, title):
        """ remove todas as refer�cias do banco de dados, com base no t�tulo """
        self.objects.get(title=title).delete()

    def add(self, url, title):
        """ Adiciona o t�tulo e a url a base de dados. 
        � importante saber se a url j� foi adicionada, use o m�todo 'exist'."""
        urlname, urlid = self.analizeUrl(url)
        urlmodel = "%s[%s]"%(urlname, urlid)

        # impede t�tulos iguais
        if self.objects.filter(title=title).count() > 0:
            title = self.setTitleIndex(title)

        models.Url(url=urlmodel, title=title).save()

        try:
            lu = self.lastUrl_objects.latest("url")
            lu.url = url; lu.title = title; lu.save()
        except: models.LastUrl(url=url, title=title).save()

    def getTitleList(self):
        return [ query.title
                 for query in self.objects.all().order_by("title")
                 ]

    def getUrlTitle(self, url):
        urlmodel = "%s[%s]"%self.analizeUrl(url)
        try: query = self.objects.get(url = urlmodel)
        except: return ""
        return query.title

    def getUrlTitleList(self):
        """ retorna todas as urls e titulos adicionados na forma [(k,v),] """
        return [(self.formatUrl(query.url), query.title) 
                for query in self.objects.all()
                ]

    def getLastUrl(self):
        try: query = self.lastUrl_objects.latest("url")
        except: return "http://", "..."
        return (query.url, query.title)

    def exist(self, url):
        """ avalia se a url j� existe na base de dados """
        urlmodel = "%s[%s]"%self.analizeUrl(url)
        query = self.objects.filter(url=urlmodel)
        return (query.count() > 0) # se maior ent�o existe

########################################################################
class ResumeBase(object):
    """ Cria a estrutura de amazenamento de dados de resumo """
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.query = None

    def base64Encode(self, value):
        """ codifica o tipo de Python em 'value' para tipo 'cPickle' -> 'base64'"""
        return base64.b64encode(cPickle.dumps(value))

    def sha_encode(self, value):
        """ codifica 'value' dado para formato de dados 'cha' """
        try: value = sha.sha( value ).hexdigest()
        except:
            try: value = unicodedata.normalize("NFKD", unicode(value,"UTF-8"))
            except: value = unicodedata.normalize("NFKD", value)
            osha = sha.sha( value.encode("ASCII","ignore") )
            value = osha.hexdigest()
        return value

    def update(self, title):
        self.query = self.get(title)

    def get_file_quality(self):
        return self.query.streamQuality

    def get_file_ext(self):
        return self.query.streamExt

    def get_file_size(self):
        """retorna o tamanho total do arquivo sendo resumido"""
        return self.query.streamSize

    def get_seek_pos(self):
        """retorna a posi��o do pr�ximo bloco de bytes"""
        return self.query.resumePosition

    def get_intervals(self):
        """retorna a lista de intervalos pendentes"""
        resumeblocks = self.query.resumeBLocks.encode("ascii")
        return cPickle.loads( resumeblocks )

    def get_send_bytes(self):
        """ n�mero de bytes que ser�o enviados ao player """
        return self.query.sendBytes

    def get_bytes_total(self):
        """ n�mero de total de bytes baixados """
        return self.query.streamDownBytes

class ResumeInfo( ResumeBase ):
    def __init__(self):
        super(ResumeInfo, self).__init__()
        self.objects = models.Resume.objects

    def add(self, title, **kwargs):
        """filename: videoExt; streamSize; seekPos; 
        pending; numTotalBytes; nBytesProntosEnvio; videoQuality
        """
        try: query = self.objects.get(title=title)
        except: query = models.Resume()

        query.title = title
        query.resumeBLocks = cPickle.dumps(kwargs["pending"])
        query.streamDownBytes = kwargs["numTotalBytes"]
        query.sendBytes = kwargs["nBytesProntosEnvio"]
        query.streamQuality = kwargs["videoQuality"]
        query.streamSize = kwargs["streamSize"]
        query.resumePosition = kwargs["seekPos"]
        query.streamExt = kwargs["videoExt"]
        query.save() # sanvando no banco de dados

    def has_info(self, title):
        return bool(self.get(title))

    def remove(self, title):
        self.objects.get(title=title).delete()

    def get(self, title):
        try: query = self.objects.get(title=title)
        except: return
        return query

################################# FILEMANAGER ##################################
# FILE MANAGER: TUDO ASSOCIADO A ESCRITA DA STREAM NO DISCO
class FM_runLocked:
    """ controla o fluxo de escrita e leitura no arquivo de v�deo """
    lock_run = threading.RLock()

    def __call__(this, method):
        def wrapped_method(self, *args, **kwargs):
            with FM_runLocked.lock_run:
                return method(self, *args, **kwargs)
        return wrapped_method

class FileManager:
    def __init__(self, **params):
        """ params: {}
        - tempfile(default=False) -> indica o uso de um arquivo tempor�rio para armazenamento.
        - videoExt(default=flv) -> extens�o do arquivo sendo processando.
        """
        self.params = params
        self.filePath = settings.DEFAULT_VIDEOS_DIR
        self.resumeInfo = ResumeInfo()

    def __del__(self):
        try: self.file.close()
        except: pass
        del self.filePath
        del self.params

    def setFileExt(self, ext):
        self.params["videoExt"] = ext
        
    def getFilePath(self, filename):
        """ retorna o caminho completo para o local do arquivo """
        query = self.resumeInfo.get( filename )

        if query: videoExt = query.streamExt
        else: videoExt = self.params.get("videoExt","")
        videoExt = videoExt or "flv"

        try: filename = unicodedata.normalize("NFKD", unicode(filename,"UTF-8"))
        except: filename = unicodedata.normalize("NFKD", filename)
        filename = filename.encode("ASCII","ignore")
        filename = "%s.%s"%(filename, videoExt)

        filepath = os.path.join(self.filePath, filename)
        return filepath

    def pathExist(self, filename):
        """avalia se o arquivo j� existe na pasta v�deos."""
        filepath = self.getFilePath(filename)
        return os.path.exists(filepath)

    @FM_runLocked()
    def recover(self, filename, badfile=False):
        """ recupera um arquivo tempor�rio, salvando-o de forma definitiva """
        # pega o tamanho atual do arquivo, movendo o ponteiro para o final dele.
        self.file.seek(0,2); filesize = self.file.tell()
        # retorna para o come�o do arquivo de onde come�ar� a leitura.
        self.file.seek(0)
        # local para o novo arquivo.
        filepath = self.getFilePath( filename )
        
        class sucess:
            def __init__(self):
                self.msg = _(u"O arquivo foi recuperado com sucesso!")
                self.sucess = False
            def get_msg(self): return self.msg
            
        class error:
            bad_file_msg = u"".join([
                _(u"O arquivo de v�deo est� corrompido!"), 
                _(u"\nIsso por causa da \"seekbar\".")
            ])
            def __init__(self):
                self.msg = _(u"Erro tentando recuperar arquivo.\nCausa: %s")
                self.error = False
            def get_msg(self): return self.msg
            def set_f_msg(self, msg): self.msg %= msg
            def set_msg(self, msg): self.msg = msg
            
        class copy:
            warning = _(u"O arquivo j� existe!")
            
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
                
        cp = copy() # representa o progresso da c�pia
        
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
                        cp.progress = ((float(bytes_count)/filesize)*100.0)
                        
                        stream = self.file.read( block_size )
                        bytes_len = len( stream )
                        
                        if bytes_len == 0: break
                        
                        new_file.write( stream )
                        bytes_count += bytes_len
                        
                        yield cp # update progress
                    cp.sucess = not cp.cancel
                    yield cp # after break
            except Exception, err:
                cp.err.set_f_msg( str(err) )
                cp.error = True
        if cp.cancel: # cancel copy
            try: os.remove( filepath )
            except: pass
        yield cp

    def resume(self, filename):
        """ faz o resumo de 'filename', caso haja as informa��os necess�rias em 'resumeInfo'"""
        if filename and self.params.get("tempfile",False) is False and self.resumeInfo.has_info( filename ):
            self.file = open(self.getFilePath( filename ), "r+b")
            self.resumeInfo.update( filename ); return True
        return False # o arquivo n�o est� sendo resumido

    def cacheFile(self, filename):
        if self.params.get("tempfile", False) is False:
            filepath = self.getFilePath( filename )
            self.file = open(filepath, "w+b")
        else:
            filepath = os.path.join(self.filePath, "temp")
            self.file = tempfile.TemporaryFile(dir = filepath)

    @FM_runLocked()
    def write(self, pos, data):
        """ Escreve os dados na posi��o dada """
        self.file.seek( pos )
        self.file.write( data )

    @FM_runLocked()
    def read(self, pos, data):
        """ L� o numero de bytes, apartir da posi��o dada """
        self.file.seek( pos )
        stream = self.file.read( data )
        npos = self.file.tell()
        return (stream, npos)

################################## INTERVALO ###################################
# INDEXADOR: TRABALHA A DIVIS�O DA STREAM
class Interval:
    def __init__(self, **params):
        """params = {}; 
        seekpos: posi��o inicial de leitura da stream; 
        index: indice do bloco de bytes; 
        pending: lista de intervals pendetes(n�o baixados); 
        offset: deslocamento do ponteiro de escrita � esquerda.
        maxsize: tamanho do block que ser� segmentado.
        """
        assert params.get("maxsize",None), "maxsize is null"
        self.locks = {}
        
        self.send_info = {"nbytes":{}, "sending":0}
        self.seekpos = params.get("seekpos", 0)
        self.pending = params.get("pending", [])

        self.maxsize = params["maxsize"]
        self.maxsplit = params.get("maxsplit",2)

        self.default_block_size = self.calcule_block_size()
        self.intervals = {}

        # caso a posi��o inicial leitura seja maior que zero, offset 
        # ajusta essa posi��o para zero. equivalente a start - offset
        self.offset = params.get("offset", self.seekpos)

    def __del__(self):
        del self.offset
        del self.seekpos
        del self.send_info
        del self.intervals
        del self.pending

    def canContinue(self, obj_id):
        """ Avalia se o objeto conex�o pode continuar a leitura, 
        sem comprometer a montagem da stream de v�deo(ou seja, sem corromper o arquivo) """
        if self.hasInterval(obj_id):
            return (self.get_end(obj_id) == self.seekpos)
        return False

    def get_offset(self):
        """ offset deve ser usado somente para leitura """
        return self.offset

    def get_index(self, obj_id):
        values = self.intervals.get(obj_id, -1)
        if values != -1: return values[0]
        return values

    def get_start(self, obj_id):
        values = self.intervals.get(obj_id, -1)
        if values != -1: return values[1]
        return values

    def get_end(self, obj_id):
        values = self.intervals.get(obj_id, -1)
        if values != -1: return values[2]
        return values

    def get_block_size(self, obj_id):
        """ retorna o tamanho do bloco de bytes"""
        values = self.intervals.get(obj_id, -1)
        if values != -1: return values[3]
        return values

    def hasInterval(self, obj_id):
        """ avalia se o objeto tem um intervalo ligado a ele """
        return bool(self.intervals.get(obj_id, None))

    def get_first_start( self):
        """ retorna o come�o(start) do primeiro intervalo da lista de intervals """
        intervs = [interval[1] for interval in self.intervals.values()] + \
                  [interval[2] for interval in self.pending]
        intervs.sort()
        try: start = intervs[0]
        except IndexError: start = -1
        return start
    
    def remove(self, obj_id):
        return self.intervals.pop(obj_id, None)
    
    def pending_store(self, *args):
        """ index; nbytes; start; end; block_size """
        self.pending.append( args)
        
    def pending_count(self):
        return len(self.pending)

    def calcule_block_size(self):
        """ calcula quantos bytes ser�o lidos por conex�o criada """
        block_size = int(float(self.maxsize) / float(self.maxsplit))
        min_size = 512*1024 # impede um bloco muito pequeno
        if block_size < min_size: block_size = min_size 
        return block_size

    def updateIndex(self):
        """ reorganiza a tabela de indices """
        intervals = self.intervals.items()
        # organiza por start: (obj_id = 1, (0, start = 1, 2, 3))
        intervals.sort(key=lambda x: x[1][1])
        for index, data in enumerate(intervals, 1):
            obj_id, interval = data
            # aplicando a reorganiza��o dos indices
            self.intervals[ obj_id ][0] = index
    
    def set_new_lock(self, obj_id):
        """ lock usando na sincroniza��o da divis�o do intervalo desse objeto """
        self.locks[ obj_id ] = threading.Lock()
        
    def get_lock(self, obj_id):
        return self.locks[ obj_id ]
        
    def remove_lock(self, obj_id):
        return self.locks.pop(obj_id,None)
    
    def pending_set(self, obj_id):
        """ Configura uma conex�o existente com um intervalo pendente(n�o baixado) """
        self.pending.sort()
        index, nbytes, start, end, block_size = self.pending.pop(0)
        # calcula quantos bytes foram lidos, at� ocorrer o erro.
        novo_grupo_bytes = nbytes - (block_size - (end - start))
        old_start = start
        # avan�a somando o que j� leu.
        start = start + novo_grupo_bytes
        block_size = end - start
        
        self.intervals[obj_id] = [index, start, end, block_size]
        self.set_new_lock( obj_id )
        
        if self.send_info["nbytes"].get(old_start,None) is not None:
            del self.send_info["nbytes"][old_start]
            
        self.send_info["nbytes"][start] = 0
    
    def derivative_set(self, other_obj_id):
        """ cria um novo intervalo, apartir de um j� existente """
        def get_average( data ):
            """ retorna a m�dia de bytes atual do intervalo """
            index, start, end, block = data
            nbytes = self.send_info["nbytes"][ start ]
            return int(float((block - nbytes))*0.5)
            
        def is_suitable( data ):
            """ verifica se o intervalo � condidato a altera��o """
            return (get_average(data) > (256*1024))
        
        intervals = self.intervals.items()
        intervals.sort(key=lambda x: x[1][1])
        
        for obj_id, data in intervals:
            if not is_suitable( data ): continue
            
            with self.get_lock( obj_id ):
                # se o objeto alterou seus dados quando chamou o lock
                data = self.intervals[ obj_id ] # dados atualizados
                index, start, end, block_size = data
                
                # segunda verifica��o, quarante que o intervalo ainda � candidato.
                if not is_suitable( data ): continue
                # reduzindo o tamanho do intervalo antigo
                new_end = end - get_average( data )
                
                # recalculando o tamanho do bloco de bytes
                new_block_size = new_end - start
                self.intervals[ obj_id ][-2] = new_end
                self.intervals[ obj_id ][-1] = new_block_size
                
                # criando um novo intervalo, derivado do atual
                start = new_end
                block_size = end - start
                
                self.intervals[ other_obj_id ] = [0, start, end, block_size]
                self.set_new_lock( other_obj_id )
                
                self.send_info["nbytes"][start] = 0
                self.updateIndex()
                break
            
    def new_set(self, obj_id):
        """ cria um novo intervalo de divis�o da stream """
        start = self.seekpos

        if start < self.maxsize: # A origem em rela��o ao final
            end = start + self.default_block_size

            # verificando se final da stream j� foi alcan�ado.
            if end > self.maxsize: end = self.maxsize
            difer = self.maxsize - end
            
            # Quando o resto da stream for muito pequeno, adiciona ao final do interv.
            if difer > 0 and difer < 512*1024: end += difer
            block_size = end - start
            
            self.intervals[obj_id] = [0, start, end, block_size]
            self.set_new_lock( obj_id )
            
            # associando o in�cio do intervalo ao contador
            self.send_info["nbytes"][start] = 0

            self.seekpos = end
            self.updateIndex()

################################ main : manage ################################
import gerador

class Streammer:
    """ l� e retorna a stream de dados """
    #----------------------------------------------------------------------
    def __init__(self, manage):
        self.manage = manage
        self.seekpos = self.sended = 0

    def get_stream(self, block_size=524288):
        while self.sended < self.manage.getVideoSize():
            if self.seekpos < self.manage.nBytesProntosEnvio:
                block_len = block_size

                if (self.seekpos + block_len) > self.manage.nBytesProntosEnvio:
                    block_len = self.manage.nBytesProntosEnvio - self.seekpos

                stream, self.seekpos = self.manage.fileManager.read(self.seekpos, block_len)
                self.sended += block_len
                yield stream
            else:
                time.sleep(0.001)
        yield "" # end stream

    def __del__(self):
        del self.manage

########################################################################
class CTRConnection(object):
    """ controla todas as conex�es criadas """
    #----------------------------------------------------------------------
    def __init__(self, manage):
        self.manage = manage
        # controla a transfer�ncia do arquivo de v�deo.
        self.streamManager = gerador.Universal.getStreamManager( manage.streamUrl )
        # guarda as conexoes criadas
        self.connList = []
        
    def __del__(self):
        del self.manage
        del self.streamManager
        del self.connList
        
    def update(self, **params):
        """ atualiza os parametros de configura��o das conex�es ativas """
        for sm in self.connList:
            if sm.wasStopped(): continue
            for key, value in params.items():
                sm[ key ] = value
                
    def startConnections(self, noProxy=False, numOfConn=0, **params):
        startedList = []
        for index in range(0, numOfConn):
            sm = self.startNewConnection(noProxy, **params)
            startedList.append( sm.ident )
        return startedList
    
    def startConnectionWithProxy(self, numOfConn=0, **params):
        return self.startConnections(False, numOfConn, **params)
    
    def startConnectionWithoutProxy(self, numOfConn=0, **params):
        return self.startConnections(True, numOfConn, **params)
    
    def stopConnections(self, numOfConn=0):
        """ p�ra groupos de conex�es dado por 'numOfConn' """
        stopedList = []
        for r_index in range(0, abs(numOfConn)):
            for s_index in range(len(self.connList)-1, -1, -1):
                sm = self.connList[ s_index ]
                if not sm.wasStopped(): # desconsidera conex�es inativas
                    sm.stop(); stopedList.append(sm.ident)
                    break
        # remove todas as conex�es paradas
        self.removeStopedConnection()
        return stopedList

    def startNewConnection(self, noProxy=False, **params):
        """ inicia uma nova conex�o de transfer�ncia de v�deo.
        params: {}
        - noProxy: se a conex�o usar� um ip de um servidor proxy.
        - ratelimit: limita a velocidade de sub-conex�es criadas, para o n�mero de bytes.
        - timeout: tempo de espera por uma resposta do servidor de stream(segundos).
        - typechange: muda o tipo de conex�o.
        - waittime: tempo de espera entra as reconex�es.
        - reconexao: tenta reconectar o n�mero de vezes informado.
        """
        sm = self.streamManager(self.manage, noProxy, **params)
        sm.start(); self.addConnection( sm)
        return sm

    def addConnection(self, refer):
        """ adiciona a refer�ncia para uma nova conex�o criada """
        msgerr = u"refer�ncia '%s' inv�lida" % refer
        assert isinstance(refer, (StreamManager, StreamManager_)), msgerr
        self.connList.append( refer)

    def getnActiveConnection(self):
        """ retorna o n�mero de conex�es criadas e ativas """
        return len([sm for sm in self.connList if not sm.wasStopped()])

    def getnTotalConnection(self):
        """ retorna o n�mero de conex�es criadas"""
        return len(self.connList)

    def removeStopedConnection(self):
        """ remove as conex�es que estiverem completamente paradas """
        searching = True
        while searching:
            for sm in self.connList:
                if not sm.isAlive():
                    self.connList.remove(sm)
                    break
            else:
                searching = False
                
    def stopAllConnections(self):
        """ p�ra todas as conex�es atualmente ativas """
        for sm in self.connList: sm.stop()

    def getConnections(self):
        """ retorna a lista com todas as conex�es criadas """
        return self.connList

# GRUPO GLOBAL DE VARIAVEIS COMPARTILHADAS
class Manage( object ):
    syncLockWriteStream = threading.Lock()
    
    if not Server.running:
        settings.LOCAL_SERVER = localServer = Server()
        localServer.start()
    else:
        localServer = settings.LOCAL_SERVER
        
    def __init__(self, URL = "", **params):
        """ params: {}
        - tempfile: define se o v�deo ser� gravado em um arquivo tempor�rio
        - videoQuality: qualidade desejada para o v�deo(1 = baixa; 2 = m�dia; 3 = alta).
        """
        assert URL, _("Entre com uma url primeiro!")
        self.streamUrl = URL # guarda a url do video
        self.params = params
        self.numTotalBytes = 0
        self.posInicialLeitura = 0
        self.updateRunning = False
        self.streamServer = None
        self.usingTempfile = params.get("tempfile", False)

        # manage log
        globalInfo.add_info("manage")
        
        # atualiza manager no servidor, pois seus dados ser�o usados na transfer�cia da stream.
        self.localServer.set_manage( self )
        
        # guarda no banco de dados as urls adicionadas
        self.urlManager = UrlManager()

        try: self.urlManager.analizeUrl( self.streamUrl )
        except: raise AttributeError, _(u"Sem suporte para a url fornecida.")

        # nome do video ligado a url
        self.videoTitle = self.urlManager.getUrlTitle( self.streamUrl )
        self.videoSize = 0 # tamanho total do video
        self.videoExt = "" # extens�o do arquivo de v�deo
        
        # embora o m�todo inicialize tenha outro prop�sito, ele tamb�m 
        # complementa a primeira inicializa��o do objeto Manage.
        self.inicialize()
        
        # controla a obten��o de links, tamanho do arquivo, title, etc.
        vmanager = gerador.Universal.getVideoManager( self.streamUrl )
        # pode ser alterado em "inicialize", se resumindo.
        qualidade = self.params.get("videoQuality", 2)
        self.videoManager = vmanager(self.streamUrl, qualidade=qualidade)
        
        # controle das conex�es
        self.ctrConnection = CTRConnection( self)
        
        # gerencia os endere�os dos servidores proxies
        self.proxyManager = ProxyManager( self)

    def inicialize(self, **params):
        """ m�todo chamado para realizar a configura��o de leitura aleat�ria da stream """
        self.params.update( params )

        self._canceledl = False    # cancelar o download?
        self.velocidadeGlobal = 0  # velocidade global da conex�o
        self.tempoDownload = ""    # tempo total de download
        self.nBytesProntosEnvio = 0
        self.fileManager = FileManager(
            tempfile = self.params.get('tempfile', False))
        
        # avalia se o arquivo pode ser resumido
        self.resumindo = self.fileManager.resume( self.videoTitle )

        if self.resumindo:
            self.nBytesProntosEnvio = self.fileManager.resumeInfo.get_send_bytes()
            self.videoSize = self.fileManager.resumeInfo.get_file_size()
            self.numTotalBytes = self.fileManager.resumeInfo.get_bytes_total()
            seekpos = self.fileManager.resumeInfo.get_seek_pos()
            intervs = self.fileManager.resumeInfo.get_intervals()

            # Sem o par�metro qualidade do resumo, o usu�rio poderia 
            # corromper o arquivo de video, dando uma qualidade diferente
            self.params["videoQuality"] = self.fileManager.resumeInfo.get_file_quality()
            self.videoExt = self.fileManager.resumeInfo.get_file_ext()

            self.interval = Interval(maxsize = self.videoSize,
                                     seekpos = seekpos, offset = 0, pending = intervs,
                                     maxsplit = self.params.get("maxsplit", 2))
            
            self.posInicialLeitura = self.numTotalBytes

    def get_streammer(self):
        """ streammer controla a leitura dos bytes enviados ao player """
        return Streammer( self)

    def delete_vars(self):
        """ deleta todas as vari�veis do objeto """
        globalInfo.del_info("manage")
        
        # desvincula o manage sendo deletado, do servidor.
        self.localServer.del_manage()
        
        # -------------------------------------------------------------------
        if not self.usingTempfile and not self.params.get("tempfile",False):
            self.salveInfoResumo()

        self.updateRunning = False
        # -------------------------------------------------------------------
        del self.ctrConnection
        del self.videoManager
        del self.proxyManager
        del self.urlManager
        del self.fileManager
        del self.streamServer
        del self.interval
        del self.params
        # -------------------------------------------------------------------

    def start(self, ntry=3, proxy={}, recall=None):
        """ Come�a a coleta de informa��es. Depende da internet, por isso pode demorar para reponder. """
        if not self.videoSize or not self.videoTitle:
            if not self.getInfo(ntry, proxy, recall):
                return False
            
            # salvando o link e o t�tulo
            if not self.usingTempfile and not self.params.get("tempfile",False):
                if not self.urlManager.exist( self.streamUrl ): # � importante n�o adcionar duas vezes
                    self.urlManager.add(self.streamUrl, self.videoTitle)
                # pega o t�tulo j� com um �ndice
                title = self.urlManager.getUrlTitle(self.streamUrl)
                self.videoTitle = title or self.videoTitle

        if not self.resumindo:
            self.fileManager.setFileExt(self.videoExt)
            self.fileManager.cacheFile( self.videoTitle )

            # intervals ser�o criados do ponto zero da stream
            self.interval = Interval(maxsize = self.videoSize, 
                                     seekpos = self.params.get("seekpos", 0),
                                     maxsplit = self.params.get("maxsplit", 2))

        if not self.updateRunning:
            self.updateRunning = True
            #atualiza os dados resumo e leitura
            thread.start_new(self.updateVideoInfo, ())

        # tempo inicial da velocidade global
        self.tempoInicialGlobal = time.time()
        return True # agora a transfer�ncia pode come�ar com sucesso.

    def getInfo(self, retry, proxy, recall):
        nfalhas = 0
        while nfalhas < retry:
            downStartMsg = u"\n".join([
                _(u"Coletando informa��es necess�rias"),
                  u"IP: %s" % proxy.get("http", _(u"Conex�o padr�o")),
                _(u"Tentativa %d/%d\n") % ((nfalhas+1), retry)
            ])
            # fun��o de atualiza��o externa
            recall(downStartMsg, "")
            
            if self.videoManager.getVideoInfo(ntry=1, proxies=proxy):
                # tamanho do arquivo de v�deo
                self.videoSize = self.videoManager.getStreamSize()
                # t�tulo do arquivo de video
                self.videoTitle = self.videoManager.getTitle()
                # extens�o do arquivo de video
                self.videoExt = self.videoManager.getVideoExt()
                break # dados obtidos com sucesso

            # fun��o de atualiza��o externa
            recall(downStartMsg, self.videoManager.get_message())
            nfalhas += 1

            # downlad cancelado pelo usu�rio. 
            if self._canceledl: return False

            # quando a conex�o padr�o falha em obter os dados
            # � vi�vel tentar com um ip de um servidro-proxy
            proxy = self.proxyManager.proxyFormatado()

        # testa se falhou em obter os dados necess�rios
        return (self.videoSize and self.videoTitle)

    @FM_runLocked()
    def recoverTempFile(self):
        """ tenta fazer a recupera��o de um arquivo tempor�rio """
        is_bad_file = (not self.params.get("tempfile",False) or self.interval.get_offset() != 0)
        
        # se o nome do arquivo, com o titulo atual receber um �ndice, guarda o
        # o t�tulo antigo para adicionar o mesmo �ndice quando adicionando a url.
        streamTitle = self.videoTitle
        
        # verifica se a url j� foi salva
        if not self.urlManager.exist( self.streamUrl ):
            # adiciona um indice se t�tulo j� existir(ex:###1)
            self.videoTitle = self.urlManager.setTitleIndex( self.videoTitle )
        else:
            # como a url j� existe, ent�o s� atualiza o t�tulo
            self.videoTitle = self.urlManager.getUrlTitle( self.streamUrl )

        # come�a a recupera��o do arquivo tempor�rio.
        for copy in self.fileManager.recover(self.videoTitle, badfile = is_bad_file):
            if copy.inProgress and copy.progress == 100.0 and copy.sucess and not copy.error:
                # salvando os dados de resumo. O arquivo ser� resum�vel
                self.salveInfoResumo()
                
                # nunca se deve adcionar a mesma url
                if not self.urlManager.exist( self.streamUrl ):
                    self.urlManager.add(self.streamUrl, streamTitle)
            yield copy
            
    def __startServer(self):
        """ Inicia o processo de escuta do servidor """
        if not self.streamServer:
            try:
                self.streamServer = Server( self) # self - o servidor usa dados de Manager
                self.streamServer.start()
            except Exception, err:
                return False
        # informa que o server iniciou com sucesso
        return True
    
    def startServer(self):
        return True
    
    def stopServer(self):
        """ p�ra o servidor completamente """
        if isinstance(self.streamServer, Server):
            self.streamServer.stop()
            self.streamServer = None # n�o iniciado

    def isComplete(self):
        """ informa se o arquivo j� foi completamente baixado """
        return (self.received_bytes() >= (self.getVideoSize()-25))

    def canceledl(self):
        self._canceledl = True

    def getVideoTitle(self):
        return self.videoTitle

    def getUrl(self):
        return self.streamUrl

    def getVideoSize(self):
        return self.videoSize

    def nowSending(self):
        return self.interval.send_info['sending']

    def received_bytes(self):
        """ retorna o numero total de bytes transferidos """
        return self.numTotalBytes

    @FM_runLocked()
    def salveInfoResumo(self):
        """ salva todos os dados necess�rios para o resumo do arquivo atual """
        self.ctrConnection.removeStopedConnection()
        pendingIntervs = [] # coleta geral de informa��es.
        
        for smanager in self.ctrConnection.getConnections():
            ident = smanager.ident
            # a conex�o deve estar ligada a um interv
            if self.interval.hasInterval( ident ):
                pendingIntervs.append((
                    self.interval.get_index( ident), 
                    smanager.numBytesLidos, 
                    self.interval.get_start( ident), 
                    self.interval.get_end( ident),
                    self.interval.get_block_size( ident)
                ))
        pendingIntervs.extend( self.interval.pending )
        pendingIntervs.sort()
        
        self.fileManager.resumeInfo.add(
            self.videoTitle, videoExt = self.videoExt, streamSize = self.getVideoSize(), 
            seekPos = self.interval.seekpos, pending = pendingIntervs, numTotalBytes = self.numTotalBytes, 
            nBytesProntosEnvio = self.nBytesProntosEnvio, videoQuality = self.params.get("videoQuality",2)
        )

    def porcentagem(self):
        """ Progresso do download em porcentagem """
        return StreamManager.calc_percent(self.numTotalBytes, self.getVideoSize())

    def progresso(self):
        """ Progresso do download """
        return "%s / %s"%(StreamManager.format_bytes( self.numTotalBytes ), 
                          StreamManager.format_bytes( self.getVideoSize() ))

    def setRandomRead(self, seekpos):
        """ Configura a leitura da stream para um ponto aleat�rio dela """
        with Manage.syncLockWriteStream:
            self.notifiqueConexoes(True)

            if not self.usingTempfile and not self.params.get("tempfile",False):
                self.salveInfoResumo()

            self.numTotalBytes = self.posInicialLeitura = seekpos
            del self.interval, self.fileManager

            self.inicialize(tempfile = True, seekpos = seekpos)
            self.params["seeking"] = True
            self.start()
        return True

    def reloadSettings(self):
        if self.params.get("seeking", False):
            with Manage.syncLockWriteStream:
                self.notifiqueConexoes(True)

                self.numTotalBytes = self.posInicialLeitura = 0
                del self.interval, self.fileManager

                self.inicialize(tempfile = self.usingTempfile, seekpos = 0)
                self.params["seeking"] = False
                self.start()
        return True

    def notifiqueConexoes(self, flag):
        """ Informa as conex�es que um novo ponto da stream est� sendo lido """
        for smanager in self.ctrConnection.getConnections(): # coloca as conex�es em estado ocioso
            if flag is True:
                smanager.fiqueEmEspera(True)
            elif smanager.estaProntoContinuar():
                # s� libera a conex�o da espera, quando ela confirmar
                # que entendeu a condi��o de reconfigura��o.
                smanager.fiqueEmEspera(False)
                
    def updateVideoInfo(self, args=None):
        """ Atualiza as vari�veis de transfer�ncia do v�deo. """
        startTime = time.time() # temporizador

        while self.updateRunning:
            try: # como self.interval acaba sendo deletado, a ocorrencia de erro � prov�vel
                intervstart = self.interval.get_first_start()
                self.interval.send_info["sending"] = intervstart
                nbytes = self.interval.send_info["nbytes"].get(intervstart, 0)

                if intervstart >= 0:
                    startabs = intervstart - self.interval.get_offset()
                    self.nBytesProntosEnvio = startabs + nbytes

                elif self.isComplete(): # isComplete: tira a necessidade de uma igualdade absoluta
                    self.nBytesProntosEnvio = self.getVideoSize()

                if not self.usingTempfile and not self.params.get("tempfile",False):
                    # salva os dados de resumo no interval de tempo 300s=5min
                    if time.time() - startTime > 300: 
                        startTime = time.time()
                        self.salveInfoResumo()

                # reinicia a atividade das conex�es
                self.notifiqueConexoes(False)
            except: time.sleep(3) # tempo de recupera��o

            time.sleep(0.1)

################################# STREAMANAGER ################################
# CONNECTION MANANGER: GERENCIA O PROCESSO DE CONEX�O

class StreamManager( threading.Thread):
    lockBlocoConfig = threading.Lock()
    syncLockWriteStream = threading.Lock()
    lockBlocoFalha = threading.Lock()

    # lockInicialize: impede que todas as conex�es iniciem ao mesmo tempo.
    lockInicialize = threading.Lock()
    listStrErro = ["onCuePoint"]

    # ordem correta das infos
    listInfo = ["http", "state", "block_index", "remainder_bytes", "local_speed"]
    
    def __init__(self, manage, noProxy=False, **params):
        """ params: {}
        ratelimit: limita a velocidade de sub-conex�es (limite em bytes)
        timeout: tempo de espera para se estabeler a conex�o (tempo em segundos)
        reconexao: n�mero de vezes que conex�o com o servidor, tentar� ser estabelecida.
        waittime: intervalo de tempo aguardado, quando houver falha na tentativa de conex�o.
        typechange: muda o tipo de conex�o(True ou False)
        """
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.params = params
        self.manage = manage
        
        # conex�o com ou sem um servidor
        self.usingProxy = noProxy
        self.proxies = {}
        
        self.link = self.linkSeek = ""
        self.aguarde = [False, False]
        
        self.numBytesLidos = 0
        self.isRunning = True

    def __setitem__(self, key, value):
        assert self.params.has_key( key ), "invalid option name: '%s'"%key
        self.params[ key ] = value
        
    def __del__(self):
        globalInfo.del_info( self.ident )
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
            exponent = long(math.log(bytes, 1024.0))
        suffix = 'bkMGTPEZY'[exponent]
        converted = float(bytes) / float(1024**exponent)
        return '%.2f%s' % (converted, suffix)

    @staticmethod
    def calc_speed(start, now, bytes):
        dif = now - start
        if bytes == 0 or dif < 0.001: # One millisecond
            return '%10s' % '---b/s'
        return '%10s' % ('%s/s' % StreamManager.format_bytes(float(bytes) / dif))

    @staticmethod
    def calc_percent(byte_counter, data_len):
        if data_len is None:
            return '---.-%'
        return '%6s' % ('%3.1f%%' % (float(byte_counter) / float(data_len) * 100.0))

    def slow_down(self, start_time, byte_counter):
        """Sleep if the download speed is over the rate limit."""
        rate_limit = self.params.get("ratelimit", 35840)
        if rate_limit is None or rate_limit == 0 or byte_counter == 0:
            return
        now = time.time()
        elapsed = now - start_time
        if elapsed <= 0.0:
            return
        speed = float(byte_counter) / elapsed
        if speed > rate_limit:
            time.sleep((byte_counter - rate_limit * (now - start_time)) / rate_limit)

    def inicialize(self):
        """ iniciado com thread. Evita travar no init """
        # globalinfo: add_info
        globalInfo.add_info(self.ident)
        globalInfo.set_info(self.ident, "state", _("Iniciando"))

        with StreamManager.lockInicialize:
            timeout = self.params.get("timeout", 25)
            videoManager = self.manage.videoManager
            proxyManager = self.manage.proxyManager

            ## evita a chamada ao m�todo getVideoInfo
            if self.wasStopped(): return

            if self.usingProxy == True:
                if videoManager.getVideoInfo(timeout=timeout):
                    self.link = videoManager.getLink()
            else:
                self.proxies, self.link = proxyManager.getProxyLink(timeout=timeout)

            ip = self.proxies.get("http",_(u"Conex�o Padr�o"))
            globalInfo.set_info(self.ident, "http", ip)

    def stop(self):
        """ p�ra toda a atividade da conex�o """
        self.isRunning = False
        self.fixeFalhaTransfer(_(u"Parado pelo usu�rio"), 3)

    def wasStopped(self):
        return (not self.isRunning)

    def checkStreamError(self, stream):
        """Verifica se os dados da stream estao corretos"""
        for err in StreamManager.listStrErro:
            index = stream.find( err )
            if index >= 0: return index
        return -1

    @staticmethod
    def responseCheck(nbytes, seekpos, seekmax, headers):
        """ Verifica se o ponto de leitura atual, mais quanto falta da stream, 
        corresponde ao comprimento total dela"""
        contentLength = headers.get("Content-Length", None)
        contentType = headers.get("Content-Type", None)

        if contentType is None: return False
        is_video = bool(re.match("(video/.*$|application/octet.*$)", contentType))

        if not is_video or contentLength is None: return False
        contentLength = long(contentLength)

        # video.mixturecloud: bug de 1bytes
        if seekpos != 0 and seekmax == (seekpos + contentLength + 1): return True
        if seekmax == contentLength: return True

        # no bytes 0 o tamanho do arquivo � o original
        if seekpos == 0: nbytes = 0
        # comprimento total(considerando os bytes removidos), da stream
        length = seekpos + contentLength - nbytes
        return seekmax == length

    def aguardeNotificacao(self):
        """ aguarda o processo de configura��o terminar """
        self.aguarde[1] = True
        while self.aguarde[0]: time.sleep(0.1)
        self.aguarde[1] = False

    def fiqueEmEspera(self, flag):
        self.aguarde[0] = flag

    def esperaSolicitada(self):
        return self.aguarde[0]

    def estaProntoContinuar(self):
        return self.aguarde[1]

    def reset_info(self):
        globalInfo.set_info(self.ident, "block_index", "")
        globalInfo.set_info(self.ident, "local_speed", "")

    def streamWrite(self, stream, nbytes):
        """ Escreve a stream de bytes dados de forma controlada """
        with Manage.syncLockWriteStream:
            hasInterval = self.manage.interval.hasInterval( self.ident )
            if not self.wasStopped() and hasInterval and not self.esperaSolicitada():
                start = self.manage.interval.get_start( self.ident )
                offset = self.manage.interval.get_offset()
                
                # Escreve os dados na posi��o resultante
                pos = start - offset + self.numBytesLidos
                self.manage.fileManager.write(pos, stream)
                
                # quanto ja foi baixado da stream
                self.manage.numTotalBytes += nbytes
                self.manage.interval.send_info["nbytes"][start] += nbytes
                
                # bytes lidos da conex�o.
                self.numBytesLidos += nbytes

    def inicieLeitura(self ):
        block_read = 1024; local_time = time.time()
        block_size = self.manage.interval.get_block_size( self.ident )
        interval_start = self.manage.interval.get_start( self.ident)

        while not self.wasStopped() and self.numBytesLidos < block_size:
            if not self.manage.interval.hasInterval(self.ident): break
            
            # bloqueia altera��es sobre os dados do intervalo da conex�o
            lockIterval = self.manage.interval.get_lock( self.ident )
            lockIterval.acquire()
            try:
                # bloco de bytes do intervalo. Poder� ser dinamicamente modificado
                block_size = self.manage.interval.get_block_size(self.ident)
                block_index = self.manage.interval.get_index(self.ident)
                
                # condi��o atual da conex�o: Baixando
                globalInfo.set_info(self.ident, "state", _("Baixando") )
                globalInfo.set_info(self.ident, "block_index", block_index)
                
                # limita a leitura ao bloco de dados
                if (self.numBytesLidos + block_read) > block_size:
                    block_read = block_size - self.numBytesLidos
                    
                # inicia a leitura da stream
                before = time.time()
                streamData = self.streamSocket.read( block_read )
                after = time.time()
                
                streamLen = len(streamData) # n�mero de bytes baixados
                
                if self.esperaSolicitada(): # caso onde a seekbar � usada
                    self.aguardeNotificacao(); break
                    
                # o servidor fechou a conex�o
                if (block_read > 0 and streamLen == 0) or self.checkStreamError( streamData) != -1:
                    self.fixeFalhaTransfer(_("Parado pelo servidor"), 2); break
                    
                # ajusta a quantidade de bytes baixados a capacidade atual da rede, ou ate seu limite
                block_read = self.best_block_size((after - before), streamLen)
                
                # come�a a escrita da stream de video no arquivo local.
                self.streamWrite(streamData, streamLen)
                
                start = self.manage.tempoInicialGlobal
                current = self.manage.received_bytes() - self.manage.posInicialLeitura
                total = self.manage.getVideoSize() - self.manage.posInicialLeitura
                
                # calcula a velocidade de transfer�ncia da conex�o
                speed = self.calc_speed(local_time, time.time(), self.numBytesLidos)
                globalInfo.set_info(self.ident, 'local_speed', speed)
                
                # tempo do download
                self.manage.tempoDownload = self.calc_eta(start, time.time(), total, current)
                # calcula a velocidade global
                self.manage.velocidadeGlobal = self.calc_speed(start, time.time(), current)
                
                if self.numBytesLidos >= block_size:
                    if self.manage.interval.canContinue(self.ident) and not self.manage.isComplete():
                        self.manage.interval.remove( self.ident )# removendo o intervalo completo
                        self.configure() # configurando um novo intervado
                        interval_start = self.manage.interval.get_start(self.ident)
                        local_time = time.time()# reiniciando as vari�veis
                        self.reset_info()
                # sem redu��o de velocidade para o intervalo pricipal
                elif self.manage.nowSending() != interval_start:
                    self.slow_down(local_time, self.numBytesLidos)
            except:
                self.fixeFalhaTransfer(_("Erro de leitura"), 2)
                break
            finally:
                # libera altera��es sobre os dados da conex�o
                lockIterval.release()
        # -----------------------------------------------------
        if self.manage.interval.hasInterval( self.ident ):
            self.manage.interval.remove( self.ident )
            self.manage.interval.remove_lock( self.ident )
            
        if hasattr(self.streamSocket, "close"):
            self.streamSocket.close()
            
        self.reset_info()
    
    @staticmethod
    def getStreamHeader(stream, seekpos, header=""):
        if stream.startswith("FLV") and (stream.endswith("\t") or stream.endswith("\t"+("\x00"*4))):
            if seekpos == 0: header = stream
            else: header, stream = stream, ""
            
        elif stream[:9].startswith("FLV") and stream[:9].endswith("\t"):
            if seekpos == 0: header = stream[:9]
            else: header = stream[:9]; stream = stream[9:]
            
        return stream, header
    
    def removaConfigs(self, errorstring, errornumber):
        """ remove todas as configura��es, importantes, dadas a conex�o """
        if self.manage.interval.hasInterval(self.ident):
            with Manage.syncLockWriteStream: # bloqueia o thread da instance, antes da escrita.
                index = self.manage.interval.get_index( self.ident)
                start = self.manage.interval.get_start( self.ident)
                end = self.manage.interval.get_end( self.ident)
                block_size = self.manage.interval.get_block_size( self.ident)

                # indice, nbytes, start, end
                self.manage.interval.pending_store(index, 
                    self.numBytesLidos, start, end, block_size
                )
                # n�mero de bytes lidos, antes da conex�o apresentar o erro
                bytesnumber = self.numBytesLidos - (block_size - (end - start))
                self.manage.interval.remove(self.ident)
        else: bytesnumber = 0
        ip = self.proxies.get("http", "default")

        # remove as configs de video geradas pelo ip. A falha pode ter
        # sido causada por um servidor inst�vel, lento ou negando conex�es.
        del self.manage.videoManager[ ip ]
        
        if ip != "default" and ((errornumber != 3 and errornumber == 1) or bytesnumber < 524288): # 512k
            self.manage.proxyManager.setBadIp( ip ) # tira a prioridade de uso do ip.
        return bytesnumber
    
    @just_try()
    def fixeFalhaTransfer(self, errorstring, errornumber):
        globalInfo.set_info(self.ident, 'state', errorstring)
        self.reset_info()

        bytesnumber = self.removaConfigs(errorstring, errornumber) # removendo configura��es
        if errornumber == 3 or self.wasStopped(): return # retorna porque a conexao foi encerrada
        time.sleep(0.5)

        globalInfo.set_info(self.ident, "state", _("Reconfigurando"))
        time.sleep(0.5)

        ip = self.proxies.get("http", "default")
        timeout = self.params.get("timeout", 25)
        typechange = self.params.get("typechange", False)
        videoManager = self.manage.videoManager
        proxyManager = self.manage.proxyManager
        
        if self.usingProxy:
            if typechange:
                proxies, link = proxyManager.getProxyLink(timeout=timeout)
                self.usingProxy, self.proxies, self.link = True, proxies, link
                
        elif errornumber == 1 or bytesnumber < 524288: # 512k
            if typechange:
                if videoManager.getVideoInfo(timeout=timeout): # sucess
                    self.proxies, self.link = {}, videoManager.getLink()
                    self.usingProxy = True
            else:
                self.proxies, self.link = proxyManager.getProxyLink(timeout=timeout)
                self.usingProxy = False
                
        globalInfo.set_info(self.ident,"http",self.proxies.get("http",_(u"Conex�o Padr�o")))

    def conecte(self):
        videoManager = self.manage.videoManager
        seekpos = self.manage.interval.get_start(self.ident)
        streamSize = self.manage.getVideoSize()
        initTime = time.time()

        nfalhas = 0
        while not self.wasStopped() and nfalhas < self.params.get("reconexao",3):
            try:
                globalInfo.set_info(self.ident, "state", _("Conectando"))
                waittime = self.params.get("waittime", 2)
                timeout = self.params.get("timeout", 25)
                
                # come�a a conex�o
                self.streamSocket = videoManager.conecte(self.linkSeek, 
                        proxies=self.proxies, timeout=timeout, login=False)
                
                data = self.streamSocket.read( videoManager.STREAM_HEADER_SIZE )
                stream, header = self.getStreamHeader(data, seekpos)
                
                # verifica a validade a resposta.
                isValid = self.responseCheck(len(header), seekpos, 
                                             streamSize, self.streamSocket.headers)
                
                if isValid and self.streamSocket.code == 200:
                    if stream: self.streamWrite(stream, len(stream))
                    return True
                else:
                    globalInfo.set_info(self.ident, "state", _(u"Resposta inv�lida"))
                    self.streamSocket.close(); time.sleep( waittime )
            except Exception as e:
                globalInfo.set_info(self.ident, "state", _(u"Falha na conex�o"))
                time.sleep( waittime )
                
            # se passar do tempo de timeout o ip ser� descartado
            if (time.time() - initTime) > timeout: break
            else: initTime = time.time()

            nfalhas += 1
        return False # nao foi poss�vel conectar

    def configure(self ):
        """ associa a conex�o a uma parte da stream """
        globalInfo.set_info(self.ident, "state", _("Ocioso"))

        if not self.esperaSolicitada():
            with StreamManager.lockBlocoConfig:

                if self.manage.interval.pending_count() > 0:
                    # associa um intervalo pendente(intervalos pendentes, s�o gerados em falhas de conex�o)
                    self.manage.interval.pending_set( self.ident )
                else:
                    # cria um novo intervalo e associa a conex�o.
                    self.manage.interval.new_set( self.ident )

                    # como novos intervalos n�o s�o infinitos, atribui um novo, apartir de um j� existente.
                    if not self.manage.interval.hasInterval( self.ident ):
                        self.manage.interval.derivative_set( self.ident )
                        
                # bytes lido do intervalo atual(como os blocos reduzem seu tamanho, o n�mero inicial ser� sempre zero).
                self.numBytesLidos = 0
        else:
            # aguarda a configura��o terminar
            self.aguardeNotificacao()

    def run(self):
        # configura um link inicial
        self.inicialize()

        while not self.wasStopped() and not self.manage.isComplete():
            try:
                # configura um intervalo para cada conexao
                self.configure()

                if self.manage.interval.hasInterval( self.ident ):
                    start = self.manage.interval.get_start( self.ident )
                    start = self.manage.videoManager.get_relative( start )
                    print 'start: ', start
                    
                    self.linkSeek = gerador.get_with_seek(self.link, start)
                    
                    # Tenta conectar e iniciar a tranfer�ncia do arquivo de video.
                    assert self.conecte(), "IO erro!"
                    self.inicieLeitura()
                    
                # estado ocioso
                else: time.sleep(1)
            except Exception as e:
                self.fixeFalhaTransfer(_("Incapaz de conectar"), 1)
                print "SM - Err: %s" %(e)
        # estado final da conex�o
        globalInfo.set_info(self.ident, "state", _(u"Conex�o parada"))
        
#########################  STREAMANAGER: (megaupload, youtube) ######################
class StreamManager_( StreamManager ):

    def __init__(self, manage, noProxy= False, **params):
        StreamManager.__init__(self, manage, noProxy, **params)
        
    def inicialize(self):
        """ iniciado com thread. Evita travar no init """
        # globalinfo: add_info
        globalInfo.add_info( self.ident)
        globalInfo.set_info(self.ident, "state", "Iniciando")

        if self.usingProxy == True: # conex�o padr�o - sem proxy
            globalInfo.set_info(self.ident, "http", _(u"Conex�o Padr�o"))
        else:
            self.proxies = self.manage.proxyManager.proxyFormatado()
            globalInfo.set_info(self.ident, "http", self.proxies['http'])
            
    @just_try()
    def fixeFalhaTransfer(self, errorstring, errornumber):
        globalInfo.set_info(self.ident, 'state', errorstring)
        self.reset_info()

        typechange = self.params.get("typechange", False)
        proxyManager = self.manage.proxyManager

        bytesnumber = self.removaConfigs(errorstring, errornumber) # removendo configura��es
        if errornumber == 3: return # retorna porque a conexao foi encerrada
        time.sleep(0.5)

        globalInfo.set_info(self.ident, "state", _("Reconfigurando"))
        time.sleep(0.5)

        if self.usingProxy:
            if typechange is True:
                self.usingProxy, self.proxies = False, proxyManager.proxyFormatado()
        elif errornumber == 1 or bytesnumber < 524288:
            if typechange is True:
                self.usingProxy, self.proxies = True, {}
            else:
                self.usingProxy, self.proxies = False, proxyManager.proxyFormatado()

        globalInfo.set_info(self.ident,"http",self.proxies.get("http",_(u"Conex�o Padr�o")))

    def conecte(self):
        videoManager = self.manage.videoManager
        seekpos = self.manage.interval.get_start( self.ident) # posi��o inicial de leitura
        streamSize = self.manage.getVideoSize()
        nfalhas = 0

        while nfalhas < self.params.get("reconexao",1):
            try:
                sleep_for = self.params.get("waittime",2)

                globalInfo.set_info(self.ident, "state", _("Conectando"))
                data = videoManager.get_init_page( self.proxies) # pagina incial
                link = videoManager.get_file_link( data) # link de download
                wait_for = videoManager.get_count( data) # contador
                
                for second in range(wait_for, 0, -1):
                    globalInfo.set_info(self.ident, "state", _(u"Aguarde %02ds")%second)
                    time.sleep(1)

                globalInfo.set_info(self.ident, "state", _("Conectando"))
                self.streamSocket = videoManager.conecte(
                    link, proxies=self.proxies, headers={"Range":"bytes=%s-"%seekpos})

                data = self.streamSocket.read( videoManager.STREAM_HEADER_SIZE )
                stream, header = self.getStreamHeader(data, seekpos)
                
                isValid = self.responseCheck(len(header), seekpos, 
                                             streamSize, self.streamSocket.headers)

                if isValid and (self.streamSocket.code == 200 or self.streamSocket.code == 206):
                    if stream: self.streamWrite(stream, len(stream))
                    return True
                else:
                    globalInfo.set_info(self.ident, "state", _(u"Resposta inv�lida"))
                    self.streamSocket.close()
                    time.sleep( sleep_for )
            except Exception as err:
                globalInfo.set_info(self.ident, "state", _(u"Falha na conex�o"))
                if hasattr(err, "code") and err.code == 503: return False
                time.sleep( sleep_for )
            nfalhas += 1
        return False #nao foi possivel conectar

    def run(self):
        # configura um link inicial
        self.inicialize()

        while self.isRunning and not self.manage.isComplete():
            try:
                # configura um intervalo para cada conexao
                self.configure()

                if self.manage.interval.hasInterval( self.ident ):
                    # tentando estabelece a conex�o como o servidor
                    assert self.conecte(), "IO error!"
                    self.inicieLeitura() # inicia a transferencia de dados
                # estado ocioso
                else: time.sleep(1)
            except Exception as err:
                self.fixeFalhaTransfer(_("Incapaz de conectar"), 1)
                print "SM - Err: %s" %err
        globalInfo.set_info(self.ident, "state", _(u"Conex�o parada"))
        
########################### EXECU��O APARTIR DO SCRIPT  ###########################

if __name__ == '__main__':
    installTranslation() # instala as tradu��es