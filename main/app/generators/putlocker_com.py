# coding: utf-8
import re
from urllib.parse import urlencode

from ._sitebase import SiteBase
from main.app.util import sites


class PutLocker(SiteBase):
    ##
    # http://www.putlocker.com/file/3E3190548EE7A2BD
    ##
    controller = {
        "url": "http://www.putlocker.com/file/%s",
        "patterns": (
            re.compile("(?P<inner_url>(?:http://)?www\.putlocker\.com/file/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?www\.putlocker\.com/embed/(?P<id>\w+))")]
        ),
        "control": "SM_RANGE",
        "video_control": None
    }
    pattern_form = re.compile(
        '<form method="post">.*?<input.+?(?:value="(?P<hash>\w+)|name="(?P<name>\w+)")'
        '.*?(?:value="(?P<hash_second>\w+)|name="(?P<name_second>\w+)").*?<input.*value="(?P<confirm>[\w\s]+)"',
        re.DOTALL | re.IGNORECASE
    )

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.getFileBaseUrl = "http://www.putlocker.com"
        self.basename = "putlocker.com"
        self.url = url

    def random_mode(self):
        return True

    def get_site_message(self, web_page):
        try:
            try:
                msg = re.search("<div class='message t_\d+'>(?P<msg>.+?)</div>", web_page).group("msg")
            except:
                msg = re.search("<div class='error_message'>(?P<msg>.+?)</div>", web_page).group("msg")
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
        web_page = fd.read()
        fd.close()

        # messagem de erro. se houver alguma
        self.message = self.get_site_message(web_page)

        # padrão captua de dados
        match_obj = self.pattern_form.search(web_page)

        hash_value = match_obj.group("hash") or match_obj.group("hash_second")
        hash_name = match_obj.group("name") or match_obj.group("name_second")
        confirm = match_obj.group("confirm")

        data = urlencode({hash_name: hash_value, "confirm": confirm})
        fd = self.connect(url, proxies=proxies, timeout=timeout, data=data)
        web_page = fd.read()
        fd.close()

        self.message = self.get_site_message(web_page)

        # extraindo o titulo.
        try:
            title = re.search("<title>(.*?)</title>", web_page).group(1)
        except:
            title = sites.get_random_text()

        # começa a extração do link vídeo.
        ## playlist: '/get_file.php?stream=WyJORVE0TkRjek5FUkdPRFJETkRKR05Eb3',
        pattern = "playlist:\s*(?:'|\")(/get_file\.php\?stream=.+?)(?:'|\")"
        match_obj = re.search(pattern, web_page, re.DOTALL | re.IGNORECASE)
        url = self.getFileBaseUrl + match_obj.group(1)

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