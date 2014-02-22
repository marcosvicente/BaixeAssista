# coding: utf-8
from _sitebase import *

##################################### MEGAUPLOAD ######################################
class Uploaded( SiteBase ):
    ## http://uploaded.to/io/ticket/captcha/urxo7anj
    ## http://uploaded.to/file/urxo7anj
    controller = {
        "url": "http://uploaded.to/file/%s", 
        "patterns": re.compile("(?P<inner_url>(?:http://)?uploaded.to/file/(?P<id>\w+))"), 
        "control": "SM_RANGE", 
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.captchaUrl = "http://uploaded.to/io/ticket/captcha/%s"
        # unidade usadas para pegar o tamanho aproximado do video(arquivo)
        self.unidades = {'B': 1, 'KB':1024, 'MB': 1024**2, 'GB':1024**3, 'TB':1024**4}
        self.matchFileSize = re.compile("<small.*>(\d+,?\d*)\s*(\w+)</small>", re.DOTALL)
        self.matchFileExt = re.compile("[\w\-_]+\.(\w+)")
        self.basename = "uploaded.to"
        self.streamSize = 0
        self.url = url
        
    def __del__(self):
        del self.url
        del self.unidades
        del self.streamSize
        del self.matchFileSize

    def get_size(self, proxies=None):
        return self.streamSize

    def get_file_size(self, data):
        search = self.matchFileSize.search(data)
        size, unit = search.group(1), search.group(2)
        # convers�o da unidade para bytes
        bytes_size = float(size.replace(",",".")) * self.unidades[ unit.upper() ]
        return int( bytes_size )

    def start_extraction(self, proxies={}, timeout=25):
        """ extrai as informa��es necess�rias, para a transfer�cia do arquivo de video """
        url_id = Universal.get_video_id(self.basename, self.url)

        webPage = self.connect(self.url, proxies=proxies, timeout=timeout).read()

        # tamanho aproximado do arquivo
        self.streamSize = self.get_file_size( webPage )

        # nome do arquivo
        try: title = re.search("<title>(.*)</title>", webPage).group(1)
        except: title = sites.get_random_text()

        # extens�o do arquivo
        try: ext = self.matchFileExt.search(title).group(1)
        except: ext = "file"

        ## {type:'download',url:'http://stor1074.uploaded.to/dl/46d975ec-a24e-4e88-a4c9-4000ce5bd1aa'}
        data = self.connect(self.captchaUrl%url_id, proxies=proxies, timeout=timeout).read()
        url = re.search("url:\s*(?:'|\")(.*)(?:'|\")", data).group(1)
        self.configs = {"url": url, "ext": ext, "title": title}