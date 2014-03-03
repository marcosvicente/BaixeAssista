# coding: utf-8
import re

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.util import sites


class Uploaded(SiteBase):
    ##
    # http://uploaded.to/io/ticket/captcha/urxo7anj
    # http://uploaded.to/file/urxo7anj
    ##
    controller = {
        "url": "http://uploaded.to/file/%s",
        "patterns": re.compile("(?P<inner_url>(?:http://)?uploaded.to/file/(?P<id>\w+))"),
        "control": "SM_RANGE",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.captcha_url = "http://uploaded.to/io/ticket/captcha/%s"
        # unidade usadas para pegar o tamanho aproximado do video(arquivo)
        self.units = {'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}
        self.pattern_file_size = re.compile("<small.*>(\d+,?\d*)\s*(\w+)</small>", re.DOTALL)
        self.pattern_file_ext = re.compile("[\w\-_]+\.(\w+)")
        self.basename = "uploaded.to"
        self.stream_size = 0
        self.url = url

    def __del__(self):
        del self.url
        del self.units
        del self.stream_size
        del self.pattern_file_size

    def get_size(self, proxies=None):
        return self.stream_size

    def get_file_size(self, data):
        search = self.pattern_file_size.search(data)
        size, unit = search.group(1), search.group(2)
        # conversão da unidade para bytes
        bytes_size = float(size.replace(",", ".")) * self.units[unit.upper()]
        return int(bytes_size)

    def start_extraction(self, proxies={}, timeout=25):
        """ extrai as informaões necessárias, para a transferêcia do arquivo de video """
        url_id = Universal.get_video_id(self.basename, self.url)
        request = self.connect(self.url, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        # tamanho aproximado do arquivo
        self.stream_size = self.get_file_size(page)

        # nome do arquivo
        try:
            title = re.search("<title>(.*)</title>", page).group(1)
        except:
            title = sites.get_random_text()

        # extensão do arquivo
        try:
            ext = self.pattern_file_ext.search(title).group(1)
        except:
            ext = "file"
        ##
        # {type:'download',url:'http://stor1074.uploaded.to/dl/46d975ec-a24e-4e88-a4c9-4000ce5bd1aa'}
        ##
        request = self.connect(self.captcha_url % url_id, proxies=proxies, timeout=timeout)
        url = re.search("url:\s*(?:'|\")(.*)(?:'|\")", request.text).group(1)
        request.close()

        self.configs = {"url": url, "ext": ext, "title": title}