import json

from qgis.PyQt.QtCore import Qt, QVariant, QUrl, QUrlQuery, QSettings
from qgis.PyQt.QtNetwork import QNetworkRequest

from qgis.core import (
    QgsProject,
    QgsApplication,
    QgsMessageLog,
    QgsNetworkAccessManager,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
)

limitSearchToExtent = False
gnOptions = ""


def getHttp(uri, params):
    nam = QgsNetworkAccessManager.instance()
    QgsApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        rq = QUrl(uri)
        q = QUrlQuery()
        for (k, v) in params.items():
            q.addQueryItem(k, v)

        rq.setQuery(q)
        req = QNetworkRequest(rq)
        try:
            reply = nam.blockingGet(req)
            resource = reply.content().data().decode("utf8")
            r = json.loads(resource)

            if isinstance(r, list):
                return r
            else:
                return [r]

        except Exception as e:
            for m in e.args:
                QgsMessageLog.logMessage(m, "Extensions")

    finally:
        QgsApplication.restoreOverrideCursor()

    return None


def osmSearchJson(params, options, options2):
    contents = str(options).strip()
    items = contents.split(" ")

    for (k, v) in options2.items():
        if k in ["viewbox"]:
            params["bounded"] = "1"
        params[k] = v

    pairs = []
    for item in items:
        pair = item.split("=", 1)
        if pair != [""] and pair != [] and len(pair) > 1:
            pairs.append(pair)

    for (k, v) in pairs:
        if (
            k
            in [
                "viewbox",
                "countrycodes",
                "limit",
                "exclude_place_ids",
                "addressdetails",
                "exclude_place_ids",
                "bounded",
                "routewidth",
                "osm_type",
                "osm_id",
            ]
            and not (k in options2.keys())
        ):
            params[k] = v

        if k in ["viewbox"]:
            params["bounded"] = "1"

    params["polygon_text"] = "1"
    params["format"] = "json"

    try:
        locale = QSettings().value("locale/userLocale")
        params["accept-language"] = locale[0:2]
    except:
        pass

    uri = "https://nominatim.openstreetmap.org/search"

    return getHttp(uri, params)


def osmFindNearbyJSON(params, options):
    uri = "https://nominatim.openstreetmap.org/reverse"
    params["format"] = "json"

    try:
        locale = QSettings().value("locale/userLocale")
        params["accept-language"] = locale[0:2]
    except:
        pass

    return getHttp(uri, params)


def osmSearch(canvas, txt):
    global gnOptions
    global limitSearchToExtent

    try:
        options = gnOptions
        options2 = {}
        if limitSearchToExtent:
            sourceCrs = canvas.mapSettings().destinationCrs()
            targetCrs = QgsCoordinateReferenceSystem("EPSG:4326")
            xform = QgsCoordinateTransform(sourceCrs, targetCrs, QgsProject.instance())
            geom = xform.transform(canvas.extent())
            vb = "{},{},{},{}".format(
                round(geom.xMinimum(), 4),
                round(geom.yMaximum(), 4),
                round(geom.xMaximum(), 4),
                round(geom.yMinimum(), 4),
            )
            options2 = {"viewbox": vb}

        params = {"q": txt, "addressdetails": "0"}
        return osmSearchJson(params, options, options2)

    except Exception:
        pass

    return None
