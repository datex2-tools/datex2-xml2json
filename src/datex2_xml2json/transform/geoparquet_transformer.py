import json
import logging
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile

import geoparquet_io as gpio
import pyarrow as pa

logger = logging.getLogger(__name__)

fields: list[tuple[str, pa.DataType]] = [
    ('publicationTime', pa.timestamp('ms', tz='UTC')),
    ('publicationCreator', pa.string()),
    ('publicationIdentifier', pa.string()),
    ('sourceIdentification', pa.string()),
    ('situationId', pa.string()),
    ('situationVersionTime', pa.timestamp('ms', tz='UTC')),
    ('overallSeverity', pa.string()),
    ('confidentiality', pa.string()),
    ('informationStatus', pa.string()),
    ('id', pa.string()),
    ('version', pa.string()),
    ('situationRecordCreationTime', pa.timestamp('ms', tz='UTC')),
    ('situationRecordVersionTime', pa.timestamp('ms', tz='UTC')),
    ('overallStartTime', pa.timestamp('ms', tz='UTC')),
    ('overallEndTime', pa.timestamp('ms', tz='UTC')),
    ('probabilityOfOccurrence', pa.string()),
    ('type', pa.string()),
    ('complianceOption', pa.string()),
    ('validityStatus', pa.string()),
    ('severity', pa.string()),
    ('description', pa.string()),
    ('roadworksType', pa.string()),
    ('roadworksName', pa.string()),
    ('heavyDutyTransportRestriction', pa.string()),
    ('routeRecommendation', pa.string()),
    ('applicableForTrafficDirection', pa.string()),
    ('placesAtWhichApplicable', pa.string()),
    ('cause', pa.string()),
    ('numberOfLanesRestricted', pa.int8()),
    ('numberOfOperationalLanes', pa.int8()),
    ('residualRoadWidth', pa.float32()),
    ('trafficConstrictionType', pa.string()),
    ('situationRecordSubtype', pa.string()),
    ('actionPlanIdentifier', pa.string()),
    ('operatorActionStatus', pa.string()),
    ('laneRestriction', pa.string()),  # TODO should be json
    ('laneStatusCoded', pa.string()),
    ('extendedLaneStatusCoded', pa.string()),
    ('hardShoulderStatus', pa.string()),
    ('residualHeight', pa.float64()),
    ('maxVehicleWeight', pa.float64()),  # TODO should only be set if valid for allCariageWays
    ('capacityRemaining', pa.int32()),
    ('originalNumberOfLanes', pa.int32()),
    ('numberOfObstructions', pa.int32()),
    ('forVehiclesWithCharacteristicsOf', pa.string()),  # TODO should be json
    ('validPeriods', pa.string()),  # TODO should be json
    ('subjectTypeOfWorks', pa.string()),
    ('applicableForTrafficType', pa.string()),
    ('roadworksDurationClassification', pa.string()),
    ('mobilityType', pa.string()),
    ('roadworksLayout', pa.string()),
    ('urlLinkAddress', pa.string()),
    ('roadNumber', pa.string()),
    ('roadName', pa.string()),
    ('fromASBSegmentStation', pa.float64()),
    ('fromASBSegmentFromNode', pa.string()),
    ('fromASBSegmentTowardsNode', pa.string()),
    ('toASBSegmentStation', pa.float64()),
    ('toASBSegmentFromNode', pa.string()),
    ('toASBSegmentTowardsNode', pa.string()),
    ('lengthAffected', pa.float64()),
    ('temporarySpeedLimit', pa.float32()),
    ('geometry', pa.binary()),
]

MOSTLY_FLAT_SITUATION_RECORD_TARGET_SCHEMA = pa.schema(fields)


class GeoparquetRenderer:
    """
    GeoparquetRenderer renders a GeoJSON file as a geoparquet file.
    Only properties matchting the supplied target_schema (default ist OSTLY_FLAT_SITUATION_RECORD_TARGET_SCHEMA)
    are exported.

    Note: As a workaround for https://github.com/geoparquet/geoparquet-io/issues/1152, all timestamp properties
      (according to the supplied target_schema) are converted to UTC strings. Note also, that this modification
      happend in situ, no deep copy of the GeoJSON dict is created.
    """

    def __init__(self, target_schema=MOSTLY_FLAT_SITUATION_RECORD_TARGET_SCHEMA):
        self.target_schema = target_schema

    def _get_timestamp_fieldnames(self):
        """
        Return a list of all fieldnames of self.target_schema, whose type is pyarrow.TimestampType.
        """
        fieldnames = []
        for index, field in enumerate(self.target_schema.types):
            if isinstance(field, pa.TimestampType):
                fieldnames.append(self.target_schema.names[index])
        return fieldnames

    def _set_timestamps_to_UTC(self, a_geojson_dict: dict):
        """
        Adds/subtracts optional timezone offset for
        all timestamp properties to assure they are in UTC.
        Note: timestamps without timezone adjustment are assumed to be
        in UTC already.
        This works around https://github.com/geoparquet/geoparquet-io/issues/1152
        and might be obsolete once the it's fix is released in a geoparquet-io
        version > 1.6.0
        """
        ts_fieldnames = self._get_timestamp_fieldnames()
        for feature in a_geojson_dict['features']:
            props = feature['properties']
            for ts_property in ts_fieldnames:
                if ts_property in props:
                    dt = datetime.fromisoformat(props[ts_property])
                    # Assume datetime was given in UTC if no timezone was specified
                    if not dt.tzinfo:
                        dt.replace(tzinfo=timezone.utc)
                    props[ts_property] = dt.astimezone(timezone.utc).isoformat()

    def _cast_fields_and_add_missing(self, table) -> None:
        """
        Replaces table's pyarrow table by a new one which
        has expected columns in expected order and type.
        """
        arrays = []
        patable = table._table
        for field in self.target_schema:
            try:
                if field.name in patable.column_names:
                    # Cast existing column
                    arrays.append(patable[field.name].cast(field.type))
                else:
                    # Create null column of the correct type
                    arrays.append(pa.nulls(len(patable), type=field.type))
            except Exception:
                logger.exception(f'Exception handling field {field}')

        patable = pa.Table.from_arrays(arrays, schema=self.target_schema)
        table._table = patable

    def _as_table(self, a_geojson_dict: dict):
        """
        Writes a_geojson_dict to a tempory file which is then read
        via geoparquet-io as pyarrow table.
        """
        with NamedTemporaryFile('w', delete_on_close=False) as f:
            json.dump(a_geojson_dict, f, indent=2)
            f.close()
            return gpio.convert(f.name)

    def render(self, filename, a_geojson_dict: dict) -> None:
        self._set_timestamps_to_UTC(a_geojson_dict)
        table = self._as_table(a_geojson_dict)
        self._cast_fields_and_add_missing(table)
        table.write(filename)
