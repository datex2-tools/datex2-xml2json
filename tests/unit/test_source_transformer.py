from datex2_xml2json.transform.base import SituationRecordTransformer


class SourceTransformer(SituationRecordTransformer):
    sourceIdentification: str | None = None
    publicationId: str | None = None

    def __init__(self, publicationId: str | None, sourceIdentification: str | None):
        super().__init__('payload/situation/situationRecord')
        self.publicationId = publicationId
        self.sourceIdentification = sourceIdentification

    def process_situation_record(self, situation_record: dict) -> None:
        situation_record['source'] = {'sourceIdentification': self.sourceIdentification}

    def transform(self, publication: dict) -> dict:
        publication = super().transform(publication)

        publication['payload']['publicationId'] = self.publicationId
        return publication


def test_source_added():
    transformer = SourceTransformer('https://xyz.xyz/dataset-id', 'roadworks_source')
    payload = {'payload': {'situation': [{'situationRecord': [{}]}]}}
    expected = {
        'payload': {
            'publicationId': 'https://xyz.xyz/dataset-id',
            'situation': [{'situationRecord': [{'source': {'sourceIdentification': 'roadworks_source'}}]}],
        }
    }
    actual = transformer.transform(payload)
    assert expected == actual
