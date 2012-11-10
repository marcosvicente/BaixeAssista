import binascii
import os
import re

def DECODE(texto, alter="ISO-8859-1"):
    """ Tenta decodificar para utf-8. 
    Em caso de erro, a decodifica��o alternativa ser� usada """
    try:
        texto = texto.decode('utf-8')
    except UnicodeDecodeError:
        texto = texto.decode(alter)
    except Exception:
        pass
    return texto

def ENCODE(texto, alter="ISO-8859-1"):
    """ Tenta codificar para utf-8. 
    Em caso de erro, a codfica��o alternativa ser� usada """
    try:
        texto = texto.encode('utf-8')
    except UnicodeEncodeError:
        texto = texto.encode( alter)
    except Exception:
        pass
    return texto

def limite_text(text, maxchars=50, endchars="..."):
    if len(text) > maxchars: text = text[:maxchars] + endchars
    return text

def clear_text(text):
    """ remove todos os carecteres considerados inv�lidos """
    return re.sub(r"[/*&:|\"\'=\\?<>!%$@#()]+", "_", text)

def get_radom_text(size=25):
    return binascii.hexlify(os.urandom(int(size*0.5)))

def get_with_seek(link, seek):
    if link.endswith(","): link += str(seek)
    if re.match(".+(?:start=|ec_seek=|fs=)", link): link += str(seek)
    if re.match(".+(?:range=%s-)", link): link %= str(seek)
    return link

