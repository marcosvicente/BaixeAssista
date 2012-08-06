# -*- coding: ISO-8859-1 -*-
import os
import re
import sys
import cgi
import time
import json
import random
import string
import urllib
import base64
import locale
import urllib2
import urlparse
import decrypter
import datetime
import cookielib
import HTMLParser
import xml.etree.ElementTree

if __name__ == "__main__":
	os.environ['DJANGO_SETTINGS_MODULE'] = "main.settings"
	curdir = os.path.dirname(os.path.abspath(__file__))
	pardir = os.path.split(curdir)[0]
	maindir = os.path.split(pardir)[0]

	if not maindir in sys.path: sys.path.append(maindir)
	if not pardir in sys.path: sys.path.append(pardir)
	if not curdir in sys.path: sys.path.append(curdir)
	os.chdir( maindir )

import manager
# versão será mantida pelo módulo principal
PROGRAM_VERSION = manager.PROGRAM_VERSION
#######################################################################################

def DECODE(texto, alter="ISO-8859-1"):
	""" Tenta decodificar para utf-8. 
	Em caso de erro, a decodificação alternativa será usada """
	try:
		texto = texto.decode('utf-8')
	except UnicodeDecodeError:
		texto = texto.decode(alter)
	except Exception:
		pass
	return texto

def ENCODE(texto, alter="ISO-8859-1"):
	""" Tenta codificar para utf-8. 
	Em caso de erro, a codficação alternativa será usada """
	try:
		texto = texto.encode('utf-8')
	except UnicodeEncodeError:
		texto = texto.encode( alter)
	except Exception:
		pass
	return texto

def limiteTexto(texto, nCaracter=50, final="..."):
	if len(texto) > nCaracter:
		texto = texto[ :nCaracter] + final
	return texto

def clearTitle( title):
	""" remove todos os carecteres considerados inválidos """
	return re.sub(r"[/*&:|\"\'=\\?<>!%$@#()]+", "_", title)

def get_radom_title(size=25):
	chars = [char for char in string.ascii_letters]
	return "".join([random.choice(chars) for i in range(size)])

def get_with_seek(link, seek):
	if link[-1] == ",": link += str(seek)
	if re.match(".+(?:start=|ec_seek=|fs=)", link): link += str(seek)
	if re.match(".+(?:range=%s-)", link): link %= str(seek)
	return link

########################################################################
class ConnectionProcessor:
	def __init__(self):
		"""Constructor"""
		self.ip_section = {}
		self.loginSucess = False

	def __del__(self):
		del self.ip_section

	def get_section(self, section_name):
		if not self.has_section(section_name):
			self.create_section(section_name)
		return self.ip_section[ section_name ]

	def has_section(self, section_name):
		return self.ip_section.has_key(section_name)

	def create_section(self, section_name):
		self.ip_section[ section_name ] = {}

	def remove_section(self, section_name):
		if self.has_section(section_name):
			del self.ip_section[ section_name ]

	def set_cookiejar(self, section_name, cookieJar):
		section = self.get_section( section_name )
		section["cookieJar"] = cookieJar

	def has_cookieJar(self, section_name):
		section = self.get_section( section_name )
		return section.has_key("cookieJar")

	def get_cookieJar(self, section_name):
		section = self.get_section( section_name )
		return section["cookieJar"]

	def login(self, opener=None, timeout=0):
		""" struct login"""
		return True

	def get_request(self, url, headers, data):
		req = urllib2.Request(url, headers=headers, data=data)
		req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:11.0) Gecko/20100101 Firefox/11.0")
		req.add_header("Connection", "keep-alive")
		return req

	def conecte(self, url="", headers={}, data=None, proxies={}, timeout=25, request=None, login=False):
		""" conecta a url data e retorna o objeto criado """
		ip = proxies.get("http", "default")

		if not self.has_cookieJar(ip):
			self.set_cookiejar(ip, cookielib.CookieJar())

		if request is None:
			request = self.get_request(url, headers, data)

		processor = urllib2.HTTPCookieProcessor(cookiejar= self.get_cookieJar( ip ))
		opener = urllib2.build_opener(processor, urllib2.ProxyHandler(proxies))

		# faz o login se necessário
		if not self.loginSucess or login:
			self.loginSucess = self.login(opener, timeout=timeout)
			if not self.loginSucess: return

		return opener.open(request, timeout=timeout)

#################################### BASEVIDEOSITE ####################################
class SiteBase(ConnectionProcessor):
	#----------------------------------------------------------------------
	def __init__(self, **params):
		ConnectionProcessor.__init__(self)
		self.url = self.basename = self.message = ''
		self.streamHeaderSize = self.streamSize = 0
		self.params = params
		self.configs = {}
		self.headers = {}
		
	def __del__(self):
		del self.basename
		del self.params
		del self.configs
		del self.url

	def __delitem__(self, arg):
		if self.has_section( arg ):
			self.remove_section( arg )

	def get_message(self):
		return self.message

	def suportaSeekBar(self):
		return False

	def get_video_id(self):
		""" retorna só o id do video """
		return Universal.get_video_id(self.basename, self.url)

	def getStreamHeaderSize(self):
		""" número inicial de bytes removidos da stream segmentada """
		return self.streamHeaderSize

	def get_init_page(self, proxies={}, timeout=25):	
		assert self.getVideoInfo(proxies=proxies, timeout=timeout)

	def getVideoInfo(self, ntry=3, proxies={}, timeout=25):
		ip = proxies.get("http","default")
		section = self.get_section( ip )
		settings = section.get("settings",None)

		# extrai o titulo e o link do video, se já não tiverem sido extraidos
		if not settings:
			nfalhas = 0
			while nfalhas < ntry:
				try:
					self.start_extraction(proxies=proxies, timeout=timeout)
					if not self.streamSize: # extrai e guarda o tanho do arquivo
						self.streamSize = self.get_size(proxies=proxies, timeout=timeout)
					if not self.has_link() or not self.has_title() or not self.streamSize:
						self.configs = {}; nfalhas += 1
						continue # falhou em obter o link ou titulo
					else:
						section["settings"] = self.configs # relaciona as configs ao ip
						break # sucesso!
				except: pass
				nfalhas += 1
		else:
			self.configs = section["settings"] # transfere para variável de trabalho

		return self.has_link() and self.has_title() and self.streamSize

	def has_link(self):
		try: return bool(self.getLink())
		except: return False

	def has_title(self):
		try: return bool(self.getTitle())
		except: return False

	def get_file_link(self, data):
		""" retorna o link para download do arquivo de video """
		return self.getLink()

	def get_count(self, data):
		""" herdado e anulado. retorna zero para manter a compatibilidade """
		return 0

	def getLink(self):
		return self.configs["url"]

	def getVideoExt(self):
		return self.configs.get("ext","")

	def getTitle(self):
		""" pega o titulo do video """
		title = urllib.unquote_plus(self.configs["title"])
		title = DECODE(title) # decodifica o title
		# remove caracteres invalidos
		title = clearTitle(title)
		return limiteTexto(title)

	def get_size(self, proxies={}, timeout=60):
		""" retorna o tamanho do arquivo de vídeo, através do cabeçalho de resposta """
		file_size = 0
		link = get_with_seek(self.getLink(), 0)
		
		h = {"Range":"bytes=0-"}; h.update(self.headers)
		req = self.get_request(link, h, data=None)
		
		resp = self.conecte(request = req, proxies=proxies, timeout=timeout)
		file_size = resp.headers.get("Content-Length", None)
		resp.close()
		
		if (resp.code == 200 or resp.code == 206) and not file_size is None:
			return long(file_size)
		assert file_size, "err: get_stream_size"

	def getStreamSize(self):
		""" retorna o tamanho compleot do arquivo de video """
		return self.streamSize

##################################### MEGAUPLOAD ######################################
class Uploaded( SiteBase ):
	## http://uploaded.to/io/ticket/captcha/urxo7anj
	## http://uploaded.to/file/urxo7anj
	controller = {
	    "url": "http://uploaded.to/file/%s", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?uploaded.to/file/(?P<id>\w+))"), 
	    "control": "SM_RANGE", 
	    "video_control": None
	}

	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.captchaUrl = "http://uploaded.to/io/ticket/captcha/%s"
		# unidade usadas para pegar o tamanho aproximado do video(arquivo)
		self.unidades = {'B': 1, 'KB':1024, 'MB': 1024**2, 'GB':1024**3, 'TB':1024**4}
		self.matchFileSize = re.compile("<small.*>(\d+,?\d*)\s*(\w+)</small>", re.DOTALL)
		self.matchFileExt = re.compile("[\w\-_]+\.(\w+)")
		self.basename = "uploaded.to"
		self.streamSize = 0
		self.url = url
		
	def __del__(self):
		del self.url
		del self.unidades
		del self.streamSize
		del self.matchFileSize

	def get_size(self, proxies=None):
		return self.streamSize

	def get_file_size(self, data):
		search = self.matchFileSize.search(data)
		size, unit = search.group(1), search.group(2)
		# conversão da unidade para bytes
		bytes_size = float(size.replace(",",".")) * self.unidades[ unit.upper() ]
		return long( bytes_size )

	def start_extraction(self, proxies={}, timeout=25):
		""" extrai as informações necessárias, para a transferêcia do arquivo de video """
		url_id = Universal.get_video_id(self.basename, self.url)

		webPage = self.conecte(self.url, proxies=proxies, timeout=timeout).read()

		# tamanho aproximado do arquivo
		self.streamSize = self.get_file_size( webPage )

		# nome do arquivo
		try: title = re.search("<title>(.*)</title>", webPage).group(1)
		except: title = get_radom_title()

		# extensão do arquivo
		try: ext = self.matchFileExt.search(title).group(1)
		except: ext = "file"

		## {type:'download',url:'http://stor1074.uploaded.to/dl/46d975ec-a24e-4e88-a4c9-4000ce5bd1aa'}
		data = self.conecte(self.captchaUrl%url_id, proxies=proxies, timeout=timeout).read()
		url = re.search("url:\s*(?:'|\")(.*)(?:'|\")", data).group(1)
		self.configs = {"url": url, "ext": ext, "title": title}

###################################### METACAFE #######################################
class Metacafe( SiteBase ):
	"""Information Extractor for metacafe.com."""
	## http://www.metacafe.com/watch/8492972/wheel_of_fortune_fail/
	controller = {
	    "url": "http://www.metacafe.com/watch/%s/", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?www\.metacafe\.com/watch/(?P<id>\w+)/.*)"), 
	    "control": "SM_RANGE", 
	    "video_control": None
	}

	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "metacafe.com"
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)

		# Check if video comes from YouTube
		mobj2 = re.match(r'^yt-(.*)$', video_id)
		if mobj2 is not None: return

		# Retrieve video webpage to extract further information
		try:
			url = "http://www.metacafe.com/watch/%s/" % video_id
			fd = self.conecte( url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a página

		mobj = re.search(r'(?m)&mediaURL=([^&]+)', webpage)
		if mobj is not None:
			mediaURL = urllib.unquote(mobj.group(1))
			video_extension = mediaURL[-3:]

			# Extract gdaKey if available
			mobj = re.search(r'(?m)&gdaKey=(.*?)&', webpage)
			if mobj is None:
				video_url = mediaURL
			else:
				gdaKey = mobj.group(1)
				video_url = '%s?__gda__=%s' % (mediaURL, gdaKey)
		else:
			mobj = re.search(r' name="flashvars" value="(.*?)"', webpage)
			if mobj is None: return

			vardict = cgi.parse_qs(mobj.group(1))
			if 'mediaData' not in vardict: return

			mobj = re.search(r'"mediaURL":"(http.*?)","key":"(.*?)"', vardict['mediaData'][0])
			if mobj is None: return

			mediaURL = mobj.group(1).replace('\\/', '/')
			video_extension = mediaURL[-3:]
			video_url = '%s?__gda__=%s' % (mediaURL, mobj.group(2))

		try:
			mobj = re.search(r'(?im)<title>(.*) - Video</title>', webpage)
			video_title = mobj.group(1).decode('utf-8')	
		except:
			video_title = get_radom_title()

		try:
			mobj = re.search(r'(?ms)By:\s*<a .*?>(.+?)<', webpage)
			video_uploader = mobj.group(1)
		except:
			video_uploader = ""

		self.configs = {
			'id': video_id.decode('utf-8'),
			'url': video_url.decode('utf-8'),
			'uploader':	video_uploader.decode('utf-8'),
			'upload_date': u'NA',
			'title': video_title,
			'ext': video_extension.decode('utf-8'),
			'format': u'NA',
			'player_url': None,
		}

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
			urlh = self.conecte(json_url, proxies=proxies, timeout=timeout)
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

##################################### DAILYMOTION #####################################
class Dailymotion( SiteBase ):
	"""Information Extractor for Dailymotion"""
	## http://www.dailymotion.com/video/xowm01_justin-bieber-gomez-at-chuck-e-cheese_news#
	controller = {
	    "url": "http://www.dailymotion.com/video/%s", 
	    "patterns": re.compile(r"(?P<inner_url>(?i)(?:https?://)?(?:www\.)?dailymotion(?:\.com)?(?:[a-z]{2,3})?/video/(?P<id>.+))"), 
	    "control": "SM_RANGE", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "dailymotion.com"
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		try:
			video_id = Universal.get_video_id(self.basename, self.url)
			video_extension = 'flv'

			fd = self.conecte(self.url, proxies=proxies, 
						      timeout=timeout, headers={'Cookie': 'family_filter=off'})
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a página

		# Extract URL, uploader and title from webpage
		mobj = re.search(r'addVariable\(\"sequence\"\s*,\s*\"(.+?)\"\)', webpage, re.DOTALL|re.IGNORECASE)

		sequence = urllib.unquote(mobj.group(1))
		mobj = re.search(r',\"sdURL\"\:\"([^\"]+?)\",', sequence)
		mediaURL = urllib.unquote(mobj.group(1)).replace('\\', '')
		# if needed add http://www.dailymotion.com/ if relative URL
		video_url = mediaURL

		try:
			htmlParser = HTMLParser.HTMLParser()
			mobj = re.search(r'<meta property="og:title" content="(?P<title>[^"]*)" />', webpage)
			video_title = htmlParser.unescape(mobj.group('title'))
		except:
			video_title = get_radom_title()

		mobj = re.search(r'(?im)<span class="owner[^\"]+?">[^<]+?<a [^>]+?>([^<]+?)</a></span>', webpage)
		if mobj is None: return

		video_uploader = mobj.group(1)

		self.configs = {
			'id':		video_id.decode('utf-8'),
			'url':		video_url.decode('utf-8'),
			'uploader':	video_uploader.decode('utf-8'),
			'upload_date': u'NA',
			'title':	video_title,
			'ext':		video_extension.decode('utf-8'),
			'format':	u'NA',
			'player_url': None,
		}

##################################### VIDEO.GOOGLE ####################################
class GoogleVideo( SiteBase ):
	"""Information extractor for video.google.com."""
	## http://video.google.com.br/videoplay?docid=-1717800235769991478
	controller = {
	    "url": "http://video.google.com.br/videoplay?docid=%s", 
	    "patterns": re.compile(r'(?P<inner_url>(?:http://)?video\.google\.(?:com(?:\.au)?(?:\.br)?|co\.(?:uk|jp|kr|cr)|ca|de|es|fr||it|nl|pl)/videoplay\?docid=(?P<id>-?[^\&]+).*)'), 
	    "control": "SM_RANGE", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "video.google"
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		# extrai o id da url
		video_id = Universal.get_video_id(self.basename, self.url)
		video_extension = "mp4"

		# Retrieve video webpage to extract further information
		try:
			url = "http://video.google.com/videoplay?docid=%s&hl=en&oe=utf-8" % video_id
			fd = self.conecte(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a página

		# Extract URL, uploader, and title from webpage
		mobj = re.search(r"download_url:'([^']+)'", webpage)
		if mobj is None:
			video_extension = 'flv'
			mobj = re.search(r"(?i)videoUrl\\x3d(.+?)\\x26", webpage)
		if mobj is None: return

		mediaURL = urllib.unquote(mobj.group(1))
		mediaURL = mediaURL.replace('\\x3d', '\x3d')
		mediaURL = mediaURL.replace('\\x26', '\x26')

		video_url = mediaURL

		mobj = re.search(r'<title>(.*)</title>', webpage)
		if mobj is None: return

		video_title = mobj.group(1).decode('utf-8')

		# Extract video description
		mobj = re.search(r'<span id=short-desc-content>([^<]*)</span>', webpage)
		if mobj is None: return

		video_description = mobj.group(1).decode('utf-8')
		if not video_description:
			video_description = 'No description available.'

		self.configs = {
			'id':		video_id.decode('utf-8'),
			'url':		video_url.decode('utf-8'),
			'uploader':	u'NA',
			'upload_date':	u'NA',
			'title':	video_title,
			'ext':		video_extension.decode('utf-8'),
			'format':	u'NA',
			'player_url': None,
		}

##################################### PHOTOBUCKET #####################################
class Photobucket( SiteBase ):
	"""Information extractor for photobucket.com."""
	## http://photobucket.com/videos
	controller = {
	    "url": "http://media.photobucket.com/video/%s", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?media\.photobucket\.com/video/(?P<id>.*))"), 
	    "control": "SM_RANGE", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "media.photobucket"
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		video_extension = 'flv'

		# Retrieve video webpage to extract further information
		try:
			fd = self.conecte(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a página

		# Extract URL, uploader, and title from webpage
		mobj = re.search(r'<link rel="video_src" href=".*\?file=([^"]+)" />', webpage)
		mediaURL = urllib.unquote(mobj.group(1))
		video_url = mediaURL

		try:
			mobj = re.search(r'<meta name="description" content="(.+)"', webpage)
			video_title = mobj.group(1).decode('utf-8')
		except:
			video_title = get_radom_title()

		self.configs = {
			'url': video_url.decode('utf-8'),
			'upload_date': u'NA',
			'title': video_title,
			'ext': video_extension.decode('utf-8'),
			'format': u'NA',
			'player_url': None
		}

####################################### YOUTUBE #######################################
class Youtube( SiteBase ):
	## normal: http://www.youtube.com/watch?v=bWDZ-od-otI
	## embutida: http://www.youtube.com/watch?feature=player_embedded&v=_PMU_jvOS4U
	## http://www.youtube.com/watch?v=VW51Q_YBsNk&feature=player_embedded
	## http://www.youtube.com/v/VW51Q_YBsNk?fs=1&hl=pt_BR&rel=0&color1=0x5d1719&color2=0xcd311b
	## http://www.youtube.com/embed/ulZZ4mG9Ums
	controller = {
	    "url": "http://www.youtube.com/watch?v=%s", 
	    "patterns": (
	         re.compile("(?P<inner_url>(?:http://)?www\.youtube\.com/watch\?.*v=(?P<id>[0-9A-Za-z_-]+))"),
	        [re.compile("(?P<inner_url>(?:http://)?www.youtube(?:-nocookie)?\.com/(?:v/|embed/)(?P<id>[0-9A-Za-z_-]+))")]
	    ), 
	    "control": "SM_SEEK", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		"""Constructor"""
		SiteBase.__init__(self, **params)
		self.info_url = "http://www.youtube.com/get_video_info?video_id=%s&el=embedded&ps=default&eurl=&hl=en_US"
		self.video_quality_opts = {1: "small", 2: "medium", 3: "large"}
		self.basename = u"youtube.com"
		self.url = url
		
	def __str__(self): pass
	def suportaSeekBar(self):
		return True

	def get_urls(self, url_encoded):
		url_data_strs = url_encoded.split(',')
		url_data = [cgi.parse_qs(uds) for uds in url_data_strs]
		return url_data
	
	def getMessage(self, data):
		try:
			if data.get("status",[""])[0] == "fail":
				reason = data.get("reason",[""])[0]
				msg = u"%s informa: %s"%(self.basename, unicode(reason,"UTF-8"))
			else: msg = ""
		except: msg = ""
		return msg
	
	def set_configs(self, video_info):
		""" atualiza a dicionário de configuração """
		url_encoded = video_info["url_encoded_fmt_stream_map"][0]
		self.configs["urls"] = self.get_urls( url_encoded )

		try: # video title
			self.configs["title"] = video_info[ "title" ][0]
		except (KeyError, IndexError):
			self.configs["title"] = get_radom_title()

		try: # video thumbnail
			self.configs["thumbnail_url"] = video_info[ "thumbnail_url" ][0]
		except (KeyError, IndexError):
			self.configs["thumbnail_url"] = ""

	def getLink(self):
		vquality = self.params.get("qualidade", 2)
		quality_opt = self.video_quality_opts[ vquality ]
		defaultUrl = type_short = ""

		for url in self.configs["urls"]:
			type = url["type"][0]
			matchobj = re.search("([^\s;]+)", type)
			if matchobj: type_short = matchobj.group(1)

			# o formato video/webm, mostra-se impatível como o swf player
			if type_short != "video/webm":
				if url['quality'][0] == quality_opt:
					matchObj = re.search("video/([^\s;]+)", type)
					if matchObj: self.configs["ext"] = matchObj.group(1)
					return urllib.unquote_plus(url["url"][0]) + "&range=%s-"

				elif not defaultUrl:
					# se não exisitir a qualidade procurada
					# usa a primeira url encontrada.
					matchObj = re.search("video/([^\s;]+)", type)
					if matchObj: self.configs["ext"] = matchObj.group(1)
					defaultUrl = urllib.unquote_plus(url["url"][0]) + "&range=%s-"

		else: # na falta da url com a qualidade procurada, usa a padrão
			return defaultUrl 

	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		
		url = self.info_url % video_id
		fd = self.conecte(url, proxies=proxies, timeout=timeout)
		data = fd.read(); fd.close()
		
		data = cgi.parse_qs( data )
		self.message = self.getMessage(data)
		# atualiza o dicionário de parâmetros
		self.set_configs( data )
		
######################################## VIMEO ########################################
class Vimeo( SiteBase ):
	"""Information extractor for vimeo.com."""
	## http://vimeo.com/40620829
	## http://vimeo.com/channels/news/40620829
	## http://vimeo.com/channels/hd/40716035
	controller = {
	    "url": "http://vimeo.com/%s", 
	    "patterns": re.compile(r'(?P<inner_url>(?:https?://)?(?:(?:www|player).)?vimeo\.com/(?:groups/[^/]+/|channels?/(?:news/|hd/))?(?:videos?/)?(?P<id>[0-9]+))'), 
	    "control": "SM_RANGE", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = u"vimeo.com"
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		try:
			# extrai o id do video
			video_id = Universal.get_video_id(self.basename, self.url)
			url = "http://vimeo.com/moogaloop/load/clip:%s" % video_id

			fd = self.conecte(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a página

		try:# Extract title
			mobj = re.search(r'<caption>(.*?)</caption>', webpage)
			video_title = mobj.group(1).decode('utf-8')
		except:
			video_title = get_radom_title()

		try:# Extract uploader
			mobj = re.search(r'<uploader_url>http://vimeo.com/(.*?)</uploader_url>', webpage)
			video_uploader = mobj.group(1).decode('utf-8')
		except:
			video_uploader = ""

		try:# Extract video thumbnail
			mobj = re.search(r'<thumbnail>(.*?)</thumbnail>', webpage)
			video_thumbnail = mobj.group(1).decode('utf-8')
		except:
			video_thumbnail = ""

		video_description = 'Foo.'

		# Vimeo specific: extract request signature
		mobj = re.search(r'<request_signature>(.*?)</request_signature>', webpage)
		sig = mobj.group(1).decode('utf-8')

		# Vimeo specific: extract video quality information
		mobj = re.search(r'<isHD>(\d+)</isHD>', webpage)
		quality = mobj.group(1).decode('utf-8')

		if int(quality) == 1: quality = 'hd'
		else: quality = 'sd'

		# Vimeo specific: Extract request signature expiration
		mobj = re.search(r'<request_signature_expires>(.*?)</request_signature_expires>', webpage)
		sig_exp = mobj.group(1).decode('utf-8')

		## http://player.vimeo.com/play_redirect?clip_id=36031564&sig=10e1f89cb26ab0221c84fbc35b2051ec&time=1335225117&quality=hd&codecs=H264,VP8,VP6&type=moogaloop_local&embed_location=
		## video_url = "http://vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=%s" % (video_id, sig, sig_exp, quality)
		video_url = "http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s" % (video_id, sig, sig_exp, quality)

		self.configs = {
			'id':		video_id.decode('utf-8'),
			'url':		video_url,
			'uploader':	video_uploader,
			'upload_date':	u'NA',
			'title':	video_title,
			'ext':		u'mp4',
			'thumbnail':	video_thumbnail.decode('utf-8'),
			'description':	video_description,
			'thumbnail':	video_thumbnail,
			'description':	video_description,
			'player_url':	None,
		}

####################################### MYVIDEO #######################################
class MyVideo( SiteBase ):
	"""Information Extractor for myvideo.de."""
	## http://www.myvideo.de/watch/8532190/D_Gray_man_Folge_2_Der_Schwarze_Orden
	controller = {
	    "url": "http://www.myvideo.de/watch/%s", 
	    "patterns": re.compile(r'(?P<inner_url>(?:http://)?(?:www\.)?myvideo\.de/watch/(?P<id>[0-9]+)/(?:[^?/]+)?.*)'), 
	    "control": "SM_RANGE", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "myvideo.de"
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		# Get video webpage
		try:
			video_id = Universal.get_video_id(self.basename, self.url)
			url = 'http://www.myvideo.de/watch/%s' % video_id

			fd = self.conecte(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a página

		mobj = re.search(r'<link rel=\'image_src\' href=\'(http://is[0-9].myvideo\.de/de/movie[0-9]+/[a-f0-9]+)/thumbs/[^.]+\.jpg\' />', webpage)
		video_url = mobj.group(1) + ('/%s.flv' % video_id)

		try: video_title = re.search('<title>([^<]+)</title>', webpage).group(1)
		except: video_title = get_radom_title()

		self.configs = {
			'id': video_id,
			'url': video_url,
			'uploader':	u'NA',
			'upload_date': u'NA',
			'title': video_title,
			'ext': u'flv',
			'format': u'NA',
			'player_url': None,
		}

##################################### COLLEGEHUMOR ####################################
class CollegeHumor( SiteBase ):
	"""Information extractor for collegehumor.com"""
	## http://www.collegehumor.com/video/6768211/hardly-working-the-human-gif
	controller = {
	    "url": "http://www.collegehumor.com/video/%s", 
	    "patterns": re.compile(r'(?P<inner_url>^(?:https?://)?(?:www\.)?collegehumor\.com/(?:video|embed)/(?P<id>[0-9]+)/.+)'), 
	    "control": "SM_RANGE", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "collegehumor.com"
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		try:
			fd = self.conecte(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a página

		m = re.search(r'id="video:(?P<internalvideoid>[0-9]+)"', webpage)
		if m is None: return

		internal_video_id = m.group('internalvideoid')

		info = {'id': video_id, 'internal_id': internal_video_id}
		xmlUrl = 'http://www.collegehumor.com/moogaloop/video:' + internal_video_id
		try:
			fd = self.conecte(xmlUrl, proxies=proxies, timeout=timeout)
			metaXml = fd.read(); fd.close()
		except: return # falha obtendo dados xml

		mdoc = xml.etree.ElementTree.fromstring(metaXml)
		videoNode = mdoc.findall('./video')[0]
		info['title'] = videoNode.findall('./caption')[0].text
		info['url'] = videoNode.findall('./file')[0].text
		try:	
			info['description'] = videoNode.findall('./description')[0].text
			info['thumbnail'] = videoNode.findall('./thumbnail')[0].text
			info['ext'] = info['url'].rpartition('.')[2]
			info['format'] = info['ext']
		except: pass

		self.configs = info

###################################### MEGAVIDEO ######################################
class Megavideo( SiteBase ):
	controller = {
	    "url": "http://www.megavideo.com/?v=%s", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?www\.megavideo\.com/\?(?:v|d)=(?P<id>\w+))"), 
	    "control": "SM_SEEK", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.confgsMacth = re.compile('\s*(.+?)\s*=\s*"(.*?)"', re.DOTALL)
		self.videoLink = 'http://www.megavideo.com/xml/videolink.php?v='
		# bytes inicias removidos da stream segmentada
		self.streamHeaderSize = 9
		self.url = url
		self.val = {}

	def suportaSeekBar(self):
		return True

	def getLink(self):
		link = "http://www%s.megavideo.com/files/%s/" %(
			self.configs["s"], 
			decrypter.decrypt32byte(self.configs["un"], 
				                    self.configs["k1"], 
				                    self.configs["k2"])
		)
		return link

	def get_size(self, proxies=None):
		""" retorna um inteiro longo. O valor representa o tamanho da stream """
		size = self.configs.get("size", False)
		assert size, "Pegando o tamanho do arquivo."
		return long(size)

	def getQueryString(self, url):
		""" retorna v ou d mais o id: CYXMVK0G da url, como uma tupla """
		parse = urlparse.urlparse( url)
		s, id = parse.query.split("=")
		return (s, id)

	def getMegavideoId(self, url, proxies, timeout):
		fd = self.conecte(url, proxies, timeout)
		data = fd.read(); fd.close()
		# inicia a procura do id
		match = re.search('flashvars\.v\s*=\s*"(.*)";', data)
		return match.group(1) ## valor de flashvars.v

	def converteURL(self, url ):
		""" Troca o nome do servidor megaupload:megavideo """
		return url.replace("megaupload", "megavideo")

	def start_extraction(self, proxies={}, timeout=25):
		#converte a url de megaupload para megavideo
		url = self.converteURL( self.url)
		queryattr, url_id = self.getQueryString( url)

		if queryattr == "d": # url com parametro d
			if self.val.get(url_id, None) is None:
				megavId = self.getMegavideoId( url, proxies, timeout)
				# id encontrado dentro da pagina do megaupload
				url = self.videoLink + megavId
				self.val[ url_id ] = megavId
			else:
				url = self.videoLink + self.val[ url_id ]

		elif queryattr == "v": # url com parametro v
			url = self.videoLink + url_id

		fd = self.conecte(url, proxies, timeout)
		data = fd.read(); fd.close()

		if fd.code == 200:
			self.configs = dict( self.confgsMacth.findall( data ) )
			self.configs["ext"] = "flv"
	
###################################### MEGAPORN #######################################
class MegaPorn( Megavideo):
	controller = {
	    "url": "http://www.megaporn.com/video/?v=%s", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?www\.(?:megaporn|cum)?\.com/video/\?v=(?P<id>\w+))"), 
	    "control": "SM_SEEK", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		Megavideo.__init__(self, url, **params)
		self.videoLink = "http://www.megaporn.com/video/xml/videolink.php?v="

###################################### VIDEOBB ########################################
class Videobb( SiteBase ):
	## http://www.videobb.com/video/XuS6EAfMb7nf
	## http://www.videobb.com/watch_video.php?v=XuS6EAfMb7nf
	controller = {
	    "url": "http://www.videobb.com/video/%s", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?(?:www\.)?videobb\.com/(?:video/|watch_video\.php\?v=)(?P<id>\w+))"), 
	    "control": "SM_SEEK", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)	
		self.settingsLink = "http://www.videobb.com/player_control/settings.php?v=%s"
		self.basename = manager.UrlManager.getBaseName( url)
		self.env = ["settings","config"]
		self.res = ["settings","res"]
		self.key2 = 226593
		self.cfg = {}
		# bytes inicias removidos da stream segmentada
		self.streamHeaderSize = 13
		self.url = url

	def suportaSeekBar(self):
		return True

	def isToken(self, key):
		""" retorna True se key=token """
		return (key[0:5] == 'token' and key != 'token2' and key != 'token3')

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
		for tokenname in filter(self.isToken, config.keys()):
			url = base64.b64decode(config[tokenname])

			if url.startswith("http"):
				url = self.getNewUrl(url, params)
				urls[tokenname] = url+"start="
		return urls

	def get_res_urls(self, params):
		urls = {}
		_res = params[self.res[0]].get(self.res[1], [])
		for index, res in enumerate(_res):
			url = base64.b64decode( res["u"] )

			seekname = res.get("seekname","start")+"="
			t_param = res.get("t","")
			r_param = res.get("r","")

			url = self.getNewUrl(url, params)

			if t_param: url = re.sub("t=[^&]+","t=%s"%t_param, url)
			if r_param: url = re.sub("r=[^&]+","r=%s"%r_param, url)

			urls[index+1] = url+seekname
		return urls

	def getNewUrl(self, url, params):
		""" Faz a conversão da url antiga e inválida, para a mais nova. """
		new_url = url.replace(":80", "")

		g_ads = self.get_gads(params)
		sece2 = self.get_sece2(params)
		spn = self.get_spn(params)
		rkts = self.get_rkts(params)

		# faz a decriptografia do link
		parse = decrypter.parse(g_ads_url = g_ads["url"], 
				                g_ads_type = g_ads["type"], g_ads_time = g_ads["time"],
				                key2 = self.key2, rkts=rkts, sece2=sece2, spn=spn
				                )
		return "&".join([new_url, parse])

	def getLink(self):
		vquality = int(self.params.get("qualidade", 2))

		optToNotFound = self.configs.get("token1", None)
		optToNotFound = self.configs.get(1, optToNotFound)
		optToNotFound = self.configs.get(2, optToNotFound)
		optToNotFound = self.configs.get(3, optToNotFound)

		videoLink = self.configs.get(vquality, optToNotFound)
		return videoLink

	def getTitle(self):
		title = self.configs["title"]
		title = urllib.unquote_plus( title)
		title = DECODE( title) # decodifica o title
		# remove caracteres invalidos
		title = clearTitle( title )
		return limiteTexto( title )

	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		url = self.settingsLink % video_id

		fd = self.conecte(url, proxies=proxies, timeout=timeout)
		data = fd.read(); fd.close()

		params = json.loads(data)

		try: # urls normais - formato antigo
			urls = self.get_urls(params)
			self.configs["token1"] = urls["token1"]
		except: pass

		# urls com nível de resução
		self.configs.update( self.get_res_urls(params) )

		self.configs["title"] = self.get_title(params)
		self.configs["ext"] = "flv"

###################################### VIDEOZER #######################################
class Videozer( Videobb):
	## http://www.videozer.com/video/ceN9vZXa
	controller = {
	    "url": "http://www.videozer.com/video/%s", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?(?:www\.)?videozer\.com/video/(?P<id>\w+))"), 
	    "control": "SM_SEEK", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		Videobb.__init__(self, url, **params)
		self.settingsLink = 'http://www.videozer.com/player_control/settings.php?v=%s&fv=v1.1.14'
		self.env = ["cfg","environment"]
		self.res = ["cfg","quality"]
		self.key2 = 215678

	def get_sece2(self, params):
		return params["cfg"]["info"]["sece2"]

	def get_title(self, params):
		return params["cfg"]["info"]["video"]["title"]

	def get_gads(self, params):
		return params["cfg"]["ads"]["g_ads"]

	def get_rkts(self, params):
		return params[self.env[0]][self.env[1]]["rkts"]

	def get_spn(self, params):
		return params["cfg"]["login"]["spn"]

###################################### USERPORN #######################################
class Userporn( Videobb ):
	## http://www.userporn.com/video/WZ8Nuf2blzw8
	## http://www.userporn.com/watch_video.php?v=WZ8Nuf2blzw8
	controller = {
	    "url": "http://www.userporn.com/video/%s", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?(?:www\.)?userporn\.com/(?:video/|watch_video\.php\?v=)(?P<id>\w+))"), 
	    "control": "SM_SEEK",
	    "video_control": None
	}

	def __init__(self, url, **params):
		Videobb.__init__(self, url, **params)
		self.settingsLink = "http://www.userporn.com/player_control/settings.php?v=%s"
		self.key2 = 526729
		
################################# VIDEO_MIXTURECLOUD ##################################
class Mixturecloud( SiteBase ):
	## http://www.mixturecloud.com/video=iM1zoh
	## http://www.mixturecloud.com/download=MB8JBD
	## http://www.mixturecloud.com/media/anSK2C
	## http://player.mixturecloud.com/embed=Sc0oym
	## http://player.mixturecloud.com/video/zQfFrx.swf
	## http://video.mixturecloud.com/video=jlkjljk
	## http://www.mixturevideo.com/video=xFRjoQ
	controller = {
	    "url": "http://www.mixturecloud.com/video=%s",
	    "basenames": ["video.mixturecloud","mixturecloud.com","player.mixturecloud","mixturevideo.com"],
	    "patterns": (
	        re.compile("(?P<inner_url>(?:http://)?www\.mixturecloud\.com/(?:video=|download=|media/)(?P<id>\w+))"),
	        re.compile("(?P<inner_url>(?:http://)?video\.mixturecloud\.com/video=(?P<id>\w+))"), [
	            re.compile("(?P<inner_url>(?:http://)?player\.mixturecloud\.com/(?:embed=|video/)(?P<id>\w+)(?:\.swf)?)"),
	            re.compile("(?P<inner_url>(?:http://)?www.mixturevideo.com/video=(?P<id>\w+))")
	        ],
	    ),
	    "control": "SM_SEEK",
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		# parte principal da url usada como elemento chave no programa
		self.basename = manager.UrlManager.getBaseName( url )
		self.streamHeaderSize = 13
		self.url = url
		
	def getPostData(self, webpage=""):
		""" extrai informações da página de login para o post """
		longin_data = {
			"email": "creachut@temporarioemail.com.br",
			"password": "creachut@temporarioemail.com.br", 
			"submit_form_login": 1,
			"submit_key": ""}

		regex_str = ['name="submit_form_login" value="(\w+?)".*?',
				     'name="submit_key" value="(\w*?)"']		
		matchobj = re.search("".join(regex_str), webpage, re.DOTALL)

		if matchobj:
			longin_data["submit_form_login"] = matchobj.group(1)
			longin_data["submit_key"] = matchobj.group(2)

		return urllib.urlencode( longin_data )

	def login(self, opener, timeout):
		""" faz o login necessário para transferir o arquivo de vídeo.
		opener é quem armazerá o cookie """
		try:
			url = "http://www.mixturecloud.com/login"
			response = opener.open(url, timeout=timeout)
			loginPage = response.read()
			response.close()

			# dados do método post
			post_data = self.getPostData( loginPage )

			# logando
			response = opener.open(url, data = post_data, timeout=timeout)
			response.close()
			sucess = True
		except Exception, err:
			sucess = False
		return sucess

	def suportaSeekBar(self):
		return True

	def getLink(self):
		vquality = int(self.params.get("qualidade", 2))

		optToNotFound = self.configs.get(1, None)
		optToNotFound = self.configs.get(2, optToNotFound)
		optToNotFound = self.configs.get(3, optToNotFound)

		videoLink = self.configs.get(vquality, optToNotFound)
		return videoLink

	def getMessage(self, webpage):
		matchobj = re.search('<div class="alert i_alert red".*?>(?P<msg>.+?)</div>', webpage)
		try: msg = u"%s informa: %s"%(self.basename, unicode(matchobj.group("msg"),"UTF-8"))
		except: msg = ""
		return msg
	
	def get_configs(self, webpage):
		info = {}
		try:
			matchobj = re.search("<title.*>(.+?)</title>", webpage)
			info["title"] = matchobj.group(1)
		except:
			# usa um titulo gerado de caracteres aleatórios
			info["title"] = get_radom_title()

		try: # ** URL NORMAL **
			matchobj = re.search("flashvars.+(?:'|\")file(?:'|\")\s*:\s*(?:'|\")(.+?\.flv.*?)(?:'|\")", webpage, re.DOTALL|re.IGNORECASE)
			flv_code = matchobj.group(1)

			#'streamer':'http://www441.mixturecloud.com/streaming.php?key_stream=a31dff5ee1528ded3df4841b6364f9b5'
			matchobj = re.search("flashvars.+(?:'|\")streamer(?:'|\")\s*:\s*(?:'|\")(.+?)(?:'|\")", webpage, re.DOTALL|re.IGNORECASE)
			streamer = matchobj.group(1)

			# guarda a url para atualizar nas configs
			info[1] = "%s&file=%s&start="%(streamer, flv_code)
		except: pass

		try: # ** URL HD **
			matchobj = re.search("property=\"og:video\"\s*content=\".+hd\.file=(.+?\.flv)", webpage, re.DOTALL|re.IGNORECASE)
			if matchobj: 
				flv_code_hd = matchobj.group(1)
			else:
				matchobj = re.search("flashvars.+(?:'|\")hd\.file(?:'|\")\s*:\s*(?:'|\")(.*?\.flv)(?:'|\")", webpage, re.DOTALL|re.IGNORECASE)
				flv_code_hd = matchobj.group(1)

			matchobj = re.search("property=\"og:video\"\s*content=\".+streamer=(.+?)\"", webpage, re.DOTALL|re.IGNORECASE)

			if matchobj:
				streamer_hd = matchobj.group(1)
				info[2] = "%s&file=%s&start="%(streamer_hd, flv_code_hd)
			else:
				info[2] = "%s&file=%s&start="%(streamer, flv_code_hd)
		except: pass

		return info

	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		url = "http://video.mixturecloud.com/video=%s"% video_id
		
		fd = self.conecte(url, proxies=proxies, timeout=timeout, login=True)
		webpage = fd.read(); fd.close()
		
		self.message = self.getMessage( webpage)
		self.configs.update(self.get_configs(webpage))

###################################### MODOVIDEO ######################################
class Modovideo( SiteBase ):
	## http://www.modovideo.com/video.php?v=08k9h2hm0mq3zjvs69850dyjpdgzghfg
	## http://www.modovideo.com/video?v=t15yzbsacm6z10vs0wh0v9hc1cprba76
	## http://www.modovideo.com/frame.php?v=4mcyh0h5y2gc27g2dgsc7g80j6tpw4c0
	controller = {
	    "url": "http://www.modovideo.com/video.php?v=%s", 
	    "patterns":(
	         re.compile("(?P<inner_url>(?:http://)?(?:www\.)?modovideo\.com/(?:video\?|video\.php\?)v=(?P<id>\w+))"),
	        [re.compile("(?P<inner_url>(?:http://)?(?:www\.)?modovideo\.com/frame\.php\?v=(?P<id>\w+))")]
	    ),
	    "control": "SM_SEEK", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "modovideo.com"
		self.streamHeaderSize = 13
		self.url = url

	def suportaSeekBar(self):
		return True

	def getLink(self):
		vquality = int(self.params.get("qualidade", 2))

		optToNotFound = self.configs.get(1, None)
		optToNotFound = self.configs.get(2, optToNotFound)
		optToNotFound = self.configs.get(3, optToNotFound)

		videoLink = self.configs.get(vquality, optToNotFound)
		return videoLink

	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		url = 'http://www.modovideo.com/video.php?v=%s'%video_id

		try:
			fd = self.conecte(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha ao obter página

		try:
			self.configs["title"] = re.search("<title.*>(.+?)</title>", webpage).group(1)
		except:
			try: self.configs["title"] = re.search("<meta name=\"title\" content=\"(.+?)\"\s*/>", webpage).group(1)
			except: self.configs["title"] = get_radom_title() # usa um titulo gerado de caracteres aleatórios

		# o link está dentro de <iframe>
		## playerUrl = re.search('(?:<iframe)?.+?src="(.+?frame\.php\?v=.+?)"', webpage).group(1)
		playerUrl = "http://www.modovideo.com/frame.php?v=%s"%video_id
		fd = self.conecte(playerUrl, proxies=proxies, timeout=timeout)
		script = fd.read(); fd.close()

		matchobj = re.search("\.setup\(\{\s*flashplayer:\s*\"(.+)\"", script, re.DOTALL|re.IGNORECASE)
		qs_dict = cgi.parse_qs( matchobj.group(1) )
		videoUrl = qs_dict["player5plugin.video"][0]

		# guarda a url para atualizar nas configs
		self.configs[1] = videoUrl + "?start="

###################################### VIDEOWEED ######################################
class Videoweed( SiteBase ):
	## http://www.videoweed.es/file/sackddsywnmyt
	## http://embed.videoweed.es/embed.php?v=sackddsywnmyt
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
		# link direto para o site(não embutido)
		self.siteVideoLink = "http://www.videoweed.es/file/%s"
		# parte principal da url usada como elemento chave no programa
		self.basename = manager.UrlManager.getBaseName( url )
		self.streamHeaderSize = 13
		self.url = url
		
	def suportaSeekBar(self):
		return True

	def getLink(self):
		vquality = int(self.params.get("qualidade", 2))

		optToNotFound = self.configs.get(1, None)
		optToNotFound = self.configs.get(2, optToNotFound)
		optToNotFound = self.configs.get(3, optToNotFound)

		videoLink = self.configs.get(vquality, optToNotFound)
		return videoLink

	def start_extraction(self, proxies={}, timeout=25):
		try:
			url_id = Universal.get_video_id(self.basename, self.url)
			url = self.siteVideoLink % url_id

			fd = self.conecte(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a página

		## flashvars.filekey="189.24.243.113-505db61fc331db7a2a7fa91afb22e74d-"
		matchobj = re.search('flashvars\.filekey="(.+?)"', webpage)
		filekey = matchobj.group(1)

		try:
			url = self.player_api % (filekey, url_id) # ip; id
			fd = self.conecte(url, proxies=proxies, timeout=timeout)
			info_data = fd.read(); fd.close()
		except: return # falha obtendo a página

		params = dict(re.findall("(\w+)=(.*?)&", info_data))

		url = urllib.unquote_plus( params["url"] )
		seekparm = urllib.unquote_plus( params["seekparm"] )

		if not seekparm: seekparm = "?start="
		elif seekparm.rfind("=") < 0:
			seekparm = seekparm + "="
			
		try: title = urllib.unquote_plus( params["title"] )
		except: title = get_radom_title()

		self.configs = {1: url + seekparm, "title": title}

####################################### NOVAMOV #######################################
class Novamov( Videoweed ):
	""" Novamov: segue a mesma sequência lógica de Videoweed """
	## http://www.novamov.com/video/cfqxscgot96pe
	## http://embed.novamov.com/embed.php?width=520&height=320&v=cfqxscgot96pe&px=1
	controller = {
	    "url": "http://www.novamov.com/video/%s", 
	    "basenames": ["novamov.com", "embed.novamov"],
		"patterns": (
	         re.compile("(?P<inner_url>(?:http://)?www\.novamov\.com/video/(?P<id>\w+))"),
	        [re.compile("(?P<inner_url>(?:http://)?embed\.novamov\.com/embed\.php\?.*v=(?P<id>\w+))")]
	    ),
		"control": "SM_SEEK", 
		"video_control": None
	}
	
	def __init__(self, url, **params):
		"""Constructor"""
		# objetos de Videoweed não anulados nessa inicialização,
		# serão considerados objetos válidos para novos objetos de Novamov.
		Videoweed.__init__(self, url, **params)
		self.player_api = "http://www.novamov.com/api/player.api.php?key=%s&user=undefined&codes=1&pass=undefined&file=%s"
		# link direto para o site(não embutido)
		self.siteVideoLink = "http://www.novamov.com/video/%s"		
		# parte principal da url usada como elemento chave no programa
		self.basename = manager.UrlManager.getBaseName( url )
		self.url = url

####################################### NOVAMOV #######################################
class NowVideo( Videoweed ):
	""" Novamov: segue a mesma sequência lógica de Videoweed """
	## http://embed.nowvideo.eu/embed.php?v=xhfpn4q7f8k3u&width=600&height=480
	## http://www.nowvideo.eu/video/frvtqye2xed4i
	controller = {
	    "url": "http://www.nowvideo.eu/video/%s",
	    "basenames": ["embed.nowvideo", "nowvideo.eu"],
	    "patterns": (
	         re.compile("(?P<inner_url>(?:http://)?www\.nowvideo\.eu/video/(?P<id>\w+))"),
	        [re.compile("(?P<inner_url>(?:http://)?embed\.nowvideo\.eu/embed\.php\?.*v=(?P<id>\w+))")]
	    ),
	    "control": "SM_SEEK", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		"""Constructor"""
		# objetos de Videoweed não anulados nessa inicialização,
		# serão considerados objetos válidos para novos objetos de Novamov.
		Videoweed.__init__(self, url, **params)
		self.player_api = "http://www.nowvideo.eu/api/player.api.php?key=%s&user=undefined&codes=1&pass=undefined&file=%s"
		# link direto para o site(não embutido)
		self.siteVideoLink = "http://embed.nowvideo.eu/embed.php?v=%s"		
		# parte principal da url usada como elemento chave no programa
		self.basename = manager.UrlManager.getBaseName( url )
		self.url = url

######################################## VEEVR ########################################
class Veevr( SiteBase ):
	## http://veevr.com/videos/L5pP6wxDK
	controller = {
	    "url": "http://veevr.com/videos/%s", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?veevr\.com/videos/(?P<id>\w+))"), 
	    "control": "SM_RANGE", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		"""Constructor"""
		SiteBase.__init__(self, **params)
		self.streamHeaderSize = 0
		self.basename = "veevr.com"
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		try:
			# página web inicial
			fd = self.conecte(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a página

		try:
			patternUrl = "http://mps.hwcdn.net/.+?/ads/videos/download.+?"
			matchobj = re.search(
				"playlist:.+?url:\s*(?:'|\")(%s)(?:'|\")"%patternUrl, 
				webpage, re.DOTALL|re.IGNORECASE
			)
			# url final para o vídeo ?
			mediaUrl = urllib.unquote_plus( matchobj.group(1) )
		except Exception, err:
			matchobj = re.search(
				"playlist:.+url:\s*(?:'|\")(http://hwcdn.net/.+/cds/.+?token=.+?)(?:'|\")", 
				webpage, re.DOTALL|re.IGNORECASE )

			# url final para o vídeo
			mediaUrl = matchobj.group(1)
			mediaUrl = urllib.unquote_plus( mediaUrl )

		# iniciando a extração do título do vídeo
		try:
			matchobj = re.search("property=\"og:title\" content=\"(.+?)\"", webpage)
			title = matchobj.group(1)
		except:
			try:
				matchobj = re.search("property=\"og:description\" content=\"(.+?)\"", webpage)
				title = matchobj.group(1)[:25] # apenas parte da descrição será usada							
			except:
				# usa um titulo gerado de caracteres aleatórios
				title = get_radom_title()

		ext = "mp4" # extensão padrão

		if re.match(".+/Manifest\.", mediaUrl):
			fd = self.conecte(mediaUrl, proxies=proxies, timeout=timeout)
			xmlData = fd.read(); fd.close()

			# documento xml
			mdoc = xml.etree.ElementTree.fromstring( xmlData )

			# url final para o vídeo
			media = mdoc.find("{http://ns.adobe.com/f4m/1.0}media")
			mediaUrl = media.attrib["url"] + "Seg1-Frag1"

			try:
				mimeType = mdoc.find("{http://ns.adobe.com/f4m/1.0}mimeType")
				ext = mimeType.text.split("/", 1)[-1] # extensão representada pelo texto da tag
			except:pass # em caso de erro, usa a extesão padrão

		self.configs = {"url": mediaUrl, "ext": ext, "title": title}

###################################### PUTLOCKER ######################################
class PutLocker( SiteBase ):
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
		re.DOTALL|re.IGNORECASE
	)

	def __init__(self, url, **params):
		"""Constructor"""
		SiteBase.__init__(self, **params)
		self.streamHeaderSize = 0
		self.basename = "putlocker.com"
		self.getFileBaseUrl = "http://www.putlocker.com"
		self.url = url

	def suportaSeekBar(self):
		return False

	def getMessage(self, webpage):
		## <div class='message t_0'>This file doesn't exist, or has been removed.</div>
		try:
			matchobj = re.search("<div class='message t_\d+'>(.*?)</div>", webpage)
			msg = "%s informa: %s"%(self.basename, unicode(matchobj.group(1),"utf-8"))
		except: msg = ""
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
		url = self.url.replace("/embed","/file")
		fd = self.conecte(url, proxies=proxies, timeout=timeout)
		webpage = fd.read(); fd.close()

		# messagem de erro. se houver alguma
		self.message = self.getMessage( webpage )

		# padrão captua de dados
		matchobj = self.patternForm.search( webpage )
		hashvalue =  matchobj.group("hash") or  matchobj.group("_hash")
		hashname = matchobj.group("name") or  matchobj.group("_name")
		confirmvalue = matchobj.group("confirm")

		data = urllib.urlencode({hashname: hashvalue, "confirm": confirmvalue})
		fd = self.conecte(url, proxies=proxies, timeout=timeout, data=data)
		webpage = fd.read(); fd.close()

		# extraindo o titulo.
		try: title = re.search("<title>(.*?)</title>", webpage).group(1)
		except: title = get_radom_title()

		# começa a extração do link vídeo.
		## playlist: '/get_file.php?stream=WyJORVE0TkRjek5FUkdPRFJETkRKR05Eb3',
		pattern = """playlist:\s*(?:'|")(/get_file\.php\?stream=.+?(?:'|"))"""
		matchobj = re.search(pattern, webpage, re.DOTALL|re.IGNORECASE)
		url = self.getFileBaseUrl + matchobj.group(1)

		# começa a análize do xml
		fd = self.conecte(url, proxies=proxies, timeout=timeout)
		rssData = fd.read(); fd.close()

		ext = "flv" # extensão padrão.

		# url do video.
		url = re.search("<media:content url=\"(.+?)\"", rssData).group(1)
		url = self.unescape( url )

		try: ext = re.search("type=\"video/([\w-]+)", rssData).group(1)
		except: pass # usa a extensão padrão.
		
		self.configs = {"url": url, "title":title, "ext": ext}

###################################### PUTLOCKER ######################################
class Sockshare( PutLocker ):
	## http://www.sockshare.com/file/E6DDA74FBBBFFC12
	## http://www.sockshare.com/embed/E6DDA74FBBBFFC12
	controller = {
		"url": "http://www.sockshare.com/file/%s", 
		"patterns": (
		     re.compile("(?P<inner_url>(?:http://)?www\.sockshare\.com/file/(?P<id>\w+))"),
		    [re.compile("(?P<inner_url>(?:http://)?www\.sockshare\.com/embed/(?P<id>\w+))")]
		    ),
		"control": "SM_RANGE", 
		"video_control": None
	}

	def __init__(self, url, **params):
		"""Constructor"""
		PutLocker.__init__(self, url, **params)
		self.streamHeaderSize = 0
		self.getFileBaseUrl = "http://www.sockshare.com"
		self.basename = "sockshare.com"
		self.url = url

###################################### MOVIEZER #######################################
class Moviezer( SiteBase ):
	controller = {
	    "url": "http://moviezer.com/video/%s", 
	    "patterns": (
	         re.compile("(?P<inner_url>(?:http://)?moviezer\.com/video/(?P<id>\w+))"),
	        [re.compile("(?P<inner_url>(?:http://)?moviezer\.com/e/(?P<id>\w+))")] #embed url
	    ),
	    "control": "SM_SEEK", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		"""Constructor"""
		SiteBase.__init__(self, **params)
		self.streamHeaderSize = 13
		self.basename = "moviezer.com"
		self.url = url

	def suportaSeekBar(self):
		return True

	def start_extraction(self, proxies={}, timeout=25):
		try:
			fd = self.conecte(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()

			matchobj = re.search("flashvars\s*=\s*\{.*?'file':\s*'(?P<url>.*?)'", webpage, re.DOTALL)
			url = matchobj.group("url")
		except: return # falha em obter a página

		try:
			matchobj = re.search("<title>(?P<title>.*?)</title>", webpage)
			title = matchobj.group("title")
		except:
			title = get_radom_title()

		self.configs = {"url": url+"?start=", "title": title}

###################################### MOEVIDEO #######################################
class MoeVideo( SiteBase ):
	## http://moevideo.net/video.php?file=64141.60e02b3b80c5e95e2e4ac85f0838&width=600&height=450
	## http://moevideo.net/?page=video&uid=79316.7cd2a2d4b5e02fd77f017bbc1f01
	controller = {
	    "url": "http://moevideo.net/video.php?file=%s", 
	    "patterns":(
	         re.compile("(?P<inner_url>http://moevideo\.net/\?page=video&uid=(?P<id>\w+\.\w+))"),
	        [re.compile("(?P<inner_url>http://moevideo\.net/video\.php\?file=(?P<id>\w+\.\w+))")]
	    ),
	    "control": "SM_RANGE", 
	    "video_control": None
	}

	def __init__(self, url, **params):
		"""Constructor"""
		SiteBase.__init__(self, **params)
		self.apiUrl = "http://api.letitbit.net/"
		self.basename = "moevideo.net"
		self.streamHeaderSize = 13
		self.url = url
		
	def suportaSeekBar(self):
		return True

	def getPostData(self, video_id):
		encoder = json.JSONEncoder()
		post = {"r": encoder.encode(
			["tVL0gjqo5", 
			 ["preview/flv_image",{"uid":"%s"%video_id}], 
			 ["preview/flv_link",{"uid":"%s"%video_id}]])
				}
		return urllib.urlencode( post )

	def extratcLink(self, videoinfo):
		link = ""
		if videoinfo["status"].lower() == "ok":
			for info in videoinfo["data"]:
				if type(info) is dict and info.has_key("link"):
					link = info["link"]
					break
		return link

	def extraticTitle(self, url):
		title = url.rsplit("/", 1)[-1]
		title = title.rsplit(".", 1)[0]
		return title

	def setErrorMessage(self, url, videoinfo):
		if not url:
			if videoinfo["status"].lower() == "fail":
				msg = videoinfo["data"]
			else:
				if u"not_found" in videoinfo["data"]:
					msg = "file not found"
				else:
					msg = videoinfo["data"][0]
			self.message = msg

	def start_extraction(self, proxies={}, timeout=25):
		try:
			video_id = Universal.get_video_id(self.basename, self.url)
			postdata = self.getPostData( video_id )

			fd = self.conecte(self.apiUrl, proxies=proxies, timeout=timeout, data=postdata)
			webdata = fd.read(); fd.close()

			videoinfo = json.loads( webdata)
			url = self.extratcLink( videoinfo)
		except: return # falha obtendo a página

		try:
			self.setErrorMessage(url, videoinfo)
		except:pass

		# obtendo o título do video
		try: title = self.extraticTitle( url)
		except: title = get_radom_title()

		self.configs = {"url": url, "title": title}

###################################### ANIMETUBE #######################################
class Anitube( SiteBase ):
	## http://www.anitube.jp/video/43595/Saint-Seiya-Omega-07
	controller = {
	    "url": "http://www.anitube.jp/video/%s", 
	    "patterns": re.compile("(?P<inner_url>http://www\.anitube\.jp/video/(?P<id>\w+))"),
	    "control": "SM_RANGE", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "anitube.jp"
		self.streamHeaderSize = 0
		self.url = url

	def suportaSeekBar(self):
		return False

	def start_extraction(self, proxies={}, timeout=25):
		try:
			fd = self.conecte(self.url, proxies=proxies, timeout=timeout)
			webdata = fd.read(); fd.close()
		except: return

		## addParam("flashvars",'config=http://www.anitube.jp/nuevo/config.php?key=c3ce49fd327977f837ab')
		##<script type="text/javascript">var cnf=
		try:
			mathobj = re.search("addParam\(\"flashvars\",\s*'config=\s*(?P<url>.+?)'\)", webdata, re.DOTALL)			
			url = mathobj.group("url")
		except:
			mathobj = re.search("\<script type=\"text/javascript\"\>\s*var\s*cnf\s*=\s*(?:'|\")(?P<url>.+?)(?:'|\")", webdata, re.DOTALL)			
			url = mathobj.group("url")

		## <file>http://lb01-wdc.anitube.com.br/42f56c9f566c1859da833f80131fdcd5/4fafe9c0/43595.flv</file>
		## <title>Saint Seiya Omega 07</title>
		fd = self.conecte(url, proxies=proxies, timeout=timeout)
		xmldata = fd.read(); fd.close()

		if not re.match("http://www.anitube\.jp/nuevo/playlist\.php", url):
			play_url = re.search("<playlist>(.*?)</playlist>", xmldata).group(1)
			fd = self.conecte(play_url, proxies=proxies, timeout=timeout)
			xmldata = fd.read(); fd.close()

		video_url = re.search("<file>(.*?)</file>", xmldata).group(1)

		try: title = re.search("<title>(.*?)</title>", xmldata).group(1)
		except: title = get_radom_title()

		self.configs = {"url": video_url, "title": title}

###################################### VK #######################################
class Vk( SiteBase ):
	## http://vk.com/video_ext.php?oid=164478778&id=163752296&hash=246b8447ed557240&hd=1
	## http://vk.com/video103395638_162309869?hash=23aa2195ccec043b
	controller = {
	    "url": "http://vk.com/video_ext.php?%s",
	    "patterns": (
	         re.compile("(?P<inner_url>http://vk\.com/(?P<id>video\d+_\d+\?hash=\w+))"),
	        [re.compile("(?P<inner_url>http://vk\.com/video_ext\.php\?(?P<id>oid=\w+&id=\w+&hash=\w+(?:&hd=\d+)?))")]
	    ),
	    "control": "SM_SEEK",
	    "video_control": None
	}

	def __init__(self, url, **params):
		"""Constructor"""
		SiteBase.__init__(self, **params)
		self.streamHeaderSize = 13
		self.basename = "vk.com"
		self.url = url

	def suportaSeekBar(self):
		return True

	def getLink(self):
		vquality = int(self.params.get("qualidade", 2))

		optToNotFound = self.configs.get(1, None)
		optToNotFound = self.configs.get(2, optToNotFound)
		optToNotFound = self.configs.get(3, optToNotFound)

		videoLink = self.configs.get(vquality, optToNotFound)
		return videoLink

	def start_extraction(self, proxies={}, timeout=25):
		try:
			fd = self.conecte(self.url, proxies=proxies, timeout=timeout)
			webdata = fd.read(); fd.close()
		except: return

		mathobj = re.search("var\s*video_host\s*=\s*'(?P<url>.+?)'", webdata, re.DOTALL)
		url = mathobj.group("url")

		mathobj = re.search("var\s*video_uid\s*=\s*'(?P<uid>.+?)'", webdata, re.DOTALL)
		uid = mathobj.group("uid")

		mathobj = re.search("var\s*video_vtag\s*=\s*'(?P<vtag>.+?)'", webdata, re.DOTALL)
		vtag = mathobj.group("vtag")

		mathobj = re.search("var\s*video_max_hd\s*=\s*(?:')?(?P<max_hd>.+?)(?:')?", webdata, re.DOTALL)
		max_hd = mathobj.group("max_hd")

		mathobj = re.search("var\s*video_no_flv\s*=\s*(?:')?(?P<no_flv>.+?)(?:')?", webdata, re.DOTALL)
		no_flv = mathobj.group("no_flv")

		try: title = re.search("var\s*video_title\s*=\s*'(.+?)'", webdata).group(1)
		except: title = get_radom_title()

		## http://cs519609.userapi.com/u165193745/video/7cad4a848e.360.mp4
		if int(no_flv):
			ext = "mp4"
			if int(max_hd): self.configs[1] = url + "u%s/video/%s.240.mp4"%(uid, vtag)			
			self.configs[2] = url + "u%s/video/%s.360.mp4"%(uid, vtag)
		else:
			url = url + "u%s/video/%s.flv"
			ext = "flv"

		self.configs.update({"title": title, "ext":ext})

###################################### XVIDEOS #######################################
class Xvideos( SiteBase ):
	## http://www.xvideos.com/video2037621/mommy_and_daughter_spreading
	controller = {
		"url": "http://www.xvideos.com/%s", 
		"patterns": re.compile("(?P<inner_url>http://www.xvideos.com/(?P<id>video\w+)(?:/\w+)?)"),
		"control": "SM_SEEK",
		"video_control": None
	}

	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "xvideos.com"
		self.streamHeaderSize = 13
		self.url = url

	def suportaSeekBar(self):
		return True

	def start_extraction(self, proxies={}, timeout=25):
		try:
			fd = self.conecte(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return

		flashvar = re.search('\<embed\s*type.+flashvars="(.*?)"', webpage).group(1)
		video_data = cgi.parse_qs(flashvar)

		try: title = re.search("<title>(.*?)</title>", webpage).group(1)
		except: title = get_radom_title()

		self.configs = {"url": video_data["flv_url"][0]+"&fs=", "title": title}

###################################### REDTUBE #######################################
class Redtube( SiteBase ):
	## http://www.redtube.com/78790
	controller = {
		"url": "http://www.redtube.com/%s", 
		"patterns": re.compile("(?P<inner_url>http://www.redtube.com/(?P<id>\d+))"),
		"control": "SM_SEEK",
		"video_control": None
	}

	def __init__(self, url, **params):
		"""Constructor"""
		SiteBase.__init__(self, **params)
		self.basename = "redtube.com"
		self.streamHeaderSize = 13
		self.url = url

	def suportaSeekBar(self):
		return True

	def start_extraction(self, proxies={}, timeout=25):
		try:
			fd = self.conecte(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return

		flashvar = re.search("""so\.addParam\((?:"|')flashvars(?:"|'),\s*(?:"|')(.*?)(?:"|')""", webpage).group(1)
		video_data = cgi.parse_qs(flashvar)

		try: title = re.search("<title>(.*?)</title>", webpage).group(1)
		except: title = get_radom_title()

		self.configs = {"url": video_data["flv_h264_url"][0]+"&ec_seek=", "title": title}

###################################### REDTUBE #######################################
class Pornhub( SiteBase ):
	## http://www.pornhub.com/view_video.php?viewkey=1156461684&utm_source=embed&utm_medium=embed&utm_campaign=embed-logo
	controller = {
		"url": "http://www.pornhub.com/view_video.php?viewkey=%s", 
		"patterns": (
		     re.compile("(?P<inner_url>http://www\.pornhub\.com/view_video\.php\?viewkey=(?P<id>\w+))"),
		    [re.compile("(?P<inner_url>http://www\.pornhub\.com/view_video\.php\?viewkey=(?P<id>\w+).*&utm_source=embed)")]
		    ),
		"control": "SM_SEEK",
		"video_control": None
	}

	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.apiUrl = "http://www.pornhub.com/embed_player.php?id=%s"
		self.basename = "pornhub.com"
		self.streamHeaderSize = 13
		self.url = url
		
	def suportaSeekBar(self):
		return True

	def start_extraction(self, proxies={}, timeout=25):
		try:
			fd = self.conecte(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return

		## <video_url><![CDATA[http://cdn1b.video.pornhub.phncdn.com/videos/005/005/576/5005576.flv?rs=125&ri=600&s=1340328487&e=1340330287&h=717b8edd6e04c34e17ee054fb9ea1fcd]]></video_url>
		## image_url>http://cdn1.image.pornhub.phncdn.com/thumbs/005/005/576/xxlarge.jpg?cache=6497524</image_url>
		## var flashvars = {.*"video_url":"http%3A%2F%2Fcdn1b.video.pornhub.phncdn.com%2Fvideos%2F001%2F037%2F248%2F1037248.flv%3Frs%3D125%26ri%3D600%26s%3D1340409510%26e%3D1340411310%26h%3D62f117f5171484a9d63453ee9ef5558a", "video_title":"Two+Blonde+Girls+With+One+Guy"};
		## "video_title":"Two+Blonde+Girls+With+One+Guy"
		fs = ""
		try:
			matchobj = re.search('''(?:"|')video_url(?:"|')\s*:\s*(?:"|')(.+?)(?:"|')''', webpage, re.DOTALL)
			url = urllib.unquote_plus( matchobj.group(1) )
			try:
				matchobj = re.search('''(?:"|')video_title(?:"|')\s*:\s*(?:"|')(.*?)(?:"|')''', webpage, re.DOTALL)
				title = urllib.unquote_plus( matchobj.group(1) )
			except: title = ""
		except:
			urlid = Universal.get_video_id(self.basename, self.url)
			fd = self.conecte(self.apiUrl % urlid, proxies=proxies, timeout=timeout)
			xmlData = fd.read(); fd.close()

			url = re.search("""<video_url><!\[CDATA\[(.+)\]\]></video_url>""", xmlData).group(1)

			try: title = re.search("<video_title>(.*)</video_title>", xmlData).group(1)
			except: title = ""
			try: fs = re.search("<flvStartAt>(.+)</flvStartAt>", xmlData).group(1)
			except: fs = ""

		self.configs = {"url": url+(fs or "&fs="), "title": (title or get_radom_title())}

########################################################################
class DwShare( SiteBase ):
	## http://dwn.so/player/embed.php?v=DSFAE06F1C&width=505&height=400
	## http://dwn.so/xml/videolink.php?v=DSFAE06F1C&yk=c0352ffc881e858669b7c0f08d16f3edf47bfdea&width=1920&id=1342495730819&u=undefined
	## http://st.dwn.so/xml/videolink.php?v=DS4DDC9CDF&yk=3a31f85d3547ecddaa35d6b3329c11cfc69ff156&width=485&id=1344188495210&u=undefined	
	## un link = http://s1023.dwn.so/movie-stream,63e9266ab2e5baa4874fa8948ec7e3b8,5004e0ab,DSFAE06F1C.flv,0
	## <?xml version="1.0" encoding="utf-8"?>
	## <rows><row url="" runtime="0"  downloadurl="http://dwn.so/show-file/0c8fa9b8c2/114367/_Pie_8.O.Reencontro.Dub.cinefilmesonline.net.avi.html" runtimehms="89:17" size="1024" waitingtime="5000" k="" k1="76752" k2="75398" un="s1023.dwn.so/movie-stream,63e9266ab2e5baa4874fa8948ec7e3b8,5004e0ab,DSFAE06F1C.flv,0" s="" title="American Pie 8.O.Reencontro.Dub.cinefilmesonline.net.avi" description="Description" added="2011-05-30" views="-" comments="0" favorited="0" category="" tags="tags" rating="0" embed="%3Ciframe+src%3D%22http%3A%2F%2Fdwn.so%2Fplayer%2Fembed.php%3Fv%3DDSFAE06F1C%26width%3D500%26height%3D350%22+width%3D%22500%22+height%3D%22350%22+frameborder%3D%220%22+scrolling%3D%22no%22%3E%3C%2Fiframe%3E" private="1" mobilepay="0" icc="PL" mpaylang="en" limit1="You+have+watched+%5BN1%5D+minutes+of+video+today." limit2="Please+wait+%5BN2%5D+minutes+or+click+here+to+register+and+enjoy+unlimited+videos+FOR+FREE" limit3="purchase+premium+membership+with+Paypal+or+Moneybookers" limit4="or+purchase+it+using+your+mobile+phone" mobilepaylatin="1"></row>
	## </rows>
	controller = {
		"url": "http://dwn.so/player/embed.php?v=%s", 
		"patterns": [re.compile("(?P<inner_url>http://dwn\.so/player/embed\.php\?v=(?P<id>\w+)(?:&width=\d+)?(?:&height=\d+)?)")],
		"control": "SM_SEEK",
		"video_control": None
	}
	videolink = ("http://st.dwn.so/xml/videolink.php?v=%s", "http://dwn.so/xml/videolink.php?v=%s")
	#----------------------------------------------------------------------
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.streamHeaderSize = 13
		self.basename = "dwn.so"
		self.url = url
	
	def suportaSeekBar(self):
		return True
	
	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		for videlink in self.videolink:
			try:
				fd = self.conecte(videlink % video_id, proxies=proxies, timeout=timeout)
				xmlData = fd.read(); fd.close(); break
			except: continue
		else: raise IOError
		
		url = re.search("""un=(?:'|")(.*?)(?:'|")""", xmlData, re.DOTALL).group(1)
		if not url.startswith("http://"): url = "http://"+url
		if url[-2:] == ",0": url = url[:-1]
		
		try: title = re.search("""title\s*=\s*(?:'|")(.*?)(?:'|")""", xmlData, re.DOTALL).group(1)
		except: title = get_radom_title()
		
		self.configs = {"url": url, "title": title}

#######################################################################################
class Hostingbulk( SiteBase ):
	""""""
	## http://hostingbulk.com/jp33tfqh8835.html
	## http://hostingbulk.com/embed-jp33tfqh8835-600x480.html
	controller = {
		"url": "http://hostingbulk.com/%s.html", 
		"patterns": (
	         re.compile("(?P<inner_url>http://hostingbulk\.com/(?P<id>\w+)\.html)"),
		    [re.compile("(?P<inner_url>http://hostingbulk\.com/embed\-?(?P<id>\w+)\-?(?:\d+x\d+)?\.html)")]
	    ),
		"control": "SM_SEEK",
		"video_control": None
	}

	@staticmethod
	def base36encode( number ):
		if not isinstance(number, (int, long)):
			raise TypeError('number must be an integer')
		if number < 0:
			raise ValueError('number must be positive')
		alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
		base36 = ''
		while number:
			number, i = divmod(number, 36)
			base36 = alphabet[i] + base36

		return base36 or alphabet[0]

	@staticmethod
	def unpack_params(p, a, c, k, e=None, d=None):
		for index in range(c-1, -1, -1):
			pattern = r"\b%s\b"%Hostingbulk.base36encode( index ).lower()
			p = re.sub(pattern, k[ index ], p, re.M|re.DOTALL)
		return p.replace(r"\'", "'")

	#----------------------------------------------------------------------
	def __init__(self, url, **params):
		"""Constructor"""
		SiteBase.__init__(self, **params)
		self.basename = "hostingbulk.com"
		self.streamHeaderSize = 13
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		url = self.controller["url"] % video_id

		fd = self.conecte(url, proxies=proxies, timeout=timeout)
		webpage = fd.read(); fd.close()

		params = re.search("eval\(\s*function\s*\(.*\)\s*{.*?}\s*(.+)\)", webpage).group(1)
		matchobj = re.search("'(?P<ps>(.+?))'\s*,\s*(?P<n1>\d+?),\s*(?P<n2>\d+?),\s*'(?P<lps>.+?)\.split.+", params)

		uparams = self.unpack_params( matchobj.group("ps"), int(matchobj.group("n1")), int(matchobj.group("n2")), matchobj.group("lps").split("|"))

		url = re.search("'file'\s*,\s*'(.+?)'", uparams).group(1)
		pattern = "(http://.+?)//"; search = re.search(pattern, url)
		if search: url = re.sub(pattern, search.group(1)+"/d/", url)

		try: title = re.search("<title>(.+)</title>", webpage).group(1)
		except: title = get_radom_title()

		self.configs = {"url": url+"?start=", "title": title}

#######################################################################################
class Universal:
	"""A classe Universal, quarda varias informações e dados usados em
	toda a extensão do programa. Ela é usada para diminuir o número de modificações
	necessárias, quando adiciando suporte a um novo site vídeo.
	"""
	SM_SEEK  = staticmethod(lambda manage, noProxy=False, **params: manager.StreamManager(manage, noProxy, **params))
	SM_RANGE = staticmethod(lambda manage, noProxy=False, **params: manager.StreamManager_(manage, noProxy, **params))
	sites = {}
	
	@staticmethod
	def get_sites():
		return Universal.sites.keys()

	@staticmethod
	def add_site(basename="", args=None, **kwargs):
		""" adiciona as referências para um novo site """
		if args:
			url, patterns, control, video_control = args

			Universal.sites[ basename ] = {
				"video_control": video_control,
				"control": control,
				"patterns": patterns,
				"url": url,
			}
		elif kwargs:
			Universal.sites.update({ 
				basename: kwargs 
			})

	@staticmethod
	def get_video_id(sitename, url):
		""" retorna o id da url """
		matchobj = Universal.patternMatch(sitename, url)
		return matchobj.group("id")
	
	@staticmethod
	def getStreamManager( url):
		""" Procura pelo controlador de tranferênicia de arquivo de video"""
		smanager = None
		try:
			for sitename in Universal.get_sites():
				matchobj = Universal.patternMatch(sitename, url)
				if matchobj:
					smanager = Universal.get_control( sitename)
					break
		except AssertionError, err:
			raise AttributeError, _("Sem suporte para a url fornecida.")
		assert smanager, _("url desconhecida!")
		return smanager

	@staticmethod
	def getVideoManager( url):
		""" Procura pelo controlador de video baseado na url dada """
		vmanager = None
		try:
			for sitename in Universal.get_sites():
				matchobj = Universal.patternMatch(sitename, url)
				if matchobj:
					vmanager = Universal.get_video_control( sitename )
					break
		except AssertionError, err:
			raise AttributeError, _("Sem suporte para a url fornecida.")
		assert vmanager, _("url desconhecida!")
		return vmanager
	
	@staticmethod
	def get_patterns(sitename, validar=True):
		if validar: Universal.valide(sitename, "patterns")
		return Universal.sites[ sitename ]["patterns"]

	@staticmethod
	def patternMatch(sitename, url):
		""" analiza se a url casa o padrão de urls.
		Duas situações são possiveis:
			A url é única; A url está dentro de outra url.
		"""
		patterns = Universal.get_patterns(sitename)
		if type(patterns) is tuple:
			for pattern in patterns:
				if type(pattern) is list:
					for patter in pattern:
						matchobj = patter.match( url )
						if matchobj: break
				else:
					matchobj = pattern.match( url )
				if matchobj: break
		elif type(patterns) is list:
			for pattern in patterns:
				matchobj = pattern.match( url )
				if matchobj: break
		else:
			matchobj = patterns.match( url )
		return matchobj

	@staticmethod
	def isEmbed(url):
		""" analiza se a url é de um player embutido """
		sitename = manager.UrlManager.getBaseName(url)
		patterns = Universal.get_patterns(sitename)
		siteAttrs = Universal.sites[sitename]
		if type(patterns) is tuple:
			for pattern in patterns:
				if type(pattern) is list:
					for patter in pattern:
						matchobj = patter.match( url )
						if matchobj: return True
		elif type(patterns) is list:
			for pattern in patterns:
				matchobj = pattern.match( url )
				if matchobj: return True
		else:
			return siteAttrs.get("embed", False)

	@staticmethod
	def get_url(sitename, validar=True):
		if validar: Universal.valide(sitename, "url")
		return Universal.sites[ sitename ]["url"]

	@staticmethod
	def get_control(sitename, validar=True):
		if validar: Universal.valide(sitename, "control")
		return Universal.sites[ sitename ]["control"]

	@staticmethod
	def get_video_control(sitename, validar=True):
		if validar: Universal.valide(sitename, "video_control")
		return Universal.sites[ sitename ]["video_control"]

	@staticmethod
	def valide(sitename, obj):
		assert bool(Universal.sites.get(sitename, None)), u"Site %s não encontrado"%sitename
		if obj == "patterns":
			assert bool(Universal.sites[sitename].get("patterns", None)), u"Padrão não definido para %s"%sitename
		elif obj == "url":
			assert bool(Universal.sites[sitename].get("url", None)), u"Url não definida para %s"%sitename
		elif obj == "control":
			assert bool(Universal.sites[sitename].get("control", None)), u"Controlador não definido para %s"%sitename
		elif obj == "video_control":
			assert bool(Universal.sites[sitename].get("video_control", None)), u"Controlador de video não definido para %s"%sitename

#######################################################################################
def is_site_class( item ):
	""" retorna só os site devidamente configurados """
	try:
		sitename, classdef  = item
		return (callable(classdef) and issubclass(classdef,SiteBase) and hasattr(classdef,"controller"))
	except:
		return False
	
def register_site(basename, site):
	if site.controller["video_control"] is None:
		site.controller["video_control"] = site
	if isinstance(site.controller["control"], (str, unicode)):
		control = getattr(Universal, site.controller["control"])
		site.controller["control"] = control
	Universal.add_site(basename, **site.controller)
	
for sitename, site in filter(is_site_class, locals().items()):
	default = manager.UrlBase.getBaseName(site.controller["url"])
	basename = site.controller.get("basenames", default)	
	if type(basename) is list:
		for name in basename:
			register_site(name, site)
	else:
		register_site(basename, site)
#######################################################################################

if __name__ == "__main__":
	def checkSite(url="", proxies={}, timeout=30, **params):
		""" verifica se o site dado por 'baseName' está respondendo as requisições """
		baseName = manager.UrlManager.getBaseName( url )
		print "Checking: ", baseName

		videoControl = Universal.get_video_control(baseName)
		site = videoControl(url, **params)

		if site.getVideoInfo(1, proxies=proxies, timeout=timeout):
			print "Url: %s" % site.getLink()
			print "Size: %s" % site.getStreamSize()
			print "Title: %s" % site.getTitle()
			print "-"*25
			return True
		else:
			print "Msgerr: %s"%site.messagem
		print "-"*25
		return False
	# ----------------------------------------------
	proxyManager = manager.ProxyManager(None)

	for n in range(proxyManager.getNumIps()):
		proxies = proxyManager.proxyFormatado()
		print proxies["http"]
		proxies = {}

		if not checkSite("http://dwn.so/player/embed.php?v=DS4DDC9CDF&width=505&height=400", proxies=proxies, quality=3):
			proxyManager.setBadIp( proxies )

	del proxyManager