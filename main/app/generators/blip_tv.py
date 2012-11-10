from _sitebase import *

####################################### BLIPTV ########################################
class BlipTV( SiteBase ):
    """Information extractor for blip.tv"""
    ## http://blip.tv/thechrisgethardshow/tcgs-45-we-got-nothing-6140017
    controller = {
        "url": "http://blip.tv/%s", 
        "patterns": re.compile("(?P<inner_url>(?:http://)?blip\.tv/(?P<id>.+-\d+))"), 
        "control": "SM_RANGE", 
        "video_control": None
    }
    URL_EXT = r'^.*\.([a-z0-9]+)$'
    
    def __init__(self, url, **params):
        SiteBase.__init__(self, **params)
        self.basename = "blip.tv"
        self.url = url

    def start_extraction(self, proxies={}, timeout=25):
        if '?' in self.url: cchar = '&'
        else: cchar = '?'

        info = None
        try:
            ## http://blip.tv/rv-news-net/episode-6099740?skin=json&version=2&no_wrap=1
            json_url = self.url + cchar + "skin=json&version=2&no_wrap=1"
            urlh = self.connect(json_url, proxies=proxies, timeout=timeout)
        except: return # falha obtendo a págian

        if urlh.headers.get("Content-Type", "").startswith("video/"): # Direct download
            basename = self.url.split("/")[-1]
            title,ext = os.path.splitext(basename)
            title = title.decode("UTF-8")
            ext = ext.replace(".", "")

            info = {'id': title, 'url': urlh, 'title': title, 'ext': ext}

        if info is None: # Regular URL
            try: json_code = urlh.read()
            except: return # erro lendo os dados

            json_data = json.loads(json_code)
            if 'Post' in json_data:
                data = json_data['Post']
            else:
                data = json_data

            ## http://blip.tv/file/get/RVNN-TAPP1163433.m4v?showplayer=20120417163409
            video_url = data['media']['url'] + "?showplayer=20120417163409"

            try:
                umobj = re.match(self.URL_EXT, video_url)
                ext = umobj.group(1)
            except:
                ext = "flv"

            info = {
                'id': data['item_id'],
                'url': video_url,
                'uploader': data['display_name'],
                'title': data['title'],
                'ext': ext,
                'format': data['media']['mimeType'],
                'thumbnail': data['thumbnailUrl'],
                'description': data['description'],
                'player_url': data['embedUrl']
            }

        self.configs.update( info )