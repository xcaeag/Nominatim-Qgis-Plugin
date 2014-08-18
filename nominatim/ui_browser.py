# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_atlashelp.ui'
#
# Created: Tue Jan 24 23:32:27 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

_fromUtf8 = lambda s: (s.decode("utf-8").encode("latin-1")) if s else s
_toUtf8 = lambda s: s.decode("latin-1").encode("utf-8") if s else s


class Ui_browser(object):
    def setupUi(self, featureInfo):
        featureInfo.setObjectName(_fromUtf8("Help"))
        featureInfo.resize(800, 650)
        self.verticalLayout = QtGui.QVBoxLayout(featureInfo)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.helpContent = QtWebKit.QWebView(featureInfo)
        self.helpContent.setObjectName(_fromUtf8("featureInfoContent"))
        self.verticalLayout.addWidget(self.helpContent)
        self.buttonBox = QtGui.QDialogButtonBox(featureInfo)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(featureInfo)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), featureInfo.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), featureInfo.reject)
        QtCore.QMetaObject.connectSlotsByName(featureInfo)

    def retranslateUi(self, w):
        w.setWindowTitle("Help")

from PyQt4 import QtWebKit
