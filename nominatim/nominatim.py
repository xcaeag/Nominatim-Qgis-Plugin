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
import sys
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import showPluginHelp

from nominatim_dlg import nominatim_dlg
from nominatim_conf_dlg import nominatim_conf_dlg

# Initialize Qt resources from file resources.py
import resources


class nominatim:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.path = QFileInfo(os.path.realpath(__file__)).path()
        self.toolBar = None
        self.canvas = self.iface.mapCanvas()
        self.dlgPosX = 100
        self.dlgPosY = 100
        self.lastSearch = ""
        self.localiseOnStartup = (True)
        self.limitSearchToExtent = (False)
        self.gnOptions = ""
        self.gnUsername = ""
        self.defaultArea = Qt.LeftDockWidgetArea
        self.singleLayer = True
        
        self.read()
        
        # récup langue par défaut
        locale = QSettings().value("locale/userLocale")
        self.myLocale = locale[0:2]
        # exploiter le bon dictionnaire
        localePath = QFileInfo(os.path.realpath(__file__)).path() + "/i18n/nominatim_" + self.myLocale + ".qm"
        # initialiser le traducteur
        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
                
        try:
            self.nominatim_dlg
        except:
            self.nominatim_dlg = nominatim_dlg(self.iface.mainWindow(), self)
            self.nominatim_dlg.visibilityChanged.connect(self.dockVisibilityChanged)
            self.nominatim_dlg.dockLocationChanged.connect(self.dockLocationChanged)
        
        try:
            self.nominatim_dlg.editSearch.setText(self.lastSearch)
        except:
            pass
                
    def store(self):
        s = QSettings()
        s.setValue("nominatim/localiseOnStartup", self.localiseOnStartup)
        s.setValue("nominatim/limitSearchToExtent", self.limitSearchToExtent)
        s.setValue("nominatim/dlgPosX", self.dlgPosX)
        s.setValue("nominatim/dlgPosY", self.dlgPosY)
        s.setValue("nominatim/lastSearch", self.lastSearch)
        s.setValue("nominatim/gnOptions", self.gnOptions)
        s.setValue("nominatim/gnUsername", self.gnUsername)
        s.setValue("nominatim/defaultArea", self.defaultArea)
        s.setValue("nominatim/singleLayer", self.singleLayer)
    
    def read(self):
        s = QSettings()
    
        self.localiseOnStartup = s.value("nominatim/localiseOnStartup", (False), type=bool)
        self.limitSearchToExtent = s.value("nominatim/limitSearchToExtent", (False), type=bool)
        self.dlgPosX = s.value("nominatim/dlgPosX", 100, type=int)
        self.dlgPosY = s.value("nominatim/dlgPosY", 100, type=int)
        self.lastSearch = s.value("nominatim/lastSearch", '')
        self.gnOptions = s.value("nominatim/gnOptions", '')
        self.gnUsername = s.value("nominatim/gnUsername", '')
        self.defaultArea = s.value("nominatim/defaultArea", Qt.LeftDockWidgetArea, type=int)
        self.singleLayer = s.value("nominatim/singleLayer", (True), type=bool)
    
    def initGui(self):  
        self.toolBar = self.iface.pluginToolBar()
    
        self.act_config = QAction(QApplication.translate("nominatim", "Configuration", None, QApplication.UnicodeUTF8) + "...", self.iface.mainWindow())
        self.act_nominatim_help = QAction(QApplication.translate("nominatim", "Help", None, QApplication.UnicodeUTF8) + "...", self.iface.mainWindow())
    
        self.iface.addPluginToMenu("&"+QApplication.translate("nominatim", "OSM place search", None, QApplication.UnicodeUTF8) + "...", self.act_config)
        self.iface.addPluginToMenu("&"+QApplication.translate("nominatim", "OSM place search", None, QApplication.UnicodeUTF8) + "...", self.act_nominatim_help)
    
        # Add actions to the toolbar
        QObject.connect(self.act_config, SIGNAL("triggered()"), self.do_config)
        QObject.connect(self.act_nominatim_help, SIGNAL("triggered()"), self.do_help)
        
        self.iface.addDockWidget( self.defaultArea, self.nominatim_dlg )
        
    def unload(self):
        self.iface.removePluginMenu("&"+QApplication.translate("nominatim", "OSM place search", None, QApplication.UnicodeUTF8) + "...", self.act_config)
        self.iface.removePluginMenu("&"+QApplication.translate("nominatim", "OSM place search", None, QApplication.UnicodeUTF8) + "...", self.act_nominatim_help)
        self.store()
        self.deactivate()
        self.iface.removeDockWidget(self.nominatim_dlg)     
    
    def dockVisibilityChanged(self, visible):
        try:
            self.defaultActive = visible
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
        result = dlg.exec_()
        del dlg
    
    def do_help(self):
        showPluginHelp()
