# coding: utf-8
from main.app.util import base
import urllib.parse
import re

class UrlBase(object):
    sep   = "::::::"
    short = "%s[%s]"
    
    @classmethod
    def Universal(cls):
        from main.app.generators import Universal
        return Universal
    
    @classmethod
    def joinUrlDesc(cls, url, desc):
        """ junta a url com sua decrição(título), usando o separador padrão """
        return "%s %s %s"%(url, cls.sep, desc)
    
    @classmethod
    def splitUrlDesc(cls, string):
        """ separa a url de sua decrição(título), usando o separador padrão """
        str_split = string.rsplit(cls.sep, 1)
        if len(str_split) == 2:
            url, title = str_split[0].strip(), str_split[1].strip()
        else:
            url, title = str_split[0], ""
        return url, title
    
    @staticmethod
    def splitBaseId(string):
        """ value: megavideo[t53vqf0l] -> (megavideo, t53vqf0l) """
        matchobj = re.search("(?P<base>.+?)\[(?P<id>.+)\]", string, re.S|re.U)
        return (matchobj.group("base"), matchobj.group("id"))
    
    @classmethod
    def formatUrl(cls, string):
        """ megavideo[t53vqf0l] -> http://www.megavideo.com/v=t53vqf0l """
        base, strID = cls.splitBaseId(string)
        return cls.Universal().get_url( base ) % strID
    
    @classmethod
    def shortUrl(cls, url):
        return cls.short %cls.analizeUrl( url )
        
    @staticmethod
    def getBaseName(url):
        """ http://www.megavideo.com/v=t53vqf0l -> megavideo.com """
        parse = urllib.parse.urlparse( url )
        netloc_split = parse.netloc.split(".")
        if parse.netloc.startswith("www"):
            basename = "%s.%s"%tuple(netloc_split[1:3])
        else:# para url sem www inicial
            basename = "%s.%s"%tuple(netloc_split[0:2])
        return basename
    
    @classmethod
    def analizeUrl(cls, url):
        """ http://www.megavideo.com/v=t53vqf0l -> (megavideo.com, t53vqf0l) """
        basename = cls.getBaseName( url )
        urlid = cls.Universal().get_video_id(basename, url)
        return (basename, urlid)
    
    def getUrlId(self, title):
        """ retorna o id da url, com base no título(desc) """
        query = self.objects.get(title = title)
        basename = self.getBaseName(query.url)
        return self.Universal().get_video_id(basename, query.url)
    
########################################################################
class UrlManager( UrlBase ):
    def __init__(self):
        super(UrlManager, self).__init__()
        # acesso a queryset
        self.objects = self.models.Url.objects
        
    @property
    def models(self):
        """ tentativa de escapar do import recursivo """
        from main.app import models
        return models
    
    def setTitleIndex(self, title):
        """ adiciona um índice ao título se ele já existir """
        pattern = title + "(?:###\d+)?"
        query = self.objects.filter(title__regex = pattern)
        query = query.order_by("title")
        count = query.count()
        if count > 0:
            db_title = query[count-1].title # last title
            matchobj = re.search("(?:###(?P<index>\d+))?$", db_title)
            try: index = int(matchobj.group("index"))
            except: index = 0
            title = title + ("###%d"%(index+1))
        return title
    
    @base.LogOnError
    def remove(self, title):
        """ remove todas as referêcias do banco de dados, com base no título """
        self.objects.get(title=title).delete()

    def add(self, url, title):
        """ Adiciona o título e a url a base de dados """
        if self.objects.filter(title = title).count() > 0:
            title = self.setTitleIndex(title)
        
        self.models.Url(_url = self.shortUrl(url), title=title).save()
        
    def saveLast(self, url, title):
        try: lasturl = self.models.LastUrl.objects.latest("url")
        except: lasturl = self.models.LastUrl()
        
        lasturl.title = title
        lasturl.url = url
        lasturl.save()
        
    def getTitleList(self):
        return [query.title for query in self.objects.all().order_by("title")]

    def getUrlTitle(self, url):
        try: query = self.objects.get(_url = self.shortUrl(url))
        except: query = self.models.Url(title = "")
        return query.title
        
    def getUrlTitleList(self):
        """ retorna todas as urls e titulos adicionados na forma [(k,v),] """
        return [(query.url, query.title) for query in self.objects.all()]
        
    def getLastUrl(self):
        """ retorna a url do último video baixado """
        try: query = self.models.LastUrl.objects.latest("url")
        except: query = self.models.LastUrl(url="http://", title="...")
        return (query.url, query.title)
        
    def exist(self, url):
        """ avalia se a url já existe na base de dados """
        query = self.objects.filter(_url = self.shortUrl(url))
        return (query.count() > 0) # se maior então existe
    
