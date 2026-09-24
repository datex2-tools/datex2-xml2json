import jsonata

from .base import AbstractTransformer

# ruff: noqa: E501 (JSONata expressions are long...)

# TODO: we asume arrays applicableForTrafficType, placesAtWhichApplicable, applicableForTrafficDirection have at most 1 element... We should check this
mostly_flat_geojson_expression = """
{
  "type": "FeatureCollection",
  "features": payload.situation[].situationRecord.{
    "type": "Feature",
    "properties": {
        "publicationTime": %.%.publicationTime,
        "publicationCreator": %.%.publicationCreator.nationalIdentifier,
        "situationId": %.id,
        "situationVersionTime": %.situationVersionTime,
        "confidentiality": %.headerInformation.confidentiality,
        "informationStatus": %.headerInformation.informationStatus,
        "overallSeverity": %.overallSeverity,
        "id": id,
        "version": version,
        "situationRecordCreationTime": situationRecordCreationTime,
        "situationRecordVersionTime": situationRecordVersionTime,
        "probabilityOfOccurrence": probabilityOfOccurrence,
        /* description is not declared in BEMaS */
        "description": generalPublicComment[commentType.value="description"].comment.values[lang="de"].value,
        "roadworksType": generalPublicComment[commentExtension.commentExtended.commentType2="roadworksType"].comment.values[lang="de"].value,
        "roadworksName": generalPublicComment[commentExtension.commentExtended.commentType2="roadworksName"].comment.values[lang="de"].value,
        "heavyDutyTransportRestriction": generalPublicComment[commentExtension.commentExtended.commentType2="heavyDutyTransportRestriction"].comment.values[lang="de"].value,
        "routeRecommendation": generalPublicComment[commentExtension.commentExtended.commentType2="routeRecommendation"][0].comment.values[lang="de"].value,
        "type": type,
        "complianceOption": complianceOption,
        "applicableForTrafficDirection":applicableForTrafficDirection[0],
        /* TODO this is not set for BEMaS? */
        "placesAtWhichApplicable":placesAtWhichApplicable[0],
        "cause":cause.managedCause.objectReference.id,
        "numberOfOperationalLanes": impact.numberOfOperationalLanes,
        "numberOfLanesRestricted": impact.numberOfLanesRestricted,
        "residualRoadWidth": impact.residualRoadWidth,
        "trafficConstrictionType": impact.trafficConstrictionType,
        "laneRestriction": impact.impactExtension.impactExtended.laneRestriction,
        "laneStatusCoded": impact.impactExtension.impactExtended.laneStatusCoded,
        "extendedLaneStatusCoded": situationRecordExtension.situationRecordExtended.extendedLaneStatusCoded,
        "hardShoulderStatus": impact.impactExtension.impactExtended.hardShoulderStatus,
        /* Note: other publication (i.e. TrafficMessages) use roadClosed and forVehiclesWithCharacteristicsOf */
        "residualHeight": impact.impactExtension.impactExtended.residualHeight,
        /* Note: other publication (i.e. TrafficMessages) use roadClosed and forVehiclesWithCharacteristicsOf */
        "maxVehicleWeight": impact.impactExtension.impactExtended.laneRestriction[lane="allLanesCompleteCarriageway"].maxVehicleWeight,
        "capacityRemaining": impact.capacityRemaining,
        "originalNumberOfLanes": impact.originalNumberOfLanes,
        /* is numberOfObstructions used?*/
        "numberOfObstructions": impact.numberOfObstructions,
        /* Note: some publications (i.e. BEMaS use impactExtended to communicate height and weight restrictions ) */
        "forVehiclesWithCharacteristicsOf": forVehiclesWithCharacteristicsOf,
        "validityStatus": validity.validityStatus,
        "overallStartTime": validity.validityTimeSpecification.overallStartTime,
        "overallEndTime": validity.validityTimeSpecification.overallEndTime,
        "validPeriods": validity.validityTimeSpecification.validPeriod,
        "subjectTypeOfWorks": subjects.subjectTypeOfWorks,
        "severity": severity,
        "applicableForTrafficType":applicableForTrafficType[0],
        /* TODO Check which types are defined with maxoccurs=*, check which have value */
        "situationRecordSubtype": obstructionType[0] ?? reroutingManagementType[0] ?? constructionWorkType ?? generalInstructionToRoadUsersType ?? infrastructureDamageType ?? accidentType[0] ?? abnormalTrafficType ?? speedManagementType ?? roadMaintenanceType[0] ?? animalPresenceType ?? environmentalObstructionType ?? generalNetworkManagementType ?? authorityOperationType ?? roadOrCarriagewayOrLaneManagementType ?? vehicleObstructionType ?? poorEnvironmentType,
        "actionPlanIdentifier": actionPlanIdentifier,
        "operatorActionStatus": operatorActionStatus,
        "roadworksDurationClassification": roadworksDurationClassification,
        "mobilityType": mobility.mobilityType,
        "roadworksLayout": roadworksExtension.roadworksExtended.roadworksLayout,
        "urlLinkAddress": urlLink[0].urlLinkAddress,
        "roadNumber": locationReference.linearWithinLinearElement.linearElement.locLinearElement.roadNumber,
        "roadName": locationReference.linearWithinLinearElement.linearElement.locLinearElement.roadName.values[0].value,
        "fromASBSegmentFromNode": locationReference.linearWithinLinearElement.fromPoint.fromReferent.referentIdentifier,
        "fromASBSegmentTowardsNode": locationReference.linearWithinLinearElement.fromPoint.towardsReferent.referentIdentifier,
        "fromASBSegmentStation": locationReference.linearWithinLinearElement.fromPoint.distanceAlong,
        "toASBSegmentFromNode": locationReference.linearWithinLinearElement.toPoint.fromReferent.referentIdentifier,
        "toASBSegmentTowardsNode": locationReference.linearWithinLinearElement.toPoint.towardsReferent.referentIdentifier,
        "toASBSegmentStation": locationReference.linearWithinLinearElement.toPoint.distanceAlong,
        "lengthAffected": locationReference.supplementaryPositionalDescription.lengthAffected,
        "temporarySpeedLimit": temporarySpeedLimit ?? operatorActionExtension.operatorActionExtended.mainSpeedLimit
    },
    "geometry": locationReference.geoJsonGeometry
  } ?? []
}
"""


class JsonataTransformer(AbstractTransformer):
    def __init__(self, jsonata_expression=mostly_flat_geojson_expression):
        self.jsonata_expr = jsonata.Jsonata(jsonata_expression)

    def transform(self, a_dict: dict) -> dict:
        result = self.jsonata_expr.evaluate(a_dict)

        return self.post_transform(result)

    def post_transform(self, a_dict: dict) -> dict:
        return a_dict
