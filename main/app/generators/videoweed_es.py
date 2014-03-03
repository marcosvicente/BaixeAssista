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

    def random_mode(self):
        return True

    @staticmethod
    def get_message_(page):
        try:
            match_obj = re.search("<center>(?P<message>.+?)(?:</div>|</center>)", page, re.DOTALL)
            message = match_obj.group("message")
            message = message.decode("utf-8", "ignore")
            message = re.sub("^[\s\t\n]+|[\n\s\t]+$", "", message)
        except:
            message = ''
        return message

    def get_link(self):
        video_quality = int(self.params.get("quality", 2))

        when_not_found = self.configs.get(1, None)
        when_not_found = self.configs.get(2, when_not_found)
        when_not_found = self.configs.get(3, when_not_found)

        return self.configs.get(video_quality, when_not_found)

    def start_extraction(self, proxies={}, timeout=25):
        url_id = Universal.get_video_id(self.basename, self.url)
        request = self.connect(self.video_url % url_id, proxies=proxies, timeout=timeout)
        page = request.text
        request.close()

        # message gerada caso o video tenha sido removido
        self.message = self.get_message_(page)

        ##
        # flashvars.filekey="189.24.243.113-505db61fc331db7a2a7fa91afb22e74d-"
        ##
        match_obj = re.search('flashvars\.filekey="(.+?)"', page)
        file_key = match_obj.group(1)

        url = self.player_api % (file_key, url_id)  # ip; id
        request = self.connect(url, proxies=proxies, timeout=timeout)
        params = dict(re.findall("(\w+)=(.*?)&", request.text))
        request.close()

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

        self.configs = {
            1: url + seek_parm,
            "title": title
        }