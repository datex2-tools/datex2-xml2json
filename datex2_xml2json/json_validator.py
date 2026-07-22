from check_jsonschema.checker import SchemaChecker
from check_jsonschema.cli.param_types import CustomLazyFile
from check_jsonschema.formats import FormatOptions
from check_jsonschema.instance_loader import InstanceLoader
from check_jsonschema.regex_variants import RegexImplementation, RegexVariantName
from check_jsonschema.reporter import REPORTER_BY_NAME, Reporter
from check_jsonschema.schema_loader import SchemaLoader


class JsonValidator:
    def __init__(self, schema_path):
        self.schema_loader = SchemaLoader(
            schema_path,
            disable_cache=False,
            base_uri=None,
            validator_class=None,
        )

    def build_reporter(self, output_format: str, verbosity: int) -> Reporter:
        cls = REPORTER_BY_NAME[output_format]
        return cls(verbosity=verbosity)

    def validate(self, filename):
        checker = SchemaChecker(
            schema_loader=self.schema_loader,
            instance_loader=InstanceLoader([CustomLazyFile(filename, 'rb')]),
            reporter=self.build_reporter('text', 2),
            format_opts=FormatOptions(
                regex_impl=RegexImplementation(RegexVariantName.default),
                enabled=True,
                disabled_formats=[],
            ),
            regex_impl=RegexImplementation(RegexVariantName.default),
        )

        return checker.run()
