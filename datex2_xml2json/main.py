import json
from argparse import ArgumentParser
from pathlib import Path
from enum import StrEnum
import geoparquet_io as gpio

from .json_validator import JsonValidator
from .transform import TransformerPipeline, RulesTransformer, JsonataTransformer, TransformationRuleFactory, RoadsRegioTransformer,GeoJSONGeometryTransformer
from .util import load_as_json_using_schema

import logging
logger= logging.getLogger(__name__)

class InputFormat(StrEnum):
    DATEX2_2_2_XML = 'datex2_2_2_xml'
    DATEX2_3_7_XML = 'datex2_3_7_xml'
   
class OutputFormat(StrEnum):
    GEOJSON = 'geojson'
    DATEX2_3_7_JSON = 'datex2_3_7_json'
    GEOPARQUET = 'geoparquet'

FILE_SUFFIXES_PER_FORMAT = {
    OutputFormat.GEOJSON: '.geojson',
    OutputFormat.DATEX2_3_7_JSON: '.json',
    OutputFormat.GEOPARQUET: '.parquet',   
}

DEFAULT_SCHEMAS = {
    InputFormat.DATEX2_2_2_XML: 'schema/DATEXIISchema_2_2_3.xsd',
    InputFormat.DATEX2_3_7_XML: 'schema/DATEXII_3.7_Profile/xml/DATEXII_3_D2Payload.xsd'
}

def build_transformer(input_format: InputFormat, output_format: OutputFormat, outfile_name: str):
    if input_format==InputFormat.DATEX2_2_2_XML:
        if output_format==OutputFormat.DATEX2_3_7_JSON:
            # TODO need to specify input format also
            return TransformerPipeline([RulesTransformer(TransformationRuleFactory().xmlv2_to_json3_7()), RoadsRegioTransformer()])
        elif output_format in (OutputFormat.GEOJSON, OutputFormat.GEOPARQUET) :
            #return TransformerPipeline([RulesTransformer(TransformationRuleFactory().xmlv2_to_json()), RoadsRegioTransformer('payload/situation/situationRecord'), GeoJSONGeometryTransformer('payload/situation/situationRecord'), JsonataTransformer()])
            return TransformerPipeline([RulesTransformer(TransformationRuleFactory().xmlv2_to_json()), RoadsRegioTransformer('payload/situation/situationRecord'), GeoJSONGeometryTransformer('payload/situation/situationRecord')])
    else:
        return TransformerPipeline([RulesTransformer(TransformationRuleFactory().xmlv3_to_json3_7())])


def main(filename:str, outDir:str, input_format: InputFormat, output_format: OutputFormat, validate:bool):
    stem = Path(filename).stem

    suffix = FILE_SUFFIXES_PER_FORMAT[output_format]
    outfile_name = Path(outDir) / (stem + suffix)

    input_schema = DEFAULT_SCHEMAS[input_format]
    json_input = load_as_json_using_schema(filename, input_schema)
    transformer = build_transformer(input_format, output_format, outfile_name)
    result = transformer.transform(json_input)
    outfile_name.parent.mkdir(parents=True, exist_ok=True)
    if output_format != OutputFormat.GEOPARQUET:
        with open(outfile_name, 'w') as f:  
            json.dump(result, f, indent=2)
        if validate:
                exit(JsonValidator().validate(outfile_name))
    else:
        geojson_filename = Path(outDir) / (stem + FILE_SUFFIXES_PER_FORMAT.get(OutputFormat.GEOJSON))
        with open(geojson_filename, 'w') as f:  
            json.dump(result, f, indent=2)
        gpio.convert(geojson_filename).write(outfile_name)
       
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument(
        '-V', '--validate', help='validate result against DATEXIIv3 schema', action='store_true'
    )
    parser.add_argument('-i', '--input_format', help='input format', type=InputFormat, choices=list(InputFormat), default=InputFormat.DATEX2_2_2_XML)
    parser.add_argument('-f', '--output_format', help='output format to generate', type=OutputFormat, choices=list(OutputFormat), default=OutputFormat.DATEX2_3_7_JSON)
    
    parser.add_argument(
        '-o', '--outputDir', help='output directory the transformed files are written to', default='out'
    )
    
    args = parser.parse_args()

    main(args.filename, args.outputDir, args.input_format, args.output_format, args.validate)

