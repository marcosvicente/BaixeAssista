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
    def __init__(self, **params):
        """ params:{}
        - filename: nome do arquivo da tabela mtime.
        - excludes: padrões de extensões a serem ignorados da tabela mtime. ex(".+pyc$")
        - path: caminho base, para o qual, a tabela mtime está sendo gerada.
        """
        self.path = params.get("path", TARGET_DIR)
        filename = params.get("filename", "t_file.txt")
        self.t_conf_path = os.path.join(PACKER_DIR, filename)
        self.t_conf = configobj.ConfigObj(self.t_conf_path)
        
        self.excludes = self.p_compile(*(".+pyc$", ".+pyo$", ".+po$"))
        excludes = params.get("excludes", tuple())
        self.excludes += self.p_compile(*excludes)
    
    def p_compile(self, *args):
        return tuple([re.compile(p) for p in args])
        
    def get_base_name(self, path):
        """ C:\somedir\somefile.txt -> (somedir, somefile.txt)"""
        parts = os.path.dirname( path ).split( os.sep )
        if len(parts) >= 3: base = "_".join(parts[-2:])
        else: base = os.path.basename(os.path.dirname(path))
        name = os.path.basename( path )
        return (base, name)
    
    def get_relative_name(self, path):
        """ C:\somedir\somefile.txt -> somedir.somefile.txt"""
        base, name = self.get_base_name(path)
        return base+"."+name

    def f_mtime(self, mtime):
        return "%.4f"%mtime

    def exclude(self, name="", path=""):
        """ avalia se o arquivo, pela sua extensão, deve ser excluido da tabela mtime """
        if path: rname = self.get_relative_name(path)
        else: rname = name
        for pattern in self.excludes:
            if pattern.match( rname ):
                return True
        return False

    def set_mtime(self, path):
        rname = self.get_relative_name(path)
        mtime = os.path.getmtime(path)
        self.t_conf[rname] = self.f_mtime( mtime )

    def modified(self, path):
        """ avalia se o arquivo no 'path' sofreu alguma modificação """
        rname   = self.get_relative_name(path)
        b_mtime = self.t_conf[rname]
        a_mtime = os.path.getmtime( path )
        a_mtime = self.f_mtime( a_mtime )
        return a_mtime > b_mtime

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
            exit(1)

def create_mtime_table(path, update=False):
    timer = Timer(path = path)
    for root, dirs, files in os.walk(path):
        # diretório contendo o arquivo '__ignore__' não é consirado válido.
        if "__ignore__" in files: continue
        for filename in files:
            if timer.exclude(name=filename): continue
            abspath = os.path.join(root, filename)
            if not update and timer.has_mtime(abspath): continue
            timer.set_mtime(abspath)
    timer.save()
    return timer
# ---------------------------------------------------------------
########################################################################
class Packer(object):
    """ adiciona todos os arquivos modificados ao pacote de atualização """
    #----------------------------------------------------------------------
    def __init__(self, **params):
        """params: {}
        - timer: objeto monitorador das modificação no diretório em questão
        - filename: nome do pacote gerado na saída
        - path: caminho alvo
        - pycompile: booleano indicando se arquivos .py devem ser compilados para .pyc
        """
        self.timer = params.get("timer", Timer(path=TARGET_DIR))
        self.path = params.get("path", self.timer.path)
        self.pycompile = params.get("pycompile",True)
        filename = params.get("filename", "packet_test.zip")
        self.f_path = os.path.join(PACKER_DIR, filename)
        self.p_file = self.get_packet()
        
    def get_packet(self):
        try: p_file = zipfile.ZipFile(self.f_path, "w")
        except Exception, err:
            msg = "ZIP Err[Packer.get_packet_file]: %s"%err
            log.write(msg+"\n")
            print msg; exit(1)
        return p_file
    
    def add_file(self, path):
        if self.timer.has_mtime(path) and self.timer.modified(path):
            if self.pycompile and re.match(path, ".+py$"):
                compileall.compile_file(path, force=True)
                path = path.replace(".py", ".pyc")
            relpath = path.split(os.getcwd()+os.sep)[-1]
            self.p_file.write(path, relpath)
            
    def save(self):
        for root, dirs, files in os.walk(self.path):
            if "__ignore__" in files: continue
            for filename in files:
                path = os.path.join(root, filename)
                self.add_file( path )
                
    def close(self ):
        self.p_file.close()
        
#----------------------------------------------------------------------
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

#----------------------------------------------------------------------
if __name__ == "__main__":
    # cria tabela mtime para os arquivos que ainda não existirem.
    timer = create_mtime_table(TARGET_DIR)
    packer = Packer(timer = timer)
    packer.save()
    packer.close()
    # atualiza a tabela para os arquivos já trabalhados.
    create_mtime_table(TARGET_DIR, update=True)
    print "Finish!"