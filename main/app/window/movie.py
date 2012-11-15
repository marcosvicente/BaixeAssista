# -*- coding: ISO-8859-1 -*-
import os
import wx
import sys
try:
	from agw import genericmessagedialog as GMD
except ImportError: # if it's not there locally, try the wxPython lib.
	import wx.lib.agw.genericmessagedialog as GMD

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necessário para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )

import manager
import logging
import wx.dataview as dv

#----------------------------------------------------------------------
# This model class provides the data to the view when it is asked for.
# Since it is a list-only model (no hierachical data) then it is able
# to be referenced by row rather than by item object, so in this way
# it is easier to comprehend and use than other model types.  In this
# example we also provide a Compare function to assist with sorting of
# items in our model.  Notice that the data items in the data model
# object don't ever change position due to a sort or column
# reordering.  The view manages all of that and maps view rows and
# columns to the model's rows and columns as needed.
#
# For this example our data is stored in a simple list of lists.  In
# real life you can use whatever you want or need to hold your data.

class MovieModel(dv.PyDataViewIndexListModel):
	def __init__(self, data):
		dv.PyDataViewIndexListModel.__init__(self, len(data))
		self.colourCols = []
		self.data = data

	# All of our columns are strings.  If the model or the renderers
	# in the view are other types then that should be reflected here.
	def GetColumnType(self, col):
		return "string"

	# This method is called to provide the data object for a
	# particular row,col
	def GetValueByRow(self, row, col):
		return self.data[row][col]

	# This method is called when the user edits a data item in the view.
	def SetValueByRow(self, value, row, col):
		self.data[row][col] = value
	
	def GetColumnCount(self):
		""" Report how many columns this model provides data for. """
		return len(self.data[0])

	def GetCount(self):
		""" Report the number of rows in the model """
		#self.log.write('GetCount')
		return len(self.data)
	
	def setColourCol(self, col):
		self.colourCols.append(col)
		
	def GetAttrByRow(self, row, col, attr):
		""" Called to check if non-standard attributes should be used in the
		 cell at (row, col)
		"""
		##self.log.write('GetAttrByRow: (%d, %d)' % (row, col))
		if col in self.colourCols:
			attr.SetColour('blue')
			attr.SetBold(True)
			return True
		return False

	def Compare(self, item1, item2, col, ascending):
		"""
		 This is called to assist with sorting the data in the view.  The
		 first two args are instances of the DataViewItem class, so we
		 need to convert them to row numbers with the GetRow method.
		 Then it's just a matter of fetching the right values from our
		 data set and comparing them.  The return value is -1, 0, or 1,
		 just like Python's cmp() function.
		"""
		if not ascending: # swap sort order?
			item2, item1 = item1, item2
		row1 = self.GetRow(item1)
		row2 = self.GetRow(item2)
		if col == 0:
			return cmp(int(self.data[row1][col]), int(self.data[row2][col]))
		else:
			return cmp(self.data[row1][col], self.data[row2][col])

	def DeleteRows(self, rows):
		# make a copy since we'll be sorting(mutating) the list
		rows = list(rows)
		# use reverse order so the indexes don't change as we remove items
		rows.sort(reverse=True)

		for row in rows:
			# remove it from our data structure
			del self.data[row]
			# notify the view(s) using this model that it has been removed
			self.RowDeleted(row)

	def AddRow(self, value):
		# update data structure
		self.data.append(value)
		# notify views
		self.RowAppended()
		
#----------------------------------------------------------------------
class MovieView(wx.Panel):
	def __init__(self, parent, model=None, data=None):
		wx.Panel.__init__(self, parent, -1)

		# Create a dataview control
		self.dvc = dv.DataViewCtrl(self,
								   style=wx.BORDER_THEME
								   | dv.DV_ROW_LINES # nice alternating bg colors
								   #| dv.DV_HORIZ_RULES
								   | dv.DV_VERT_RULES
								   | dv.DV_MULTIPLE
								   )

		# Create an instance of our simple model...
		if model is None:
			self.model = MovieModel(data)
		else:
			self.model = model

		# ...and associate it with the dataview control.  Models can
		# be shared between multiple DataViewCtrls, so this does not
		# assign ownership like many things in wx do.  There is some
		# internal reference counting happening so you don't really
		# need to hold a reference to it either, but we do for this
		# example so we can fiddle with the model from the widget
		# inspector or whatever.
		self.dvc.AssociateModel(self.model)

		# Now we create some columns.  The second parameter is the
		# column number within the model that the DataViewColumn will
		# fetch the data from.  This means that you can have views
		# using the same model that show different columns of data, or
		# that they can be in a different order than in the model.
		column_id = 0
		colID = self.dvc.AppendTextColumn(_(u"ID"),  column_id, width=50)
		colID.Renderer.Alignment = wx.ALIGN_RIGHT
		
		column_id += 1
		self.dvc.AppendTextColumn(_(u"Título"),  column_id, width=350, mode=dv.DATAVIEW_CELL_EDITABLE)
		
	 	column_id += 1
		colExt = self.dvc.AppendTextColumn(_(u"Ext"),  column_id, width=100)
		colExt.Renderer.Alignment = wx.ALIGN_RIGHT
		
		column_id += 1
		colQuality = self.dvc.AppendTextColumn(_(u"Qualidade"), column_id, width=100)
		colQuality.Renderer.Alignment = wx.ALIGN_RIGHT
		
		column_id += 1
		self.dvc.AppendTextColumn(_(u"Tamanho"), column_id, width=100)
		self.model.setColourCol( column_id )
		
		column_id += 1
		self.dvc.AppendTextColumn(_(u"Baixado"), column_id, width=100)
		self.model.setColourCol( column_id )
		
		column_id += 1
		self.dvc.AppendTextColumn(_(u"Estado"), column_id, width=150)
		self.model.setColourCol( column_id )
		
		# Through the magic of Python we can also access the columns
		# as a list via the Columns property.  Here we'll mark them
		# all as sortable and reorderable.
		for c in self.dvc.Columns:
			c.Sortable = True
			c.Reorderable = True
			
		# set the Sizer property (same as SetSizer)
		self.Sizer = wx.BoxSizer(wx.VERTICAL) 
		self.Sizer.Add(self.dvc, 1, wx.EXPAND)
		
#----------------------------------------------------------------------
class MovieManager(wx.MiniFrame):
	logger = logging.getLogger("main.app.window.movie")

	def __init__(self, mainWin, title, pos=wx.DefaultPosition, 
				 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE ):
		
		wx.MiniFrame.__init__(self, mainWin, -1, title, pos, size, style)
		self.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.SetMinSize((640, 350))
		
		# ponteiro para a janela principal
		self.mainWin = mainWin
		self.fileManager = None
		self.urlManager = None

		# caminho padrão para desenvolvimento.
		self.playerPath = "C:\Program Files (x86)\FLV Player\FLVPlayer.exe"

		if hasattr(mainWin, "manage"):
			# quando manage for iniciado, seu atributo "fileManager" será usado.
			self.fileManager = getattr(mainWin.manage, "fileManager", None)
			self.urlManager = getattr(mainWin.manage, "urlManager", None)

		# se o objeto "fileManager" não existir, isso será um indicador de que
		# não existe um download sendo feito no momento em que ele for necessário.
		if self.fileManager is None: self.fileManager = manager.FileManager()
		if self.urlManager is None: self.urlManager = manager.UrlManager()
		
		if hasattr(mainWin, "configs"):
			locais = mainWin.configs["Locais"]
			self.playerPath = locais["playerPath"]

		self.painelControles = wx.Panel( self)
		self.painelSizer = wx.BoxSizer( wx.VERTICAL )
		self.painelControles.SetSizer( self.painelSizer)

		# controlador de videos -------------------------------------------
		data = []
		self.titleColID = 1
		condition = {True: _("completo"), False: _("incompleto")}
		for query in manager.ResumeInfo().objects.all():
			data.append([query.pk, 
						 query.title, query.videoExt, query.videoQuality, 
						 manager.StreamManager.format_bytes(query.videoSize),
						 manager.StreamManager.format_bytes(query.cacheBytesCount),
						 condition[query.isCompleteDown]
						])
		self.movieView = MovieView(self.painelControles, data = data)
		
		# Bind some events so we can see what the DVC sends us
		self.movieView.dvc.Bind(dv.EVT_DATAVIEW_ITEM_EDITING_DONE, self.OnEditingDone)
		self.movieView.dvc.Bind(dv.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self.OnValueChanged)
		
		##################################################################################
		# remover e sair
		self.btnOpenFileID = 25
		self.btnOpenFile = wx.Button(self.painelControles, self.btnOpenFileID, _("Visualizar"))
		self.btnOpenFile.Bind(wx.EVT_BUTTON, self.fileOpen)
		
		# remover e sair
		self.btnDeleteExitID = 50
		self.btnDeleteExit = wx.Button(self.painelControles, self.btnDeleteExitID, _("remover e sair"))
		self.btnDeleteExit.Bind( wx.EVT_BUTTON, self.OnDeleteRows)
		
		# remover
		self.btnDeleteID = 75; self.deleteListName = []
		self.btnDelete = wx.Button(self.painelControles, self.btnDeleteID, _("remover"))
		self.btnDelete.Bind( wx.EVT_BUTTON, self.OnDeleteRows)
		
		# confirmar e sair
		self.btnConfirmExit = wx.Button(self.painelControles, -1, _("aplicar e sair"))
		self.btnConfirmExit.Bind( wx.EVT_BUTTON, self.deleteFileNameList)
		# inativo até o botão "btnDelete" ser usado.
		self.btnConfirmExit.Enable(False)
		
		# cancela todas as operacoes
		self.btnCancel = wx.Button(self.painelControles, -1, _("cancelar"))
		self.btnCancel.Bind(wx.EVT_BUTTON, self.OnCancel )
		
		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

		# sizer
		hSizerButton = wx.BoxSizer(wx.HORIZONTAL)
		hSizerButton.AddStretchSpacer()
		hSizerButton.Add(self.btnOpenFile, 0, wx.ALIGN_RIGHT)
		hSizerButton.Add(self.btnDeleteExit, 0, wx.ALIGN_RIGHT)
		hSizerButton.Add(self.btnDelete, 0, wx.ALIGN_RIGHT)
		hSizerButton.Add(self.btnConfirmExit, 0, wx.ALIGN_RIGHT)
		hSizerButton.Add(self.btnCancel, 0, wx.ALIGN_RIGHT)
		
		winSizer = wx.BoxSizer(wx.VERTICAL)
		winSizer.Add(self.painelControles, 1, wx.EXPAND)
		
		# painel sizer
		self.painelSizer.Add(self.movieView, 1, wx.EXPAND)
		self.painelSizer.Add(hSizerButton, 0, wx.EXPAND)
		
		self.SetSizer( winSizer)
		self.SetAutoLayout(True)
		winSizer.Fit( self)
		self.Show(True)

	def __del__(self):
		del self.deleteListName
		del self.fileManager
		del self.urlManager
		del self.playerPath
		del self.mainWin
	
	def OnDeleteRows(self, evt):
		""" Remove the selected row(s) from the model. The model will take care
		of notifying the view (and any other observers) that the change has
		happened.
		"""
		items = self.movieView.dvc.GetSelections()
		rows = [self.movieView.model.GetRow(item) for item in items]
		print "items index: %s"%rows
		
		objEventID = evt.GetId()
		objModalID = -1
		
		if len(items):
			if objEventID == self.btnDeleteExitID:
				dlg = GMD.GenericMessageDialog(self, 
						_("Tem certeza que deseja remover\ntodos os videos marcados ?"),
						_(u"Confirme a remoção."), wx.ICON_QUESTION|wx.YES_NO)
				objModalID = dlg.ShowModal()
				dlg.Destroy()
				
			if objModalID == wx.ID_YES or objEventID != self.btnDeleteExitID:
				for row in rows:
					filename = self.movieView.model.GetValueByRow(row, self.titleColID)
					
					if objEventID == self.btnDeleteExitID:
						self.deleteFileName( filename )
						
					elif objEventID == self.btnDeleteID:
						self.deleteListName.append( filename )
						self.btnDeleteExit.Enable(False)
						
				# deletando o items visuais
				self.movieView.model.DeleteRows(rows)
				
			# ativa quando a confirmação for necessária para a remoção
			self.btnConfirmExit.Enable( bool(self.deleteListName) )
			
		# finaliza fechando a janela
		if objEventID == self.btnDeleteExitID:
			if objModalID == wx.ID_YES:
				self.Close(True)
		
	def OnEditingDone(self, evt):
		print "OnEditingDone\n"

	def OnValueChanged(self, evt):
		print "OnValueChanged\n"
		
	def saveDataBase(self, filename):
		self.fileManager.resumeInfo.remove( filename )
		self.urlManager.remove( filename )
		
	def deleteFileName(self, filename):
		""" remove o arquivo de vídeo do disco """
		filepath = ""
		
		try: filepath = self.fileManager.getFilePath(filename)
		except Exception as err:
			self.logger.error("getFilePath: %s"%err)
			
		try: os.remove(filepath)
		except os.error as err:
			self.logger.error(u"Erro removendo: %s" %(filepath or filename))
			self.logger.error(str(err))
		finally:
			if filepath and not os.path.exists(filepath):
				self.saveDataBase(filename)
				
	def deleteFileNameList(self, evt):
		""" remoção real dos arquivos removidos do controle """
		for filename in self.deleteListName:
			self.deleteFileName( filename )
		self.Close(True)

	def fileOpen(self, evt):
		""" Abre o vídeo no player externo, quando um elemento for
		clicado duas vezes pelo usuário. Isso permite uma pré-visualização 
		do video antes que ele seja removido """
		if hasattr(self.mainWin, "configs"):
			self.playerPath = self.mainWin.cfg_locais["playerPath"]
			
		# o usário não escolheu um caminho para o player ainda.
		if hasattr(self.mainWin, "setPlayerPath") and not self.playerPath:
			self.playerPath = self.mainWin.setPlayerPath()
			
		if self.playerPath:
			items = self.movieView.dvc.GetSelections()
			for row in [self.movieView.model.GetRow(item) for item in items]:
				filename = self.movieView.model.GetValueByRow(row, self.titleColID)
				filepath = self.fileManager.getFilePath( filename )
				flvplayer = manager.FlvPlayer(self.playerPath, filepath = filepath)
				flvplayer.start()
				
	def OnCancel(self, event):
		self.Close(True)

	def OnCloseWindow(self, event):
		self.Destroy()

########################################################################
if __name__ == "__main__":
	# dir com os diretórios do projeto
	os.chdir( pardir )

	from main.app.util import base
	base.trans_install() # instala as traduções.

	def onClose(evt):
		obj = evt.GetEventObject()
		parent = obj.GetParent()
		parent.Destroy()
		obj.Destroy()

	try:
		app = wx.App(False)
		frame = wx.Frame(None, -1, "Fram", size = (800, 500))
		frame.Show()

		control = MovieManager(frame, "MovieControl")
		control.Bind(wx.EVT_CLOSE, onClose)

		app.MainLoop()
	except Exception, err:
		print err
