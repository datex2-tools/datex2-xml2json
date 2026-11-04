from datetime import datetime
from pathlib import Path

import pyarrow.parquet as pq

from datex2_xml2json.transform import GeoparquetRenderer


def test_timezones(tmp_path: Path) -> None:
    geojson = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {
                    'situationRecordCreationTime': '2026-01-01T00:00:00+01:00',
                },
                'geometry': {'type': 'Point', 'coordinates': [9.0, 49.0]},
            },
            {
                'type': 'Feature',
                'properties': {
                    'situationRecordCreationTime': '2026-01-01T00:00:00',
                },
                'geometry': {'type': 'Point', 'coordinates': [9.0, 49.0]},
            },
        ],
    }

    renderer = GeoparquetRenderer()
    filename = tmp_path / 'test_timezones.parquet'
    renderer.render(filename, geojson)

    with pq.ParquetFile(str(filename)) as reader:
        table = reader.read()

        features = table.to_pylist()
        assert features[0]['situationRecordCreationTime'].timestamp() == datetime.fromisoformat('2026-01-01T00:00:00+01:00').timestamp()
        assert features[1]['situationRecordCreationTime'].timestamp() == datetime.fromisoformat('2026-01-01T00:00:00+00:00').timestamp()
