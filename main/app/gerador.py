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
# vers�o ser� mantida pelo m�dulo principal
PROGRAM_VERSION = manager.PROGRAM_VERSION
#######################################################################################

def DECODE(texto, alter="ISO-8859-1"):
	""" Tenta decodificar para utf-8. 
	Em caso de erro, a decodifica��o alternativa ser� usada """
	try:
		texto = texto.decode('utf-8')
	except UnicodeDecodeError:
		texto = texto.decode(alter)
	except Exception:
		pass
	return texto

def ENCODE(texto, alter="ISO-8859-1"):
	""" Tenta codificar para utf-8. 
	Em caso de erro, a codfica��o alternativa ser� usada """
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
	""" remove todos os carecteres considerados inv�lidos """
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
class Section(object):
	def __init__(self):
		self.section = {}
		
	def add(self, name):
		self.section[name] = {}
	
	def has(self, name):
		return self.section.has_key(name)
	
	def get(self, name):
		if not self.has(name): self.add(name)
		return self.section[name]
	
	def delete(self, name):
		self.section.pop(name,None)
		
	def __del__(self):
		del self.section
		
	def __delitem__(self, name):
		del self.section[name]
		
	def __getitem__(self, name):
		if not self.has(name): self.add(name)
		return self.section[name]
	
	def __setitem__(self, name, value):
		self.section[name] = value
		
class ConnectionProcessor(object):
	""" Processa conex�es guardando 'cookies' e dados por ips """
	def __init__(self):
		self.section = Section()
		self.logged = False
		
	def __del__(self):
		del self.section
		
	def set_cookiejar(self, section_name, cookieJar):
		section = self.section[ section_name ]
		section["cookieJar"] = cookieJar
		
	def has_cookieJar(self, section_name):
		section = self.section[ section_name ]
		return section.has_key("cookieJar")
		
	def get_cookieJar(self, section_name):
		section = self.section[ section_name ]
		return section["cookieJar"]
		
	def login(self, opener=None, timeout=0):
		""" struct login"""
		return True

	def get_request(self, url, headers, data):
		req = urllib2.Request(url, headers=headers, data=data)
		req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:11.0) Gecko/20100101 Firefox/11.0")
		req.add_header("Connection", "keep-alive")
		return req

	def connect(self, url="", headers={}, data=None, proxies={}, timeout=25, request=None, login=False):
		""" conecta a url data e retorna o objeto criado """
		ip = proxies.get("http", "default")

		if not self.has_cookieJar(ip): self.set_cookiejar(ip, cookielib.CookieJar())
		if request is None: request = self.get_request(url, headers, data)
		
		processor = urllib2.HTTPCookieProcessor(cookiejar= self.get_cookieJar( ip ))
		opener = urllib2.build_opener(processor, urllib2.ProxyHandler(proxies))
		
		# faz o login se necess�rio
		if not self.logged or login:
			self.logged = self.login(opener, timeout=timeout)
			if not self.logged: return
			
		return opener.open(request, timeout=timeout)

#################################### BASEVIDEOSITE ####################################
class SiteBase(ConnectionProcessor):
	MP4_HEADER = "\x00\x00\x00\x1cftypmp42\x00\x00\x00\x01isommp423gp5\x00\x00\x00*freevideo served by mod_h264_streaming"
	FLV_HEADER = "FLV\x01\x01\x00\x00\x00\t\x00\x00\x00\t"
	
	#----------------------------------------------------------------------
	def __init__(self, **params):
		ConnectionProcessor.__init__(self)
		self.url = self.basename = self.message = ""
		self.params = params
		self.streamSize = 0
		self.configs = {}
		self.headers = {}
		
	def __del__(self):
		del self.basename
		del self.params
		del self.configs
		del self.url
	
	def get_basename(self):
		return self.basename
	
	def __delitem__(self, arg):
		self.section.delete(arg)
		
	def get_message(self):
		return self.message

	def suportaSeekBar(self):
		return False
	
	def get_stream_header(self):
		if self.is_mp4(): header = self.MP4_HEADER
		else: header = self.FLV_HEADER
		return header
	
	def get_header_size(self):
		if self.is_mp4(): size = len(self.MP4_HEADER)
		else: size = len(self.FLV_HEADER)
		return size
	
	def get_video_id(self):
		""" retorna s� o id do video """
		return Universal.get_video_id(self.basename, self.url)
	
	def get_init_page(self, proxies={}, timeout=30):	
		assert self.getVideoInfo(proxies=proxies, timeout=timeout)

	def getVideoInfo(self, ntry=3, proxies={}, timeout=30):
		ip = proxies.get("http","default")
		section = self.section.get( ip )
		settings = section.get("settings",None)
		
		# extrai o titulo e o link do video, se j� n�o tiverem sido extraidos
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
				except Exception as err:
					pass
				nfalhas += 1
		else:
			self.configs = section["settings"] # transfere para vari�vel de trabalho

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
	
	def has_duration(self):
		return bool(self.configs.get("duration",None))
	
	def get_duration(self):
		return self.configs["duration"]
	
	def get_relative(self, pos):
		""" retorna o valor de pos em bytes relativo a dura��o em mp4 """
		if self.has_duration(): # if 'video/mp4' file
			try: result = float(self.get_duration()) * (float(pos)/self.getStreamSize())
			except: result = 0
		else: result = pos
		return result
	
	def get_relative_mp4(self, pos):
		if self.has_duration(): # if 'video/mp4' file
			try: result = (float(pos)/self.get_duration()) * self.getStreamSize()
			except: result = 0
		else: result = pos
		return result
	
	def is_mp4(self):
		return self.has_duration()
	
	def getVideoExt(self):
		return self.configs.get("ext","flv")

	def getTitle(self):
		""" pega o titulo do video """
		title = urllib.unquote_plus(self.configs["title"])
		title = DECODE(title) # decodifica o title
		# remove caracteres invalidos
		title = clearTitle(title)
		return limiteTexto(title)

	def get_size(self, proxies={}, timeout=60):
		""" retorna o tamanho do arquivo de v�deo, atrav�s do cabe�alho de resposta """
		link = get_with_seek(self.getLink(), 0)
		headers = {"Range": "bytes=0-"}
		headers.update( self.headers )
		req = self.get_request(link, headers, data=None)
		try:
			fd = self.connect(request = req, proxies=proxies, timeout=timeout)
			fd.close()
		except:
			fd = urllib.urlopen( link )
			fd.close()
		length = fd.headers.get("Content-Length", None)
		assert (length and (fd.code == 200 or fd.code == 206))
		return long(length)

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
		# convers�o da unidade para bytes
		bytes_size = float(size.replace(",",".")) * self.unidades[ unit.upper() ]
		return long( bytes_size )

	def start_extraction(self, proxies={}, timeout=25):
		""" extrai as informa��es necess�rias, para a transfer�cia do arquivo de video """
		url_id = Universal.get_video_id(self.basename, self.url)

		webPage = self.connect(self.url, proxies=proxies, timeout=timeout).read()

		# tamanho aproximado do arquivo
		self.streamSize = self.get_file_size( webPage )

		# nome do arquivo
		try: title = re.search("<title>(.*)</title>", webPage).group(1)
		except: title = get_radom_title()

		# extens�o do arquivo
		try: ext = self.matchFileExt.search(title).group(1)
		except: ext = "file"

		## {type:'download',url:'http://stor1074.uploaded.to/dl/46d975ec-a24e-4e88-a4c9-4000ce5bd1aa'}
		data = self.connect(self.captchaUrl%url_id, proxies=proxies, timeout=timeout).read()
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
		
	def getLink(self):
		vquality = int(self.params.get("qualidade", 2))
		optToNotFound = self.configs.get(1, None)
		optToNotFound = self.configs.get(2, optToNotFound)
		optToNotFound = self.configs.get(3, optToNotFound)
		videoLink = self.configs.get(vquality, optToNotFound)
		return videoLink
	
	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		
		url = "http://www.metacafe.com/watch/%s/" % video_id
		fd = self.connect( url, proxies=proxies, timeout=timeout)
		webpage = fd.read(); fd.close()
		
		matchobj = re.search("flashVarsCache\s*=\s*\{(.*?)\}", webpage)
		flashvars = urllib.unquote_plus(matchobj.group(1))
		
		matchobj = re.search("\"mediaData\".+?\"mediaURL\"\s*:\s*\"(.*?)\".*\"key\"\s*:\s*\"(.*?)\".*\"value\"\s*:\s*\"(.*?)\"", flashvars)
		lowMediaURL = urllib.unquote_plus(matchobj.group(1)) +"?%s=%s" % (matchobj.group(2), matchobj.group(3))
		lowMediaURL = lowMediaURL.replace("\/", "/")
		
		matchobj = re.search("\"highDefinitionMP4\".+?\"mediaURL\"\s*:\s*\"(.*?)\".*\"key\"\s*:\s*\"(.*?)\".*\"value\"\s*:\s*\"(.*?)\"", flashvars)
		highMediaURL = urllib.unquote_plus(matchobj.group(1)) +"?%s=%s" % (matchobj.group(2), matchobj.group(3))
		highMediaURL = highMediaURL.replace("\/", "/")
		
		try: title = re.search("<title>(.+)</title>", webpage).group(1)
		except: title = get_radom_title()
		
		self.configs = {1: lowMediaURL, 2: highMediaURL, 'title': title}

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
		except: return # falha obtendo a p�gian

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

			fd = self.connect(self.url, proxies=proxies, 
						      timeout=timeout, headers={'Cookie': 'family_filter=off'})
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a p�gina

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
			fd = self.connect(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a p�gina

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
			fd = self.connect(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a p�gina

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
		self.raw_data = None
		self.url = url
		
	def suportaSeekBar(self):
		return True
	
	def getMessage(self):
		try:
			if self.raw_data.get("status",[""])[0] == "fail":
				reason = self.raw_data.get("reason",[""])[0]
				msg = u"%s informa: %s"%(self.basename, unicode(reason,"UTF-8"))
			else: msg = ""
		except: msg = ""
		return msg
	
	def getLink(self):
		default_url = ""
		vquality = self.params.get("qualidade", 2)
		quality_opt = self.video_quality_opts[ vquality ]
		
		for index, _type in enumerate( self.raw_data["type"] ):
			quality = self.raw_data['quality'][index]
			url = self.configs["urls"][index]
			
			matchobj = re.search("video/([^\s;]+)", _type)
			if matchobj: self.configs["ext"] = matchobj.group(1)
			
			# o formato video/webm, mostra-se impat�vel como o swf player
			if re.match(quality_opt, quality):
				if not re.match("video/webm", _type):
					return urllib.unquote_plus( url )+"&range=%s-"
			elif not default_url:
				default_url = urllib.unquote_plus( url )+"&range=%s-"
		return default_url
		
	def get_raw_data(self, proxies, timeout):
		video_id = Universal.get_video_id(self.basename, self.url)
		url = self.info_url % video_id
		fd = self.connect(url, proxies=proxies, timeout=timeout)
		data = fd.read(); fd.close()
		return cgi.parse_qs( data )
	
	def start_extraction(self, proxies={}, timeout=25):
		self.raw_data = self.get_raw_data(proxies, timeout)
		self.message = self.getMessage()
		
		uparams = cgi.parse_qs(self.raw_data["url_encoded_fmt_stream_map"][0])
		self.raw_data["quality"] = uparams["quality"]
		self.raw_data["type"] = uparams["type"]
		self.configs["urls"] = []
		
		for index, url in enumerate(uparams["url"]):
			fullurl = url + "&signature=%s" %uparams["sig"][index]
			self.configs["urls"].append( fullurl )
			
		try: self.configs["title"] = self.raw_data["title"][0]
		except (KeyError, IndexError):
			self.configs["title"] = get_radom_title()
			
		try: self.configs["thumbnail_url"] = self.raw_data["thumbnail_url"][0]
		except (KeyError, IndexError):
			self.configs["thumbnail_url"] = ""
		
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

			fd = self.connect(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a p�gina

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

			fd = self.connect(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a p�gina

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
			fd = self.connect(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a p�gina

		m = re.search(r'id="video:(?P<internalvideoid>[0-9]+)"', webpage)
		if m is None: return

		internal_video_id = m.group('internalvideoid')

		info = {'id': video_id, 'internal_id': internal_video_id}
		xmlUrl = 'http://www.collegehumor.com/moogaloop/video:' + internal_video_id
		try:
			fd = self.connect(xmlUrl, proxies=proxies, timeout=timeout)
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
class Videomega( SiteBase ):
	## http://videomega.tv/iframe.php?ref=OEKgdSTMGQ&width=505&height=4
	controller = {
	    "url": "http://videomega.tv/iframe.php?ref=%s", 
	    "patterns": [re.compile("(?P<inner_url>http://videomega\.tv/iframe\.php\?ref=(?P<id>\w+)(?:&width=\d+)?(&height=\d+)?)")], 
	    "control": "SM_RANGE", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.url = url
		
	def suportaSeekBar(self):
		return True
	
	def start_extraction(self, proxies={}, timeout=25):
		fd = self.connect(self.url, proxies=proxies, timeout=timeout)	
		webpage = fd.read(); fd.close()
		
		matchobj = re.search("unescape\s*\((?:\"|')(.+)(?:\"|')\)", webpage)
		settings = urllib.unquote_plus( matchobj.group(1) )
		
		matchobj = re.search("file\s*:\s*(?:\"|')(.+?)(?:\"|')", settings)
		url = matchobj.group(1)
		
		try: title = re.search("<title>(.+)</title>", webpage).group(1)
		except: title = get_radom_title()
		
		self.configs = {"url": url+"&start=", "title": title}
	
###################################### MEGAPORN #######################################
class MegaPorn( Videomega ):
	controller = {
	    "url": "http://www.megaporn.com/video/?v=%s", 
	    "patterns": re.compile("(?P<inner_url>(?:http://)?www\.(?:megaporn|cum)?\.com/video/\?v=(?P<id>\w+))"), 
	    "control": "SM_SEEK", 
	    "video_control": None
	}
	
	def __init__(self, url, **params):
		super(MegaPorn, self).__init__(url, **params)
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
		""" Faz a convers�o da url antiga e inv�lida, para a mais nova. """
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

		fd = self.connect(url, proxies=proxies, timeout=timeout)
		data = fd.read(); fd.close()

		params = json.loads(data)

		try: # urls normais - formato antigo
			urls = self.get_urls(params)
			self.configs["token1"] = urls["token1"]
		except: pass

		# urls com n�vel de resu��o
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
		self.url = url
		
	def getPostData(self, webpage=""):
		""" extrai informa��es da p�gina de login para o post """
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
		""" faz o login necess�rio para transferir o arquivo de v�deo.
		opener � quem armazer� o cookie """
		try:
			url = "http://www.mixturecloud.com/login"
			response = opener.open(url, timeout=timeout)
			loginPage = response.read()
			response.close()

			# dados do m�todo post
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
			# usa um titulo gerado de caracteres aleat�rios
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
		
		fd = self.connect(url, proxies=proxies, timeout=timeout, login=True)
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
			fd = self.connect(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha ao obter p�gina

		try:
			self.configs["title"] = re.search("<title.*>(.+?)</title>", webpage).group(1)
		except:
			try: self.configs["title"] = re.search("<meta name=\"title\" content=\"(.+?)\"\s*/>", webpage).group(1)
			except: self.configs["title"] = get_radom_title() # usa um titulo gerado de caracteres aleat�rios

		# o link est� dentro de <iframe>
		## playerUrl = re.search('(?:<iframe)?.+?src="(.+?frame\.php\?v=.+?)"', webpage).group(1)
		playerUrl = "http://www.modovideo.com/frame.php?v=%s"%video_id
		fd = self.connect(playerUrl, proxies=proxies, timeout=timeout)
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
		# link direto para o site(n�o embutido)
		self.siteVideoLink = "http://www.videoweed.es/file/%s"
		# parte principal da url usada como elemento chave no programa
		self.basename = manager.UrlManager.getBaseName( url )
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

			fd = self.connect(url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a p�gina

		## flashvars.filekey="189.24.243.113-505db61fc331db7a2a7fa91afb22e74d-"
		matchobj = re.search('flashvars\.filekey="(.+?)"', webpage)
		filekey = matchobj.group(1)

		try:
			url = self.player_api % (filekey, url_id) # ip; id
			fd = self.connect(url, proxies=proxies, timeout=timeout)
			info_data = fd.read(); fd.close()
		except: return # falha obtendo a p�gina

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
	""" Novamov: segue a mesma sequ�ncia l�gica de Videoweed """
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
		# objetos de Videoweed n�o anulados nessa inicializa��o,
		# ser�o considerados objetos v�lidos para novos objetos de Novamov.
		Videoweed.__init__(self, url, **params)
		self.player_api = "http://www.novamov.com/api/player.api.php?key=%s&user=undefined&codes=1&pass=undefined&file=%s"
		# link direto para o site(n�o embutido)
		self.siteVideoLink = "http://www.novamov.com/video/%s"		
		# parte principal da url usada como elemento chave no programa
		self.basename = manager.UrlManager.getBaseName( url )
		self.url = url

####################################### NOVAMOV #######################################
class NowVideo( Videoweed ):
	""" Novamov: segue a mesma sequ�ncia l�gica de Videoweed """
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
		# objetos de Videoweed n�o anulados nessa inicializa��o,
		# ser�o considerados objetos v�lidos para novos objetos de Novamov.
		Videoweed.__init__(self, url, **params)
		self.player_api = "http://www.nowvideo.eu/api/player.api.php?key=%s&user=undefined&codes=1&pass=undefined&file=%s"
		# link direto para o site(n�o embutido)
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
		self.basename = "veevr.com"
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		try:
			# p�gina web inicial
			fd = self.connect(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()
		except: return # falha obtendo a p�gina

		try:
			patternUrl = "http://mps.hwcdn.net/.+?/ads/videos/download.+?"
			matchobj = re.search(
				"playlist:.+?url:\s*(?:'|\")(%s)(?:'|\")"%patternUrl, 
				webpage, re.DOTALL|re.IGNORECASE
			)
			# url final para o v�deo ?
			mediaUrl = urllib.unquote_plus( matchobj.group(1) )
		except Exception, err:
			matchobj = re.search(
				"playlist:.+url:\s*(?:'|\")(http://hwcdn.net/.+/cds/.+?token=.+?)(?:'|\")", 
				webpage, re.DOTALL|re.IGNORECASE )

			# url final para o v�deo
			mediaUrl = matchobj.group(1)
			mediaUrl = urllib.unquote_plus( mediaUrl )

		# iniciando a extra��o do t�tulo do v�deo
		try:
			matchobj = re.search("property=\"og:title\" content=\"(.+?)\"", webpage)
			title = matchobj.group(1)
		except:
			try:
				matchobj = re.search("property=\"og:description\" content=\"(.+?)\"", webpage)
				title = matchobj.group(1)[:25] # apenas parte da descri��o ser� usada							
			except:
				# usa um titulo gerado de caracteres aleat�rios
				title = get_radom_title()

		ext = "mp4" # extens�o padr�o

		if re.match(".+/Manifest\.", mediaUrl):
			fd = self.connect(mediaUrl, proxies=proxies, timeout=timeout)
			xmlData = fd.read(); fd.close()

			# documento xml
			mdoc = xml.etree.ElementTree.fromstring( xmlData )

			# url final para o v�deo
			media = mdoc.find("{http://ns.adobe.com/f4m/1.0}media")
			mediaUrl = media.attrib["url"] + "Seg1-Frag1"

			try:
				mimeType = mdoc.find("{http://ns.adobe.com/f4m/1.0}mimeType")
				ext = mimeType.text.split("/", 1)[-1] # extens�o representada pelo texto da tag
			except:pass # em caso de erro, usa a extes�o padr�o

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
		SiteBase.__init__(self, **params)
		self.getFileBaseUrl = "http://www.putlocker.com"
		self.basename = "putlocker.com"
		self.url = url

	def suportaSeekBar(self):
		return True
	
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
		# p�gina web inicial
		url = self.url.replace("/embed","/file")
		fd = self.connect(url, proxies=proxies, timeout=timeout)
		webpage = fd.read(); fd.close()

		# messagem de erro. se houver alguma
		self.message = self.getMessage( webpage )

		# padr�o captua de dados
		matchobj = self.patternForm.search( webpage )
		hashvalue =  matchobj.group("hash") or  matchobj.group("_hash")
		hashname = matchobj.group("name") or  matchobj.group("_name")
		confirmvalue = matchobj.group("confirm")

		data = urllib.urlencode({hashname: hashvalue, "confirm": confirmvalue})
		fd = self.connect(url, proxies=proxies, timeout=timeout, data=data)
		webpage = fd.read(); fd.close()

		# extraindo o titulo.
		try: title = re.search("<title>(.*?)</title>", webpage).group(1)
		except: title = get_radom_title()

		# come�a a extra��o do link v�deo.
		## playlist: '/get_file.php?stream=WyJORVE0TkRjek5FUkdPRFJETkRKR05Eb3',
		pattern = "playlist:\s*(?:'|\")(/get_file\.php\?stream=.+?)(?:'|\")"
		matchobj = re.search(pattern, webpage, re.DOTALL|re.IGNORECASE)
		url = self.getFileBaseUrl + matchobj.group(1)
		
		# come�a a an�lize do xml
		fd = self.connect(url, proxies=proxies, timeout=timeout)
		rssData = fd.read(); fd.close()

		ext = "flv" # extens�o padr�o.
		## print rssData
		
		# url do video.
		url = re.search("<media:content url=\"(.+?)\"", rssData).group(1)
		url = self.unescape( url ).replace("'","").replace('"',"")
		
		try: ext = re.search("type=\"video/([\w-]+)", rssData).group(1)
		except: pass # usa a extens�o padr�o.
		
		self.configs = {"url": url+"&start=", "title":title, "ext": ext}

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
		self.basename = "moviezer.com"
		self.url = url

	def suportaSeekBar(self):
		return True

	def start_extraction(self, proxies={}, timeout=25):
		try:
			fd = self.connect(self.url, proxies=proxies, timeout=timeout)
			webpage = fd.read(); fd.close()

			matchobj = re.search("flashvars\s*=\s*\{.*?'file':\s*'(?P<url>.*?)'", webpage, re.DOTALL)
			url = matchobj.group("url")
		except: return # falha em obter a p�gina

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

			fd = self.connect(self.apiUrl, proxies=proxies, timeout=timeout, data=postdata)
			webdata = fd.read(); fd.close()

			videoinfo = json.loads( webdata)
			url = self.extratcLink( videoinfo)
		except: return # falha obtendo a p�gina

		try:
			self.setErrorMessage(url, videoinfo)
		except:pass

		# obtendo o t�tulo do video
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
		self.url = url

	def suportaSeekBar(self):
		return True

	def start_extraction(self, proxies={}, timeout=25):
		fd = self.connect(self.url, proxies=proxies, timeout=timeout)
		webdata = fd.read(); fd.close()
		
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
		fd = self.connect(url, proxies=proxies, timeout=timeout)
		xmldata = fd.read(); fd.close()

		if not re.match("http://www.anitube\.jp/nuevo/playlist\.php", url):
			play_url = re.search("<playlist>(.*?)</playlist>", xmldata).group(1)
			fd = self.connect(play_url, proxies=proxies, timeout=timeout)
			xmldata = fd.read(); fd.close()

		video_url = re.search("<file>(.*?)</file>", xmldata).group(1)

		try: title = re.search("<title>(.*?)</title>", xmldata).group(1)
		except: title = get_radom_title()

		self.configs = {"url": video_url+"?start=", "title": title}

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
	    "control": "SM_RANGE",
	    "video_control": None
	}

	def __init__(self, url, **params):
		"""Constructor"""
		SiteBase.__init__(self, **params)
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
		## http://cs519609.userapi.com/u165193745/video/7cad4a848e.360.mp4
		fd = self.connect(self.url, proxies=proxies, timeout=timeout)
		webdata = fd.read(); fd.close()
		params = {}
		try:
			mathobj = re.search("var\s*video_host\s*=\s*'(?P<url>.+?)'", webdata, re.DOTALL)
			params["url"] = mathobj.group("url")
			
			mathobj = re.search("var\s*video_uid\s*=\s*'(?P<uid>.+?)'", webdata, re.DOTALL)
			params["uid"] = mathobj.group("uid")
	
			mathobj = re.search("var\s*video_vtag\s*=\s*'(?P<vtag>.+?)'", webdata, re.DOTALL)
			params["vtag"] = mathobj.group("vtag")
	
			mathobj = re.search("var\s*video_max_hd\s*=\s*(?:')?(?P<max_hd>.+?)(?:')?", webdata, re.DOTALL)
			params["max_hd"] = mathobj.group("max_hd")
	
			mathobj = re.search("var\s*video_no_flv\s*=\s*(?:')?(?P<no_flv>.+?)(?:')?", webdata, re.DOTALL)
			params["no_flv"] = mathobj.group("no_flv")
		except:
			matchobj = re.search("var\s*vars\s*=\s*{(?P<vars>.+?)}", webdata, re.DOTALL)
			raw_params = matchobj.group("vars").replace(r'\"', '"')
			params = dict([(a, (b or c)) for a,b,c in re.findall('"(.+?)"\s*:\s*(?:"(.*?)"|(-?\d*))',raw_params)])
			params["url"] = "http://cs%s.vk.com" % params.pop("host")
			
		try: title = re.search("<title>(.+?)</title>", webdata).group(1)
		except: title = get_radom_title()
		
		if int(params.get("no_flv",0)):
			baseUrl = params["url"] + "/u%s/video/%s.{res}.mp4"%(params["uid"], params["vtag"])
			url_hd240 = baseUrl.format(res = 240)
			url_hd360 = baseUrl.format(res = 360)
			ext = "mp4"
		else:
			url_hd240 = url_hd360 = params["url"] + "u%s/video/%s.flv"%(params["uid"], params["vtag"])
			ext = "flv"
			
		self.configs = {1: url_hd240, 2: url_hd360, "title": title, "ext": ext}
		
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
		self.url = url

	def suportaSeekBar(self):
		return True

	def start_extraction(self, proxies={}, timeout=25):
		try:
			fd = self.connect(self.url, proxies=proxies, timeout=timeout)
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
		self.url = url

	def suportaSeekBar(self):
		return True

	def start_extraction(self, proxies={}, timeout=25):
		try:
			fd = self.connect(self.url, proxies=proxies, timeout=timeout)
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
		self.url = url
		
	def suportaSeekBar(self):
		return True

	def start_extraction(self, proxies={}, timeout=25):
		fd = self.connect(self.url, proxies=proxies, timeout=timeout)
		webpage = fd.read(); fd.close()
		try:
			fs = ""
			matchobj = re.search('''(?:"|')video_url(?:"|')\s*:\s*(?:"|')(.+?)(?:"|')''', webpage, re.DOTALL)
			try: url = base64.b64decode(urllib.unquote_plus(matchobj.group(1)))
			except: url = urllib.unquote_plus(matchobj.group(1))
			
			matchobj = re.search('''(?:"|')video_title(?:"|')\s*:\s*(?:"|')(.*?)(?:"|')''', webpage, re.DOTALL)
			try: title = urllib.unquote_plus( matchobj.group(1) )
			except: title = get_radom_title()
		except:
			urlid = Universal.get_video_id(self.basename, self.url)
			fd = self.connect(self.apiUrl % urlid, proxies=proxies, timeout=timeout)
			xmlData = fd.read(); fd.close()
			
			url = re.search("""<video_url><!\[CDATA\[(.+)\]\]></video_url>""", xmlData).group(1)

			try: title = re.search("<video_title>(.*)</video_title>", xmlData).group(1)
			except: title = get_radom_title()
			
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
		self.basename = "dwn.so"
		self.url = url
	
	def suportaSeekBar(self):
		return True
	
	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		for videlink in self.videolink:
			try:
				fd = self.connect(videlink % video_id, proxies=proxies, timeout=timeout)
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
	## http://hostingbulk.com/d74oyrowf9p6.html
	controller = {
		"url": "http://hostingbulk.com/%s.html", 
		"patterns": (
	         re.compile("(?P<inner_url>http://hostingbulk\.com/(?P<id>\w+)\.html)"),
		    [re.compile("(?P<inner_url>http://hostingbulk\.com/embed\-?(?P<id>\w+)\-?(?:\d+x\d+)?\.html)")]
	    ),
		"control": "SM_SEEK",
		"video_control": None
	}
	def suportaSeekBar(self):
		return True
	
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
		self.url = url

	def start_extraction(self, proxies={}, timeout=25):
		video_id = Universal.get_video_id(self.basename, self.url)
		url = self.controller["url"] % video_id

		fd = self.connect(url, proxies=proxies, timeout=timeout)
		webpage = fd.read(); fd.close()

		matchobj = re.search("eval\(\s*function\s*\(.*\)\s*{.*?}\s*(.+)\)", webpage)
		if matchobj:
			params = matchobj.group(1)
			
			matchobj = re.search("'(?P<ps>(.+?))'\s*,\s*(?P<n1>\d+?),\s*(?P<n2>\d+?),\s*'(?P<lps>.+?)\.split.+", params)
			uparams = self.unpack_params( matchobj.group("ps"), int(matchobj.group("n1")), int(matchobj.group("n2")), matchobj.group("lps").split("|"))
			
			url = re.search("'file'\s*,\s*'(.+?)'", uparams).group(1)
			pattern = "(http://.+?)//"; search = re.search(pattern, url)
			if search: url = re.sub(pattern, search.group(1)+"/d/", url)
		else:
			matchobj = re.search("setup\(\{.*?(?:'|\")file(?:'|\")\s*:\s*(?:'|\")(.+?)(?:'|\")", webpage, re.DOTALL)
			url = matchobj.group(1)
			try:
				matchobj = re.search("setup\(\{.*?(?:'|\")duration(?:'|\")\s*:\s*(?:'|\")(.+?)(?:'|\")", webpage, re.DOTALL)
				duration = int(matchobj.group(1))
			except:
				duration = None
		
		try: title = re.search("<title>(.+)</title>", webpage).group(1)
		except: title = get_radom_title()
		
		self.configs = {"url": url+"?start=", "title": title, "duration": duration}

########################################################################
class Videoslasher( SiteBase ):
	##<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
	##<channel><item><title>Preview</title>
	##<media:content url="http://www.videoslasher.com/static/img/previews/3/37/370f254c0be38819213191232e528d78.jpg" type="image/jpeg">
	##</media:content></item><item><title>Video</title><link>http://www.videoslasher.com/video/6O9TSHUUR4UY</link>
	##<media:content url="http://proxy1.videoslasher.com/free/6/6O/6O9TSHUUR4UY.flv?h=ih4mBk-jPyXCEJ-aaDaY3g&e=1344819603" type="video/x-flv"  duration="5269" />
	##</item></channel></rss>
	
	## http://www.videoslasher.com/video/6O9TSHUUR4UY == http://www.videoslasher.com/embed/6O9TSHUUR4UY
	controller = {
		"url": "http://www.videoslasher.com/video/%s", 
		"patterns": (
	        re.compile("(?P<inner_url>http://www\.videoslasher\.com/video/(?P<id>\w+))"),
	        [re.compile("(?P<inner_url>http://www\.videoslasher\.com/embed/(?P<id>\w+))")]
	    ),
		"control": "SM_SEEK",
		"video_control": None
	}
	domain =  "http://www.videoslasher.com"
	#----------------------------------------------------------------------
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "videoslasher.com"
		self.url = url
	
	def suportaSeekBar(self):
		return True
	
	def postPage(self, webpage, proxies, timeout):
		matchobj = PutLocker.patternForm.search( webpage )
		hashvalue =  matchobj.group("hash") or  matchobj.group("_hash")
		hashname = matchobj.group("name") or  matchobj.group("_name")
		confirmvalue = matchobj.group("confirm")
		
		data = urllib.urlencode({hashname: hashvalue, "confirm": confirmvalue})
		fd = self.connect(self.url, proxies=proxies, timeout=timeout, data=data)
		webpage = fd.read(); fd.close()
		return webpage
	
	def start_extraction(self, proxies={}, timeout=25):
		fd = self.connect(self.url, proxies=proxies, timeout=timeout)
		firstWebpage = fd.read(); fd.close()
		
		try: webpage = self.postPage(firstWebpage, proxies, timeout)
		except: webpage = firstWebpage
		
		matchobj = re.search("""playlist:\s*(?:'|")(/playlist/\w+)(?:'|")""", webpage, re.DOTALL)
		playlistUrl = matchobj.group(1)
		
		if not playlistUrl.endswith('/'):
			playlistUrl += '/'
		
		fd = self.connect(self.domain + playlistUrl, proxies=proxies, timeout=timeout)
		rssData = fd.read(); fd.close()
		
		for item in re.findall("<item>(.+?)</item>", rssData, re.DOTALL):
			matchobj = re.search('''\<media:content\s*url\s*=\s*"(.+?)"\s*type="video.+?"''', item, re.DOTALL)
			if matchobj:
				url = matchobj.group(1)
				break
		else:
			raise Exception
		
		try: title = re.search("<title>(.+?)</title>", webpage, re.DOTALL).group(1)
		except: title = get_radom_title()
		
		self.configs = {"url": url+"&start=", "title": title}

class Supervideo(SiteBase):
	# http://supervideo.biz/embed-duzx1non5fch-518x392.html
	
	controller = {
		"url": "http://supervideo.biz/%s", 
		"patterns": (
	        [re.compile("(?P<inner_url>http://supervideo\.biz/(?P<id>.+))")],
	    ),
		"control": "SM_RANGE",
		"video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "supervideo.biz"
		self.url = url
	
	def start_extraction(self, proxies={}, timeout=25):
		fd = self.connect(self.url, proxies=proxies, timeout=timeout)
		webpage = fd.read(); fd.close()
		
		matchobj = re.search("file\s*:\s*\"(.+?)\"", webpage, re.DOTALL)
		url = matchobj.group(1)
		
		matchobj = re.search("duration\s*:\s*\"(\d*?)\"", webpage, re.DOTALL)
		try: duration = int(matchobj.group(1))
		except: duration = None
		
		try: title = re.search("<title>(.+?)</title>", webpage, re.DOTALL).group(1)
		except: title = get_radom_title()
		
		self.configs = {"url": url+"&start=", "title": title, "duration": duration}
		
class Videobash(SiteBase):
	# www.videobash.com/embed/NDMwMzU5
	# http://www.videobash.com/video_show/acirc-thriller-acirc-halloween-light-show-6225
	
	controller = {
		"url": "http://www.videobash.com/%s", 
		"patterns": (
			re.compile("(?P<inner_url>http://www\.videobash\.com/(?P<id>.+))"),
	        [re.compile("(?P<inner_url>http://www\.videobash\.com/(embed/?P<id>.+))")],
	    ),
		"control": "SM_RANGE",
		"video_control": None
	}
	
	def __init__(self, url, **params):
		SiteBase.__init__(self, **params)
		self.basename = "videobash.com"
		self.url = url
		
	def start_extraction(self, proxies={}, timeout=25):
		fd = self.connect(self.url, proxies=proxies, timeout=timeout)
		webpage = fd.read(); fd.close()
		
		matchobj = re.search("flashvars\s*\+=\s*(?:\"|').*?file=(?:\"|')\s*\+?\s*(?:\"|')(?:http://)?(?:\"|')\s*\+?\s*(?:\"|')(.+?)(?:\"|')", webpage, re.DOTALL)
		raw_url = matchobj.group(1)
		if not raw_url.startswith("http://"):
			url = "http://" + raw_url
		else:
			url = raw_url
		matchobj = re.search("duration\s*(?:=|:)\s*(\d+)", webpage, re.DOTALL)
		try: duration = int(matchobj.group(1))
		except: duration = None
		
		try: title = re.search("<title>(.+?)</title>", webpage, re.DOTALL).group(1)
		except: title = get_radom_title()
		
		self.configs = {"url": url, "title": title, "duration": duration}	
		
#######################################################################################
class Universal(object):
	"""A classe Universal, quarda varias informa��es e dados usados em
	toda a extens�o do programa. Ela � usada para diminuir o n�mero de modifica��es
	necess�rias, quando adiciando suporte a um novo site v�deo.
	"""
	
	sites = {}
	
	@staticmethod
	def SM_SEEK(*args, **kwargs):
		return manager.StreamManager(*args, **kwargs)
	
	@staticmethod
	def SM_RANGE(*args, **kwargs):
		return manager.StreamManager_(*args, **kwargs)
		
	@classmethod
	def get_sites(cls):
		return cls.sites.keys()
	
	@classmethod
	def add_site(cls, basename="", args=None, **kwargs):
		""" adiciona as refer�ncias para um novo site """
		if args:
			url, patterns, control, video_control = args
			
			cls.sites[ basename ] = {
				"video_control": video_control,
				"control": control,
				"patterns": patterns,
				"url": url,
			}
		elif kwargs:
			cls.sites.update({ 
				basename: kwargs 
			})

	@classmethod
	def get_video_id(cls, sitename, url):
		""" retorna o id da url """
		matchobj = cls.patternMatch(sitename, url)
		return matchobj.group("id")
	
	@classmethod
	def getStreamManager(cls, url):
		""" Procura pelo controlador de tranfer�nicia de arquivo de video"""
		smanager = None
		try:
			for sitename in cls.get_sites():
				matchobj = cls.patternMatch(sitename, url)
				if matchobj:
					smanager = cls.get_control( sitename)
					break
		except AssertionError as err:
			raise AttributeError, _("Sem suporte para a url fornecida.")
		assert smanager, _("url desconhecida!")
		return smanager

	@classmethod
	def getVideoManager(cls, url):
		""" Procura pelo controlador de video baseado na url dada """
		vmanager = None
		try:
			for sitename in cls.get_sites():
				matchobj = cls.patternMatch(sitename, url)
				if matchobj:
					vmanager = cls.get_video_control( sitename )
					break
		except AssertionError as err:
			raise AttributeError, _("Sem suporte para a url fornecida.")
		assert vmanager, _("url desconhecida!")
		return vmanager
	
	@classmethod
	def get_patterns(cls, sitename, validar=True):
		if validar: cls.valide(sitename, "patterns")
		return cls.sites[ sitename ]["patterns"]

	@classmethod
	def patternMatch(cls, sitename, url):
		""" analiza se a url casa o padr�o de urls.
		Duas situa��es s�o possiveis:
			A url � �nica; A url est� dentro de outra url.
		"""
		patterns = cls.get_patterns(sitename)
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

	@classmethod
	def isEmbed(cls, url):
		""" analiza se a url � de um player embutido """
		sitename = manager.UrlManager.getBaseName(url)
		patterns = cls.get_patterns(sitename)
		siteAttrs = cls.sites[sitename]
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

	@classmethod
	def get_url(cls, sitename, validar=True):
		if validar: cls.valide(sitename, "url")
		return cls.sites[ sitename ]["url"]

	@classmethod
	def get_control(cls, sitename, validar=True):
		if validar: cls.valide(sitename, "control")
		return cls.sites[ sitename ]["control"]

	@classmethod
	def get_video_control(cls, sitename, validar=True):
		if validar: cls.valide(sitename, "video_control")
		return cls.sites[ sitename ]["video_control"]

	@classmethod
	def valide(cls, sitename, obj):
		assert bool(cls.sites.get(sitename, None)), u"Site %s n�o encontrado"%sitename
		if obj == "patterns":
			assert bool(cls.sites[sitename].get("patterns", None)), u"Padr�o n�o definido para %s"%sitename
		elif obj == "url":
			assert bool(cls.sites[sitename].get("url", None)), u"Url n�o definida para %s"%sitename
		elif obj == "control":
			assert bool(cls.sites[sitename].get("control", None)), u"Controlador n�o definido para %s"%sitename
		elif obj == "video_control":
			assert bool(cls.sites[sitename].get("video_control", None)), u"Controlador de video n�o definido para %s"%sitename

#######################################################################################
def is_site_class( item ):
	""" retorna s� os site devidamente configurados """
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
	
	