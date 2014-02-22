# coding: utf-8
import re
import urllib.request
import urllib.parse
import urllib.error
import urllib.request
import urllib.error
import urllib.parse
from http import cookiejar

from main.app.generators import Universal
from main.app.util import sites


class ConnectionProcessor(object):
    """ Processa conexões guardando 'cookies' e dados por ips """

    def __init__(self):
        self.cookiejar = cookiejar.CookieJar()
        self.cookieProcessor = urllib.request.HTTPCookieProcessor(cookiejar=self.cookiejar)
        self.logged = False

    def login(self, opener=None, timeout=0):
        """ struct login"""
        return True

    @staticmethod
    def get_stream_header(stream, seekpos, header=""):
        if stream.startswith("FLV"):
            if (stream[:13].endswith("\t" + ("\x00" * 4)) or stream[:13].endswith(("\x00" * 3) + "\t")):
                if seekpos == 0:
                    header = stream[:13]
                else:
                    header, stream = stream[:13], stream[13:]
            elif stream[:9].endswith("\t"):
                if seekpos == 0:
                    header = stream[:9]
                else:
                    header, stream = stream[:9], stream[9:]
        return stream, header

    @staticmethod
    def check_response(offset, seekpos, seekmax, headers):
        """ Verifica se o ponto de leitura atual, mais quanto falta da stream, 
        corresponde ao comprimento total dela """
        contentLength = headers.get("Content-Length", None)
        contentType = headers.get("Content-Type", None)

        if contentType is None: return False
        is_video = bool(re.match("(video/.*$|application/octet.*$)", contentType))

        if not is_video or contentLength is None: return False
        contentLength = int(contentLength)

        # video.mixturecloud: bug de 1bytes
        is_valid = (seekpos != 0 and seekmax == (seekpos + contentLength + 1))

        if not is_valid: is_valid = (seekmax == contentLength)

        if not is_valid:
            # no bytes 0 o tamanho do arquivo é o original
            if seekpos == 0:
                _offset = 0
            else:
                _offset = offset

            # comprimento total(considerando os bytes removidos), da stream
            length = seekpos + contentLength - _offset
            is_valid = (seekmax == length)

        return is_valid

    def get_request(self, url, headers={}, data=None):
        req = urllib.request.Request(url, headers=headers, data=data)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:11.0) Gecko/20100101 Firefox/11.0")
        req.add_header("Connection", "keep-alive")
        return req

    def connect(self, url="", headers={}, data=None, proxies={}, timeout=25, request=None, login=False):
        """ conecta a url data e retorna o objeto criado """
        if request is None: request = self.get_request(url, headers, data)

        self.opener = urllib.request.build_opener(self.cookieProcessor, urllib.request.ProxyHandler(proxies))

        # faz o login se necessário
        if not self.logged or login:
            self.logged = self.login(self.opener, timeout=timeout)
            if not self.logged: return

        return self.opener.open(request, timeout=timeout)


class SiteBase(ConnectionProcessor):
    MP4_HEADER = "\x00\x00\x00\x1cftypmp42\x00\x00\x00\x01isommp423gp5\x00\x00\x00*freevideo served by mod_h264_streaming"
    FLV_HEADER = "FLV\x01\x01\x00\x00\x00\t\x00\x00\x00\t"

    #----------------------------------------------------------------------
    def __init__(self, **params):
        ConnectionProcessor.__init__(self)
        self.params = params
        self.setDefaultParams()

        self.stream_size = params.get("streamSize", 0)
        self.url = self.basename = self.message = ""

        self.configs = {}
        self.headers = {}

    def setDefaultParams(self):
        self.params.setdefault("quality", 2)
        if self.params["quality"] == 0:
            self.params["quality"] = 1

    def __del__(self):
        del self.basename
        del self.params
        del self.configs
        del self.url

    def get_basename(self):
        return self.basename

    def __delitem__(self, arg):
        self.configs.clear()

    def __getitem__(self, name):
        return self.configs[name]

    def __setitem__(self, name, value):
        self.configs[name] = value

    def get_message(self):
        return self.message

    def suportaSeekBar(self):
        return False

    def get_header(self):
        if self.is_mp4():
            header = self.MP4_HEADER
        else:
            header = self.FLV_HEADER
        return header

    def get_header_size(self):
        if self.is_mp4():
            size = len(self.MP4_HEADER)
        else:
            size = len(self.FLV_HEADER)
        return size

    def get_video_id(self):
        """ retorna só o id do video """
        return Universal.get_video_id(self.basename, self.url)

    def get_init_page(self, proxies={}, timeout=30):
        assert self.getVideoInfo(proxies=proxies, timeout=timeout)

    def getVideoInfo(self, ntry=3, proxies={}, timeout=60):
        # extrai o titulo e o link do video, se já não tiverem sido extraidos
        if not self.configs:
            nfalhas = 0
            while nfalhas < ntry:
                try:
                    self.start_extraction(proxies=proxies, timeout=timeout)
                    # extrai e guarda o tanho do arquivo
                    if not self.stream_size:
                        self.stream_size = self.get_size(proxies=proxies, timeout=timeout)
                except Exception as e:
                    print(str(e))
                if not self.has_conf():
                    self.configs = {}
                    nfalhas += 1
                else:
                    break  # sucesso!
        return self.has_conf()

    def has_conf(self):
        return (self.has_link() and self.has_title() and
                bool(self.stream_size))

    def has_link(self):
        try:
            haslink = bool(self.getLink())
        except:
            haslink = False
        return haslink

    def has_title(self):
        try:
            hastitle = bool(self.getTitle())
        except:
            hastitle = False
        return hastitle

    def get_file_link(self, data):
        """ retorna o link para download do arquivo de video """
        return self.getLink()

    def get_count(self, data):
        """ herdado e anulado. retorna zero para manter a compatibilidade """
        return 0

    def getLink(self):
        return self.configs["url"]

    def has_duration(self):
        return bool(self.configs.get("duration", None))

    def get_duration(self):
        return self.configs["duration"]

    def get_relative(self, pos):
        """ retorna o valor de pos em bytes relativo a duração em mp4 """
        if self.has_duration():  # if 'video/mp4' file
            try:
                result = float(self.get_duration()) * (float(pos) / self.getStreamSize())
            except:
                result = 0
        else:
            result = pos
        return result

    def get_relative_mp4(self, pos):
        if self.has_duration():  # if 'video/mp4' file
            try:
                result = (float(pos) / self.get_duration()) * self.getStreamSize()
            except:
                result = 0
        else:
            result = pos
        return result

    def is_mp4(self):
        return self.has_duration()

    def getVideoExt(self):
        return self.configs.get("ext", "flv")

    def getTitle(self):
        """ pega o titulo do video """
        title = urllib.parse.unquote_plus(self.configs["title"])
        title = sites.DECODE(title)  # decodifica o title
        # remove caracteres invalidos
        title = sites.clear_text(title)
        return sites.limite_text(title, endchars="_")

    def get_size(self, proxies={}, timeout=60):
        """ retorna o tamanho do arquivo de vídeo, através do cabeçalho de resposta """
        link = self.getLink()
        try:
            fd = self.connect(sites.get_with_seek(link, 0),
                              headers={"Range": "bytes=0-"},
                              proxies=proxies, timeout=timeout)
            fd.close()
            length = int(fd.headers.get("Content-Length", 0))
            assert (length and (fd.code == 200 or fd.code == 206))
        except:
            link = link.rsplit("&", 1)[0]
            fd = self.connect(url=link, timeout=timeout);
            fd.close()
            length = int(fd.headers.get("Content-Length", 0))
            assert (length and (fd.code == 200 or fd.code == 206))
        return length

    def getStreamSize(self):
        """ retorna o tamanho compleot do arquivo de video """
        return self.stream_size
    
