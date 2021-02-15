# Nominatim-Qgis-Plugin

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Flake8](https://img.shields.io/badge/flake8-enabled-yellowgreen)](https://flake8.pycqa.org/)

## Nominatim-Qgis-Plugin :gb:

### Goal

Facilitate location by looking for places (cities, hydrography ...), based on Nominatim (https://operations.osmfoundation.org/policies/nominatim/)

### Configuration

Specific API options for "Nominatim" service can be set as "option1=value option2=value"
Thus, a limitation of the research in a given bounding box is configured by specifying (for example) the viewbox parameter : "viewbox=-1.85,46.35,3.90,42.50"
The other options are described online : https://wiki.openstreetmap.org/wiki/Nominatim

### Usage

- Activate the panel,
- Then enter the beginning of the name of the location. Confirm.
- The search can be limited to the current map extent.
- Selecting an item shows the corresponding geometry on the map.
- Double-click the item (or zoom button) moves to the place.

You can also create a layer (or enrich the layers 'OSM polygon', 'line' or 'point' depending on the configuration) from the selected object, a mask layer (from mask plugin if exists) when element is a polygon

## Nominatim-Qgis-Plugin (Français) :fr:

Aide à la localisation

### Objectif

Faciliter la localisation par la recherche de lieux (villes, hydrographie...), basé sur l'outil Nominatim (https://operations.osmfoundation.org/policies/nominatim/)

### Configuration

Les options propres à l'API REST "nominatim" peuvent être paramétrées sous la forme "option1=valeur option2=valeur"
Ainsi, une limitation de la recherche à une étendue rectangulaire donnée se configure de la façon suivante : "viewbox=-1.85,46.35,3.90,42.50"
Les autres options sont décrites en ligne : https://wiki.openstreetmap.org/wiki/Nominatim

### Usage

- Activez l'onglet,
- Puis saisissez le début du nom du lieu recherché, validez.
- La recherche peut se limiter à l'emprise géographique courante.
- Le survol d'un élément de réponse affiche l'emprise géographique correspondante sur la carte.
- Un double-clic sur l'item (ou bouton zoomer) se positionne sur le lieu en question.

Vous pouvez également créer une couche (ou enrichir les couches 'OSM polygon', 'line' ou 'point', selon la configuration) à partir de l'objet sélectionné, un masque (issue du plugin mask si il est actif) lorsqu'il s'agit d'un polygone.
