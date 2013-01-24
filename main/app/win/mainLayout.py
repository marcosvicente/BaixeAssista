# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainLayout.ui'
#
# Created: Thu Jan 24 00:16:18 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1024, 768)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.centralFrame = QtGui.QFrame(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.centralFrame.sizePolicy().hasHeightForWidth())
        self.centralFrame.setSizePolicy(sizePolicy)
        self.centralFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.centralFrame.setFrameShadow(QtGui.QFrame.Plain)
        self.centralFrame.setObjectName("centralFrame")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.centralFrame)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.locationMainUrl = QtGui.QComboBox(self.centralFrame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.locationMainUrl.sizePolicy().hasHeightForWidth())
        self.locationMainUrl.setSizePolicy(sizePolicy)
        self.locationMainUrl.setEditable(True)
        self.locationMainUrl.setModelColumn(0)
        self.locationMainUrl.setObjectName("locationMainUrl")
        self.horizontalLayout_3.addWidget(self.locationMainUrl)
        self.btnStartDl = QtGui.QPushButton(self.centralFrame)
        self.btnStartDl.setCheckable(True)
        self.btnStartDl.setFlat(False)
        self.btnStartDl.setObjectName("btnStartDl")
        self.horizontalLayout_3.addWidget(self.btnStartDl)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.tabPanel = QtGui.QTabWidget(self.centralFrame)
        self.tabPanel.setObjectName("tabPanel")
        self.tabPlayer = QtGui.QWidget()
        self.tabPlayer.setObjectName("tabPlayer")
        self.tabPanel.addTab(self.tabPlayer, "")
        self.tabBrowser = QtGui.QWidget()
        self.tabBrowser.setObjectName("tabBrowser")
        self.tabPanel.addTab(self.tabBrowser, "")
        self.tabConfig = QtGui.QWidget()
        self.tabConfig.setObjectName("tabConfig")
        self.tabPanel.addTab(self.tabConfig, "")
        self.verticalLayout.addWidget(self.tabPanel)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout.addWidget(self.centralFrame)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1024, 26))
        self.menubar.setObjectName("menubar")
        self.menuEdit = QtGui.QMenu(self.menubar)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.menuEdit.setFont(font)
        self.menuEdit.setObjectName("menuEdit")
        self.menuLang = QtGui.QMenu(self.menubar)
        self.menuLang.setObjectName("menuLang")
        self.menuAbout = QtGui.QMenu(self.menubar)
        self.menuAbout.setObjectName("menuAbout")
        self.menuUpdate = QtGui.QMenu(self.menuAbout)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.menuUpdate.setFont(font)
        self.menuUpdate.setObjectName("menuUpdate")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setCheckable(False)
        self.actionExit.setChecked(False)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionExit.setFont(font)
        self.actionExit.setObjectName("actionExit")
        self.actionEnglish = QtGui.QAction(MainWindow)
        self.actionEnglish.setCheckable(True)
        self.actionEnglish.setChecked(True)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionEnglish.setFont(font)
        self.actionEnglish.setObjectName("actionEnglish")
        self.actionPortuguse = QtGui.QAction(MainWindow)
        self.actionPortuguse.setCheckable(True)
        self.actionPortuguse.setChecked(False)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionPortuguse.setFont(font)
        self.actionPortuguse.setObjectName("actionPortuguse")
        self.actionAbout = QtGui.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionAbout.setFont(font)
        self.actionAbout.setObjectName("actionAbout")
        self.actionSpanish = QtGui.QAction(MainWindow)
        self.actionSpanish.setCheckable(True)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionSpanish.setFont(font)
        self.actionSpanish.setObjectName("actionSpanish")
        self.actionReloadPlayer = QtGui.QAction(MainWindow)
        self.actionReloadPlayer.setCheckable(True)
        self.actionReloadPlayer.setObjectName("actionReloadPlayer")
        self.actionLoadExternalPlayer = QtGui.QAction(MainWindow)
        self.actionLoadExternalPlayer.setCheckable(True)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionLoadExternalPlayer.setFont(font)
        self.actionLoadExternalPlayer.setObjectName("actionLoadExternalPlayer")
        self.actionEmbedPlayer = QtGui.QAction(MainWindow)
        self.actionEmbedPlayer.setCheckable(True)
        self.actionEmbedPlayer.setChecked(True)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionEmbedPlayer.setFont(font)
        self.actionEmbedPlayer.setObjectName("actionEmbedPlayer")
        self.actionExternalPlayer = QtGui.QAction(MainWindow)
        self.actionExternalPlayer.setCheckable(True)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionExternalPlayer.setFont(font)
        self.actionExternalPlayer.setObjectName("actionExternalPlayer")
        self.actionError_reporting = QtGui.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionError_reporting.setFont(font)
        self.actionError_reporting.setObjectName("actionError_reporting")
        self.actionAutomaticSearch = QtGui.QAction(MainWindow)
        self.actionAutomaticSearch.setCheckable(True)
        self.actionAutomaticSearch.setChecked(True)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionAutomaticSearch.setFont(font)
        self.actionAutomaticSearch.setObjectName("actionAutomaticSearch")
        self.actionCheckNow = QtGui.QAction(MainWindow)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actionCheckNow.setFont(font)
        self.actionCheckNow.setObjectName("actionCheckNow")
        self.menuEdit.addAction(self.actionEmbedPlayer)
        self.menuEdit.addAction(self.actionExternalPlayer)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionLoadExternalPlayer)
        self.menuEdit.addAction(self.actionReloadPlayer)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionExit)
        self.menuLang.addAction(self.actionEnglish)
        self.menuLang.addAction(self.actionPortuguse)
        self.menuLang.addAction(self.actionSpanish)
        self.menuUpdate.addAction(self.actionAutomaticSearch)
        self.menuUpdate.addAction(self.actionCheckNow)
        self.menuAbout.addAction(self.actionError_reporting)
        self.menuAbout.addAction(self.menuUpdate.menuAction())
        self.menuAbout.addAction(self.actionAbout)
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuLang.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())

        self.retranslateUi(MainWindow)
        self.tabPanel.setCurrentIndex(2)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.btnStartDl.setText(QtGui.QApplication.translate("MainWindow", "Download", None, QtGui.QApplication.UnicodeUTF8))
        self.tabPanel.setTabText(self.tabPanel.indexOf(self.tabPlayer), QtGui.QApplication.translate("MainWindow", "Player", None, QtGui.QApplication.UnicodeUTF8))
        self.tabPanel.setTabText(self.tabPanel.indexOf(self.tabBrowser), QtGui.QApplication.translate("MainWindow", "Browser", None, QtGui.QApplication.UnicodeUTF8))
        self.tabPanel.setTabText(self.tabPanel.indexOf(self.tabConfig), QtGui.QApplication.translate("MainWindow", "Configuration", None, QtGui.QApplication.UnicodeUTF8))
        self.menuEdit.setTitle(QtGui.QApplication.translate("MainWindow", "Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.menuLang.setTitle(QtGui.QApplication.translate("MainWindow", "Lang", None, QtGui.QApplication.UnicodeUTF8))
        self.menuAbout.setTitle(QtGui.QApplication.translate("MainWindow", "Help", None, QtGui.QApplication.UnicodeUTF8))
        self.menuUpdate.setTitle(QtGui.QApplication.translate("MainWindow", "Update", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExit.setText(QtGui.QApplication.translate("MainWindow", "Exit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionEnglish.setText(QtGui.QApplication.translate("MainWindow", "English", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPortuguse.setText(QtGui.QApplication.translate("MainWindow", "Portuguese", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAbout.setText(QtGui.QApplication.translate("MainWindow", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSpanish.setText(QtGui.QApplication.translate("MainWindow", "Spanish", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReloadPlayer.setText(QtGui.QApplication.translate("MainWindow", "Reload player", None, QtGui.QApplication.UnicodeUTF8))
        self.actionLoadExternalPlayer.setText(QtGui.QApplication.translate("MainWindow", "Choose external player", None, QtGui.QApplication.UnicodeUTF8))
        self.actionEmbedPlayer.setText(QtGui.QApplication.translate("MainWindow", "Use embedded player", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExternalPlayer.setText(QtGui.QApplication.translate("MainWindow", "Use external player", None, QtGui.QApplication.UnicodeUTF8))
        self.actionError_reporting.setText(QtGui.QApplication.translate("MainWindow", "Error reporting", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAutomaticSearch.setText(QtGui.QApplication.translate("MainWindow", "Automatic search", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCheckNow.setText(QtGui.QApplication.translate("MainWindow", "Check now", None, QtGui.QApplication.UnicodeUTF8))

