# coding: utf-8
from django.conf import settings
import configobj
import logging
import os

logger = logging.getLogger("main.app.manager")

# INTERNACIONALIZATION
def trans_install(configs = None):
    """ instala as traduções apartir do arquivo de configurações. """
    if not isinstance(configs, configobj.ConfigObj):
        try:
            path = os.path.join(settings.CONFIGS_DIR, "configs.cfg")
            configs = configobj.ConfigObj( path )
        except:
            configs = {}
    try: import gettext
    except ImportError as err:
        logger.critical("import gettext: %s"%err)
        raise err
    
    menus = configs.get("Menus", {})
    lang = menus.get("language", "en")
    
    localepath = os.path.join(settings.APPDIR, "locale")
    language = gettext.translation("ba_trans", localepath, languages=[lang])

    # instala no espaço de nomes embutidos
    language.install(unicode=True)
    
#################################### JUST_TRY ##################################
class just_try(object):
    """ executa o méthodo dentro de um try:except """
    def __call__(self, method):
        def wrap(*args, **kwargs): # magic!
            try: method(*args, **kwargs)
            except Exception as err:
                logger.error("%s: %s"%(self.__class__.__name__, err))
        return wrap
        
def get_filename(filepath, fullname=True):
    """
    fullname: True  -> C:\\filedir\\file.txt -> file.txt
    fullname: False -> C:\\filedir\\file.txt -> file
    """
    filename = os.path.split( filepath )[-1]
    if not fullname: filename = os.path.splitext( filename )[0]
    return filename

def security_save(filepath, _configobj=None, _list=None, newline="\n"):
    """ salva as configurações da forma mais segura possível. 
    filepath - local para salvar o arquivo
    _configobj - dicionário de configurações
    _list - salva a lista, aplicando ou não a newline.
    newline='' - caso não haja interesse na adição de uma nova linha.
    """
    try: # criando o caminho para o arquivo de backup
        filename = get_filename( filepath ) # nome do arquivo no path.
        bkfilepath = filepath.replace(filename,("bk_"+filename))
    except Exception as err:
        logger.error(u"Path to backup file: %s"%err)
        return False
    
    # guarda o arquivo antigo temporariamente
    if os.path.exists( filepath ):
        try: os.rename(filepath, bkfilepath)
        except Exception as err:
            logger.error(u"Rename config to backup: %s"%err)
            return False
            
    try: # começa a criação do novo arquivo de configuração
        with open(filepath, "w") as configsfile:
            if type(_list) is list:
                for data in _list:
                    configsfile.write("%s%s"%(data, newline))
            elif isinstance(_configobj, configobj.ConfigObj):
                _configobj.write( configsfile )
            # levanta a exeção com o objetivo de recuperar o arquivo original
            else:
                raise AttributeError, "invalid config data"
        if os.path.exists(filepath):
            try: os.remove(bkfilepath)
            except: pass
    except Exception as err:
        logger.critical(u"Saving config file: %s"%err)
        # remove o arquivo atual do erro.
        if os.path.exists( filepath ):
            try: os.remove(filepath)
            except: pass
        # restaura o arquivo original
        if not os.path.exists( filepath ):
            try: os.rename(bkfilepath, filepath)
            except: pass
        return False
    return True