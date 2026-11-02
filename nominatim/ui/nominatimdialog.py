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
from qgis.PyQt.QtCore import QEvent, Qt, pyqtSignal, QMetaType, QCoreApplication

# Compatibilité Qt5 / Qt6: certaines builds n'exposent pas QMetaType.Long
VQT = 6
try:
    OSM_ID_FIELD_TYPE = QMetaType.Long
except Exception:
    try:
        OSM_ID_FIELD_TYPE = QMetaType.LongLong
    except Exception:
        VQT = 5
        from qgis.PyQt.QtCore import QVariant

        OSM_ID_FIELD_TYPE = QVariant.LongLong

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
            self.rbLine.reset()
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

        self.rbLine = QgsRubberBand(
            self.plugin.canvas, QgsWkbTypes.GeometryType.LineGeometry
        )
        self.rbLine.setColor(QColor(50, 50, 255, 100))
        self.rbLine.setWidth(4)

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

        header = self.tableResult.horizontalHeader()
        header.setSectionResizeMode(
            # QHeaderView.ResizeMode.ResizeToContents
            QHeaderView.ResizeMode.Interactive
            # QHeaderView.ResizeMode.Stretch
        )
        # header.setStretchLastSection(True)
        self.tableResult.setColumnWidth(0, 350)

        try:
            self.editSearch.setText(self.plugin.lastSearch)
        except Exception:
            pass

    @staticmethod
    def tr(message):
        return QCoreApplication.translate("nominatim", message)

    def cellEntered(self, row, col):
        item = self.tableResult.item(row, 0)

        self.rbPoint.reset()
        self.rbLine.reset()
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

    @staticmethod
    def resultFields():
        fields = QgsFields()
        if VQT == 6:
            fields.append(QgsField("osm_id", OSM_ID_FIELD_TYPE))
            fields.append(QgsField("class", QMetaType.QString))
            fields.append(QgsField("type", QMetaType.QString))
            fields.append(QgsField("name", QMetaType.QString))
            fields.append(QgsField("address", QMetaType.QString))
            fields.append(QgsField("extratags", QMetaType.QString))
            fields.append(QgsField("namedetails", QMetaType.QString))
        else:
            fields.append(QgsField("osm_id", OSM_ID_FIELD_TYPE))
            fields.append(QgsField("class", QVariant.String))
            fields.append(QgsField("type", QVariant.String))
            fields.append(QgsField("name", QVariant.String))
            fields.append(QgsField("address", QVariant.String))
            fields.append(QgsField("extratags", QVariant.String))
            fields.append(QgsField("namedetails", QVariant.String))
        return fields

    @staticmethod
    def buildGeometry(item):
        wkt = item.get("geotext")
        # QgsMessageLog.logMessage(wkt, "Extensions")

        if wkt is None and "boundingbox" in item:
            bbox = item["boundingbox"]
            wkt = "POLYGON(({b[2]} {b[0]}, {b[2]} {b[1]}, {b[3]} {b[1]}, {b[3]} {b[0]}, {b[2]} {b[0]}))".format(
                b=bbox
            )
        if wkt is None:
            lat = item["lat"]
            lng = item["lon"]
            wkt = "POINT({} {})".format(lng, lat)

        geom = QgsGeometry.fromWkt(wkt)
        if geom is None or geom.isEmpty():
            raise ValueError("Unable to build geometry from Nominatim result")
        return geom

    def populateRow(self, item, idx):
        osm_id = item.get("osm_id")
        name = item["display_name"]

        className = item["class"]

        try:
            typeName = QApplication.translate("nominatim", item["type"], None)
        except Exception:
            typeName = ""

        address = tools.dict_to_hstore_string(item, "address")
        extratags = tools.dict_to_hstore_string(item, "extratags")
        namedetails = tools.dict_to_hstore_string(item, "namedetails")

        geom = self.buildGeometry(item)

        feature = QgsFeature()
        feature.setFields(self.resultFields())
        feature.setGeometry(geom)
        feature.setAttribute("osm_id", osm_id)
        feature.setAttribute("class", className)
        feature.setAttribute("type", typeName)
        feature.setAttribute("name", name)
        feature.setAttribute("address", address)
        feature.setAttribute("extratags", extratags)
        feature.setAttribute("namedetails", namedetails)

        itemWidget = QTableWidgetItem(name)
        itemWidget.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        itemWidget.setData(Qt.ItemDataRole.UserRole, feature)
        self.tableResult.setItem(idx, 0, itemWidget)

        itemLibelle = QTableWidgetItem(
            "{} {}".format(self.tr(className), self.tr(typeName))
        )
        itemLibelle.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.tableResult.setItem(idx, 1, itemLibelle)

        itemWidget.setToolTip("{}/{} - {}".format(className, typeName, name))
        if className == "boundary":
            itemWidget.setForeground(QColor(110, 50, 50))
        if className == "place":
            itemWidget.setForeground(QColor(80, 80, 80))
        if className in ("water", "waterway"):
            itemWidget.setForeground(QColor(50, 100, 200))
        if className in ("natural",):
            itemWidget.setForeground(QColor(20, 110, 50))
        if className in ("landuse",):
            itemWidget.setForeground(QColor(30, 90, 60))

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
        feature = item.data(Qt.ItemDataRole.UserRole)
        geom = QgsGeometry(feature.geometry())
        self.transform(geom)

        if geom.type() == QgsWkbTypes.GeometryType.PointGeometry:
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

        bbox = geom.boundingBox()
        rubberRect = QgsRectangle(
            bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum()
        )
        return rubberRect

    def showItem(self, item):
        if not item:
            return

        feature = item.data(Qt.ItemDataRole.UserRole)
        geom = QgsGeometry(feature.geometry())
        self.transform(geom)

        self.rbPoint.reset()
        self.rbLine.reset()
        self.rbPolygon.reset()

        if geom.type() == QgsWkbTypes.GeometryType.PointGeometry:
            self.rbPoint.setToGeometry(geom, None)
        elif geom.type() == QgsWkbTypes.GeometryType.LineGeometry:
            self.rbLine.setToGeometry(geom, None)
        else:
            if not self.plugin.canvas.extent().contains(geom.boundingBox()):
                geom = geom.intersection(
                    QgsGeometry.fromRect(self.plugin.canvas.extent())
                )
            self.rbPolygon.setToGeometry(geom, None)

    def go(self, item, zoom=True):
        self.rbPoint.reset()
        self.rbLine.reset()
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

        feature = item.data(Qt.ItemDataRole.UserRole)
        geom = QgsGeometry(feature.geometry())
        self.transform(geom)

        fields = self.resultFields()

        fet = QgsFeature()
        fet.initAttributes(len(fields))
        fet.setFields(fields)
        fet.setGeometry(geom)
        fet.setAttribute("osm_id", feature["osm_id"])
        fet.setAttribute("class", feature["class"])
        fet.setAttribute("type", feature["type"])
        fet.setAttribute("name", feature["name"])
        fet.setAttribute("address", feature["address"])
        fet.setAttribute("extratags", feature["extratags"])
        fet.setAttribute("namedetails", feature["namedetails"])

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
            layerName = "OSM " + str(feature["osm_id"])
            vl = self.addNewLayer(layerName, geom.type(), fields)

        if vl is not None:
            pr = vl.dataProvider()
            vl.startEditing()
            pr.addFeatures([fet])
            vl.commitChanges()

            vl.updateExtents()
            self.go(item, False)

            return vl

    def doMask(self, item):
        mapcrs = self.plugin.canvas.mapSettings().destinationCrs()

        feature = item.data(Qt.ItemDataRole.UserRole)
        layerName = "OSM " + str(feature["osm_id"])
        geom = QgsGeometry(feature.geometry())
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
                maskLayer.loadNamedStyle(
                    str(DIR_PLUGIN_ROOT / "resources" / "mask.qml")
                )
                maskLayer.triggerRepaint()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
