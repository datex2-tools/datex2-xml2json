from datex2_xml2json.util import replace

def replace_and_check(value, expected, renamings={}, value_transforms={}, keys_to_drop={}, type_mappings={}, keys_to_pull_up={}):
    # Helper function which performs replacements and asserts the result is as expected
    actual = replace(value, None, renamings, value_transforms, keys_to_drop, type_mappings, keys_to_pull_up)
    assert actual == expected

def test_renamings():
    # Some properties need to be renamed
    renamings = {'d2LogicalModel': 'payload',}

    # Renaming at root level
    replace_and_check({ 'd2LogicalModel': {}}, { 'payload': {}}, renamings=renamings)
    # renaming for nested element
    replace_and_check({ 'anyParent': {'d2LogicalModel': {}}}, { 'anyParent': {'payload': {}}}, renamings=renamings)

def test_value_transforms():
    # Some properties require specific transfomations

    value_transforms = {'key': lambda v: int(v)}

    replace_and_check({ 'key': '1'}, { 'key': 1}, value_transforms=value_transforms)
    
def test_keys_to_drop_from_any_parent():
    # Some properties need to be dropped, either in general, or only if appearing under a specific parent
    keys_to_drop = {'unwanted_key': None}

    replace_and_check({ 'parent': {'unwanted_key': '1', 'wanted_key': '2'}}, {'parent': {'wanted_key': '2'}}, keys_to_drop=keys_to_drop)
    
def test_keys_to_drop_from_specific_parent():
    # Some properties need to be dropped, either in general, or only if appearing under a specific parent
    
    keys_to_drop = {'unwanted_key': 'parent'}

    replace_and_check({ 'parent': {'unwanted_key': '1', 'wanted_key': '2'}}, {'parent': {'wanted_key': '2'}}, keys_to_drop=keys_to_drop)
    replace_and_check({ 'another_parent': {'unwanted_key': '1', 'wanted_key': '2'}}, {'another_parent': {'unwanted_key': '1', 'wanted_key': '2'}}, keys_to_drop=keys_to_drop)

def test_type_mappings():
    # Instead of having the objects type indicated by e.g. @xsitype, 
    # a wrapping type object is inserted by DATEXII Part 15.
    
    xsitype_mappings = {
        'AbnormalTraffic': 'sitAbnormalTraffic',
    }
    
    replace_and_check({ 'situationRecord': {'@xsi:type': 'AbnormalTraffic'}}, { 'situationRecord': {'sitAbnormalTraffic': {'@xsi:type': 'AbnormalTraffic'}}}, type_mappings=xsitype_mappings)
    
def test_keys_to_pull_up_all_children():
    # For some objects, all or some of their properties need to be pulled one level up
    
    keys_to_pull_up = {
        'openlrExtendedPoint': None
    }
    
    replace_and_check({ 'openlrExtendedPoint': {'a': 'value', 'b': 'value'}}, { 'a': 'value', 'b': 'value'}, keys_to_pull_up=keys_to_pull_up)

def test_keys_to_pull_up_specified_children():
    # For some objects, all or some of their properties need to be pulled one level up
    keys_to_pull_up = {
        'openlrExtendedPoint': ['a']
    }
    
    replace_and_check({ 'openlrExtendedPoint': {'a': 'value', 'b': 'value'}}, { 'a': 'value', 'openlrExtendedPoint': {'b': 'value'}}, keys_to_pull_up=keys_to_pull_up)
