from datex2_xml2json.transform.source_setter import SourceSetter


def test_source_added():
    transformer = SourceSetter('https://xyz.xyz/dataset-id', 'roadworks_source')
    payload = {'d2LogicalModel': {'payloadPublication': {'situation': [{'situationRecord': [{}]}]}}}
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
