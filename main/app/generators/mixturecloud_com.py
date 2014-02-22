# coding: utf-8
from ._sitebase import *
from main.app.manager.urls import UrlManager

################################# VIDEO_MIXTURECLOUD ##################################
class Mixturecloud(SiteBase):
    ## http://www.mixturecloud.com/video=iM1zoh
    ## http://www.mixturecloud.com/download=MB8JBD
    ## http://www.mixturecloud.com/media/anSK2C
    ## http://player.mixturecloud.com/embed=Sc0oym
    ## http://player.mixturecloud.com/video/zQfFrx.swf
    ## http://video.mixturecloud.com/video=jlkjljk
    ## http://www.mixturevideo.com/video=xFRjoQ
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

    def getPostData(self, web_page=""):
        """ extrai informa��es da p�gina de login para o post """
        longin_data = {
            "email": "creachut@temporarioemail.com.br",
            "password": "creachut@temporarioemail.com.br",
            "submit_form_login": 1,
            "submit_key": ""}

        regex_str = ['name="submit_form_login" value="(\w+?)".*?',
                     'name="submit_key" value="(\w*?)"']
        matchobj = re.search("".join(regex_str), web_page, re.DOTALL)

        if matchobj:
            longin_data["submit_form_login"] = matchobj.group(1)
            longin_data["submit_key"] = matchobj.group(2)

        return urllib.parse.urlencode(longin_data)

    def login(self, opener, timeout):
        """ faz o login necess�rio para transferir o arquivo de v�deo. opener � quem armazer� o cookie """
        try:
            url = "http://www.mixturecloud.com/login"
            response = opener.open(url, timeout=timeout)
            loginPage = response.read()
            response.close()

            # dados do m�todo post
            post_data = self.getPostData(loginPage)

            # logando
            response = opener.open(url, data=post_data, timeout=timeout)
            response.close()
            sucess = True
        except Exception as err:
            sucess = False
        return sucess

    def suportaSeekBar(self):
        return True

    def getLink(self):
        vquality = int(self.params.get("quality", 2))
        optToNotFound = self.configs.get(1, None)
        optToNotFound = self.configs.get(2, optToNotFound)
        optToNotFound = self.configs.get(3, optToNotFound)
        return self.configs.get(vquality, optToNotFound)

    def getMessage(self, web_page):
        matchobj = re.search('<div class="alert i_alert red".*?>(?P<msg>.+?)</div>', web_page)
        try:
            msg = "%s informa: %s" % (self.basename, str(matchobj.group("msg"), "UTF-8"))
        except:
            msg = ""
        return msg

    def get_configs(self, web_page):
        info = {}
        try:
            matchobj = re.search("<title.*>(.+?)</title>", web_page)
            info["title"] = matchobj.group(1)
        except:
            # usa um titulo gerado de caracteres aleat�rios
            info["title"] = sites.get_random_text()

        try:  # ** URL NORMAL **
            matchobj = re.search("flashvars.+(?:'|\")file(?:'|\")\s*:\s*(?:'|\")(.+?\.flv.*?)(?:'|\")", web_page,
                                 re.DOTALL | re.IGNORECASE)
            flv_code = matchobj.group(1)

            #'streamer':'http://www441.mixturecloud.com/streaming.php?key_stream=a31dff5ee1528ded3df4841b6364f9b5'
            matchobj = re.search("flashvars.+(?:'|\")streamer(?:'|\")\s*:\s*(?:'|\")(.+?)(?:'|\")", web_page,
                                 re.DOTALL | re.IGNORECASE)
            streamer = matchobj.group(1)

            # guarda a url para atualizar nas configs
            info[1] = "%s&file=%s&start=" % (streamer, flv_code)
        except:
            pass

        try:  # ** URL HD **
            matchobj = re.search("property=\"og:video\"\s*content=\".+hd\.file=(.+?\.flv)", web_page,
                                 re.DOTALL | re.IGNORECASE)
            if matchobj:
                flv_code_hd = matchobj.group(1)
            else:
                matchobj = re.search("flashvars.+(?:'|\")hd\.file(?:'|\")\s*:\s*(?:'|\")(.*?\.flv)(?:'|\")", web_page,
                                     re.DOTALL | re.IGNORECASE)
                flv_code_hd = matchobj.group(1)

            matchobj = re.search("property=\"og:video\"\s*content=\".+streamer=(.+?)\"", web_page,
                                 re.DOTALL | re.IGNORECASE)

            if matchobj:
                streamer_hd = matchobj.group(1)
                info[2] = "%s&file=%s&start=" % (streamer_hd, flv_code_hd)
            else:
                info[2] = "%s&file=%s&start=" % (streamer, flv_code_hd)
        except:
            pass

        return info

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        url = "http://video.mixturecloud.com/video=%s" % video_id

        fd = self.connect(url, proxies=proxies, timeout=timeout, login=True)
        web_page = fd.read();
        fd.close()

        self.message = self.getMessage(web_page)
        self.configs.update(self.get_configs(web_page))
        
        