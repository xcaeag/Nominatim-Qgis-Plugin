"""
/***************************************************************************
Name			 	 : nominatim
Description          : Aide à la localisation
Date                 : March 2013
copyright            : (C) 2013 by AEAG
email                : xavier.culos@eau-adour-garonne.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
import os

from qgis.PyQt.QtCore import QCoreApplication, QFileInfo, Qt, QSettings, QTranslator
from qgis.PyQt.QtWidgets import QAction, QApplication
#from qgis.utils import showPluginHelp
from .ui.nominatimdialog import NominatimDialog
from .ui.nominatim_conf_dlg import nominatim_conf_dlg

# from .osmLocatorFilter import OsmLocatorFilter

from nominatim.__about__ import DIR_PLUGIN_ROOT, __title__, __version__
from nominatim.logic import tools


class Nominatim:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.path = QFileInfo(os.path.realpath(__file__)).path()
        self.toolBar = None
        self.canvas = self.iface.mapCanvas()
        self.dlgPosX = 100
        self.dlgPosY = 100
        self.lastSearch = ""
        self.localiseOnStartup = True
        self.defaultArea = Qt.LeftDockWidgetArea
        self.singleLayer = True

        self.read()

        # récup langue par défaut
        locale = QSettings().value("locale/userLocale")
        try:
            self.myLocale = locale[0:2]

            # exploiter le bon dictionnaire
            localePath = (
                QFileInfo(os.path.realpath(__file__)).path()
                + "/i18n/"
                + self.myLocale
                + ".qm"
            )

            # initialiser le traducteur
            if QFileInfo(localePath).exists():
                self.translator = QTranslator()
                self.translator.load(localePath)
                QCoreApplication.installTranslator(self.translator)
        except:
            # no translation
            pass

        try:
            self.nominatim_dlg
        except:
            self.nominatim_dlg = NominatimDialog(self.iface.mainWindow(), self)
            self.nominatim_dlg.visibilityChanged.connect(self.dockVisibilityChanged)
            self.nominatim_dlg.dockLocationChanged.connect(self.dockLocationChanged)

        try:
            self.nominatim_dlg.editSearch.setText(self.lastSearch)
        except:
            pass

        # self.filter = OsmLocatorFilter(self.iface, self)
        # self.filter.resultProblem.connect(self.showLocatorProblem)
        # self.iface.registerLocatorFilter(self.filter)

    # def showLocatorProblem(self, err):
    #    self.iface.messageBar().pushWarning(
    #        "{} - {}".format(self.tr("Error during OSM search"), err)
    #    )

    @staticmethod
    def tr(message):
        return QCoreApplication.translate("nominatim", message)

    def store(self):
        s = QSettings()
        s.setValue("nominatim/localiseOnStartup", self.localiseOnStartup)
        s.setValue("nominatim/limitSearchToExtent", tools.limitSearchToExtent)
        s.setValue("nominatim/dlgPosX", self.dlgPosX)
        s.setValue("nominatim/dlgPosY", self.dlgPosY)
        s.setValue("nominatim/lastSearch", self.lastSearch)
        s.setValue("nominatim/gnOptions", tools.gnOptions)
        s.setValue("nominatim/defaultArea", self.defaultArea)
        s.setValue("nominatim/singleLayer", self.singleLayer)

    def read(self):
        s = QSettings()

        self.localiseOnStartup = s.value(
            "nominatim/localiseOnStartup", (False), type=bool
        )
        tools.limitSearchToExtent = s.value(
            "nominatim/limitSearchToExtent", (False), type=bool
        )
        self.dlgPosX = s.value("nominatim/dlgPosX", 100, type=int)
        self.dlgPosY = s.value("nominatim/dlgPosY", 100, type=int)
        self.lastSearch = s.value("nominatim/lastSearch", "")
        tools.gnOptions = s.value("nominatim/gnOptions", "")
        self.defaultArea = s.value(
            "nominatim/defaultArea", Qt.LeftDockWidgetArea, type=int
        )
        self.singleLayer = s.value("nominatim/singleLayer", (True), type=bool)

    def initGui(self):
        self.toolBar = self.iface.pluginToolBar()

        self.act_config = QAction(
            self.tr("Configuration") + "...",
            self.iface.mainWindow(),
        )
        self.act_nominatim_help = QAction(
            self.tr("Help") + "...",
            self.iface.mainWindow(),
        )

        self.iface.addPluginToMenu(
            "&" + self.tr(__title__),
            self.act_config,
        )
        self.iface.addPluginToMenu(
            "&" + self.tr(__title__),
            self.act_nominatim_help,
        )

        # Add actions to the toolbar
        self.act_config.triggered.connect(self.do_config)
        self.act_nominatim_help.triggered.connect(
            lambda: tools.showPluginHelp(filename="doc/index")
        )

        self.iface.addDockWidget(self.defaultArea, self.nominatim_dlg)

    def unload(self):
        self.iface.removePluginMenu(
            "&" + self.tr(__title__),
            self.act_config,
        )
        self.iface.removePluginMenu(
            "&" + self.tr(__title__),
            self.act_nominatim_help,
        )
        self.store()
        self.deactivate()
        self.iface.removeDockWidget(self.nominatim_dlg)

    def dockVisibilityChanged(self, visible):
        try:
            self.defaultActive = visible
            if visible and self.localiseOnStartup:
                self.nominatim_dlg.doLocalize()
        except:
            pass

    def dockLocationChanged(self, area):
        self.defaultArea = area

    def activate(self):
        self.nominatim_dlg.show()

    def deactivate(self):
        try:
            self.nominatim_dlg.hide()
        except:
            pass

    def zoom(self):
        pass

    def do_config(self):
        dlg = nominatim_conf_dlg(self.iface.mainWindow(), self)
        dlg.setModal(True)

        dlg.show()
        dlg.exec_()
        del dlg
