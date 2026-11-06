from typing import Any

import pytest

from datex2_xml2json.transform import CifsTransformer


def test_post_transform() -> None:
    transformer = CifsTransformer()
    incidents = {
        'incidents': [
            {'id': '1487640-1487641-1487644-3508083', 'type': 'HAZARD'},
            {
                'id': '1487640-1487641-1487644-3508083-sperrung',
                'type': 'ROAD_CLOSED',
                'geometry': {'type': 'LineString', 'coordinates': [[8.110721, 47.606249], [8.110684, 47.60628]]},
            },
        ]
    }
    expected = {
        'incidents': [
            {
                'id': '1487640-1487641-1487644-3508083-sperrung',
                'type': 'ROAD_CLOSED',
                'polyline': '47.606249 8.110721 47.60628 8.110684',
            },
        ]
    }
    actual = transformer.post_transform(incidents)
    assert expected == actual


testdata = [
    (['HAZARD', None], ['ROAD_CLOSED', None], ['ROAD_CLOSED', None]),
    (['HAZARD', 'HAZARD_ON_ROAD_CONSTRUCTION'], ['HAZARD', None], ['HAZARD', 'HAZARD_ON_ROAD_CONSTRUCTION']),
    (['ACCIDENT', 'ACCIDENT_MINOR'], ['CHIT_CHAT', None], ['ACCIDENT', 'ACCIDENT_MINOR']),
    (['JAM', 'JAM_HEAVY_TRAFFIC'], ['CHIT_CHAT', None], ['JAM', 'JAM_HEAVY_TRAFFIC']),
]


@pytest.mark.parametrize(
    'type_subtype_first_situation_record,type_subtype_second_situation_record,expected_type_subtype_after_merge', testdata
)
def test_most_specific_type_and_subtype_is_retained_on_merge(
    type_subtype_first_situation_record: list[Any],
    type_subtype_second_situation_record: list[Any],
    expected_type_subtype_after_merge: list[Any],
) -> None:
    transformer = CifsTransformer()

    first_sr = {
        'id': '1487640-1487641-1487644-3508083',
        'type': type_subtype_first_situation_record[0],
        'subtype': type_subtype_first_situation_record[1],
        'geometry': {'type': 'LineString', 'coordinates': [[8.110721, 47.606249], [8.110684, 47.60628]]},
    }
    second_sr = {
        'id': '1487640-1487641-1487644-3508083-sperrung',
        'type': type_subtype_second_situation_record[0],
        'subtype': type_subtype_second_situation_record[1],
        'geometry': {'type': 'LineString', 'coordinates': [[8.110721, 47.606249], [8.110684, 47.60628]]},
    }
    incidents = {
        'incidents': [
            first_sr,
            second_sr,
        ]
    }
    actual = transformer.post_transform(incidents)
    retained_sr = actual['incidents'][0]

    assert expected_type_subtype_after_merge == [retained_sr['type'], retained_sr.get('subtype')]
