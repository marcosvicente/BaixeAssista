# -*- coding: ISO-8859-1 -*-

import os
import wx
import sys
from main import settings

curdir = os.path.dirname(os.path.abspath(__file__))
pardir = os.path.split( curdir )[0]

# necessário para o importe de manager
if not pardir in sys.path: sys.path.append( pardir )
if not curdir in sys.path: sys.path.append( curdir )
########################################################################

IMAGES_TYPES = {
    "jpg": wx.BITMAP_TYPE_JPEG,
    "png": wx.BITMAP_TYPE_PNG
}
def createBitmap(imgpath, scalex, scaley):
    imgType = os.path.split(imgpath)[-1].rsplit(".",1)[-1] # tipo de arquivo
    image = wx.Image(imgpath, IMAGES_TYPES[ imgType.lower() ])
    image.Rescale(scalex, scaley)
    return image.ConvertToBitmap()

class PageButton( wx.Panel ):
    """ cria botões com imagens e atribui um painel para ele.
    selemelhante ao controle notebook nativo, ao clicar em um dos botões, o paneil
    associado à ele será mostrado. """
    panels = {}

    #----------------------------------------------------------------------
    def __init__(self, parent, imgPath, pageStr="", pageTootip="", scalex=32, scaley=32, widget=False):
        """Constructor"""
        wx.Panel.__init__(self, parent, -1)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer( mainSizer )
        self.SetAutoLayout(True)
        # -----------------------------------------------

        # cria o botão ativador da página
        bitmap = createBitmap(imgPath, scalex=scalex, scaley=scaley)
        self.pageButton = wx.BitmapButton(self, -1, bitmap)
        
        self.pageButton.SetToolTipString( pageTootip )
        buttonSizeX = scalex+35; buttonSizeY = scaley+10
        self.pageButton.SetMinSize((buttonSizeX, buttonSizeY))
        self.pageButton.SetMaxSize((buttonSizeX, buttonSizeY))
        
        mainSizer.Add(self.pageButton, 0, wx.ALIGN_CENTER)
        
        if pageStr: # texto abaixo do botão
            mainSizer.Add(wx.StaticText(self, -1, pageStr), 0, wx.ALIGN_CENTER)
            
        if not widget: # widget são botões sem painel
            self.pageButton.Bind(wx.EVT_BUTTON, self.showPage)

            # cada botão de página está associado a um painel.
            # cada painel tem como "parent" o main frame(janela principal)
            mainParent = self.GetParent().GetParent()
            mainParentSizer = mainParent.GetSizer()
            
            btnPanelPage = wx.Panel(mainParent, -1)
            btnPanelPage.SetBackgroundColour(wx.WHITE)
            PageButton.panels[ self ] = btnPanelPage
            
            # o primeiro painel sempre será mostrado
            if len(PageButton.panels) != 1: btnPanelPage.Hide()

            btnPanelPage.SetSizer( wx.BoxSizer(wx.VERTICAL) )
            btnPanelPage.SetAutoLayout(True)
            mainParentSizer.Add(btnPanelPage, 1, wx.EXPAND)

    def hidePages(self, _except):
        """ oculta todas as páginas, exceto a que deve ser mostrada """
        for panel in self.panels.values():
            if _except != panel: panel.Hide()
            
    def BIND_CALLBACK(self, callback):
        """ liga o  'callback' ao click do botão real """
        self.pageButton.Bind(wx.EVT_RIGHT_DOWN, callback)
    
    def showPage(self, evt):
        """ mostra o painel da página clicada """
        # objeto botão da página clicado
        win = evt.GetEventObject()

        # painel da página clicado
        panel = PageButton.panels[ self ]

        # oculta as páginas anteriormente mostradas
        self.hidePages( panel )

        panel.Show(); panel.Refresh()
        parent = panel.GetParent()
        parent.Layout()

    def getPanel(self):
        return PageButton.panels[ self ]

########################################################################
class PageBar( wx.Panel ):
    """ organiza os botões de página alinhados na horizontal """
    #----------------------------------------------------------------------
    def __init__(self, parent, function):
        """Constructor"""
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER_THEME)
        self.parent = parent
        self.function = function

        self.Bind(wx.EVT_CHAR_HOOK, self.shortCutHandle)
        self.Bind(wx.EVT_LEFT_DOWN, self.setFocusBar)

        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer( self.mainSizer)
        self.SetAutoLayout(True)

        # controla o layout dos botões de página.
        self.mainGridSizer = wx.FlexGridSizer(rows=1, hgap=5)
        self.mainSizer.Add(self.mainGridSizer, 0, wx.EXPAND)

        self.widgets = {
            "FullScreen": {"CreationHandle": self.createFullScreenWidget}
        }
        # -------------------------------------------------------------
        self.painelExpandir = wx.Panel(self, -1)
        self.painelExpandir.SetToolTip(wx.ToolTip( _("clique para expandir.") ))
        self.painelExpandir.SetMinSize((-1, 8))
        self.painelExpandir.SetBackgroundColour(wx.WHITE)
        self.painelExpandir.Bind(wx.EVT_ENTER_WINDOW, self.panelHadleIn)
        self.painelExpandir.Bind(wx.EVT_LEAVE_WINDOW, self.panelHadleOut)
        self.painelExpandir.Bind(wx.EVT_LEFT_DOWN, self.expadirHandle)
        self.mainSizer.Add(self.painelExpandir, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 1)
        self.painelExpandir.Hide()
        #####################

        self.btnBoxSizer = wx.BoxSizer()
        self.btnBoxSizer.AddStretchSpacer()

        path = os.path.join(settings.IMAGES_DIR, "navigate-up24x24.png")
        image = wx.Image(path, wx.BITMAP_TYPE_PNG)
        self.setaCima = image.ConvertToBitmap()

        ##path = os.path.join(settings.IMAGES_DIR,"seta_baixo.jpg")
        ##image = wx.Image(path, wx.BITMAP_TYPE_JPEG)
        ##self.setaBaixo = image.ConvertToBitmap()

        self.btnHideBar = wx.BitmapButton(self, -1, self.setaCima)
        self.btnHideBar.SetToolTipString( _("Click para ocultar[Atalho: seta cima/baixo]") )
        # o primeiro evento será botão pressionado
        self.btnHideBar.is_pressed = True 
        self.btnHideBar.SetBitmap( self.setaCima )
        self.btnHideBar.SetMinSize((24,24))

        self.btnBoxSizer.Add(self.btnHideBar, 0, wx.ALIGN_BOTTOM|wx.BOTTOM|wx.RIGHT, 1)
        self.Bind(wx.EVT_BUTTON, self.btnHideBarHandle, self.btnHideBar)
        # sizer do botão expadido com espaço à esquerda.
        self.mainSizer.Add(self.btnBoxSizer, 1, wx.EXPAND)
        
    def hasWidgetType(self, widgetType):
        """ indica se o type de widget é um tipo válido """
        return self.widgets.has_key( widgetType )
        
    def setFocusBar(self, evt):
        self.SetFocus()

    def shortCutHandle(self, evt):
        """ implementa o atalho para o botão hide """
        keycode = evt.GetKeyCode()
        if (keycode == wx.WXK_UP and self.btnHideBar.is_pressed) or \
           (keycode == wx.WXK_DOWN and not self.btnHideBar.is_pressed):
            self.btnHideBarHandle(evt)

        if keycode == wx.WXK_ESCAPE: # permite a chama para esc
            evt.Skip()

    def btnHideBarHandle(self, evt):
        """ impleta a ação do botão ocultar páginas """
        win = self.btnHideBar ##evt.GetEventObject()
        # -------------------------------------------------------
        if win.is_pressed:
            for sizerItem in self.mainGridSizer.GetChildren():
                hSizer = sizerItem.GetSizer()
                for index, item in enumerate(hSizer.GetChildren()):
                    item.GetWindow().Hide()
                    if index == 1: break
                    
            ## win.SetBitmap( self.setaBaixo )
            self.btnBoxSizer.Hide(0)
            self.btnBoxSizer.Hide(1)
            self.painelExpandir.Show()
        # -------------------------------------------------------    
        elif not win.is_pressed:
            for sizerItem in self.mainGridSizer.GetChildren():
                hSizer = sizerItem.GetSizer()
                for index, item in enumerate(hSizer.GetChildren()):
                    item.GetWindow().Show()
                    if index == 1: break
                    
            win.SetBitmap( self.setaCima )
            self.btnBoxSizer.Show(0)
            self.btnBoxSizer.Show(1)
            self.painelExpandir.Hide()
        # -------------------------------------------------------
        # função chamada sempre que a barra sofrer mudança
        self.function( win.is_pressed )

        # permuta o estado do botão
        win.is_pressed = not win.is_pressed
        self.parent.Layout()
        self.parent.Refresh()
        # -------------------------------------------------------
        
    def expadirHandle(self, evt):
        """ expade a barra de controle ao clicar na linha de retorno """
        if not self.btnHideBar.is_pressed:
            evt.SetEventObject( self.btnHideBar )
            self.btnHideBarHandle( evt )

    def addPageButton(self, pageButton):
        """ adiciona o botão página para a barra de páginas """
        hsize = wx.BoxSizer(wx.HORIZONTAL)
        
        sline = wx.StaticLine(self, style=wx.LI_VERTICAL)
        hsize.Add(sline, 0, wx.EXPAND)
        hsize.Add(pageButton, 0, wx.EXPAND|wx.LEFT, 4)
        
        self.mainGridSizer.Add(hsize, 0, wx.EXPAND|wx.LEFT, 2)
        self.Layout()

    def panelHadleIn(self, evt):
        """ destaca a linha de retorno na entrada do mouse """
        win = evt.GetEventObject()
        win.SetBackgroundColour(wx.BLACK)
        win.Refresh() # desenha a cor

    def panelHadleOut(self, evt):
        """ destaca a linha de retorno na saída do mouse """
        win = evt.GetEventObject()
        win.SetBackgroundColour(wx.WHITE)
        win.Refresh() # desenha a cor

    def setFullScreen(self, event, mainWin):
        assert self.widgets["FullScreen"].has_key("btnWidget"), "Widget button don`t was created!"
        
        # janela principal(do mais alto nível)
        isFullScreen = not mainWin.IsFullScreen()
        mainWin.ShowFullScreen( isFullScreen )
        
        btnWidget = self.widgets["FullScreen"]["btnWidget"]
        
        if not isFullScreen:
            btnWidget.pageButton.SetBitmap(
                createBitmap(btnWidget.imgCollapse, btnWidget.scalex, btnWidget.scaley)
            )
        else:
            btnWidget.pageButton.SetBitmap(
                createBitmap(btnWidget.imgExpad, btnWidget.scalex, btnWidget.scaley)
            )
        
    def createFullScreenWidget(self, mainWin, pageTootip="", scalex=32, scaley=32):
        imgCollapse = os.path.join(settings.IMAGES_DIR, "fullscreen-in.jpg")
        imgExpad = os.path.join(settings.IMAGES_DIR, "fullscreen-out.jpg")
        
        btnFullScreen = PageButton(self, imgCollapse, "", pageTootip, scalex, scaley, widget=True)
        self.widgets["FullScreen"]["btnWidget"] = btnFullScreen
        
        btnFullScreen.scalex = scalex
        btnFullScreen.scaley = scaley
        btnFullScreen.imgCollapse = imgCollapse
        btnFullScreen.imgExpad = imgExpad
        
        btnFullScreen.Bind(wx.EVT_BUTTON, lambda evt, mainWin = mainWin: self.setFullScreen(evt, mainWin))
        self.addPageButton( btnFullScreen ) # adiciona a grade horizontal
        
########################################################################		
class NoteBookImage( wx.Panel ):
    """ simula o controle wx.NotBook """
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent, -1)
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetBackgroundColour(wx.Colour(240, 240, 240))

        # barra das páginas
        self.pageBar = PageBar(self, self.OnHide)
        self.mainSizer.Add(self.pageBar, 0, wx.EXPAND|wx.LEFT|wx.DOWN)

        self.SetSizer( self.mainSizer )
        self.SetAutoLayout(True)
        
    def setWidget(self, mainWin, widgetType, helpText="", scalex=32, scaley=32):
        assert self.pageBar.hasWidgetType( widgetType ), "widget type \"%s\" not exist!"%widgetType
        self.pageBar.widgets[ widgetType ]["CreationHandle"](mainWin, helpText, scalex, scaley)
        
    def setFullScreen(self, evt, mainWin):
        self.pageBar.setFullScreen(evt, mainWin)
        
    def OnHide(self, isHidden):
        """ Pode ser anulada, com o objetivo de 
        fazer algo quando a barra de páginas for oculta """
        pass

    def createPage(self, imgPath, pageStr="", pageTootip="", scalex=32, scaley=32, callback=None):
        """ A página é formada por um conjunto de controles.
        A base prinicipal é um painel. Em seu layout estão o BitmapButton e um
        StaticText. Assim a idéia é criar um botão só, formado de  painel+botão+rótulo de texto.
        Cada botão de página mostra seu painel quando clicado pelo usuário.
        """
        btnPage = PageButton(self.pageBar, imgPath, pageStr, pageTootip, scalex, scaley)
        if callable( callback ): btnPage.BIND_CALLBACK( callback )
        self.pageBar.addPageButton( btnPage )
        return btnPage.getPanel()
        
    def addPage(self, page, win):
        page.GetSizer().Add(win, 1, wx.EXPAND)
        page.GetSizer().Layout()
        
## ------------------------------------------------------------------------
if __name__ == "__main__":
    # dir com os diretórios do projeto
    os.chdir( pardir )
    
    from manager import installTranslation
    
    # instala as traduções.
    installTranslation()
    
    app = wx.App(False)
    
    try:
        frame = wx.Frame(None, -1, "Fram", size = (800, 500))
        control = NoteBookImage( frame )

        imgpath = os.path.join(settings.IMAGES_DIR, "fullscreen-in.jpg")

        for i in range(7):
            master = control.addPage(imgpath, "Page-%d"%i, "ButtonPage-%d"%i)
            wx.StaticText(master, -1, "Painel Página- %s"%i)

        control.setWidget(frame, "FullScreen", _("Tela cheia"))
    except Exception, err:
        print err

    frame.Show()
    app.MainLoop()