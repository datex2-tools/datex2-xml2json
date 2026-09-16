import json
import logging
from pathlib import Path

import geoparquet_io as gpio
import pyarrow as pa

logger = logging.getLogger(__name__)


# TODO Zeiten ?
target_schema = pa.schema(
    [
        ('publicationTime', pa.timestamp('ms', tz='Europe/Berlin')),
        ('publicationCreator', pa.string()),
        ('situationId', pa.string()),
        ('situationVersionTime', pa.timestamp('ms', tz='Europe/Berlin')),
        ('overallSeverity', pa.string()),
        ('confidentiality', pa.string()),
        ('informationStatus', pa.string()),
        ('id', pa.string()),
        ('version', pa.string()),
        ('situationRecordCreationTime', pa.timestamp('ms', tz='Europe/Berlin')),
        ('situationRecordVersionTime', pa.timestamp('ms', tz='Europe/Berlin')),
        ('overallStartTime', pa.timestamp('ms', tz='Europe/Berlin')),
        ('overallEndTime', pa.timestamp('ms', tz='Europe/Berlin')),
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
)


class GeoparquetRenderer:
    def __init__(self):
        pass

    def render(self, filename, a_geojson_dict: dict) -> None:
        geojson_filename = Path(filename).with_suffix('.geojson')
        with open(geojson_filename, 'w') as f:
            json.dump(a_geojson_dict, f, indent=2)
        table = gpio.convert(geojson_filename)

        arrays = []
        patable = table._table
        for field in target_schema:
            try:
                if field.name in patable.column_names:
                    # Cast existing column
                    arrays.append(patable[field.name].cast(field.type))
                else:
                    # Create null column of the correct type
                    arrays.append(pa.nulls(len(patable), type=field.type))
            except Exception:
                logger.exception(f'Exception handling field {field}')

        patable = pa.Table.from_arrays(arrays, schema=target_schema)
        table._table = patable
        table.write(filename)
