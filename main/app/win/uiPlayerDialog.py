# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'uiPlayerDialog.ui'
#
# Created: Wed Feb 06 17:43:50 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui


class Ui_playerDialog(object):
    def setupUi(self, playerDialog):
        playerDialog.setObjectName("playerDialog")
        playerDialog.resize(945, 482)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../images/movies.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        playerDialog.setWindowIcon(icon)
        self.verticalLayout = QtGui.QVBoxLayout(playerDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 4, 1, 1)
        self.btnReload = QtGui.QPushButton(playerDialog)
        self.btnReload.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("../images/btnrefresh-blue.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnReload.setIcon(icon1)
        self.btnReload.setObjectName("btnReload")
        self.gridLayout_2.addWidget(self.btnReload, 0, 0, 1, 1)
        self.btnFlowPlayer = QtGui.QPushButton(playerDialog)
        self.btnFlowPlayer.setToolTip("")
        self.btnFlowPlayer.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("../images/flowplayer-eyes.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnFlowPlayer.setIcon(icon2)
        self.btnFlowPlayer.setCheckable(True)
        self.btnFlowPlayer.setChecked(True)
        self.btnFlowPlayer.setFlat(False)
        self.btnFlowPlayer.setObjectName("btnFlowPlayer")
        self.gridLayout_2.addWidget(self.btnFlowPlayer, 0, 1, 1, 1)
        self.btnJwPlayer = QtGui.QPushButton(playerDialog)
        self.btnJwPlayer.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("../images/jwplayer-play.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnJwPlayer.setIcon(icon3)
        self.btnJwPlayer.setCheckable(True)
        self.btnJwPlayer.setObjectName("btnJwPlayer")
        self.gridLayout_2.addWidget(self.btnJwPlayer, 0, 2, 1, 1)
        self.btnSkins = QtGui.QPushButton(playerDialog)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("../images/settings-tool.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSkins.setIcon(icon4)
        self.btnSkins.setObjectName("btnSkins")
        self.gridLayout_2.addWidget(self.btnSkins, 0, 3, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.playerFrame = QtGui.QFrame(playerDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.playerFrame.sizePolicy().hasHeightForWidth())
        self.playerFrame.setSizePolicy(sizePolicy)
        self.playerFrame.setFrameShape(QtGui.QFrame.Panel)
        self.playerFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.playerFrame.setObjectName("playerFrame")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.playerFrame)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout.addWidget(self.playerFrame)

        self.retranslateUi(playerDialog)
        QtCore.QMetaObject.connectSlotsByName(playerDialog)

    def retranslateUi(self, playerDialog):
        playerDialog.setWindowTitle(
            QtGui.QApplication.translate("playerDialog", "SWF Player", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSkins.setText(
            QtGui.QApplication.translate("playerDialog", "skin", None, QtGui.QApplication.UnicodeUTF8))

