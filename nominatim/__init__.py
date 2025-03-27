"""
/***************************************************************************
Name	        :  plugin
Description          : Aide à la localisation
Date                 : March/13
copyright            : (C) 2011 by AEAG
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
 This script initializes the plugin, making it known to QGIS.

<p>Nominatim Search Courtesy of <a href="http://www.mapquest.com/" target="_blank">MapQuest</a> <img src="http://developer.mapquest.com/content/osm/mq_logo.png"></p>
data © OpenStreetMap contributors - <a href="www.openstreetmap.org/copyright">copyright</a>"

"""


def classFactory(iface):
    # load aeag_search class from file aeag_search
    from .nominatim import Nominatim

    return Nominatim(iface)
