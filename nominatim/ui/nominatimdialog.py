from osgeo import ogr
from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsMessageLog,
    QgsProject,
    QgsRectangle,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsRubberBand
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QEvent, Qt, pyqtSignal, QVariant
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import QApplication, QDockWidget, QHeaderView, QTableWidgetItem

from nominatim.__about__ import DIR_PLUGIN_ROOT
from nominatim.logic import tools

FORM_CLASS, _ = uic.loadUiType(DIR_PLUGIN_ROOT / "ui/dockwidget.ui")


class NominatimDialog(QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    """
    Gestion de l'évènement "leave", afin d'effacer l'objet sélectionné en sortie du dock
    """

    def eventFilter(self, obj, event):
        typ = event.type()
        if typ == QEvent.Type.Leave:
            self.rbPoint.reset()
            self.rbPolygon.reset()

        return False

    def __init__(self, parent, plugin):
        self.plugin = plugin
        QDockWidget.__init__(self, parent)
        self.setupUi(self)

        self.btnApply.setIcon(QIcon(str(DIR_PLUGIN_ROOT / "resources/arrow_green.png")))
        self.btnMask.setIcon(QIcon(str(DIR_PLUGIN_ROOT / "resources/add_mask.png")))
        self.btnLayer.setIcon(QIcon(str(DIR_PLUGIN_ROOT / "resources/add_layer.png")))
        self.btnHelp.setIcon(QIcon(QgsApplication.iconPath("mActionHelpContents.svg")))

        self.tableResult.installEventFilter(self)  # cf. eventFilter method
        self.tableResult.cellDoubleClicked.connect(self.onChoose)
        self.tableResult.cellEntered.connect(self.cellEntered)

        self.editSearch.returnPressed.connect(self.onReturnPressed)
        self.btnSearch.clicked.connect(self.onReturnPressed)
        self.btnApply.clicked.connect(self.onApply)
        self.btnHelp.clicked.connect(
            lambda: tools.showPluginHelp(filename="../doc/index")
        )

        self.btnLocalize.clicked.connect(self.doLocalize)
        self.btnMask.clicked.connect(self.onMask)
        self.btnLayer.clicked.connect(self.onLayer)

        self.singleLayerId = {
            QgsWkbTypes.GeometryType.PolygonGeometry: None,
            QgsWkbTypes.GeometryType.LineGeometry: None,
            QgsWkbTypes.GeometryType.PointGeometry: None,
        }
        self.singleLayerName = {
            QgsWkbTypes.GeometryType.PolygonGeometry: "OSM Place Search Polygons",
            QgsWkbTypes.GeometryType.LineGeometry: "OSM Place Search Lines",
            QgsWkbTypes.GeometryType.PointGeometry: "OSM Place Search Points",
        }
        self.memoryLayerType = {
            QgsWkbTypes.GeometryType.PolygonGeometry: "MultiPolygon",
            QgsWkbTypes.GeometryType.LineGeometry: "MultiLineString",
            QgsWkbTypes.GeometryType.PointGeometry: "Point",
        }

        self.rbPoint = QgsRubberBand(
            self.plugin.canvas, QgsWkbTypes.GeometryType.PointGeometry
        )
        self.rbPoint.setColor(QColor(50, 50, 255, 100))
        self.rbPoint.setIcon(self.rbPoint.ICON_CIRCLE)
        self.rbPoint.setIconSize(15)
        self.rbPoint.setWidth(2)

        self.rbPolygon = QgsRubberBand(
            self.plugin.canvas, QgsWkbTypes.GeometryType.PolygonGeometry
        )
        self.rbPolygon.setColor(QColor(50, 50, 255, 100))
        self.rbPolygon.setWidth(4)

        try:
            self.cbExtent.setChecked(tools.limitSearchToExtent)
        except Exception:
            self.cbExtent.setChecked(tools.limitSearchToExtent)

        self.currentExtent = self.plugin.canvas.extent()

        self.tableResult.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        try:
            self.editSearch.setText(self.plugin.lastSearch)
        except Exception:
            pass

    def cellEntered(self, row, col):
        item = self.tableResult.item(row, 0)

        self.rbPoint.reset()
        self.rbPolygon.reset()
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
        osm_id = item.get("osm_id")
        name = item["display_name"]

        try:
            className = QApplication.translate("nominatim", item["class"], None)
        except Exception:
            className = ""

        try:
            typeName = QApplication.translate("nominatim", item["type"], None)
        except Exception:
            typeName = ""

        wkt = item.get("geotext")
        # osm_type = item.get("osm_type")

        # extratags and address_details are dictionaries with content that can
        # vary per feature and also per nominatim server. We expose them as
        # HStore strings as that is easy to handle in QGIS with the
        # hstore_to_map expression function.
        # When querying the official OSM nominatim server, the extratags
        # contain all the tags not already included in the class, address, etc
        # fields. Other nominatim servers can be configured differently.
        address = item.get("address")
        if address:
            address = tools.dict_to_hstore_string(address)
        else:
            address = ""

        extratags = item.get("extratags")
        if extratags:
            extratags = tools.dict_to_hstore_string(extratags)
        else:
            extratags = ""

        if "boundingbox" in item.keys():
            # we have a polygonal item
            bbox = item["boundingbox"]

            poFD = ogr.FeatureDefn("Rectangle")
            poFD.SetGeomType(ogr.wkbPolygon)
            NominatimDialog.add_fields(poFD)

            ogrFeature = ogr.Feature(poFD)
            if wkt is None:
                wkt = "POLYGON(({b[2]} {b[0]}, {b[2]} {b[1]}, {b[3]} {b[1]}, {b[3]} {b[0]}, {b[2]} {b[0]}))".format(
                    b=bbox
                )

            ogrGeom = ogr.CreateGeometryFromWkt(wkt)
        else:
            # we have something to represent as a point
            lat = item["lat"]
            lng = item["lon"]

            poFD = ogr.FeatureDefn("Point")
            poFD.SetGeomType(ogr.wkbPoint)
            NominatimDialog.add_fields(poFD)

            ogrFeature = ogr.Feature(poFD)
            wkt = "POINT({} {})".format(lng, lat)
            ogrGeom = ogr.CreateGeometryFromWkt(wkt)

        ogrFeature.SetGeometry(ogrGeom)
        ogrFeature.SetFID(int(idx + 1))
        ogrFeature.SetField("osm_id", osm_id)
        ogrFeature.SetField("class", className)
        ogrFeature.SetField("type", typeName)
        ogrFeature.SetField("name", name)
        ogrFeature.SetField("address", address)
        ogrFeature.SetField("extratags", extratags)

        item = QTableWidgetItem(name)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        item.setData(Qt.ItemDataRole.UserRole, ogrFeature)
        self.tableResult.setItem(idx, 0, item)

        itemLibelle = QTableWidgetItem(className)
        itemLibelle.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.tableResult.setItem(idx, 1, itemLibelle)

        itemType = QTableWidgetItem(typeName)
        itemType.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.tableResult.setItem(idx, 2, itemType)

    def populateTable(self, r):
        idx = 0
        self.tableResult.clearContents()
        self.tableResult.setRowCount(len(r))
        for item in r:
            self.populateRow(item, idx)
            idx = idx + 1

    def doLocalize(self):
        try:
            # center
            bbox = self.plugin.canvas.extent()
            sourceCrs = self.plugin.canvas.mapSettings().destinationCrs()
            targetCrs = QgsCoordinateReferenceSystem("EPSG:4326")
            xform = QgsCoordinateTransform(sourceCrs, targetCrs, QgsProject.instance())
            bbox = xform.transform(bbox)

            params = {"lon": str(bbox.center().x()), "lat": str(bbox.center().y())}
            r = tools.osmFindNearbyJSON(params)
            if r is not None:
                self.populateTable(r)
            else:
                self.tableResult.clearContents()

        except Exception as e:
            for m in e.args:
                QgsMessageLog.logMessage(m, "Extensions")
            pass

    def search(self, txt):
        try:
            self.plugin.lastSearch = self.editSearch.text()
            tools.limitSearchToExtent = self.cbExtent.isChecked()
            return tools.osmSearch(self.plugin.iface.mapCanvas(), txt)

        except Exception as e:
            for m in e.args:
                QgsMessageLog.logMessage(m, "Extensions")

        return None

    def onReturnPressed(self):
        txt = self.editSearch.text().strip()
        r = self.search(txt)
        if r is not None:
            self.populateTable(r)
        else:
            self.tableResult.clearContents()

    def onChoose(self, row, col):
        item = self.tableResult.item(row, 0)
        self.go(item)

    def onApply(self):
        for item in self.tableResult.selectedItems():
            self.go(item)
            break

    def transform(self, geom):
        sourceSRS = QgsCoordinateReferenceSystem("EPSG:4326")
        mapCrs = self.plugin.canvas.mapSettings().destinationCrs()
        trsf = QgsCoordinateTransform(sourceSRS, mapCrs, QgsProject.instance())
        try:
            geom.transform(trsf)
        except TypeError:
            QgsMessageLog.logMessage(
                "Nominatim - transformation error. Check map projection.", "Extensions"
            )

    def getBBox(self, item):
        ogrFeature = item.data(Qt.ItemDataRole.UserRole)
        geom = QgsGeometry.fromWkt(ogrFeature.GetGeometryRef().ExportToWkt())
        self.transform(geom)

        if ogrFeature.GetDefnRef().GetGeomType() == ogr.wkbPoint:
            mapextent = self.plugin.canvas.extent()
            ww = mapextent.width() / 100
            mapcrs = self.plugin.canvas.mapSettings().destinationCrs()

            x = geom.boundingBox().center().x()
            y = geom.boundingBox().center().y()

            ww = 50.0
            if mapcrs.mapUnits() == QgsUnitTypes.DistanceUnit.DistanceFeet:
                ww = 150
            if mapcrs.mapUnits() == QgsUnitTypes.DistanceUnit.DistanceDegrees:
                ww = 0.0005

            bbox = QgsRectangle(x - 10 * ww, y - 10 * ww, x + 10 * ww, y + 10 * ww)
            return bbox
        else:
            bbox = geom.boundingBox()
            rubberRect = QgsRectangle(
                bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum()
            )
            return rubberRect

    def showItem(self, item):
        ogrFeature = item.data(Qt.ItemDataRole.UserRole)
        geom = QgsGeometry.fromWkt(ogrFeature.GetGeometryRef().ExportToWkt())
        self.transform(geom)

        if ogrFeature.GetDefnRef().GetGeomType() == ogr.wkbPoint:
            self.rbPoint.setToGeometry(geom, None)
        else:
            # dont show if it is larger than the canvas
            if self.plugin.canvas.extent().contains(geom.boundingBox()):
                pass
            else:
                geom = geom.intersection(
                    QgsGeometry.fromRect(self.plugin.canvas.extent())
                )
            self.rbPolygon.setToGeometry(geom, None)

    def go(self, item, zoom=True):
        self.rbPoint.reset()
        self.rbPolygon.reset()

        if zoom:
            bbox = self.getBBox(item)
            self.plugin.canvas.setExtent(bbox)

        self.plugin.canvas.refresh()
        self.showItem(item)

    def addNewLayer(self, layerName, typ, fields):
        vl = QgsVectorLayer(self.memoryLayerType[typ], layerName, "memory")
        if vl:
            vl.setProviderEncoding("UTF-8")
            pr = vl.dataProvider()
            pr.addAttributes(fields.toList())
            vl.setCrs(self.plugin.canvas.mapSettings().destinationCrs())
            QgsProject.instance().addMapLayer(vl)
            renderer = vl.renderer()
            s = renderer.symbol()
            s.setOpacity(0.85)

        return vl

    def doLayer(self, item, singleLayer=None):
        if singleLayer is None:
            singleLayer = self.plugin.singleLayer

        ogrFeature = item.data(Qt.ItemDataRole.UserRole)
        geom = QgsGeometry.fromWkt(ogrFeature.GetGeometryRef().ExportToWkt())
        self.transform(geom)

        fields = QgsFields()
        fields.append(QgsField("osm_id", QVariant.LongLong))
        fields.append(QgsField("class", QVariant.String))
        fields.append(QgsField("type", QVariant.String))
        fields.append(QgsField("name", QVariant.String))
        fields.append(QgsField("address", QVariant.String))
        fields.append(QgsField("extratags", QVariant.String))
        fet = QgsFeature()
        fet.initAttributes(2)
        fet.setFields(fields)
        fet.setGeometry(geom)
        fet.setAttribute("osm_id", (ogrFeature.GetFieldAsInteger64("osm_id")))
        fet.setAttribute("class", (ogrFeature.GetFieldAsString("class")))
        fet.setAttribute("type", (ogrFeature.GetFieldAsString("type")))
        fet.setAttribute("name", (ogrFeature.GetFieldAsString("name")))
        fet.setAttribute("address", (ogrFeature.GetFieldAsString("address")))
        fet.setAttribute("extratags", (ogrFeature.GetFieldAsString("extratags")))

        vl = None
        if not singleLayer:
            layerId = self.singleLayerId[geom.type()]
            layerName = self.singleLayerName[geom.type()]
            vl = QgsProject.instance().mapLayer(layerId)
            if vl is None:
                vl = self.addNewLayer(layerName, geom.type(), fields)
                if vl:
                    self.singleLayerId[geom.type()] = vl.id()
        else:
            layerName = "OSM " + ogrFeature.GetFieldAsString("osm_id")
            vl = self.addNewLayer(layerName, geom.type(), fields)

        if vl is not None:
            pr = vl.dataProvider()
            vl.startEditing()
            pr.addFeatures([fet])
            vl.commitChanges()

            # mise a jour etendue de la couche
            vl.updateExtents()
            self.go(item, False)

            return vl

    @staticmethod
    def add_fields(feature_definition):
        """Adds a predefined set of fields to an OGR feature definition.

        Args:
            feature_definition: Feature definition to add the fields to.
        """
        oFLD = ogr.FieldDefn("osm_id", ogr.OFTInteger64)
        feature_definition.AddFieldDefn(oFLD)
        oFLD = ogr.FieldDefn("class", ogr.OFTString)
        feature_definition.AddFieldDefn(oFLD)
        oFLD = ogr.FieldDefn("type", ogr.OFTString)
        feature_definition.AddFieldDefn(oFLD)
        oFLD = ogr.FieldDefn("name", ogr.OFTString)
        feature_definition.AddFieldDefn(oFLD)
        oFLD = ogr.FieldDefn("address", ogr.OFTString)
        feature_definition.AddFieldDefn(oFLD)
        oFLD = ogr.FieldDefn("extratags", ogr.OFTString)
        feature_definition.AddFieldDefn(oFLD)

    def doMask(self, item):
        mapcrs = self.plugin.canvas.mapSettings().destinationCrs()

        ogrFeature = item.data(Qt.ItemDataRole.UserRole)
        layerName = "OSM " + ogrFeature.GetFieldAsString("osm_id")
        geom = QgsGeometry.fromWkt(ogrFeature.GetGeometryRef().ExportToWkt())
        self.transform(geom)

        if geom.type() == QgsWkbTypes.GeometryType.PolygonGeometry:
            try:
                try:
                    from mask import aeag_mask
                except Exception:
                    from mask_plugin import aeag_mask

                aeag_mask.do(mapcrs, {geom}, "Mask " + layerName)
                self.go(item)

            except Exception:
                maskLayer = self.doLayer(item, True)
                maskLayer.loadNamedStyle(str(DIR_PLUGIN_ROOT / "resources" / "mask.qml"))
                maskLayer.triggerRepaint()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
