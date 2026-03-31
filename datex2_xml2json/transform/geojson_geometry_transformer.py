from .base import ProcessingTransformer
from datex2_xml2json.util import find

import logging
logger = logging.getLogger(__name__)

class GeoJSONGeometryTransformer(ProcessingTransformer):

    def __init__(self, situation_record_json_pointer:str = 'payload/sitSituationPublication/situation/situationRecord', geom_container_element_json_point:str|None = None):
        super().__init__(situation_record_json_pointer)
        self.geom_container_element_json_point = geom_container_element_json_point

    def _extract_coordinates_from_gmlLineString(self, posList:str) -> list:
        return [[lon, lat] for lat, lon in zip(*[iter(map(float, posList.split()))]*2)]

    def _extract_line_geom(self, linearExtended: dict) -> dict:
        gmlLineString = linearExtended.get('gmlLineString')
        if gmlLineString is None:
            logger.warning("No linearExtended/gmlLineString")
            return None
        else:
            srsName = gmlLineString.get('srsName')
            if srsName is None or not 'WGS84' in srsName:
                logger.warning("Unkown srsName %s", srsName)
            geometry = { "type": "LineString",
                "coordinates": self._extract_coordinates_from_gmlLineString(gmlLineString['posList'])
            }
            return geometry

    def _extract_point_geom(self, pointCoordinates: dict) -> dict:
        if pointCoordinates is None:
            logger.warning("No pointCoordinates")
            return None
        else:
            geometry = { "type": "Point",
                "coordinates": [pointCoordinates.get('longitude'), pointCoordinates.get('latitude')]
            }
            return geometry

    def _extract_multi_line_string(self, locationReference: dict)->dict:
        locations = locationReference.get('locationContainedInGroup',{})

        lineStrings = []
        for location in locations:
            if not location.get('type') == 'Linear':
                logger.warning("Unexpected location type %s, location is ignored", location.get('type'))
                continue
            lineStrings.append(self._extract_coordinates_from_gmlLineString(location.get('gmlLineString',{}).get('posList','')))
            
        return { "type": "MultiLineString", "coordinates": lineStrings}

    def _extract_extendedLinear_geom(self, locationReference: dict) -> dict:
        """
        Some publications use a custom extension extendedLinear to provide linear geometries using a verbose
        xml encoding.
        We construct geojson geometries from these.
        Note: as this extension is not defined in standard XML schemas, we need to handle some type and cardinality issues,
        e.g. only a single intermediate point vs a list and lat/lon not beeing converted to floats during xml2json conversion.
        """
        linearByCoordinates = locationReference.get('extendedLinear',{}).get('linearByCoordinates',{})
        coordinates = []        
        coordinates.append([float(linearByCoordinates.get('start').get('longitude')), float(linearByCoordinates.get('start').get('latitude')), ])
        intermediates = [linearByCoordinates.get('intermediate')] if isinstance(linearByCoordinates.get('intermediate'), dict) else linearByCoordinates.get('intermediate', [])
        for intermediate in intermediates:
            coordinates.append([float(intermediate.get('pointCoordinates').get('longitude')), float(intermediate.get('pointCoordinates').get('latitude')), ])
        coordinates.append([float(linearByCoordinates.get('end').get('longitude')), float(linearByCoordinates.get('end').get('latitude')), ])
        
        return { "type": "LineString", "coordinates": coordinates}
          

    def process(self, situation_record_wrapper: dict):
        if isinstance(situation_record_wrapper, dict) and len(situation_record_wrapper)== 1:
            situation_record = situation_record_wrapper.get(next(iter(situation_record_wrapper.keys())))
        else:
            situation_record = situation_record_wrapper
        locationReference = situation_record.get('locationReference', {})

        geom_container_element = locationReference.get(self.geom_container_element_json_point) if self.geom_container_element_json_point is not None else locationReference
        if isinstance(geom_container_element, dict):
            if 'gmlLineString' in geom_container_element:
                geoJsonGeometry = self._extract_line_geom(geom_container_element)
                geom_container_element['geoJsonGeometry'] = geoJsonGeometry
            elif 'pointByCoordinates' in geom_container_element:
                geoJsonGeometry = self._extract_point_geom(geom_container_element.get('pointByCoordinates',{}).get('pointCoordinates'))
                geom_container_element['geoJsonGeometry'] = geoJsonGeometry
            elif 'locationContainedInGroup' in geom_container_element:
                geoJsonGeometry = self._extract_multi_line_string(geom_container_element)
                geom_container_element['geoJsonGeometry'] = geoJsonGeometry
            elif 'extendedLinear' in geom_container_element:
                geoJsonGeometry = self._extract_extendedLinear_geom(geom_container_element)
                geom_container_element['geoJsonGeometry'] = geoJsonGeometry
            elif 'coordinatesForDisplay' in geom_container_element:
                geoJsonGeometry = self._extract_point_geom(geom_container_element.get('coordinatesForDisplay'))
                geom_container_element['geoJsonGeometry'] = geoJsonGeometry
            

class GeoJSONGeometryTransformer_DATEXII_3_7(GeoJSONGeometryTransformer):
    def __init__(self):
        super().__init__('payload/sitSituationPublication/situation/situationRecord', 'linearExtended')

class GeoJSONGeometryTransformer_Simplified(GeoJSONGeometryTransformer):
    def __init__(self):
        super().__init__('payload/situation/situationRecord', None)
