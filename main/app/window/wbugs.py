# -*- coding: ISO-8859-1 -*-
import os
import wx
import sys
import math
import thread
import wx.lib.agw.genericmessagedialog as GMD

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necessário para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )

import bugs
from manager import installTranslation, PROGRAM_VERSION
########################################################################

class BugInfo( wx.MiniFrame ):
	""" Formulário de bugs """
	#----------------------------------------------------------------------
	def __init__(self, parent, title="Form"):
		"""Constructor"""
		wx.MiniFrame.__init__(self, parent, -1, title, style=wx.DEFAULT_FRAME_STYLE)
		self.SetBackgroundColour(wx.WHITE)
		self.sendingForm = False
		
		self.SetSize((640, 480))
		self.SetMinSize((640, 480))
		self.SetMaxSize((800, 600))
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		gridSizer = wx.GridSizer(cols=1)
		mainSizer.Add(gridSizer, 1, wx.EXPAND)
		# -----------------------------------------------------------
		
		box = wx.StaticBox(self, -1, _(u"Ação realizada"))
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		gridSizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 4)
		
		# *** ação executada antes do erro.
		self.controlAction = wx.TextCtrl(self, style=wx.TE_MULTILINE)
		helpText = _(u"Preencha com as ações realizadas, até ocorrer o erro.")
		self.controlAction.SetToolTip(wx.ToolTip( helpText ))
		bsizer.Add(self.controlAction, 1, wx.EXPAND)
		# -----------------------------------------------------------
		
		box = wx.StaticBox(self, -1, _("Erro ocorrido"))
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		gridSizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 4)	
		
		# *** erro apresentado.
		self.controlErro = wx.TextCtrl(self, style=wx.TE_MULTILINE)
		helpText = _("Informe o erro que ocorreu.")
		self.controlErro.SetToolTip(wx.ToolTip( helpText ))	
		bsizer.Add(self.controlErro, 1, wx.EXPAND)
		# -----------------------------------------------------------
		
		box = wx.StaticBox(self, -1, _(u"Sugestões de melhorias"))
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		gridSizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 4)
		
		# *** erro apresentado.
		self.controlSugestoes = wx.TextCtrl(self, style=wx.TE_MULTILINE)
		helpText = _(u"Você acha que o programa poderia ser melhor ?\nApresente sua idéia aqui.")
		self.controlSugestoes.SetToolTip(wx.ToolTip( helpText ))
		bsizer.Add(self.controlSugestoes, 1, wx.EXPAND)
		# -----------------------------------------------------------
		
		box = wx.StaticBox(self, -1, _("Mensagem pessoal"))
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		gridSizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 4)
		
		# *** erro apresentado.
		self.controlMensagem= wx.TextCtrl(self, style=wx.TE_MULTILINE)
		helpText = _(u"Tem algo a dizer ao desenvolvedor ?\nAqui é o local certo.")
		self.controlMensagem.SetToolTip(wx.ToolTip( helpText ))		
		bsizer.Add(self.controlMensagem, 1, wx.EXPAND)
		# -----------------------------------------------------------	
		box = wx.StaticBox(self, -1, _("Dados adicionais"))
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		gridSizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 4)
		
		# *** erro apresentado.
		self.controlExtra= wx.TextCtrl(self)
		helpText = _(u"Você pode informar um endereço de \nemail para receber uma resposta.")
		self.controlExtra.SetToolTip(wx.ToolTip( helpText ))		
		bsizer.Add(self.controlExtra, 1, wx.EXPAND)
		# -----------------------------------------------------------
		
		bsizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer.Add(bsizer, 0, wx.EXPAND)
		
		self.info = wx.StaticText(self, -1, "...")
		bsizer.Add(self.info, 0, wx.LEFT, 5)
		bsizer.AddStretchSpacer()
		
		self.btnSendEmail = wx.Button(self, -1, _("Enviar"))
		helpText = _(u"Envia o formulário para o email, pessoal, do desenvolvedor.")
		self.btnSendEmail.SetToolTip(wx.ToolTip( helpText ))
		self.btnSendEmail.Bind(wx.EVT_BUTTON, self.sendFormHandle)
		bsizer.Add(self.btnSendEmail)
		
		self.btnCancel = wx.Button(self, -1, _("Cancelar"))
		self.btnCancel.Bind(wx.EVT_BUTTON, self.OnCancel)
		bsizer.Add(self.btnCancel, 0, wx.RIGHT|wx.LEFT, 2)
		
		self.SetSizer(mainSizer)
		self.SetAutoLayout(True)
		mainSizer.Fit(self)
		
		self.CenterOnParent() # centralizado
		self.Show()
		
	def sendFormHandle(self, evt):
		if not self.sendingForm:
			thread.start_new(self.sendMailForm, tuple())
			self.sendingForm = True
			
	def sendMailForm(self, args=None):
		self.info.SetLabel(_("Enviando ..."))
		
		ibugs = bugs.Bugs(
		    program = PROGRAM_VERSION,
		    steps = self.controlAction.GetValue(),
		    error = self.controlErro.GetValue(),
		    suggestion = self.controlSugestoes.GetValue(),
		    message = self.controlMensagem.GetValue(),
		    extra = self.controlExtra.GetValue()
		)
		sucess, msgstr = ibugs.report()
		
		if sucess is True: # erro
			wx.CallAfter(self.showSafeMessageDialog,
				msgstr, _("Muito obrigado!"), style = wx.ICON_INFORMATION|wx.OK,
			    p_destroy = True
			)
		else: # erro enviando o form.
			self.info.SetLabel("...")
			
			wx.CallAfter(self.showSafeMessageDialog,
			    msgstr, _("Erro!"), style = wx.ICON_ERROR|wx.OK
			)
			self.sendingForm = False
		
	def showSafeMessageDialog(self, *args, **kwargs):
		p_destroy = kwargs.pop("p_destroy", False)
		
		dlg = GMD.GenericMessageDialog(self, *args, **kwargs)
		dlg.ShowModal(); dlg.Destroy()
		
		# fecha o formulário concluindo o trabalho
		if p_destroy: self.Destroy()
		
	def OnCancel(self, evt):
		self.Destroy()

########################################################################
if __name__ == "__main__":
	# muda para o diretório pai por depender dos recursos dele.
	os.chdir( pardir )
	
	# instala as traduções.
	installTranslation()
	
	def onClose(evt):
		obj = evt.GetEventObject()
		parent = obj.GetParent()
		parent.Destroy()
		obj.Destroy()
		
	app = wx.App(False)
	try:
		frame = wx.Frame(None, -1, "Frame", size = (800, 500))
		control = BugInfo(frame, "Formulário de erro")
		control.Bind(wx.EVT_CLOSE, onClose)
	except Exception, err:
		print err

	frame.Show()
	app.MainLoop()
	