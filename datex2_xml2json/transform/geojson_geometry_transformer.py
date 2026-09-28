import logging

from .base import ProcessingTransformer

logger = logging.getLogger(__name__)


class GeoJSONGeometryTransformer(ProcessingTransformer):
    def __init__(
        self,
        situation_record_json_pointer: str = 'payload/sitSituationPublication/situation/situationRecord',
        geom_container_element_json_point: str | None = None,
    ):
        super().__init__(situation_record_json_pointer)
        self.geom_container_element_json_point = geom_container_element_json_point

    def _extract_coordinates_from_gmlLineString(self, gmlLineString: dict) -> list:
        # Coordinate Order Confusion
        # There is often some confusion regarding the correct ordering of coordinate values.
        # While EPSG:4326 usually uses lat,lon ordering, and CRS84 (and GeoJSON) use lon/lat,
        # older GIS software might use lon/lat also for EPSG:4326.
        #
        # Assuming lat,lon in GML's posList when "WGS84 EPSG 4326" is set as srsName,
        # we swap coordinates for GeoJSON.
        is_lat_lon_order = False
        srsName = gmlLineString.get('srsName')
        if srsName is not None:
            if srsName not in {'WGS84 EPSG 4326', 'WGS84'}:
                logger.warning('Unhandled srsName %s, might need reprojection/ latlon order handling.', srsName)
            else:
                logger.info('Detected srsName "%s". We assume  latlon gmlLineString coordinates ordering for these.', srsName)
                is_lat_lon_order = True
        posList = gmlLineString.get('posList', '')

        zipped_coords = zip(*[iter(map(float, posList.split()))] * 2)
        if is_lat_lon_order:
            return [[lon, lat] for lat, lon in zipped_coords]
        else:
            return [[lon, lat] for lon, lat in zipped_coords]

    def _extract_line_geom(self, linearExtended: dict) -> None | dict:
        gmlLineString = linearExtended.get('gmlLineString')
        if gmlLineString is None:
            logger.warning('No linearExtended/gmlLineString')
            return None
        else:
            geometry = {
                'type': 'LineString',
                'coordinates': self._extract_coordinates_from_gmlLineString(gmlLineString),
            }
            return geometry

    def _extract_point_geom(self, pointCoordinates: dict | None) -> dict | None:
        if pointCoordinates is None:
            logger.warning('No pointCoordinates')
            return None
        else:
            geometry = {
                'type': 'Point',
                'coordinates': [
                    pointCoordinates.get('longitude'),
                    pointCoordinates.get('latitude'),
                ],
            }
            return geometry

    def _extract_multi_line_string(self, locationReference: dict) -> dict:
        locations = locationReference.get('locationContainedInGroup', {})

        lineStrings = []
        for location in locations:
            location_type = location.get('type')
            if not location_type == 'Linear':
                logger.warning(
                    'Unexpected location type %s, location is ignored',
                    location.get('type'),
                )
                continue
            coordinates = self._extract_coordinates_from_gmlLineString(location.get('gmlLineString', {}))
            if coordinates:
                lineStrings.append(coordinates)

        return {'type': 'MultiLineString', 'coordinates': lineStrings}

    def _extract_extendedLinear_geom(self, locationReference: dict) -> dict:
        """
        Some publications use a custom extension extendedLinear to provide linear geometries using a verbose
        xml encoding.
        We construct geojson geometries from these.
        Note: as this extension is not defined in standard XML schemas, we need to handle some type and cardinality issues,
        e.g. only a single intermediate point vs a list and lat/lon not beeing converted to floats during xml2json conversion.
        """
        linearByCoordinates = locationReference.get('extendedLinear', {}).get('linearByCoordinates', {})
        coordinates = []
        coordinates.append(
            [
                float(linearByCoordinates.get('start').get('longitude')),
                float(linearByCoordinates.get('start').get('latitude')),
            ]
        )
        intermediates = (
            [linearByCoordinates.get('intermediate')]
            if isinstance(linearByCoordinates.get('intermediate'), dict)
            else linearByCoordinates.get('intermediate', [])
        )
        for intermediate in intermediates:
            coordinates.append(
                [
                    float(intermediate.get('pointCoordinates').get('longitude')),
                    float(intermediate.get('pointCoordinates').get('latitude')),
                ]
            )
        coordinates.append(
            [
                float(linearByCoordinates.get('end').get('longitude')),
                float(linearByCoordinates.get('end').get('latitude')),
            ]
        )

        return {'type': 'LineString', 'coordinates': coordinates}

    def process(self, situation_record_wrapper: dict) -> None:
        if isinstance(situation_record_wrapper, dict) and len(situation_record_wrapper) == 1:
            situation_record = situation_record_wrapper.get(next(iter(situation_record_wrapper.keys())))
        else:
            situation_record = situation_record_wrapper
        if situation_record is None:
            return
        locationReference = situation_record.get('locationReference')
        if locationReference is None:
            return

        geom_container_element = (
            locationReference.get(self.geom_container_element_json_point)
            if self.geom_container_element_json_point is not None
            else locationReference
        )
        if isinstance(geom_container_element, dict):
            geoJsonGeometry = None
            if 'gmlLineString' in geom_container_element:
                geoJsonGeometry = self._extract_line_geom(geom_container_element)
            elif 'pointByCoordinates' in geom_container_element:
                geoJsonGeometry = self._extract_point_geom(geom_container_element.get('pointByCoordinates', {}).get('pointCoordinates'))
            elif 'locationContainedInGroup' in geom_container_element:
                geoJsonGeometry = self._extract_multi_line_string(geom_container_element)
            elif 'extendedLinear' in geom_container_element:
                geoJsonGeometry = self._extract_extendedLinear_geom(geom_container_element)
            elif 'coordinatesForDisplay' in geom_container_element:
                geoJsonGeometry = self._extract_point_geom(geom_container_element.get('coordinatesForDisplay'))

            if geoJsonGeometry is not None:
                geom_container_element['geoJsonGeometry'] = geoJsonGeometry


class GeoJSONGeometryTransformer_DATEXII_3_7(GeoJSONGeometryTransformer):
    def __init__(self):
        super().__init__(
            'payload/sitSituationPublication/situation/situationRecord',
            'linearExtended',
        )


class GeoJSONGeometryTransformer_Simplified(GeoJSONGeometryTransformer):
    def __init__(self):
        super().__init__('payload/situation/situationRecord', None)
