import logging

from .base import ProcessingTransformer

logger = logging.getLogger(__name__)


class RoadsRegioTransformer(ProcessingTransformer):
    def __init__(self, path: str = 'payload/sitSituationPublication/situation/situationRecord'):
        super().__init__(path)

    def _filter_empty_comments(self, situation_record: dict):
        # Remove comments without value
        if 'generalPublicComment' in situation_record:
            comments = [
                c
                for c in situation_record['generalPublicComment']
                if len(c['comment']['values']) > 0 and c['comment']['values'][0].get('value') is not None
            ]
            situation_record['generalPublicComment'] = comments

    def _handle_originalNumberOfLanes(self, situation_record: dict):
        # Removes originalNumberOfLanes from impact.

        if 'impact' in situation_record:
            # TODO originalNumberOfLanes probably should they be added elsewhere
            situation_record['impact'].pop('originalNumberOfLanes', None)

    def _handle_bemas_locations(self, situation_record: dict):
        # Removes originalNumberOfLanes from impact.

        # BEMaS
        # Expectation:
        # locationGroup/
        #   linearExtended/gmlLineString/roadInformation
        # .  linearWithinLinearElement[0]/linearElement
        # Result:
        #  linearElement/locLinearElementByLineString/
        # .   gmlLineString/locGmlLineString
        # .   roadNumber
        # .   roadName
        locationGroup = situation_record.get('locationReference', {}).get('locSingleRoadLinearLocation', {})

        linearExtended = locationGroup.pop('linearExtended', None)
        gmlLineString = None
        if isinstance(linearExtended, dict) and 'gmlLineString' in linearExtended:
            gmlLineString = linearExtended['gmlLineString']
            # roadInformation is not part of gmlLineString any more, remove it
            gmlLineString.pop('roadInformation', {})

        linearWithinLinearElements = locationGroup.get('linearWithinLinearElement', [])

        # Copy roadinformation and gmlLineString to locLinearElementByLineString
        if len(linearWithinLinearElements) == 1:
            linearElement = linearWithinLinearElements[0].get('linearElement', {})
            locLinearElementByLineString = {'gmlLineString': {'locGmlLineString': gmlLineString}} if gmlLineString else {}
            if 'roadNumber' in linearElement:
                locLinearElementByLineString['roadNumber'] = linearElement.pop('roadNumber', None)
            if 'roadName' in linearElement:
                locLinearElementByLineString['roadName'] = linearElement.pop('roadName', None)

            linearElement['locLinearElementByLineString'] = locLinearElementByLineString
            linearWithinLinearElements[0]['linearElement'] = linearElement

    def _fix_missing_linearElement(self, situation_record: dict):
        # Removes originalNumberOfLanes from impact.

        # BEMaS
        # Expectation:
        # locationGroup/
        #   linearExtended/gmlLineString/roadInformation
        # .  linearWithinLinearElement[0]/linearElement
        # Result:
        #  linearElement/locLinearElementByLineString/
        # .   gmlLineString/locGmlLineString
        # .   roadNumber
        # .   roadName
        locationGroup = situation_record.get('locationReference', {}).get('locSingleRoadLinearLocation', {})
        linearWithinLinearElements = locationGroup.get('linearWithinLinearElement', [])
        if len(linearWithinLinearElements) == 1:
            if 'linearElement' not in linearWithinLinearElements[0]:
                linearWithinLinearElements[0]['linearElement'] = {}

    def process(self, situation_record_wrapper: dict):
        if isinstance(situation_record_wrapper, dict) and len(situation_record_wrapper) == 1:
            situation_record = situation_record_wrapper.get(next(iter(situation_record_wrapper.keys())))
        else:
            situation_record = situation_record_wrapper
        if situation_record is None:
            return

        # self._handle_bemas_locations(situation_record)
        self._fix_missing_linearElement(situation_record)
        self._handle_originalNumberOfLanes(situation_record)
        self._filter_empty_comments(situation_record)
