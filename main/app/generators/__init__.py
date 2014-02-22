# coding: utf-8
import importlib
import os
import glob
import collections

from django.conf import settings

from main.app.manager.streamManager import StreamManager
from main.app.manager.streamManager import StreamManager_
from main.app.manager.urls import UrlManager, UrlBase
from main.app.util import base


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
        return list(cls.sites.keys())

    @classmethod
    def add_site(cls, basename="", args=None, **kwargs):
        """ adiciona as referências para um novo site """
        if args:
            url, patterns, control, video_control = args

            cls.sites[basename] = {
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
    def get_video_id(cls, site_name, url):
        """ retorna o id da url """
        matchobj = cls.patternMatch(site_name, url)
        return matchobj.group("id")

    @classmethod
    def getStreamManager(cls, url):
        """ Procura pelo controlador de tranferênicia de arquivo de video"""
        stream_manager = None
        try:
            for site_name in cls.get_sites():
                matchobj = cls.patternMatch(site_name, url)
                if matchobj:
                    stream_manager = cls.get_control(site_name)
                    break
        except AssertionError as e:
            raise AttributeError(_("Sem suporte para a url fornecida."))
        assert stream_manager, _("url desconhecida!")
        return stream_manager

    @classmethod
    def getVideoManager(cls, url):
        """ Procura pelo controlador de video baseado na url dada """
        video_manager = None
        try:
            for site_name in cls.get_sites():
                matchobj = cls.patternMatch(site_name, url)
                if matchobj:
                    video_manager = cls.get_video_control(site_name)
                    break
        except AssertionError as e:
            raise AttributeError(_("Sem suporte para a url fornecida."))
        assert video_manager, _("url desconhecida!")
        return video_manager

    @classmethod
    def get_patterns(cls, sitename, validar=True):
        if validar: cls.valide(sitename, "patterns")
        return cls.sites[sitename]["patterns"]

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
                        match_obj = patter.match(url)
                        if match_obj: break
                else:
                    match_obj = pattern.match(url)
                if match_obj:
                    break
        elif type(patterns) is list:
            for pattern in patterns:
                match_obj = pattern.match(url)
                if match_obj:
                    break
        else:
            match_obj = patterns.match(url)
        return match_obj

    @classmethod
    def isEmbed(cls, url):
        """ analiza se a url é de um player embutido """
        site_name = UrlManager.getBaseName(url)
        patterns = cls.get_patterns(site_name)
        site_attrs = cls.sites[site_name]
        if type(patterns) is tuple:
            for pattern in patterns:
                if type(pattern) is list:
                    for patter in pattern:
                        matchobj = patter.match(url)
                        if matchobj: return True
        elif type(patterns) is list:
            for pattern in patterns:
                matchobj = pattern.match(url)
                if matchobj: return True
        else:
            return site_attrs.get("embed", False)

    @classmethod
    def get_url(cls, site_name, validar=True):
        if validar: cls.valide(site_name, "url")
        return cls.sites[site_name]["url"]

    @classmethod
    def get_control(cls, site_name, validar=True):
        if validar: cls.valide(site_name, "control")
        return cls.sites[site_name]["control"]

    @classmethod
    def get_video_control(cls, site_name, validar=True):
        if validar: cls.valide(site_name, "video_control")
        return cls.sites[site_name]["video_control"]

    @classmethod
    def valide(cls, site_name, obj):
        assert bool(cls.sites.get(site_name, None)), "Site %s não encontrado" % site_name
        if obj == "patterns":
            assert bool(cls.sites[site_name].get("patterns", None)), "Padrão não definido para %s" % site_name
        elif obj == "url":
            assert bool(cls.sites[site_name].get("url", None)), "Url não definida para %s" % site_name
        elif obj == "control":
            assert bool(cls.sites[site_name].get("control", None)), "Controlador não definido para %s" % site_name
        elif obj == "video_control":
            assert bool(
                cls.sites[site_name].get("video_control",
                                         None)), "Controlador de video não definido para %s" % site_name

    @classmethod
    def has_site(cls, url):
        """ avalia se a url é de um site registrado """
        try:
            base_name = UrlManager.getBaseName(url)
            matchobj = cls.patternMatch(base_name, url)
            has = matchobj and (base_name in cls.get_sites())
        except:
            has = False
        return has

    @classmethod
    def get_inner_url(cls, url):
        matchobj = cls.patternMatch(UrlManager.getBaseName(url), url)
        if matchobj: url = matchobj.group("inner_url")
        return url


def get_class_ref(mod_file):
    """ retorna apenas, sites com a variável de controle(controller) """
    for class_ref in list(vars(mod_file).values()):
        if isinstance(class_ref, collections.Callable) and hasattr(class_ref, "controller"):
            return class_ref


def find_all_sites():
    """ retorna toda a lista de scripts(já importada) das definições dos sites suportados. """
    mod_all = []
    mods_py = glob.glob(os.path.join(settings.APPDIR, "generators", "*.py"))
    mods_pyc = glob.glob(os.path.join(settings.APPDIR, "generators", "*.pyc"))

    for filepath in (mods_py if bool(len(mods_py)) else mods_pyc):
        filename = base.get_filename(filepath, False)

        if not filename.startswith("_"):
            mod_name = "{!s}.{!s}".format(Universal.__module__, filename)
            module = importlib.import_module(mod_name, Universal.__module__)
            mod_all.append(module)

    return list(map(get_class_ref, mod_all))


def register_site(base_name, site_obj):
    if site_obj.controller["video_control"] is None:
        site_obj.controller["video_control"] = site_obj

    if isinstance(site_obj.controller["control"], str):
        control = getattr(Universal, site_obj.controller["control"])
        site_obj.controller["control"] = control

    Universal.add_site(base_name, **site_obj.controller)


for site in find_all_sites():
    default = UrlBase.getBaseName(site.controller["url"])
    basename = site.controller.get("basenames", default)

    if type(basename) is list:
        for name in basename:
            register_site(name, site)
    else:
        register_site(basename, site)