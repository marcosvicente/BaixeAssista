# -*- coding: ISO-8859-1 -*-
## guarda a vers�o do programa.
PROGRAM_VERSION = "0.1.8"
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
	""" instala as tradu��es apartir do arquivo de configura��es. """
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
	
	# instala no espa�o de nomes embutidos
	language.install(unicode=True)
#######################################################################################

def get_filename(filepath, fullname=True):
	""" fullname = (True | False) - C:\\dirfile\\arquivo.txt -> (arquivo.txt | arquivo) """
	filename = filepath.rsplit(os.sep,1)[-1]
	if not fullname: filename = filename.rsplit(".",1)[0]
	return filename

def security_save(filepath, _configobj=None, _list=None, newline="\n"):
	""" salva as configura��es da forma mais segura poss�vel. 
	filepath - local para salvar o arquivo
	_configobj - dicion�rio de configura��es
	_list - salva a lista, aplicando ou n�o a newline.
	newline='' - caso n�o haja interesse na adi��o de uma nova linha.
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
	try: # come�a a cria��o do novo arquivo de configura��o
		with open(filepath, "w") as configsfile:
			if type(_list) is list:
				for data in _list:
					configsfile.write("%s%s"%(data, newline))
			elif isinstance(_configobj, configobj.ConfigObj):
				_configobj.write( configsfile )
			# levanta a exe��o com o objetivo de recuperar o arquivo original
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
	""" Guarda informa��es de estado de outros objetos.
	O objetivo � criar um meio f�cil de obter informa��es de objetos, no escopo
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
	""" Executa opera��es de inser��o, recupera��o, atualiza��o e remo��o de dados, baco de dados sqlite3"""
	#----------------------------------------------------------------------
	def __init__(self, **params):
		"""params={}
		tablename: nome da tabela no banco de dados
		fieldsnames: nomes dos campos da tabela
		databasepath: caminho do bando de dados """
		self.params = params

		assert params.get("tablename",None), u"nome da tabela est� vazio!"
		assert params.get("fieldsnames",None), u"nenhum nome de campo fornecido!"

		# se um caminho n�o for dado, usa o de desenvolvimento.
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
		""" cria uma nova tabela, com o nome dado na inicializa��o, se ele ainda n�o existir. """
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
		""" salva as altera��es no banco de dados """
		self.database.commit()

	def close(self):
		""" fecha o banco de dados. Encerra todas as opera��es sobre ele. """
		self.database.close()

################################# UPDATESEARCH ##################################
class UpdateSearch:
	""" UpdateSearch procurar por novas vers�es lan�adas do programa """

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self.downloadListUrl = "http://code.google.com/p/gerenciador-de-videos-online/downloads/list"
		self.matchDownFiles = re.compile("<td class=\"vt\s*(?:id)?\s*col_\d+\".*?>(.*?)</td>", re.DOTALL)
		self.matchDownFilesInfo = re.compile("<a.*?>(.*?)</a>", re.DOTALL)
		self.menssagem = _(u"Ainda n�o h� uma nova vers�o dispon�vel.")
		self.webpage = ""

	def checkVersion(self, filesInfo):
		""" verifica se existe uma vers�o maior do que a vers�o atual """
		for filename, summary, uploaded, releasedata, size, downloadedcount in filesInfo:
			matchobj = re.search("BaixeAssista_v(.+?)(?:_exe)?\.(?:rar|zip|exe)", filename)
			if matchobj: version = matchobj.group(1)
			else: version = ""

			if version > PROGRAM_VERSION:
				info  = _(u"Vers�o atual do programa - BaixeAssista v%s\n\n") % PROGRAM_VERSION
				info += _(u"Vers�o lan�ada: %s\n") % filename
				info += _(u"Descri��o: %s\n") % summary
				info += _(u"Enviado: %s\n") % uploaded
				info += _(u"Lan�ado: %s\n") % releasedata
				info += _(u"Tamanho: %s\n") % size
				info += _(u"Baixado: %s vezes\n") % downloadedcount
				return (True, info)
		return (False, self.menssagem)

	def getWebPage(self):
		return self.webpage

	def search(self):
		try:
			fd = urllib2.urlopen( self.downloadListUrl)
			self.webpage = fd.read()
			fd.close()

			filesInfo = []
			for fileInfo in self.matchDownFiles.findall( self.webpage ):
				matchobj = self.matchDownFilesInfo.search( fileInfo )
				if matchobj: info = matchobj.group(1)
				else: info = ""

				info = info.replace(r"\n","").strip()
				info = info.decode("utf-8", "ignore")
				filesInfo.append( info )

			listaArquivos = []
			for index in range(0, len(filesInfo), 6):
				listaArquivos.append( filesInfo[index :index+6] )

			return self.checkVersion( listaArquivos )
		except Exception, err:
			return (None, _(u"Houve um erro ao procura por uma nova vers�o."))

class PackSearch:
	""" Procura por pacotes de atualiza��o """
	#----------------------------------------------------------------------
	## old: packet_v0.0.1_0.1.3.zip - new: packet_oswinv0.0.1_0.1.3.zip

	def __init__(self, **params):
		""" params = {} - packetVersion: vers�o corrente do pacote """
		assert  params.get("packetVersion",None), u"informe a vers�o do pacote atual!"
		self.packetVersion = params["packetVersion"]

		self.downloadListUrl = "http://code.google.com/p/gerenciador-de-videos-online/downloads/list"
		self.downloadUrl = "http://gerenciador-de-videos-online.googlecode.com/files/"
		self.matchPacketsList = re.compile("packet_(?:oswin|oslinux)?v.+?_.+?\.zip")
		self.matchPacketVersion = re.compile("packet_(?P<os>(?:oswin|oslinux)?)v(?P<packer>.+?)_(?P<program>.+?)\.zip")
		self.updateDir = os.path.join(settings.APPDIR, "update")
		self.libDir = os.path.join(settings.APPDIR, "lib", "shared.zip")

		self.packetsGroupsNames = []
		self.packetsGroupsPaths = []
		self.newPacketVersion = ""

		self.packetFound = self.is_old = False
		self.excludes = {"dirs": ("imagens", "configs", "locale"), "files": ("changes.txt", )}

		self.updateSucess = (True, _(u"O programa foi atualizado com sucesso!"))
		self.sucessWarning = _(u"Um novo pacote de atualiza��o est� dispon�vel: packet_v%s_%s.zip.")
		self.errorUpdateSearching = (None, _(u"Erro procurando por pacotes de atualiza��o."))
		self.errorUpdating = (None, _(u"Erro aplicando a atualiza��o. Tente novamente mais tarde."))
		self.warning = _(u"Vers�o antiga do programa detectada(atualize para a mais nova).")
		self.updatedWarning = (False, _(u"O programa j� est� atualizado."))

	def getNewVersion(self):
		return self.newPacketVersion

	def isValidFileName(self, filename):
		""" avalia se filename � um script .pyc """
		for dirname in self.excludes["dirs"]:
			if re.match(r"%s(?:\\|/).*"%dirname, filename):
				return False

		if filename in self.excludes["files"]:
			return False

		return True

	def updateLib(self, updateZip):
		""" cria uma nova biblioteca inserindo os scripts de atualiza��o """
		# nomes dos arquivos que ser�o atualizados.
		updateFileNames = updateZip.namelist()
		print "Updating files: " + " - ".join(updateFileNames)

		# zip com todos os arquivo da biblioteca.
		with zipfile.ZipFile( self.libDir ) as libZip:

			# arquivo zip de montagem da nova biblioteca.
			zipSharedPath = os.path.join(self.updateDir, "shared.zip")

			with zipfile.ZipFile(zipSharedPath, "w") as zipShared:
				# move para zipShared s� os arquivos que n�o ser�o atualizados.
				for zinfo in libZip.infolist():
					if not zinfo.filename in updateFileNames:
						bytes = libZip.read( zinfo.filename )
						zipShared.writestr(zinfo, bytes)

				# adiciona os novos scripts para zipShared, 
				# desconsiderando os que n�o forem scrits(como imagens, configs, etc)
				for zinfo in updateZip.infolist():
					if self.isValidFileName( zinfo.filename ):
						bytes = updateZip.read( zinfo.filename )
						zipShared.writestr(zinfo, bytes)

		# remove a biblioteca antiga.
		os.remove( libZip.filename )

		# salva a nova biblioteca, na pasta padr�o lib.
		import shutil
		path = os.path.join(settings.APPDIR, "lib")
		shutil.move(zipShared.filename, path)
		return True

	def getLastChanges(self, language="en"):
		""" retorna o texto informativo das �ltimas altera��es do programa """
		lastchanges = []
		try:
			for packetPath in self.packetsGroupsPaths:
				with zipfile.ZipFile(packetPath) as updateZip:
					zipinfo = updateZip.getinfo("changes.txt")
					rawText = updateZip.read( zipinfo )

					pattern = "<{language}>(.*)</{language}>".format(language=language)
					matchobj = re.search(pattern, rawText, re.DOTALL)

					text = matchobj.group(1)
					text = text.strip("\r\n ")

					header = "%s:\n"%get_filename(packetPath, False)
					lastchanges.append( header + text )
		except Exception, err:
			print "Error[Update changes] %s"%err
		return lastchanges

	def cleanUpdateDir(self):
		""" remove todos os arquivos da pasta de atualiza��o """
		for name in os.listdir(self.updateDir):
			path = os.path.join(self.updateDir, name)
			try: os.remove( path )
			except Exception, err:
				print "Error[Packer.cleanUpdateDir] %s"%path

	def updateFiles(self, updateZip):
		""" atualiza tudo que n�o for script, no programa """
		for zipinfo in updateZip.infolist():
			if re.match(r"(?:imagens|configs|locale)(?:\\|/).+", zipinfo.filename):
				# extrai no diret�rio principal, atualizando os arquivo
				updateZip.extract(zipinfo, settings.APPDIR)
		return True

	def update(self):
		""" Com o pacote de atualiza��es j� baixado, e 
		pronto para ser lido, instala as atualiza��es.
		"""
		assert len(self.packetsGroupsPaths), "Warning: no packets paths!"

		for index, packetPath in enumerate(self.packetsGroupsPaths):
			try:
				with zipfile.ZipFile( packetPath ) as updateZip:
					assert not updateZip.testzip(), "Corrupt: %s"%packetPath

					# atualizando a lib de scripts
					self.updateLib( updateZip )

					# atualizando as pastas de arquivos(imagens,locale,configs)
					self.updateFiles( updateZip )

					# guarda a vers�o do �ltimo pacote atualizado
					packetName = get_filename(packetPath)
					self.newPacketVersion, programVer = self.get_versions(packetName)
			except Exception, err:
				if index == 0: return self.errorUpdating
				else:
					# considera s� o grupo atualizado com sucesso
					self.packetsGroupsPaths = self.packetsGroupsPaths[:index]
					break
		# informa: atualizado com sucesso
		return self.updateSucess

	def packetDown(self):
		""" baixa o pacote de atuliza��es """
		assert self.packetFound, "Warning: no packets!"

		for index, packetName in enumerate(self.packetsGroupsNames):
			try:
				url = self.downloadUrl + packetName
				print "Baixando: " + url

				fd = urllib2.urlopen( url )

				if fd.code == 200:
					block_size = 1024
					packetPath = os.path.join(self.updateDir, packetName)

					with open(packetPath, "wb") as updateFile:
						while True:
							before = time.time()
							stream = fd.read(block_size)
							after = time.time()

							streamLen = len(stream)
							if streamLen == 0: break

							# ajusta a velocidade de download
							block_size = StreamManager.best_block_size((after-before), streamLen)

							updateFile.write( stream )

						# guarda o caminho do pacote baixado com sucesso
						self.packetsGroupsPaths.append( packetPath )

					fd.close()
				# erro no primeiro pacote p�ra todo o processo de atuliza��o
				elif index == 0: return self.errorUpdating
				else: break
			except Exception, err:
				if index == 0: return self.errorUpdating
				break
		return (True, _("Baixado com sucesso!"))

	def loadPage(self):
		""" carrega a p�gina da lista de pacotes """
		fd = urllib2.urlopen( self.downloadListUrl )
		webpage = fd.read(); fd.close()
		return webpage

	def get_versions(self, packetStr):
		""" packet_0.1.5_0.1.3.zip -> (0.1.5, 0.1.3) """
		matchobj = self.matchPacketVersion.match( packetStr )
		try:
			packer = matchobj.group("packer")
			program = matchobj.group("program")
		except:
			packer = program = ""
		return packer, program

	def get_system_name(self, packetStr):
		matchobj = self.matchPacketVersion.match( packetStr )
		try: system = matchobj.group("os")
		except: system = ""
		return system

	def packetListFilter(self, packets):
		""" remove as repeti��es das vers�es de pacotes e 
		pacotes que n�o pertencem a vers�o atual """
		validPacketsNames = []

		for packetName in packets:
			packet, program = self.get_versions( packetName )

			if program == PROGRAM_VERSION:
				if packet > self.packetVersion and not packetName in validPacketsNames:
					osystem = self.get_system_name( packetName )

					if not osystem or PROGRAM_SYSTEM.get(platform.system(),"") == osystem:
						validPacketsNames.append( packetName )

			elif program > PROGRAM_VERSION:
				# caso a vers�o atual seja mais antiga, avisa o usu�rio para atualizar
				# isso ocorrer� caso n�o haja mais atualiza��es para a vers�o atual
				self.is_old = True
		# organiza do menor pacote para o maior
		validPacketsNames.sort()
		return validPacketsNames

	def is_old_program(self):
		""" avalia se o programa � antigo, ap�s n�o encontrar novas atualiza��es """
		return self.is_old and not self.packetFound

	def search(self, webpage=None):
		""" packet_version: pacote que o programa est� usando """
		try:
			# quando webpage for dado como parametro, 
			# ser� em conjunto com UpdateSearch.
			if not webpage: webpage = self.loadPage()

			# lista de pacotes, sem repeti��es
			packetList = self.matchPacketsList.findall( webpage )
			packetList = self.packetListFilter( packetList )

			# guarda o grupo de pacotes com vers�o maior que a atual
			self.packetsGroupsNames = packetList
			self.packetFound = bool(len(packetList))
		except Exception, err: pass
		return self.packetFound

################################## FLVPLAYER ##################################
class FlvPlayer( threading.Thread):
	""" Classe de controle para player externo. 
	O objetivo � abrir o player exeterno e indicar a ele o que fazer.
	"""
	def __init__(self, cmd="", porta=80, filename="stream", videoPath=""):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		
		self.is_running = False
		
		if not videoPath:
			local = "http://localhost:%d/%s"%(porta, filename)
			self.args = (cmd, local)
		else:
			self.args = (cmd, videoPath)

	def playerStop(self):
		""" p�ra a execu��o do player """
		try: self.playerProcess.terminate()
		except: pass

	def isRunning(self):
		return self.is_running

	def run(self):
		self.is_running = False
		self.playerProcess = subprocess.Popen( self.args)
		self.is_running = True

		# aguarda o processo do player terminar
		if not self.playerProcess.wait() is None: 
			self.is_running = False

################################ STREAMHANDLE ################################
class run_locked:
	""" decorador usado para sincronizar as conex�es com o servidor """
	SYNC_THREAD = threading.Lock()
	
	def __call__(_self, method):
		def wrap(self, *args): # magic!
			with _self.SYNC_THREAD:
				method( self )
		return wrap
		
class StreamHandler( threading.Thread ):
	""" Essa classe controla as requisi��es feitas pelo player.
	Uma vez estabelecida a conex�o, a medida que novos dados v�o chegando, estes v�o sendo enviados ao player. """

	HEADER_OK_200 = "\r\n".join([
		"HTTP/1.1 200 OK", 
		"Server: Python/2.7", 
		"Connection: keep-alive",
		"Content-Length: %s", 
		"Content-Type: video/flv", 
		"Content-Disposition: attachment", 
		"Content-Transfer-Encoding: binary",
		"Accept-Ranges: bytes", 
	"\n"])
	
	HEADER_PARTIAL_206 = "\r\n".join([
		"HTTP/1.1 206 OK Partial Content", 
		'Content-type: video/flv',
		'Content-Length: %s' ,
		'Content-Range: bytes %d-%d/%d',
	'\n'])
	
	def __init__(self, server, request):
		threading.Thread.__init__(self)
		self.request = request
		self.manage = server.manage
		self.server = server
		self.nb_sended = 0
		self.streamPos = 0	
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
		
	def request_meta_data( self):
		""" envia apenas uma sequencia de bytes como amostra """
		if self.headers.get("Connection","").lower() != "keep-alive":
			if self.nb_sended > 262144 and not self.server.sendMeta(): # 256 k
				self.server.setMeta(True)
				raise BufferError, "Err: meta-data"
		
	def get_request_data(self, timeout=60):
		data = ""
		ready = select.select([self.request],[],[],timeout)[0]
		while ready:
			data += self.request.recv(1024)
			ready = select.select([self.request],[],[],0)[0]
		return data
	
	@run_locked()
	def run( self):
		self.server.client = self.request
		try: self.handle()
		except: pass
		self.server.set_need_stop(False)
		self.server.client = None
		self.request.close()
		
	def handle( self):
		data = self.get_request_data()
		
		self.GET, self.headers = self.get_headers( data )
		self.streamPos = self.get_range(self.GET, self.headers)
		print "REQUEST: %s RANGE: %s"%(self.GET, self.streamPos)
		
		if self.streamPos > 0 and self.manage.videoManager.suportaSeekBar():
			self.manage.setRandomRead( self.streamPos )
			
			self.send_206_PARTIAL(self.streamPos, self.manage.getVideoSize())
			self.request.send( self.manage.streamHeader )
		else:
			self.manage.reloadSettings()
			self.send_200_OK()
			
		# n�mero de bytes j� enviados ao cliente(player)
		self.nb_sended = self.streamPos
		# =========================
		while not self.server.need_stop():
			try:
				cached_stream = self.manage.getStream()
				if cached_stream:
					self.nb_sended += self.request.send( cached_stream )
					self.request_meta_data()
				else:
					if self.nb_sended >= self.manage.getVideoSize():
						break # all data sended!
					time.sleep(0.5)
					continue
			except Exception, err:
				print "Erro[Player] %s"%err
				break
			if self.manage.isComplete(): # diminui a sobrecarga
				time.sleep(0.01)
			
################################### SERVER ####################################
class Server( threading.Thread ):
	def __init__(self, manage, host="localhost", port=80):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind((host, port))
		self.server.listen(5)
		
		self.manage = manage
		self._need_stop = False
		self.enviouMeta = False
		self.client = None
		
	def __del__(self):
		del self.manage

	def clienteStop(self):
		""" Fecha o cliente �nico conectado ao servidor """
		if hasattr(self.client,"close"): self.client.close()
		self.set_need_stop(True) # informa o cliente para fechar a conex�o.
		self.setMeta(False)
		
	def need_stop(self):
		return self._need_stop

	def set_need_stop(self, flag=False):
		self._need_stop = flag

	def stop(self):
		self.server.close()

	def setMeta(self, flag):
		self.enviouMeta = flag

	def sendMeta(self):
		return self.enviouMeta

	def run(self):
		print "Starting server..."
		while True:
			try:
				rlist, wlist, xlist = select.select([self.server],[],[])
				if len(rlist) == 0: continue
				client, addr = self.server.accept()
			except: break
			StreamHandler(self, client).start()
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
		""" retorna o n�mero de ips armazenados no arquivo """
		return len(self.listaIp)

	def salveIps(self):
		""" Salva todas as modifica��es """
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
		""" retorna um novo ip sem formata��o -> 250.180.200.125:8080 """
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

		# remove a formata��o do ip
		if ip.startswith("http://"):
			httpLen = len("http://")
			ip = ip[httpLen: ]

		# remove o bad ip de sua localiza��o atual
		self.listaIp.remove( ip )

		# desloca o bad ip para o final da lista
		self.listaIp.append( ip )

	def getProxyLink(self, timeout=25):
		""" retona um endere�o de um servidor 
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
# LINK MANAGER: ADICIONA, REMOVE, E OBT�M INFORMA��ES DOS LINKS ADICIONADAS
class UrlBase(object):
	def __init__(self):
		self.sep = u"::::"
		
	def __del__(self):
		del self.sep

	def joinUrlDesc(self, url, desc):
		""" junta a url com sua decri��o(t�tulo), usando o separador padr�o """
		return u"%s %s %s"%(url, self.sep, desc)

	def splitUrlDesc(self, url_desc_str):
		""" separa a url de sua decri��o(t�tulo), usando o separador padr�o """
		str_split = url_desc_str.rsplit( self.sep, 1)
		if len(str_split) == 2:
			url, desc = str_split
			return url.strip(), desc.strip()
		# caso n�o haja ainda, uma desc(t�tulo)
		return str_split[0], ""

	def splitBaseId(self, value):
		""" value: megavideo[t53vqf0l] -> (megavideo, t53vqf0l) """
		base, id = value.split("[")
		return base, id[:-1] #remove ]

	def formatUrl(self, valor):
		import gerador
		""" megavideo[t53vqf0l] -> http://www.megavideo.com/v=t53vqf0l """
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
		import gerador
		""" http://www.megavideo.com/v=t53vqf0l -> (megavideo.com, t53vqf0l) """
		basename = self.getBaseName(url)
		urlid = gerador.Universal.get_video_id(basename, url)
		return (basename, urlid)

########################################################################
class UrlManager( UrlBase ):
	def __init__(self):
		super(UrlManager, self).__init__()
		self.objects = models.Url.objects # acesso a queryset

	def getUrlId(self, title):
		""" retorna o id da url, com base no t�tulo(desc) """
		query = self.objects.get(title = title)
		return self.splitBaseId( query.url )[-1]

	def setTitleIndex(self, title):
		""" adiciona um �ndice ao t�tulo se ele j� existir """
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
		""" remove todas as refer�cias do banco de dados, com base no t�tulo """
		self.objects.get(title=title).delete()

	def add(self, url, title):
		""" Adiciona o t�tulo e a url a base de dados. 
		� importante saber se a url j� foi adicionada, use o m�todo 'exist'."""
		urlname, urlid = self.analizeUrl(url)
		urlmodel = "%s[%s]"%(urlname, urlid)
		
		# impede t�tulos iguais
		if self.objects.filter(title=title).count() > 0:
			title = self.setTitleIndex(title)
			
		models.Url(url=urlmodel, title=title).save()
		
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
		try: query = self.objects.latest("url")
		except: return "http://", "..."
		return (self.formatUrl(query.url), query.title)
	
	def exist(self, url):
		""" avalia se a url j� existe na base de dados """
		urlmodel = "%s[%s]"%self.analizeUrl(url)
		query = self.objects.filter(url=urlmodel)
		return (query.count() > 0) # se maior ent�o existe

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
		"""retorna a posi��o do pr�ximo bloco de bytes"""
		return self.query.resumePosition

	def get_intervals(self):
		"""retorna a lista de intervalos pendentes"""
		resumeblocks = self.query.resumeBLocks.encode("ascii")
		return cPickle.loads( resumeblocks )

	def get_send_bytes(self):
		""" n�mero de bytes que ser�o enviados ao player """
		return self.query.sendBytes

	def get_bytes_total(self):
		""" n�mero de total de bytes baixados """
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
		- tempfile: False -  padr�o sempre False.
		- videoExt: flv - usando como padr�o.
		- videoId: id do arquivo de v�deo(deve ser dado ao iniciar o objeto).
		"""
		self.params = params
		self.filePath = os.path.join(settings.APPDIR, "videos")
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
		"""avalia se o arquivo j� existe na pasta v�deos."""
		filepath = self.getFilePath(filename)
		return os.path.exists(filepath)

	def recover(self, filename):
		""" recupera um arquivo tempor�rio, salvando-o de forma definitiva """
		with FileManager.lockReadWrite:
			try:
				from shutil import copyfileobj
				# come�a a leitura do byte zero
				self.file.seek(0)
				filepath = self.getFilePath(filename)
				if os.path.exists(filepath):
					msg = _(u"O arquivo j� existe!")
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
		""" Tenta fazer o resumo do video, se poss�vel.
		O resumo ser� baseado na vari�vel "tempfile". Se "False" o video passa 
		para um arquivo efetivo. Quando "True", um arquivo tempor�rio ser� criado 
		e o resumo ignorado. """
		if filename and self.params.get("tempfile",False) is False:
			filepath = self.getFilePath( filename )
			
			if self.resumeInfo.has_info( filename ):
				self.resumeInfo.update( filename )
				
				self.file = open(filepath, "r+b")
				return True
		return False # o arquivo n�o est� sendo resumido

	def cacheFile(self, filename):
		if self.params.get("tempfile", False) is False:
			filepath = self.getFilePath( filename )
			self.file = open(filepath, "w+b")
		else:
			self.file = tempfile.TemporaryFile(
				dir=os.path.join(self.filePath,"temp"))

	def write(self, pos, dados):
		"""Escreve os dados na posi��o dada"""
		FileManager.lockReadWrite.acquire()

		self.file.seek( pos)
		self.file.write( dados)

		FileManager.lockReadWrite.release()

	def read(self, pos, bytes):
		"""L� o numero de bytes, apartir da posi��o dada"""
		FileManager.lockReadWrite.acquire()

		self.file.seek( pos)
		stream = self.file.read( bytes)
		npos = self.file.tell()

		FileManager.lockReadWrite.release()
		return (stream, npos)

################################## INTERVALO ###################################
# INDEXADOR: TRABALHA A DIVIS�O DA STREAM
class Interval:
	def __init__(self, **params):
		"""params = {}; 
		seekpos: posi��o inicial de leitura da stream; 
		index: indice do bloco de bytes; 
		intervPendentes: lista de intervals pendetes(n�o baixados); 
		offset: deslocamento do ponteiro de escrita � esquerda.
		maxsize: tamanho do block que ser� segmentado.
		"""
		assert params.get("maxsize",None), "maxsize is null"

		self.send_info = {"nbytes":{}, "sending":0}
		self.seekpos = params.get("seekpos", 0)
		self.intervPendentes = params.get("intervPendentes", [])

		self.maxsize = params["maxsize"]
		self.maxsplit = params.get("maxsplit",2)

		self.default_block_size = self.calcule_block_size()
		self.intervals = {}

		# caso a posi��o inicial leitura seja maior que zero, offset 
		# ajusta essa posi��o para zero. equivalente a start - offset
		self.offset = params.get("offset", self.seekpos)

	def __del__(self):
		del self.offset
		del self.seekpos
		del self.send_info
		del self.intervals
		del self.intervPendentes

	def canContinue(self, obj_id):
		""" Avalia se o objeto conex�o pode continuar a leitura, 
		sem comprometer a montagem da stream de v�deo(ou seja, sem corromper o arquivo) """
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
		""" retorna o come�o(start) do primeiro intervalo da lista de intervals """
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
		""" calcula quantos bytes ser�o lidos por conex�o criada """
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
			# aplicando a reorganiza��o dos indices
			self.intervals[ obj_id ][0] = index

	def associeIntervPendente(self, obj_id):
		""" Configura uma conex�o existente com um intervalo pendente(n�o baixado) """
		self.intervPendentes.sort()
		index, nbytes, start, end, block_size = self.intervPendentes.pop(0)
		old_start = start

		# calcula quantos bytes foram lidos, at� ocorrer o erro.
		novo_grupo_bytes = nbytes - (block_size - (end - start))

		# avan�a somando o que j� leu.
		start = start + novo_grupo_bytes
		block_size = end - start

		self.intervals[obj_id] = [index, start, end, block_size]

		if self.send_info["nbytes"].get(old_start,None) is not None:
			del self.send_info["nbytes"][old_start]

		self.send_info["nbytes"][start] = 0	

	def associeIntervDerivado(self, obj_id_):
		""" cria um novo intervalo, apartir de um j� existente """
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
		""" cria um novo intervalo de divis�o da stream """
		start = self.seekpos

		if start < self.maxsize: # A origem em rela��o ao final
			end = start + self.default_block_size

			# verificando se final da stream j� foi alcan�ado.
			if end > self.maxsize: end = self.maxsize

			difer = self.maxsize - end

			# Quando o resto da stream for muito pequeno, adiciona ao final do interv.
			if difer > 0 and difer < 512*1024: end += difer

			block_size = end - start

			self.intervals[obj_id] = [0, start, end, block_size]
			# associando o in�cio do intervalo ao contador
			self.send_info["nbytes"][start] = 0

			self.seekpos = end
			self.updateIndex()

################################ main : manage ################################
import gerador

# GRUPO GLOBAL DE VARIAVEIS COMPARTILHADAS
class Manage:
	syncLockWriteStream = threading.Lock()

	def __init__(self, URL = "", **params):
		""" params {}:
			tempfile - define se o v�deo ser� gravado em um arquivo tempor�rio
			videoQuality - qualidade desejada para o v�deo. 
			Pode ser: 1 = baixa; 2 = m�dia; 3 = alta
		"""
		if not URL: raise AttributeError, _("Entre com uma url primeiro!")

		# guarda a url do video
		self.streamUrl = URL
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
		self.videoExt = "" # extens�o do arquivo de v�deo

		# videoManager: controla a obten��o de links, tamanho do arquivo, title, etc.
		vmanager = self.getVideoManager( self.streamUrl )
		self.videoManager = vmanager(self.streamUrl, qualidade=self.params.get("videoQuality",2))

		# streamManager: controla a transfer�ncia do arquivo de v�deo
		self.streamManager = self.getStreamManager( self.streamUrl )

		# gerencia os endere�os dos servidores proxies
		self.proxyManager = ProxyManager( self)

		# embora o m�todo inicialize tenha outro prop�sito, ele tamb�m 
		# complementa a primeira inicializa��o do objeto Manage.
		self.inicialize()

	def inicialize(self, **params):
		""" m�todo chamado para realizar a configura��o de leitura aleat�ria da stream """
		self.params.update( params )

		self._canceledl = False    # cancelar o download?
		self.velocidadeGlobal = 0  # velocidade global da conex�o
		self.tempoDownload = ""    # tempo total de download
		self.nBytesProntosEnvio = self.posLeitura = 0

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

			# Sem o par�metro qualidade do resumo, o usu�rio poderia 
			# corromper o arquivo de video, dando uma qualidade diferente
			self.params["videoQuality"] = self.fileManager.resumeInfo.get_file_quality()
			self.videoExt = self.fileManager.resumeInfo.get_file_ext()

			self.interval = Interval(maxsize = self.videoSize,
						             seekpos = seekpos, offset = 0, intervPendentes = intervs,
						             maxsplit = self.params.get("maxsplit", 2))

			self.posInicialLeitura = self.numTotalBytes

	def delete_vars(self):
		""" Deleta todas as vari�veis do objeto """
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
		""" Come�a a coleta de informa��es. Depende da 
		internet, por isso pode demorar para reponder. """
		if not self.videoSize or not self.videoTitle:
			if not self.getInfo(ntry, proxy, recall):
				return False

			# salvando o link e o t�tulo
			if not self.usingTempfile and not self.params.get("tempfile",False):
				if not self.urlManager.exist( self.streamUrl ): # � importante n�o adcionar duas vezes
					self.urlManager.add(self.streamUrl, self.videoTitle)
				# pega o t�tulo j� com um �ndice
				title = self.urlManager.getUrlTitle(self.streamUrl)
				self.videoTitle = title or self.videoTitle

		if not self.resumindo:
			self.fileManager.setFileExt(self.videoExt)
			self.fileManager.cacheFile( self.videoTitle )

			# intervals ser�o criados do ponto zero da stream
			self.interval = Interval(maxsize = self.videoSize, 
						             seekpos = self.params.get("seekpos", 0),
						             maxsplit = self.params.get("maxsplit", 2))

		if not self.updateRunning:
			self.updateRunning = True
			#atualiza os dados resumo e leitura
			thread.start_new(self.updateVideoInfo, ())

		# tempo inicial da velocidade global
		self.tempoInicialGlobal = time.time()
		return True # agora a transfer�ncia pode come�ar com sucesso.

	def getInfo(self, retry, proxy, recall):
		nfalhas = 0
		while nfalhas < retry:
			msg = u"\n".join([
				_(u"Coletando informa��es necess�rias"),
				u"IP: %s" % proxy.get("http", _(u"Conex�o padr�o")),
				_(u"Tentativa %d/%d\n") % ((nfalhas+1), retry)
			])
			# fun��o de atualiza��o externa
			recall(msg, "")

			if self.videoManager.getVideoInfo(ntry=2, proxies=proxy):
				# tamanho do arquivo de v�deo
				self.videoSize = self.videoManager.getStreamSize()
				# t�tulo do arquivo de video
				self.videoTitle = self.videoManager.getTitle()
				# extens�o do arquivo de video
				self.videoExt = self.videoManager.getVideoExt()
				break # dados obtidos com sucesso

			# fun��o de atualiza��o externa
			recall(msg, self.videoManager.get_message())
			nfalhas += 1

			# downlad cancelado pelo usu�rio. 
			if self._canceledl: return False

			# quando a conex�o padr�o falha em obter os dados
			# � vi�vel tentar com um ip de um servidro-proxy
			proxy = self.proxyManager.proxyFormatado()

		# testa se falhou em obter os dados necess�rios
		return (self.videoSize and self.videoTitle)

	def recoverTempFile(self):
		""" tenta fazer a recupera��o de um arquivo tempor�rio """
		if not self.params.get("tempfile",False) or self.interval.get_offset() != 0:
			return None, ""

		# sincroniza com a escrita/leitura
		with FileManager.lockReadWrite: 
			videoTitle = self.videoTitle

			# verifica se a url j� foi salva
			if not self.urlManager.exist( self.streamUrl ):
				# adiciona um indice se t�tulo j� existir(ex:###1)
				self.videoTitle = self.urlManager.setTitleIndex(self.videoTitle)
			else:
				# como a url j� existe, ent�o s� atualiza o t�tulo
				self.videoTitle = self.urlManager.getUrlTitle(self.streamUrl)

			# come�a a recupera��o do arquivo tempor�rio.
			flag, msgstr = self.fileManager.recover( self.videoTitle )

			if flag is True:
				# salvando os dados de resumo. O arquivo ser� resum�vel
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
		""" p�ra o servidor completamente """
		if isinstance(self.streamServer, Server):
			self.streamServer.stop()
			self.streamServer = None # n�o iniciado

	def startNewConnection(self, noProxy=False, **params):
		""" inicia uma nova conex�o de transfer�ncia de v�deo.
		params: {}
		- noProxy: se a conex�o usar� um ip de um servidor proxy.
		- ratelimit: limita a velocidade de sub-conex�es criadas, para o n�mero de bytes.
		- timeout: tempo de espera por uma resposta do servidor de stream(segundos).
		- typechange: muda o tipo de conex�o.
		- waittime: tempo de espera entra as reconex�es.
		- reconexao: tenta reconectar o n�mero de vezes informado.
		"""
		smanager = self.streamManager(self, noProxy, **params)
		smanager.start(); self.addConnection( smanager)
		return smanager

	def isComplete(self):
		""" informa se o arquivo j� foi completamente baixado """
		return (self.numBytesRecebidos() >= (self.getVideoSize()-25))

	def addConnection(self, refer):
		""" adiciona a refer�ncia para uma nova conex�o criada """
		info = u"O controlador dado como refer�ncia � inv�lido."
		assert isinstance(refer, (StreamManager, StreamManager_)), info
		self.connections.append( refer)

	def getnConnection(self):
		""" retorna o n�mero de conex�es criadas e ativas """
		return len([sm for sm in self.connections if not sm.wasStopped()])

	def getnConnectionReal(self):
		""" retorna o n�mero de conex�es criadas"""
		return len(self.connections)

	def removaConexoesInativas(self):
		""" remove as conex�es que estiverem completamente paradas """
		searching = True
		while searching:
			for smanager in self.connections:
				if not smanager.isAlive():
					self.connections.remove(smanager)
					break
			else:
				searching = False

	def stopConnections(self):
		""" p�ra todas as conex�es atualmente ativas """
		for smanager in self.connections:
			smanager.stop()

	def getConnections(self):
		""" retorna uma lista de conex�es criadas """
		return self.connections

	def canceledl(self):
		self._canceledl = True

	def getVideoTitle(self):
		return self.videoTitle

	def getUrl(self):
		return self.streamUrl

	def getVideoSize(self):
		return self.videoSize

	@staticmethod
	def getStreamManager( url):
		""" Procura pelo controlador de tranfer�nicia de arquivo de video"""
		smanager = None
		try:
			for sitename in gerador.Universal.get_sites():
				matchobj = gerador.Universal.patternMatch(sitename, url)
				if matchobj:
					smanager = gerador.Universal.get_control( sitename)
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
			for sitename in gerador.Universal.get_sites():
				matchobj = gerador.Universal.patternMatch(sitename, url)
				if matchobj:
					vmanager = gerador.Universal.get_video_control( sitename )
					break
		except AssertionError, err:
			raise AttributeError, _("Sem suporte para a url fornecida.")
		assert vmanager, _("url desconhecida!")
		return vmanager

	def intervSendoEnviado(self):
		return self.interval.send_info['sending']

	def numBytesRecebidos(self):
		""" retorna o numero total de bytes transferidos """
		return self.numTotalBytes

	def getBaseName(self):
		""" Nome do servidor fornecendo a stream de video corrente """
		return self.servername

	def salveInfoResumo(self):
		""" salva todos os dados necess�rios para o resumo do arquivo atual """
		with FileManager.lockReadWrite:
			self.removaConexoesInativas()
			listInterv = [] # coleta geral de informa��es.
			for smanager in self.getConnections():
				ident = smanager.ident

				# a conex�o deve estar ligada a um interv
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
		""" Configura a leitura da stream para um ponto aleat�rio dela """
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
		self.posLeitura = 0

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
		""" Informa as conex�es que um novo ponto da stream est� sendo lido """
		for smanager in self.getConnections(): # coloca as conex�es em estado ocioso
			if flag is True:
				smanager.fiqueEmEspera(True)
			elif smanager.estaProntoContinuar():
				# s� libera a conex�o da espera, quando ela confirmar
				# que entendeu a condi��o de reconfigura��o.
				smanager.fiqueEmEspera(False)

	def getStream(self):
		bytestream = ""
		if self.posLeitura < self.nBytesProntosEnvio:
			chunksize = 524288 # 512k
			if (self.posLeitura + chunksize) > self.nBytesProntosEnvio:
				chunksize = self.nBytesProntosEnvio - self.posLeitura

			bytestream, self.posLeitura = self.fileManager.read(self.posLeitura, chunksize)

			# cabe�alho da stream de v�deo(varia de 9 a 13 bytes).
			streamHeaderSize = self.videoManager.getStreamHeaderSize()
			if not self.streamHeader and streamHeaderSize != 0 and len(bytestream) > streamHeaderSize:
				self.streamHeader = bytestream[:streamHeaderSize]
		return bytestream

	def updateVideoInfo(self, args=None):
		""" Atualiza as vari�veis de transfer�ncia do v�deo. """
		startTime = time.time() # temporizador

		while self.updateRunning:
			try: # como self.interval acaba sendo deletado, a ocorrencia de erro � prov�vel
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

				# reinicia a atividade das conex�es
				self.notifiqueConexoes(False)
			except: time.sleep(3) # tempo de recupera��o

			time.sleep(0.1)
################################# STREAMANAGER ################################

# CONNECTION MANANGER: GERENCIA O PROCESSO DE CONEX�O
class StreamManager( threading.Thread):
	lockBlocoFalha = threading.Lock()
	lockBlocoConfig = threading.Lock()
	syncLockWriteStream = threading.Lock()

	# Esse lock tem um objetivo interessante. Ao iniciar um
	# arquivo pelo resumo, n�o existem dados sobre o arquivo
	# de v�deo, como os links de download. Assim, usando o lock,
	# somente uma conex�o pegar� esse dados, por causa dele.
	lockInicialize = threading.Lock()
	listStrErro = ["onCuePoint"]

	# ordem correta das infos
	listInfo = ["http", "estado", "indiceBloco", 
		        "numBytesFaltando", "velocidadeLocal"]

	def __init__(self, manage, noProxy=False, **params):
		""" params: {}
		ratelimit: limita a velocidade de sub-conex�es (limite em bytes)
		timeout: tempo de espera para se estabeler a conex�o (tempo em segundos)
		reconexao: n�mero de vezes que conex�o com o servidor, tentar� ser estabelecida.
		waittime: intervalo de tempo aguardado, quando houver falha na tentativa de conex�o.
		typechange: muda o tipo de conex�o(True ou False)
		"""
		threading.Thread.__init__(self)
		self.setDaemon(True)

		self.params = params
		self.manage = manage

		# conex�o com ou sem um servidor
		self.usingProxy = noProxy
		self.proxies = {}

		self.link = self.linkSeek = ""
		self.aguarde = [False, False]
		self.megaFile, self.isRunning = False, True
		self.numBytesLidos = 0

	def __setitem__(self, k, v):
		if not self.params.has_key(k):
			print "Aviso: \"%s\" ainda n�o existe."%k
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

			## evita a chamada ao m�todo getVideoInfo
			if self.wasStopped(): return

			if self.usingProxy == True:
				if videoManager.getVideoInfo(timeout=timeout):
					self.link = videoManager.getLink()
			else:
				self.proxies, self.link = proxyManager.getProxyLink(timeout=timeout)

			ip = self.proxies.get("http",_(u"Conex�o Padr�o"))
			globalInfo.set_info(self.ident, "http", ip)

	def stop(self):
		""" p�ra toda a atividade da conex�o """
		self.isRunning = False
		self.fixeFalhaTransfer(_(u"Parado pelo usu�rio"), 3)

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
		
		# no bytes 0 o tamanho do arquivo � o original
		if seekpos == 0: nbytes = 0
		# comprimento total(considerando os bytes removidos), da stream
		length = seekpos + contentLength - nbytes
		return seekmax == length

	def aguardeNotificacao(self):
		""" aguarda o processo de configura��o terminar """
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

				# Escreve os dados na posi��o resultante
				pos = start - self.manage.interval.get_offset() + self.numBytesLidos
				self.manage.fileManager.write(pos, stream)

				# quanto ja foi baixado da stream
				self.manage.numTotalBytes += nbytes
				self.manage.interval.send_info["nbytes"][start] += nbytes

	def inicieLeitura(self ):
		blockSizeLen = 1024; tempoInicialLocal = time.time()
		blockSize = self.manage.interval.get_block_size( self.ident )
		intervstart = self.manage.interval.get_start( self.ident)

		while self.numBytesLidos < blockSize and not self.wasStopped():
			try:
				# bloco de bytes do intervalo. Poder� ser dinamicamente modificado
				blockSize = self.manage.interval.get_block_size(self.ident)
				intervIndex = self.manage.interval.get_index(self.ident)
				if intervIndex < 0: raise AttributeError

				# condi��o atual da conex�o: Baixando
				globalInfo.set_info(self.ident, "estado", _("Baixando") )
				globalInfo.set_info(self.ident, "indiceBloco", intervIndex)

				# limita a leitura ao bloco de dados
				if (self.numBytesLidos + blockSizeLen) > blockSize:
					blockSizeLen = blockSize - self.numBytesLidos

				# inicia a leitura da stream
				before = time.time()
				streamData = self.streamSocket.read( blockSizeLen )
				after = time.time()

				streamLen = len(streamData) # n�mero de bytes baixados

				if self.esperaSolicitada(): # caso onde a seekbar � usada
					self.aguardeNotificacao(); break

				# o servidor fechou a conex�o
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

				# calcula a velocidade de transfer�ncia da conex�o
				globalInfo.set_info(self.ident, 'velocidadeLocal', 
								    self.calc_speed(tempoInicialLocal, time.time(), self.numBytesLidos) )

				# tempo do download
				self.manage.tempoDownload = self.calc_eta(start, time.time(), total, current)

				# calcula a velocidade global
				self.manage.velocidadeGlobal = self.calc_speed(start, time.time(),  current)

				if self.numBytesLidos == blockSize:
					if self.manage.interval.canContinue(self.ident) and not self.manage.isComplete():
						self.manage.interval.remove(self.ident)# removendo o intervalo completo
						self.configureConexao(); self.info_clear()# configurando um novo intervado
						intervstart = self.manage.interval.get_start(self.ident)
						tempoInicialLocal = time.time()# reiniciando as vari�veis

				# sem redu��o de velocidade para o intervalo pricipal
				elif self.manage.intervSendoEnviado() != intervstart:
					self.slow_down(tempoInicialLocal, self.numBytesLidos)
			except Exception, erro:
				self.fixeFalhaTransfer(_("Erro de leitura"), 2)
				break
		# -----------------------------------------------------
		try: self.manage.interval.remove(self.ident)
		except:pass
		try: self.streamSocket.close()
		except:pass
		self.info_clear()

	def removaConfigs(self, errorstring, errornumber):
		""" remove todas as configura��es, importantes, dadas a conex�o """
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
				# n�mero de bytes lidos, antes da conex�o apresentar o erro
				bytesnumber = self.numBytesLidos - (blockSize - (end - start))
				self.manage.interval.remove(self.ident)
		else: bytesnumber = 0
		ip = self.proxies.get("http", "default")

		# remove as configs de video geradas pelo ip. A falha pode ter
		# sido causada por um servidor inst�vel, lento ou negando conex�es.
		del self.manage.videoManager[ ip ]

		if ip != "default" and ((errornumber != 3 and errornumber == 1) or bytesnumber < 524288): # 512k
			self.manage.proxyManager.setBadIp( ip ) # tira a prioridade de uso do ip.
		return bytesnumber

	def fixeFalhaTransfer(self, errorstring, errornumber):
		globalInfo.set_info(self.ident, 'estado', errorstring)
		self.info_clear()

		bytesnumber = self.removaConfigs(errorstring, errornumber) # removendo configura��es
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

		globalInfo.set_info(self.ident,"http",self.proxies.get("http",_(u"Conex�o Padr�o")))

	def conecte(self):
		videoManager = self.manage.videoManager
		seekpos = self.manage.interval.get_start(self.ident)
		headerSize = videoManager.getStreamHeaderSize()
		streamSize = self.manage.getVideoSize()
		initTime = time.time()

		nfalhas = 0
		while nfalhas < self.params.get("reconexao",3) and not self.wasStopped():
			try:
				globalInfo.set_info(self.ident, "estado", _("Conectando"))
				waittime = self.params.get("waittime", 2)
				timeout = self.params.get("timeout", 25)

				# come�a a conex�o
				self.streamSocket = videoManager.conecte(
					self.linkSeek, proxies=self.proxies, timeout=timeout, login=False)

				# verifica a validade a resposta.
				is_valid = self.responseCheck(headerSize, 
				        seekpos, streamSize, self.streamSocket.headers)

				if self.streamSocket.code == 200 and is_valid:
					if seekpos > headerSize and headerSize != 0:
						self.streamSocket.read( headerSize )
					return True
				else:
					globalInfo.set_info(self.ident, "estado", _(u"Resposta inv�lida"))
					self.streamSocket.close(); time.sleep( waittime )
			except Exception, err:
				globalInfo.set_info(self.ident, "estado", _(u"Falha na conex�o"))
				time.sleep( waittime )

			# se passar do tempo de timeout o ip ser� descartado
			if (time.time() - initTime) > timeout: break
			else: initTime = time.time()

			nfalhas += 1
		return False # nao foi poss�vel conectar

	def configureConexao(self ):
		""" associa a conex�o a uma parte da stream """
		globalInfo.set_info(self.ident, "estado", _("Ocioso"))

		if not self.esperaSolicitada():
			with StreamManager.lockBlocoConfig:

				if self.manage.interval.numIntervPendentes() > 0:
					# associa um intervalo pendente(intervalos pendentes, s�o gerados em falhas de conex�o)
					self.manage.interval.associeIntervPendente( self.ident )

				else:
					# cria um novo intervalo e associa a conex�o.
					self.manage.interval.associeNovoInterv( self.ident )

					# como novos intervalos n�o s�o infinitos, atribui um novo, apartir de um j� existente.
					if not self.manage.interval.hasInterval( self.ident ):
						self.manage.interval.associeIntervDerivado( self.ident )

				# bytes lido do intervalo atual(como os blocos reduzem seu tamanho, o n�mero inicial ser� sempre zero).
				self.numBytesLidos = 0
		else:
			# aguarda a configura��o terminar
			self.aguardeNotificacao()

	@staticmethod
	def configureLink(link, seek, server):
		return gerador.get_with_seek(link, seek)
	
	def run(self):
		# configura um link inicial
		self.inicialize()

		while not self.wasStopped() and not self.manage.isComplete():
			try:
				# configura um intervalo para cada conexao
				self.configureConexao()

				if self.manage.interval.hasInterval( self.ident ):
					self.linkSeek = self.configureLink(self.link, 
										               self.manage.interval.get_start(self.ident), 
										               self.manage.getBaseName())

					# tenta estabelecer a conex�o como o servidor
					if self.conecte():
						# inicia a transfer�ncia de dados
						self.inicieLeitura()
					else:
						self.fixeFalhaTransfer(_("Incapaz de conectar"), 1)

				# estado ocioso
				else: time.sleep(1)

			except Exception, erro:
				print "Erro[Processando stream] %s" %erro

		# estado final da conex�o
		globalInfo.set_info(self.ident, "estado", _(u"Conex�o parada"))

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

		if self.usingProxy == True: # conex�o padr�o - sem proxy
			globalInfo.set_info(self.ident, "http", _(u"Conex�o Padr�o"))
		else:
			self.proxies = self.manage.proxyManager.proxyFormatado()
			globalInfo.set_info(self.ident, "http", self.proxies['http'])

	def fixeFalhaTransfer(self, errorstring, errornumber):
		globalInfo.set_info(self.ident, 'estado', errorstring)
		self.info_clear()

		typechange = self.params.get("typechange", False)
		proxyManager = self.manage.proxyManager

		bytesnumber = self.removaConfigs(errorstring, errornumber) # removendo configura��es
		if errornumber == 3: return # retorna porque a conexao foi encerrada
		time.sleep(0.5)

		globalInfo.set_info(self.ident, "estado", _("Reconfigurando"))
		time.sleep(0.5)

		if self.usingProxy:
			if typechange is True:
				self.proxies = proxyManager.proxyFormatado()
				self.usingProxy = False
		elif errornumber == 1 or bytesnumber < 524288:
			if typechange is True:
				self.usingProxy, self.proxies = True, {}
			else:
				self.proxies = proxyManager.proxyFormatado()
				self.usingProxy = False

		globalInfo.set_info(self.ident,"http",self.proxies.get("http",_(u"Conex�o Padr�o")))

	def conecte(self):
		videoManager = self.manage.videoManager
		seekpos = self.manage.interval.get_start( self.ident) # posi��o inicial de leitura
		reconexao = self.params.get("reconexao", 1)

		nfalhas = 0
		while nfalhas < reconexao:
			try:
				waittime = self.params.get("waittime", 2)
				reconexao = self.params.get("reconexao", 1)

				globalInfo.set_info(self.ident, "estado", _("Conectando"))
				data = videoManager.get_init_page( self.proxies) # pagina incial
				link = videoManager.get_file_link( data) # link de download
				tempo_espera = videoManager.get_count( data) # contador

				for second in range(tempo_espera, 0, -1):
					globalInfo.set_info(self.ident, "estado", _(u"Aguarde %02ds")%second)
					time.sleep(1)

				globalInfo.set_info(self.ident, "estado", _("Conectando"))

				self.streamSocket = videoManager.conecte(link, 
								                         proxies = self.proxies, headers={"Range":"bytes=%s-"%seekpos})

				if self.streamSocket.code == 200 or self.streamSocket.code == 206:
					if seekpos == 0: # anula o tamanho aproximado pelo real do arquivo
						tamanho_aproximado = self.manage.getVideoSize()
						tamanho_real = self.streamSocket.headers.get("Content-Length", tamanho_aproximado)
						self.manage.videoSize = long( tamanho_real )
					return True
				else:
					globalInfo.set_info(self.ident, "estado", _(u"Resposta inv�lida"))
					self.streamSocket.close()
					time.sleep( waittime )
			except Exception, err:
				globalInfo.set_info(self.ident, "estado", _(u"Falha na conex�o"))

				if hasattr(err, "code") and err.code == 503:
					return False

				time.sleep( waittime )
			nfalhas += 1
		return False #nao foi possivel conectar

	def run(self):
		# configura um link inicial
		self.inicialize()

		while self.isRunning and not self.manage.isComplete():
			try:
				# configura um intervalo para cada conexao
				self.configureConexao()

				if self.manage.interval.hasInterval( self.ident ):
					# tentando estabelece a conex�o como o servidor
					if self.conecte():
						self.inicieLeitura() # inicia a transferencia de dados
					else:
						self.fixeFalhaTransfer(_("Incapaz de conectar"), 1)

				# estado ocioso
				else: time.sleep(1)

			except Exception, erro:
				print "Erro[Processando stream] %s" %erro

		globalInfo.set_info(self.ident, "estado", _(u"Conex�o parada"))

########################### EXECU��O APARTIR DO SCRIPT  ###########################

if __name__ == '__main__':
	installTranslation() # instala as tradu��es

	ps = PackSearch(packetVersion="1.1.0")
	sucess = ps.search()

	if sucess is True:
		print "Novas atualizacoes encontradas"
		continue_ = raw_input("Continuar[yes ou no] ?")

		if continue_ == "yes":
			sucess, response = ps.packetDown()
			print response

			if sucess is True:
				continue_ = raw_input("Aplicar a atualizacao[yes ou no] ?")
				if continue_ == "yes":
					sucess, response = ps.update()
					print response

					print "Current Version: %s"%ps.getNewVersion()

					print "*"*25
					print "\n\n".join( ps.getLastChanges() )

					print "<> Clean all <>"
					ps.cleanUpdateDir()
					print "Finish sucess!!!"
				else:
					print "Cancelado"
		else:
			print "Cancelado"