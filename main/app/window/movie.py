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
########################################################################

class MovieManager(wx.MiniFrame):
	def __init__( self, mainWin, title, pos=wx.DefaultPosition, 
		          size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE ):

		wx.MiniFrame.__init__(self, mainWin, -1, title, pos, size, style)
		self.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.SetMinSize((450, 200))
		self.SetMaxSize((720, 300))

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
		self.controlMovies = wx.CheckListBox(self.painelControles, -1, wx.DefaultPosition)
		self.controlMovies.Bind( wx.EVT_LEFT_DCLICK, self.open_movie )
		# adiciona a lista de videos ao controle
		moviesNames = self.urlManager.getTitleList()
		self.controlMovies.AppendItems( moviesNames)

		# remover e sair
		self.removerSairId = 50
		self.botaoRemoverSair = wx.Button(self.painelControles, self.removerSairId, _("remover e sair"))
		self.botaoRemoverSair.Bind( wx.EVT_BUTTON, self.remove_movie)
		
		# remover
		self.removerId = 75; self.listaRemovidos = []
		self.botaoRemover = wx.Button(self.painelControles, self.removerId, _("remover"))
		self.botaoRemover.Bind( wx.EVT_BUTTON, self.remove_movie)

		# confirmar e sair
		self.botaoConfirmarSair = wx.Button(self.painelControles, -1, _("aplicar e sair"))
		self.botaoConfirmarSair.Bind( wx.EVT_BUTTON, self.remove_movielist)
		# inativo até o botão "botaoRemover" ser usado.
		self.botaoConfirmarSair.Enable(False)
		
		# cancela todas as operacoes
		self.botaoCancelar = wx.Button(self.painelControles, -1, _("cancelar"))
		self.botaoCancelar.Bind( wx.EVT_BUTTON, self.OnCancel )

		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

		# sizer
		hSizerButton = wx.BoxSizer( wx.HORIZONTAL)
		winSizer = wx.BoxSizer( wx.VERTICAL )#winsizer

		# sizer config
		winSizer.Add( self.painelControles, 1, wx.EXPAND)
		# painel sizer
		self.painelSizer.Add( self.controlMovies, 1, wx.EXPAND)
		self.painelSizer.Add( hSizerButton, 0, wx.EXPAND)

		hSizerButton.AddStretchSpacer()
		hSizerButton.Add(self.botaoRemoverSair, 0, wx.ALIGN_RIGHT)
		hSizerButton.Add(self.botaoRemover, 0, wx.ALIGN_RIGHT)
		hSizerButton.Add(self.botaoConfirmarSair, 0, wx.ALIGN_RIGHT)
		hSizerButton.Add(self.botaoCancelar, 0, wx.ALIGN_RIGHT)

		self.SetSizer( winSizer)
		self.SetAutoLayout(True)
		winSizer.Fit( self)
		self.Show(True)

	def __del__(self):
		del self.listaRemovidos
		del self.fileManager
		del self.urlManager
		del self.playerPath
		del self.mainWin
		
	def apply_changes(self, filename):
		self.fileManager.resumeInfo.remove( filename )
		self.urlManager.remove( filename )
	
	def remove_file(self, filename):
		""" remove o arquivo de vídeo do disco """
		filepath = ""
		try:
			filepath = self.fileManager.getFilePath(filename)
			os.remove(filepath)
		except os.error as err:
			print u"Erro removendo: %s" % (filepath or filename)
			print u"Causa: %s" % err
		finally:
			if filepath and not os.path.exists(filepath):
				self.apply_changes(filename)
				
	def remove_movie(self, evt):
		win_id = evt.GetId()
		showModalId = -1
		if self.controlMovies.GetChecked():
			if win_id == self.removerSairId:
				msg = _("Tem certeza que deseja remover\ntodos os videos marcados ?")
				dlg = GMD.GenericMessageDialog(self, msg,
				    _(u"Confirme a remoção."), wx.ICON_QUESTION|wx.YES_NO)
				showModalId = dlg.ShowModal(); dlg.Destroy()
				
			if showModalId == wx.ID_YES or win_id != self.removerSairId:
				while self.controlMovies.GetChecked():
					checked = self.controlMovies.GetChecked()
					
					# string do item removido
					filename = self.controlMovies.GetString(checked[0])
					self.controlMovies.Delete( checked[0] )
					
					if win_id == self.removerSairId:
						self.remove_file( filename )
						
					elif win_id == self.removerId:
						self.listaRemovidos.append( filename )
						self.botaoRemoverSair.Enable(False)
						
			# ativa quando a confirmação for necessária para a remoção
			self.botaoConfirmarSair.Enable( bool(self.listaRemovidos) )
			
		# finaliza fechando a janela
		if win_id == self.removerSairId:
			if showModalId == wx.ID_YES:
				self.Close(True)
				
	def remove_movielist(self, evt):
		""" remoção real dos arquivos removidos do controle """
		for filename in self.listaRemovidos:
			self.remove_file( filename )
		self.Close(True)
		
	def open_movie(self, evt):
		""" Abre o vídeo no player externo, quando um elemento for
		clicado duas vezes pelo usuário. Isso permite uma pré-visualização 
		do video antes que ele seja removido """
		if hasattr(self.mainWin, "configs"):
			self.playerPath = self.mainWin.cfg_locais["playerPath"]

		# o usário não escolheu um caminho para o player ainda.
		if hasattr(self.mainWin, "setPlayerPath") and not self.playerPath:
			self.playerPath = self.mainWin.setPlayerPath()

		if self.playerPath:
			filename = self.controlMovies.GetStringSelection()
			filepath = self.fileManager.getFilePath(filename)
			player = manager.FlvPlayer(self.playerPath, filepath = filepath)
			player.start()

	def OnCancel(self, event):
		self.Close(True)
	
	def OnCloseWindow(self, event):
		self.Destroy()
		
########################################################################
if __name__ == "__main__":
	# dir com os diretórios do projeto
	os.chdir( pardir )
	
	# instala as traduções.
	manager.installTranslation()
	
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

	