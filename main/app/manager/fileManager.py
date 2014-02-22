import unicodedata
import threading
import tempfile
import os

from main.app.util import base
from main import settings


class FileManager(object):
    tempDir = os.path.join(settings.DEFAULT_VIDEOS_DIR, settings.VIDEOS_DIR_TEMP_NAME)

    class sincronize(object):
        """ sicroniza a escrita com a leitura de dados e alteração externas no arquivo """
        _lock = threading.RLock()

        def __init__(self, func):
            self.fun = func

        def __get__(self, inst, cls):
            def wrapper(*args, **kwargs):
                with self._lock:
                    return self.fun(inst, *args, **kwargs)

            return wrapper

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

        try:
            filename = unicodedata.normalize("NFKD", filename)
        except:
            filename = unicodedata.normalize("NFKD", filename)

        filename = filename.encode("ASCII", "ignore")
        filename = "%s.%s" % (filename, self.params["fileext"])

        return os.path.join(self.params["filepath"], filename)

    @sincronize
    def recover(self, badfile=False):
        """ recupera um arquivo temporário, salvando-o de forma definitiva """
        # pega o tamanho atual do arquivo, movendo o ponteiro para o final dele.
        self.file.seek(0, 2)
        filesize = self.file.tell()
        # retorna para o começo do arquivo de onde começará a leitura.
        self.file.seek(0)
        # local para o novo arquivo.
        filepath = self.getFilePath()

        class Copy(object):
            """ converte um arquivo temporário em um definitivo em disco """
            warning = _("O arquivo já existe!")

            class Sucess(object):
                info = _("O arquivo foi recuperado com sucesso!")

                def __init__(self):
                    self.sucess = False

                def getInfo(self):
                    return self.info

            class Error(object):
                bFileInfo = "".join([
                    _("O arquivo de vídeo está corrompido!"),
                    _("\nIsso por causa da \"seekbar\".")
                ])

                def __init__(self):
                    self.info = _("Erro tentando recuperar arquivo.\nCausa: %s")
                    self.error = False

                def getInfo(self): return self.info

                def setFormatInfo(self, info): self.info %= info

                def setInfo(self, info): self.info = info

            def __init__(self):
                self.progress = 0.0
                self.inProgress = self.cancel = False
                self.scs = self.Sucess()
                self.err = self.Error()

            @property
            def sucess(self):
                return self.scs.sucess

            @property
            def error(self):
                return self.err.error

            @sucess.setter
            def sucess(self, b):
                self.scs.sucess = b

            @error.setter
            def error(self, b):
                self.err.error = b

            def getInfo(self):
                if self.error:
                    info = self.err.getInfo()
                elif self.sucess:
                    info = self.scs.getInfo()
                return info

        # representa o progresso da cópia
        copy = Copy()

        if os.path.exists(filepath) or badfile:
            if not badfile:
                copy.err.setFormatInfo(copy.warning)
            else:
                copy.err.setInfo(copy.err.bFileInfo)
            copy.error = True
        else:
            try:
                block_size = (1024 ** 2) * 4  # 4M
                bytes_count = 0

                with open(filepath, "w+b") as new_file:
                    copy.inProgress = True

                    while not copy.cancel:
                        if filesize == 0: break  # zerodivision erro!
                        copy.progress = ((float(bytes_count) / filesize) * 100.0)

                        stream = self.file.read(block_size)
                        bytes_len = len(stream)

                        if bytes_len == 0: break

                        new_file.write(stream)
                        bytes_count += bytes_len

                        yield copy  # update progress
                    copy.sucess = not copy.cancel
                    yield copy  # after break
            except Exception as err:
                copy.err.setFormatInfo(str(err))
                copy.error = True
        if copy.cancel:  # cancel copy
            try:
                os.remove(filepath)
            except:
                pass
        yield copy

    def fileGetOrCreate(self):
        """ cria o arquivo """
        if self.params["tempfile"]:
            obj = tempfile.TemporaryFile(dir=self.tempDir)
        else:
            filepath = self.getFilePath()
            obj = open(filepath, ("w+b" if not os.path.exists(filepath) else "r+b"))
        return obj

    @sincronize
    def write(self, pos, data):
        """ Escreve os dados na posição dada """
        self.file.seek(pos)
        self.file.write(data)

    @sincronize
    def read(self, pos, data):
        """ Lê o numero de bytes, apartir da posição dada """
        self.file.seek(pos)
        stream = self.file.read(data)
        npos = self.file.tell()
        return (stream, npos)