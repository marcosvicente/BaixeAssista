# coding: utf-8
import os, sys
from main.app.manager.streamManager import StreamManager
from main.app.manager.streamManager import StreamManager_
from main.app.manager.urls import UrlManager, UrlBase
from django.conf import settings
from main.app import util
import glob
import imp

class Universal(object):
    """ A classe Universal, quarda varias informações e dados usados em toda a extensão do programa. 
     Ela é usada para diminuir o número de modificações necessárias, quando adicionando suporte a um novo site de vídeo.
    """
    sites = {}
    
    @staticmethod
    def SM_SEEK(*args, **kwargs):
        return StreamManager(*args, **kwargs)
    
    @staticmethod
    def SM_RANGE(*args, **kwargs):
        return StreamManager_(*args, **kwargs)
        
    @classmethod
    def get_sites(cls):
        return cls.sites.keys()
    
    @classmethod
    def add_site(cls, basename="", args=None, **kwargs):
        """ adiciona as referências para um novo site """
        if args:
            url, patterns, control, video_control = args
            
            cls.sites[ basename ] = {
                "video_control": video_control,
                "control": control,
                "patterns": patterns,
                "url": url,
            }
        elif kwargs:
            cls.sites.update({ 
                basename: kwargs 
            })

    @classmethod
    def get_video_id(cls, sitename, url):
        """ retorna o id da url """
        matchobj = cls.patternMatch(sitename, url)
        return matchobj.group("id")
    
    @classmethod
    def getStreamManager(cls, url):
        """ Procura pelo controlador de tranferênicia de arquivo de video"""
        smanager = None
        try:
            for sitename in cls.get_sites():
                matchobj = cls.patternMatch(sitename, url)
                if matchobj:
                    smanager = cls.get_control( sitename)
                    break
        except AssertionError as err:
            raise AttributeError, _("Sem suporte para a url fornecida.")
        assert smanager, _("url desconhecida!")
        return smanager

    @classmethod
    def getVideoManager(cls, url):
        """ Procura pelo controlador de video baseado na url dada """
        vmanager = None
        try:
            for sitename in cls.get_sites():
                matchobj = cls.patternMatch(sitename, url)
                if matchobj:
                    vmanager = cls.get_video_control( sitename )
                    break
        except AssertionError as err:
            raise AttributeError, _("Sem suporte para a url fornecida.")
        assert vmanager, _("url desconhecida!")
        return vmanager
    
    @classmethod
    def get_patterns(cls, sitename, validar=True):
        if validar: cls.valide(sitename, "patterns")
        return cls.sites[ sitename ]["patterns"]

    @classmethod
    def patternMatch(cls, sitename, url):
        """ analiza se a url casa o padrão de urls.
        Duas situações são possiveis:
            A url é única; A url está dentro de outra url.
        """
        patterns = cls.get_patterns(sitename)
        if type(patterns) is tuple:
            for pattern in patterns:
                if type(pattern) is list:
                    for patter in pattern:
                        matchobj = patter.match( url )
                        if matchobj: break
                else:
                    matchobj = pattern.match( url )
                if matchobj: break
        elif type(patterns) is list:
            for pattern in patterns:
                matchobj = pattern.match( url )
                if matchobj: break
        else:
            matchobj = patterns.match( url )
        return matchobj

    @classmethod
    def isEmbed(cls, url):
        """ analiza se a url é de um player embutido """
        sitename = UrlManager.getBaseName(url)
        patterns = cls.get_patterns(sitename)
        siteAttrs = cls.sites[sitename]
        if type(patterns) is tuple:
            for pattern in patterns:
                if type(pattern) is list:
                    for patter in pattern:
                        matchobj = patter.match( url )
                        if matchobj: return True
        elif type(patterns) is list:
            for pattern in patterns:
                matchobj = pattern.match( url )
                if matchobj: return True
        else:
            return siteAttrs.get("embed", False)

    @classmethod
    def get_url(cls, sitename, validar=True):
        if validar: cls.valide(sitename, "url")
        return cls.sites[ sitename ]["url"]

    @classmethod
    def get_control(cls, sitename, validar=True):
        if validar: cls.valide(sitename, "control")
        return cls.sites[ sitename ]["control"]

    @classmethod
    def get_video_control(cls, sitename, validar=True):
        if validar: cls.valide(sitename, "video_control")
        return cls.sites[ sitename ]["video_control"]

    @classmethod
    def valide(cls, sitename, obj):
        assert bool(cls.sites.get(sitename, None)), u"Site %s não encontrado"%sitename
        if obj == "patterns":
            assert bool(cls.sites[sitename].get("patterns", None)), u"Padrão não definido para %s"%sitename
        elif obj == "url":
            assert bool(cls.sites[sitename].get("url", None)), u"Url não definida para %s"%sitename
        elif obj == "control":
            assert bool(cls.sites[sitename].get("control", None)), u"Controlador não definido para %s"%sitename
        elif obj == "video_control":
            assert bool(cls.sites[sitename].get("video_control", None)), u"Controlador de video não definido para %s"%sitename
    
    @classmethod
    def has_site(cls, url):
        """ avalia se a url é de um site registrado """
        try:
            basename = UrlManager.getBaseName(url)
            matchobj = cls.patternMatch(basename, url)
            has = matchobj and (basename in cls.get_sites())
        except: has = False
        return has
        
    @classmethod
    def get_inner_url(cls, url):
        matchobj = cls.patternMatch(UrlManager.getBaseName(url), url)
        if matchobj: url = matchobj.group("inner_url")
        return url
        
# -----------------------------------------------------------------------------
def get_classref(filemod):
    """ retorna apenas, sites com a variável de controle(controller) """
    for classref in filemod.__dict__.values():
        if callable(classref) and hasattr(classref,"controller"):
            return classref
           
def find_all_sites():
    """ retorna toda a lista de scripts(já importada) das definições dos sites suportados. """
    modulelist = []
    pylist = glob.glob(os.path.join(settings.APPDIR, "generators", "*.py"))
    pyclist = glob.glob(os.path.join(settings.APPDIR, "generators", "*.pyc"))
    
    for filepath in (pylist if bool(len(pylist)) else pyclist):
        name = util.base.get_filename(filepath, False)
        
        if not name.startswith("_"):
            modname = "%s.%s"%(Universal.__module__, name)
            
            try: module = imp.load_compiled(modname, filepath)
            except: module = imp.load_source(modname, filepath)
            
            modulelist.append( module )
    return map(get_classref, modulelist)
    
def register_site(basename, site):
    if site.controller["video_control"] is None:
        site.controller["video_control"] = site
        
    if isinstance(site.controller["control"], (str, unicode)):
        control = getattr(Universal, site.controller["control"])
        site.controller["control"] = control
        
    Universal.add_site(basename, **site.controller)

for site in find_all_sites():
    ## print "Site: %s"%site
    default = UrlBase.getBaseName(site.controller["url"])
    basename = site.controller.get("basenames", default)    
    
    if type(basename) is list:
        for name in basename:
            register_site(name, site)
    else:
        register_site(basename, site)