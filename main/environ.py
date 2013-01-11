# coding: utf-8
import os, sys

def setup(skip = False):
    """ configura o ambiente para a execução de um script separado """
    if not skip:
        os.environ['DJANGO_SETTINGS_MODULE'] = "main.settings"
        
        SCRIPT_PATH = os.path.dirname( os.path.abspath(__file__) )
        MAIN_DIR  = os.path.dirname( SCRIPT_PATH )
        
        if not MAIN_DIR in sys.path: sys.path.append(MAIN_DIR)
        
        os.chdir( MAIN_DIR )