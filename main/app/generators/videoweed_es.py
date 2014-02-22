# coding: utf-8
import re
import urllib.parse

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.manager.urls import UrlManager
from main.app.util import sites


class Videoweed(SiteBase):
    ##
    # http://www.videoweed.es/file/sackddsywnmyt
    # http://embed.videoweed.es/embed.php?v=sackddsywnmyt
    ##
    controller = {
        "url": "http://www.videoweed.es/file/%s",
        "basenames": ["embed.videoweed", "videoweed.es"],
        "patterns": (
            re.compile("(?P<inner_url>(?:http://)?www\.videoweed\.es/file/(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?embed\.videoweed\.es/embed\.php\?v=(?P<id>\w+))")]
        ),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.player_api = "http://www.videoweed.es/api/player.api.php?key=%s&user=undefined&codes=undefined&pass=undefined&file=%s"
        self.video_url = "http://www.videoweed.es/file/%s"
        self.basename = UrlManager.getBaseName(url)
        self.url = url

    def suportaSeekBar(self):
        return True

    @staticmethod
    def get_site_message(web_page):
        try:
            matchobj = re.search("<center>(?P<message>.+?)(?:</div>|</center>)", web_page, re.DOTALL)
            message = matchobj.group("message")
            message = message.decode("utf-8", "ignore")
            message = re.sub("^[\s\t\n]+|[\n\s\t]+$", "", message)
        except:
            message = ''
        return message

    def getLink(self):
        video_quality = int(self.params.get("quality", 2))
        when_not_found = self.configs.get(1, None)
        when_not_found = self.configs.get(2, when_not_found)
        when_not_found = self.configs.get(3, when_not_found)
        return self.configs.get(video_quality, when_not_found)

    def start_extraction(self, proxies={}, timeout=25):
        url_id = Universal.get_video_id(self.basename, self.url)
        url = self.video_url % url_id

        fd = self.connect(url, proxies=proxies, timeout=timeout)
        web_page = fd.read()
        fd.close()

        # message gerada caso o video tenha sido removido
        self.message = self.get_site_message(web_page)
        ##
        # flashvars.filekey="189.24.243.113-505db61fc331db7a2a7fa91afb22e74d-"
        ##
        matchobj = re.search('flashvars\.filekey="(.+?)"', web_page)
        file_key = matchobj.group(1)

        url = self.player_api % (file_key, url_id)  # ip; id
        fd = self.connect(url, proxies=proxies, timeout=timeout)
        info_data = fd.read()
        fd.close()

        params = dict(re.findall("(\w+)=(.*?)&", info_data))

        url = urllib.parse.unquote_plus(params["url"])
        seek_parm = urllib.parse.unquote_plus(params["seekparm"])

        if not seek_parm:
            seek_parm = "?start="
        elif seek_parm.rfind("=") < 0:
            seek_parm += "="

        try:
            title = urllib.parse.unquote_plus(params["title"])
        except:
            title = sites.get_random_text()

        self.configs = {1: url + seek_parm, "title": title}