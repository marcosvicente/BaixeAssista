# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uiDialogAbout.ui'
#
# Created: Mon Feb 11 19:18:17 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(435, 200)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../images/info-blue.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setObjectName("verticalLayout")
        self.devInfo = QtGui.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.devInfo.setFont(font)
        self.devInfo.setText("")
        self.devInfo.setObjectName("devInfo")
        self.verticalLayout.addWidget(self.devInfo)
        self.btnMakeDonation = QtGui.QCommandLinkButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnMakeDonation.sizePolicy().hasHeightForWidth())
        self.btnMakeDonation.setSizePolicy(sizePolicy)
        self.btnMakeDonation.setObjectName("btnMakeDonation")
        self.verticalLayout.addWidget(self.btnMakeDonation)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.btnMakeDonation.setText(
            QtGui.QApplication.translate("Dialog", "Contribute to the project. Make a donation.", None,
                                         QtGui.QApplication.UnicodeUTF8))

