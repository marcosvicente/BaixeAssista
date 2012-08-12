# -*- coding: ISO-8859-1 -*-
## guarda a versão do programa.
PROGRAM_VERSION = "0.2.0"
PROGRAM_SYSTEM = {"Windows": "oswin", "Linux": "oslinux"}

import sys
import sha
import os
import re
import time
import zipfile
import math
import platform
import socket
import urllib2
import thread
import cPickle
import urlparse
import tempfile
import threading
import configobj
import subprocess
import SocketServer
import unicodedata
import sqlite3
import base64
import select

from main import settings
from main.app import models # modelo de banco de dados

# INTERNACIONALIZATION
def installTranslation(configs = None):
	""" instala as traduções apartir do arquivo de configurações. """
	if not isinstance(configs, configobj.ConfigObj):
		try:
			path = os.path.join(settings.CONFIGS_DIR, "configs.cfg")
			configs = configobj.ConfigObj( path )
		except:
			configs = {}
	try: import gettext
	except ImportError, err:
		print "Error[import gettext] %s"%err
		raise err
	
	menus = configs.get("Menus", {})
	lang = menus.get("language", "en")
	
	localepath = os.path.join(settings.APPDIR, "locale")
	language = gettext.translation("ba_trans", localepath, languages=[lang])
	
	# instala no espaço de nomes embutidos
	language.install(unicode=True)
#######################################################################################

def get_filename(filepath, fullname=True):
	""" fullname = (True | False) - C:\\dirfile\\arquivo.txt -> (arquivo.txt | arquivo) """
	filename = filepath.rsplit(os.sep,1)[-1]
	if not fullname: filename = filename.rsplit(".",1)[0]
	return filename

def security_save(filepath, _configobj=None, _list=None, newline="\n"):
	""" salva as configurações da forma mais segura possível. 
	filepath - local para salvar o arquivo
	_configobj - dicionário de configurações
	_list - salva a lista, aplicando ou não a newline.
	newline='' - caso não haja interesse na adição de uma nova linha.
	"""
	try: # criando o caminho para o arquivo de backup
		filename = get_filename( filepath ) # nome do arquivo no path.
		backFilePath = filepath.replace(filename, ("_"+filename))
	except Exception, err:
		try: print "Error[security_save:backfilename] %s"%err
		except: pass
		return False
	######
	# guarda o arquivo antigo temporariamente
	if os.path.exists(filepath):
		try: os.rename(filepath, backFilePath)
		except Exception, err:
			try: print "Error[security_save:rename-backfile] %s"%err
			except: pass
			try:
				os.remove(backFilePath); os.rename(filepath,backFilePath)
			except Exception, err:
				try: print "Error[security_save:remove-backfile] %s"%err
				except: pass
				return False
	######
	try: # começa a criação do novo arquivo de configuração
		with open(filepath, "w") as configsfile:
			if type(_list) is list:
				for data in _list:
					configsfile.write("%s%s"%(data, newline))
			elif isinstance(_configobj, configobj.ConfigObj):
				_configobj.write( configsfile )
			# levanta a exeção com o objetivo de recuperar o arquivo original
			else: raise AttributeError, "invalid attribute" 

			if os.path.exists(filepath):
				try: os.remove(backFilePath)
				except: pass
	except Exception, err:
		try: print "Error[security_save:saving-configs] %s"%err
		except: pass
		# remove o arquivo atual do erro.
		if os.path.exists(filepath):
			try: os.remove(filepath)
			except: pass
		# restaura o arquivo original
		if not os.path.exists(filepath):
			try: os.rename(backFilePath, filepath)
			except: pass
		return False
	return True

class GlobalInfo:
	""" Guarda informações de estado de outros objetos.
	O objetivo é criar um meio fácil de obter informações de objetos, no escopo
	global, sem precisar ficar acessando o objeto diretamento """

	def __init__(self):
		self.info = {}

	def add_info(self, keyRoot):
		self.info[ keyRoot ] = {}

	def del_info(self, keyRoot):
		if self.info.has_key( keyRoot ):
			del self.info[ keyRoot ]
		return self.info.get(keyRoot, False)

	def get_info(self, keyRoot, keyInfo):
		return self.info.get(keyRoot, {}).get(keyInfo, "")

	def set_info(self, keyRoot, keyInfo, valueInfo):
		self.info[ keyRoot ][ keyInfo ] = valueInfo

globalInfo = GlobalInfo()

########################################################################
class SqliteOperation:
	""" Executa operações de inserção, recuperação, atualização e remoção de dados, baco de dados sqlite3"""
	#----------------------------------------------------------------------
	def __init__(self, **params):
		"""params={}
		tablename: nome da tabela no banco de dados
		fieldsnames: nomes dos campos da tabela
		databasepath: caminho do bando de dados """
		self.params = params

		assert params.get("tablename",None), u"nome da tabela está vazio!"
		assert params.get("fieldsnames",None), u"nenhum nome de campo fornecido!"

		# se um caminho não for dado, usa o de desenvolvimento.
		dbpath = params.get("databasepath", os.path.join(settings.APPDIR, "configs", "database", "baixeassista.db"))
		self.params["databasepath"] = dbpath

		self._create_table()

	def __getitem__(self, key):
		return self.params[key]

	def connect(self):
		self.database = sqlite3.connect(self.params["databasepath"], detect_types=sqlite3.PARSE_DECLTYPES)
		self.database.row_factory = sqlite3.Row # key words suport
		return self.database

	def execute(self, operation, fieldsvalues=[]):
		cursor = self.connect()
		if fieldsvalues: exc = cursor.execute(operation, fieldsvalues)
		else: exc = cursor.execute(operation)
		return exc

	def _create_table(self, tablename="", fieldsnames=[]):
		""" cria uma nova tabela, com o nome dado na inicialização, se ele ainda não existir. """
		fieldsnames = ", ".join( self.params["fieldsnames"] )
		operation = "CREATE TABLE IF NOT EXISTS %s(id INTEGER PRIMARY KEY AUTOINCREMENT, %s)"%(self.params["tablename"], fieldsnames)
		self.execute(operation)
		self.close()

	def filter(self, sqlstr="", **kwargs):
		""" filtra e retorna os valores. kwargs: filter name, fields """
		fields = kwargs.pop("fields", tuple())
		fields = ", ".join( fields ) or "*" # all fields
		filter_by = " and ".join(["%s=\"%s\""%(k, v) for k, v in kwargs.iteritems()])
		operation = "SELECT %s FROM %s WHERE %s %s"%(fields, self.params["tablename"], filter_by, sqlstr)
		return self.execute( operation )

	def get_all(self, sqlstr=""):
		""" retorna todos os valores dos campos da tabela """
		operation = "SELECT * FROM %s %s"%(self.params["tablename"], sqlstr)
		return self.execute(operation)

	def add(self, *fieldsvalues):
		""" adiciona a tupla de valores nos campos correspondes a sua tabela """
		placeholders = ", ".join(("?"*len(fieldsvalues)))
		operation = "INSERT INTO %s VALUES(null, %s)"%(self.params["tablename"], placeholders)
		return self.execute(operation, fieldsvalues)

	def update(self, fields={}, filter_by={}):
		""" atualiza os 'fields' filtrando por 'filter_by' """
		fields = ", ".join(["%s='%s'"%(k,v) for k, v in fields.iteritems()])
		filter_by = " and ".join(["%s='%s'"%(k,v) for k, v in filter_by.iteritems()])
		if filter_by:
			operation = "UPDATE %s SET %s WHERE %s"%(self.params["tablename"], fields, filter_by)
		else:
			operation = "UPDATE %s SET %s"%(self.params["tablename"], fields)
		return self.execute( operation )

	def delete(self, fieldname, fieldvalue):
		""" deleta o valor do campo dado """
		operation = "DELETE FROM %s WHERE %s=\"%s\""%(self.params["tablename"], fieldname, fieldvalue)
		return self.execute( operation )

	def exists(self, fieldname, fieldvalue):
		""" verifica a existencia do valor no campo. retorna True(exist) ou False(not exist) """
		operation = "SELECT * FROM %s WHERE %s=?"%(self.params["tablename"], fieldname)
		exc = self.execute(operation, (fieldvalue,))
		exist = bool(exc.fetchall())
		self.close()
		return exist

	def saveAndClose(self):
		""" simplifica a chamada para 'save' seguido de 'close' """
		self.save(); self.close()

	def save(self):
		""" salva as alterações no banco de dados """
		self.database.commit()

	def close(self):
		""" fecha o banco de dados. Encerra todas as operações sobre ele. """
		self.database.close()
		
################################## FLVPLAYER ##################################
def runElevated(cmd, params):
	""" executa um processo, porém requistando permissões. """
	import win32com.shell.shell as shell
	from win32com.shell import shellcon
	from win32con import SW_NORMAL
	import win32event, win32api
	
	process = shell.ShellExecuteEx(
	    lpVerb="runas", lpFile=cmd, fMask=shellcon.SEE_MASK_NOCLOSEPROCESS, 
	    lpParameters=params, nShow=SW_NORMAL
	)
	hProcess = process["hProcess"]
	class Process:
		processHandle = hProcess
		@staticmethod
		def terminate(): win32api.TerminateProcess(hProcess,0)
		@staticmethod
		def wait(): win32event.WaitForSingleObject(hProcess, win32event.INFINITE)
	return Process

class FlvPlayer( threading.Thread):
	""" Classe de controle para player externo. 
	O objetivo é abrir o player exeterno e indicar a ele o que fazer.
	"""
	def __init__(self, cmd="", filename="streamFlv", filepath="", port=80):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.cmd = cmd
		self.process, self.running = None, False
		
		if not filepath:
			self.url="http://localhost:%d/%s"%(port, filename)
		else:
			self.url = '"%s"'%filepath
		
	def playerStop(self):
		""" pára a execução do player """
		try: self.process.terminate()
		except: pass
		
	def isRunning(self):
		return self.running
	
	def run(self):
		try:
			self.process = runElevated(self.cmd, self.url)
			self.running = True; self.process.wait()
		except ImportError:
			self.process = subprocess.Popen(self.url, executable=self.cmd)
			self.running = True; self.process.wait()
		except: pass
		finally:
			self.running = False
		
################################ STREAMHANDLE ################################
class run_locked:
	""" decorador usado para sincronizar as conexões com o servidor """
	SYNC_THREAD = threading.Lock()
	
	def __call__(_self, method):
		def wrap(self, *args): # magic!
			with _self.SYNC_THREAD:
				method( self )
		return wrap
		
class StreamHandler( threading.Thread ):
	""" Essa classe controla as requisições feitas pelo player.
	Uma vez estabelecida a conexão, a medida que novos dados vão chegando, estes vão sendo enviados ao player. """

	HEADER_OK_200 = "\r\n".join([
		"HTTP/1.1 200 OK", 
		"Server: Python/2.7", 
		"Connection: keep-alive",
		"Content-Length: %s", 
		"Content-Type: video/flv", 
		"Content-Disposition: attachment", 
		"Content-Transfer-Encoding: binary",
		"Accept-Ranges: bytes", 
	    "icy-metaint: 0",
	"\n"])
	
	HEADER_PARTIAL_206 = "\r\n".join([
		"HTTP/1.1 206 OK Partial Content", 
		'Content-type: video/flv',
		'Content-Length: %s' ,
	    "icy-metaint: 0",
		'Content-Range: bytes %d-%d/%d',
	'\n'])
	
	def __init__(self, server, request):
		threading.Thread.__init__(self)
		self.request = request
		self.manage = server.manage
		self.server = server
		self.streammer = self.manage.get_streammer()
		self.sended = self.streamPos = 0
		self.headers = {}
		self.GET = ""
		
	def get_headers(self, request_data):
		headers = dict( re.findall(r"(.+?):\s*(.*?)(?:\r)?\n+", request_data) )
		get = re.search(r"(GET.+?(?:start=)?\d*)(?:\r)?\n+", request_data).group(1)
		return get, headers

	def get_range(self, get="", headers={}):
		if headers.has_key("Range"):
			matchobj = re.search("bytes=(?P<range>\d+)-?\d*", headers["Range"])
		else:
			matchobj = re.search("GET.+?(?:start=)?(?P<range>\d+)\s+HTTP.+", get)
		if matchobj: seekpos = matchobj.group("range")
		else: seekpos = 0
		return long(seekpos)
	
	def send_206_PARTIAL(self, streamPos, streamSize):
		headers = self.HEADER_PARTIAL_206 %(str(streamSize-streamPos), streamPos, (streamSize-1), streamSize)
		self.request.send( headers )

	def send_200_OK(self):
		headers = self.HEADER_OK_200 % self.manage.getVideoSize()
		self.request.send( headers )
		
	def get_request_data(self, timeout=60):
		data = ""
		ready = select.select([self.request],[],[],timeout)[0]
		while ready:
			data += self.request.recv(1024)
			ready = select.select([self.request],[],[],0)[0]
		return data
	
	def close_me(self, headers):
		agent = headers.get("User-Agent", "").lower()
		conn = headers.get("Connection", "close").lower()
		return (conn=="close" and not re.search("VLC",agent,re.IGNORECASE))
		
	def run(self):
		try: self.handle()
		except: pass
		finally:
			self.request.close()
			self.server.remove_client(self.request)
			del self.streammer
		
	def handle(self):
		data = self.get_request_data()
		
		self.GET, self.headers = self.get_headers( data )
		self.streamPos = self.get_range(self.GET, self.headers)
		print "REQUEST: %s RANGE: %s"%(self.GET, self.streamPos)
		if self.close_me(self.headers): return
		
		if self.streamPos > 0 and self.manage.videoManager.suportaSeekBar():
			self.manage.setRandomRead( self.streamPos )
			self.send_206_PARTIAL(self.streamPos, self.manage.getVideoSize())
			self.request.send( self.manage.videoManager.getStreamHeader() )
		else:
			self.manage.reloadSettings()
			self.send_200_OK()
			
		# número de bytes já enviados ao cliente(player)
		self.sended = self.streamPos
		
		for stream in self.streammer.get_stream():
			self.sended += self.request.send( stream )
			if self.manage.isComplete(): # diminui a sobrecarga
				time.sleep(0.001)
			
################################### SERVER ####################################
class Server( threading.Thread ):
	def __init__(self, manage, host="localhost", port=80):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind((host, port))
		self.server.listen(5)
		
		self.manage = manage
		self.clients = []
		
	def __del__(self):
		del self.manage

	def stop_clients(self):
		""" fecha todas as conexões atualmente ativas """
		for clt in self.clients: clt.close()
	
	def remove_client(self, clt):
		self.clients.remove(clt)

	def stop(self):
		self.server.close()
		
	def run(self):
		print "Starting server..."
		while True:
			try:
				rlist, wlist, xlist = select.select([self.server],[],[])
				if len(rlist) == 0: continue
				client, addr = self.server.accept()
			except: break
			StreamHandler(self, client).start()
			self.clients.append( client )
		print "Server stoped!"
		
################################ PROXYMANAGER ################################
# PROXY MANAGER: TRABALHA OS IPS DE SERVIDORES PROXY
class ProxyManager:
	lockNewIp = threading.Lock()

	def __init__(self, manage):
		self.manage = manage

		self.configPath = os.path.join(settings.APPDIR, "configs")
		self.filePath = os.path.join(self.configPath, "ipSP.cfg")

		fileIp = open( self.filePath )
		self.listaIp = [ip[:-1] for ip in fileIp.readlines()]
		fileIp.close() # close file

		self.generator = self.create_generator()

	def __del__(self):
		self.salveIps()
		del self.configPath
		del self.filePath
		del self.generator
		del self.manage		
		del self.listaIp

	def getNumIps(self):
		""" retorna o número de ips armazenados no arquivo """
		return len(self.listaIp)

	def salveIps(self):
		""" Salva todas as modificações """
		if not security_save(self.filePath, _list=self.listaIp):
			print "Erro salvando lista de ips!!!"

	def create_generator( self):
		""" Cria um gerador para iterar sobre a lista de ips """
		return (ip for ip in self.listaIp)

	def proxyFormatado( self):
		"""Retorna um servidor proxy ja mapeado: {"http": "http://0.0.0.0}"""
		proxy = self.getNewProxy()
		return self.formateProxy( proxy)

	def formateProxy(self, proxy):
		"""Retorna o servidor proxy mapeado: {"http": "http://0.0.0.0}"""
		return {"http": "http://%s"%proxy}

	def getNewProxy(self):
		""" retorna um novo ip sem formatação -> 250.180.200.125:8080 """
		ProxyManager.lockNewIp.acquire()
		try:
			new_proxy = self.generator.next()
		except StopIteration:
			self.generator = self.create_generator()
			new_proxy = self.generator.next()

		ProxyManager.lockNewIp.release()
		return new_proxy

	def setBadIp(self, ip):
		""" reoganiza a lista de ips, 
		colocando os piores para o final """
		if type(ip) is dict: ip = ip["http"]

		# remove a formatação do ip
		if ip.startswith("http://"):
			httpLen = len("http://")
			ip = ip[httpLen: ]

		# remove o bad ip de sua localização atual
		self.listaIp.remove( ip )

		# desloca o bad ip para o final da lista
		self.listaIp.append( ip )

	def getProxyLink(self, timeout=25):
		""" retona um endereço de um servidor 
		proxy e um link para um arquivo de video.
		"""
		vmanager = self.manage.videoManager

		while True:	
			proxy = self.getNewProxy()
			proxies = self.formateProxy(proxy)

			if vmanager.getVideoInfo(ntry=1, proxies=proxies, timeout=timeout):
				videoLink = vmanager.getLink(); break
			else:
				self.setBadIp(proxies["http"])

		return (proxies, videoLink)

################################# LINKMANAGER #################################
# LINK MANAGER: ADICIONA, REMOVE, E OBTÉM INFORMAÇÕES DOS LINKS ADICIONADAS
class UrlBase(object):
	def __init__(self):
		self.sep = u"::::"
		
	def __del__(self):
		del self.sep

	def joinUrlDesc(self, url, desc):
		""" junta a url com sua decrição(título), usando o separador padrão """
		return u"%s %s %s"%(url, self.sep, desc)

	def splitUrlDesc(self, url_desc_str):
		""" separa a url de sua decrição(título), usando o separador padrão """
		str_split = url_desc_str.rsplit( self.sep, 1)
		if len(str_split) == 2:
			url, desc = str_split
			return url.strip(), desc.strip()
		# caso não haja ainda, uma desc(título)
		return str_split[0], ""

	def splitBaseId(self, value):
		""" value: megavideo[t53vqf0l] -> (megavideo, t53vqf0l) """
		base, id = value.split("[")
		return base, id[:-1] #remove ]

	def formatUrl(self, valor):
		""" megavideo[t53vqf0l] -> http://www.megavideo.com/v=t53vqf0l """
		import gerador
		base, id = self.splitBaseId( valor )
		return gerador.Universal.get_url( base ) % id

	@staticmethod
	def getBaseName(url):
		""" http://www.megavideo.com/v=t53vqf0l -> megavideo.com """
		parse = urlparse.urlparse( url )
		netloc_split = parse.netloc.split(".")
		if parse.netloc.startswith("www"):
			basename = "%s.%s"%tuple(netloc_split[1:3])
		else:# para url sem www inicial
			basename = "%s.%s"%tuple(netloc_split[0:2])
		return basename

	def analizeUrl(self, url):
		""" http://www.megavideo.com/v=t53vqf0l -> (megavideo.com, t53vqf0l) """
		import gerador
		basename = self.getBaseName(url)
		urlid = gerador.Universal.get_video_id(basename, url)
		return (basename, urlid)

########################################################################
class UrlManager( UrlBase ):
	def __init__(self):
		super(UrlManager, self).__init__()
		self.objects = models.Url.objects # acesso a queryset
		self.lastUrl_objects = models.LastUrl.objects
		
	def getUrlId(self, title):
		""" retorna o id da url, com base no título(desc) """
		query = self.objects.get(title = title)
		return self.splitBaseId( query.url )[-1]

	def setTitleIndex(self, title):
		""" adiciona um índice ao título se ele já existir """
		pattern = title + "(?:###\d+)?"
		query = self.objects.filter(title__regex = pattern).order_by("title")
		count = query.count()
		if count > 0:
			db_title = query[count-1].title # last title
			matchobj = re.search("(?:###(?P<index>\d+))?$", db_title)
			try: index = int(matchobj.group("index"))
			except: index = 0
			title = title + ("###%d"%(index+1))
		return title
		
	def remove(self, title):
		""" remove todas as referêcias do banco de dados, com base no título """
		self.objects.get(title=title).delete()

	def add(self, url, title):
		""" Adiciona o título e a url a base de dados. 
		É importante saber se a url já foi adicionada, use o método 'exist'."""
		urlname, urlid = self.analizeUrl(url)
		urlmodel = "%s[%s]"%(urlname, urlid)
		
		# impede títulos iguais
		if self.objects.filter(title=title).count() > 0:
			title = self.setTitleIndex(title)
			
		models.Url(url=urlmodel, title=title).save()
		
		try:
			lu = self.lastUrl_objects.latest("url")
			lu.url = url; lu.title = title; lu.save()
		except: models.LastUrl(url=url, title=title).save()
		
	def getTitleList(self):
		return [ query.title
		    for query in self.objects.all().order_by("title")
		]
	
	def getUrlTitle(self, url):
		urlmodel = "%s[%s]"%self.analizeUrl(url)
		try: query = self.objects.get(url = urlmodel)
		except: return ""
		return query.title
	
	def getUrlTitleList(self):
		""" retorna todas as urls e titulos adicionados na forma [(k,v),] """
		return [(self.formatUrl(query.url), query.title) 
		    for query in self.objects.all()
		]

	def getLastUrl(self):
		try: query = self.lastUrl_objects.latest("url")
		except: return "http://", "..."
		return (query.url, query.title)
	
	def exist(self, url):
		""" avalia se a url já existe na base de dados """
		urlmodel = "%s[%s]"%self.analizeUrl(url)
		query = self.objects.filter(url=urlmodel)
		return (query.count() > 0) # se maior então existe

########################################################################
class ResumeBase(object):
	""" Cria a estrutura de amazenamento de dados de resumo """
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self.query = None
		
	def base64Encode(self, value):
		""" codifica o tipo de Python em 'value' para tipo 'cPickle' -> 'base64'"""
		return base64.b64encode(cPickle.dumps(value))

	def sha_encode(self, value):
		""" codifica 'value' dado para formato de dados 'cha' """
		try: value = sha.sha( value ).hexdigest()
		except:
			try: value = unicodedata.normalize("NFKD", unicode(value,"UTF-8"))
			except: value = unicodedata.normalize("NFKD", value)
			osha = sha.sha( value.encode("ASCII","ignore") )
			value = osha.hexdigest()
		return value

	def update(self, title):
		self.query = self.get(title)

	def get_file_quality(self):
		return self.query.streamQuality

	def get_file_ext(self):
		return self.query.streamExt

	def get_file_size(self):
		"""retorna o tamanho total do arquivo sendo resumido"""
		return self.query.streamSize

	def get_seek_pos(self):
		"""retorna a posição do próximo bloco de bytes"""
		return self.query.resumePosition

	def get_intervals(self):
		"""retorna a lista de intervalos pendentes"""
		resumeblocks = self.query.resumeBLocks.encode("ascii")
		return cPickle.loads( resumeblocks )

	def get_send_bytes(self):
		""" número de bytes que serão enviados ao player """
		return self.query.sendBytes

	def get_bytes_total(self):
		""" número de total de bytes baixados """
		return self.query.streamDownBytes
	
class ResumeInfo( ResumeBase ):
	def __init__(self):
		super(ResumeInfo, self).__init__()
		self.objects = models.Resume.objects

	def add(self, title, **kwargs):
		"""filename: videoExt; streamSize; seekPos; 
		intervPendentes; numTotalBytes; nBytesProntosEnvio; videoQuality
		"""
		try: query = self.objects.get(title=title)
		except: query = models.Resume()
		
		query.title = title
		query.resumeBLocks = cPickle.dumps(kwargs["intervPendentes"])
		query.streamDownBytes = kwargs["numTotalBytes"]
		query.sendBytes = kwargs["nBytesProntosEnvio"]
		query.streamQuality = kwargs["videoQuality"]
		query.streamSize = kwargs["streamSize"]
		query.resumePosition = kwargs["seekPos"]
		query.streamExt = kwargs["videoExt"]
		query.save() # sanvando no banco de dados
		
	def has_info(self, title):
		return bool(self.get(title))

	def remove(self, title):
		self.objects.get(title=title).delete()
		
	def get(self, title):
		try: query = self.objects.get(title=title)
		except: return
		return query
	
################################# FILEMANAGER ##################################
# FILE MANAGER: TUDO ASSOCIADO A ESCRITA DA STREAM NO DISCO
class FileManager:
	lockReadWrite = threading.RLock()

	def __init__(self, **params):
		""" params={}
		- tempfile: False -  padrão sempre False.
		- videoExt: flv - usando como padrão.
		- videoId: id do arquivo de vídeo(deve ser dado ao iniciar o objeto).
		"""
		self.params = params
		self.filePath = settings.DEFAULT_VIDEOS_DIR
		self.resumeInfo = ResumeInfo()
		
	def __del__(self):
		try: self.file.close()
		except: pass
		del self.filePath
		del self.params

	def setFileExt(self, ext):
		self.params["videoExt"] = ext

	def setFileId(self, ext):
		self.params["videoId"] = ext

	def getFilePath(self, filename):
		""" retorna o caminho completo para o local do arquivo """
		query = self.resumeInfo.get( filename )
		
		if query: videoExt = query.streamExt
		else: videoExt = self.params.get("videoExt","")
		videoExt = videoExt or "flv"
		
		try: filename = unicodedata.normalize("NFKD", unicode(filename,"UTF-8"))
		except: filename = unicodedata.normalize("NFKD", filename)
		filename = filename.encode("ASCII","ignore")
		filename = "%s.%s"%(filename, videoExt)
		
		filepath = os.path.join(self.filePath, filename)
		return filepath

	def pathExist(self, filename):
		"""avalia se o arquivo já existe na pasta vídeos."""
		filepath = self.getFilePath(filename)
		return os.path.exists(filepath)

	def recover(self, filename):
		""" recupera um arquivo temporário, salvando-o de forma definitiva """
		with FileManager.lockReadWrite:
			try:
				from shutil import copyfileobj
				# começa a leitura do byte zero
				self.file.seek(0)
				filepath = self.getFilePath(filename)
				if os.path.exists(filepath):
					msg = _(u"O arquivo já existe!")
					raise IOError, msg.encode("utf-8","ignore")
				with open(filepath, "w+b") as file:
					copyfileobj(self.file, file, 1024**2) # 1mega
					msg  = _("O arquivo foi recuperado com sucesso!")
					flag = True
			except Exception, err:
				errmsg = err.message.decode("utf-8","ignore")
				msg  = _(u"Erro tentando recuperar arquivo.\nCausa: %s")%errmsg
				flag = False
		return flag, msg

	def resume(self, filename):
		""" Tenta fazer o resumo do video, se possível.
		O resumo será baseado na variável "tempfile". Se "False" o video passa 
		para um arquivo efetivo. Quando "True", um arquivo temporário será criado 
		e o resumo ignorado. """
		if filename and self.params.get("tempfile",False) is False:
			filepath = self.getFilePath( filename )
			
			if self.resumeInfo.has_info( filename ):
				self.resumeInfo.update( filename )
				
				self.file = open(filepath, "r+b")
				return True
		return False # o arquivo não está sendo resumido

	def cacheFile(self, filename):
		if self.params.get("tempfile", False) is False:
			filepath = self.getFilePath( filename )
			self.file = open(filepath, "w+b")
		else:
			self.file = tempfile.TemporaryFile(
				dir=os.path.join(self.filePath,"temp"))

	def write(self, pos, dados):
		"""Escreve os dados na posição dada"""
		FileManager.lockReadWrite.acquire()

		self.file.seek( pos)
		self.file.write( dados)

		FileManager.lockReadWrite.release()

	def read(self, pos, bytes):
		"""Lê o numero de bytes, apartir da posição dada"""
		FileManager.lockReadWrite.acquire()

		self.file.seek( pos)
		stream = self.file.read( bytes)
		npos = self.file.tell()

		FileManager.lockReadWrite.release()
		return (stream, npos)

################################## INTERVALO ###################################
# INDEXADOR: TRABALHA A DIVISÃO DA STREAM
class Interval:
	def __init__(self, **params):
		"""params = {}; 
		seekpos: posição inicial de leitura da stream; 
		index: indice do bloco de bytes; 
		intervPendentes: lista de intervals pendetes(não baixados); 
		offset: deslocamento do ponteiro de escrita à esquerda.
		maxsize: tamanho do block que será segmentado.
		"""
		assert params.get("maxsize",None), "maxsize is null"

		self.send_info = {"nbytes":{}, "sending":0}
		self.seekpos = params.get("seekpos", 0)
		self.intervPendentes = params.get("intervPendentes", [])

		self.maxsize = params["maxsize"]
		self.maxsplit = params.get("maxsplit",2)

		self.default_block_size = self.calcule_block_size()
		self.intervals = {}

		# caso a posição inicial leitura seja maior que zero, offset 
		# ajusta essa posição para zero. equivalente a start - offset
		self.offset = params.get("offset", self.seekpos)

	def __del__(self):
		del self.offset
		del self.seekpos
		del self.send_info
		del self.intervals
		del self.intervPendentes

	def canContinue(self, obj_id):
		""" Avalia se o objeto conexão pode continuar a leitura, 
		sem comprometer a montagem da stream de vídeo(ou seja, sem corromper o arquivo) """
		if self.hasInterval(obj_id):
			return (self.get_end(obj_id) == self.seekpos)
		return False

	def get_offset(self):
		""" offset deve ser usado somente para leitura """
		return self.offset

	def get_index(self, obj_id):
		values = self.intervals.get(obj_id, -1)
		if values != -1: return values[0]
		return values

	def get_start(self, obj_id):
		values = self.intervals.get(obj_id, -1)
		if values != -1: return values[1]
		return values

	def get_end(self, obj_id):
		values = self.intervals.get(obj_id, -1)
		if values != -1: return values[2]
		return values

	def get_block_size(self, obj_id):
		""" retorna o tamanho do bloco de bytes"""
		values = self.intervals.get(obj_id, -1)
		if values != -1: return values[3]
		return values

	def hasInterval(self, obj_id):
		""" avalia se o objeto tem um intervalo ligado a ele """
		return bool(self.intervals.get(obj_id, None))

	def get_first_start( self):
		""" retorna o começo(start) do primeiro intervalo da lista de intervals """
		intervs  = [interval[1] for interval in self.intervals.values()]
		intervs += [interval[2] for interval in self.intervPendentes]
		intervs.sort()
		try: start = intervs[0]
		except IndexError: start = -1
		return start

	def remove(self, obj_id):
		return self.intervals.pop(obj_id, None)

	def fixeIntervPendente(self, *args):
		""" indice; nbytes; start; end; block_size"""
		self.intervPendentes.append( args)

	def numIntervPendentes(self):
		return len( self.intervPendentes )

	def calcule_block_size(self):
		""" calcula quantos bytes serão lidos por conexão criada """
		block_size = int(float(self.maxsize) / float(self.maxsplit))
		min_size = 512*1024 # impede um bloco muito pequeno
		if block_size < min_size: block_size = min_size 
		return block_size

	def updateIndex(self):
		""" reorganiza a tabela de indices """
		intervals = self.intervals.items()
		# organiza por start: (obj_id = 1, (0, start = 1, 2, 3))
		intervals.sort(key=lambda x: x[1][1])

		for index, data in enumerate( intervals, 1):
			obj_id, interval = data
			# aplicando a reorganização dos indices
			self.intervals[ obj_id ][0] = index

	def associeIntervPendente(self, obj_id):
		""" Configura uma conexão existente com um intervalo pendente(não baixado) """
		self.intervPendentes.sort()
		index, nbytes, start, end, block_size = self.intervPendentes.pop(0)
		old_start = start

		# calcula quantos bytes foram lidos, até ocorrer o erro.
		novo_grupo_bytes = nbytes - (block_size - (end - start))

		# avança somando o que já leu.
		start = start + novo_grupo_bytes
		block_size = end - start

		self.intervals[obj_id] = [index, start, end, block_size]

		if self.send_info["nbytes"].get(old_start,None) is not None:
			del self.send_info["nbytes"][old_start]

		self.send_info["nbytes"][start] = 0	

	def associeIntervDerivado(self, obj_id_):
		""" cria um novo intervalo, apartir de um já existente """
		intervals = self.intervals.items()
		# organiza pelos indices dos intervals: (1, (0, 1, 2, 3))
		intervals.sort(key=lambda x: x[1][0])

		for obj_id, interv in intervals:
			index, start, end, block_size = interv
			nbytes = self.send_info["nbytes"][start]
			average_bytes = int(float((block_size - nbytes)) *0.5)

			if average_bytes > (512*1024):
				# reduzindo o tamanho do intervalo antigo
				new_end = end - average_bytes
				# recalculando o tamanho do bloco de bytes
				new_block_size = new_end - start
				self.intervals[ obj_id ][-2] = new_end
				self.intervals[ obj_id ][-1] = new_block_size

				# criando um novo intervalo, derivado do atual
				start = new_end
				block_size = end - start
				self.intervals[ obj_id_] = [0, start, end, block_size]
				self.send_info["nbytes"][start] = 0
				self.updateIndex()
				break

	def associeNovoInterv(self, obj_id):
		""" cria um novo intervalo de divisão da stream """
		start = self.seekpos

		if start < self.maxsize: # A origem em relação ao final
			end = start + self.default_block_size

			# verificando se final da stream já foi alcançado.
			if end > self.maxsize: end = self.maxsize

			difer = self.maxsize - end

			# Quando o resto da stream for muito pequeno, adiciona ao final do interv.
			if difer > 0 and difer < 512*1024: end += difer

			block_size = end - start

			self.intervals[obj_id] = [0, start, end, block_size]
			# associando o início do intervalo ao contador
			self.send_info["nbytes"][start] = 0

			self.seekpos = end
			self.updateIndex()

################################ main : manage ################################
import gerador

class Streammer:
	""" lê e retorna a stream de dados """
	#----------------------------------------------------------------------
	def __init__(self, manage):
		self.manage = manage
		self.seekpos = self.sended = 0
		
	def get_stream(self, block_size=524288):
		while self.sended < self.manage.getVideoSize():
			if self.seekpos < self.manage.nBytesProntosEnvio:
				block_len = block_size
				
				if (self.seekpos + block_len) > self.manage.nBytesProntosEnvio:
					block_len = self.manage.nBytesProntosEnvio - self.seekpos
					
				stream, self.seekpos = self.manage.fileManager.read(self.seekpos, block_len)
				self.sended += block_len
				yield stream
			else:
				time.sleep(0.001)
		yield "" # end stream
		
	def __del__(self):
		del self.manage
		
# GRUPO GLOBAL DE VARIAVEIS COMPARTILHADAS
class Manage:
	syncLockWriteStream = threading.Lock()
	
	def __init__(self, URL = "", **params):
		""" params {}:
			tempfile - define se o vídeo será gravado em um arquivo temporário
			videoQuality - qualidade desejada para o vídeo. 
			Pode ser: 1 = baixa; 2 = média; 3 = alta
		"""
		assert URL, _("Entre com uma url primeiro!")
		self.streamUrl = URL # guarda a url do video
		self.params = params
		self.numTotalBytes = 0
		self.posInicialLeitura = 0
		self.streamManager = None
		self.updateRunning = False
		self.streamServer = None
		self.streamHeader = ""
		self.usingTempfile = params.get("tempfile", False)
		
		# guarda as conexoes criadas
		self.connections = []

		# manage log
		globalInfo.add_info("manage")

		try:
			# cria um banco de dados dos links adicionados
			self.urlManager = UrlManager()
			self.servername, video_id = self.urlManager.analizeUrl( self.streamUrl)
		except: raise AttributeError, _(u"Sem suporte para a url fornecida.")

		# nome do video ligado a url
		self.videoTitle = self.urlManager.getUrlTitle( self.streamUrl )
		self.videoSize = 0 # tamanho total do video
		self.videoExt = "" # extensão do arquivo de vídeo

		# videoManager: controla a obtenção de links, tamanho do arquivo, title, etc.
		vmanager = gerador.Universal.getVideoManager( self.streamUrl )
		self.videoManager = vmanager(self.streamUrl, qualidade=self.params.get("videoQuality",2))
		
		# streamManager: controla a transferência do arquivo de vídeo
		self.streamManager = gerador.Universal.getStreamManager( self.streamUrl )
		
		# gerencia os endereços dos servidores proxies
		self.proxyManager = ProxyManager( self)

		# embora o método inicialize tenha outro propósito, ele também 
		# complementa a primeira inicialização do objeto Manage.
		self.inicialize()

	def inicialize(self, **params):
		""" método chamado para realizar a configuração de leitura aleatória da stream """
		self.params.update( params )

		self._canceledl = False    # cancelar o download?
		self.velocidadeGlobal = 0  # velocidade global da conexão
		self.tempoDownload = ""    # tempo total de download
		self.nBytesProntosEnvio = 0

		self.fileManager = FileManager(
			tempfile = self.params.get('tempfile', False), 
			videoId = self.videoManager.get_video_id())

		# avalia se o arquivo pode ser resumido
		self.resumindo = self.fileManager.resume( self.videoTitle )

		if self.resumindo:
			self.nBytesProntosEnvio = self.fileManager.resumeInfo.get_send_bytes()
			self.videoSize = self.fileManager.resumeInfo.get_file_size()
			self.numTotalBytes = self.fileManager.resumeInfo.get_bytes_total()
			seekpos = self.fileManager.resumeInfo.get_seek_pos()
			intervs = self.fileManager.resumeInfo.get_intervals()

			# Sem o parâmetro qualidade do resumo, o usuário poderia 
			# corromper o arquivo de video, dando uma qualidade diferente
			self.params["videoQuality"] = self.fileManager.resumeInfo.get_file_quality()
			self.videoExt = self.fileManager.resumeInfo.get_file_ext()

			self.interval = Interval(maxsize = self.videoSize,
						             seekpos = seekpos, offset = 0, intervPendentes = intervs,
						             maxsplit = self.params.get("maxsplit", 2))

			self.posInicialLeitura = self.numTotalBytes
			
	def get_streammer(self):
		""" streammer controla a leitura dos bytes enviados ao player """
		return Streammer(self)
	
	def delete_vars(self):
		""" Deleta todas as variáveis do objeto """
		globalInfo.del_info("manage")
		###############################
		if not self.usingTempfile and not self.params.get("tempfile",False):
			self.salveInfoResumo()

		self.updateRunning = False
		###############################
		del self.posInicialLeitura
		del self.velocidadeGlobal
		del self.streamManager
		del self.numTotalBytes
		del self.tempoDownload
		del self.videoManager
		del self.proxyManager
		del self.urlManager
		del self.connections
		del self.fileManager
		del self.usingTempfile
		del self.streamHeader
		del self.streamServer		
		del self.videoTitle
		del self.servername
		del self._canceledl
		del self.videoSize
		del self.resumindo
		del self.streamUrl
		del self.interval
		del self.videoExt
		del self.params
		###############################

	def start(self, ntry=3, proxy={}, recall=None):
		""" Começa a coleta de informações. Depende da 
		internet, por isso pode demorar para reponder. """
		if not self.videoSize or not self.videoTitle:
			if not self.getInfo(ntry, proxy, recall):
				return False

			# salvando o link e o título
			if not self.usingTempfile and not self.params.get("tempfile",False):
				if not self.urlManager.exist( self.streamUrl ): # é importante não adcionar duas vezes
					self.urlManager.add(self.streamUrl, self.videoTitle)
				# pega o título já com um índice
				title = self.urlManager.getUrlTitle(self.streamUrl)
				self.videoTitle = title or self.videoTitle

		if not self.resumindo:
			self.fileManager.setFileExt(self.videoExt)
			self.fileManager.cacheFile( self.videoTitle )

			# intervals serão criados do ponto zero da stream
			self.interval = Interval(maxsize = self.videoSize, 
						             seekpos = self.params.get("seekpos", 0),
						             maxsplit = self.params.get("maxsplit", 2))

		if not self.updateRunning:
			self.updateRunning = True
			#atualiza os dados resumo e leitura
			thread.start_new(self.updateVideoInfo, ())

		# tempo inicial da velocidade global
		self.tempoInicialGlobal = time.time()
		return True # agora a transferência pode começar com sucesso.

	def getInfo(self, retry, proxy, recall):
		nfalhas = 0
		while nfalhas < retry:
			msg = u"\n".join([
				_(u"Coletando informações necessárias"),
				u"IP: %s" % proxy.get("http", _(u"Conexão padrão")),
				_(u"Tentativa %d/%d\n") % ((nfalhas+1), retry)
			])
			# função de atualização externa
			recall(msg, "")

			if self.videoManager.getVideoInfo(ntry=2, proxies=proxy):
				# tamanho do arquivo de vídeo
				self.videoSize = self.videoManager.getStreamSize()
				# título do arquivo de video
				self.videoTitle = self.videoManager.getTitle()
				# extensão do arquivo de video
				self.videoExt = self.videoManager.getVideoExt()
				break # dados obtidos com sucesso

			# função de atualização externa
			recall(msg, self.videoManager.get_message())
			nfalhas += 1

			# downlad cancelado pelo usuário. 
			if self._canceledl: return False

			# quando a conexão padrão falha em obter os dados
			# é viável tentar com um ip de um servidro-proxy
			proxy = self.proxyManager.proxyFormatado()

		# testa se falhou em obter os dados necessários
		return (self.videoSize and self.videoTitle)

	def recoverTempFile(self):
		""" tenta fazer a recuperação de um arquivo temporário """
		if not self.params.get("tempfile",False) or self.interval.get_offset() != 0:
			return None, ""

		# sincroniza com a escrita/leitura
		with FileManager.lockReadWrite: 
			videoTitle = self.videoTitle

			# verifica se a url já foi salva
			if not self.urlManager.exist( self.streamUrl ):
				# adiciona um indice se título já existir(ex:###1)
				self.videoTitle = self.urlManager.setTitleIndex(self.videoTitle)
			else:
				# como a url já existe, então só atualiza o título
				self.videoTitle = self.urlManager.getUrlTitle(self.streamUrl)

			# começa a recuperação do arquivo temporário.
			flag, msgstr = self.fileManager.recover( self.videoTitle )

			if flag is True:
				# salvando os dados de resumo. O arquivo será resumível
				self.salveInfoResumo()

				# nunca se deve adcionar a mesma url
				if not self.urlManager.exist(self.streamUrl):
					self.urlManager.add(self.streamUrl, videoTitle)
			return flag, msgstr

	def startServer(self):
		""" Inicia o processo de escuta do servidor """
		if not self.streamServer:
			try:
				self.streamServer = Server( self) # self - o servidor usa dados de Manager
				self.streamServer.start()
			except Exception, err:
				return False
		# informa que o server iniciou com sucesso
		return True

	def stopServer(self):
		""" pára o servidor completamente """
		if isinstance(self.streamServer, Server):
			self.streamServer.stop()
			self.streamServer = None # não iniciado

	def startNewConnection(self, noProxy=False, **params):
		""" inicia uma nova conexão de transferência de vídeo.
		params: {}
		- noProxy: se a conexão usará um ip de um servidor proxy.
		- ratelimit: limita a velocidade de sub-conexões criadas, para o número de bytes.
		- timeout: tempo de espera por uma resposta do servidor de stream(segundos).
		- typechange: muda o tipo de conexão.
		- waittime: tempo de espera entra as reconexões.
		- reconexao: tenta reconectar o número de vezes informado.
		"""
		smanager = self.streamManager(self, noProxy, **params)
		smanager.start(); self.addConnection( smanager)
		return smanager

	def isComplete(self):
		""" informa se o arquivo já foi completamente baixado """
		return (self.numBytesRecebidos() >= (self.getVideoSize()-25))

	def addConnection(self, refer):
		""" adiciona a referência para uma nova conexão criada """
		info = u"O controlador dado como referência é inválido."
		assert isinstance(refer, (StreamManager, StreamManager_)), info
		self.connections.append( refer)

	def getnConnection(self):
		""" retorna o número de conexões criadas e ativas """
		return len([sm for sm in self.connections if not sm.wasStopped()])

	def getnConnectionReal(self):
		""" retorna o número de conexões criadas"""
		return len(self.connections)

	def removaConexoesInativas(self):
		""" remove as conexões que estiverem completamente paradas """
		searching = True
		while searching:
			for smanager in self.connections:
				if not smanager.isAlive():
					self.connections.remove(smanager)
					break
			else:
				searching = False

	def stopConnections(self):
		""" pára todas as conexões atualmente ativas """
		for smanager in self.connections:
			smanager.stop()

	def getConnections(self):
		""" retorna uma lista de conexões criadas """
		return self.connections

	def canceledl(self):
		self._canceledl = True

	def getVideoTitle(self):
		return self.videoTitle

	def getUrl(self):
		return self.streamUrl

	def getVideoSize(self):
		return self.videoSize
	
	def intervSendoEnviado(self):
		return self.interval.send_info['sending']

	def numBytesRecebidos(self):
		""" retorna o numero total de bytes transferidos """
		return self.numTotalBytes

	def salveInfoResumo(self):
		""" salva todos os dados necessários para o resumo do arquivo atual """
		with FileManager.lockReadWrite:
			self.removaConexoesInativas()
			listInterv = [] # coleta geral de informações.
			for smanager in self.getConnections():
				ident = smanager.ident

				# a conexão deve estar ligada a um interv
				if self.interval.hasInterval( ident ):
					listInterv.append((
						self.interval.get_index( ident), 
						smanager.numBytesLidos, 
						self.interval.get_start( ident), 
						self.interval.get_end( ident),
						self.interval.get_block_size( ident))
									  )
			listInterv.extend(self.interval.intervPendentes)
			listInterv.sort()

			self.fileManager.resumeInfo.add(self.videoTitle,
						                    videoExt = self.videoExt, streamSize = self.getVideoSize(), 
						                    seekPos = self.interval.seekpos, intervPendentes = listInterv, 
						                    numTotalBytes = self.numTotalBytes, nBytesProntosEnvio = self.nBytesProntosEnvio,
						                    videoQuality = self.params.get("videoQuality",2))

	def porcentagem(self):
		""" Progresso do download em porcentagem """
		return StreamManager.calc_percent(self.numTotalBytes, self.getVideoSize())

	def progresso(self):
		""" Progresso do download """
		return "%s / %s"%(StreamManager.format_bytes( self.numTotalBytes ), 
				          StreamManager.format_bytes( self.getVideoSize() ))

	def setRandomRead(self, seekpos):
		""" Configura a leitura da stream para um ponto aleatório dela """
		with Manage.syncLockWriteStream:
			self.notifiqueConexoes(True)

			if not self.usingTempfile and not self.params.get("tempfile",False):
				self.salveInfoResumo()

			self.numTotalBytes = self.posInicialLeitura = seekpos
			del self.interval, self.fileManager

			self.inicialize(tempfile = True, seekpos = seekpos)
			self.params["seeking"] = True
			self.start()
		return True

	def reloadSettings(self):
		if self.params.get("seeking", False):
			with Manage.syncLockWriteStream:
				self.notifiqueConexoes(True)

				self.numTotalBytes = self.posInicialLeitura = 0
				del self.interval, self.fileManager

				self.inicialize(tempfile = self.usingTempfile, seekpos = 0)
				self.params["seeking"] = False
				self.start()
		return True

	def notifiqueConexoes(self, flag):
		""" Informa as conexões que um novo ponto da stream está sendo lido """
		for smanager in self.getConnections(): # coloca as conexões em estado ocioso
			if flag is True:
				smanager.fiqueEmEspera(True)
			elif smanager.estaProntoContinuar():
				# só libera a conexão da espera, quando ela confirmar
				# que entendeu a condição de reconfiguração.
				smanager.fiqueEmEspera(False)
				
	def updateVideoInfo(self, args=None):
		""" Atualiza as variáveis de transferência do vídeo. """
		startTime = time.time() # temporizador

		while self.updateRunning:
			try: # como self.interval acaba sendo deletado, a ocorrencia de erro é provável
				intervstart = self.interval.get_first_start()
				self.interval.send_info["sending"] = intervstart
				nbytes = self.interval.send_info["nbytes"].get(intervstart, 0)

				if intervstart >= 0:
					startabs = intervstart - self.interval.get_offset()
					self.nBytesProntosEnvio = startabs + nbytes

				elif self.isComplete(): # isComplete: tira a necessidade de uma igualdade absoluta
					self.nBytesProntosEnvio = self.getVideoSize()

				if not self.usingTempfile and not self.params.get("tempfile",False):
					# salva os dados de resumo no interval de tempo 300s=5min
					if time.time() - startTime > 300: 
						startTime = time.time()
						self.salveInfoResumo()

				# reinicia a atividade das conexões
				self.notifiqueConexoes(False)
			except: time.sleep(3) # tempo de recuperação

			time.sleep(0.1)
################################# STREAMANAGER ################################

# CONNECTION MANANGER: GERENCIA O PROCESSO DE CONEXÃO
class StreamManager( threading.Thread):
	lockBlocoFalha = threading.Lock()
	lockBlocoConfig = threading.Lock()
	syncLockWriteStream = threading.Lock()

	# Esse lock tem um objetivo interessante. Ao iniciar um
	# arquivo pelo resumo, não existem dados sobre o arquivo
	# de vídeo, como os links de download. Assim, usando o lock,
	# somente uma conexão pegará esse dados, por causa dele.
	lockInicialize = threading.Lock()
	listStrErro = ["onCuePoint"]

	# ordem correta das infos
	listInfo = ["http", "estado", "indiceBloco", 
		        "numBytesFaltando", "velocidadeLocal"]

	def __init__(self, manage, noProxy=False, **params):
		""" params: {}
		ratelimit: limita a velocidade de sub-conexões (limite em bytes)
		timeout: tempo de espera para se estabeler a conexão (tempo em segundos)
		reconexao: número de vezes que conexão com o servidor, tentará ser estabelecida.
		waittime: intervalo de tempo aguardado, quando houver falha na tentativa de conexão.
		typechange: muda o tipo de conexão(True ou False)
		"""
		threading.Thread.__init__(self)
		self.setDaemon(True)

		self.params = params
		self.manage = manage

		# conexão com ou sem um servidor
		self.usingProxy = noProxy
		self.proxies = {}

		self.link = self.linkSeek = ""
		self.aguarde = [False, False]
		self.megaFile, self.isRunning = False, True
		self.numBytesLidos = 0

	def __setitem__(self, k, v):
		if not self.params.has_key(k):
			print "Aviso: \"%s\" ainda não existe."%k
		self.params[k] = v

	def __del__(self):
		globalInfo.del_info(self.ident)
		del self.aguarde
		del self.numBytesLidos
		del self.isRunning
		del self.manage
		del self.megaFile
		del self.linkSeek
		del self.usingProxy
		del self.proxies
		del self.params
		del self.link

	@staticmethod
	def calc_eta(start, now, total, current):
		if total is None:
			return '--:--'
		dif = now - start
		if current == 0 or dif < 0.001: # One millisecond
			return '--:--'
		rate = float(current) / dif
		eta = long((float(total) - float(current)) / rate)
		(eta_mins, eta_secs) = divmod(eta, 60)
		(eta_hours, eta_mins)=  divmod(eta_mins, 60)
		return '%02d:%02d:%02d' % (eta_hours, eta_mins, eta_secs)

	@staticmethod
	def best_block_size(elapsed_time, bytes):
		new_min = max(bytes / 2.0, 1.0)
		new_max = min(max(bytes * 2.0, 1.0), 4194304) # Do not surpass 4 MB
		if elapsed_time < 0.001:
			return long(new_max)
		rate = bytes / elapsed_time
		if rate > new_max:
			return long(new_max)
		if rate < new_min:
			return long(new_min)
		return long(rate)

	@staticmethod
	def format_bytes(bytes):
		if bytes is None:
			return 'N/A'
		if type(bytes) is str:
			bytes = float(bytes)
		if bytes == 0.0:
			exponent = 0
		else:
			exponent = long(math.log(bytes, 1024.0))
		suffix = 'bkMGTPEZY'[exponent]
		converted = float(bytes) / float(1024**exponent)
		return '%.2f%s' % (converted, suffix)

	@staticmethod
	def calc_speed(start, now, bytes):
		dif = now - start
		if bytes == 0 or dif < 0.001: # One millisecond
			return '%10s' % '---b/s'
		return '%10s' % ('%s/s' % StreamManager.format_bytes(float(bytes) / dif))

	@staticmethod
	def calc_percent(byte_counter, data_len):
		if data_len is None:
			return '---.-%'
		return '%6s' % ('%3.1f%%' % (float(byte_counter) / float(data_len) * 100.0))

	def slow_down(self, start_time, byte_counter):
		"""Sleep if the download speed is over the rate limit."""
		rate_limit = self.params.get("ratelimit", 35840)
		if rate_limit is None or rate_limit == 0 or byte_counter == 0:
			return
		now = time.time()
		elapsed = now - start_time
		if elapsed <= 0.0:
			return
		speed = float(byte_counter) / elapsed
		if speed > rate_limit:
			time.sleep((byte_counter - rate_limit * (now - start_time)) / rate_limit)

	def inicialize(self):
		""" iniciado com thread. Evita travar no init """
		# globalinfo: add_info
		globalInfo.add_info(self.ident)
		globalInfo.set_info(self.ident, "estado", _("Iniciando"))

		with StreamManager.lockInicialize:
			timeout = self.params.get("timeout", 25)
			videoManager = self.manage.videoManager
			proxyManager = self.manage.proxyManager

			## evita a chamada ao método getVideoInfo
			if self.wasStopped(): return

			if self.usingProxy == True:
				if videoManager.getVideoInfo(timeout=timeout):
					self.link = videoManager.getLink()
			else:
				self.proxies, self.link = proxyManager.getProxyLink(timeout=timeout)

			ip = self.proxies.get("http",_(u"Conexão Padrão"))
			globalInfo.set_info(self.ident, "http", ip)

	def stop(self):
		""" pára toda a atividade da conexão """
		self.isRunning = False
		self.fixeFalhaTransfer(_(u"Parado pelo usuário"), 3)

	def wasStopped(self):
		return (not self.isRunning)

	def checkStreamError(self, stream):
		"""Verifica se os dados da stream estao corretos"""
		for err in StreamManager.listStrErro:
			index = stream.find( err )
			if index >= 0: return index
		return -1

	@staticmethod
	def responseCheck(nbytes, seekpos, seekmax, headers):
		""" Verifica se o ponto de leitura atual, mais quanto falta da stream, 
		corresponde ao comprimento total dela"""
		contentLength = headers.get("Content-Length", None)
		contentType = headers.get("Content-Type", None)

		if contentType is None: return False
		is_video = bool(re.match("(video/.*$|application/octet.*$)", contentType))

		if not is_video or contentLength is None: return False
		contentLength = long(contentLength)

		# video.mixturecloud: bug de 1bytes
		if seekpos != 0 and seekmax == (seekpos + contentLength + 1): return True
		if seekmax == contentLength: return True
		
		# no bytes 0 o tamanho do arquivo é o original
		if seekpos == 0: nbytes = 0
		# comprimento total(considerando os bytes removidos), da stream
		length = seekpos + contentLength - nbytes
		return seekmax == length

	def aguardeNotificacao(self):
		""" aguarda o processo de configuração terminar """
		self.aguarde[1] = True
		while self.aguarde[0]: time.sleep(0.1)
		self.aguarde[1] = False

	def fiqueEmEspera(self, flag):
		self.aguarde[0] = flag

	def esperaSolicitada(self):
		return self.aguarde[0]

	def estaProntoContinuar(self):
		return self.aguarde[1]

	def info_clear(self):
		globalInfo.set_info(self.ident, "indiceBloco", "")
		globalInfo.set_info(self.ident, "velocidadeLocal", "")

	def streamWrite(self, stream, nbytes):
		""" Escreve a stream de bytes dados de forma controlada """
		with Manage.syncLockWriteStream:
			if not self.esperaSolicitada() and not self.wasStopped() and \
			   self.manage.interval.hasInterval(self.ident):
				start = self.manage.interval.get_start(self.ident)

				# Escreve os dados na posição resultante
				pos = start - self.manage.interval.get_offset() + self.numBytesLidos
				self.manage.fileManager.write(pos, stream)

				# quanto ja foi baixado da stream
				self.manage.numTotalBytes += nbytes
				self.manage.interval.send_info["nbytes"][start] += nbytes

	def inicieLeitura(self ):
		blockSizeLen = 1024; localTimeStart = time.time()
		blockSize = self.manage.interval.get_block_size( self.ident )
		intervstart = self.manage.interval.get_start( self.ident)

		while self.numBytesLidos < blockSize and not self.wasStopped():
			try:
				# bloco de bytes do intervalo. Poderá ser dinamicamente modificado
				blockSize = self.manage.interval.get_block_size(self.ident)
				intervIndex = self.manage.interval.get_index(self.ident)
				if intervIndex < 0: raise AttributeError

				# condição atual da conexão: Baixando
				globalInfo.set_info(self.ident, "estado", _("Baixando") )
				globalInfo.set_info(self.ident, "indiceBloco", intervIndex)

				# limita a leitura ao bloco de dados
				if (self.numBytesLidos + blockSizeLen) > blockSize:
					blockSizeLen = blockSize - self.numBytesLidos

				# inicia a leitura da stream
				before = time.time()
				streamData = self.streamSocket.read( blockSizeLen )
				after = time.time()

				streamLen = len(streamData) # número de bytes baixados

				if self.esperaSolicitada(): # caso onde a seekbar é usada
					self.aguardeNotificacao(); break
					
				# o servidor fechou a conexão
				if (blockSizeLen > 0 and streamLen == 0) or self.checkStreamError( streamData) != -1:
					self.fixeFalhaTransfer(_("Parado pelo servidor"), 2); break

				# ajusta a quantidade de bytes baixados a capacidade atual da rede, ou ate seu limite
				blockSizeLen = self.best_block_size((after - before), streamLen)

				# permite somente uma escrita por vez
				self.streamWrite(streamData, streamLen)
				self.numBytesLidos += streamLen
				
				start = self.manage.tempoInicialGlobal
				current = self.manage.numBytesRecebidos() - self.manage.posInicialLeitura
				total = self.manage.getVideoSize() - self.manage.posInicialLeitura

				# calcula a velocidade de transferência da conexão
				speed = self.calc_speed(localTimeStart, time.time(), self.numBytesLidos)
				globalInfo.set_info(self.ident, 'velocidadeLocal', speed)
				
				# tempo do download
				self.manage.tempoDownload = self.calc_eta(start, time.time(), total, current)
				
				# calcula a velocidade global
				self.manage.velocidadeGlobal = self.calc_speed(start, time.time(), current)
				
				if self.numBytesLidos == blockSize:
					if self.manage.interval.canContinue(self.ident) and not self.manage.isComplete():
						self.manage.interval.remove(self.ident)# removendo o intervalo completo
						self.configure(); self.info_clear()# configurando um novo intervado
						intervstart = self.manage.interval.get_start(self.ident)
						localTimeStart = time.time()# reiniciando as variáveis
						
				# sem redução de velocidade para o intervalo pricipal
				elif self.manage.intervSendoEnviado() != intervstart:
					self.slow_down(localTimeStart, self.numBytesLidos)
			except Exception, erro:
				self.fixeFalhaTransfer(_("Erro de leitura"), 2)
				break
		# -----------------------------------------------------
		try: self.manage.interval.remove(self.ident)
		except:pass
		try: self.streamSocket.close()
		except:pass
		self.info_clear()
	
	def getStreamHeader(self, seekpos, nbytes=13):
		header = ""; stream = self.streamSocket.read( nbytes )
		if stream.startswith("FLV") and stream.endswith("\t"):
			if seekpos == 0: header = stream
			else: header, stream = stream, ""
			
		if stream[:9].startswith("FLV") and stream[:9].endswith("\t"):
			if seekpos == 0: header = stream[:9]
			else: header = stream[:9]; stream = stream[9:]
			
		return stream, header
	
	def removaConfigs(self, errorstring, errornumber):
		""" remove todas as configurações, importantes, dadas a conexão """
		if self.manage.interval.hasInterval(self.ident):
			with Manage.syncLockWriteStream: # bloqueia o thread da instance, antes da escrita.
				index = self.manage.interval.get_index( self.ident)
				start = self.manage.interval.get_start( self.ident)
				end = self.manage.interval.get_end( self.ident)
				blockSize = self.manage.interval.get_block_size( self.ident)

				# indice, nbytes, start, end
				self.manage.interval.fixeIntervPendente(
					index, self.numBytesLidos, start, end, blockSize
				)
				# número de bytes lidos, antes da conexão apresentar o erro
				bytesnumber = self.numBytesLidos - (blockSize - (end - start))
				self.manage.interval.remove(self.ident)
		else: bytesnumber = 0
		ip = self.proxies.get("http", "default")

		# remove as configs de video geradas pelo ip. A falha pode ter
		# sido causada por um servidor instável, lento ou negando conexões.
		del self.manage.videoManager[ ip ]

		if ip != "default" and ((errornumber != 3 and errornumber == 1) or bytesnumber < 524288): # 512k
			self.manage.proxyManager.setBadIp( ip ) # tira a prioridade de uso do ip.
		return bytesnumber

	def fixeFalhaTransfer(self, errorstring, errornumber):
		globalInfo.set_info(self.ident, 'estado', errorstring)
		self.info_clear()

		bytesnumber = self.removaConfigs(errorstring, errornumber) # removendo configurações
		if errornumber == 3 or self.wasStopped(): return # retorna porque a conexao foi encerrada
		time.sleep(0.5)

		globalInfo.set_info(self.ident, "estado", _("Reconfigurando"))
		time.sleep(0.5)

		ip = self.proxies.get("http", "default")
		timeout = self.params.get("timeout", 25)
		typechange = self.params.get("typechange", False)
		videoManager = self.manage.videoManager
		proxyManager = self.manage.proxyManager

		if self.usingProxy:
			if typechange:
				proxies, link = proxyManager.getProxyLink(timeout=timeout)
				self.usingProxy, self.proxies, self.link = True, proxies, link
		elif errornumber == 1 or bytesnumber < 524288: # 512k
			if typechange:
				if videoManager.getVideoInfo(timeout=timeout): # sucess
					self.proxies, self.link = {}, videoManager.getLink()
					self.usingProxy = True
			else:
				self.proxies, self.link = proxyManager.getProxyLink(timeout=timeout)
				self.usingProxy = False

		globalInfo.set_info(self.ident,"http",self.proxies.get("http",_(u"Conexão Padrão")))

	def conecte(self):
		videoManager = self.manage.videoManager
		seekpos = self.manage.interval.get_start(self.ident)
		streamSize = self.manage.getVideoSize()
		initTime = time.time()

		nfalhas = 0
		while nfalhas < self.params.get("reconexao",3) and not self.wasStopped():
			try:
				globalInfo.set_info(self.ident, "estado", _("Conectando"))
				waittime = self.params.get("waittime", 2)
				timeout = self.params.get("timeout", 25)

				# começa a conexão
				self.streamSocket = videoManager.conecte(self.linkSeek, 
				    proxies=self.proxies, timeout=timeout, login=False)
				
				stream, header = self.getStreamHeader(seekpos)
				
				# verifica a validade a resposta.
				isValid = self.responseCheck(len(header), seekpos, 
				    streamSize, self.streamSocket.headers)
				
				if isValid and self.streamSocket.code == 200:
					if stream:
						self.streamWrite(stream, len(stream))
						self.numBytesLidos += len(stream)					
					return True
				else:
					globalInfo.set_info(self.ident, "estado", _(u"Resposta inválida"))
					self.streamSocket.close(); time.sleep( waittime )
			except Exception, err:
				globalInfo.set_info(self.ident, "estado", _(u"Falha na conexão"))
				time.sleep( waittime )
				
			# se passar do tempo de timeout o ip será descartado
			if (time.time() - initTime) > timeout: break
			else: initTime = time.time()

			nfalhas += 1
		return False # nao foi possível conectar

	def configure(self ):
		""" associa a conexão a uma parte da stream """
		globalInfo.set_info(self.ident, "estado", _("Ocioso"))
		
		if not self.esperaSolicitada():
			with StreamManager.lockBlocoConfig:

				if self.manage.interval.numIntervPendentes() > 0:
					# associa um intervalo pendente(intervalos pendentes, são gerados em falhas de conexão)
					self.manage.interval.associeIntervPendente( self.ident )

				else:
					# cria um novo intervalo e associa a conexão.
					self.manage.interval.associeNovoInterv( self.ident )

					# como novos intervalos não são infinitos, atribui um novo, apartir de um já existente.
					if not self.manage.interval.hasInterval( self.ident ):
						self.manage.interval.associeIntervDerivado( self.ident )

				# bytes lido do intervalo atual(como os blocos reduzem seu tamanho, o número inicial será sempre zero).
				self.numBytesLidos = 0
		else:
			# aguarda a configuração terminar
			self.aguardeNotificacao()
			
	def run(self):
		# configura um link inicial
		self.inicialize()

		while not self.wasStopped() and not self.manage.isComplete():
			try:
				# configura um intervalo para cada conexao
				self.configure()
				
				if self.manage.interval.hasInterval( self.ident ):
					self.linkSeek = gerador.get_with_seek(
					    self.link, self.manage.interval.get_start(self.ident))
					# Tenta conectar e iniciar a tranferência do arquivo de video.
					if self.conecte(): self.inicieLeitura()
					else: self.fixeFalhaTransfer(_("Incapaz de conectar"), 1)
					
				# estado ocioso
				else: time.sleep(1)

			except Exception, erro:
				print "Erro[Processando stream] %s" %erro

		# estado final da conexão
		globalInfo.set_info(self.ident, "estado", _(u"Conexão parada"))

#########################  STREAMANAGER: (megaupload, youtube) ######################

class StreamManager_( StreamManager ):
	def __init__(self, manage, noProxy= False, **params):
		StreamManager.__init__(self, manage, noProxy, **params)
		self.megaFile = True

	def inicialize(self):
		""" iniciado com thread. Evita travar no init """
		# globalinfo: add_info
		globalInfo.add_info( self.ident)
		globalInfo.set_info(self.ident, "estado", "Iniciando")

		if self.usingProxy == True: # conexão padrão - sem proxy
			globalInfo.set_info(self.ident, "http", _(u"Conexão Padrão"))
		else:
			self.proxies = self.manage.proxyManager.proxyFormatado()
			globalInfo.set_info(self.ident, "http", self.proxies['http'])

	def fixeFalhaTransfer(self, errorstring, errornumber):
		globalInfo.set_info(self.ident, 'estado', errorstring)
		self.info_clear()

		typechange = self.params.get("typechange", False)
		proxyManager = self.manage.proxyManager

		bytesnumber = self.removaConfigs(errorstring, errornumber) # removendo configurações
		if errornumber == 3: return # retorna porque a conexao foi encerrada
		time.sleep(0.5)

		globalInfo.set_info(self.ident, "estado", _("Reconfigurando"))
		time.sleep(0.5)
		
		if self.usingProxy:
			if typechange is True:
				self.usingProxy, self.proxies = False, proxyManager.proxyFormatado()
		elif errornumber == 1 or bytesnumber < 524288:
			if typechange is True:
				self.usingProxy, self.proxies = True, {}
			else:
				self.usingProxy, self.proxies = False, proxyManager.proxyFormatado()
				
		globalInfo.set_info(self.ident,"http",self.proxies.get("http",_(u"Conexão Padrão")))

	def conecte(self):
		videoManager = self.manage.videoManager
		seekpos = self.manage.interval.get_start( self.ident) # posição inicial de leitura
		streamSize = self.manage.getVideoSize()
		nfalhas = 0
		
		while nfalhas < self.params.get("reconexao",1):
			try:
				sleep_for = self.params.get("waittime",2)
				
				globalInfo.set_info(self.ident, "estado", _("Conectando"))
				data = videoManager.get_init_page( self.proxies) # pagina incial
				link = videoManager.get_file_link( data) # link de download
				wait_for = videoManager.get_count( data) # contador
				
				for second in range(wait_for, 0, -1):
					globalInfo.set_info(self.ident, "estado", _(u"Aguarde %02ds")%second)
					time.sleep(1)
					
				globalInfo.set_info(self.ident, "estado", _("Conectando"))
				self.streamSocket = videoManager.conecte(
				    link, proxies=self.proxies, headers={"Range":"bytes=%s-"%seekpos})
				
				stream, header = self.getStreamHeader(seekpos) # get and write
				
				isValid = self.responseCheck(len(header), seekpos, 
				    streamSize, self.streamSocket.headers)
				
				if isValid and (self.streamSocket.code == 200 or self.streamSocket.code == 206):
					if stream:
						self.streamWrite(stream, len(stream))
						self.numBytesLidos += len(stream)
					return True
				else:
					globalInfo.set_info(self.ident, "estado", _(u"Resposta inválida"))
					self.streamSocket.close()
					time.sleep( sleep_for )
			except Exception, err:
				globalInfo.set_info(self.ident, "estado", _(u"Falha na conexão"))
				if hasattr(err, "code") and err.code == 503: return False
				time.sleep( sleep_for )
			nfalhas += 1
		return False #nao foi possivel conectar

	def run(self):
		# configura um link inicial
		self.inicialize()

		while self.isRunning and not self.manage.isComplete():
			try:
				# configura um intervalo para cada conexao
				self.configure()

				if self.manage.interval.hasInterval( self.ident ):
					# tentando estabelece a conexão como o servidor
					if self.conecte():
						self.inicieLeitura() # inicia a transferencia de dados
					else:
						self.fixeFalhaTransfer(_("Incapaz de conectar"), 1)

				# estado ocioso
				else: time.sleep(1)

			except Exception, erro:
				print "Erro[Processando stream] %s" %erro

		globalInfo.set_info(self.ident, "estado", _(u"Conexão parada"))

########################### EXECUÇÃO APARTIR DO SCRIPT  ###########################

if __name__ == '__main__':
	installTranslation() # instala as traduções