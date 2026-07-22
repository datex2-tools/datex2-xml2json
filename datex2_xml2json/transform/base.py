from datex2_xml2json.util import replace, xpath_dict

from .transformation_rules import TransformationRules


class AbstractTransformer:
    def transform(self, a_dict: dict) -> dict:
        pass


class TransformerPipeline(AbstractTransformer):
    def __init__(self, transformers: list[AbstractTransformer]):
        self.transformers = list(transformers)

    def add_transformer(self, transformer: AbstractTransformer):
        self.transformer.append(transformer)

    def transform(self, a_dict: dict) -> dict:
        result = a_dict
        for t in self.transformers:
            result = t.transform(result)

        return result


class RulesTransformer(AbstractTransformer):
    def __init__(self, rules: TransformationRules):
        self.rules = rules

    def transform(self, a_dict: dict) -> dict:
        # Transforms the result of xml2json transformation into DATEXIIv3 json.
        # This includes:
        # * renamings of certain properties according to v2 to v3 name changes
        # * renamings of certain properties according to changed writing in json
        # * casts values of certain properties to intended types
        # * ...

        return replace(
            a_dict,
            None,
            self.rules.renamings,
            self.rules.value_transforms,
            self.rules.keys_to_drop,
            self.rules.type_mappings,
            self.rules.keys_to_pull_up,
        )


class ProcessingTransformer(AbstractTransformer):
    def __init__(self, xpath: str):
        self.xpath = xpath

    def transform(self, a_dict: dict) -> dict:
        for elem in xpath_dict(a_dict, self.xpath):
            self.process(elem)

        return a_dict

    def process(self, a_dict: dict):
        pass
