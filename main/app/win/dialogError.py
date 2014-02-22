from PySide import QtCore, QtGui
from .uiErrorDialog import Ui_Dialog
from main.app.bugs import Bugs
from main import settings
import glob, os, threading

## --------------------------------------------------------------------------
class ReportingThread(QtCore.QObject, threading.Thread):
    responseAfter = QtCore.Signal(bool, str)
    
    def __init__(self, callback, parent=None):
        QtCore.QObject.__init__(self, parent)
        threading.Thread.__init__( self)
        
        self.callback = callback
    
    def run(self):
        result, response = self.callback()
        self.responseAfter.emit(result, response)
        
class DialogError(QtGui.QDialog):
    def __init__(self, parent=None):
        super(DialogError, self).__init__(parent)
        
        self.uiDialog = Ui_Dialog()
        self.uiDialog.setupUi(self)
        
        self.uiDialog.btnSendEmail.clicked.connect(self.sendEmail)
        self.sendEmailNow = False
    
    def setDeveloperEmail(self, email):
        self.uiDialog.developerEmail.setText(email)
    
    def onReportingResult(self, result, response):
        if result:
            QtGui.QMessageBox.information(self, self.tr("sucess!"), response)
            self.close()
        else:
            QtGui.QMessageBox.information(self, self.tr("error!"), response)
        
        self.uiDialog.infoSendEmail.setText("...")
        self.sendEmailNow = False
        
    def sendEmail(self):
        if self.sendEmailNow:
            QtGui.QMessageBox.information(self, self.tr("wait!"), 
                self.tr("Wait until the program finishes sending the current mail"))
            return
        
        self.sendEmailNow = True
        self.uiDialog.infoSendEmail.setText(
                    self.tr("Sending the email. Please wait."))
        
        userIssueText = self.uiDialog.userIssue.toPlainText()
        userOpinionText = self.uiDialog.userOpinion.toPlainText()
        userEmail = self.uiDialog.userEmail.text()
        sendLogOk = self.uiDialog.logSend.isChecked()
        
        info = Bugs(program=settings.PROGRAM_VERSION, 
                    userIssue = userIssueText, 
                    userOpinion = userOpinionText,
                    userEmail = userEmail,
                    files = glob.glob(os.path.join(settings.LOGS_DIR,"*.log")) if sendLogOk else [])
        
        # iniciando o envio do email em uma thread separada
        thread = ReportingThread(info.report)
        thread.responseAfter.connect(self.onReportingResult)
        thread.start()
        

        
        
        