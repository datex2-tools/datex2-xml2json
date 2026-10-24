from datex2_xml2json.util import replace, xpath_dict

from .transformation_rules import TransformationRules


class AbstractTransformer:
    def transform(self, a_dict: dict) -> dict:
        return a_dict


class TransformerPipeline(AbstractTransformer):
    def __init__(self, transformers: list[AbstractTransformer]):
        self.transformers = list(transformers)

    def add_transformer(self, transformer: AbstractTransformer):
        self.transformers.append(transformer)
        return self

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


class SituationRecordTransformer(ProcessingTransformer):
    def __init__(self, xpath: str):
        super().__init__(xpath)

    def process_situation_record(self, situation_record: dict) -> None:
        pass

    def process(self, situation_record_wrapper: dict) -> None:
        if isinstance(situation_record_wrapper, dict) and len(situation_record_wrapper) == 1:
            situation_record = situation_record_wrapper.get(next(iter(situation_record_wrapper.keys())))
        else:
            situation_record = situation_record_wrapper
        if situation_record is None:
            return

        self.process_situation_record(situation_record)
