from datex2_xml2json.util import load_as_json_using_schema
from datex2_xml2json.transform import TransformerPipeline, RulesTransformer, JsonataTransformer,GeoJSONGeometryTransformer, RoadsRegioTransformer, TransformationRuleFactory
from datex2_xml2json.json_validator import JsonValidator
import json
import tempfile

DATEX2_XSD_2_2_0_SCHEMA = 'schema/DATEXIISchema_2_2_3.xsd'
FIXTURES_DIR = "tests/integration/data/"

def load_and_transform(FIXTURE_NAME:str, overwrite:bool, transformer, suffix:str):
    json_input = load_as_json_using_schema(FIXTURES_DIR+FIXTURE_NAME+".xml", DATEX2_XSD_2_2_0_SCHEMA)
    if overwrite:
        with open(FIXTURES_DIR+FIXTURE_NAME+".json", "w") as f:
            json.dump(json_input, f, indent=2)
    
    with open(FIXTURES_DIR+FIXTURE_NAME+".json") as f:
        expected_input = json.load(f)
    assert json_input == expected_input
    
    json_output = transformer.transform(json_input)
    if overwrite:
        with open(FIXTURES_DIR+FIXTURE_NAME+"_"+suffix+".json", "w") as f:
            json.dump(json_output, f, indent=2)
    
    with open(FIXTURES_DIR+FIXTURE_NAME+"_"+suffix+".json") as f:
        expected_output = json.load(f)
    assert json_output == expected_output
    
    return json_output

def transform_validate(FIXTURE_NAME:str, overwrite:bool, transformer, suffix:str):
    json_output = load_and_transform(FIXTURE_NAME, overwrite, transformer, suffix)

    with tempfile.NamedTemporaryFile("w",delete_on_close=False) as fp:
        json.dump(json_output, fp)
        fp.close()
        res = JsonValidator().validate(fp.name)
    if res != 0:
        raise Exception("Failed validation")

def transform_to_3_7_validate(inputfile:str, overwrite:bool):
    transform_validate(inputfile, overwrite, TransformerPipeline([RulesTransformer(TransformationRuleFactory().xmlv2_to_json3_7())]), "3_7")

def transform_to_flat_geojson(inputfile:str, overwrite:bool):
    transformer = TransformerPipeline([RulesTransformer(TransformationRuleFactory().xmlv2_to_json()), RoadsRegioTransformer('payload/situation/situationRecord'), GeoJSONGeometryTransformer('payload/situation/situationRecord'), JsonataTransformer()])
    #transformer = TransformerPipeline([RulesTransformer(TransformationRuleFactory().xmlv2_to_json()), RoadsRegioTransformer('payload/situation/situationRecord'), GeoJSONGeometryTransformer('payload/situation/situationRecord')])
    load_and_transform(inputfile, overwrite, transformer, "flat_geojson")

# ----------
def test_sitpub_comments_to_json3_7():
    transform_to_3_7_validate("sitpub_comments", False)

def test_sitpub_linearExtension_to_json3_7():
    transform_to_3_7_validate("sitpub_linearExtension", False)

def test_sitpub_linearExtension_to_flat_geojson():
    transform_to_flat_geojson("sitpub_linearExtension", False)

def test_sitpub_linearExtended_to_json3_7():
    transform_to_3_7_validate("sitpub_linearExtended", False)

def test_sitpub_linearExtended_to_flat_geojson():
    transform_to_flat_geojson("sitpub_linearExtended", False)

def test_sitpub_pointCoordinate_to_3_7():
    transform_to_3_7_validate("sitpub_pointCoordinate", False)

def test_sitpub_pointCoordinate_to_flat_geojson():
    transform_to_flat_geojson("sitpub_pointCoordinate", False)

def test_sitpub_sitpub_multi_linearExtended_to_flat_geojson():
    transform_to_flat_geojson("sitpub_multi_linearExtended", False)

def test_sitpub_linearByCoordinates_to_flat_geojson():
    transform_to_flat_geojson("sitpub_linearByCoordinates", False)

def test_sitpub_only_coordinatesForDisplay_to_flat_geojson():
    transform_to_flat_geojson("sitpub_only_coordinatesForDisplay", False)

