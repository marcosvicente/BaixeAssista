# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uiPaypalDonation.ui'
#
# Created: Mon Feb 11 18:57:27 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(640, 400)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../../../../../../.designer/images/movies.png"), QtGui.QIcon.Normal,
                       QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnFrame = QtGui.QFrame(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnFrame.sizePolicy().hasHeightForWidth())
        self.btnFrame.setSizePolicy(sizePolicy)
        self.btnFrame.setAutoFillBackground(False)
        self.btnFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.btnFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.btnFrame.setObjectName("btnFrame")
        self.horizontalLayout.addWidget(self.btnFrame)
        self.address = QtGui.QLineEdit(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.address.sizePolicy().hasHeightForWidth())
        self.address.setSizePolicy(sizePolicy)
        self.address.setObjectName("address")
        self.horizontalLayout.addWidget(self.address)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.webViewFrame = QtGui.QFrame(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.webViewFrame.sizePolicy().hasHeightForWidth())
        self.webViewFrame.setSizePolicy(sizePolicy)
        self.webViewFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.webViewFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.webViewFrame.setObjectName("webViewFrame")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.webViewFrame)
        self.verticalLayout_2.setSpacing(5)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout.addWidget(self.webViewFrame)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.info = QtGui.QLabel(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.info.sizePolicy().hasHeightForWidth())
        self.info.setSizePolicy(sizePolicy)
        self.info.setObjectName("info")
        self.horizontalLayout_2.addWidget(self.info)
        self.btnClose = QtGui.QPushButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnClose.sizePolicy().hasHeightForWidth())
        self.btnClose.setSizePolicy(sizePolicy)
        self.btnClose.setObjectName("btnClose")
        self.horizontalLayout_2.addWidget(self.btnClose)
        self.donationBoxStatus = QtGui.QCheckBox(Dialog)
        self.donationBoxStatus.setObjectName("donationBoxStatus")
        self.horizontalLayout_2.addWidget(self.donationBoxStatus)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(
            QtGui.QApplication.translate("Dialog", "Make a donation.", None, QtGui.QApplication.UnicodeUTF8))
        self.info.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClose.setText(QtGui.QApplication.translate("Dialog", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.donationBoxStatus.setText(QtGui.QApplication.translate("Dialog", "Do not show this message again.", None,
                                                                    QtGui.QApplication.UnicodeUTF8))

