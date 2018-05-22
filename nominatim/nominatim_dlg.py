import json
from urllib.parse import urlencode

from .dockwidget import Ui_search
from . import resources

from PyQt5.QtCore import (Qt, QVariant)
from PyQt5.QtWidgets import (QDockWidget, QHeaderView, QApplication, QTableWidgetItem)
from PyQt5.QtGui import (QIcon, QColor)

from qgis.core import (QgsProject, QgsApplication, QgsCoordinateReferenceSystem, 
                       QgsCoordinateTransform, QgsMessageLog, QgsGeometry,
                       QgsRectangle, QgsVectorLayer,
                       QgsField, QgsFields, QgsFeature,
                       QgsLineSymbol, QgsProject, QgsWkbTypes, QgsUnitTypes)

from qgis.gui import (QgsRubberBand)
from osgeo import ogr
from osgeo import osr

import requests

  
def getHttp(uri, params):
    QgsMessageLog.logMessage(uri+"?"+urlencode(params), 'Extensions')
    r = requests.get(uri, params=params)
    return r.text

def searchJson(params, user, options, options2):
    contents = str(options).strip()
    items = contents.split(' ') 
    
    for (k,v) in options2.items():
        if k in ['viewbox']:
            params["bounded"]="1"
        params[k]=v

    pairs = []    
    for item in items:
        pair = item.split('=',1)
        if (pair != [''] and pair != [] and len(pair) > 1):    
            pairs.append(pair)
        
    for (k,v) in pairs:
        if k in ['viewbox', 'countrycodes', 'limit', 'exclude_place_ids', 'addressdetails', 'exclude_place_ids', 'bounded', 'routewidth', 'osm_type', 'osm_id'] and not(k in list(options2.keys())) :
            params[k] = v
            
        if k in ['viewbox']:
            params["bounded"]="1"
            
    params["polygon_text"]="1"
    params["format"]="json"
    
    uri = 'https://nominatim.openstreetmap.org/search'
    
    QgsMessageLog.logMessage(uri+"?"+urlencode(params), 'Extensions')

    resource = getHttp(uri, params)
    results = json.loads(resource)

    return results
    
"""
"""    
def findNearbyJSON(params, user, options):
    uri = "https://nominatim.openstreetmap.org/reverse"

    params["format"]="json"

    resource = getHttp(uri, params)
    results = json.loads(resource)
    
    return results

class nominatim_dlg(QDockWidget, Ui_search):

    """
     Gestion de l'évènement "leave", afin d'effacer l'objet sélectionné en sortie du dock  
    """
    def eventFilter(self, obj, event):
        typ = event.type()
        if typ == event.Leave:
            try:
                self.plugin.canvas.scene().removeItem(self.rubber)
            except:
                pass

        return False

    def __init__(self, parent, plugin):
        self.plugin = plugin
        QDockWidget.__init__(self, parent)
        self.setupUi(self)
     
        self.defaultcursor = self.cursor
        
        self.btnApply.setIcon(QIcon(":plugins/nominatim/arrow_green.png"))
        self.btnMask.setIcon(QIcon(":plugins/nominatim/add_mask.png"))
        self.btnLayer.setIcon(QIcon(":plugins/nominatim/add_layer.png"))

        self.tableResult.installEventFilter(self) # cf. eventFilter method
        self.tableResult.cellDoubleClicked.connect(self.onChoose)
        self.tableResult.cellEntered.connect(self.cellEntered)

        self.editSearch.returnPressed.connect(self.onReturnPressed)
        self.btnSearch.clicked.connect(self.onReturnPressed)
        self.btnApply.clicked.connect(self.onApply)
        self.btnHelp.clicked.connect(self.plugin.do_help)
        self.btnLocalize.clicked.connect(self.doLocalize)
        self.btnMask.clicked.connect(self.onMask)
        self.btnLayer.clicked.connect(self.onLayer)
        
        self.MultiPolygonLayerId = None
        self.LineLayerId = None
        self.PointLayerId = None

        try:
            self.cbExtent.setChecked(self.plugin.limitSearchToExtent)
        except:
            self.cbExtent.setChecked(self.plugin.limitSearchToExtent)
        
        self.currentExtent = self.plugin.canvas.extent()
        
        
        self.tableResult.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        try:
            self.editSearch.setText(self.plugin.lastSearch)
        except: 
            pass
        
        try:
            if self.plugin.localiseOnStartup:
                self.doLocalize()
        except Exception as e:
            for m in e.args:
                QgsMessageLog.logMessage(m, 'Extensions')
            pass
        

    def cellEntered(self, row, col):
        item = self.tableResult.item(row, 0)

        try:
            self.plugin.canvas.scene().removeItem(self.rubber)
        except:
            pass
        
        self.showItem(item)
                    
    def onLayer(self):
        for r in self.tableResult.selectedRanges():
            item = self.tableResult.item(r.topRow(), 0)
            self.doLayer(item)

    def onMask(self):
        for r in self.tableResult.selectedRanges():
            item = self.tableResult.item(r.topRow(), 0)
            self.doMask(item)

    def populateRow(self, item, idx):         
        id = item['place_id']
        name = item['display_name']
            
        try:
            className = QApplication.translate("nominatim", item['class'], None)
        except:
            className = ""
            
        try:
            typeName = QApplication.translate("nominatim", item['type'], None)
        except:
            typeName = ""
        
        try:
            wkt = item['geotext']
        except:
            wkt = None
        
        try:
            osm_type = item['osm_type']
        except:
            osm_type = None

        bbox = {}
        if osm_type == "node":
            lat = item['lat']
            lng = item['lon']

            poFD = ogr.FeatureDefn("Point")
            poFD.SetGeomType(ogr.wkbPoint)
            
            oFLD = ogr.FieldDefn('id', ogr.OFTString)
            poFD.AddFieldDefn(oFLD)
            oFLD = ogr.FieldDefn('name', ogr.OFTString)
            poFD.AddFieldDefn(oFLD)
                    
            ogrFeature = ogr.Feature(poFD)
            wkt = "POINT("+str(lng)+" "+str(lat)+")"
            ogrGeom = ogr.CreateGeometryFromWkt(wkt)
        else:
            try:
                bbox = item['boundingbox']

                poFD = ogr.FeatureDefn("Rectangle")
                poFD.SetGeomType(ogr.wkbPolygon)
                
                oFLD = ogr.FieldDefn('id', ogr.OFTString)
                poFD.AddFieldDefn(oFLD)
                oFLD = ogr.FieldDefn('name', ogr.OFTString)
                poFD.AddFieldDefn(oFLD)
                        
                ogrFeature = ogr.Feature(poFD)
                if wkt == None:
                    wkt = "POLYGON(("+str(bbox[2])+" "+str(bbox[0])+", "+str(bbox[2])+" "+str(bbox[1])+", "+str(bbox[3])+" "+str(bbox[1])+", "+str(bbox[3])+" "+str(bbox[0])+", "+str(bbox[2])+" "+str(bbox[0])+"))"
                    
                ogrGeom = ogr.CreateGeometryFromWkt(wkt)
            except:
                lat = item['lat']
                lng = item['lon']
    
                poFD = ogr.FeatureDefn("Point")
                poFD.SetGeomType(ogr.wkbPoint)
                
                oFLD = ogr.FieldDefn('id', ogr.OFTString)
                poFD.AddFieldDefn(oFLD)
                oFLD = ogr.FieldDefn('name', ogr.OFTString)
                poFD.AddFieldDefn(oFLD)
                        
                ogrFeature = ogr.Feature(poFD)
                wkt = "POINT("+str(lng)+" "+str(lat)+")"
                ogrGeom = ogr.CreateGeometryFromWkt(wkt)
        
        mapCrsWKT = self.plugin.canvas.mapSettings().destinationCrs().toWkt()
        
        sourceSRS = osr.SpatialReference()
        sourceSRS.ImportFromEPSG( 4326 )
        targetSRS = osr.SpatialReference()
        targetSRS.ImportFromWkt ( str(mapCrsWKT) )
        trsf = osr.CoordinateTransformation(sourceSRS, targetSRS)
        try:
            ogrGeom.Transform(trsf)
        except TypeError as e:
            QgsMessageLog.logMessage("Nominatim - transformation error. Check map projection.", 'Extensions')

        ogrFeature.SetGeometry(ogrGeom)
        
        ogrFeature.SetFID(int(idx+1))
        ogrFeature.SetField(str('id'), str(id))
        ogrFeature.SetField(str('name'), name)
        
        item = QTableWidgetItem(name)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled )
        item.setData(Qt.UserRole, ogrFeature)
        self.tableResult.setItem(idx, 0, item)

        itemLibelle = QTableWidgetItem(className)
        itemLibelle.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled )
        self.tableResult.setItem(idx, 1, itemLibelle)
    
        itemType = QTableWidgetItem(typeName)
        itemType.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled )
        self.tableResult.setItem(idx, 2, itemType)

    def populateTable(self, r):         
        idx = 0
        self.tableResult.clearContents()
        self.tableResult.setRowCount (len(r))
        for item in r:
            self.populateRow(item, idx)
            idx = idx+1
        
    def doLocalize(self):
        try:
            QgsApplication.setOverrideCursor(Qt.WaitCursor)
            
            # center
            bbox = self.plugin.canvas.extent()
            sourceCrs = self.plugin.canvas.mapSettings().destinationCrs()
            targetCrs = QgsCoordinateReferenceSystem()
            targetCrs.createFromSrid(4326)
            xform = QgsCoordinateTransform(sourceCrs, targetCrs, QgsProject.instance())
            bbox = xform.transform(bbox)
            
            params = {"lon":str(bbox.center().x()), "lat":str(bbox.center().y()), "zoom":"10"}
            self.tableResult.clearContents()
            r = findNearbyJSON(params, self.plugin.gnUsername, self.plugin.gnOptions)
            if r != None:
                self.tableResult.setRowCount(1)
                self.populateRow(r, 0)
                
        except Exception as e:
            for m in e.args:
                QgsMessageLog.logMessage(m, 'Extensions')
            pass
                
        QgsApplication.restoreOverrideCursor()
                
    def onReturnPressed(self):
        try:
            QgsApplication.setOverrideCursor(Qt.WaitCursor)
            
            txt = self.editSearch.text().strip()
            self.plugin.lastSearch = self.editSearch.text()
            self.plugin.limitSearchToExtent = (self.cbExtent.isChecked())
            options = self.plugin.gnOptions
            
            options2 = {}
            if self.plugin.limitSearchToExtent:
                sourceCrs = self.plugin.canvas.mapSettings().destinationCrs()
                targetCrs = QgsCoordinateReferenceSystem()
                targetCrs.createFromSrid(4326)
                xform = QgsCoordinateTransform(sourceCrs, targetCrs, QgsProject.instance())
                geom = xform.transform(self.plugin.canvas.extent())
                options2 = {'viewbox':str(geom.xMinimum())+','+str(geom.yMaximum())+','+str(geom.xMaximum())+','+str(geom.yMinimum())}
            
            params = { 'q':txt, 'addressdetails':'0' }
            r = searchJson(params, self.plugin.gnUsername, options, options2)
            if r != None:
                self.populateTable(r)
                
        except Exception as e:
            for m in e.args:
                QgsMessageLog.logMessage(m, 'Extensions')
            pass
                
        QgsApplication.restoreOverrideCursor()

    def onChoose(self, row, col):
        item = self.tableResult.item(row, 0)
        self.go(item) 
        
    def onApply(self):
        for item in self.tableResult.selectedItems():
            self.go(item)
            break
        
    def getBBox(self, item):
        ogrFeature = item.data(Qt.UserRole)
        geom = QgsGeometry.fromWkt(ogrFeature.GetGeometryRef().ExportToWkt())

            
        if (ogrFeature.GetDefnRef().GetGeomType() == ogr.wkbPoint):
            mapextent = self.plugin.canvas.extent()
            ww = mapextent.width()/100
            mapcrs = self.plugin.canvas.mapSettings().destinationCrs()

            x = geom.boundingBox().center().x()
            y = geom.boundingBox().center().y()
            
            ww = 50.0
            if mapcrs.mapUnits() ==  QgsUnitTypes.DistanceFeet :
                ww = 150
            if mapcrs.mapUnits() ==  QgsUnitTypes.DistanceDegrees :
                ww = 0.0005
                
            bbox = QgsRectangle(x-10*ww, y-10*ww, x+10*ww, y+10*ww) 
            return bbox
        else:
            bbox = geom.boundingBox()
            rubberRect = QgsRectangle(bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum())
            return rubberRect
        
    def showItem(self, item):
        ogrFeature = item.data(Qt.UserRole)
        geom = QgsGeometry.fromWkt(ogrFeature.GetGeometryRef().ExportToWkt())

        if (ogrFeature.GetDefnRef().GetGeomType() == ogr.wkbPoint):
            self.rubber = QgsRubberBand(self.plugin.canvas, QgsWkbTypes.PointGeometry)  
            self.rubber.setColor(QColor(50,50,255,100))
            self.rubber.setIcon (self.rubber.ICON_CIRCLE)
            self.rubber.setIconSize(15)
            self.rubber.setWidth(2)
            self.rubber.setToGeometry(geom, None)        
        else:
            # dont show if it is larger than the canvas
            if self.plugin.canvas.extent().contains(geom.boundingBox()):
                pass
            else:
                geom = geom.intersection(QgsGeometry.fromRect(self.plugin.canvas.extent()))
                
            self.rubber = QgsRubberBand(self.plugin.canvas, QgsWkbTypes.PolygonGeometry) 
            self.rubber.setColor(QColor(50,50,255,100))
            self.rubber.setWidth(4)
            self.rubber.setToGeometry(geom, None)        

    def go(self, item, zoom=True):
        try:
            self.plugin.canvas.scene().removeItem(self.rubber)
        except:
            pass

        if zoom:
            bbox = self.getBBox(item)
            self.plugin.canvas.setExtent(bbox)
            
        self.plugin.canvas.refresh();
        
        self.showItem(item);

    def doMask(self, item):
        mapcrs = self.plugin.canvas.mapSettings().destinationCrs()

        ogrFeature = item.data(Qt.UserRole)
        layerName = "OSM "+ogrFeature.GetFieldAsString('id')
        geom = QgsGeometry.fromWkt(ogrFeature.GetGeometryRef().ExportToWkt())
        if (geom.type() == QgsWkbTypes.PolygonGeometry):
            try:
                try:
                    from mask import aeag_mask
                except:
                    from mask_plugin import aeag_mask
                    
                aeag_mask.do(mapcrs, { geom }, "Mask "+layerName)
            
            except:

                geom = QgsGeometry.fromWkt(ogrFeature.GetGeometryRef().ExportToWkt())
                
                toCrs = self.plugin.canvas.mapSettings().destinationCrs()
    
                l = max(geom.boundingBox().width(), geom.boundingBox().height())
                x = geom.boundingBox().center().x()
                y = geom.boundingBox().center().y()
                rect = QgsRectangle(x-l, y-l, x+l, y+l) # geom.boundingBox()
                rect.scale(4)
                mask = QgsGeometry.fromRect(rect)
                    
                mask = mask.difference(geom)
    
                maskLayer = QgsVectorLayer("MultiPolygon", "Mask "+layerName, "memory")
                maskLayer.setCrs(toCrs) 
                QgsProject.instance().addMapLayer(maskLayer)
                pr = maskLayer.dataProvider()
                
                fields = QgsFields()
                fields.append(QgsField("id", QVariant.String))
                fields.append(QgsField("name",  QVariant.String))
                fet = QgsFeature()
                fet.initAttributes(2)    
                fet.setGeometry( mask )
                fet.setFields(fields)
                fet.setAttribute("id", (ogrFeature.GetFieldAsString('id')))
                fet.setAttribute("name", (ogrFeature.GetFieldAsString('name')))
            
                pr.addAttributes( fields.toList() )
                    
                maskLayer.startEditing()
                pr.addFeatures( [ fet ] )
                maskLayer.commitChanges()
                maskLayer.updateExtents()        
                    
                # transparence, epaisseur
                renderer = maskLayer.renderer() # QgsFeatureRenderer, QgsSingleSymbolRenderer  ?
                s = renderer.symbol()
                s.setAlpha(0.90)
                s.setColor(QColor(255, 255, 255))
                if isinstance(s, QgsLineSymbol):
                    s.setWidth(0)
                
                layerTree = QgsProject.instance().layerTreeRoot().findLayer(maskLayer)
                if layerTree:
                    self.plugin.iface.layerTreeView().layerTreeModel().refreshLayerLegend(layerTree)  #Refresh legend
            
            self.go(item)

    def doLayer(self, item):
        ogrFeature = item.data(Qt.UserRole)
        geom = QgsGeometry.fromWkt(ogrFeature.GetGeometryRef().ExportToWkt())

        fields = QgsFields()
        fields.append(QgsField("id", QVariant.String))
        fields.append(QgsField("name",  QVariant.String))
        fet = QgsFeature()
        fet.initAttributes(2)    
        fet.setFields(fields)
        fet.setGeometry(geom)
        fet.setAttribute("id", (ogrFeature.GetFieldAsString('id')))
        fet.setAttribute("name", (ogrFeature.GetFieldAsString('name')))

        vl = None
        if not self.plugin.singleLayer:
            if geom.type() == QgsWkbTypes.PolygonGeometry:
                layerName = "OSMPlaceSearch Polygon"
                layerId = self.MultiPolygonLayerId
            if geom.type() == QgsWkbTypes.LineGeometry:
                layerName = "OSMPlaceSearch Line"
                layerId = self.LineLayerId
            if geom.type() == QgsWkbTypes.PointGeometry:
                layerName = "OSMPlaceSearch Point"
                layerId = self.PointLayerId
                
            vl = QgsProject.instance().mapLayer(layerId)
            if vl != None:
                pr = vl.dataProvider()
            else:
                if geom.type() == QgsWkbTypes.PolygonGeometry:
                    vl = QgsVectorLayer("MultiPolygon", layerName, "memory")
                    self.MultiPolygonLayerId = vl.id()
                if geom.type() == QgsWkbTypes.LineGeometry:
                    vl = QgsVectorLayer("MultiLineString", layerName, "memory")
                    self.LineLayerId = vl.id()
                if geom.type() == QgsWkbTypes.PointGeometry:
                    vl = QgsVectorLayer("Point", layerName, "memory")
                    self.PointLayerId = vl.id()
                    
                if vl != None:
                    pr = vl.dataProvider()
                    # ajout de champs
                    pr.addAttributes( fields.toList() )
                    
                QgsProject.instance().addMapLayer(vl)
        else:                
            layerName = "OSM "+ogrFeature.GetFieldAsString('id')
            
            # creer une nouvelle couche si n'existe pas encore
            if geom.type() == QgsWkbTypes.PolygonGeometry:
                vl = QgsVectorLayer("MultiPolygon", layerName, "memory")
            if geom.type() == QgsWkbTypes.LineGeometry:
                vl = QgsVectorLayer("MultiLineString", layerName, "memory")
            if geom.type() == QgsWkbTypes.PointGeometry:
                vl = QgsVectorLayer("Point", layerName, "memory")
                
            if vl != None:
                pr = vl.dataProvider()
                # ajout de champs
                pr.addAttributes( fields.toList() )

            QgsProject.instance().addMapLayer(vl)

        if vl != None:
            vl.setProviderEncoding('UTF-8')
            vl.startEditing()
            pr.addFeatures( [ fet ] )
            vl.commitChanges()
            
            # mise a jour etendue de la couche
            vl.updateExtents()        
                          
            layerTree = QgsProject.instance().layerTreeRoot().findLayer(vl)
            if layerTree:
                self.plugin.iface.layerTreeView().layerTreeModel().refreshLayerLegend(layerTree)  #Refresh legend
                    
            self.go(item, False)
                    