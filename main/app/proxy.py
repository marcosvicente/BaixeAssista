# -*- coding: ISO-8859-1 -*-
import os
import time
import random
import threading
import generators
from main import settings
from main.app.util import base, sites

try: _("test translation")
except: base.trans_install() # instala as traduções.

########################################################################
class ProxyControl(object):
	""" Controla a pesquisa de obtenção de ips """
	
	def __init__(self, searsh=False, **params):
		""" params: {}
		- filepath: local do arquivo de ips estáticos
		"""
		self.params = params
		filepath = os.path.join(settings.APPDIR, "configs", "statics_ips.txt")
		self.iplist = self.gen_iplist(params.get("filepath", filepath))
		
	def gen_iplist(self, filepath):
		with open( filepath ) as fileobj:
			ips = (line[:-1] for line in fileobj.readlines())
		return ips
	
	def getNextIP(self):
		try: ip = self.iplist.next()
		except StopIteration: ip = ""
		return ip
	
########################################################################
class CtrSearch(object):
	#----------------------------------------------------------------------
	def __init__(self, **params):
		""" params: {}
		- numips: número de ips que devem ser encontrados(tipo int).
		- filepath: local para o arquivo da nova lista de ips.
		"""
		self.params = params
		self.connections = []
		self.ips = []
		self.log = ""
		
	def __del__(self):
		del self.params
		del self.connections
		del self.ips, self.log
		
	def getLog(self):
		return self.log
	
	def setLog(self, info):
		self.log = info
		
	def getNumIps(self):
		""" retorna o número de ips válidos já encontrados """
		return len(self.ips)
	
	def addConnection(self, refer):
		""" refer: guarda a referêcia para o objeto conexão """
		self.connections.append( refer)
		
	def stopConnections(self):
		for connection in self.connections:
			connection.stop()
			
	def addNewIp(self, ip):
		self.ips.append(ip)
		
	def waitConnections(self):
		""" espera todas as conexões pararem """
		alive = True
		while alive:
			for connection in self.connections:
				if connection.isAlive():
					alive = True; break
			else: alive = False
			time.sleep(1)
			
	def isSearching(self):
		""" avalia se todas as conexões já foram paradas """
		alive = True
		for connection in self.connections:
			if connection.isAlive():
				alive = True; break
		else: alive = False
		return alive
	
	def save(self):
		""" salva a lista de ips obtidos """
		if self.getNumIps() > int(self.params.get("numips",0)/2):
			# caminho completo para o arquivo de ips
			filepath = os.path.join(settings.APPDIR, "configs", "ipSP.cfg")
			filepath = self.params.get("filepath", filepath)
			
			with open(filepath, "w", buffering=0) as file:
				try:
					# irá salvar dos servidores mais rápidos, para os mais lentos.
					self.ips.sort(reverse=True)
					for timer, ip in self.ips: 
						file.write("%s\n"%ip)
						
					self.log = _(u"Nova lista de ips criada com sucesso!")
				except Exception as e:
					self.log = _(u"Erro salvando ips: %s")%e
		else:
			self.log = _(u"Erro: número de ips, insuficientes.")
		
########################################################################
class TesteIP( threading.Thread ):
	lockSucess = threading.Lock()
	lockNextIP = threading.Lock()
	
	def __init__(self, proxyControl, ctrSearch, params):
		threading.Thread.__init__(self)
		self.setDaemon(True) #termina com o processo principal
		
		self.isRunning = True
		
		self.params = params
		self.ctrSearch = ctrSearch
		self.proxyControl = proxyControl
		
		# objeto que trabalha as informações dos vídeos
		url = self.params.get("url","")
		videoManager = generators.Universal.getVideoManager( url )
		self.videoManager = videoManager( url )
		
	def stop(self):
		self.isRunning = False
	
	def start_read(self, address):
		proxies = {"http": "http://%s"%address}
		
		if self.videoManager.getVideoInfo(1, proxies=proxies, timeout=15):
			streamSize = self.videoManager.getStreamSize()
			streamLink = self.videoManager.getLink()
		else:
			del self.videoManager[ address ]
			return
		# ----------------------------------------------------------------
		block_size = self.params.get("bytes_block_test", 32768)
		num_of_tests = self.params.get("num_of_tests", 5)
		num_of_ips = self.params.get("num_of_ips", 10)
		sucess_len = 0; speed_list = []
		cache_size = 128
		index = 0
		
		while self.isRunning and index < num_of_tests:
			# retorna quando a meta de ips for alcaçada.
			if self.ctrSearch.getNumIps() >= num_of_ips: return
			try:
				seekpos = 1024 + random.randint(0, int(streamSize*0.75))
				
				streamSocket = self.videoManager.connect(
				   	sites.get_with_seek(streamLink, seekpos),
				    headers = {"Range": "bytes=%s-" %seekpos},
				    proxies = proxies, timeout = 30)
				
				data = streamSocket.read( cache_size )
				stream, header = self.videoManager.get_stream_header(data, seekpos)
				
				# valida o cabeçalho de resposta
				isValid = self.videoManager.check_response(len(header), seekpos, 
														   streamSize, streamSocket.headers)
				
				if isValid and (streamSocket.code == 200 or streamSocket.code == 206):
					before = time.time(); stream = streamSocket.read(block_size)
					after  = time.time(); streamLen = len(stream)
					
					if streamLen == block_size:
						speed = float(streamLen)/(after - before)
						speed_list.append( speed )
						# conta o número de testes, que obtiveram sucesso
						sucess_len += 1
				streamSocket.close()
			except Exception as err:
				print address, err
				sucess_len -= 1
			index += 1
			
		# um erro de tolerância
		if num_of_tests - sucess_len  < 2:
			with self.lockSucess:
				# média de todas as velocidades alcançadas
				average = reduce(lambda x, y: x + y, speed_list)
				
				# média global da soma de todas as velocidades
				average =  average / len(speed_list)
				
				# i ip é guardado com sua média global de velociade, 
				# pois ela servirá como base de comparação.
				self.ctrSearch.addNewIp((average, address))
				
				# log informativo
				log = _("%02d de %02d")
				log = log % (self.ctrSearch.getNumIps(), num_of_ips)
				self.ctrSearch.setLog( log )
				print self.ctrSearch.getLog()
				
		# remove a relação do ip com as configs da instância.
		del self.videoManager[ proxies["http"] ]
		
	def run(self):
		num_of_ips = self.params.get("num_of_ips", 0)
		while self.isRunning and self.ctrSearch.getNumIps() < num_of_ips:
			try:
				# o bloqueio do lock, evita teste duplo.
				with TesteIP.lockNextIP:
					ip = self.proxyControl.getNextIP()
				if not ip: break # lista de ips esgotada
				self.start_read( ip )
			except:
				pass