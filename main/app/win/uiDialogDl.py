# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uiDialogDl.ui'
#
# Created: Sun Jan 27 01:29:21 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(542, 285)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../images/movies.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.infoProgress = QtGui.QLabel(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.infoProgress.sizePolicy().hasHeightForWidth())
        self.infoProgress.setSizePolicy(sizePolicy)
        self.infoProgress.setObjectName("infoProgress")
        self.verticalLayout.addWidget(self.infoProgress)
        self.siteResponse = QtGui.QTextEdit(Dialog)
        self.siteResponse.setObjectName("siteResponse")
        self.verticalLayout.addWidget(self.siteResponse)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.infoProgress.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))

