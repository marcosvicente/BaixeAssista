# -*- coding: UTF-8 -*-
import os
import zipfile
import platform
import re
import time

import urllib.request, urllib.error, urllib.parse
from main import environ


environ.setup((__name__ == "__main__"))

from main.app.manager.streamManager import StreamManager
from django.conf import settings
from main.app.util import base


class Release(object):
    """ Busca por novas versões do programa """

    def __init__(self):
        """Constructor"""
        self.warning = _("Ainda não há uma nova versão disponível.")
        self.dl_url = "http://code.google.com/p/gerenciador-de-videos-online/downloads/list"
        self.dl_pattern = re.compile("<td class=\"vt\s*(?:id)?\s*col_\d+\".*?>(.*?)</td>", re.DOTALL)
        self.tag_pattern = re.compile("<a.*?>(.*?)</a>", re.DOTALL)

    def check(self, dl_opts):
        """ verifica se existe uma versão maior do que a versão atual """
        for filename, summary, uploaded, releasedata, size, downloadedcount in dl_opts:
            matchobj = re.search("BaixeAssista(?:_|\s+)?v(?P<version>.+?)(?:_exe)?\.(?:rar|zip|exe)", filename)

            try:
                version = matchobj.group("version")
            except:
                continue

            if version > settings.PROGRAM_VERSION:
                info = _("Versão atual do programa - BaixeAssista v%s\n\n") % settings.PROGRAM_VERSION
                info += _("Versão lançada: %s\n") % filename
                info += _("Descrição: %s\n") % summary
                info += _("Enviado: %s\n") % uploaded
                info += _("Lançado: %s\n") % releasedata
                info += _("Tamanho: %s\n") % size
                info += _("Baixado: %s vezes\n") % downloadedcount
                return (True, info)
        return (False, self.warning)

    def search(self):
        try:
            fd = urllib.request.urlopen(self.dl_url)
            webpage = fd.read()
            fd.close()

            groups = []
            for raw_tag in self.dl_pattern.findall(webpage):
                matchobj = self.tag_pattern.search(raw_tag)

                if matchobj:
                    tag = matchobj.group(1)
                else:
                    tag = ""

                tag = tag.replace(r"\n", "").strip()
                tag = tag.decode("utf-8", "ignore")
                groups.append(tag)

            return self.check([groups[i:i + 6] for i in range(0, len(groups), 6)])
        except:
            return (None, _("Houve um erro ao procura por uma nova versão."))


################################# UPDATER ##################################
class Updater(object):
    """ Procura por pacotes de atualização """
    #----------------------------------------------------------------------
    ## old: packet_v0.0.1_0.1.3.zip - new: packet_oswinv0.0.1_0.1.3.zip
    def __init__(self, **params):
        """ params: {}
        - packetVersion: versão atual do pacote de atualização.
        """
        self.packetVersion = params.get("packetVersion", None)
        assert self.packetVersion, "informe a versão do pacote atual!"

        self.sourcesLink = "https://dl.dropbox.com/u/67269258/BaixeAssistaUpdateSources"
        self.pl_pattern = re.compile("packet_(?:oswin|oslinux)?v.+?_.+?\.zip")
        self.pv_pattern = re.compile("packet_(?P<os>(?:oswin|oslinux)?)v(?P<pk>.+?)_(?P<pg>.+?)\.zip")

        self.newVersion = ""
        self.updateDir = os.path.join(settings.APPDIR, "update")
        self.packetsLinks = []
        self.packetsPaths = []
        self.packetFound = self.oldRelease = False

        self.updateSucess = (True, _("O programa foi atualizado com sucesso!"))
        self.sucessWarning = _("Um novo pacote de atualização está disponível: packet_v%s_%s.zip.")
        self.errorUpdateSearching = (None, _("Erro procurando por pacotes de atualização."))
        self.errorUpdating = (None, _("Erro aplicando a atualização. Tente novamente mais tarde."))
        self.warning = _("Versão antiga do programa detectada(atualize para a mais nova).")
        self.updatedWarning = (False, _("O programa já está atualizado."))

    def getNewVersion(self):
        return self.newVersion

    def getLastChanges(self, language="en"):
        """ retorna o texto informativo das últimas alterações do programa """
        changes = []
        for packetPath in self.packetsPaths:
            try:
                with zipfile.ZipFile(packetPath) as updateZip:
                    zipinfo = updateZip.getinfo("main/changes.txt")
                    rawText = updateZip.read(zipinfo)

                    pattern = "<{language}>(.*)</{language}>".format(language=language)
                    matchobj = re.search(pattern, rawText, re.DOTALL)

                    text = matchobj.group(1)
                    text = text.strip("\r\n ")

                    header = "%s:\n" % base.get_filename(packetPath, False)
                    changes.append(header + text)
            except:
                continue
        return changes

    def cleanUpdateDir(self):
        """ remove todos os arquivos da pasta de atualização """
        for name in os.listdir(self.updateDir):
            path = os.path.join(self.updateDir, name)
            try:
                os.remove(path)
            except Exception as e:
                print(("Err[clean: {!s}] {!s}".format(path, e)))

    def update(self):
        """ Com o pacote de atualizações já baixado, e pronto para ser lido, instala as atualizações """
        assert len(self.packetsPaths), "No packets!"
        pattern = re.compile("main/changes\.txt")
        for index, path in enumerate(self.packetsPaths):
            try:
                with zipfile.ZipFile(path) as updateZip:
                    assert not updateZip.testzip()
                    for zipinfo in updateZip.infolist():
                        if not pattern.match(zipinfo.filename):
                            updateZip.extract(zipinfo, os.getcwd())
                    # guarda a versão do último pacote atualizado
                    self.newVersion, programVersion = self.get_versions(base.get_filename(path))
            except:
                if index == 0:
                    return self.errorUpdating
                else:
                    # considera só o grupo atualizado com sucesso
                    self.packetsPaths = self.packetsPaths[:index]
                    break
        # informa: atualizado com sucesso
        return self.updateSucess

    def download(self):
        """ baixa o pacote de atualização """
        assert self.packetFound, "Packets not found!"
        for index, link in enumerate(self.packetsLinks):
            try:
                print(("Downloading: ", link))
                packetname = os.path.basename(link)
                fd = urllib.request.urlopen(link)

                if fd.code == 200:
                    block_size = 1024
                    packetpath = os.path.join(self.updateDir, packetname)

                    with open(packetpath, "wb") as updateFile:
                        while True:
                            before = time.time()
                            stream = fd.read(block_size)
                            after = time.time()

                            streamLen = len(stream)
                            if streamLen == 0: break

                            # ajusta a velocidade de download
                            block_size = StreamManager.best_block_size((after - before), streamLen)
                            updateFile.write(stream)

                        # guarda o caminho do pacote baixado com sucesso
                        self.packetsPaths.append(packetpath)

                    fd.close()
                # erro no primeiro pacote pára todo o processo de atulização
                elif index == 0:
                    return self.errorUpdating
                else:
                    break
            except:
                if index == 0: return self.errorUpdating
                break
        return True, _("Baixado com sucesso!")

    def get_versions(self, link):
        """ packet_0.1.5_0.1.3.zip -> (0.1.5, 0.1.3) """
        matchobj = self.pv_pattern.search(link)
        pk = pg = ""
        if matchobj:
            pk = matchobj.group("pk")
            pg = matchobj.group("pg")
        return (pk, pg)

    def get_system_name(self, link):
        matchobj = self.pv_pattern.search(link)
        if matchobj:
            os = matchobj.group("os")
        else:
            os = ""
        return os

    def packetFilter(self, links):
        """ remove as repetições das versões de pacotes e
        pacotes que não pertencem a versão atual """
        v_links = []

        for link in links:
            packet, program = self.get_versions(link)

            if program == settings.PROGRAM_VERSION:
                if packet > self.packetVersion and not link in v_links:
                    osystem = self.get_system_name(link)

                    if settings.PROGRAM_SYSTEM.get(platform.system(), "") == osystem:
                        v_links.append(link)

            elif program > settings.PROGRAM_VERSION:
                # caso a versão atual seja mais antiga, avisa o usuário para atualizar
                # isso ocorrerá caso não haja mais atualizações para a versão atual
                self.oldRelease = True
        # organiza do menor pacote para o maior
        v_links.sort()
        return v_links

    def isOldRelease(self):
        """ avalia se o programa é antigo, após não encontrar novas atualizações """
        return (self.oldRelease and not self.packetFound)

    def search(self):
        """ inicia a busca por novos pacotes de atualização """
        try:
            s = urllib.request.urlopen(self.sourcesLink)
            contenty = s.read()
            s.close()
            assert contenty
        except:
            return False

        links = contenty.split("\r\n")
        if not any(links): links = contenty.split("\n")

        # guarda o grupo de pacotes com versão maior que a atual
        self.packetsLinks = self.packetFilter(links)
        self.packetFound = bool(len(self.packetsLinks))
        return self.packetFound

########################### EXECUÇÃO APARTIR DO SCRIPT  ###########################
if __name__ == "__main__":
    base.trans_install()  # instala as traduções.

    r = Release()
    r.search()

    ps = Updater(packetVersion="1.6.2")
    success = ps.search()

    if success is True:
        print("New updates found")
        continue_ = eval(input("Proceed [yes or no] ?"))

        if continue_ == "yes":
            success, response = ps.download()
            print(response)

            if success is True:
                continue_ = eval(input("Aplicar a atualizacao[yes ou no] ?"))
                if continue_ == "yes":
                    success, response = ps.update()
                    print(response)

                    print(("Current Version: ", ps.getNewVersion()))

                    print(("*" * 25))
                    print(("\n\n".join(ps.getLastChanges())))

                    print("** clean all **")
                    ps.cleanUpdateDir()
                    print("Finish success!")
                else:
                    print("Canceled")
        else:
            print("Canceled")