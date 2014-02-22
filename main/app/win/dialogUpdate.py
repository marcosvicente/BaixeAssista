from PySide import QtCore, QtGui
from .uiDialogUpdate import Ui_Dialog

class DialogUpdate(QtGui.QDialog):
    
    def __init__(self, parent=None):
        super(DialogUpdate, self).__init__(parent)
        
        self.uiDialog = Ui_Dialog()
        self.uiDialog.setupUi(self)
        
        self.uiDialog.btnOk.clicked.connect(self.close)
        
    def setTextInfo(self, text):
        self.uiDialog.infoUpdate.setText(text)
    
    def setTextChanges(self, text):
        self.uiDialog.changesUpdate.setText(text)
        
        