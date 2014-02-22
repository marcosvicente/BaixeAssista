# -*- coding: ISO-8859-1 -*-
import base64
import re
import math


class AES(object):
    BIT_KEY_128 = 128
    BIT_KEY_192 = 192
    BIT_KEY_256 = 256
    SBOX = [99, 124, 119, 123, 242, 107, 111, 197, 48, 1, 103, 43, 254, 215, 171, 118, 202, 130, 201, 125, 250, 89, 71,
            240, 173, 212, 162, 175, 156, 164, 114, 192, 183, 253, 147, 38, 54, 63, 247, 204, 52, 165, 229, 241, 113,
            216, 49, 21, 4, 199, 35, 195, 24, 150, 5, 154, 7, 18, 128, 226, 235, 39, 178, 117, 9, 131, 44, 26, 27, 110,
            90, 160, 82, 59, 214, 179, 41, 227, 47, 132, 83, 209, 0, 237, 32, 252, 177, 91, 106, 203, 190, 57, 74, 76,
            88, 207, 208, 239, 170, 251, 67, 77, 51, 133, 69, 249, 2, 127, 80, 60, 159, 168, 81, 163, 64, 143, 146, 157,
            56, 245, 188, 182, 218, 33, 16, 255, 243, 210, 205, 12, 19, 236, 95, 151, 68, 23, 196, 167, 126, 61, 100,
            93, 25, 115, 96, 129, 79, 220, 34, 42, 144, 136, 70, 238, 184, 20, 222, 94, 11, 219, 224, 50, 58, 10, 73, 6,
            36, 92, 194, 211, 172, 98, 145, 149, 228, 121, 231, 200, 55, 109, 141, 213, 78, 169, 108, 86, 244, 234, 101,
            122, 174, 8, 186, 120, 37, 46, 28, 166, 180, 198, 232, 221, 116, 31, 75, 189, 139, 138, 112, 62, 181, 102,
            72, 3, 246, 14, 97, 53, 87, 185, 134, 193, 29, 158, 225, 248, 152, 17, 105, 217, 142, 148, 155, 30, 135,
            233, 206, 85, 40, 223, 140, 161, 137, 13, 191, 230, 66, 104, 65, 153, 45, 15, 176, 84, 187, 22]
    RCON = [[0, 0, 0, 0], [1, 0, 0, 0], [2, 0, 0, 0], [4, 0, 0, 0], [8, 0, 0, 0], [16, 0, 0, 0], [32, 0, 0, 0],
            [64, 0, 0, 0], [128, 0, 0, 0], [27, 0, 0, 0], [54, 0, 0, 0]]

    def decrypt(self, param1, param2, param3):
        loc_16 = 0
        loc_18 = 0
        loc_19 = None
        loc_20 = None
        loc_4 = 16

        if not (param3 == self.BIT_KEY_128 or param3 == self.BIT_KEY_192 or param3 == self.BIT_KEY_256):
            raise AttributeError("Must be a key mode of either 128, 192, 256 bits")

        param1 = base64.b64decode(param1)
        param2 = param2.encode("utf-8")

        loc_5 = param3 / 8
        loc_6 = [0] * loc_5

        loc_7 = 0
        while (loc_7 < loc_5):
            loc_6[loc_7] = ord(param2[loc_7])
            loc_7 += 1

        loc_8 = self.cipher(loc_6, self.keyExpansion(loc_6))
        loc_8.extend(self.cipher(loc_6, self.keyExpansion(loc_6)))
        loc_8 = loc_8[0: (loc_5 - 16)]

        loc_9 = [0] * 16
        loc_10 = param1[0: 8]

        loc_7 = 0
        while (loc_7 < 8):
            loc_9[loc_7] = ord(loc_10[loc_7])
            loc_7 += 1

        loc_11 = self.keyExpansion(loc_8)
        loc_12 = int(math.ceil((len(param1) - 8.0) / loc_4))

        loc_13 = [0] * loc_12

        loc_16 = 0
        while (loc_16 < loc_12):
            loc_13[loc_16] = param1[8 + loc_16 * loc_4: 8 + loc_16 * loc_4 + loc_4]
            loc_16 += 1

        loc_14 = loc_13
        loc_15 = [0] * len(loc_14)

        loc_16 = 0
        while (loc_16 < loc_12):

            loc_18 = 0
            while (loc_18 < 4):
                loc_9[15 - loc_18] = loc_16 >> loc_18 * 8 & 255
                loc_18 += 1

            loc_18 = 0
            while (loc_18 < 4):
                expr = (loc_16 + 1) / 4294967296 - 1
                expr = (int(expr) >> loc_18 * 8 & 255)

                loc_9[15 - loc_18 - 4] = expr
                loc_18 += 1

            loc_19 = self.cipher(loc_9, loc_11)
            loc_20 = [0] * len(str(loc_14[loc_16]))

            loc_7 = 0
            while (loc_7 < len(str((loc_14[loc_16]))) ):
                loc_20[loc_7] = loc_19[loc_7] ^ ord(str(loc_14[loc_16])[loc_7])
                loc_20[loc_7] = chr(loc_20[loc_7])
                loc_7 += 1

            loc_15[loc_16] = "".join(loc_20)
            loc_16 += 1

        return "".join(loc_15)

    def cipher(self, param1, param2):
        loc_3 = 4
        loc_4 = len(param2) / loc_3 - 1
        loc_5 = [[0] * 4, [0] * 4, [0] * 4, [0] * 4]

        loc_6 = 0
        while (loc_6 < 4 * loc_3):
            floorIndex = int(math.floor(loc_6 / 4))
            moduleIndex = loc_6 % 4

            loc_5[moduleIndex][floorIndex] = param1[loc_6]
            loc_6 += 1

        print(loc_5)

        loc_5 = self.addRoundKey(loc_5, param2, 0, loc_3)

        loc_7 = 1
        while (loc_7 < (len(param2) / loc_3)):
            loc_5 = self.subBytes(loc_5, loc_3)
            loc_5 = self.shiftRows(loc_5, loc_3)
            loc_5 = self.mixColumns(loc_5)
            loc_5 = self.addRoundKey(loc_5, param2, loc_7, loc_3)
            loc_7 += 1

        loc_5 = self.subBytes(loc_5, loc_3)
        loc_5 = self.shiftRows(loc_5, loc_3)
        loc_5 = self.addRoundKey(loc_5, param2, loc_4, loc_3)
        loc_8 = [0] * (4 * loc_3)

        loc_9 = 0
        while (loc_9 < 4 * loc_3):
            loc_8[loc_9] = loc_5[loc_9 % 4][int(math.floor(loc_9 / 4))]
            loc_9 += 1

        return loc_8

    def keyExpansion(self, param1):
        loc_8 = None
        loc_9 = 0
        loc_2 = 4
        loc_3 = len(param1) / 4
        loc_4 = loc_3 + 6
        loc_5 = [0] * (loc_2 * (loc_4 + 1))
        loc_6 = [0] * 4

        loc_7 = 0
        while (loc_7 < loc_3):
            loc_8 = [param1[4 * loc_7], param1[4 * loc_7 + 1], param1[4 * loc_7 + 2], param1[4 * loc_7 + 3]]
            loc_5[loc_7] = loc_8
            loc_7 += 1

        loc_7 = loc_3
        while (loc_7 < loc_2 * (loc_4 + 1)):
            loc_5[loc_7] = [0] * 4

            loc_9 = 0
            while (loc_9 < 4):
                loc_6[loc_9] = loc_5[loc_7 - 1][loc_9]
                loc_9 += 1

            if (loc_7 % loc_3 == 0):
                loc_6 = self.subWord(self.rotWord(loc_6))

                loc_9 = 0
                while (loc_9 < 4):
                    loc_6[loc_9] = loc_6[loc_9] ^ self.RCON[loc_7 / loc_3][loc_9]
                    loc_9 += 1

            elif (loc_3 > 6 and loc_7 % loc_3 == 4):
                loc_6 = self.subWord(loc_6)

            loc_9 = 0
            while (loc_9 < 4):
                loc_5[loc_7][loc_9] = loc_5[loc_7 - loc_3][loc_9] ^ loc_6[loc_9]
                loc_9 += 1

            loc_7 += 1
        return loc_5

    def subBytes(self, param1, param2):
        loc_4 = 0
        loc_3 = 0
        while (loc_3 < 4):
            loc_4 = 0
            while (loc_4 < param2):
                param1[loc_3][loc_4] = self.SBOX[param1[loc_3][loc_4]]
                loc_4 += 1

            loc_3 += 1
        return param1

    def shiftRows(self, param1, param2):
        loc_3 = [0] * 4
        loc_5 = 0
        loc_4 = 1
        while (loc_4 < 4):

            loc_5 = 0
            while (loc_5 < 4):
                loc_3[loc_5] = param1[loc_4][(loc_5 + loc_4) % param2]
                loc_5 += 1

            loc_5 = 0
            while (loc_5 < 4):
                param1[loc_4][loc_5] = loc_3[loc_5]
                loc_5 += 1

            loc_4 += 1
        return param1

    def mixColumns(self, param1):
        loc_2 = 0
        while (loc_2 < 4):
            loc_3 = [0] * 4
            loc_4 = [0] * 4

            loc_5 = 0
            while (loc_5 < 4):
                loc_3[loc_5] = param1[loc_5][loc_2]

                if (param1[loc_5][loc_2] & 128):
                    loc_4[loc_5] = (param1[loc_5][loc_2] << 1 ^ 283)
                else:
                    loc_4[loc_5] = (param1[loc_5][loc_2] << 1)

                loc_5 += 1

            param1[0][loc_2] = loc_4[0] ^ loc_3[1] ^ loc_4[1] ^ loc_3[2] ^ loc_3[3]
            param1[1][loc_2] = loc_3[0] ^ loc_4[1] ^ loc_3[2] ^ loc_4[2] ^ loc_3[3]
            param1[2][loc_2] = loc_3[0] ^ loc_3[1] ^ loc_4[2] ^ loc_3[3] ^ loc_4[3]
            param1[3][loc_2] = loc_3[0] ^ loc_4[0] ^ loc_3[1] ^ loc_3[2] ^ loc_4[3]

            loc_2 += 1
        return param1

    def addRoundKey(self, param1, param2, param3, param4):
        loc_5 = 0
        while (loc_5 < 4):
            loc_6 = 0
            while (loc_6 < param4):
                param1[loc_5][loc_6] = param1[loc_5][loc_6] ^ param2[param3 * 4 + loc_6][loc_5]
                loc_6 += 1

            loc_5 += 1
        return param1

    def subWord(self, param1):
        loc_2 = 0
        while (loc_2 < 4):
            param1[loc_2] = self.SBOX[param1[loc_2]]
            loc_2 += 1
        return param1

    def rotWord(self, param1):
        loc_2 = param1[0]

        loc_3 = 0
        while (loc_3 < 3):
            param1[loc_3] = param1[loc_3 + 1]
            loc_3 += 1

        param1[3] = loc_2
        return param1


###################################################################################################
def string2bin(hexString):
    """ hexString -> lista bin [0001, 0002, ....]"""
    lista_bin = []
    for hexValue in hexString:
        # extrai 0b, depois o nibble 4 bits
        bin_value = "000%s" % ( bin(int(hexValue, 16))[2:])
        lista_bin.append(bin_value[-4:])
    return [chunk for chunk in "".join(lista_bin)]


def d9300(param1, param2, param3):
    return bitDecrypt(param1, param2, param3, 26, 25431, 56989, 93, 32589, 784152)


def lion(param1, param2, param3):
    return bitDecrypt(param1, param2, param3, 82, 84669, 48779, 32, 65598, 115498)


def bin2String(lista_bin):
    listaHex = [hex(int(bin_value, 2))[2:] for bin_value in lista_bin]
    return "".join(listaHex)


def decrypt32byte(hexString, key1, key2):
    """"""
    reg1 = string2bin(hexString)

    reg6 = []
    for index in range(384):
        key1 = (int(key1) * 11 + 77213) % 81371
        key2 = (int(key2) * 17 + 92717) % 192811
        reg6.append((int(key1) + int(key2)) % 128)

    for index in range(256, -1, -1):
        reg5 = reg6[index]
        reg8 = reg1[reg5]

        reg4 = index % 128
        reg1[reg5] = reg1[reg4]

        reg1[reg4] = reg8

    for index in range(0, 128):
        reg1[index] = str(int(reg1[index]) ^ int(reg6[index + 256]) & 1)

    lista_bin = []
    binString = "".join(reg1)
    for index in range(0, len(binString), 4):
        # fatiando a string em pedaços de 4 caracteres
        lista_bin.append(binString[index: index + 4])

    # string hexadecimal decriptada
    return bin2String(lista_bin)


def bitDecrypt(param1, param2, param3, param4=11, param5=77213, param6=81371, param7=17, param8=92717, param9=192811):
    loc_10 = string2bin(param1)
    loc_11 = len(loc_10) * 2

    loc_12 = []
    loc_13 = 0

    while loc_13 < loc_11 * 1.5:
        param2 = (param2 * param4 + param5) % param6
        param3 = (param3 * param7 + param8) % param9
        loc_12.append(int((param2 + param3) % (loc_11 * 0.5)))
        loc_13 += 1

    loc_13 = loc_11
    while (loc_13 >= 0):
        loc_17 = loc_12[loc_13]
        loc_18 = int(loc_13 % (loc_11 * 0.5))
        loc_19 = loc_10[loc_17]
        loc_10[loc_17] = loc_10[loc_18]
        loc_10[loc_18] = loc_19
        loc_13 -= 1

    loc_13 = 0
    while (loc_13 < loc_11 * 0.5):
        loc_10[loc_13] = str(int(loc_10[loc_13]) ^ int(loc_12[loc_13 + loc_11]) & 1)
        loc_13 += 1

    loc_13 = 0
    loc_15 = []
    loc_14 = "".join(loc_10)

    while (loc_13 < len(loc_14)):
        loc_20 = loc_14[loc_13: loc_13 + 4]
        loc_15.append(loc_20)
        loc_13 = loc_13 + 4

    return bin2String(loc_15)


def parse(**kwargs):
    output = ""
    outputPattern = base64.b64decode(kwargs["spn"])
    params = [values.split("=") for values in outputPattern.split("&")]

    for paramNameType in params:
        if paramNameType[1] == "1":
            keyString1, randomKey = kwargs["sece2"], kwargs["rkts"]
            decryptedString = decrypt32byte(keyString1, randomKey, kwargs["key2"])
            output = output + (paramNameType[0] + "=" + decryptedString + "&")

        elif paramNameType[1] == "2":
            keyString1, randomKey = kwargs["g_ads_url"], kwargs["rkts"]
            decryptedString = bitDecrypt(keyString1, randomKey, kwargs["key2"])
            output = output + (paramNameType[0] + "=" + decryptedString + "&")

        elif paramNameType[1] == "3":
            keyString1, randomKey = kwargs["g_ads_type"], kwargs["rkts"]
            decryptedString = d9300(keyString1, randomKey, kwargs["key2"])
            output = output + (paramNameType[0] + "=" + decryptedString + "&")

        elif paramNameType[1] == "4":
            keyString1, randomKey = kwargs["g_ads_time"], kwargs["rkts"]
            decryptedString = lion(keyString1, randomKey, kwargs["key2"])
            output = output + (paramNameType[0] + "=" + decryptedString + "&")

    if output.find("&f=") < 0:
        matchObj = re.search("c=([^\&]+)", output)
        if matchObj: output += ("f=" + matchObj.group(1) + "&")
    return output


if __name__ == "__main__":
    title = "Filling this ebony whores gaping asshole"
    url = "nwDaHk+De1Dun0x1EDTR+wkg5J3ks0t9tDYP7tejr76+2yFH2ce4F0dWXgRYZQiNWStgP9ngyTz2ZPJ22LExSBzv4o7L3jVUgvWfmhGDZSC1y+6ezVQGuxtOBsUoChl6cnEPMFxjswQG2AMaz7+rk3AKMbRj3aCPUgZk/M/Aq1wf9Pemv6d8vecXhx2Ut12w+aJYPgWd"

    aes = AES()

    print((title, url))
    print((aes.decrypt(url, title, AES.BIT_KEY_256)))