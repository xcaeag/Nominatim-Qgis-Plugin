Nominatim-Qgis-Plugin
=====================

Goal
----

Facilitate location by looking for places (cities, hydrography ...), based on Nominatim (http://wiki.openstreetmap.org/wiki/Nominatim_usage_policy), exposed by Mapquest (http://developer.mapquest.com/web/products/open/nominatim)

Configuration
-------------

Specific API options for "Nominatim" service can be set as "option1=value option2=value"
Thus, a limitation of the research in a given bounding box is configured by specifying (for example) the viewbox parameter : "viewbox=-1.85,46.35,3.90,42.50"
The other options are described online : http://open.mapquestapi.com/nominatim/

Usage
-----

- Activate the panel,
- Then enter the beginning of the name of the location. Confirm.
- The search can be limited to the current map extent.
- Selecting an item shows the corresponding geometry on the map.
- Double-click the item (or zoom button) moves to the place.

You can also create a layer (or enrich the layers 'OSM polygon', 'line' or 'point' depending on the configuration) from the selected object, a mask layer (from mask plugin if exists) when element is a polygon

Nominatim-Qgis-Plugin (Français)
--------------------------------

