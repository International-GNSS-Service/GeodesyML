# GeodesyML

[![Build Status](https://travis-ci.org/GeoscienceAustralia/GeodesyML.svg?branch=master)](https://travis-ci.org/GeoscienceAustralia/GeodesyML)

## Background
The eGeodesy Logical Model, developed by the Permanent Committee on Geodesy (PCG) of the Australian and New Zealand Intergovernmental Committee on Surveying and Mapping (ICSM), defines a technology-independent language to model the core business processes, entities, and relationships within the geodetic domain.

GeodesyML, an XML implementation of the eGeodesy model, is a Geography Markup Language (GML) application schema for transfer of geodetic information. For more information about eGeodesy and GeodesyML, see http://www.geodesyml.org.

Geoscience Australia (GA) is adopting GeodesyML as the standard for exchange of geodetic information.

## About GeodesyML
The Geodesy Markup Language (GeodesyML) is a standard way of describing (encoding) and sharing geodetic data and metadata. In the same way people from all over the world speak different languages, so do geodesists; for example, some people use the term 'GNSS station' and others use the term 'GNSS site'. GeodesyML is a common language. By mapping your database to GeodesyML, when your data is shared with others, it is easy for the user to discover and combine with other data. For more information, please visit www.geodesyml.org.

## Documentation

GeodesyML [GitHub Pages](http://geoscienceaustralia.github.io/GeodesyML-Github-Pages) contain
HTML documentation with diagrams for GeodesyML and all supporting schemas.

*Note:* `gh-pages` branch is very large, so to clone this repository and bring down only `master` branch, use:

```
git clone -b master --single-branch https://github.com/GeoscienceAustalia/GeodesyML
```

You can later fetch the branches you are interested in using:

```
git remote set-branches --add origin branch-1 branch-2
git fetch origin
```

## Contact Information

Contributions, suggestions, and bug reports are welcome!

Please feel free to contact us through GitHub or directly via email at geodesy@ga.gov.au.

-Lazar Bodor (lazar.bodor@ga.gov.au)
