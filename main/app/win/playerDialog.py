# coding: utf-8
from PySide import QtCore, QtGui, QtWebKit

from swfplayer import JWPlayer, FlowPlayer
from uiPlayerDialog import Ui_playerDialog

from main.app.util import base

## --------------------------------------------------------------------------
class PlayerDialog(QtGui.QDialog):
    def __init__(self, title="SWF Player", parent=None, configs={}):
        super(PlayerDialog, self).__init__(parent)
        self.uiPlayerDialog = Ui_playerDialog()
        self.uiPlayerDialog.setupUi(self)
        
        # instância para as configurações global
        self.configs = configs
        self.setWindowTitle( title )
        
        self.mFlowPlayer = FlowPlayer.Player( self.playerFrame )
        self.mJWPlayer = JWPlayer.Player( self.playerFrame )
        
        self.mFlowPlayer.hide()
        self.mJWPlayer.hide()
        
        self.btnFlowPlayer.clicked.connect( self.changePlayer )
        self.btnJwPlayer.clicked.connect( self.changePlayer )
        
        self.btnFlowPlayer.setToolTip(self.tr("load FlowPlayer"))
        self.btnJwPlayer.setToolTip(self.tr("load JW Player"))
        
        # inicializa o player da configuração
        self._startDefaultPlayer()
        
    def start(self, **kwargs):
        self.mplayer.update(**kwargs)
        self.mplayer.reload()
        self.show()
        
    def stop(self):
        self.mplayer.stop()
        self.hide()
        
    def reload(self, **kwargs):
        """ recarrega o player, mas antes atualiza seus parâmetros """
        self.mplayer.update(**kwargs)
        self.mplayer.reload()
        
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
    
    @property
    def btnSkins(self):
        return self.uiPlayerDialog.btnSkins
    
    def _startDefaultPlayer(self):
        self.setDefaultConf()
        
        size = map(lambda v: int, self.configs["embedPlayer"]["size"])
        pos  = map(lambda v: int, self.configs["embedPlayer"]["pos"])
        
        if len(size) > 0: self.resize(*size)
        if len( pos) > 0: self.move(*pos)
        
        flowplayer = self.mFlowPlayer.__class__.__module__
        jwplayer = self.mJWPlayer.__class__.__module__
        
        if flowplayer.endswith(self.configs["embedPlayer"]["player"]):
            self.mplayer = self.mFlowPlayer
            self.mplayer["skinName"] = self.configs[flowplayer]["skinName"]
            
        elif jwplayer.endswith(self.configs["embedPlayer"]["player"]):
            self.mplayer = self.mJWPlayer
            self.mplayer["skinName"] = self.configs[jwplayer]["skinName"]
            
        layout = self.playerFrame.layout()
        layout.addWidget(self.mplayer)
        
        self.btnSkins.setMenu(self.setupSkinMenu())
        
        self.mplayer.show()

    def setDefaultConf(self):
        self.configs.setdefault("embedPlayer", {})
        
        flowplayer = self.mFlowPlayer.__class__.__module__
        jwplayer = self.mJWPlayer.__class__.__module__
        
        self.configs.setdefault(flowplayer, {})
        self.configs.setdefault(jwplayer, {})
        
        self.configs["embedPlayer"].setdefault("size", tuple())
        self.configs["embedPlayer"].setdefault("pos", tuple())
        self.configs["embedPlayer"].setdefault("player", flowplayer)
        
        self.configs[flowplayer].setdefault("skinName", self.mFlowPlayer.defaultskin)
        self.configs[jwplayer].setdefault("skinName", self.mJWPlayer.defaultskin)
        
    def saveSettings(self):
        mplayer = self.mplayer.__class__.__module__
        flowplayer = self.mFlowPlayer.__class__.__module__
        jwplayer = self.mJWPlayer.__class__.__module__
        
        self.configs["embedPlayer"]["size"] = self.size()
        self.configs["embedPlayer"]["pos"]  = self.pos()
        self.configs["embedPlayer"]["player"] = mplayer
        
        self.configs[flowplayer]["skinName"] = self.mFlowPlayer["skinName"]
        self.configs[jwplayer]["skinName"] = self.mJWPlayer["skinName"]
        
    def setupSkinMenu(self):
        menu = QtGui.QMenu(self)
        actionSkinGroup = QtGui.QActionGroup(self)
        actionSkinGroup.triggered.connect( self.onSkinChange )
        
        for skinName in self.mplayer.getSkinsNames():
            actionSkin = QtGui.QAction(skinName, self)
            actionSkin.setCheckable(True)
            
            if skinName == self.mplayer["skinName"]:
                actionSkin.setChecked(True)
                
            actionSkinGroup.addAction( actionSkin )
            menu.addAction( actionSkin )
        return menu
    
    def onSkinChange(self):
        """ altera a skin mostrada no player """
        actionGroup = self.sender()
        action = actionGroup.checkedAction()
        self.mplayer["skinName"] = action.text()
        self.mplayer.reload()
        
    @base.protected()
    def removePlayer(self, layout):
        params = dict(autostart = self.mplayer["autostart"])
        
        self.mplayer.hide()
        self.mplayer.stop()
        
        layout.removeWidget(self.mplayer)
        return params
    
    def loadFlowPlayer(self):
        layout = self.playerFrame.layout()
        params = self.removePlayer( layout )
        
        self.mplayer = self.mFlowPlayer
        layout.addWidget( self.mplayer )
        
        self.reload(**params)
        self.mplayer.show()
        
        self.btnSkins.setMenu( self.setupSkinMenu() )
        
    def loadJwPlayer(self):
        layout = self.playerFrame.layout()
        params = self.removePlayer( layout )
        
        self.mplayer = self.mJWPlayer
        layout.addWidget( self.mJWPlayer )
        
        self.reload(**params)
        self.mplayer.show()
        
        self.btnSkins.setMenu( self.setupSkinMenu() )
        
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
                
## ------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    
    p = PlayerDialog()
    p.show()
    
    sys.exit(app.exec_())
    
    
    