# -*- coding: ISO-8859-1 -*-
import os
import re
import sys
import time
import urllib
import urllib2
import random
import threading
import generators
import socket
import manager

from main import settings
from main.app.util import base

try: _("test translation")
except: base.trans_install() # instala as traduções.

#######################################################################################

class Proxylist( generators._sitebase.ConnectionProcessor ):
	"""Trabalha extraindo proxies de paginas da web"""
	#----------------------------------------------------------------------
	def __init__(self):
		generators._sitebase.ConnectionProcessor.__init__(self)
		self.countIp = 0; self.name = "proxylist"
		manager.Info.add( self.name)
		
		self.cookie = {"Cookie": "cf_clearance=84d7c368a55ef2b26e6beb5ce041c935-1321375733-1800"}
		self.proxylist_url = "http://www.proxylist.net/list/0/0/1/0/%d"
		self.numPagina = 0

	def __del__(self):
		manager.Info.delete( self.name)

	def getProxies(self, data):
		listProxies = re.findall('<a href="/proxy/(\d+\.\d+\.\d+\.\d+:\d+)"', data)
		return listProxies
	
	def getWebPage(self, url, headers={}):
		try:
			fd = self.connect( url, headers=headers)
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
		manager.Info.set(self.name, self.name,
		    "%s pagina: %s numIP: %d"%(self.name, self.numPagina, len(proxies)))
		self.numPagina += 1
		return proxies
	
########################################################################
class Freeproxylists( generators._sitebase.ConnectionProcessor ):
	"""Trabalha extraindo proxies de paginas da web"""
	#----------------------------------------------------------------------
	def __init__(self):
		generators._sitebase.ConnectionProcessor.__init__(self)
		self.regexHostPort = re.compile('IPDecode\("(.*?)"\).*?(\d{1,5})', re.DOTALL)
		self.regexHost = re.compile("(\d{1,4}\.\d{1,4}\.\d{1,4}.\d{1,4})")
		self.countIp = 0; self.name = "freeproxylists"
		manager.Info.add( self.name)
		
		self.cookie = {"Cookie": "hl=en; pv=12; userno=20120614-007721"}
		self.cookie_url = " http://www.freeproxylists.net/cookie.php?page=%s"
		self.proxylist_url = "http://www.freeproxylists.net/?page=%s"
		self.numPagina = 1
		
	def __del__(self):
		manager.Info.delete( self.name)

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
			fd = self.connect(url, headers=headers)
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
		manager.Info.set(self.name, self.name,
		    "%s pagina: %s numIP: %d"%(self.name, self.numPagina, len(proxies)))
		self.numPagina += 1
		return proxies
	
########################################################################
class Xroxy( generators._sitebase.ConnectionProcessor ):
	def __init__(self):
		generators._sitebase.ConnectionProcessor.__init__(self)
		self.countIp = 0; self.name = "xroxy"
		manager.Info.add( self.name )
		
		self.xroxy_url ="http://www.xroxy.com/proxylist.php?port=&type="\
			"&ssl=&country=&latency=&reliability=&sort=reliability"\
			"&desc=true&pnum=%d#table"
		self.numPagina = 0

	def __del__(self):
		manager.Info.delete( self.name)

	def getProxies(self, webpage):
		host_port = re.findall("host=(\d{1,4}\.\d{1,4}\.\d{1,4}\.\d{1,4})&port=(\d{1,5})", webpage)
		return ["%s:%s"%(host, port) for host, port in host_port]
	
	def getWebPage(self, url):
		try:
			fd = self.connect( url )
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
		
		manager.Info.set(self.name, self.name, 
		    "%s pagina: %s numIP: %d"%(self.name, self.numPagina, len(proxies)))
		self.numPagina += 1
		return proxies

########################################################################
class ProxyControl(object):
	""" Controla a pesquisa de obtenção de ips """
	def __init__(self, searsh=False, **params):
		""" params: {}
		- filepath: local do arquivo de ips estáticos """
		self.info = ''
		self.listaIps = []
		self.params = params
		self.searsh = searsh
		
		if not self.searsh:
			self.listaSites = [Freeproxylists(), Proxylist(), Xroxy()]
		else:
			filepath = os.path.join(settings.APPDIR, "configs", "statics_ips.txt")
			filepath = self.params.get("filepath", filepath)
			self.listaIps = self.get_ips( filepath )
			
	def __str__(self):
		return self.info
	
	def get_ips(self, filepath):
		with open( filepath ) as file:
			ips = (line[:-1] for line in file.readlines())
		return ips
	
	def getNextIP(self):
		if not self.searsh:
			# preenche a lista de ips quando vazia
			if not self.listaIps: self.updateIPs()
			ip =  self.listaIps.pop(0)
		else:
			try: ip =  self.listaIps.next()
			except StopIteration: ip = ''
		return ip
	
	def updateIPs(self, staticList=False):
		self.info = ''; total = 0
		for site in self.listaSites:
			proxies = site.search()
			
			if proxies: self.listaIps.extend(proxies)
			self.info += manager.Info.get(site.name, site.name)
			self.info += "\n"
			total += len(proxies)
			
		self.info += "Total de ips: %d \n"%total
		return self.listaIps
	
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
		vManager = generators.Universal.getVideoManager( url )
		self.videoManager = vManager( url )
		
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
		SM = manager.StreamManager
		cache_size = 128
		index = 0
		
		while self.isRunning and index < num_of_tests:
			# retorna quando a meta de ips for alcaçada.
			if self.ctrSearch.getNumIps() >= num_of_ips: return
			try:
				seekpos = 1024 + random.randint(0, int(streamSize*0.75))
				
				streamSocket = self.videoManager.connect(
				    generators._sitebase.get_with_seek(streamLink, seekpos),
				    headers = {"Range": "bytes=%s-" %seekpos},
				    proxies = proxies, timeout = 30
					)
				
				data = streamSocket.read( cache_size )
				stream, header = SM.get_FLVheader(data, seekpos)
				
				# valida o cabeçalho de resposta
				isValid = SM.responseCheck(len(header), seekpos, streamSize, streamSocket.headers)
				
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
			
############################ EXECUCAO DO SCRIPT ############################
if __name__ == "__main__":
	response = raw_input("start new ip search(yes or no): ")
	if response == "yes":
		proxyControl = ProxyControl()
		
		filepath = os.path.join(settings.APPDIR, "configs", "statics_ips.txt")
		with open(filepath, "w", 0) as file:
			while True:
				proxyControl.updateIPs()
				
				print proxyControl, "\n", "|".join(proxyControl.listaIps)
				if len(proxyControl.listaIps) == 0: break
				
				for ip in proxyControl.listaIps:
					file.write(ip+"\n")
				proxyControl.listaIps = []
	else:
		print "Canceled..."