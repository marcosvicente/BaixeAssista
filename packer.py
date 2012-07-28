import os
import re
import compileall
import zipfile
import datetime

EXTS_PATTERN = [".+pyc$", ".+pyo$"] # ext final
TARGET_DIR = os.path.join(os.getcwd(), "main")
# ---------------------------------------------------------------

logname = "packer.log"
if os.path.getsize(logname) > 1024**2: #1M
	try: os.remove(logname)
	except: pass
	
if not os.path.exists(logname):
	log = open(logname, "w")
else:
	log = open(logname, "a")
log.write("START: %s\n"%datetime.datetime.now())
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
	try:
		path = os.path.join(os.getcwd(), "packet_beta.zip")
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
