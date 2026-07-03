# DATEX2-XML2JSON (Proof of Concept)

This tool provides a PoC converter to convert DATEXII XML to JSON. 

As output format, the following formats are supported

* DATEXII v3.7 JSON
* a custom DATEXII 3.7 variation which deviates from official schema but is easier to process (see below)
* a (mostly) flattened GeoJSON
* a geoparquet format derived from above mostly flatt GeoJSON format.

Curently, supported DATEXII input is limited to `SituationPublication`s in DATEXII v2.x.

Note: This tool uses XML schemas to derive cardinality and type information for the JSON conversion to JSON.
Custom extensions might require supplying specific schemas to support this conversion.

## Preliminaries

This project requires Python >= 3.12.

Install the needed dependencies via 

```
$ pip install -r requirements.txt
```

### Usage

Below, you find a couple of sample formats to generate different output formats.

If you encounter issues, i.e. an invalid DATEXII v3.7, you might consult the [troubleshooting guide](doc/troubleshooting.md). 
If this is does not help, please open an issue and supply a minimal DATEXII XML sample and your command to reproduce the issue.

In case you fixed an error or want to contribute, please create an issue as well and feel free to send a PR, thanks.

#### DATEXII v3.7
To convert a DATEXII v2.2 XML publication to DATEXII v3.7, use the following command. It will create out/situation_publication.json and will validate it after generation.

```sh 
python -m datex2_xml2json.main -V situation_publication.xml
```

#### DATEXII (mostly) flat GeoJSON

To convert a DATEXII v2.2 XML publication to a (mostly) flat GeoJSON file, use the following command. It will create out/situation_publication.geojson.

```sh
python -m datex2_xml2json.main -f geojson situation_publication.xml
```

#### DATEXII Geoparquet

To convert a DATEXII v2.2 XML publication to a Geoparquet file, use the following command. It will create out/situation_publication.geoparquet.

```sh
python -m datex2_xml2json.main -f geoparquet situation_publication.xml
```

#### DATEXII v3.7 JSON Lite

To convert a DATEXII v2.2 XML publication to a DATEXII v3.7 JSON "Lite" format, use the following command. It will create out/situation_publication.lite.json.


Warning: the JSON resulting from this conversion does not comply with DATEXII JSON Schema. 

Some differences:
* this format does not use the DATEXII part 15 xsi-type dependant wrapper objects, but keeps the `xsi:type` attribute as property `type`.
* it does not wrap text objects in `value` wrappers
* we try to create a `geoJsonGeometry` location from `gmlLineString` locations. For `locationContainedInGroup`, we collect all linestrings in an `MultiLineString` object

#### DATEXII v2.2 RAW JSON

To convert a DATEXII v2.2 XML publication to an intermediate JSON which just converts the XML to a JSON file using the DATEXII v2.2 schema, use the following command. It will create out/situation_publication.raw.json.
```sh
python -m datex2_xml2json.main -f raw situation_publication.xml
```

#### WAZE CIFS Format

To convert a DATEXII v2.2 XML situation publication to [WAZE CIFS Format](https://developers.google.com/waze/data-feed/cifs-specification?hl=de), use the following command. It will create out/situation_publication.cifs.json.

```sh
python -m datex2_xml2json.main -f cifs situation_publication.xml
```

To validate the generated json against the CIFS schema, supply the -v switch.
```sh
python -m datex2_xml2json.main -f cifs -v situation_publication.xml
```

Note: currently, this converter does not handle validityPeriods. I.E. recurring events at specific days/hours are not yet mapped to CIFS schedule.
