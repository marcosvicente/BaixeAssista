# -*- coding: ISO-8859-1 -*-

import wx
import os
import json
import base64
import random
import base64
import string
#######################################################################################

if wx.Platform == '__WXMSW__':
	from wx.lib.flashwin import FlashWindow

class PlayerPanel(wx.Panel):
	def __init__(self, parent, id):
		wx.Panel.__init__(self, parent, -1)
		self.SetBackgroundColour( wx.WHITE )
		self.mainWindow = parent

		mainSizer = wx.BoxSizer( wx.VERTICAL )

		self.swf_name = ["player_1.swf", "player_2.swf"]
		self.flash = FlashWindow(self, style=wx.SUNKEN_BORDER)

		self.reload()

		mainSizer.Add(self.flash, 1, wx.EXPAND)
		self.SetSizer(mainSizer)
		self.SetAutoLayout(True)

	def changeDisplayState(self, evt=None):
		# permuta o modo de tela
		isFullScreen = not self.GetParent().IsFullScreen()
		self.GetParent().ShowFullScreen( isFullScreen)

	def getfilename(self, size=25):
		letras = [char for char in string.ascii_letters]
		filename = "".join( [random.choice( letras) for i in range(size)] )
		return filename

	def setSettings(self):
		porta, filename = 80, self.getfilename()
		localStream = "http://localhost:%d/%s"%(porta, filename)

		## json.cfg modelo de configs para settings.txt
		path = os.path.join(os.getcwd(), 'swf_player', 'json.cfg')
		jsonCfgFile = open( path)
		data = jsonCfgFile.read()
		configs = json.loads( data )
		jsonCfgFile.close()

		env = configs['cfg']['environment']
		env['thumbnail'] = ""
		env['token1'] = base64.b64encode( localStream)
		configs['cfg']['info']['video']['title'] = ""
		env['vcode'] = self.getfilename(5)
		env['usage_limit'] = '30000000'
		env['usage_reset_timeleft'] = '0'
		env['usage_amount'] = '0'
		env['scst'] = '0'

		env['isembed'] = False
		configs['cfg']['ads']['text_ad'] = {}
		configs['cfg']['ads']['play_banner']['m_url'] = ""
		configs['cfg']['ads']['popunder']['url'] = '' 

		if hasattr(self.mainWindow, "manage"):
			if self.mainWindow.manage: # manage já deve ter sido iniciado
				configs['cfg']['info']['video']['title'] = self.mainWindow.manage.getVideoTitle()

		env['ip'] = '%s.%s.%s.%s'%(random.randint(0,255), random.randint(0,255), 
				                   random.randint(0,255), random.randint(0,255))

		path = os.path.join(os.getcwd(), 'swf_player', 'settings.txt')
		settingsFile = open( path, 'w')
		data = json.dumps( configs )
		settingsFile.write( data )
		settingsFile.close()
		
	def reload(self, evt=None):
		self.setSettings()
		try:
			wx.BeginBusyCursor()
			path = os.path.join('file://', os.getcwd(), "swf_player", self.swf_name[0])
			self.flash.LoadMovie(0, path)
			wx.EndBusyCursor()
		except Exception, err:
			print err
		self.swf_name.reverse()
		
########################################################################
class Player(wx.MiniFrame):
	""""""
	#----------------------------------------------------------------------
	def __init__( self, parent, title="Player Window", pos=wx.DefaultPosition, 
		          size=(640,480), style=wx.DEFAULT_FRAME_STYLE ):
		wx.MiniFrame.__init__(self, parent, -1, title, pos, size, style)

		self.playerPainel = PlayerPanel(self, -1)

		mainSizer = wx.BoxSizer( wx.VERTICAL )
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.fullScreenButton = wx.Button(self, wx.NewId(), "Tela cheia")
		self.reloadButton = wx.Button(self, wx.NewId(), "Recarregar")

		btnSizer.AddStretchSpacer()
		btnSizer.Add(self.fullScreenButton, 0, wx.EXPAND|wx.ALL,2)
		btnSizer.Add(self.reloadButton, 0, wx.EXPAND|wx.ALL, 2)

		self.Bind(wx.EVT_BUTTON, self.displayState, self.fullScreenButton)
		self.Bind(wx.EVT_BUTTON, self.reload, self.reloadButton)

		mainSizer.Add(self.playerPainel, 1, wx.EXPAND)
		mainSizer.Add(btnSizer, 0, wx.EXPAND)

		self.SetSizer(mainSizer)
		self.Show()

	def displayState(self, evt=None):
		# troca o label do botao
		if self.fullScreenButton.GetLabel() == "Tela cheia":
			self.fullScreenButton.SetLabel("Tela normal")
		else:
			self.fullScreenButton.SetLabel("Tela cheia")
		self.playerPainel.changeDisplayState( evt)

	def reload(self, evt=None):
		self.playerPainel.reload(evt)


if __name__ == "__main__":
	app = wx.PySimpleApp()
	# create window/frame, no parent, -1 is default ID, title, size
	# change size as needed
	frame = wx.Frame(None, -1, "FlashWindow", size = (500, 400))

	playerPainel = PlayerPanel(frame, -1)
	# make instance of class, -1 is default ID
	#Player(frame)

	# show frame
	frame.Show(True)

	# start event loop
	app.MainLoop()