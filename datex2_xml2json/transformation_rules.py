from dataclasses import dataclass
from typing import Callable

@dataclass
class TransformationRules:
    renamings: dict[str,str]
    value_transforms: dict[str,Callable]
    keys_to_drop: dict[str,str|None]
    type_mappings: dict[str, str]
    keys_to_pull_up: list[str]

def push_down_vms_configuration(vms: dict) -> dict:
    vmsConfiguration = {}
    if 'numberOfPictogramDisplayAreas' in vms:
        vmsConfiguration['numberOfDisplayAreas'] = vms.pop('numberOfPictogramDisplayAreas')
    if 'vmsPictogramDisplayCharacteristics' in vms:
        displays = vms.pop('vmsPictogramDisplayCharacteristics')
        vmsConfiguration['displayArea'] = [{ 'displayArea': {'vmsPictogramDisplayArea': displayArea.get('vmsPictogramDisplayCharacteristics')}, 'displayAreaIndex': displayArea.pop('displayAreaIndex')} for displayArea in displays if 'vmsPictogramDisplayCharacteristics' in displayArea]
    if len(vmsConfiguration)>0:
        vms['vmsConfiguration']= vmsConfiguration
    return vms

def pull_up_first_length_affected(v: dict):
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


class TransformationRuleFactory:

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
        'InfrastructureDamageObstruction':'sitInfrastructureDamageObstruction',
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
        'SpeedManagement': 'sitSpeedManagement',
        'TransitInformation': 'sitTransitInformation',
        'VehicleObstruction': 'sitVehicleObstruction',
        'WinterDrivingManagement': 'sitWinterDrivingManagement',
        'Linear': 'locSingleRoadLinearLocation',
        'SituationPublication': 'sitSituationPublication',
        'TpegNonJunctionPoint': 'locTpegNonJunctionPoint',
        'AlertCMethod4Linear': 'locAlertCMethod4Linear',
        'Point': 'locPointLocation',
        'Area': 'locAreaLocation',
        'ItineraryByIndexedLocations': 'locItineraryByIndexedLocations',
        'TpegGeometricArea': 'locTpegGeometricArea',
        'OpenlrPolygonLocationReference': 'locOpenlrPolygonLocationReference',
        'DistanceFromLinearElementReferent': 'locDistanceFromLinearElementReferent',
        # VMS
        'VmsTablePublication': 'vmsVmsTablePublication',
        'TpegSimplePoint': 'locTpegSimplePoint',
        'AlertCMethod4Point': 'locAlertCMethod4Point',
    }

    def __init__(self):
        pass

    def xmlv2_to_json3_6(self):
        renamings = {
            # xml2json artifact
            '_text': 'value',
            # Assumed DATEXII 2.2->DATEX3.6 naming changes
            'd2LogicalModel':'payload',
            'affectedCarriagewayAndLanes':'carriageway',
            'groupOfLocations': 'locationReference',
            'locationDescriptor':'positionOnCarriageway',
            'locationForDisplay': 'coordinatesForDisplay',
            'openlrCoordinate': 'openlrCoordinates',
            'openlrExtendedLinear': 'openlrLinear',
            'openlrLowestFRCToNextLRPoint': 'openlrLowestFrcToNextLRPoint',
            'roadworksDuration': 'roadworksDurationClassification',
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
            
            # Assumed DATEXII JSON Schema Artifacts 
            '@modelBaseVersion':'modelBaseVersionG',
            '@id': 'idG',
            '@lang': 'lang',
            '@version': 'versionG',
            '@targetClass': 'targetClass',

            # XML to JSON-schema conversion artefacts which were introduced by DATEX to avoid name clashes
            'commentExtension': 'sitCommentExtensionG',
            'generalObstructionExtension': 'sitGeneralObstructionExtensionG',
            'impactExtension':'sitImpactExtensionG',
            'operatorActionExtension': 'sitOperatorActionExtensionG',
            'roadOrCarriagewayOrLaneManagementExtension': 'sitRoadOrCarriagewayOrLaneManagementExtensionG',
            'roadworksExtension': 'sitRoadworksExtensionG',
            'situationExtension': 'sitSituationExtensionG',
            'situationRecordExtension': 'sitSituationRecordExtensionG',
            'affectedCarriagewayAndLanesExtension': 'locCarriagewayExtensionG',
            'extendedLinear': 'locLinearLocationExtensionG', # Note: the extension is not defined in schema, JSON might not match expectation,
            'networkLocationExtension': 'locNetworkLocationExtensionG', # Note: the extension is not defined in schema, JSON might not match expectation,
            'openlrPointAlongLine': 'locOpenlrPointAlongLine',
            'openlrPoiWithAccessPoint':'locOpenlrPoiWithAccessPoint',
        }


        # A couple of text properties are wrapped in an object, presumably for extendability
        wrap_with_value = lambda v: { 'value': v }

        value_transforms = {
            # type transformations
            'offsetDistance': lambda v: int(v) if not isinstance(v, dict) else v,
            # value transformations
            # v3 requires timezone information in time values which are not provided in v2 xml
            # TODO this should be fixed in a more complex post processing
            'endTimeOfPeriod': lambda v: v+'+01:00' if not '+' in v else v, 
            'startTimeOfPeriod': lambda v: v+'+01:00' if not '+' in v else v,
            # v3 removed some v2 enum values which need to be mapped
            'commentType':  lambda v: { 'value': 'other' if v == 'locationDescriptor' else v },
            'vehicleObstructionType': lambda v: { 'value': 'brokenDownVehicle'} if v == 'brokenDownHeavyLorry' else { 'value': 'dangerousSlowMovingVehicle'} if v=='slowMovingMaintenanceVehicle' else {'value': v },
            'causeType': lambda v: { 'value': 'other'} if v == 'shearWeightOfTraffic' else {'value': v },
            'openlrFunctionalRoadClass': lambda v: { 'value': v.lower() },
            'openlrLowestFRCToNextLRPoint': lambda v: { 'value': v.lower() },
            # lang: de-DE -> de as JSON schema allows only 2 chars, bemas uses uppercase
            '@lang': lambda v: v[0:2].lower(),
            'lane': lambda v: { 'laneNumber': int(v[4:])} if v.startswith('lane') else { 'laneUsage': { 'value': v }},
            # comment/values is expected to be a dict with value/lang. For now, we assume values only includes multi ling string
            #'values': lambda value: {'value': value, 'lang': defaultLanguage} if isinstance(value, str) else value,
            'values': lambda value: value['value'] if isinstance(value, dict) else value, 
            'alertCDirection': lambda v: v | { 'alertCAffectedDirection': {'value': 'unknown'}},
            'grossWeightCharacteristic': lambda v: v | { 'typeOfWeight': { 'value': 'actual'}},
        
            # Value wrapping...
            'abnormalTrafficType': wrap_with_value,
            'accidentType': wrap_with_value,
            'informationStatus': wrap_with_value,
            'confidentiality': wrap_with_value,
            'applicableForTrafficDirection': wrap_with_value,
            'constructionWorkType': wrap_with_value,
            'probabilityOfOccurrence': wrap_with_value,
            'poorEnvironmentType': wrap_with_value,
            'roadMaintenanceType': wrap_with_value,
            'mobilityType': wrap_with_value,
            'locationDescription': wrap_with_value,
            'operatorActionStatus': wrap_with_value,
            'tpegDirection': wrap_with_value,
            'tpegLinearLocationType': wrap_with_value,
            'tpegOtherPointDescriptorType': wrap_with_value,
            'locationDescriptor':  wrap_with_value,
            'validityStatus': wrap_with_value,
            'openlrFormOfWay': wrap_with_value,
            'complianceOption': wrap_with_value,
            'placesAtWhichApplicable': wrap_with_value,
            'loadType': wrap_with_value,
            'applicableForTrafficType': wrap_with_value,
            'roadOrCarriagewayOrLaneManagementType': wrap_with_value,
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
            'alertCDirectionCoded': wrap_with_value,
            'severity': wrap_with_value,
            'authorityOperationType': wrap_with_value,
            'equipmentOrSystemFaultType':wrap_with_value,
            'faultyEquipmentOrSystemType':wrap_with_value,
            'generalNetworkManagementType':wrap_with_value,
            'overallSeverity':wrap_with_value,
            'carriageway': wrap_with_value,
            
            'recurringDayWeekMonthPeriod': lambda v: { 'comDayWeekMonth': v} if v is not None else None,
            'supplementaryPositionalDescription': pull_up_first_length_affected,
            'openlrPoiWithAccessPoint':  wrap_lroffset,
            'openlrPointAlongLine':  wrap_lroffset,
            'managedCause': lambda v: { 'objectReference': v},
            # VMS
            'vmsType': lambda v: {'value': 'fullMatrixSign' if v=='matrixSign' else v},
            'physicalSupport': wrap_with_value,
            'vmsPhysicalMounting': wrap_with_value,
            'tpegSimplePointLocationType': wrap_with_value,
            'vmsRecord': push_down_vms_configuration,

            'roadMaintenanceType': lambda v: v if isinstance(v, list) else [wrap_with_value(v)], # TODO conversion issue?
            'alertCLinear': lambda v: v if isinstance(v, list) else [v], # TODO conversion issue?
            
            'linearWithinLinearElement': lambda v: v if isinstance(v, list) else [v],
            'linearElement': lambda v: { 'locLinearElement': v},
        }

        keys_to_drop = { 
            'urgency': None, # Apparently, support for urgency has been dropped?
            '@xmlns:xsi': None,
            '@version': ['situation'], 
            'type': ['recurringTimePeriodOfDay', 'cause'], 
            'management': ['situationRecord'], # apparently support for lifecyclemanagement notifications has been dropped?
            'openlrGeoCoordinate': ['openlrPointLocationReference'],
            '@xmlns': None,
            'exchange': None,
            '@xsi:type': None,
            'originalNumberOfLanes': ['impact'], # TODO, check, if we shold copy this value to carriageways
        }

        # keys_to_pull_up convert { ..., '<value>': { <nested properties> } } in { ..., <nested properties>}
        keys_to_pull_up = {
            'linearExtension', 
            'pointExtension',
            'openlrExtendedPoint',
            'areaExtension',
            'openlrExtendedArea',
            'payloadPublication',
        }

        return TransformationRules(renamings, value_transforms, keys_to_drop, self.datex_xml_2_json_xsitype_mappings, keys_to_pull_up)

       