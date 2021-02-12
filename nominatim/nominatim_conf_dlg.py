"""
"""
from .conf_dialog import Ui_ConfDialog

from PyQt5.QtWidgets import QDialog


class nominatim_conf_dlg(QDialog, Ui_ConfDialog):
    def __init__(self, parent, plugin):
        self.plugin = plugin
        self.parent = parent
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.defaultcursor = self.cursor

        self.buttonBox.accepted.connect(self.onAccepted)
        self.buttonBox.rejected.connect(self.onRejected)
        self.btnBox.released.connect(self.onExBox)
        self.btnCountry.released.connect(self.onExCountry)
        self.btnMax.released.connect(self.onExMax)

        self.cbStart.setChecked(self.plugin.localiseOnStartup)
        self.singleLayerCbx.setChecked(self.plugin.singleLayer)
        try:
            self.editOptions.setText((self.plugin.gnOptions))
        except:
            pass

    def onExBox(self):
        self.editOptions.setText(self.editOptions.text() + " " + self.btnBox.text())

    def onExCountry(self):
        self.editOptions.setText(self.editOptions.text() + " " + self.btnCountry.text())

    def onExMax(self):
        self.editOptions.setText(self.editOptions.text() + " " + self.btnMax.text())

    def onAccepted(self):
        self.plugin.projects = []

        self.plugin.localiseOnStartup = self.cbStart.isChecked()
        self.plugin.singleLayer = self.singleLayerCbx.isChecked()

        try:
            self.plugin.gnOptions = self.editOptions.text()
        except:
            pass

        self.plugin.store()

    def onRejected(self):
        pass
