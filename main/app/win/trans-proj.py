import glob
import os
import re

## ------------------------------------------------------------
cdir = os.path.dirname(os.path.abspath(__file__))
ldir = os.path.join(cdir, "i18n")

def set_relative_paths():
    for filename in os.listdir(ldir):
        print(("Processing: ", filename))
        
        with open(os.path.join(ldir, filename), "r+") as f:
            content = f.read()
            lnames = []
            
            for name in re.findall("filename=\"(.+?)\"", content):
                name = os.path.basename( name )
                
                if name in lnames: continue
                lnames.append( name )
                
                content = content.replace(name, os.path.join("..", name))
            
            f.seek(0)
            f.write(content)

def create_proj(lfiles, projname, template):
    with open(projname, "w") as _file:
        sources = " ".join(lfiles)
        data = template.format(sources = sources)
        _file.write( data )
        print(data)

template = """
SOURCES = {sources}

TRANSLATIONS = i18n\en_US_pt_BR.ts i18n\en_US_es_ES.ts
"""

projname = "py-win.pro"
create_proj(glob.glob( "*.py"), projname, template)

os.system("pyside-lupdate " + projname)
set_relative_paths()

## ------------------------------------------------------------
#template = """
#SOURCES = {sources}
#
#TRANSLATIONS = i18n\en_pt_BR-qt.ts i18n\en_es-qt.ts
#"""
#
#projname = "qt-win.pro"
#create_proj(glob.glob("*.ui"), projname, template)
#os.system("lupdate "+ projname)
#        
            
        
            
            
            
            
            
            
            
            
            
            
            
