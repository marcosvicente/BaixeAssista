# -*- coding: UTF-8 -*-
import os, sys, re

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Definem a versão e o sistema operacional do programa
PROGRAM_VERSION = "3.0.0"
PROGRAM_SYSTEM = {"Windows": "oswin", "Linux": "oslinux"}

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

EMAIL_USE_TLS = 1
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 25

MANAGE_OBJECT = None
PROJECTPATH = ""

# cuidado com isso!!!
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

matchobj = re.search("(?P<maindir>.+main)", os.getcwd())
if matchobj: PROJECTPATH = matchobj.group("maindir")

# Diretórios contendo os scripts do programa
if not re.match(".+main$", PROJECTPATH):
    PROJECTPATH = os.path.join(os.getcwd(), "main")

# diretório do exectável final
matchobj = re.search("(?P<roortdir>.+)main", PROJECTPATH)
ROOT_DIR = matchobj.group("roortdir")

STATIC_PATH = os.path.join(PROJECTPATH, "static")
TEMPLATE_PATH = os.path.join(PROJECTPATH, "templates")

APPDIR = os.path.join(PROJECTPATH, "app")
CONFIGS_DIR = os.path.join(APPDIR, "configs")
IMAGES_DIR = os.path.join(APPDIR, "images")
LOGS_DIR = os.path.join(APPDIR, "logs")
INTERFACE_DIR = os.path.join(APPDIR, "win")

# pasta(diretório) padrão de vídeos
VIDEOS_DIR_TEMP_NAME = "temp"
VIDEOS_DIR_NAME = "videos"
DEFAULT_VIDEOS_DIR = os.path.join(ROOT_DIR, VIDEOS_DIR_NAME)

if not ROOT_DIR in sys.path: # import do projeto
    sys.path.append( ROOT_DIR )
    
if not PROJECTPATH in sys.path: # import do projeto
    sys.path.append( PROJECTPATH )
    
if not APPDIR in sys.path: # import das apps
    sys.path.append( APPDIR )
# ------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(CONFIGS_DIR,"database","db_main.db"),  # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    STATIC_PATH.replace(os.sep,"/"),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '^h*90a=&08zj=m^!kg5b8xh_qyj65)a6a8fulgm1!jca*euq#o'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'main.app.manager.ManageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'main.urls'

TEMPLATE_DIRS = (
    TEMPLATE_PATH.replace(os.sep,"/"),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'main.app',
    'concurrent_server',
    'south',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(levelname)s][%(asctime)s] %(message)s'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
         'BA_MANAGER': {
            'filename': os.path.join(LOGS_DIR, "manager.log"),
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'simple',
            'maxBytes': 1024**2, # 1 MB
            'backupCount': 5,
            'level': 'DEBUG'
        },
        'BA_SEND_MAIL': {
            'filename': os.path.join(LOGS_DIR, "sendmail.log"),
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'simple',
            'maxBytes': 1024**2, # 1 MB
            'backupCount': 5,
            'level': 'DEBUG'
        },
         'BA_WMOVIE': {
            'filename': os.path.join(LOGS_DIR, "wmovie.log"),
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'simple',
            'maxBytes': 1024**2, # 1 MB
            'backupCount': 5,
            'level': 'DEBUG'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'main.app.manager': {
            'handlers': ['BA_MANAGER'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'main.app.bugs': {
            'handlers': ['BA_SEND_MAIL'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'main.app.window.movie': {
            'handlers': ['BA_WMOVIE'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}
