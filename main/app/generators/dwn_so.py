# coding: utf-8
from ._sitebase import *

########################################################################
class DwShare(SiteBase):
    ## http://dwn.so/player/embed.php?v=DSFAE06F1C&width=505&height=400
    ## http://dwn.so/xml/videolink.php?v=DSFAE06F1C&yk=c0352ffc881e858669b7c0f08d16f3edf47bfdea&width=1920&id=1342495730819&u=undefined
    ## http://st.dwn.so/xml/videolink.php?v=DS4DDC9CDF&yk=3a31f85d3547ecddaa35d6b3329c11cfc69ff156&width=485&id=1344188495210&u=undefined    
    ## un link = http://s1023.dwn.so/movie-stream,63e9266ab2e5baa4874fa8948ec7e3b8,5004e0ab,DSFAE06F1C.flv,0
    ## <?xml version="1.0" encoding="utf-8"?>
    ## <rows><row url="" runtime="0"  downloadurl="http://dwn.so/show-file/0c8fa9b8c2/114367/_Pie_8.O.Reencontro.Dub.cinefilmesonline.net.avi.html" runtimehms="89:17" size="1024" waitingtime="5000" k="" k1="76752" k2="75398" un="s1023.dwn.so/movie-stream,63e9266ab2e5baa4874fa8948ec7e3b8,5004e0ab,DSFAE06F1C.flv,0" s="" title="American Pie 8.O.Reencontro.Dub.cinefilmesonline.net.avi" description="Description" added="2011-05-30" views="-" comments="0" favorited="0" category="" tags="tags" rating="0" embed="%3Ciframe+src%3D%22http%3A%2F%2Fdwn.so%2Fplayer%2Fembed.php%3Fv%3DDSFAE06F1C%26width%3D500%26height%3D350%22+width%3D%22500%22+height%3D%22350%22+frameborder%3D%220%22+scrolling%3D%22no%22%3E%3C%2Fiframe%3E" private="1" mobilepay="0" icc="PL" mpaylang="en" limit1="You+have+watched+%5BN1%5D+minutes+of+video+today." limit2="Please+wait+%5BN2%5D+minutes+or+click+here+to+register+and+enjoy+unlimited+videos+FOR+FREE" limit3="purchase+premium+membership+with+Paypal+or+Moneybookers" limit4="or+purchase+it+using+your+mobile+phone" mobilepaylatin="1"></row>
    ## </rows>
    controller = {
        "url": "http://dwn.so/player/embed.php?v=%s",
        "patterns": [re.compile(
            "(?P<inner_url>http://dwn\.so/player/embed\.php\?v=(?P<id>\w+)(?:&width=\d+)?(?:&height=\d+)?)")],
        "control": "SM_SEEK",
        "video_control": None
    }
    videolink = ("http://st.dwn.so/xml/videolink.php?v=%s", "http://dwn.so/xml/videolink.php?v=%s")
    #----------------------------------------------------------------------
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "dwn.so"
        self.url = url

    def suportaSeekBar(self):
        return True

    def start_extraction(self, proxies={}, timeout=25):
        video_id = Universal.get_video_id(self.basename, self.url)
        for videlink in self.videolink:
            try:
                fd = self.connect(videlink % video_id, proxies=proxies, timeout=timeout)
                xmlData = fd.read();
                fd.close();
                break
            except:
                continue
        else:
            raise IOError

        url = re.search("""un=(?:'|")(.*?)(?:'|")""", xmlData, re.DOTALL).group(1)
        if not url.startswith("http://"): url = "http://" + url
        if url[-2:] == ",0": url = url[:-1]

        try:
            title = re.search("""title\s*=\s*(?:'|")(.*?)(?:'|")""", xmlData, re.DOTALL).group(1)
        except:
            title = sites.get_random_text()

        self.configs = {"url": url, "title": title}
        
        