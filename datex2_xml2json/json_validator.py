from check_jsonschema.checker import SchemaChecker
from check_jsonschema.instance_loader import InstanceLoader
from check_jsonschema.reporter import REPORTER_BY_NAME, Reporter
from check_jsonschema.formats import FormatOptions
from check_jsonschema.schema_loader import SchemaLoader
from check_jsonschema.cli.param_types import CustomLazyFile
from check_jsonschema.regex_variants import RegexImplementation, RegexVariantName

DEFAULT_DATEX_JSON = 'schema/DATEXII_3.6_Profile_2026-03-08/DATEXII_3_D2Payload.json'

class JsonValidator:
    def __init__(self):
        pass


    def build_reporter(self, output_format:str, verbosity:int) -> Reporter:
        cls = REPORTER_BY_NAME[output_format]
        return cls(verbosity=verbosity)

    def validate(self, filename):
        schema_loader = SchemaLoader(
            DEFAULT_DATEX_JSON,
            disable_cache=False,
            base_uri=None,
            validator_class=None,
            
        )
        checker = SchemaChecker(schema_loader=schema_loader,
            instance_loader=InstanceLoader([CustomLazyFile(filename,"rb")]),
            reporter=self.build_reporter('text', 2),
            format_opts= FormatOptions(
                regex_impl=RegexImplementation(RegexVariantName.default),
                enabled=True,
                disabled_formats=[],
                ),
            regex_impl=RegexImplementation(RegexVariantName.default))
        checker.run()