import logging
import re

from .jsonata_transformer import JsonataTransformer

logger = logging.getLogger(__name__)

# TODO: PublicEvent notificcations and GeneralInstructionOrMessageToRoadUsers do not really match
# TODO how can we deduce direction for NRW incidents
cifs_expression = """
{
    "incidents": features[
        properties.type!="CarParks" and
        properties.type!="ReroutingManagement" and
        properties.type!="EquipmentOrSystemFault" and
        properties.validityStatus!="suspended"
        ][].{
        "id": properties.id,
        "creationtime": properties.situationRecordCreationTime,
        "updatetime": properties.situationRecordVersionTime,
        "description": properties.roadworksName ? properties.roadworksName : properties.description ?? "-",
        "starttime": properties.overallStartTime,
        "endtime": properties.overallEndTime,
        "direction": "ONE_DIRECTION",
        "street": $trim(properties.roadNumber?($contains(properties.roadName, properties.roadNumber)?
          properties.roadName: properties.roadNumber & " " & properties.roadName): $split(properties.description, "\n")[0] ??
          "Unbekannte Straße"),
        "type": (
            $typeBySubtypeLookup := {
                "carriagewayClosures": "ROAD_CLOSED",
                "closedPermanentlyForTheWinter": "ROAD_CLOSED",
                "overnightClosures": "ROAD_CLOSED",
                "roadClosed": "ROAD_CLOSED",
                "unprotectedAccidentArea": "ACCIDENT"
                };
            $typeLookup := {
                "Accident": "ACCIDENT",
                "AnimalPresence": "HAZARD",
                "AnimalPresenceObstruction": "HAZARD",
                "AbnormalTraffic": "JAM",
                "AuthorityOperation": "HAZARD",
                "Conditions": "HAZARD",
                "ConstructionWorks": "CONSTRUCTION",
                "EnvironmentalObstruction": "HAZARD",
                "GeneralObstruction": "HAZARD",
                "GeneralNetworkManagement": "HAZARD",
                "InfrastructureDamageObstruction": "HAZARD",
                "MaintenanceWorks": "CONSTRUCTION",
                "Obstruction": "HAZARD",
                "RoadOrCarriagewayOrLaneManagement":"HAZARD",
                "SpeedManagement": "HAZARD",
                "VehicleObstruction": "HAZARD",
                "PublicEvent": "CHIT_CHAT",
                "GeneralInstructionOrMessageToRoadUsers": "CHIT_CHAT",
                "NonWeatherRelatedRoadConditions": "HAZARD",
                "WeatherRelatedRoadConditions": "HAZARD",
                "DisturbanceActivity": "CHIT_CHAT",
                "TransitInformation": "CHIT_CHAT"
                };
            $lookup($typeBySubtypeLookup , properties.situationRecordSubtype)?:$lookup($typeLookup , properties.type)?:"TODO"),
        "subtype": (
            $subtypeByTypeLookup := {
                /* Accident (no subtypes, as DATEXII does not provide accident severity) */
                /* AnimalPresence has no exact correspondance, we prefer HAZARD_ON_SHOULDER_ANIMALS over HAZARD_ON_ROAD_ROAD_KILL */
                "AnimalPresence": "HAZARD_ON_SHOULDER_ANIMALS",
                "AnimalPresenceObstruction": "HAZARD_ON_SHOULDER_ANIMALS",
                "AuthorityOperation": "HAZARD_ON_ROAD",
                "GeneralNetworkManagement": "HAZARD_ON_ROAD",
                "InfrastructureDamageObstruction": "HAZARD_ON_ROAD",
                "MaintenanceWorks": "HAZARD_ON_ROAD_CONSTRUCTION",
                "Obstruction": "HAZARD_ON_ROAD",
                "RoadOrCarriagewayOrLaneManagement": "HAZARD_ON_ROAD",
                "VehicleObstruction": "HAZARD_ON_ROAD",
                "WeatherRelatedRoadConditions": "HAZARD_WEATHER"
                };
            $subtypeBySubtypeLookup := {
                /* AbnormalTraffic (no subtype for unspecifiedAbnormalTraffic and other)*/
                "stationaryTraffic": "JAM_STAND_STILL_TRAFFIC",
                "queuingTraffic": "JAM_HEAVY_TRAFFIC",
                "slowTraffic": "JAM_MODERATE_TRAFFIC",
                "heavyTraffic": "JAM_LIGHT_TRAFFIC",
                /* Accident (no subtypes, as DATEXII does not provide accident severity) */
                "roadworks": "HAZARD_ON_ROAD_CONSTRUCTION",
                /* EnvironmentalObstruction*/
                "avalanches": "HAZARD_WEATHER",
                "earthquakeDamage": "HAZARD_ON_ROAD",
                "fallenTrees": "HAZARD_ON_ROAD_OBJECT",
                "fallingIce": "HAZARD_WEATHER_HAIL",
                "fallingLightIceOrSnow": "HAZARD_WEATHER_FREEZING_RAIN",
                "flashFloods": "HAZARD_WEATHER_MONSOON",
                "flooding": "HAZARD_WEATHER_FLOOD",
                "forestFire": "HAZARD_WEATHER",
                "grassFire": "HAZARD_WEATHER",
                "landslips": "HAZARD_ON_ROAD",
                "mudSlide": "HAZARD_ON_ROAD",
                "sewerOverflow": "HAZARD_ON_ROAD",
                "rockfalls": "HAZARD_ON_ROAD",
                "seriousFire": "HAZARD_WEATHER",
                "smokeOrFumes": "HAZARD_WEATHER",
                "stormDamage": "HAZARD_ON_ROAD",
                "subsidence": "HAZARD_ON_ROAD",
                /* GeneralNetworkManagement (default defined via subtypeByTypeLookup, no exceptions )*/
                /* Obstruction (default defined via subtypeByTypeLookup, here only exceptions ) */
                "objectOnTheRoad": "HAZARD_ON_ROAD_OBJECT",
                "objectsFallingFromMovingVehicle": "HAZARD_ON_ROAD_OBJECT",
                "obstructionOnTheRoad": "HAZARD_ON_ROAD_OBJECT",
                /* RoadOrCarriagewayOrLaneManagement (default defined via subtypeByTypeLookup, here only exceptions ) */
                "carriagewayClosures": "ROAD_CLOSED_CONSTRUCTION",/* TODO: subtype needs to be figured out via sibling situationRecord*/
                "closedPermanentlyForTheWinter": "ROAD_CLOSED_HAZARD",
                "doNotUseSpecifiedLanesOrCarriageways": "HAZARD_ON_ROAD_LANE_CLOSED",
                "laneClosures": "HAZARD_ON_ROAD_LANE_CLOSED",
                "overnightClosures": "ROAD_CLOSED_CONSTRUCTION",/* TODO: subtype needs to be figured out via sibling situationRecord*/
                "roadClosed": "ROAD_CLOSED_CONSTRUCTION", /* TODO: subtype needs to be figured out via sibling situationRecord*/
                /* VehicleObstruction (default defined via subtypeByTypeLookup, here only exceptions )*/
                "abandonedVehicle": "HAZARD_ON_ROAD_CAR_STOPPED",
                "brokenDownBus": "HAZARD_ON_ROAD_CAR_STOPPED",
                "brokenDownHeavyLorry": "HAZARD_ON_ROAD_CAR_STOPPED",
                "brokenDownVehicle": "HAZARD_ON_ROAD_CAR_STOPPED",
                "damagedVehicle": "HAZARD_ON_ROAD_CAR_STOPPED",
                "emergencyVehicle": "HAZARD_ON_ROAD_EMERGENCY_VEHICLE",
                "unlitVehicleOnTheRoad": "HAZARD_ON_ROAD_CAR_STOPPED",
                "vehicleOnFire": "HAZARD_ON_ROAD_CAR_STOPPED",
                /* NonWeatherRelatedRoadConditions */
                "roadSurfaceInPoorCondition": "HAZARD_ON_ROAD_POT_HOLE"
                };
            $lookup($subtypeBySubtypeLookup, properties.situationRecordSubtype)?:$lookup($subtypeByTypeLookup, properties.type)
        ),
        "polyline": $replace($replace($join($map(geometry.coordinates, $string), " "), ",", " "), /[\\[\\]]/, "")
    }
}
"""


class CifsTransformer(JsonataTransformer):
    # This pattern is used to exract the common ID prefix of all situation records which
    # should be grouped in a single CIFS entry.
    # Currently expected patterns are:
    # 1. four hyphen separated numeric values, followed by no or any subsring
    # 2. Any string/char prefix followed by dot + number
    situation_record_group_prefix_regexp = r'^(\d+-\d\d\d\dV\d+)$|^(\d+-\d+-\d+-\d+-gegen).*|^(\d+-\d+-\d+-\d+).*|^(.*)\.\d+$'

    def __init__(self, **kwargs):
        super().__init__(cifs_expression)

    def _group_by_common_situation_record_id_substring(self, incidents, pattern):
        grouped_incidents = {}
        p = re.compile(pattern)

        for incident in incidents:
            m = p.match(incident['id'])
            if m is None:
                logger.warning(f'No match for id {incident["id"]} with pattern {pattern} ')
                continue
            common_id_substring = next(group for group in m.groups() if group is not None)
            if common_id_substring in grouped_incidents:
                grouped_incidents[common_id_substring].append(incident)
            else:
                grouped_incidents[common_id_substring] = [incident]

        return grouped_incidents

    def _get_type_sub_type_prio(self, incident):
        if incident['type'] == 'ROAD_CLOSED':
            return 10
        if incident.get('subtype') == 'HAZARD_ON_ROAD_LANE_CLOSED':
            return 4
        if incident.get('subtype') == 'HAZARD_ON_ROAD_CONSTRUCTION':
            return 3
        if incident.get('subtype') == 'HAZARD_ON_ROAD' or incident['type'] in ['CHIT_CHAT']:
            return 1
        else:
            return 2

    def _merge_incident_group(self, incident_group):
        # Assumptions: besides type and subtype, all properties are assumed to be equals
        # (TODO: we might check this explicitly)
        #
        # For now, all incidents are merged into one single incident which should represent all of them.
        # Rules are as follows:
        # * highest priority subtype/type wins
        # TODO: subtype for road_closed to be set according to other incidents
        # TODO: should jam be communicated in addition?
        highest_prio = None
        highest_prio_type = None
        highest_prio_subtype = None

        for incident in incident_group:
            current_prio = self._get_type_sub_type_prio(incident)
            if highest_prio is None or current_prio > highest_prio:
                logger.debug(
                    f'For {incident["id"]}, replace {highest_prio} {highest_prio_type} {highest_prio_subtype}'
                    f' by {incident["type"]} {incident.get("subtype")}'
                )
                highest_prio = current_prio
                highest_prio_type = incident['type']
                highest_prio_subtype = incident.get('subtype')
            else:
                logger.debug(
                    f'For {incident["id"]}, do not replace {highest_prio} {highest_prio_type} {highest_prio_subtype}'
                    f' by {incident["type"]} {incident.get("subtype")}'
                )
        return incident_group[0]

    def _merge_grouped_incidents(self, grouped_incidents):
        incidents = []
        for key in grouped_incidents:
            incidents.append(self._merge_incident_group(grouped_incidents[key]))

        return incidents

    def post_transform(self, a_dict: dict) -> dict:
        grouped_incidents = self._group_by_common_situation_record_id_substring(
            a_dict['incidents'], self.situation_record_group_prefix_regexp
        )
        a_dict['incidents'] = self._merge_grouped_incidents(grouped_incidents)
        return a_dict
