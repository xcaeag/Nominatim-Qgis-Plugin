import json
import os

from qgis.PyQt.QtCore import Qt, QVariant, QUrl, QUrlQuery, QSettings
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QLocale, QUrl, QDir
from qgis.PyQt.QtGui import QDesktopServices

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
    params["extratags"] = "1"
    params["addressdetails"] = "1"

    try:
        locale = QSettings().value("locale/userLocale")
        params["accept-language"] = locale[0:2]
    except:
        pass

    uri = "https://nominatim.openstreetmap.org/search"

    return getHttp(uri, params)


def osmFindNearbyJSON(params):
    uri = "https://nominatim.openstreetmap.org/reverse"
    params["format"] = "json"

    results = []
    locale = QSettings().value("locale/userLocale")
    params["accept-language"] = locale[0:2]
    params["polygon_text"] = "1"
    for zoom in ("11", "9"):
        try:
            params["zoom"] = zoom
            result = getHttp(uri, params)
            results = results + result
        except:
            pass

    return results

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


def dict_to_hstore_string(d):
    """Returns an hstore string representation of the dictionary.

    Note: The dictionary must be flat or the resulting hstore string
          might be erroneous.

    Args:
        d (dict): A flat dictionary

    Returns:
        str: A hstore string representation of the dict
    """

    hstore_strings = []
    for key, value in d.items():
        hstore_string = f'"{key}"=>"{value}"'
        hstore_strings.append(hstore_string)
    return ",".join(hstore_strings)

"""
    A problem it seems in the 'utils' module of QGis.
    The showPluginHelp function mixes '/' and '', and the Qt Url produced is invalid, under windows.
    This code, while waiting for a QGis API patch.
"""
def showPluginHelp(packageName: str = None, filename: str = "index", section: str = ""):
    try:
        source = ""
        if packageName is None:
            import inspect
            source = inspect.currentframe().f_back.f_code.co_filename
        else:
            import sys
            source = sys.modules[packageName].__file__
    except:
        return
    path = os.path.dirname(source)
    locale = str(QLocale().name())
    helpfile = os.path.join(path, filename + "-" + locale + ".html")
    if not os.path.exists(helpfile):
        helpfile = os.path.join(path, filename + "-" + locale.split("_")[0] + ".html")
    if not os.path.exists(helpfile):
        helpfile = os.path.join(path, filename + "-en.html")
    if not os.path.exists(helpfile):
        helpfile = os.path.join(path, filename + "-en_US.html")
    if not os.path.exists(helpfile):
        helpfile = os.path.join(path, filename + ".html")
    if os.path.exists(helpfile):
        url = QDir.fromNativeSeparators(helpfile)
        if section != "":
            url = url + "#" + section
        if not QDesktopServices.openUrl(QUrl("file:///"+url, QUrl.TolerantMode)):
            QDesktopServices.openUrl(QUrl("file://"+url, QUrl.TolerantMode))
