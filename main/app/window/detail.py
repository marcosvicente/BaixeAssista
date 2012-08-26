# -*- coding: ISO-8859-1 -*-
import os
import wx
import sys
import math
from wx.lib.agw import ultimatelistctrl as ULC

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necessário para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )

import manager
########################################################################

PIPE_HEIGHT = 25; PIPE_WIDTH = 512
class SubProgressBarRenderer(object):
	DONE_BITMAP = REMAINING_BITMAP = None
	
	def __init__(self, parent):
		self.metaValue = self.currentValue = 0
		self.progressValue = 0
		
	def calculePorcentagem(self):
		""" Calcula a porcentagem sem formatação """
		return int(float(self.currentValue) / float(self.metaValue) * 100.0)
	
	def DrawSubItem(self, dc, rect, line, highlighted, enabled):
		"""Draw a custom progress bar using double buffering to prevent flicker"""
		canvas = wx.EmptyBitmap(rect.width, rect.height)
		mdc = wx.MemoryDC()
		mdc.SelectObject(canvas)

		if highlighted:
			mdc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT)))
		else:
			mdc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW)))
		mdc.Clear()

		self.DrawProgressBar(mdc, 0, 0, rect.width, rect.height, self.progressValue)
		mdc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))

		text = "%s / %s"%(manager.StreamManager.format_bytes( self.currentValue ), 
		                  manager.StreamManager.format_bytes( self.metaValue ))
		
		textWidth, dummy = mdc.GetTextExtent(text)
		mdc.DrawText(text, rect.width/2 - textWidth/2, rect.height/2 - dummy/2)
		dc.SetClippingRegion(rect.x, rect.y, rect.width, rect.height)
		dc.Blit(rect.x+3, rect.y, rect.width-6, rect.height, mdc, 0, 0)
		dc.DestroyClippingRegion()

	def GetLineHeight(self):
		return PIPE_HEIGHT + 6

	def GetSubItemWidth(self):
		return 130

	def UpdateValue(self, current_value, max_value):
		if max_value > 0:
			if current_value < 0: current_value = 0
			
			self.currentValue = current_value
			self.metaValue = max_value
			
			self.progressValue = self.calculePorcentagem()
		else:
			self.currentValue = self.metaValue = self.progressValue = 0
			
	def DrawHorizontalPipe(self, dc, x, y, w, colour):
		"""Draws a horizontal 3D-looking pipe."""
		for r in range(PIPE_HEIGHT):
			red = int(colour.Red() * math.sin((math.pi/PIPE_HEIGHT)*r))
			green = int(colour.Green() * math.sin((math.pi/PIPE_HEIGHT)*r))
			blue = int(colour.Blue() * math.sin((math.pi/PIPE_HEIGHT)*r))
			dc.SetPen(wx.Pen(wx.Colour(red, green, blue)))
			dc.DrawLine(x, y+r, x+w, y+r)

	def DrawProgressBar(self, dc, x, y, w, h, percent):
		"""
		Draws a progress bar in the (x,y,w,h) box that represents a progress of 
		'percent'. The progress bar is only horizontal and it's height is constant 
		(PIPE_HEIGHT). The 'h' parameter is used to vertically center the progress 
		bar in the allotted space.
		
		The drawing is speed-optimized. Two bitmaps are created the first time this
		function runs - one for the done (green) part of the progress bar and one for
		the remaining (white) part. During normal operation the function just cuts
		the necessary part of the two bitmaps and draws them.
		"""
		# Create two pipes
		if self.DONE_BITMAP is None:
			self.DONE_BITMAP = wx.EmptyBitmap(PIPE_WIDTH, PIPE_HEIGHT)
			mdc = wx.MemoryDC()
			mdc.SelectObject(self.DONE_BITMAP)
			self.DrawHorizontalPipe(mdc, 0, 0, PIPE_WIDTH, wx.GREEN)
			mdc.SelectObject(wx.NullBitmap)

			self.REMAINING_BITMAP = wx.EmptyBitmap(PIPE_WIDTH, PIPE_HEIGHT)
			mdc = wx.MemoryDC()
			mdc.SelectObject(self.REMAINING_BITMAP)
			self.DrawHorizontalPipe(mdc, 0, 0, PIPE_WIDTH, wx.RED)
			self.DrawHorizontalPipe(mdc, 1, 0, PIPE_WIDTH-1, wx.WHITE)
			mdc.SelectObject(wx.NullBitmap)
			
		# Center the progress bar vertically in the box supplied
		y = y + (h - PIPE_HEIGHT)/2
		done_rate = (w/100) * percent
		
		dc.DrawBitmap(self.REMAINING_BITMAP.GetSubBitmap((0,0, w, PIPE_HEIGHT)), x, y, False) # gray bitmap
		if done_rate > 0:
			try:
				doneBitmap = self.DONE_BITMAP.GetSubBitmap((0,0, done_rate, PIPE_HEIGHT))
				dc.DrawBitmap(doneBitmap, x, y, False)
			except Exception, err:
				print "Debug[%s] px: %d py: %d rate_width: %d heigth: %d"%(
				    err, x, y, done_rate, PIPE_HEIGHT)
				
########################################################################
class DetailControl( wx.Panel ): # DetailControl
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
		
		self.listControl = ULC.UltimateListCtrl(self,
		        agwStyle = wx.LC_REPORT | 
		        wx.BORDER_RAISED | wx.LC_VRULES |
		        wx.LC_HRULES | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT )
		
		self.listControl.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))

		# col size update
		self.updateTimer = wx.Timer(self, wx.ID_ANY)
		self.Bind( wx.EVT_TIMER, self.updateColunm, self.updateTimer)
		self.updateTimer.Start(1000)

		self.listSubProgressBar = []
		self.rowIndexCount = 0
		self.rowIndex = {}

		self.listColInfo = [_("Proxy"), _("Estado"), _("Segmentos"), _("Progresso"), _("Velocidade")]
		for colIndex in range(len(self.listColInfo)):
			if self.listColInfo[colIndex] == _("Segmentos"):
				self.listControl.InsertColumn(colIndex, self.listColInfo[ colIndex ], format=wx.LIST_FORMAT_CENTRE)
			else:
				self.listControl.InsertColumn(colIndex, self.listColInfo[ colIndex ])

		# Sizer config
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.listControl, 1, wx.EXPAND)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)

	def __del__(self):
		del self.listSubProgressBar
		del self.rowIndexCount
		del self.rowIndex

	def updateColunm(self, evt=''):
		""" altualiza o comprimento das colunas """
		numHeaders = len(self.listColInfo)
		col_size = (self.GetSize().width / numHeaders)
		col_size-= (col_size*(0.5/numHeaders))

		for col_index in range(len(self.listColInfo)):
			if self.listColInfo[ col_index ] == _("Proxy"):
				self.listControl.SetColumnWidth(col_index, int(col_size*1.4))
			else:
				self.listControl.SetColumnWidth(col_index, col_size)

	def removaItemConexao(self, obj_id):
		"""remove o item associado ao id da conexao"""
		item_index = self.rowIndex[ obj_id ]
		del self.rowIndex[ obj_id ]

		del self.listSubProgressBar[ item_index ]
		self.listControl.DeleteItem( item_index )

		self.rowIndexCount -= 1

	def getRowIndex(self, obj_id):
		return self.rowIndex[ obj_id ]

	def removaTodosItens(self):
		self.listControl.DeleteAllItems()
		self.listSubProgressBar = []
		self.rowIndexCount = 0
		self.rowIndex = {}

	def GetListCtrl(self):
		return self.listControl

	def setInfoItem(self, obj_id, str_defauf=""):
		self.listControl.InsertStringItem(self.rowIndexCount, str_defauf)
		
		# SubProgressBarRenderer
		renderer = SubProgressBarRenderer( self)
		self.listSubProgressBar.append( renderer)
		self.listControl.SetItemCustomRenderer(self.rowIndexCount, 3, renderer)

		# associa o indice do item ao id da conexão
		self.rowIndex[ obj_id ] = self.rowIndexCount
		self.rowIndexCount += 1

########################################################################
if __name__ == "__main__":
	# muda para o diretório pai por depender dos recursos dele.
	os.chdir( pardir )
	
	# instala as traduções.
	manager.installTranslation() 
	
	app = wx.App(False)
	try:
		frame = wx.Frame(None, -1, "Fram", size = (800, 500))
		control = DetailControl( frame )
		for i in range(1, 6):
			control.setInfoItem(100*i, "Row id-"+str(100*i))
			
	except Exception, err:
		print err

	frame.Show()
	app.MainLoop()