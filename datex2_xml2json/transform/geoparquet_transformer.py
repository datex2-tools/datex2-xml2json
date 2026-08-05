import geoparquet_io as gpio
import pyarrow as pa
from shapely.geometry import shape


class GeoparquetRenderer:
    def __init__(self):
        pass

    def render(self, filename, a_geojson_dict: dict) -> None:
        records = []
        for f in a_geojson_dict['features']:
            props = f['properties'].copy()
            props['geometry'] = shape(f['geometry']).wkb
            records.append(props)

        table = pa.Table.from_pylist(records)

        gpio.write_geoparquet(table, filename)
