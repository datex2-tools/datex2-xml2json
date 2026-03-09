import json
from argparse import ArgumentParser
from pathlib import Path
from lxml import etree
from enum import StrEnum
from .json_validator import JsonValidator
from .transformer import Transformer

import logging
logger= logging.getLogger(__name__)


class OutputFormat(StrEnum):
    GEOJSON = 'geojson'
    DATEX_3_6_JSON = 'datex_3_6_json'
    

def main(filename:str, outDir:str, format: OutputFormat, validate:bool):
    stem = Path(filename).stem
    suffix = '.geojson' if format == OutputFormat.GEOJSON else '.json'
    outfile_name = Path(outDir) / (stem + suffix)

    if filename.endswith('.xml'):
        # TODO convert to json
        tree = etree.parse(filename)
    elif filename.endswith('.json'):
        with open(filename) as f:
            json_input = json.load(f)

    result = Transformer().transform(json_input)

    outfile_name.parent.mkdir(parents=True, exist_ok=True)
    with open(outfile_name, 'w') as f:
        json.dump(result, f, indent=2)

    if validate:
        JsonValidator().validate(outfile_name)
       
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument(
        '-V', '--validate', help='validate result against DATEXIIv3 schema', action='store_true'
    )
    parser.add_argument('-f', '--format', help='output format to generate', type=OutputFormat, choices=list(OutputFormat), default=OutputFormat.DATEX_3_6_JSON)
    
    parser.add_argument(
        '-o', '--outputDir', help='output directory the transformed files are written to', default='out'
    )
    
    args = parser.parse_args()

    main(args.filename, args.outputDir, args.format, args.validate)

