# coding: utf-8
import sys
import os

from PySide import QtCore, QtGui
from PySide.QtWebKit import QWebView
from django.template import Context, loader

from .uiPaypalDonation import Ui_Dialog
from .stopRefreshButton import StopRefreshButton
from main import settings


class DialogDonate(QtGui.QDialog):
    template = "paypalDoar.html"
    url = QtCore.QUrl("http://www.contrib-paypal/")

    def __init__(self, parent=None):
        super(DialogDonate, self).__init__(parent)
        self.uiDialog = Ui_Dialog()
        self.uiDialog.setupUi(self)

        self.userName = os.environ.get("USERNAME", self.tr("User"))

        boxLayout = QtGui.QVBoxLayout()
        self.btnFrame.setLayout(boxLayout)

        self.btnSR = StopRefreshButton()
        self.btnSR.clicked.connect(self.onStopRefresh)
        boxLayout.addWidget(self.btnSR, 0, 0)

        self.webView = QWebView(self.webViewFrame)
        self.webView.loadStarted.connect(self.onPageLoad)
        self.webView.loadFinished.connect(self.onPageFinished)
        self.webView.loadProgress.connect(self.onProgress)
        self.webView.urlChanged.connect(self.onChangeUrl)

        self.html = self.getTemplateHtml({"msg": self.getDevMsg()})

        self.webView.setHtml(self.html, self.url)
        self.webViewFrame.layout().addWidget(self.webView)

        self.btnClose.clicked.connect(self.close)

    def getDevMsg(self):
        msg = self.tr("Hello! {username}<br/><br/>"
                      "Now you have the opportunity to contribute to the development of this project.<br/>"
                      "Donate the amount you can with the system palypal.<br/><br/>"
                      "Suggested Value: $ 5.00<br/><br/>"
                      "Click the donate button to start the donation process.<br/>"
                      "If you do not have a paypal account, you can do by clicking the donate button.<br/><br/>"
                      "You can disable this message by checking the box at the bottom of the window.<br/>"
                      "You can also donate at any time by clicking the menu about.<br/>"
                      "Anyway, Thanks for attention.<br/>")
        return msg.format(username=self.userName)

    def onPageLoad(self):
        self.address.setText(self.webView.url().toString())
        self.info.setText(self.tr("Loading..."))
        self.btnSR.setStopState()

    def onStopRefresh(self):
        if self.btnSR["state"] == "refresh":
            if self.webView.url().host() == self.url.host():
                self.webView.setHtml(self.html, self.url)
            else:
                self.webView.reload()
        else:
            self.webView.stop()

    def onPageFinished(self, url):
        self.info.setText(self.tr("..."))
        self.btnSR.setRefreshState()

    def onProgress(self, progress):
        self.info.setText(self.tr("Loading...") + (" %d%%" % progress))

    def onChangeUrl(self, url):
        self.address.setToolTip(self.webView.url().toString())
        self.uiDialog.address.setText(url.toString())

    @classmethod
    def getTemplateHtml(cls, params):
        try:
            tmpl = loader.get_template(cls.template)
        except:
            tmpl = loader.find_template(cls.template, dirs=(settings.TEMPLATE_PATH,))[0]
        return tmpl.render(Context({"params": params}))

    @property
    def isOn(self):
        return not self.donationBoxStatus.isChecked()

    def setOff(self, flag):
        self.donationBoxStatus.setChecked(flag)

    @property
    def btnFrame(self):
        return self.uiDialog.btnFrame

    @property
    def webViewFrame(self):
        return self.uiDialog.webViewFrame

    @property
    def info(self):
        return self.uiDialog.info

    @property
    def address(self):
        return self.uiDialog.address

    @property
    def donationBoxStatus(self):
        return self.uiDialog.donationBoxStatus

    @property
    def btnClose(self):
        return self.uiDialog.btnClose


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    win = DialogDonate()
    win.show()

    sys.exit(app.exec_())