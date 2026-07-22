from dataclasses import dataclass
from typing import Callable


@dataclass
class TransformationRules:
    renamings: dict[str, str]
    value_transforms: dict[str, Callable]
    keys_to_drop: dict[str, str | None]
    type_mappings: dict[str, str]
    keys_to_pull_up: list[str]


def push_down_vms_configuration(vms: dict) -> dict:
    vmsConfiguration = {}
    if 'numberOfPictogramDisplayAreas' in vms:
        vmsConfiguration['numberOfDisplayAreas'] = vms.pop('numberOfPictogramDisplayAreas')
    if 'vmsPictogramDisplayCharacteristics' in vms:
        displays = vms.pop('vmsPictogramDisplayCharacteristics')
        vmsConfiguration['displayArea'] = [
            {
                'displayArea': {'vmsPictogramDisplayArea': displayArea.get('vmsPictogramDisplayCharacteristics')},
                'displayAreaIndex': displayArea.pop('displayAreaIndex'),
            }
            for displayArea in displays
            if 'vmsPictogramDisplayCharacteristics' in displayArea
        ]
    if len(vmsConfiguration) > 0:
        vms['vmsConfiguration'] = vmsConfiguration
    return vms


INFRASTRUCTURE_DESCRIPTOR_VALUES = {
    'atMotorwayInterchange',
    'atRestArea',
    'atServiceArea',
    'atTollPlaza',
    'atTunnelEntryOrExit',
    'inGallery',
    'inTunnel',
    'onBridge',
    'onConnector',
    'onElevatedSection',
    'onFlyover',
    'onIceRoad',
    'onLevelCrossing',
    'onLinkRoad',
    'onRoundabout',
    'onTheRoadway',
    'onUndergroundSection',
    'onUnderpass',
    'withinJunction',
}
POSITION_ON_CARRIAGEWAY_VALUES = {
    'onTheLeft',
    'onTheRight',
    'inTheCentre',
}
GEOGRAPHIC_CHARACATERISTIC_VALUES = {
    'aroundABendInRoad',
    'onBorder',
    'onPass',
    'overCrestOfHill',
}


def transform_supplementaryPositionalDescription(v: dict):
    # locationDescriptior needs to be split in multiple properties
    if 'locationDescriptor' in v:
        locationDescriptors = v.pop('locationDescriptor')
        for ld_value in locationDescriptors:
            if ld_value in INFRASTRUCTURE_DESCRIPTOR_VALUES:
                if 'infrastructureDescriptor' in v:
                    logger.warning(
                        'Conflicting values for infrastructureDescriptor (%s vs %s), keeping former.',
                        v['infrastructureDescriptor'],
                        ld_value,
                    )
                    continue
                v['infrastructureDescriptor'] = {'value': ld_value}
            if ld_value in POSITION_ON_CARRIAGEWAY_VALUES:
                if 'positionOnCarriageway' in v:
                    logger.warning(
                        'Conflicting values for positionOnCarriageway (%s vs %s), keeping former.',
                        v['positionOnCarriageway'],
                        ld_value,
                    )
                    continue
                v['positionOnCarriageway'] = {'value': ld_value}
            if ld_value in GEOGRAPHIC_CHARACATERISTIC_VALUES:
                if 'geographicDescriptor' in v:
                    logger.warning(
                        'Conflicting values for geographicDescriptor (%s vs %s), keeping former.',
                        v['geographicDescriptor'],
                        ld_value,
                    )
                    continue
                v['geographicDescriptor'] = {'value': ld_value}

    if 'carriageway' in v:
        for c in v['carriageway']:
            lengthAffected = c.pop('lengthAffected', None)
            if lengthAffected is not None:
                return v | {'lengthAffected': float(lengthAffected)}

    return v


def wrap_lroffset(lr_dict: dict):
    new_dict = {}
    for k in lr_dict:
        if k == 'openlrPositiveOffset':
            new_dict['openlrOffsets'] = {k: lr_dict[k]}
        else:
            new_dict[k] = lr_dict[k]
    return new_dict


def transform_alertc(v: dict, shouldWrapWithValue: bool):
    """
    In v2, alertCDirection did not distinguish between encoding and affected direction.
    We assume, as apparently NDW mandated explictly, that for encoding matches affected direction and,
    in case of both or unknown affected direction, encoding is positive.
    """
    currentAlertCDirectionCoded = v['alertCDirectionCoded']
    if 'alertCDirectionCoded' in v:
        v['alertCAffectedDirection'] = 'aligned' if currentAlertCDirectionCoded in ['positive', 'negative'] else v['alertCDirectionCoded']
        v['alertCDirectionCoded'] = 'positive' if currentAlertCDirectionCoded in ['both', 'unknown'] else v['alertCDirectionCoded']
        if shouldWrapWithValue:
            v['alertCAffectedDirection'] = {'value': v['alertCAffectedDirection']}
            v['alertCDirectionCoded'] = {'value': v['alertCDirectionCoded']}

    return v


DEFAULT_LANGUAGE = 'de'


class TransformationRuleFactory:
    ACCIDENT_TYPE_MAPPINGS = {
        'seriousAccident': 'seriousInjuryOrFatalAccident',
        'multivehicleAccident': 'multipleVehicleAccident',
        'earlierAccident': 'accident',  # TODO: perhaps this should be another situationRecord?
    }

    CAUSE_TYPE_MAPPINGS = {
        'shearWeightOfTraffic': 'other',
        'earlierAccident': 'earlierIncident',
        'congestion': 'abnormalTraffic',
    }

    VEHICLE_OBSTRUCTION_TYPE_MAPPINGS = {
        'brokenDownBus': 'brokenDownVehicle',
        'brokenDownHeavyLorry': 'brokenDownVehicle',
        'slowMovingMaintenanceVehicle': 'slowVehicle',
        'trackLayingVehicle': 'trackedVehicle',
        'vehicleStuckUnderBridge': 'vehicleStuck',
        'saltingOrGrittingVehicleInUse': 'other',
        'snowplough': 'other',
    }

    # see https://docs.ndw.nu/en/dataformaten/datex2-v2.3/conversie-naar-v3/#generalobstruction-maps-to-generalobstruction
    OBSTRUCTION_TYPE_MAPPINGS = {
        'recklessDriver': 'other',
        'houseFire': 'other',
        'highSpeedChase': 'other',
    }

    CAR_PARK_STATUS_TO_SERVICE_TYPE_MAPPINGS = {
        'carParkFull': 'restAreaOvercrowdedDriveToAnotherRestArea',
        'carParkClosed': 'restAreaClosed',
        'noMoreParkingSpacesAvailable': 'restAreaOvercrowdedDriveToAnotherRestArea',
        'serviceAreaFull': 'serviceAreaOvercrowdedDriveToAnotherServiceArea',
    }

    # Type mappings convert { ..., "@xsi:type": "<key>" } to { "<value>": { ... }}
    datex_xml_2_json_xsitype_mappings = {
        'AbnormalTraffic': 'sitAbnormalTraffic',
        'Accident': 'sitAccident',
        'AnimalPresenceObstruction': 'sitAnimalPresenceObstruction',
        'AuthorityOperation': 'sitAuthorityOperation',
        'Conditions': 'sitConditions',
        'ConstructionWorks': 'sitConstructionWorks',
        'DisturbanceActivity': 'sitDisturbanceActivity',
        'EnvironmentalObstruction': 'sitEnvironmentalObstruction',
        'EquipmentOrSystemFault': 'sitEquipmentOrSystemFault',
        'GeneralObstruction': 'sitGeneralObstruction',
        'GeneralInstructionOrMessageToRoadUsers': 'sitGeneralInstructionOrMessageToRoadUsers',
        'GeneralNetworkManagement': 'sitGeneralNetworkManagement',
        'GenericSituationRecord': 'sitGenericSituationRecord',
        'InfrastructureDamageObstruction': 'sitInfrastructureDamageObstruction',
        'MaintenanceWorks': 'sitMaintenanceWorks',
        'NonWeatherRelatedRoadConditions': 'sitNonWeatherRelatedRoadConditions',
        'PoorEnvironmentConditions': 'sitPoorEnvironmentConditions',
        'PublicEvent': 'sitPublicEvent',
        'RoadOperatorServiceDisruption': 'sitRoadOperatorServiceDisruption',
        'RoadOrCarriagewayOrLaneManagement': 'sitRoadOrCarriagewayOrLaneManagement',
        'RoadsideAssistance': 'sitRoadsideAssistance',
        'ReroutingManagement': 'sitReroutingManagement',
        'WeatherRelatedRoadConditions': 'sitWeatherRelatedRoadConditions',
        'ServiceDisruption': 'sitServiceDisruption',
        # see for CarParks https://docs.ndw.nu/en/dataformaten/datex2-v2.3/conversie-naar-v3/#carparks-maps-to-servicedisruption
        'CarParks': 'sitServiceDisruption',
        # TODO: need to set serviceDisruptionType
        'RoadsideServiceDisruption': 'sitServiceDisruption',
        'SpeedManagement': 'sitSpeedManagement',
        'TransitInformation': 'sitTransitInformation',
        'VehicleObstruction': 'sitVehicleObstruction',
        'WinterDrivingManagement': 'sitWinterDrivingManagement',
        'Linear': 'locSingleRoadLinearLocation',
        'NonOrderedLocationGroupByList': 'locLocationGroupByList',
        'SituationPublication': 'sitSituationPublication',
        'TpegNonJunctionPoint': 'locTpegNonJunctionPoint',
        'AreaDestination': 'locAreaDestination',
        'AlertCMethod4Linear': 'locAlertCMethod4Linear',
        'Point': 'locPointLocation',
        'Area': 'locAreaLocation',
        'ItineraryByIndexedLocations': 'locItineraryByIndexedLocations',
        'TpegGeometricArea': 'locTpegGeometricArea',
        'TpegNamedOnlyArea': 'locTpegNamedOnlyArea',
        'OpenlrPolygonLocationReference': 'locOpenlrPolygonLocationReference',
        'DistanceFromLinearElementReferent': 'locDistanceFromLinearElementReferent',
        # VMS
        'VmsTablePublication': 'vmsVmsTablePublication',
        'TpegSimplePoint': 'locTpegSimplePoint',
        'AlertCMethod4Point': 'locAlertCMethod4Point',
        # Parking
        'ParkingStatusPublication': 'prkParkingStatusPublication',
        'SpaceStatus': 'prkSpaceStatus',
        'PlaceStatus': 'prkPlaceStatus',
    }

    def __init__(self):
        pass

    def xmlv2_to_json(self):
        renamings = {
            # xml2json artifact
            '$': 'value',
            # Assumed DATEXII 2.2->DATEX3.7 naming changes
            'd2LogicalModel': 'payload',
            'affectedCarriagewayAndLanes': 'carriageway',
            'groupOfLocations': 'locationReference',
            'locationForDisplay': 'coordinatesForDisplay',
            'openlrCoordinate': 'openlrCoordinates',
            'area': 'areaLocation',
            'openlrExtendedLinear': 'openlrLinear',
            'openlrLowestFRCToNextLRPoint': 'openlrLowestFrcToNextLRPoint',
            'roadworksDuration': 'roadworksDurationClassification',
            'roadsideServiceDisruptionType': 'serviceDisruptionType',
            'carParkStatus': 'serviceDisruptionType',
            # VMS
            'vmsUnitTable': 'vmsControllerTable',
            'vmsUnitRecord': 'vmsController',
            'vmsUnitIdentifier': 'externalIdentifier',
            'vmsUnitRecordExtension': 'vmsVmsControllerExtensionG',
            'vmsRecord': 'vms',
            'vmsRecordExtension': 'vmsVmsExtensionG',
            'vmsPhysicalMounting': 'physicalSupport',
            'vmsDescription': 'description',
            'pictogramDisplayAreaIndex': 'displayAreaIndex',
            'vmsUnitTableIdentification': 'vmsControllerTableIdentification',
            'vmsPictogramDisplayCharacteristicsExtension': 'vmsPictogramDisplayAreaExtensionG',
            #
            '@modelBaseVersion': 'modelBaseVersion',
            '@id': 'id',
            '@index': 'index',
            '@lang': 'lang',
            '@version': 'version',
            '@targetClass': 'targetClass',
            '@xsi:type': 'type',
        }

        def add_def_lang_if_missing(v):
            return v if isinstance(v, dict) else {'lang': DEFAULT_LANGUAGE, 'value': v}

        def handle_datex2_gml_extensions(v):
            if 'coordinates' in v:
                pass
            else:
                posList = v.get('posList')
            return ({'locGmlLineString': {'posList': posList}},)

        # TODO move value wrapping down to datex transform, here we should use them unwrapped
        value_transforms = {
            # type transformations
            'offsetDistance': lambda v: int(v) if not isinstance(v, dict) else v,
            # value transformations
            # v3 removed some v2 enum values which need to be mapped
            'commentType': lambda v: {  # FIXME move value mapping down
                'value': 'other' if v == 'locationDescriptor' else v
            },
            'vehicleObstructionType': lambda v: self.VEHICLE_OBSTRUCTION_TYPE_MAPPINGS.get(v, v),
            'obstructionType': lambda v: self.OBSTRUCTION_TYPE_MAPPINGS.get(v, v),
            'causeType': lambda v: self.CAUSE_TYPE_MAPPINGS.get(v, v),
            'openlrFunctionalRoadClass': lambda v: {'value': v.lower()},
            'openlrLowestFRCToNextLRPoint': lambda v: {'value': v.lower()},
            # lang: de-DE -> de as JSON schema allows only 2 chars, bemas uses uppercase
            '@lang': lambda v: v[0:2].lower(),
            'lane': lambda v: {'laneNumber': int(v[4:])} if v.startswith('lane') else {'laneUsage': {'value': v}},
            # comment/values is expected to be a dict with value/lang. For now, we assume values only includes multi ling string
            'values': lambda v: [add_def_lang_if_missing(value) for value in v['value']],
            'alertCDirection': lambda v: transform_alertc(v, False),
            'alertCPoint': lambda v: [v] if isinstance(v, dict) else v,
            'grossWeightCharacteristic': lambda v: v | {'typeOfWeight': {'value': 'actual'}},
            # v3 has no carParkStatus any longer, we map to serviceDisruption restAreaClosed
            'carParkStatus': lambda v: [{'value': self.CAR_PARK_STATUS_TO_SERVICE_TYPE_MAPPINGS.get(v, v)}],
            'recurringDayWeekMonthPeriod': lambda v: {'comDayWeekMonth': v} if v is not None else None,
            'supplementaryPositionalDescription': transform_supplementaryPositionalDescription,
            'openlrPoiWithAccessPoint': wrap_lroffset,
            'openlrPointAlongLine': wrap_lroffset,
            'managedCause': lambda v: {'objectReference': v},
            # VMS
            'vmsType': lambda v: {'value': 'fullMatrixSign' if v == 'matrixSign' else v},
            'vmsRecord': push_down_vms_configuration,
            # 'roadMaintenanceType': lambda v: v if isinstance(v, list) else [wrap_with_value(v)], # TODO conversion issue?
            'alertCLinear': lambda v: v if isinstance(v, list) else [v],  # TODO conversion issue?
            'linearWithinLinearElement': lambda v: v if isinstance(v, list) else [v],
            'linearElement': lambda v: {'locLinearElement': v},
            'gmlLineString': lambda v: {'posList': v.get('posList', v.get('coordinates', '').replace(',', ' '))},
        }

        keys_to_drop = {
            'urgency': None,  # Apparently, support for urgency has been dropped?
            '@xmlns:xsi': None,
            '@version': ['situation'],
            'type': ['recurringTimePeriodOfDay', 'cause'],
            'management': ['situationRecord'],  # apparently support for lifecyclemanagement notifications has been dropped?
            'openlrGeoCoordinate': ['openlrPointLocationReference'],
            '@xmlns': None,
            'exchange': None,
            'originalNumberOfLanes': ['impact'],  # TODO, check, if we shold copy this value to carriageways
            # v3  dropped CarParks Situation. We map to serviceDisruption which seems not to have an equivalent to carParkIdentity:
            'carParkIdentity': None,
        }

        geojson_drops = {'situationExtension': None}

        # keys_to_pull_up convert { ..., '<value>': { <nested properties> } } in { ..., <nested properties>}
        keys_to_pull_up = {
            'linearExtension': None,
            'linearExtended': None,
            'linearLineStringExtension': None,
            'pointExtension': None,
            'openlrExtendedPoint': None,
            'areaExtension': None,
            'openlrExtendedArea': None,
            'payloadPublication': None,
            'locGmlLineString': None,
            'impact': ['trafficConstrictionType'],
        }

        return TransformationRules(
            renamings,
            value_transforms,
            keys_to_drop | geojson_drops,
            {},
            keys_to_pull_up,
        )

    def xmlv3_to_json3_7(self):
        datex_json_renamings = {
            # Assumed DATEXII JSON Schema Artifacts
            '@modelBaseVersion': 'modelBaseVersionG',
            '@id': 'idG',
            '@lang': 'lang',
            '@version': 'versionG',
            '@targetClass': 'targetClass',
            '@operatingPatternIndex': 'operatingPatternIndex',
        }

        def wrap_with_value(v):
            return {'value': v}

        value_transforms = {
            # Value wrapping for parking ...
            'status': wrap_with_value,
            'operationStatus': wrap_with_value,
            'informationStatus': wrap_with_value,
            'confidentiality': wrap_with_value,
        }
        keys_to_drop = {
            '@xsi:schemaLocation': None,
            '@xmlns': None,
            '@xmlns:d2': None,
            '@xmlns:loc': None,
            '@xmlns:com': None,
            '@xmlns:fac': None,
            '@xmlns:xsd': None,
            '@xmlns:xsi': None,
            '@xsi:type': None,
        }
        keys_to_pull_up = {'modelBaseVersion'}
        return TransformationRules(
            datex_json_renamings,
            value_transforms,
            keys_to_drop,
            self.datex_xml_2_json_xsitype_mappings,
            keys_to_pull_up,
        )

    def xmlv2_to_json3_7(self):
        datex_json_renamings = {
            # Assumed DATEXII JSON Schema Artifacts
            '@modelBaseVersion': 'modelBaseVersionG',
            '@id': 'idG',
            '@lang': 'lang',
            '@version': 'versionG',
            '@targetClass': 'targetClass',
            # XML to JSON-schema conversion artefacts which were introduced by DATEX to avoid name clashes
            'commentExtension': 'sitCommentExtensionG',
            'generalObstructionExtension': 'sitGeneralObstructionExtensionG',
            'impactExtension': 'sitImpactExtensionG',
            'operatorActionExtension': 'sitOperatorActionExtensionG',
            'roadOrCarriagewayOrLaneManagementExtension': 'sitRoadOrCarriagewayOrLaneManagementExtensionG',
            'roadworksExtension': 'sitRoadworksExtensionG',
            'situationExtension': 'sitSituationExtensionG',
            'situationRecordExtension': 'sitSituationRecordExtensionG',
            'affectedCarriagewayAndLanesExtension': 'locCarriagewayExtensionG',
            # Note: the following extendedLinear extension is not defined in schema, JSON might not match expectation
            'extendedLinear': 'locLinearLocationExtensionG',
            # Note: the following networkLocationExtension extension is not defined in schema, JSON might not match expectation
            'networkLocationExtension': 'locNetworkLocationExtensionG',
            'openlrPointAlongLine': 'locOpenlrPointAlongLine',
            'openlrPoiWithAccessPoint': 'locOpenlrPoiWithAccessPoint',
        }

        # A couple of text properties are wrapped in an object, presumably for extendability
        def wrap_with_value(v):
            return {'value': v}

        value_transforms = {
            # Value wrapping...
            'abnormalTrafficType': wrap_with_value,
            'accidentType': lambda v: {'value': self.ACCIDENT_TYPE_MAPPINGS.get(v, v)},
            'informationStatus': wrap_with_value,
            'confidentiality': wrap_with_value,
            'applicableForTrafficDirection': wrap_with_value,
            'constructionWorkType': wrap_with_value,
            'delaysType': wrap_with_value,
            'probabilityOfOccurrence': wrap_with_value,
            'poorEnvironmentType': wrap_with_value,
            'roadMaintenanceType': wrap_with_value,
            'mobilityType': wrap_with_value,
            'locationDescription': wrap_with_value,
            'operatorActionStatus': wrap_with_value,
            'tpegDirection': wrap_with_value,
            'tpegLinearLocationType': wrap_with_value,
            'tpegOtherPointDescriptorType': wrap_with_value,
            'trafficManuallyDirectedBy': wrap_with_value,
            'validityStatus': wrap_with_value,
            'alertCDirection': lambda v: transform_alertc(v, True),
            'openlrFormOfWay': wrap_with_value,
            'complianceOption': wrap_with_value,
            'placesAtWhichApplicable': wrap_with_value,
            'loadType': wrap_with_value,
            'applicableForTrafficType': wrap_with_value,
            'roadOrCarriagewayOrLaneManagementType': wrap_with_value,
            'disturbanceActivityType': wrap_with_value,
            'vehicleType': wrap_with_value,
            'referentType': wrap_with_value,
            'directionRelativeOnLinearSection': wrap_with_value,
            'comparisonOperator': wrap_with_value,
            'generalInstructionToRoadUsersType': wrap_with_value,
            'environmentalObstructionType': wrap_with_value,
            'roadworksDuration': wrap_with_value,
            'drivingConditionType': wrap_with_value,
            'openlrOrientation': wrap_with_value,
            'openlrSideOfRoad': wrap_with_value,
            'tpegAreaLocationType': wrap_with_value,
            'subjectTypeOfWorks': wrap_with_value,
            'applicableDay': wrap_with_value,
            'obstructionType': wrap_with_value,
            'reroutingManagementType': wrap_with_value,
            'animalPresenceType': wrap_with_value,
            'severity': wrap_with_value,
            'authorityOperationType': wrap_with_value,
            'equipmentOrSystemFaultType': wrap_with_value,
            'faultyEquipmentOrSystemType': wrap_with_value,
            'generalNetworkManagementType': wrap_with_value,
            'overallSeverity': wrap_with_value,
            'carriageway': wrap_with_value,
            'infrastructureDamageType': wrap_with_value,
            'speedManagementType': wrap_with_value,
            'publicEventType': wrap_with_value,
            'weatherRelatedRoadConditionType': wrap_with_value,
            'nonWeatherRelatedRoadConditionType': wrap_with_value,
            'maintenanceVehicleActions': wrap_with_value,
            'roadsideServiceDisruptionType': wrap_with_value,
            'trafficConstrictionType': wrap_with_value,
            'tpegAreaDescriptorType': wrap_with_value,
            'transitServiceInformation': wrap_with_value,
            'transitServiceType': wrap_with_value,
            'vehicleObstructionType': lambda v: {'value': self.VEHICLE_OBSTRUCTION_TYPE_MAPPINGS.get(v, v)},
            # see https://docs.ndw.nu/en/dataformaten/datex2-v2.3/conversie-naar-v3/#generalobstruction-maps-to-generalobstruction
            'obstructionType': lambda v: {'value': self.OBSTRUCTION_TYPE_MAPPINGS.get(v, v)},
            'causeType': lambda v: {'value': self.CAUSE_TYPE_MAPPINGS.get(v, v)},
            # vms
            'physicalSupport': wrap_with_value,
            'vmsPhysicalMounting': wrap_with_value,
            'tpegSimplePointLocationType': wrap_with_value,
            'alertCArea': lambda v: [v],  # FIXME move up to xml2_to_json?
            'gmlLineString': lambda v: {'locGmlLineString': {'posList': v.get('posList', v.get('coordinates', '').replace(',', ' '))}},
        }

        keys_to_drop = {
            '@xsi:schemaLocation': None,
            '@xmlns:xsd': None,
            '@xsi:type': None,
        }

        rules = self.xmlv2_to_json()
        return TransformationRules(
            rules.renamings | datex_json_renamings,
            rules.value_transforms | value_transforms,
            rules.keys_to_drop | keys_to_drop,
            self.datex_xml_2_json_xsitype_mappings,
            rules.keys_to_pull_up,
        )
