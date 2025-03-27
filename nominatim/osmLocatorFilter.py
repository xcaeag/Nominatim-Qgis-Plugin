"""
crash QGis. Nonfonctional.
"""

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsLocatorFilter,
    QgsLocatorResult,
    QgsProject,
)
from qgis.PyQt.QtCore import pyqtSignal

from nominatim.logic import tools


class OsmLocatorFilter(QgsLocatorFilter):
    resultProblem = pyqtSignal(str)

    def __init__(self, iface, plugin):
        self.iface = iface
        self.plugin = plugin

        super(QgsLocatorFilter, self).__init__()

    def name(self):
        return self.__class__.__name__

    def clone(self):
        return OsmLocatorFilter(self.iface, self.plugin)

    def displayName(self):
        return "OSM search"

    def prefix(self):
        return "osm"

    def fetchResults(self, search, context, feedback):
        try:
            if len(search.strip()) < 4 or search[-1] not in (" ", "\n"):
                return

            r = tools.osmSearch(self.iface.mapCanvas(), search.strip())

            for item in r:
                wkt = item["geotext"]

                """
                id = item["place_id"]
                name = item["display_name"]
                className = item["class"]
                typeName = item["type"]
                """

                sourceCrs = QgsCoordinateReferenceSystem("EPSG:4326")
                targetCrs = self.plugin.canvas.mapSettings().destinationCrs()
                xform = QgsCoordinateTransform(
                    sourceCrs, targetCrs, QgsProject.instance()
                )

                try:
                    bbox = item["boundingbox"]
                    wkt = "POLYGON(({b[2]} {b[0]}, {b[2]} {b[1]}, {b[3]} {b[1]}, {b[3]} {b[0]}, {b[2]} {b[0]}))".format(
                        b=bbox
                    )
                except Exception:
                    if wkt is None:
                        lat = item["lat"]
                        lng = item["lon"]
                        wkt = "POINT({} {})".format(lng, lat)

                try:
                    geom = QgsGeometry.fromWkt(wkt)
                    geom.transform(xform)

                    data = {
                        "id": item["place_id"],
                        "geom": geom,
                    }

                    result = QgsLocatorResult()
                    result.filter = self
                    result.displayString = "{} {}".format(
                        item["display_name"],
                        item["type"],
                    )
                    result.userData = data
                    self.resultFetched.emit(result)
                except Exception:
                    pass

        except Exception as err:
            self.resultProblem.emit("{}".format(err))

    def triggerResult(self, result):
        try:
            data = result.userData
            geom = data["geom"]
            self.iface.mapCanvas().setExtent(geom.boundingBox(), False)
            self.iface.mapCanvas().refresh()
        except Exception:
            pass
