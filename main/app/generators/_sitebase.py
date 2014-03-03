# coding: utf-8
import re
import urllib.request
import urllib.parse
import urllib.error
import urllib.request
import urllib.error
import urllib.parse

import requests

from main.app.generators import Universal
from main.app.util import sites


class ConnectionBase(object):
    """ Processa conexões guardando 'cookies' e dados por ips """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:11.0) Gecko/20100101 Firefox/11.0"
        self.logged = self.sign_in = False

    def login(self, url, **kwargs):
        """ structs login"""
        return True

    @staticmethod
    def get_stream_header(stream, seek_pos, header=''):
        if stream.startswith(b"FLV"):
            if stream[:13].endswith(b"\t" + (b"\x00" * 4)) or stream[:13].endswith((b"\x00" * 3) + b"\t"):
                if seek_pos == 0:
                    header = stream[:13]
                else:
                    header, stream = stream[:13], stream[13:]
            elif stream[:9].endswith(b"\t"):
                if seek_pos == 0:
                    header = stream[:9]
                else:
                    header, stream = stream[:9], stream[9:]
        return stream, header

    @staticmethod
    def check_response(offset, seek_pos, seek_max, headers):
        """
        Verifica se o ponto de leitura atual, mais quanto falta da stream,
        corresponde ao comprimento total dela
        """
        content_length = headers.get("Content-Length", None)
        content_type = headers.get("Content-Type", None)

        if content_type is None:
            return False
        is_video = bool(re.match("(video/.*$|application/octet.*$)", content_type))

        if not is_video or content_length is None:
            return False
        content_length = int(content_length)

        # video.mixturecloud: bug de 1bytes
        is_valid = (seek_pos != 0 and seek_max == (seek_pos + content_length + 1))

        if not is_valid:
            is_valid = (seek_max == content_length)

        if not is_valid:
            # no bytes 0 o tamanho do arquivo é o original
            if seek_pos == 0:
                _offset = 0
            else:
                _offset = offset
            # comprimento total(considerando os bytes removidos), da stream
            length = seek_pos + content_length - _offset
            is_valid = (seek_max == length)
        return is_valid

    def connect(self, url='', headers={}, data={}, proxies={}, timeout=30, **kwargs):
        """ Conecta a url data e retorna o objeto criado. """
        if self.sign_in and not self.logged:
            self.logged = self.login(url, headers=headers, data=data, proxies=proxies,
                                     timeout=timeout, **kwargs)
        return self.session.get(url, proxies=proxies, timeout=timeout, data=data, **kwargs)


class SiteBase(ConnectionBase):
    MP4_HEADER = "\x00\x00\x00\x1cftypmp42\x00\x00\x00\x01isommp423gp5\x00\x00\x00*freevideo served by mod_h264_streaming"
    FLV_HEADER = "FLV\x01\x01\x00\x00\x00\t\x00\x00\x00\t"

    def __init__(self, **params):
        ConnectionBase.__init__(self)
        self.params = params
        self.set_default_params()

        self.stream_size = params.get("streamSize", 0)
        self.url = self.basename = self.message = ""

        self.configs = {}
        self.headers = {}

    def set_default_params(self):
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

    def random_mode(self):
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
        assert self.get_video_info(proxies=proxies, timeout=timeout)

    def start_extraction(*args, **kwargs):
        pass

    def get_video_info(self, ntry=3, proxies={}, timeout=60):
        # extrai o titulo e o link do video, se já não tiverem sido extraidos
        if not self.configs:
            try_num = 0
            while try_num < ntry:
                try:
                    self.start_extraction(proxies=proxies, timeout=timeout)
                    # extrai e guarda o tanho do arquivo
                    if not self.stream_size:
                        self.stream_size = self.get_size(proxies=proxies, timeout=timeout)
                except Exception as e:
                    print(str(e))
                if not self.has_conf():
                    self.configs = {}
                    try_num += 1
                else:
                    break  # OK
        return self.has_conf()

    def has_conf(self):
        return (self.has_link() and self.has_title() and
                bool(self.stream_size))

    def has_link(self):
        try:
            has = bool(self.get_link())
        except:
            has = False
        return has

    def has_title(self):
        try:
            has = bool(self.get_title())
        except:
            has = False
        return has

    def get_file_link(self, data):
        """ retorna o link para download do arquivo de video """
        return self.get_link()

    def get_count(self, data):
        """ herdado e anulado. retorna zero para manter a compatibilidade """
        return 0

    def get_link(self):
        return self.configs["url"]

    def has_duration(self):
        return bool(self.configs.get("duration", None))

    def get_duration(self):
        return self.configs["duration"]

    def get_relative(self, pos):
        """ retorna o valor de pos em bytes relativo a duração em mp4 """
        if self.has_duration():  # if 'video/mp4' file
            try:
                result = float(self.get_duration()) * (float(pos) / self.get_video_size())
            except:
                result = 0
        else:
            result = pos
        return result

    def get_relative_mp4(self, pos):
        if self.has_duration():  # if 'video/mp4' file
            try:
                result = (float(pos) / self.get_duration()) * self.get_video_size()
            except:
                result = 0
        else:
            result = pos
        return result

    def is_mp4(self):
        return self.has_duration()

    def get_video_ext(self):
        return self.configs.get("ext", "flv")

    def get_title(self):
        """ pega o titulo do video """
        title = urllib.parse.unquote_plus(str(self.configs["title"]))
        # remove caracteres invalidos
        title = sites.clear_text(title)
        return sites.limit_text(title, endchars="_")

    def get_size(self, proxies={}, timeout=60):
        """ retorna o tamanho do arquivo de vídeo, através do cabeçalho de resposta """
        link = self.get_link()
        try:
            fd = self.connect(sites.get_with_seek(link, 0),
                              headers={"Range": "bytes=0-"},
                              proxies=proxies, timeout=timeout)
            fd.close()
            length = int(fd.headers.get("Content-Length", 0))
            assert (length and (fd.code == 200 or fd.code == 206))
        except:
            link = link.rsplit("&", 1)[0]
            fd = self.connect(url=link, timeout=timeout)
            fd.close()
            length = int(fd.headers.get("Content-Length", 0))
            assert (length and (fd.code == 200 or fd.code == 206))
        return length

    def get_video_size(self):
        """ retorna o tamanho compleot do arquivo de video """
        return self.stream_size