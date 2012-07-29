# -*- coding: UTF-8 -*-
import os
import re
import compileall
import zipfile
import datetime
import configobj

EXTS_PATTERN = [".+pyc$", ".+pyo$"] # ext final
TARGET_DIR = os.path.join(os.getcwd(), "main")
PACKER_DIR = os.path.join(os.getcwd(), "packer_files")
LOG_PATH = os.path.join(PACKER_DIR, "packer.log")
# ---------------------------------------------------------------

if not os.path.exists( PACKER_DIR ):
	os.mkdir( PACKER_DIR )

if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 1024**2: #1M
	try: os.remove( LOG_PATH )
	except: pass

if not os.path.exists(LOG_PATH):
	log = open(LOG_PATH, "w")
else:
	log = open(LOG_PATH, "a")
log.write("START SECTION: %s\n"%datetime.datetime.now())
# ---------------------------------------------------------------

class Timer(object):
	def __init__(self):
		self.t_conf_path = os.path.join(PACKER_DIR,"t_file.txt")
		self.t_conf = configobj.ConfigObj(self.t_conf_path)
		self.excludes = (".+pyc$", ".+pyo$", ".+po$")
		
	def get_base_name(self, path):
		base = os.path.basename(os.path.dirname(path))
		name = os.path.basename( path )
		return (base, name)
	
	def get_relative_name(self, path):
		base, name = self.get_base_name(path)
		return base+"."+name
	
	def f_mtime(self, mtime):
		return "%.4f"%mtime
	
	def exclude(self, name="", path=""):
		""" avalia se o arquivo, pela sua extensão, deve ser excluido da tabela mtime """
		if path: rname = self.get_relative_name(path)
		else: rname = name
		for pattern in self.excludes:
			if re.match(pattern, rname):
				return True
		return False
		
	def set_mtime(self, path):
		rname = self.get_relative_name(path)
		mtime = os.path.getmtime(path)
		self.t_conf[rname] = self.f_mtime( mtime )
		
	def was_changed(self, path):
		rname = self.get_relative_name(path)
		before_mtime = self.t_conf[ rname ].as_float()
		after_mtime = os.path.getmtime(path)
		after_mtime = self.f_mtime( after_mtime )
		return after_mtime > before_mtime
	
	def has_mtime(self, path):
		rname = self.get_relative_name(path)
		return bool(self.t_conf.get(rname, None))
	
	def add_time(self, name, value):
		self.t_conf[ name ] = value
		
	def get_time(self, name):
		return self.t_conf[ name ]
	
	def __getitem__(self, name):
		return self.t_conf[ name ]
	
	def save(self):
		try:
			with open(self.t_conf_path, "w") as t_file:
				self.t_conf.write( t_file )
		except Exception, err:
			msg = "Err[Timer.save] %s"%err
			log.write(msg+"\n")
			print msg
			
def create_mtime_table(path):
	timer = Timer()
	for root, dirs, files in os.walk(path):
		# diretório contendo o arquivo '__ignore__' não é consirado válido.
		if "__ignore__" in files: continue
		for filename in files:
			if timer.exclude(name=filename): continue
			abspath = os.path.join(root, filename)
			if timer.has_mtime(abspath): continue
			timer.set_mtime(abspath)
	timer.save()
# ---------------------------------------------------------------

def remove(filepath):
	""" removendo o arquivo compilado do disco """
	try:
		os.remove( filepath )
		log.write("Successfully removed: %s\n"%filepath)
	except Exception, err:
		log.write("Err[%s] %s\n"%(filepath, err))
		
def process_file(filedir, filename):
	for pattern in EXTS_PATTERN:
		if re.match(pattern, filename):
			remove( os.path.join(filedir, filename) )
	
def clean_all_nopy(rootpath):
	for root, dirs, files in os.walk( rootpath ):
		for filename in files:
			process_file(root, filename)

# ---------------------------------------------------------------
if __name__ == "__main__":
	create_mtime_table(TARGET_DIR)
	
	try:
		path = os.path.join(PACKER_DIR, "packet_beta.zip")
		PACKET_FILE = zipfile.PyZipFile(path, "w")
	except Exception, err:
		print "ZIP Err: %s"%err
		exit(1)	

	print "Starting..."
	try:
		clean_all_nopy(TARGET_DIR)
		PACKET_FILE.writepy( TARGET_DIR )
	finally:
		PACKET_FILE.close()
	print "Finish!"
