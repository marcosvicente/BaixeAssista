# coding: utf-8
import re
import urllib

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.util import sites


class Modovideo(SiteBase):
    ##
    # http://www.modovideo.com/video.php?v=08k9h2hm0mq3zjvs69850dyjpdgzghfg
    # http://www.modovideo.com/video?v=t15yzbsacm6z10vs0wh0v9hc1cprba76
    # http://www.modovideo.com/frame.php?v=4mcyh0h5y2gc27g2dgsc7g80j6tpw4c0
    ##
    controller = {
        "url": "http://www.modovideo.com/video.php?v=%s",
        "patterns": (
            re.compile("(?P<inner_url>(?:http://)?(?:www\.)?modovideo\.com/(?:video\?|video\.php\?)v=(?P<id>\w+))"),
            [re.compile("(?P<inner_url>(?:http://)?(?:www\.)?modovideo\.com/frame\.php\?v=(?P<id>\w+))")]
        ),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "modovideo.com"
        self.url = url

    def suportaSeekBar(self):
        return True

    def getLink(self):
        video_quality = int(self.params.get("quality", 2))
        when_not_found = self.configs.get(1, None)
        when_not_found = self.configs.get(2, when_not_found)
        when_not_found = self.configs.get(3, when_not_found)
        return self.configs.get(video_quality, when_not_found)

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        url = 'http://www.modovideo.com/video.php?v=%s' % video_id

        fd = self.connect(url, proxies=proxies, timeout=timeout)
        web_page = fd.read()
        fd.close()

        try:
            self.configs["title"] = re.search("<title.*>(.+?)</title>", web_page).group(1)
        except:
            try:
                self.configs["title"] = re.search("<meta name=\"title\" content=\"(.+?)\"\s*/>", web_page).group(1)
            except:
                self.configs["title"] = sites.get_random_text()  # usa um titulo gerado de caracteres aleat�rios

        player_url = "http://www.modovideo.com/frame.php?v=%s" % video_id
        fd = self.connect(player_url, proxies=proxies, timeout=timeout)
        script = fd.read()
        fd.close()

        matchobj = re.search("\.setup\(\{\s*flashplayer:\s*\"(.+)\"", script, re.DOTALL | re.IGNORECASE)
        qs_dict = urllib.parser.parse_qs(matchobj.group(1))
        video_url = qs_dict["player5plugin.video"][0]

        # guarda a url para atualizar nas configs
        self.configs[1] = video_url + "?start="
