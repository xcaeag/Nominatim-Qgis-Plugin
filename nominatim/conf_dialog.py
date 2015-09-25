# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'W:\projets\QGis plugins export dev\nominatim\conf_dialog.ui'
#
# Created: Fri Sep 25 16:28:45 2015
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_ConfDialog(object):
    def setupUi(self, ConfDialog):
        ConfDialog.setObjectName(_fromUtf8("ConfDialog"))
        ConfDialog.setWindowModality(QtCore.Qt.WindowModal)
        ConfDialog.setEnabled(True)
        ConfDialog.resize(547, 192)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ConfDialog.sizePolicy().hasHeightForWidth())
        ConfDialog.setSizePolicy(sizePolicy)
        ConfDialog.setMinimumSize(QtCore.QSize(540, 150))
        ConfDialog.setSizeGripEnabled(True)
        self.verticalLayout_2 = QtGui.QVBoxLayout(ConfDialog)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.label_3 = QtGui.QLabel(ConfDialog)
        self.label_3.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_3.setOpenExternalLinks(True)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout_4.addWidget(self.label_3)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(ConfDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.editOptions = QtGui.QLineEdit(ConfDialog)
        self.editOptions.setText(_fromUtf8(""))
        self.editOptions.setObjectName(_fromUtf8("editOptions"))
        self.horizontalLayout.addWidget(self.editOptions)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.lbEx = QtGui.QLabel(ConfDialog)
        self.lbEx.setToolTip(_fromUtf8(""))
        self.lbEx.setObjectName(_fromUtf8("lbEx"))
        self.horizontalLayout_3.addWidget(self.lbEx)
        self.btnBox = QtGui.QPushButton(ConfDialog)
        self.btnBox.setAutoDefault(True)
        self.btnBox.setFlat(True)
        self.btnBox.setObjectName(_fromUtf8("btnBox"))
        self.horizontalLayout_3.addWidget(self.btnBox)
        self.btnCountry = QtGui.QPushButton(ConfDialog)
        self.btnCountry.setAutoDefault(True)
        self.btnCountry.setFlat(True)
        self.btnCountry.setObjectName(_fromUtf8("btnCountry"))
        self.horizontalLayout_3.addWidget(self.btnCountry)
        self.btnMax = QtGui.QPushButton(ConfDialog)
        self.btnMax.setAutoDefault(True)
        self.btnMax.setFlat(True)
        self.btnMax.setObjectName(_fromUtf8("btnMax"))
        self.horizontalLayout_3.addWidget(self.btnMax)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.cbStart = QtGui.QCheckBox(ConfDialog)
        self.cbStart.setObjectName(_fromUtf8("cbStart"))
        self.verticalLayout.addWidget(self.cbStart)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.singleLayerCbx = QtGui.QCheckBox(ConfDialog)
        self.singleLayerCbx.setObjectName(_fromUtf8("singleLayerCbx"))
        self.verticalLayout_2.addWidget(self.singleLayerCbx)
        self.buttonBox = QtGui.QDialogButtonBox(ConfDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_2.addWidget(self.buttonBox)
        self.label.setBuddy(self.editOptions)

        self.retranslateUi(ConfDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ConfDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ConfDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ConfDialog)
        ConfDialog.setTabOrder(self.editOptions, self.cbStart)
        ConfDialog.setTabOrder(self.cbStart, self.buttonBox)

    def retranslateUi(self, ConfDialog):
        ConfDialog.setWindowTitle(_translate("ConfDialog", "OSM place search plugin configuration", None))
        self.label_3.setText(_translate("ConfDialog", "<p>Nominatim Search from <a href=\"http://wiki.openstreetmap.org/wiki/Nominatim_usage_policy\" target=\"_blank\">OSM</a> <img src=\"http://www.openstreetmap.org/assets/osm_logo.png\">, data © OpenStreetMap contributors - <a href=\"www.openstreetmap.org/copyright\">copyright</a></p>", None))
        self.label.setText(_translate("ConfDialog", "Options : ", None))
        self.lbEx.setText(_translate("ConfDialog", "Ex : ", None))
        self.btnBox.setToolTip(_translate("ConfDialog", "Click here to pick exemple", None))
        self.btnBox.setText(_translate("ConfDialog", "viewbox=-1.85,46.35,3.90,42.50", None))
        self.btnCountry.setToolTip(_translate("ConfDialog", "Click here to pick exemple", None))
        self.btnCountry.setText(_translate("ConfDialog", "countrycodes=FR", None))
        self.btnMax.setToolTip(_translate("ConfDialog", "Click here to pick exemple", None))
        self.btnMax.setText(_translate("ConfDialog", "limit=20", None))
        self.cbStart.setText(_translate("ConfDialog", "Find the nearest location at startup", None))
        self.singleLayerCbx.setText(_translate("ConfDialog", "Create a layer for each object (new layer functionality)", None))

