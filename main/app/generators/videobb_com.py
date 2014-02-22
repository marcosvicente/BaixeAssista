# coding: utf-8
import base64
import json
import re

from ._sitebase import SiteBase
from main.app import decrypter
from main.app.generators import Universal
from main.app.manager.urls import UrlManager


class Videobb(SiteBase):
    ##
    # http://www.videobb.com/video/XuS6EAfMb7nf
    # http://www.videobb.com/watch_video.php?v=XuS6EAfMb7nf
    ##
    controller = {
        "url": "http://www.videobb.com/video/%s",
        "patterns": re.compile(
            "(?P<inner_url>(?:http://)?(?:www\.)?videobb\.com/(?:video/|watch_video\.php\?v=)(?P<id>\w+))"),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.settings_url = "http://www.videobb.com/player_control/settings.php?v=%s"
        self.basename = UrlManager.getBaseName(url)
        self.env = ["settings", "config"]
        self.res = ["settings", "res"]
        self.key2 = 226593
        self.cfg = {}
        self.url = url

    def random_mode(self):
        return True

    def isToken(self, key):
        """ retorna True se key=token """
        return key[0:5] == 'token' and key != 'token2' and key != 'token3'

    def get_sece2(self, params):
        return params["settings"]["video_details"]["sece2"]

    def get_title(self, params):
        return params["settings"]["video_details"]["video"]["title"]

    def get_gads(self, params):
        return params["settings"]["banner"]["g_ads"]

    def get_rkts(self, params):
        return params["settings"]["config"]["rkts"]

    def get_spn(self, params):
        return params["settings"]["login_status"]["spn"]

    def get_urls(self, params):
        urls = {}
        config = params[self.env[0]][self.env[1]]
        for tokenname in filter(self.isToken, list(config.keys())):
            url = base64.b64decode(config[tokenname])

            if url.startswith("http"):
                url = self.getNewUrl(url, params)
                urls[tokenname] = url + "start="
        return urls

    def get_res_urls(self, params):
        urls = {}
        _res = params[self.res[0]].get(self.res[1], [])
        for index, res in enumerate(_res):
            url = base64.b64decode(res["u"])

            seekname = res.get("seekname", "start") + "="
            t_param = res.get("t", "")
            r_param = res.get("r", "")

            url = self.getNewUrl(url, params)

            if t_param: url = re.sub("t=[^&]+", "t=%s" % t_param, url)
            if r_param: url = re.sub("r=[^&]+", "r=%s" % r_param, url)

            urls[index + 1] = url + seekname
        return urls

    def getNewUrl(self, url, params):
        """ Faz a convers�o da url antiga e inv�lida, para a mais nova. """
        new_url = url.replace(":80", "")

        g_ads = self.get_gads(params)
        sece2 = self.get_sece2(params)
        spn = self.get_spn(params)
        rkts = self.get_rkts(params)

        # faz a decriptografia do link
        parse = decrypter.parse(
            g_ads_url=g_ads["url"],
            g_ads_type=g_ads["type"],
            g_ads_time=g_ads["time"],
            key2=self.key2, rkts=rkts,
            sece2=sece2,
            spn=spn
        )
        return "&".join([new_url, parse])

    def get_link(self):
        video_quality = int(self.params.get("quality", 2))
        when_not_found = self.configs.get("token1", None)
        when_not_found = self.configs.get(1, when_not_found)
        when_not_found = self.configs.get(2, when_not_found)
        when_not_found = self.configs.get(3, when_not_found)
        return self.configs.get(video_quality, when_not_found)

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        url = self.settings_url % video_id

        fd = self.connect(url, proxies=proxies, timeout=timeout)
        data = fd.read()
        fd.close()

        params = json.loads(data)

        try:
            urls = self.get_urls(params)
            self.configs["token1"] = urls["token1"]
        except:
            pass

        self.configs.update(self.get_res_urls(params))

        self.configs["title"] = self.get_title(params)
        self.configs["ext"] = "flv"