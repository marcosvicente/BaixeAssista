# coding: utf-8
import logging
import gettext
import os

from django.conf import settings
import configobj


logger = logging.getLogger("main.app.manager")


def trans_install(configs=None):
    """ instala as traduções apartir do arquivo de configurações. """
    if not isinstance(configs, configobj.ConfigObj):
        try:
            path = os.path.join(settings.CONFIGS_DIR, "configs.cfg")
            configs = configobj.ConfigObj(path)
        except:
            configs = {}

    configs.setdefault("Lang", {})
    configs["Lang"].setdefault("code", "en_US")
    locale_path = os.path.join(settings.APPDIR, "locale")
    language_code = [configs["Lang"]["code"]]

    translator = gettext.translation("ba_trans", locale_path, languages=language_code)

    # instala no espaço de nomes embutidos
    translator.install()


class LogOnError(object):
    """ Tenta executar o método, caso algo dê errado guarda a 
        mensagem de erro no arquivo de log.
    """

    class wrap(object):
        """ excuta o método protegendo o escopo de excução """

        ferror = "[On {name}] [In Method: {method}] [Error: {error}]"

        def __init__(self, inst, method):
            self.method = method
            self.inst = inst

        def __run(self, *args, **kwargs):
            return self.method(self.inst, *args, **kwargs)

        @property
        def cls_name(self):
            """ nome da classe que está no controle do méthodo """
            return self.__class__.__name__

        @property
        def rm_name(self):
            """ retorna o nome do método sendo excutado """
            return self.method.__name__

        def __call__(self, *args, **kwargs):
            """ executa o método decorado """
            try:
                return self.__run(*args, **kwargs)
            except Exception as err:
                msg = self.ferror.format(name=self.cls_name,
                                         method=self.rm_name,
                                         error=err)
                logger.error(msg)

    def __init__(self, func):
        self.func = func

    def __get__(self, inst, cls):
        return self.wrap(inst, self.func)


class Protected(object):
    """ Executa o método dentro de um try:except. Ignora errors """

    def __init__(self, method):
        self.method = method

    def __get__(self, instance, owner):
        def wrap(*args, **kwargs):
            try:
                return self.method(instance, *args, **kwargs)
            except Exception as err:
                print(("Warnning: '{!s}' Protected: {!s}".format(self.method.__name__, err)))
        return wrap


def calc_percent(byte_counter, data_len):
    """ calcula a porcentagem. retorna o resultado sem formatação."""
    return (float(byte_counter) / float(data_len)) * 100.0


def get_filename(filepath, fullname=True):
    """
    fullname: True  -> C:\\filedir\\file.txt -> file.txt
    fullname: False -> C:\\filedir\\file.txt -> file
    """
    filename = os.path.split(filepath)[-1]
    if not fullname: filename = os.path.splitext(filename)[0]
    return filename


def security_save(filepath, _configobj=None, _list=None, newline="\n"):
    """ salva as configurações da forma mais segura possível. 
    filepath - local para salvar o arquivo
    _configobj - dicionário de configurações
    _list - salva a lista, aplicando ou não a newline.
    newline='' - caso não haja interesse na adição de uma nova linha.
    """
    try:  # criando o caminho para o arquivo de backup
        filename = get_filename(filepath)  # nome do arquivo no path.
        bkfilepath = filepath.replace(filename, ("bk_" + filename))
    except Exception as err:
        logger.error("Path to backup file: %s" % err)
        return False

    # guarda o arquivo antigo temporariamente
    if os.path.exists(filepath):
        try:
            os.rename(filepath, bkfilepath)
        except Exception as err:
            logger.error("Rename config to backup: %s" % err)
            return False

    try:  # começa a criação do novo arquivo de configuração
        with open(filepath, "w") as configsfile:
            if type(_list) is list:
                for data in _list:
                    configsfile.write("%s%s" % (data, newline))
            elif isinstance(_configobj, configobj.ConfigObj):
                _configobj.write(configsfile)
            # levanta a exeção com o objetivo de recuperar o arquivo original
            else:
                raise AttributeError("invalid config data")
        if os.path.exists(filepath):
            try:
                os.remove(bkfilepath)
            except:
                pass
    except Exception as err:
        logger.critical("Saving config file: %s" % err)
        # remove o arquivo atual do erro.
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        # restaura o arquivo original
        if not os.path.exists(filepath):
            try:
                os.rename(bkfilepath, filepath)
            except:
                pass
        return False
    return True