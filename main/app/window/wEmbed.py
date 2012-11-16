import wx

class wEmbedPlayer( wx.MiniFrame):
    def __init__(self, mainWin, title="", pos=wx.DefaultPosition, 
                  size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE ):
        wx.MiniFrame.__init__(self, mainWin, -1, title, pos, size, style)
        self.SetMinSize((800, 500))
        
        self.mainSizer = wx.BoxSizer()
        self.SetSizer( self.mainSizer )
        self.SetAutoLayout(True)
        
        self.Show(True)
        
    def attach(self, win):
        self.mainSizer.Add(win, 1, wx.EXPAND)
        self.Layout()
        
    def dettach(self, win):
        self.mainSizer.Remove(win)