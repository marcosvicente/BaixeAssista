# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainLayout.ui'
#
# Created: Mon Jan 21 21:08:15 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1123, 780)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.centralFrame = QtGui.QFrame(self.centralwidget)
        self.centralFrame.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.centralFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.centralFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.centralFrame.setObjectName("centralFrame")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.centralFrame)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.tabPanel = QtGui.QTabWidget(self.centralFrame)
        self.tabPanel.setObjectName("tabPanel")
        self.tabPlayer = QtGui.QWidget()
        self.tabPlayer.setObjectName("tabPlayer")
        self.tabPanel.addTab(self.tabPlayer, "")
        self.tabConfig = QtGui.QWidget()
        self.tabConfig.setObjectName("tabConfig")
        self.tabPanel.addTab(self.tabConfig, "")
        self.tabBrowser = QtGui.QWidget()
        self.tabBrowser.setObjectName("tabBrowser")
        self.tabPanel.addTab(self.tabBrowser, "")
        self.horizontalLayout_2.addWidget(self.tabPanel)
        self.horizontalLayout.addWidget(self.centralFrame)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1123, 26))
        self.menubar.setObjectName("menubar")
        self.menuEdit = QtGui.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuLing = QtGui.QMenu(self.menubar)
        self.menuLing.setObjectName("menuLing")
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
        self.actionEnglish.setChecked(False)
        self.actionEnglish.setObjectName("actionEnglish")
        self.actionPortuguse = QtGui.QAction(MainWindow)
        self.actionPortuguse.setCheckable(True)
        self.actionPortuguse.setChecked(False)
        self.actionPortuguse.setObjectName("actionPortuguse")
        self.menuEdit.addAction(self.actionExit)
        self.menuLing.addAction(self.actionEnglish)
        self.menuLing.addAction(self.actionPortuguse)
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuLing.menuAction())

        self.retranslateUi(MainWindow)
        self.tabPanel.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.tabPanel.setTabText(self.tabPanel.indexOf(self.tabPlayer), QtGui.QApplication.translate("MainWindow", "Player", None, QtGui.QApplication.UnicodeUTF8))
        self.tabPanel.setTabText(self.tabPanel.indexOf(self.tabConfig), QtGui.QApplication.translate("MainWindow", "Configuration", None, QtGui.QApplication.UnicodeUTF8))
        self.tabPanel.setTabText(self.tabPanel.indexOf(self.tabBrowser), QtGui.QApplication.translate("MainWindow", "Browser", None, QtGui.QApplication.UnicodeUTF8))
        self.menuEdit.setTitle(QtGui.QApplication.translate("MainWindow", "Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.menuLing.setTitle(QtGui.QApplication.translate("MainWindow", "Lang", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExit.setText(QtGui.QApplication.translate("MainWindow", "Exit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionEnglish.setText(QtGui.QApplication.translate("MainWindow", "English", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPortuguse.setText(QtGui.QApplication.translate("MainWindow", "Portuguese", None, QtGui.QApplication.UnicodeUTF8))

