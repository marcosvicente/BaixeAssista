# coding: utf-8
import urllib.parse
import re

from ._sitebase import SiteBase
from main.app.generators import Universal
from main.app.manager.urls import UrlManager
from main.app.util import sites


class Mixturecloud(SiteBase):
    ##
    # http://www.mixturecloud.com/video=iM1zoh
    # http://www.mixturecloud.com/download=MB8JBD
    # http://www.mixturecloud.com/media/anSK2C
    # http://player.mixturecloud.com/embed=Sc0oym
    # http://player.mixturecloud.com/video/zQfFrx.swf
    # http://video.mixturecloud.com/video=jlkjljk
    # http://www.mixturevideo.com/video=xFRjoQ
    ##
    controller = {
        "url": "http://www.mixturecloud.com/video=%s",
        "basenames": ["video.mixturecloud", "mixturecloud.com", "player.mixturecloud", "mixturevideo.com"],
        "patterns": (
            re.compile("(?P<inner_url>(?:http://)?www\.mixturecloud\.com/(?:video=|download=|media/)(?P<id>\w+))"),
            re.compile("(?P<inner_url>(?:http://)?video\.mixturecloud\.com/video=(?P<id>\w+))"), [
                re.compile(
                    "(?P<inner_url>(?:http://)?player\.mixturecloud\.com/(?:embed=|video/)(?P<id>\w+)(?:\.swf)?)"),
                re.compile("(?P<inner_url>(?:http://)?www.mixturevideo.com/video=(?P<id>\w+))")
            ],
        ),
        "control": "SM_SEEK",
        "video_control": None
    }

    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        # parte principal da url usada como elemento chave no programa
        self.basename = UrlManager.getBaseName(url)
        self.url = url

    @staticmethod
    def get_post_data(page=''):
        """ Extrai informações da página de login para o post """
        login_data = {
            "email": "creachut@temporarioemail.com.br",
            "password": "creachut@temporarioemail.com.br",
            "submit_form_login": 1,
            "submit_key": ''
        }
        regex_str = ['name="submit_form_login" value="(\w+?)".*?',
                     'name="submit_key" value="(\w*?)"']
        matchobj = re.search("".join(regex_str), page, re.DOTALL)

        if matchobj:
            login_data["submit_form_login"] = matchobj.group(1)
            login_data["submit_key"] = matchobj.group(2)

        return urllib.parse.urlencode(login_data)

    def login(self, url, **kwargs):
        """ login system """
        try:
            timeout = kwargs.get('timeout', 30)
            proxies = kwargs.get('proxies', {})

            url = "http://www.mixturecloud.com/login"
            response = self.session.get(url, proxies=proxies, timeout=timeout)
            data = self.get_post_data(response.text)
            response.close()

            response = self.session.get(url, data=data, proxies=proxies, timeout=timeout)
            response.close()
            success = True
        except:
            success = False
        return success

    def random_mode(self):
        return True

    def get_link(self):
        video_quality = int(self.params.get("quality", 2))

        when_not_found = self.configs.get(1, None)
        when_not_found = self.configs.get(2, when_not_found)
        when_not_found = self.configs.get(3, when_not_found)

        return self.configs.get(video_quality, when_not_found)

    def get_message_(self, web_page):
        matchobj = re.search('<div class="alert i_alert red".*?>(?P<msg>.+?)</div>', web_page)
        try:
            msg = "%s informa: %s" % (self.basename, str(matchobj.group("msg"), "UTF-8"))
        except:
            msg = ""
        return msg

    @staticmethod
    def get_video_params(page):
        params = {}
        try:
            match_obj = re.search("<title.*>(.+?)</title>", page)
            params["title"] = match_obj.group(1)
        except:
            # usa um titulo gerado de caracteres aleatórios
            params["title"] = sites.get_random_text()

        try:  # ** URL NORMAL **
            match_obj = re.search("flashvars.+(?:'|\")file(?:'|\")\s*:\s*(?:'|\")(.+?\.flv.*?)(?:'|\")", page,
                                 re.DOTALL | re.IGNORECASE)
            flv_code = match_obj.group(1)

            #'streamer':'http://www441.mixturecloud.com/streaming.php?key_stream=a31dff5ee1528ded3df4841b6364f9b5'
            match_obj = re.search("flashvars.+(?:'|\")streamer(?:'|\")\s*:\s*(?:'|\")(.+?)(?:'|\")", page,
                                 re.DOTALL | re.IGNORECASE)
            streamer = match_obj.group(1)

            # guarda a url para atualizar nas configs
            params[1] = "%s&file=%s&start=" % (streamer, flv_code)
        except:
            pass

        try:  # ** URL HD **
            match_obj = re.search("property=\"og:video\"\s*content=\".+hd\.file=(.+?\.flv)", page,
                                  re.DOTALL | re.IGNORECASE)
            if match_obj:
                flv_code_hd = match_obj.group(1)
            else:
                match_obj = re.search("flashvars.+(?:'|\")hd\.file(?:'|\")\s*:\s*(?:'|\")(.*?\.flv)(?:'|\")", page,
                                      re.DOTALL | re.IGNORECASE)
                flv_code_hd = match_obj.group(1)

            match_obj = re.search("property=\"og:video\"\s*content=\".+streamer=(.+?)\"", page,
                                  re.DOTALL | re.IGNORECASE)
            if match_obj:
                streamer_hd = match_obj.group(1)
                params[2] = "%s&file=%s&start=" % (streamer_hd, flv_code_hd)
            else:
                params[2] = "%s&file=%s&start=" % (streamer, flv_code_hd)
        except:
            pass
        return params

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        url = "http://video.mixturecloud.com/video=%s" % video_id

        request = self.connect(url, proxies=proxies, timeout=timeout, login=True)
        page = request.text
        request.close()

        self.message = self.get_message_(page)
        self.configs.update(self.get_video_params(page))