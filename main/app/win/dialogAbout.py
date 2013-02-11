# coding: utf-8
import sys, os
from PySide import QtCore, QtGui
from uiDialogAbout import Ui_Dialog
## --------------------------------------------------------------------------

class DialogAbout(QtGui.QDialog):
    
    def __init__(self, parent=None, title=""):
        super(DialogAbout, self).__init__(parent)
        
        self.uiDialog = Ui_Dialog()
        self.uiDialog.setupUi(self)
        
        self.setWindowTitle(title)
        
    def setDevInfoText(self, text):
        self.uiDialog.devInfo.setText(text)
        
    @property
    def btnMakeDonation(self):
        return self.uiDialog.btnMakeDonation
    