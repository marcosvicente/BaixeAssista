from PySide import QtCore, QtGui, QtWebKit

from swfplayer import JWPlayer, FlowPlayer
from uiPlayerDialog import Ui_playerDialog

from main.app.util import base

## --------------------------------------------------------------------------
class PlayerDialog(QtGui.QDialog):
    def __init__(self, title="SWF Player", parent=None):
        super(PlayerDialog, self).__init__(parent)
        self.uiPlayerDialog = Ui_playerDialog()
        self.uiPlayerDialog.setupUi(self)
        
        self.setWindowTitle( title )
        
        self.mFlowPlayer = FlowPlayer.Player( self.playerFrame )
        self.mJWPlayer = JWPlayer.Player( self.playerFrame )
        
        self.mFlowPlayer.hide()
        self.mJWPlayer.hide()
        
        self.btnFlowPlayer.clicked.connect( self.changePlayer )
        self.btnJwPlayer.clicked.connect( self.changePlayer )
        
        self.btnFlowPlayer.setToolTip(self.tr("load FlowPlayer"))
        self.btnJwPlayer.setToolTip(self.tr("load JW Player"))
        
        self.loadFlowPlayer()
    
    def start(self):
        self.show()
        
    def stop(self):
        self.mplayer.stop()
        self.close()
        
    def reload(self, autostart=False):
        self.playerReload(autostart)
        
    @property
    def player(self):
        return self.mplayer
    @property
    def playerFrame(self):
        return self.uiPlayerDialog.playerFrame
    @property
    def btnReload(self):
        return self.uiPlayerDialog.btnReload
    @property
    def btnFlowPlayer(self):
        return self.uiPlayerDialog.btnFlowPlayer
    @property
    def btnJwPlayer(self):
        return self.uiPlayerDialog.btnJwPlayer
    
    def playerReload(self, autostart=False):
        self.mplayer["autostart"] = autostart
        self.mplayer.reload()
        
    @base.protected()
    def removePlayer(self, layout):
        layout.removeWidget(self.mplayer)
        self.mplayer.hide()
        self.playerReload(False)
        
    def loadFlowPlayer(self):
        layout = self.playerFrame.layout()
        self.removePlayer( layout )
        
        self.mplayer = self.mFlowPlayer
        
        layout.addWidget( self.mFlowPlayer )
        self.playerReload(True)
        self.mFlowPlayer.show()
        
    def loadJwPlayer(self):
        layout = self.playerFrame.layout()
        self.removePlayer( layout )
        
        self.mplayer = self.mJWPlayer
        
        layout.addWidget( self.mJWPlayer )
        self.playerReload(True)
        self.mJWPlayer.show()
        
    def changePlayer(self):
        if self.sender() == self.btnFlowPlayer:
            if self.btnFlowPlayer.isChecked():
                self.loadFlowPlayer()
                self.btnJwPlayer.setChecked(False)
            else:
                self.btnJwPlayer.setChecked(True)
                self.loadJwPlayer()
                
        elif self.sender() == self.btnJwPlayer:
            if self.btnJwPlayer.isChecked():
                self.loadJwPlayer()
                self.btnFlowPlayer.setChecked(False)
            else:
                self.btnFlowPlayer.setChecked(True)
                self.loadFlowPlayer()
                
                
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    
    p = PlayerDialog()
    p.show()
    
    sys.exit(app.exec_())
    
    
    