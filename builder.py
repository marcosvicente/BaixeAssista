# -*- coding: UTF-8 -*-
import os, sys
import subprocess
import packer
import compileall
import shutil
import re

BUILD_DIR = os.path.join(os.getcwd(), os.environ["HOMEPATH"], "BaixeAssistaBuild") # build exe
DIST_DIR = os.path.join(BUILD_DIR, "dist") # final exe
TARGET_DIR = packer.TARGET_DIR

# ---------------------------------------------------------------
def find_compiler(compilername = "pyinstaller.py"):
	""" busca o caminho completo para o compilador(pyinstaller) """
	allpaths = os.environ["path"]
	for path in allpaths.split(";"):
		# provavel caminho do compilador
		compilerpath = os.path.join(path, compilername)
		if os.path.isfile( compilerpath ):
			return compilerpath
	return ""

# ---------------------------------------------------------------
def start_build():
	""" inica a contrução do executável """
	COMPILER = 'python "%s"' % find_compiler()
	COMMANDS = '-c --out="%s" --icon=%s --onefile BaixeAssista.py'%(BUILD_DIR, "movies.ico")
	CMD = COMPILER + " " + COMMANDS
	
	# remove all .pyc / .pyo
	packer.clean_all_nopy( TARGET_DIR )
	
	print "COMPILER: ", COMPILER
	print "COMMANDS: ", COMMANDS
	print "CMD: "     , CMD
	print "\nSTARTING BUILD"
	
	retcode = subprocess.call( CMD )
	print "Compile sucess: %d" % retcode
	return retcode

# ---------------------------------------------------------------
def copy_to_dest(source, destination):
	""" copia os arquivo do executavel para a pasta de distribuição """
	sourcedir = os.path.split( source )[0]
	
	for root, dirs, files in os.walk(source):
		try:
			relativedir = root.split(sourcedir + os.sep)[-1]
			destdir = os.path.join(destination, relativedir)
			
			# não inclui pastas que contenham o arquivo "__ignore__"
			if "__ignore__" in files: continue
			
			if not os.path.exists( destdir ):
				print "Making dir: ", destdir
				os.mkdir( destdir )
			else:
				print "Dir already exist: ", destdir
				
			for filename in files:
				if filename == "__pass__": continue
				filepath = os.path.join(root, filename)
				filedestdir = os.path.join(destdir, filename)
				
				if re.match(".+py$", filename):
					# copiando os arquivos já pré-compliados.
					compileall.compile_file(filepath, force=True)
					src = filepath.replace(".py", ".pyc")
					dest = filedestdir.replace(".py", ".pyc")
					shutil.copy(src, dest)
				else:
					shutil.copy(filepath, filedestdir)
		except Exception, err:
			print "Err[Exporting files] %s"%err
			exit(1)

# ---------------------------------------------------------------
if __name__ == "__main__":
	if not os.path.exists(BUILD_DIR):
		os.mkdir( BUILD_DIR )	

	if start_build() == 0:
		print "Compile sucessfully!"
		
		print "Exporting files to exe"
		packer.clean_all_nopy( TARGET_DIR )
		copy_to_dest( TARGET_DIR, DIST_DIR )
		
		try:
			os.chdir( DIST_DIR ) # vai para o diretorio do executável.
			subprocess.call(os.path.join(DIST_DIR, "BaixeAssista.exe"))
		except Exception, err:
			print "Err[exe start] %s"%err
	else:
		print "Error Compiling..."
	raw_input("Press enter to exit...")
