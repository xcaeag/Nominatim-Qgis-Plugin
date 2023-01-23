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
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from .ui.nominatimdialog import NominatimDialog
from .ui.nominatim_conf_dlg import nominatim_conf_dlg
from nominatim.__about__ import DIR_PLUGIN_ROOT, __title__, __version__
from nominatim.logic import tools
# from .osmLocatorFilter import OsmLocatorFilter

# from qgis.core import QgsMessageLog

class Nominatim:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.path = QFileInfo(os.path.realpath(__file__)).path()
        self.toolbar = self.iface.pluginToolBar()
        self.canvas = self.iface.mapCanvas()
        self.lastSearch = ""
        self.localiseOnStartup = True
        self.singleLayer = True
        self.mainAction = None
        self.defaultArea = Qt.LeftDockWidgetArea

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

        self.actions = []

        self.pluginIsActive = False

        # Create the dockwidget 
        self.dockwidget = NominatimDialog(self.iface.mainWindow(), self)
        # self.dockwidget.deleteLater()

        # connect events
        self.dockwidget.closingPlugin.connect(self.onClosePlugin)
        self.dockwidget.dockLocationChanged.connect(self.dockLocationChanged)
        self.dockwidget.visibilityChanged.connect(self.dockVisibilityChanged)
        self.iface.addDockWidget(self.defaultArea, self.dockwidget)

        # self.filter = OsmLocatorFilter(self.iface, self)
        # self.filter.resultProblem.connect(self.showLocatorProblem)
        # self.iface.registerLocatorFilter(self.filter)

    @staticmethod
    def tr(message):
        return QCoreApplication.translate("nominatim", message)

    def store(self):
        s = QSettings()
        s.setValue("nominatim/localiseOnStartup", self.localiseOnStartup)
        s.setValue("nominatim/limitSearchToExtent", tools.limitSearchToExtent)
        s.setValue("nominatim/lastSearch", self.lastSearch)
        s.setValue("nominatim/gnOptions", tools.gnOptions)
        s.setValue("nominatim/singleLayer", self.singleLayer)
        s.setValue("nominatim/defaultArea", self.defaultArea)

    def read(self):
        s = QSettings()

        self.localiseOnStartup = s.value(
            "nominatim/localiseOnStartup", (False), type=bool
        )
        tools.limitSearchToExtent = s.value(
            "nominatim/limitSearchToExtent", (False), type=bool
        )
        self.lastSearch = s.value("nominatim/lastSearch", "")
        tools.gnOptions = s.value("nominatim/gnOptions", "")
        self.singleLayer = s.value("nominatim/singleLayer", (True), type=bool)
        self.defaultArea = s.value(
            "nominatim/defaultArea", Qt.LeftDockWidgetArea, type=int
        )

    def add_action(
        self,
        text, menu,
        callback,
        icon_path=None,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param menu: Menu entry that should be shown in menu items for this action.
        :type text: str

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        if icon_path is None:
            action = QAction(text, parent)
        else:
            action = QAction(QIcon(icon_path), text, parent)

        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = "{}/resources/nominatim.png".format(DIR_PLUGIN_ROOT)
        self.mainAction = self.add_action(
            self.tr(__title__),
            self.tr(__title__),
            self.run,
            icon_path=icon_path,
            parent=self.iface.mainWindow())
        self.mainAction.setCheckable(True)

        self.add_action(
            self.tr("Configuration") + "...",
            self.tr(__title__),
            self.do_config,
            add_to_toolbar=False,
            parent=self.iface.mainWindow())

        self.add_action(
            self.tr("Help") + "...",
            self.tr(__title__),
            self.do_help,
            add_to_toolbar=False,
            parent=self.iface.mainWindow())

    def onClosePlugin(self):
        self.dockwidget.hide()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.dockwidget.hide()
        self.dockwidget.deleteLater()

        for action in self.actions:
            self.iface.removePluginMenu(self.tr(__title__), action)
            self.iface.removeToolBarIcon(action)

        self.store()

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            # show the dockwidget
            self.dockwidget.show()
        else:
            # hide only
            self.onClosePlugin()

    def dockLocationChanged(self, area):
        self.defaultArea = area

    def dockVisibilityChanged(self, visible):
        self.pluginIsActive = visible
        if self.mainAction:
            self.mainAction.setChecked(visible)
        try:
            if visible and self.localiseOnStartup:
                self.dockwidget.doLocalize()
        except:
            pass

    def do_config(self):
        dlg = nominatim_conf_dlg(self.iface.mainWindow(), self)
        dlg.setModal(True)

        dlg.show()
        dlg.exec_()
        del dlg

    def do_help(self):
        tools.showPluginHelp(filename="doc/index")
