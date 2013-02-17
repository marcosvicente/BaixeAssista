# coding: utf-8
from main.app.util import base
from main import settings
import unicodedata
import threading
import tempfile
import os
    
class FileManager(object):
    tempFilePath = os.path.join(settings.DEFAULT_VIDEOS_DIR, settings.VIDEOS_DIR_TEMP_NAME)
    
    class sincronize(object):
        """ sicroniza a escrita com a leitura de dados e alteração externas no arquivo """
        _lock = threading.RLock()
        
        def __init__(self, func):
            self.fun = func
        def __get__(self, inst, cls):
            def wraper(*args, **kwargs):
                with self._lock:
                    return self.fun(inst, *args, **kwargs)
            return wraper
    
    def __init__(self, **params):
        """ params: {}
         ** filepath(default=DEFAULT_VIDEOS_DIR) -> local onde o arquivo de video será salvo.
         ** tempfile(default=False) -> indica o uso de um arquivo temporário para armazenamento.
         ** fileext(default=flv) -> extensão do arquivo sendo processando.
        """
        self.params = params
        params.setdefault("filepath", settings.DEFAULT_VIDEOS_DIR)
        params.setdefault("fileext", "flv")
        params.setdefault("filename", "")
        params.setdefault("tempfile", False)
        
        if not os.path.exists(params["filepath"]):
            params["filepath"] = settings.DEFAULT_VIDEOS_DIR
        
    def __del__(self):
        self.close()
        del self.params
        
    def __setitem__(self, key, value):
        self.params["key"] = value
    
    def __getitem__(self, key):
        return self.params[key]
    
    @base.protected()
    def close(self):
        self.file.close()
    
    def open(self):
        self.file = self.fileGetOrCreate()
    
    @base.LogOnError
    def remove(self):
        os.remove(self.getFilePath())
        
    def getFilePath(self):
        """ retorna o caminho completo para o local do arquivo """
        filename = self.params["filename"]
        
        try: filename = unicodedata.normalize("NFKD", unicode(filename,"UTF-8"))
        except: filename = unicodedata.normalize("NFKD", filename)
        
        filename = filename.encode("ASCII", "ignore")
        filename = "%s.%s"%(filename, self.params["fileext"])
        
        return os.path.join(self.params["filepath"], filename)
        
    @sincronize
    def recover(self, badfile=False):
        """ recupera um arquivo temporário, salvando-o de forma definitiva """
        # pega o tamanho atual do arquivo, movendo o ponteiro para o final dele.
        self.file.seek(0,2); filesize = self.file.tell()
        # retorna para o começo do arquivo de onde começará a leitura.
        self.file.seek(0)
        # local para o novo arquivo.
        filepath = self.getFilePath()
        
        class sucess(object):
            def __init__(self):
                self.msg = _(u"O arquivo foi recuperado com sucesso!")
                self.sucess = False
            def get_msg(self): return self.msg
            
        class error(object):
            bad_file_msg = u"".join([
                _(u"O arquivo de vídeo está corrompido!"), 
                _(u"\nIsso por causa da \"seekbar\".")
            ])
            def __init__(self):
                self.msg = _(u"Erro tentando recuperar arquivo.\nCausa: %s")
                self.error = False
            def get_msg(self): return self.msg
            def set_f_msg(self, msg): self.msg %= msg
            def set_msg(self, msg): self.msg = msg
            
        class copy(object):
            warning = _(u"O arquivo já existe!")
            
            def __init__(self):
                self.progress = 0.0
                self.inProgress = self.cancel = False
                self.err, self.scs = error(), sucess()
                
            def _set_sucess(self, b): self.scs.sucess = b
            def _get_sucess(self): return self.scs.sucess
            sucess = property(fget=_get_sucess, fset=_set_sucess)
            
            def _set_error(self, b): self.err.error = b
            def _get_error(self): return self.err.error
            error = property(fget=_get_error, fset=_set_error)
            
            def get_msg(self):
                if self.error: return self.err.get_msg()
                if self.sucess: return self.scs.get_msg()
                
        cp = copy() # representa o progresso da cópia
        
        if os.path.exists( filepath ) or badfile:
            if not badfile: cp.err.set_f_msg( cp.warning )
            else: cp.err.set_msg( cp.err.bad_file_msg )
            cp.error = True
        else:
            try:
                block_size = (1024**2) *4 # 4M
                bytes_count = 0
                
                with open(filepath, "w+b") as new_file:
                    cp.inProgress = True
                    
                    while not cp.cancel:
                        if filesize == 0: break # zerodivision erro!
                        cp.progress = ((float(bytes_count)/filesize)*100.0)
                        
                        stream = self.file.read( block_size )
                        bytes_len = len( stream )
                        
                        if bytes_len == 0: break
                        
                        new_file.write( stream )
                        bytes_count += bytes_len
                        
                        yield cp # update progress
                    cp.sucess = not cp.cancel
                    yield cp # after break
            except Exception as err:
                cp.err.set_f_msg( str(err) )
                cp.error = True
        if cp.cancel: # cancel copy
            try: os.remove( filepath )
            except: pass
        yield cp
        
    def fileGetOrCreate(self):
        """ cria o arquivo """
        if self.params["tempfile"]:
            obj = tempfile.TemporaryFile(dir=self.tempFilePath)
        else:
            filepath = self.getFilePath()
            obj = open(filepath, ("w+b" if not os.path.exists(filepath) else "r+b"))
        return obj
        
    @sincronize
    def write(self, pos, data):
        """ Escreve os dados na posição dada """
        self.file.seek( pos )
        self.file.write( data )

    @sincronize
    def read(self, pos, data):
        """ Lê o numero de bytes, apartir da posição dada """
        self.file.seek( pos )
        stream = self.file.read( data )
        npos = self.file.tell()
        return (stream, npos)
    