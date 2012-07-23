# -*- coding: ISO-8859-1 -*-
import base64, re

def string2bin( hexString):
	""" hexString -> lista bin [0001, 0002, ....]"""
	lista_bin = []
	for hexValue in hexString:
		# extrai 0b, depois o nibble 4 bits
		bin_value = "000%s" % ( bin( int(hexValue, 16) ) [2:])
		lista_bin.append( bin_value[-4:] )
	return [chunk for chunk in "".join( lista_bin )]

def d9300(param1, param2, param3):
	return bitDecrypt(param1, param2, param3, 26, 25431, 56989, 93, 32589, 784152);

def lion(param1, param2, param3):
	return bitDecrypt(param1, param2, param3, 82, 84669, 48779, 32, 65598, 115498)

def bin2String( lista_bin):
	listaHex = [hex( int(bin_value, 2) )[2:] for bin_value in lista_bin]
	return "".join( listaHex )

def decrypt32byte(hexString, key1, key2):
	""""""
	reg1 = string2bin( hexString )

	reg6 = []
	for index in xrange(384):
		key1 = (int(key1) * 11 + 77213) % 81371
		key2 = (int(key2) * 17 + 92717) % 192811
		reg6.append((int(key1) + int(key2)) % 128)

	for index in xrange(256, -1, -1):
		reg5 = reg6[ index ]
		reg8 = reg1[ reg5 ]

		reg4 = index % 128
		reg1[ reg5 ] = reg1[ reg4 ]

		reg1[ reg4 ] = reg8

	for index in xrange(0, 128):
		reg1[ index ] = str( int(reg1[ index ]) ^ int(reg6[ index + 256 ] ) & 1)

	lista_bin = []
	binString = "".join( reg1 )
	for index in xrange(0, len(binString), 4):
		# fatiando a string em pedaços de 4 caracteres
		lista_bin.append( binString[ index : index + 4] )

	# string hexadecimal decriptada
	return bin2String( lista_bin )

def bitDecrypt(param1, param2, param3, param4 = 11, param5 = 77213, param6 = 81371, param7 = 17, param8 = 92717, param9 = 192811):
	_loc_10 = string2bin(param1)
	_loc_11 = len( _loc_10 ) * 2

	_loc_12 = []; _loc_13 = 0

	while _loc_13 < _loc_11 * 1.5:
		param2 = (param2 * param4 + param5) % param6
		param3 = (param3 * param7 + param8) % param9
		_loc_12.append( int( (param2 + param3) % (_loc_11 * 0.5) ) )
		_loc_13 += 1

	_loc_13 = _loc_11
	while (_loc_13 >= 0):
		_loc_17 = _loc_12[_loc_13]
		_loc_18 = int( _loc_13 % (_loc_11 * 0.5) )
		_loc_19 = _loc_10[_loc_17]
		_loc_10[_loc_17] = _loc_10[_loc_18]
		_loc_10[_loc_18] = _loc_19
		_loc_13 -= 1

	_loc_13 = 0
	while (_loc_13 < _loc_11 * 0.5):

		_loc_10[_loc_13] = str( int(_loc_10[_loc_13]) ^ int(_loc_12[_loc_13 + _loc_11]) & 1)
		_loc_13 += 1

	_loc_13 = 0; _loc_15 = []
	_loc_14 = "".join( _loc_10 )

	while (_loc_13 < len(_loc_14)):

		_loc_20 = _loc_14[_loc_13 : _loc_13 + 4]
		_loc_15.append( _loc_20 )
		_loc_13 = _loc_13 + 4

	return bin2String( _loc_15 )

def parse( **kwargs):
	output = ""
	outputPattern = base64.b64decode( kwargs["spn"] )
	params = [values.split("=") for values in outputPattern.split("&")]
	
	for paramNameType in params:
		if paramNameType[1] ==  "1":
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
	result = parse( g_ads_url = "18989a3d04bf9fe2fa690a00123e2cbad4a0cc528ce867b1fe349f18caf119c9",
		            g_ads_type = "f9d90e2ddeb12a8d948d407654414ca735404e63b3ca12140ef3d5acc42ab63e",
		            g_ads_time = "38740d2fa2b27961b9ea296c4a88ac2e39146436f2d89e21cd3429d7062336",       
		            rkts = 209220, key2 = 215678, spn = "Yz0yJmY9Mw==",
		            sece2 = "24c79892f61794c627e7c6ff8443566a2d2a658d75bbce194e2efa12e6940")    
	print result