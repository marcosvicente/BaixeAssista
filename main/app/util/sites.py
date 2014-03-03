# coding: utf-8
import binascii
import os
import re


def limit_text(text, maxchars=50, endchars="..."):
    if len(text) > maxchars:
        text = text[:maxchars] + endchars
    return text


def clear_text(text):
    """ remove todos os carecteres considerados inválidos """
    return re.sub(r"[/*&:|\"\'=\\?<>!%$@#()]+", "_", text)


def get_random_text(size=25):
    return str(binascii.hexlify(os.urandom(int(size * 0.5))), encoding='UTF-8')


def get_with_seek(link, seek):
    if link.endswith(","):
        link += str(seek)
    if re.match(".+(?:start=|ec_seek=|fs=)", link):
        link += str(seek)
    if re.match(".+(?:range=%s-)", link):
        link %= str(seek)
    return link

