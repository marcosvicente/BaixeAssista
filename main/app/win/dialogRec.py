from PySide import QtCore, QtGui
from uiDialogRec import Ui_Dialog

## --------------------------------------------------------------------------
class DialogRec(QtGui.QDialog):
    def __init__(self, title="recover file", parent=None):
        super(DialogRec, self).__init__(parent)
        
        self.uiDialog = Ui_Dialog()
        self.uiDialog.setupUi(self)
        
        self.btnOK.setEnabled(False)
        
        self.setWindowTitle(title)
        
    @property
    def progressBar(self):
        return self.uiDialog.progressBar
    
    @property
    def btnOK(self):
        return self.uiDialog.buttonBox.button(QtGui.QDialogButtonBox.Ok)
    
    @property
    def textProgress(self):
        return self.uiDialog.textProgress
    
    @property
    def btnCancel(self):
        return self.uiDialog.buttonBox.button(QtGui.QDialogButtonBox.Cancel)