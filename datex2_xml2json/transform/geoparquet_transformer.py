import geoparquet_io as gpio
import pyarrow as pa
from shapely.geometry import shape
from .base import AbstractTransformer

class GeoparquetRenderer:

    def __init__(self):
        pass

    def render(self, filename, a_geojson_dict: dict) -> dict:
        records = []
        for f in a_geojson_dict["features"]:
            props = f["properties"].copy()
            if not   "geometry" in f:
                print(f)
            props["geometry"] = shape(f["geometry"])
            records.append(props)
        
        table = gpq.to_arrow_table(
            records,
            geometry_column="geometry",
            crs="EPSG:4326"
        )
        gpq.write_geoparquet(table, filename)
