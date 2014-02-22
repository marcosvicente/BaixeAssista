# coding: utf-8
import re
from urllib.parse import urlencode

from main.app.generators._sitebase import SiteBase
from main.app.util import sites


class PutLocker(SiteBase):
    ## http://www.putlocker.com/file/3E3190548EE7A2BD
    controller = {
        "url": "http://www.putlocker.com/file/%s",
        "patterns": (
            re.compile("(?P<inner_url>(?:http://)?www\.putlocker\.com/file/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?www\.putlocker\.com/embed/(?P<id>\w+))")]
        ),
        "control": "SM_RANGE",
        "video_control": None
    }
    patternForm = re.compile(
        '<form method="post">.*?<input.+?(?:value="(?P<hash>\w+)|name="(?P<name>\w+)")'
        '.*?(?:value="(?P<_hash>\w+)|name="(?P<_name>\w+)").*?<input.*value="(?P<confirm>[\w\s]+)"',
        re.DOTALL | re.IGNORECASE
    )

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.getFileBaseUrl = "http://www.putlocker.com"
        self.basename = "putlocker.com"
        self.url = url

    def suportaSeekBar(self):
        return True

    def get_site_message(self, webpage):
        try:
            try:
                msg = re.search("<div class='message t_\d+'>(?P<msg>.+?)</div>", webpage).group("msg")
            except:
                msg = re.search("<div class='error_message'>(?P<msg>.+?)</div>", webpage).group("msg")
            msg = "%s informa: %s" % (self.basename, msg.decode("utf-8", "ignore"))
        except:
            msg = ""
        return msg

    @staticmethod
    def unescape(s):
        s = s.replace("&lt;", "<")
        s = s.replace("&gt;", ">")
        # this has to be last:
        s = s.replace("&amp;", "&")
        return s

    def start_extraction(self, proxies={}, timeout=25):
        # página web inicial
        url = self.url.replace("/embed", "/file")
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        webpage = fd.read()
        fd.close()

        # messagem de erro. se houver alguma
        self.message = self.get_site_message(webpage)

        # padrão captua de dados
        matchobj = self.patternForm.search(webpage)
        hashvalue = matchobj.group("hash") or matchobj.group("_hash")
        hashname = matchobj.group("name") or matchobj.group("_name")
        confirmvalue = matchobj.group("confirm")

        data = urlencode({hashname: hashvalue, "confirm": confirmvalue})
        fd = self.connect(url, proxies=proxies, timeout=timeout, data=data)
        webpage = fd.read()
        fd.close()

        self.message = self.get_site_message(webpage)

        # extraindo o titulo.
        try:
            title = re.search("<title>(.*?)</title>", webpage).group(1)
        except:
            title = sites.get_random_text()

        # começa a extração do link vídeo.
        ## playlist: '/get_file.php?stream=WyJORVE0TkRjek5FUkdPRFJETkRKR05Eb3',
        pattern = "playlist:\s*(?:'|\")(/get_file\.php\?stream=.+?)(?:'|\")"
        matchobj = re.search(pattern, webpage, re.DOTALL | re.IGNORECASE)
        url = self.getFileBaseUrl + matchobj.group(1)

        # começa a análize do xml
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        rssData = fd.read()
        fd.close()

        ext = "flv"  # extensão padrão.
        ## print rssData

        # url do video.
        url = re.search("<media:content url=\"(.+?)\"", rssData).group(1)
        url = self.unescape(url).replace("'", "").replace('"', "")

        try:
            ext = re.search("type=\"video/([\w-]+)", rssData).group(1)
        except:
            pass  # usa a extensão padrão.

        self.configs = {"url": url, "title": title, "ext": ext}  #+"&start="