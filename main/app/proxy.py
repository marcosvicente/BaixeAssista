# -*- coding: ISO-8859-1 -*-
import os
import re
import sys
import time
import urllib
import urllib2
import random
import threading
import gerador
import socket
import manager

from main import settings

try: 
	_("test translation")
except:
	# *** instala as traduções
	manager.installTranslation()

# A versão será mantida pelo módulo principal
PROGRAM_VERSION = manager.PROGRAM_VERSION
#######################################################################################

class Proxylist( gerador.ConnectionProcessor ):
	"""Trabalha extraindo proxies de paginas da web"""
	#----------------------------------------------------------------------
	def __init__(self):
		gerador.ConnectionProcessor.__init__(self)
		
		self.countIp = 0
		self.name = "proxylist"
		manager.globalInfo.add_info( self.name)
		self.cookie = {"Cookie": "cf_clearance=84d7c368a55ef2b26e6beb5ce041c935-1321375733-1800"}

		self.proxylist_url = "http://www.proxylist.net/list/0/0/1/0/%d"
		self.numPagina = 0

	def __del__(self):
		manager.globalInfo.del_info( self.name)

	def getProxies(self, data):
		listProxies = re.findall('<a href="/proxy/(\d+\.\d+\.\d+\.\d+:\d+)"', data)
		return listProxies
	
	def getWebPage(self, url, headers={}):
		try:
			fd = self.conecte( url, headers=headers)
			webpage = fd.read()
			fd.close()
		except: webpage = ""
		return webpage
	
	def search( self):
		url = self.proxylist_url % self.numPagina
		
		if self.numPagina > 1 and (self.countIp / self.numPagina) < 10:
			return [] # lista de ips esgotada
		
		webpage = self.getWebPage(url, self.cookie)
		proxies = self.getProxies( webpage )
		
		self.countIp += len(proxies)
		
		manager.globalInfo.set_info(self.name, self.name,
		    "%s pagina: %s numIP: %d"%(self.name, self.numPagina, len(proxies)))

		self.numPagina += 1
		return proxies
	
########################################################################
class Freeproxylists( gerador.ConnectionProcessor ):
	"""Trabalha extraindo proxies de paginas da web"""
	#----------------------------------------------------------------------
	def __init__(self):
		gerador.ConnectionProcessor.__init__(self)
		self.regexHostPort = re.compile('IPDecode\("(.*?)"\).*?(\d{1,5})', re.DOTALL)
		self.regexHost = re.compile("(\d{1,4}\.\d{1,4}\.\d{1,4}.\d{1,4})")
		
		self.countIp = 0
		
		self.name = "freeproxylists"
		manager.globalInfo.add_info( self.name)
		
		self.cookie = {"Cookie": "hl=en; pv=12; userno=20120614-007721"}
		self.cookie_url = " http://www.freeproxylists.net/cookie.php?page=%s"
		self.proxylist_url = "http://www.freeproxylists.net/?page=%s"
		self.numPagina = 1
		
	def __del__(self):
		manager.globalInfo.del_info( self.name)

	def getProxies(self, webpage):
		host_port = []
		for host, port in self.regexHostPort.findall( webpage ):
			host = urllib.unquote_plus(host)
			matchobj = self.regexHost.search(host)
			if matchobj:
				host_port.append(
				    "%s:%s"%(matchobj.group(1), port)
				)
		return host_port
	
	def getWebPage(self, url, headers={}):
		try:
			fd = self.conecte(url, headers=headers)
			webpage = fd.read()
			fd.close()
		except: webpage = ""
		return webpage
	
	def search( self):
		url = self.proxylist_url % self.numPagina
		
		if self.numPagina > 1 and (self.countIp / self.numPagina) < 10:
			return [] # lista de ips esgotada
		
		webpage = self.getWebPage(url, self.cookie)
		proxies = self.getProxies( webpage )
		
		if not proxies:
			url = self.cookie_url % self.numPagina
			webpage = self.getWebPage(url, self.cookie)
			proxies = self.getProxies( webpage )
			
		self.countIp += len(proxies)
		
		manager.globalInfo.set_info(self.name, self.name,
		    "%s pagina: %s numIP: %d"%(self.name, self.numPagina, len(proxies)))

		self.numPagina += 1
		return proxies
	
########################################################################
class Xroxy( gerador.ConnectionProcessor ):
	
	def __init__(self):
		gerador.ConnectionProcessor.__init__(self)
		
		self.countIp = 0
		
		self.name = "xroxy"
		manager.globalInfo.add_info( self.name )
		
		self.xroxy_url ="http://www.xroxy.com/proxylist.php?port=&type="\
			"&ssl=&country=&latency=&reliability=&sort=reliability"\
			"&desc=true&pnum=%d#table"
		self.numPagina = 0

	def __del__(self):
		manager.globalInfo.del_info( self.name)

	def getProxies(self, webpage):
		host_port = re.findall("host=(\d{1,4}\.\d{1,4}\.\d{1,4}\.\d{1,4})&port=(\d{1,5})", webpage)
		return ["%s:%s"%(host, port) for host, port in host_port]
	
	def getWebPage(self, url):
		try:
			fd = self.conecte( url )
			webpage = fd.read()
			fd.close()
		except: webpage = ""
		return webpage
	
	def search( self):
		url = self.xroxy_url %self.numPagina
		
		if self.numPagina > 1 and (self.countIp / self.numPagina) < 10:
			return [] # lista de ips esgotada
		
		webpage = self.getWebPage( url )
		proxies = self.getProxies( webpage )
		
		self.countIp += len(proxies)
		
		manager.globalInfo.set_info(self.name, self.name, 
		    "%s pagina: %s numIP: %d"%(self.name, self.numPagina, len(proxies)))
		
		self.numPagina += 1
		return proxies

########################################################################
class ProxyControl:
	def __init__(self, useStaticList=False):
		""" controla a pesquisa de obtenção de ips """
		self.useStaticList = useStaticList
		self.info = ""; self.listaIps = []
		
		if not useStaticList:
			self.listaSites = [Freeproxylists(), Proxylist(), Xroxy()]
		else:
			with open(os.path.join(settings.APPDIR,"configs","statics_ips.txt")) as staticFile:
				self.listaIps = (line[:-1] for line in staticFile.readlines())
				
	def __str__(self):
		return self.info

	def getNextIP(self):
		if not self.useStaticList:
			# preenche a lista de ips quando vazia
			if not self.listaIps: self.updateIPs()
			ip =  self.listaIps.pop(0)
		else:
			try:
				ip =  self.listaIps.next()
			except StopIteration:
				ip = ""
		return ip
	
	def updateIPs(self, staticList=False):
		self.info = ""; total = 0
		for site in self.listaSites:
			proxies = site.search()
			
			if proxies: self.listaIps.extend(proxies)
			self.info += manager.globalInfo.get_info(site.name, site.name)
			self.info += "\n"
			
			total += len(proxies)
			
		self.info += "Total de ips: %d \n"%total
		return self.listaIps
	
########################################################################
class Anonimidade:
	""" Classe com o propósito de testar a anonimidade de um endereço IP de um servidor proxy.
	Ips anônimos ocultam informações que permitiriam detectar o ip do computador cliente. """
	
	def __init__(self):
		self.urlsMyIP = ["http://www.nossoip.com/", 
		                 "http://www.formyip.com/",
		                 "http://www.meuenderecoip.com/",
		                 "http://meuip.gratuita.com.br/",
		                 "http://meuip.net/"]
		
		self.userIP = self.getUserIP()
		if not self.userIP: raise AttributeError, "INPACAPAZ DE OBTER O IP DA REDE!"

	def getIPInfo(self, proxy=None, timeout= 10):
		""" verifica a anonimidade do ip do servidor proxy """
		if proxy: proxy = {"http" : "http://%s"%proxy}
		ipSite = "" # ip encontrado no site

		for siteUrl in self.urlsMyIP:
			try:
				opener = urllib2.build_opener( urllib2.ProxyHandler( proxy ))
				pageIP = opener.open( siteUrl, timeout = timeout)
				data = pageIP.read(); pageIP.close(); opener.close()
				ipSite = re.search("(\d+\.\d+\.\d+\.\d+)", data).group(1)
				break
			except: pass

		return ipSite

	# obtem o IP da conexao padrao
	def getUserIP(self):
		try: myIP = socket.gethostbyname(socket.gethostname())
		except: myIP = self.getIPInfo()
		return myIP

	# testa se o ip é do tipo anonimo
	def isAnonimo(self, proxy):
		""" Testa se o ip é do tipo anônimo """
		proxyIP = self.getIPInfo(proxy = proxy)
		if proxyIP and proxyIP != self.userIP: return True
		return False
	
	
########################################################################
class TestControl:
	""""""
	#----------------------------------------------------------------------
	def __init__(self, **params):
		"""params={}
		numips: número de ips que devem ser encontrados(tipo int).
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
	
	def salveips(self):
		""" salva a lista de ips obtidos """
		try:
			# caminho completo para o arquivo de ips
			path = os.path.join(settings.APPDIR, "configs", "ipSP.cfg")
			
			with open(path, "w", buffering=0) as ip_file:
				# irá salvar dos servidores mais rápidos, para os mais lentos.
				self.ips.sort(reverse=True)
				
				# número de ips que deveriam ser encontrados
				numips = self.params.get("numips", 0)
				
				if len(self.ips) > int(numips / 2):
					for t, ip in self.ips: ip_file.write("%s\n" % ip)
					self.log = _("Nova lista de ips criada com sucesso!")
				else: self.log = _("Erro: número de ips, insuficientes.")
		except Exception, err:
			self.log = _("Erro salvando ips: %s")%err
			
########################################################################
class TesteIP( threading.Thread ):
	lockSucess = threading.Lock()
	lockNextIP = threading.Lock()
	
	def __init__(self, proxyControl, testControl, params):
		threading.Thread.__init__(self)
		self.setDaemon(True) #termina com o processo principal
		
		self.params = params
		self.isRunning = True
		
		self.proxyControl = proxyControl
		self.testControl = testControl
		self.anonimidade = Anonimidade()
		
		# objeto que trabalha as informações dos vídeos
		url = self.params.get("URL","")
		vmanager = manager.Manage.getVideoManager(url)
		self.videoManager = vmanager(url)
		
	def stop(self):
		self.isRunning = False
		
	def start_len_test(self, address):
		proxies = {"http": "http://%s"%address}

		if self.videoManager.getVideoInfo(1, proxies= proxies, timeout=15):
			streamSize = self.videoManager.getStreamSize()
			streamLink = self.videoManager.getLink()
		else:
			del self.videoManager[ address ]
			return
		
		# params
		speed_list = []
		sucess_len = test_count = 0
		
		num_bytes = self.videoManager.getStreamHeaderSize()
		block_size = self.params.get("numBytesTeste", 32768)
		num_max_ips = self.params.get("metaProxies", 0)
		max_test = self.params.get("numMaxTestes", 5)
		
		while test_count < max_test:
			try:
				seekpos = random.randint(num_bytes, int(streamSize*0.75))
				link_seek = manager.StreamManager.configureLink(streamLink, seekpos, self.videoManager.basename)
				fd = self.videoManager.conecte(link_seek, proxies=proxies, timeout=15)
				
				# valida o cabeçalho de resposta
				is_valid = manager.StreamManager.responseCheck(
				    num_bytes, seekpos, streamSize, fd.headers)
				
				if fd.code == 200 and is_valid:
					before = time.time(); stream = fd.read(block_size)
					after  = time.time(); stream_len = len(stream)
					
					if stream_len == block_size:
						speed = float(stream_len)/(after - before)
						speed_list.append( speed )
						# conta o número de testes, que obtiveram sucesso
						sucess_len += 1
				fd.close()
			except: pass
			
			# conta o número de testes
			test_count += 1 
			
			# pára o teste de leitura
			if not self.isRunning or self.testControl.getNumIps() >= num_max_ips:
				return
			
		# um erro de tolerância
		if max_test - sucess_len  < 2:
			with self.lockSucess:
				# média de todas as velocidades alcançadas
				average = reduce(lambda x, y: x + y, speed_list)
				
				# média global da soma de todas as velocidades
				average =  average / len(speed_list)
				
				# i ip é guardado com sua média global de velociade, 
				# pois ela servirá como base de comparação.
				self.testControl.addNewIp((average, address))
				
				# log informativo
				log = _("%02d de %02d")
				log = log % (self.testControl.getNumIps(), num_max_ips)
				self.testControl.setLog( log )
			
		# remove a relação do ip com as configs da instância.
		del self.videoManager[ proxies["http"] ]
		print self.testControl.getLog()
		
	def run( self):
		num_max_ips = self.params.get("metaProxies", 0)
		while self.isRunning and self.testControl.getNumIps() < num_max_ips:
			try:
				# o bloqueio do lock, evita teste duplo.
				with TesteIP.lockNextIP:
					address = self.proxyControl.getNextIP()
				
				# lista de ips esgotada
				if not address: break
				
				## if self.anonimidade.isAnonimo( address):
				self.start_len_test( address)
			except: pass
			
############################ EXECUCAO DO SCRIPT ############################

if __name__ == "__main__":
	response = raw_input("start new ip search(yes or no): ")
	if response == "yes":
		proxyControl = ProxyControl()
		
		filepath = os.path.join(settings.APPDIR, "configs", "statics_ips.txt")
		with open(filepath, "w", 0) as fileObj:
			while True:
				proxyControl.updateIPs()
				
				print proxyControl, "\n", "|".join(proxyControl.listaIps)
				if len(proxyControl.listaIps) == 0: break
				
				for ip in proxyControl.listaIps:
					fileObj.write(ip+"\n")
					
				proxyControl.listaIps = []
	else:
		print "Canceled..."