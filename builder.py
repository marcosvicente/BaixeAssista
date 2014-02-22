# coding: utf-8
import os
import subprocess
import compileall
import shutil
import re

from . import packer
from .main import settings


EXE_NAME = 'BaixeAssista_v%s' % settings.PROGRAM_VERSION
BUILD_DIR = os.path.join(os.environ["USERPROFILE"], "BaixeAssistaRelease")  # build exe
DIST_DIR = os.path.join(BUILD_DIR, "dist")
EXE_DIR = os.path.join(BUILD_DIR, EXE_NAME)
FINAL_DIR = os.path.join(EXE_DIR, EXE_NAME)
TARGET_DIR = packer.TARGET_DIR

IGNORE_FILES = ("_pass", "changes.txt", ".gitignore", "ba_trans.po")
SKIP_DIR = "_ignore"


def find_compiler(compilername="pyinstaller.py"):
    """ busca o caminho completo para o compilador(pyinstaller) """
    allpaths = os.environ["path"]
    for path in allpaths.split(";"):
        # provavel caminho do compilador
        compilerpath = os.path.join(path, compilername)
        if os.path.isfile(compilerpath):
            return compilerpath
    return ""


def start_build():
    """ inicia a contrução do executável """
    COMPILER = 'python "%s"' % find_compiler()
    COMMANDS = '-w --out="{outdir}" --icon={ico} BaixeAssista.py --name="{exename}"'.format(
        outdir=BUILD_DIR, ico="movies.ico", exename=EXE_NAME
    )
    CMD = COMPILER + " " + COMMANDS

    # remove all .pyc / .pyo
    packer.clean_all_nopy(TARGET_DIR)

    print(("COMPILER: ", COMPILER))
    print(("COMMANDS: ", COMMANDS))
    print(("CMD: ", CMD))
    print("STARTING BUILD")

    retcode = subprocess.call(CMD)
    print(("Compile success: %d" % retcode))
    return retcode


# ---------------------------------------------------------------
def copy_to_dest(source, destination):
    """ copia os arquivo do executável para a pasta de distribuição """
    sourcedir = os.path.dirname(source)

    for root, dirs, files in os.walk(source):
        try:
            relativedir = root.split(sourcedir + os.sep)[-1]
            destdir = os.path.join(destination, relativedir)

            # não inclui pastas que contenham o arquivo "__ignore__"
            if SKIP_DIR in files: continue

            if not os.path.exists(destdir):
                print(("Making dir: ", destdir))
                os.mkdir(destdir)
            else:
                print(("Dir already exist: ", destdir))

            for filename in files:
                if filename in IGNORE_FILES: continue
                filepath = os.path.join(root, filename)
                filedestdir = os.path.join(destdir, filename)

                if re.match(".+py$", filename):
                    # copiando os arquivos já compilados
                    compileall.compile_file(filepath, force=True)
                    src = filepath.replace(".py", ".pyc")
                    dest = filedestdir.replace(".py", ".pyc")
                    shutil.copy(src, dest)
                else:
                    shutil.copy(filepath, filedestdir)
        except Exception as e:
            print(("[Exporting files] {0}".format(e)))
            exit(1)


if __name__ == "__main__":
    if not os.path.exists(BUILD_DIR):
        os.mkdir(BUILD_DIR)

    if start_build() == 0:
        print("Compile successfully!")
        os.rename(DIST_DIR, EXE_DIR)

        print(("Rename: {0} to: {1} success: {2}".format(DIST_DIR, EXE_DIR, os.path.exists(EXE_DIR))))
        print("Exporting files to exe")

        packer.clean_all_nopy(TARGET_DIR)
        copy_to_dest(TARGET_DIR, FINAL_DIR)

        TO_MAKE = os.path.join(
            FINAL_DIR,
            settings.VIDEOS_DIR_NAME,
            settings.VIDEOS_DIR_TEMP_NAME
        )
        os.makedirs(TO_MAKE)
        try:
            os.chdir(FINAL_DIR)  # vai para o diretorio do executável.
            subprocess.call(os.path.join(FINAL_DIR, EXE_NAME + ".exe"))
        except Exception as err:
            print(("Err[exe start] {0}".format(err)))
    else:
        print("Error Compiling...")
    eval(input("Press enter to exit..."))
