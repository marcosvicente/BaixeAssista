# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uiErrorDialog.ui'
#
# Created: Thu Jan 31 14:52:45 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(813, 477)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../images/movies.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.verticalLayout_2 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_2.setSpacing(11)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox = QtGui.QGroupBox(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.userIssue = QtGui.QPlainTextEdit(self.groupBox)
        self.userIssue.setObjectName("userIssue")
        self.verticalLayout.addWidget(self.userIssue)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.groupBox_3 = QtGui.QGroupBox(Dialog)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.userEmail = QtGui.QLineEdit(self.groupBox_3)
        self.userEmail.setObjectName("userEmail")
        self.verticalLayout_4.addWidget(self.userEmail)
        self.verticalLayout_2.addWidget(self.groupBox_3)
        self.groupBox_4 = QtGui.QGroupBox(Dialog)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.developerEmail = QtGui.QLineEdit(self.groupBox_4)
        self.developerEmail.setObjectName("developerEmail")
        self.verticalLayout_5.addWidget(self.developerEmail)
        self.verticalLayout_2.addWidget(self.groupBox_4)
        self.groupBox_2 = QtGui.QGroupBox(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.userOpinion = QtGui.QPlainTextEdit(self.groupBox_2)
        self.userOpinion.setObjectName("userOpinion")
        self.verticalLayout_3.addWidget(self.userOpinion)
        self.verticalLayout_2.addWidget(self.groupBox_2)
        self.logSend = QtGui.QCheckBox(Dialog)
        self.logSend.setChecked(True)
        self.logSend.setObjectName("logSend")
        self.verticalLayout_2.addWidget(self.logSend)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.infoSendEmail = QtGui.QLabel(Dialog)
        self.infoSendEmail.setObjectName("infoSendEmail")
        self.horizontalLayout.addWidget(self.infoSendEmail)
        self.btnSendEmail = QtGui.QPushButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnSendEmail.sizePolicy().hasHeightForWidth())
        self.btnSendEmail.setSizePolicy(sizePolicy)
        self.btnSendEmail.setObjectName("btnSendEmail")
        self.horizontalLayout.addWidget(self.btnSendEmail)
        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(
            QtGui.QApplication.translate("Dialog", "Error reporting", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Describe the problem you are having", None,
                                                            QtGui.QApplication.UnicodeUTF8))
        self.groupBox_3.setTitle(
            QtGui.QApplication.translate("Dialog", "If you want information about the issue, please email below.", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.groupBox_4.setTitle(
            QtGui.QApplication.translate("Dialog", "Make direct contact with the developer through the email below.",
                                         None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("Dialog",
                                                              "Your opinion is important. If you want to say something about the program, suggest something.",
                                                              None, QtGui.QApplication.UnicodeUTF8))
        self.logSend.setText(
            QtGui.QApplication.translate("Dialog", "Send log files along with the problem description.", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.infoSendEmail.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSendEmail.setText(QtGui.QApplication.translate("Dialog", "Send", None, QtGui.QApplication.UnicodeUTF8))

