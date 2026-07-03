import jsonata
from .base import AbstractTransformer

mostly_flat_geojson_expression = """
{
  "type": "FeatureCollection",
  "features": payload.situation.situationRecord.{ 
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
        "routeRecommendation": generalPublicComment[commentExtension.commentExtended.commentType2="routeRecommendation"][0].comment.values[lang="de"].value,
        "type": type,
        "complianceOption": complianceOption,
        "applicableForTrafficDirection":applicableForTrafficDirection,
        /* TODO this is not set for BEMaS? */
        "placesAtWhichApplicable":placesAtWhichApplicable,
        "cause":cause.managedCause.objectReference.id,
        "numberOfOperationalLanes": impact.numberOfOperationalLanes,
        "numberOfLanesRestricted": impact.numberOfLanesRestricted,
        "residualRoadWidth": impact.residualRoadWidth,
        "trafficConstrictionType": impact.trafficConstrictionType,
        /* TODO: Remove value as soon as input json has it removed*/
        "laneUsage": impact.impactExtension.impactExtended.laneRestriction.lane.laneUsage.value,
        "laneStatusCoded": impact.impactExtension.impactExtended.laneStatusCoded,
        "extendedLaneStatusCoded": situationRecordExtension.situationRecordExtended.extendedLaneStatusCoded,
        "hardShoulderStatus": impact.impactExtension.impactExtended.hardShoulderStatus,
        "residualHeight": impact.impactExtension.impactExtended.residualHeight,
        "capacityRemaining": impact.capacityRemaining,
        "originalNumberOfLanes": impact.originalNumberOfLanes,
        /* is numberOfObstructions used?*/
        "numberOfObstructions": impact.numberOfObstructions,
        "forVehiclesWithCharacteristicsOf": forVehiclesWithCharacteristicsOf,
        "validityStatus": validity.validityStatus,
        "overallStartTime": validity.validityTimeSpecification.overallStartTime,
        "overallEndTime": validity.validityTimeSpecification.overallEndTime,
        "validPeriod": validity.validityTimeSpecification.validPeriod,
        "subjectTypeOfWorks": subjects.subjectTypeOfWorks,
        "severity": severity,
        "applicableForTrafficType":applicableForTrafficType,
        /* TODO Check which types are defined with maxoccurs=*, check which have value */
        "situationSubtype": obstructionType[0] ?? reroutingManagementType[0] ?? constructionWorkType ?? generalInstructionToRoadUsersType ?? infrastructureDamageType ?? accidentType[0] ?? abnormalTrafficType ?? speedManagementType ?? roadMaintenanceType[0] ?? animalPresenceType ?? environmentalObstructionType ?? generalNetworkManagementType ?? authorityOperationType ?? roadOrCarriagewayOrLaneManagementType ?? vehicleObstructionType ?? poorEnvironmentType,
        "actionPlanIdentifier": actionPlanIdentifier,
        "operatorActionStatus": operatorActionStatus,
        "roadworksDurationClassification": roadworksDurationClassification,
        "mobilityType": mobility.mobilityType,
        "roadworksLayout": roadworksExtension.roadworksExtended.roadworksLayout,
        "urlLinkAddress": urlLink[0].urlLinkAddress
    },
    "geometry": locationReference.geoJsonGeometry 
}
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
