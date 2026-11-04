from datex2_xml2json.transform.source_setter import SourceSetter
from datex2_xml2json.util import JsonDict


def test_source_added() -> None:
    transformer = SourceSetter('https://xyz.xyz/dataset-id', 'roadworks_source')
    payload: JsonDict = {'d2LogicalModel': {'payloadPublication': {'situation': [{'situationRecord': [{}]}]}}}
    expected = {
        'd2LogicalModel': {
            'payloadPublication': {
                'situation': [{'situationRecord': [{'source': {'sourceIdentification': 'roadworks_source'}}]}],
                'payloadPublicationExtension': {
                    'publicationIdentifier': 'https://xyz.xyz/dataset-id',
                },
            }
        }
    }
    actual = transformer.transform(payload)
    assert expected == actual


def test_existing_source_properties_are_retained() -> None:
    transformer = SourceSetter(None, 'roadworks_source')
    record = {'id': 'a', 'source': {'sourceCountry': 'de', 'sourceIdentification': 'old'}}
    payload: JsonDict = {'d2LogicalModel': {'payloadPublication': {'situation': [{'situationRecord': [record]}]}}}

    transformer.transform(payload)

    assert record['source'] == {'sourceCountry': 'de', 'sourceIdentification': 'roadworks_source'}
