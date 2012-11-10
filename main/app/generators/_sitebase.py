# coding: utf-8
import os
import re
import sys
import cgi
import time
import json
import random
import string
import urllib
import base64
import locale
import urllib2
import urlparse
import decrypter
import datetime
import cookielib
import HTMLParser
import xml.etree.ElementTree
from main.app.generators import Universal
from main.app import manager

# versão será mantida pelo módulo principal
PROGRAM_VERSION = manager.PROGRAM_VERSION
#######################################################################################

def DECODE(texto, alter="ISO-8859-1"):
    """ Tenta decodificar para utf-8. 
    Em caso de erro, a decodificação alternativa será usada """
    try:
        texto = texto.decode('utf-8')
    except UnicodeDecodeError:
        texto = texto.decode(alter)
    except Exception:
        pass
    return texto

def ENCODE(texto, alter="ISO-8859-1"):
    """ Tenta codificar para utf-8. 
    Em caso de erro, a codficação alternativa será usada """
    try:
        texto = texto.encode('utf-8')
    except UnicodeEncodeError:
        texto = texto.encode( alter)
    except Exception:
        pass
    return texto

def limiteTexto(texto, nCaracter=50, final="..."):
    if len(texto) > nCaracter:
        texto = texto[ :nCaracter] + final
    return texto

def clearTitle( title):
    """ remove todos os carecteres considerados inválidos """
    return re.sub(r"[/*&:|\"\'=\\?<>!%$@#()]+", "_", title)

def get_radom_title(size=25):
    chars = [char for char in string.ascii_letters]
    return "".join([random.choice(chars) for i in range(size)])

def get_with_seek(link, seek):
    if link[-1] == ",": link += str(seek)
    if re.match(".+(?:start=|ec_seek=|fs=)", link): link += str(seek)
    if re.match(".+(?:range=%s-)", link): link %= str(seek)
    return link

########################################################################
class Section(object):
    def __init__(self):
        self.section = {}
        
    def add(self, name):
        self.section[name] = {}
    
    def has(self, name):
        return self.section.has_key(name)
    
    def get(self, name):
        if not self.has(name): self.add(name)
        return self.section[name]
    
    def delete(self, name):
        self.section.pop(name,None)
        
    def __del__(self):
        del self.section
        
    def __delitem__(self, name):
        del self.section[name]
        
    def __getitem__(self, name):
        if not self.has(name): self.add(name)
        return self.section[name]
    
    def __setitem__(self, name, value):
        self.section[name] = value
        
class ConnectionProcessor(object):
    """ Processa conexões guardando 'cookies' e dados por ips """
    def __init__(self):
        self.section = Section()
        self.logged = False
        
    def __del__(self):
        del self.section
        
    def set_cookiejar(self, section_name, cookieJar):
        section = self.section[ section_name ]
        section["cookieJar"] = cookieJar
        
    def has_cookieJar(self, section_name):
        section = self.section[ section_name ]
        return section.has_key("cookieJar")
        
    def get_cookieJar(self, section_name):
        section = self.section[ section_name ]
        return section["cookieJar"]
        
    def login(self, opener=None, timeout=0):
        """ struct login"""
        return True

    def get_request(self, url, headers, data):
        req = urllib2.Request(url, headers=headers, data=data)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:11.0) Gecko/20100101 Firefox/11.0")
        req.add_header("Connection", "keep-alive")
        return req

    def connect(self, url="", headers={}, data=None, proxies={}, timeout=25, request=None, login=False):
        """ conecta a url data e retorna o objeto criado """
        ip = proxies.get("http", "default")

        if not self.has_cookieJar(ip): self.set_cookiejar(ip, cookielib.CookieJar())
        if request is None: request = self.get_request(url, headers, data)
        
        processor = urllib2.HTTPCookieProcessor(cookiejar= self.get_cookieJar( ip ))
        opener = urllib2.build_opener(processor, urllib2.ProxyHandler(proxies))
        
        # faz o login se necessário
        if not self.logged or login:
            self.logged = self.login(opener, timeout=timeout)
            if not self.logged: return
            
        return opener.open(request, timeout=timeout)

#################################### BASEVIDEOSITE ####################################
class SiteBase(ConnectionProcessor):
    MP4_HEADER = "\x00\x00\x00\x1cftypmp42\x00\x00\x00\x01isommp423gp5\x00\x00\x00*freevideo served by mod_h264_streaming"
    FLV_HEADER = "FLV\x01\x01\x00\x00\x00\t\x00\x00\x00\t"
    
    #----------------------------------------------------------------------
    def __init__(self, **params):
        ConnectionProcessor.__init__(self)
        self.url = self.basename = self.message = ""
        self.params = params
        self.streamSize = 0
        self.configs = {}
        self.headers = {}
        
    def __del__(self):
        del self.basename
        del self.params
        del self.configs
        del self.url
    
    def get_basename(self):
        return self.basename
    
    def __delitem__(self, arg):
        self.section.delete(arg)
        self.configs.clear()
        
    def get_message(self):
        return self.message

    def suportaSeekBar(self):
        return False
    
    def get_stream_header(self):
        if self.is_mp4(): header = self.MP4_HEADER
        else: header = self.FLV_HEADER
        return header
    
    def get_header_size(self):
        if self.is_mp4(): size = len(self.MP4_HEADER)
        else: size = len(self.FLV_HEADER)
        return size
    
    def get_video_id(self):
        """ retorna só o id do video """
        return Universal.get_video_id(self.basename, self.url)
    
    def get_init_page(self, proxies={}, timeout=30):    
        assert self.getVideoInfo(proxies=proxies, timeout=timeout)

    def getVideoInfo(self, ntry=3, proxies={}, timeout=30):
        ip = proxies.get("http","default")
        section = self.section.get( ip )
        settings = section.get("settings",None)
        
        # extrai o titulo e o link do video, se já não tiverem sido extraidos
        if not settings:
            nfalhas = 0
            while nfalhas < ntry:
                try:
                    self.start_extraction(proxies=proxies, timeout=timeout)
                    if not self.streamSize: # extrai e guarda o tanho do arquivo
                        self.streamSize = self.get_size(proxies=proxies, timeout=timeout)
                    if not self.has_link() or not self.has_title() or not self.streamSize:
                        self.configs = {}; nfalhas += 1
                        continue # falhou em obter o link ou titulo
                    else:
                        section["settings"] = self.configs # relaciona as configs ao ip
                        break # sucesso!
                except Exception as err:
                    pass
                nfalhas += 1
        else:
            self.configs = section["settings"] # transfere para variável de trabalho

        return self.has_link() and self.has_title() and self.streamSize

    def has_link(self):
        try: return bool(self.getLink())
        except: return False

    def has_title(self):
        try: return bool(self.getTitle())
        except: return False

    def get_file_link(self, data):
        """ retorna o link para download do arquivo de video """
        return self.getLink()

    def get_count(self, data):
        """ herdado e anulado. retorna zero para manter a compatibilidade """
        return 0

    def getLink(self):
        return self.configs["url"]
    
    def has_duration(self):
        return bool(self.configs.get("duration",None))
    
    def get_duration(self):
        return self.configs["duration"]
    
    def get_relative(self, pos):
        """ retorna o valor de pos em bytes relativo a duração em mp4 """
        if self.has_duration(): # if 'video/mp4' file
            try: result = float(self.get_duration()) * (float(pos)/self.getStreamSize())
            except: result = 0
        else: result = pos
        return result
    
    def get_relative_mp4(self, pos):
        if self.has_duration(): # if 'video/mp4' file
            try: result = (float(pos)/self.get_duration()) * self.getStreamSize()
            except: result = 0
        else: result = pos
        return result
    
    def is_mp4(self):
        return self.has_duration()
    
    def getVideoExt(self):
        return self.configs.get("ext","flv")

    def getTitle(self):
        """ pega o titulo do video """
        title = urllib.unquote_plus(self.configs["title"])
        title = DECODE(title) # decodifica o title
        # remove caracteres invalidos
        title = clearTitle(title)
        return limiteTexto(title)

    def get_size(self, proxies={}, timeout=60):
        """ retorna o tamanho do arquivo de vídeo, através do cabeçalho de resposta """
        link = get_with_seek(self.getLink(), 0)
        headers = {"Range": "bytes=0-"}
        headers.update( self.headers )
        req = self.get_request(link, headers, data=None)
        try:
            fd = self.connect(request = req, proxies=proxies, timeout=timeout)
            fd.close()
        except:
            fd = urllib.urlopen( link )
            fd.close()
        length = fd.headers.get("Content-Length", None)
        assert (length and (fd.code == 200 or fd.code == 206))
        return long(length)

    def getStreamSize(self):
        """ retorna o tamanho compleot do arquivo de video """
        return self.streamSize
    
