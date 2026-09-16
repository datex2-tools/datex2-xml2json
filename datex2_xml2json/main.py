import json
import logging
from argparse import ArgumentParser
from enum import StrEnum
from pathlib import Path

from .json_validator import JsonValidator
from .transform import (
    CifsTransformer,
    GeoJSONGeometryTransformer,
    GeoparquetRenderer,
    JsonataTransformer,
    RoadsRegioTransformer,
    RulesTransformer,
    TransformationRuleFactory,
    TransformerPipeline,
)
from .util import load_as_json_using_schema

logger = logging.getLogger(__name__)


class InputFormat(StrEnum):
    DATEX2_2_2_XML = 'datex2_2_2_xml'
    DATEX2_3_7_XML = 'datex2_3_7_xml'


class OutputFormat(StrEnum):
    RAW = 'raw'
    CIFS = 'cifs'
    GEOJSON = 'geojson'
    DATEX2_3_7_JSON = 'datex2_3_7_json'
    DATEX2_3_7_JSON_LITE = 'datex2_3_7_json_lite'
    GEOPARQUET = 'geoparquet'


FILE_SUFFIXES_PER_FORMAT = {
    OutputFormat.RAW: '.raw.json',
    OutputFormat.CIFS: '.cifs.json',
    OutputFormat.GEOJSON: '.geojson',
    OutputFormat.DATEX2_3_7_JSON: '.json',
    OutputFormat.DATEX2_3_7_JSON_LITE: '.lite.json',
    OutputFormat.GEOPARQUET: '.parquet',
}

DEFAULT_SCHEMAS = {
    InputFormat.DATEX2_2_2_XML: 'schema/DATEXIISchema_2_2_3.xsd',
    InputFormat.DATEX2_3_7_XML: 'schema/DATEXII_3.7_Profile/xml/DATEXII_3_D2Payload.xsd',
}

OUTPUT_SCHEMAS = {
    OutputFormat.DATEX2_3_7_JSON: 'schema/DATEXII_3.7_Profile/DATEXII_3_D2Payload.json',
    OutputFormat.CIFS: 'schema/cifs_schema.json',
}


def build_transformer(input_format: InputFormat, output_format: OutputFormat):
    if input_format == InputFormat.DATEX2_2_2_XML:
        if output_format == OutputFormat.DATEX2_3_7_JSON:
            return TransformerPipeline(
                [
                    RulesTransformer(TransformationRuleFactory().xmlv2_to_json3_7()),
                    RoadsRegioTransformer(),
                ]
            )
        elif output_format == OutputFormat.DATEX2_3_7_JSON_LITE:
            return TransformerPipeline(
                [
                    RulesTransformer(TransformationRuleFactory().xmlv2_to_json()),
                    RoadsRegioTransformer('payload/situation/situationRecord'),
                    GeoJSONGeometryTransformer('payload/situation/situationRecord'),
                ]
            )
        elif output_format == OutputFormat.GEOJSON:
            return build_transformer(input_format, OutputFormat.DATEX2_3_7_JSON_LITE).add_transformer(JsonataTransformer())
        elif output_format == OutputFormat.CIFS:
            return build_transformer(input_format, OutputFormat.GEOJSON).add_transformer(CifsTransformer())
        elif output_format == OutputFormat.RAW:
            return TransformerPipeline([])

    else:
        return TransformerPipeline([RulesTransformer(TransformationRuleFactory().xmlv3_to_json3_7())])


def write(stem: str, json_result: dict, output_format: OutputFormat, outDir: str, validate: bool = False):
    suffix = FILE_SUFFIXES_PER_FORMAT[output_format]
    outfile_name = Path(outDir) / (stem + suffix)
    outfile_name.parent.mkdir(parents=True, exist_ok=True)

    if output_format != OutputFormat.GEOPARQUET:
        with open(outfile_name, 'w') as f:
            json.dump(json_result, f, indent=2)
        if validate:
            exit(JsonValidator(OUTPUT_SCHEMAS[output_format]).validate(outfile_name))
    else:
        GeoparquetRenderer().render(outfile_name, json_result)


def generate_all(stem: str, json_input: dict, outDir: str, validate: bool):
    write(stem, json_input, OutputFormat.RAW, outDir)
    jsonLiteTransformer = build_transformer(InputFormat.DATEX2_2_2_XML, OutputFormat.DATEX2_3_7_JSON_LITE)
    jsonLite_output = jsonLiteTransformer.transform(json_input)
    write(stem, jsonLite_output, OutputFormat.DATEX2_3_7_JSON_LITE, outDir)
    geojson_output = JsonataTransformer().transform(jsonLite_output)
    write(stem, geojson_output, OutputFormat.GEOJSON, outDir)
    write(stem, geojson_output, OutputFormat.GEOPARQUET, outDir)
    cifs_output = CifsTransformer().transform(geojson_output)
    write(stem, cifs_output, OutputFormat.CIFS, outDir, validate)


def main(
    filename: str,
    outDir: str,
    input_format: InputFormat,
    output_format: OutputFormat,
    validate: bool,
):
    stem = Path(filename).stem
    input_schema = DEFAULT_SCHEMAS[input_format]
    json_input = load_as_json_using_schema(filename, input_schema)

    if output_format is None:
        generate_all(stem, json_input, outDir, validate)
    else:
        json_output_format = OutputFormat.GEOJSON if output_format == OutputFormat.GEOPARQUET else output_format
        transformer = build_transformer(input_format, json_output_format)
        result = transformer.transform(json_input)

        write(stem, result, output_format, outDir, validate)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument(
        '-V',
        '--validate',
        help='validate result against DATEXIIv3 schema (requires output format datex2_3_7_json)',
        action='store_true',
    )
    parser.add_argument(
        '-i',
        '--input_format',
        help='input format',
        type=InputFormat,
        choices=list(InputFormat),
        default=InputFormat.DATEX2_2_2_XML,
    )
    parser.add_argument(
        '-f',
        '--output_format',
        help='output format to generate',
        type=OutputFormat,
        choices=list(OutputFormat),
    )

    parser.add_argument(
        '-o',
        '--outputDir',
        help='output directory the transformed files are written to',
        default='out',
    )

    args = parser.parse_args()

    if args.validate and args.output_format is not None and args.output_format not in OUTPUT_SCHEMAS:
        logger.error('Validation is not supported for format %s', args.output_format)
        exit(1)

    main(
        args.filename,
        args.outputDir,
        args.input_format,
        args.output_format,
        args.validate,
    )
