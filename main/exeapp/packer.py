# -*- coding: ISO-8859-1 -*-
import os, sys
import os.path
import zipfile
import configobj
import glob
import getopt
import platform
from manager import PROGRAM_SYSTEM, PROGRAM_VERSION

class Packet:
	#----------------------------------------------------------------------
	def __init__(self, *args, **params):
		""" monta o pacote de atualização """
		self.pyFiles = [
		    "manager", "decrypter", "gerador",
		    "browser", "jwPlayer", "proxy", 
		    "bugs"
		]
		
		self.pyFilesPackage = ["window"]
		self.mediaFile = ["imagens"]
		
		self.internalFile = [ "changes.txt",
		    os.path.join("locale","en","LC_MESSAGES"),
		    os.path.join("locale","es","LC_MESSAGES"),
		    os.path.join("locale","pt_BR","LC_MESSAGES"),
		]
		
		self.params = params
		self.args = args
		
		if os.path.exists("time_changes.cfg"):
			self.configs = configobj.ConfigObj("time_changes.cfg")
		
	def salveTabela(self):
		""" salva a nova tabela de modificações """
		with open("time_changes.cfg", "w") as fileTimer:
			self.configs.write( fileTimer )
	
	def getFileName(self, path, fullname=False):
		"""
		fullname=False [C:\\diretório\\arquivo.txt -> arquivo]
		fullname=True  [C:\\diretório\\arquivo.txt -> arquivo.txt]
		"""
		filename = path.rsplit(os.sep, 1)[-1]
		if not fullname:
			filename = filename.rsplit(".", 1)[0]
		return filename
	
	def makeTableScripts(self, fileTimer):
		""" cria a tabela de tempo de scritps .py """
		for filename in self.pyFiles:
			filepath = os.path.join(os.getcwd(), filename)+".py"
			mtime = os.path.getmtime( filepath )
			fileTimer.write("%s = %.4f\n"%(filename, mtime))
			
	def makeTableScriptPacket(self, fileTimer):
		""" cria a tabela de tempo de pacotes python """
		for dirname in self.pyFilesPackage:
			dirFullPath = os.path.join(os.getcwd(), dirname)
			filePathList = glob.glob(os.path.join(dirFullPath,"*.py"))
			
			for filepath in filePathList:
				filename = self.getFileName( filepath )
				mtime = os.path.getmtime( filepath )
				name = "%s.%s"%(dirname, filename)
				fileTimer.write("%s = %.4f\n"%(name, mtime))
				
	def makeTableFiles(self, fileTimer):
		""" cria a tabela de tempo de arquivos """
		for dirFileName in self.internalFile:
			dirFilePath = os.path.join(os.getcwd(),dirFileName)
			
			if os.path.isdir( dirFilePath ):
				filePathList = glob.glob(os.path.join(dirFilePath,"*"))
				
				for filepath in filePathList:
					filename = self.getFileName(filepath, True)
					mtime = os.path.getmtime( filepath )
					name = os.path.join(dirFileName, filename)
					
					fileTimer.write("%s = %.4f\n"%(name, mtime))
			else:
				mtime = os.path.getmtime( dirFilePath )
				filename = self.getFileName( dirFilePath )
				fileTimer.write("%s = %.4f\n"%(filename, mtime))
			
	def crieNovaTabela(self):
		""" guarda, como uma tabela, o tempo de modificação atual do arquivo """
		with open("time_changes.cfg", "w") as fileTimer:
			try:
				self.makeTableScripts(fileTimer)
			except Exception, err:
				print "Error[scripts] %s"%err
				
			try:
				self.makeTableScriptPacket(fileTimer)
			except Exception, err:
				print "Error[script packet] %s"%err
			
			try:
				self.makeTableFiles(fileTimer)
			except Exception, err:
				print "Error[files] %s"%err
				
	def removeFile(self, path):
		if os.path.isfile( path ):
			try:
				os.remove( path )
				print "\tremoved: %s"%path
			except Exception, err:
				print "\tError[remove] %s"%(path, err)
		else: print "Not is file: %s"%path
		
	def delOldPyc(self):
		""" remove arquivos de extesão .pyc, 
		para foçar PyZipFile a criar um arquivo novo.
		"""
		# remove .pyc do diretório corrente.
		pycFilesList = glob.glob(os.path.join(os.getcwd(),"*.pyc"))
		if len(pycFilesList) > 0:
			print os.getcwd()
			
		for filepath in pycFilesList:
			self.removeFile( filepath )
			
		# remove .pyc dos pacotes
		for package in self.pyFilesPackage:
			# caminho completo do pacote python
			packagePath = os.path.join(os.getcwd(), package)
			
			if os.path.isdir( packagePath ):
				# lista de arquivos com extensão .pyc
				pycFilesList = glob.glob(os.path.join(packagePath,"*.pyc"))
				
				if len(pycFilesList) > 0:
					print "Packet: %s"%packagePath
				
				for filepath in pycFilesList:
					self.removeFile( filepath )
			
	def packageChanged(self, packageName, packagePath):
		""" caso algum scrip .py do pacote sofrer modificação, 
		todo o pacote será considerado modificado """
		isChanged = False
		pyFilesList = glob.glob(os.path.join(packagePath,"*.py"))
		
		for filepath in pyFilesList:
			filename = "%s.%s"%(packageName, self.getFileName( filepath ))
			mtime = os.path.getmtime( filepath )
			
			if mtime > self.configs.as_float( filename ):
				# atualizando o novo tempo de modificação
				self.configs[ filename ] = "%.4f"%mtime
				isChanged = True
				
		return isChanged
	
	def addScriptFiles(self, zipPacket):
		for filename in self.pyFiles:
			filepath = os.path.join(os.getcwd(), filename) + ".py"
			
			mtime = os.path.getmtime( filepath )
			
			if mtime > self.configs.as_float( filename ):
				zipPacket.writepy( filepath )
				# atualizando o novo tempo de modificação
				self.configs[ filename ] = "%.4f"%mtime
				print "\tAdicionado ao pacote: %s"%filepath
				
	def addScriptPacket(self, zipPacket):
		for dirname in self.pyFilesPackage:
			dirFullPath = os.path.join(os.getcwd(), dirname)
			# salva o pacote baseado em alguma mudança interna.
			if self.packageChanged(dirname, dirFullPath):
				zipPacket.writepy( dirFullPath )
				print "\tAdicionado ao pacote: %s"%dirFullPath
			
	def addMediaFiles(self, zipPacket):
		for dirname in self.mediaFile:
			dirFullPath = os.path.join(os.getcwd(), dirname)
			filePathList = glob.glob(os.path.join(dirFullPath, "*"))
			
			for filepath in filePathList:
				filename = self.getFileName(filepath)
				
				if filename in self.args:
					# ordem do arquivo dentro do zip
					relativeFilePath = os.path.join(
				        dirname, self.getFileName(filepath, fullname=True))
					
					zipPacket.write(filepath, relativeFilePath)
					print "\tAdicionado arquivo: %s"%relativeFilePath
				
	def addInternalFile(self, zipPacket):
		for dirFileName in self.internalFile:
			dirFilepath = os.path.join(os.getcwd(),dirFileName)
			
			if os.path.isdir( dirFilepath ):
				filePathList = glob.glob(os.path.join(dirFilepath, "*"))
				
				for filepath in filePathList:
					mtime = os.path.getmtime( filepath )
					
					# ordem do arquivo dentro do zip
					relative = os.path.join(dirFileName,self.getFileName(filepath, fullname=True))
					
					if mtime > self.configs.as_float( relative ):
						zipPacket.write(filepath, relative)
						self.configs[ relative ] = "%.4f"%mtime
						print "\tAdicionado arquivo: %s"%relative
			else:
				# nome do arquivo sem extensão
				filename = self.getFileName( dirFilepath )
				mtime = os.path.getmtime( dirFilepath )
				if mtime > self.configs.as_float( filename ):
					zipPacket.write( dirFileName )
					self.configs[ filename ] = "%.4f"%mtime
					print "\tAdicionado arquivo: %s"%dirFileName				
				
	def createPacket(self):
		programVersion = self.params.get("programVersion", '0.0.0')
		packetVersion = self.params.get("packetVersion", '0.0.0')
		
		packetPath = os.path.join(os.getcwd(),
		    "packet_%sv%s_%s.zip"%(PROGRAM_SYSTEM[platform.system()], 
		                           packetVersion, programVersion))
		### ====================================================================
		print "Pacote v%s"%packetVersion
		
		with zipfile.PyZipFile(packetPath,"w") as zipPacket:
			try:
				self.addScriptFiles(zipPacket)
			except Exception, err:
				print "Erro[scripts] %s"%err
				
			try:
				self.addScriptPacket(zipPacket)
			except Exception, err:
				print "Erro[script packet] %s"%err
				
			try:
				self.addMediaFiles(zipPacket)
			except Exception, err:
				print "Erro[media] %s"%err
				
			try:
				self.addInternalFile(zipPacket)
			except Exception, err:
				print "Erro[internal] %s"%err	
		### ====================================================================
		print "Finalizando..."
		
		try:
			self.salveTabela()
		except Exception, err:
			print "Erro[Tabela]: %s"%err
			
if __name__ == "__main__":
	msg = """
Lista de opcoes:
--pkv=0.0.0 -> versao do pacote.
--pgv=0.0.0 -> versao do programa.
--cnt=true  -> criar nova tabela de modificacoes.
-h          -> exibe esssa ajuda.
a b c d e   -> lista arbitraria de arquivos.
"""
	def helpPrint(): print msg
	
	try:
		optlist, args = getopt.getopt(sys.argv[1:], "h", ["pkv=","pgv=","cnt="])
		params = dict(optlist)
	except getopt.GetoptError, err:
		print "GetoptError: %s"%err
		sys.exit(2)
		
	if not optlist or params.has_key("-h"):
		helpPrint(); sys.exit(0)
		
	packet = Packet(*args,
	    packetVersion = params.get("--pkv","0.0.0"),
	    programVersion= params.get("--pgv","0.0.0")
	)
	
	bool_map = {"1":True,"0":False,"true":True,"false":False}
	if not bool_map[ params.get("--cnt","0") ]:
		# remove os .pyc, antigos
		packet.delOldPyc()
		
		packet.createPacket()
	else:
		packet.crieNovaTabela()
		print "Uma nova tabela de moficacoes foi criada."
